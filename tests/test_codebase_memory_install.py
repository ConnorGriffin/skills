from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "tools" / "codebase-memory"
INSTALLER = SKILL / "scripts" / "install.py"
OWNERSHIP = "Managed by codebase-memory skill installer."


def filesystem_snapshot(root: Path) -> dict[str, tuple[int, str | bytes | None]]:
    snapshot = {}

    def visit(directory: Path) -> None:
        for entry in os.scandir(directory):
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            metadata = entry.stat(follow_symlinks=False)
            kind = metadata.st_mode & 0o170000
            if entry.is_symlink():
                payload: str | bytes | None = os.readlink(path)
            elif entry.is_file(follow_symlinks=False):
                payload = path.read_bytes()
            else:
                payload = None
            snapshot[relative] = (kind, payload)
            if entry.is_dir(follow_symlinks=False):
                visit(path)

    if root.is_dir() and not root.is_symlink():
        visit(root)
    return snapshot


class CodebaseMemoryInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.claude_home = self.scratch / "claude-home"

    def tearDown(self):
        self.temporary.cleanup()

    def install(
        self,
        claude_home: Path | None = None,
        settings_file: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            "python3",
            str(INSTALLER),
            "--claude-home",
            str(claude_home or self.claude_home),
        ]
        if settings_file is not None:
            command += ["--settings-file", str(settings_file)]
        return subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def settings(self, claude_home: Path | None = None) -> dict:
        path = (claude_home or self.claude_home) / "settings.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_clean_install_activates_the_public_skill(self):
        result = self.install()

        self.assertEqual(result.returncode, 0, result.stderr)
        hooks = self.claude_home / "hooks"
        gate = hooks / "cbm-code-discovery-gate"
        session = hooks / "cbm-session-reminder"
        reminder = hooks / "cbm-code-discovery-reminder.md"
        for path in (gate, session, reminder):
            self.assertTrue(path.is_file(), path)
            self.assertIn(OWNERSHIP, path.read_text(encoding="utf-8"))
        self.assertTrue(os.access(gate, os.X_OK))
        self.assertTrue(os.access(session, os.X_OK))
        self.assertFalse(reminder.stat().st_mode & 0o111)

        settings = self.settings()
        self.assertEqual(settings["hooks"]["PreToolUse"][0]["matcher"], "Grep|Glob")
        self.assertEqual(
            [entry["matcher"] for entry in settings["hooks"]["SessionStart"]],
            ["startup", "resume", "clear", "compact"],
        )
        self.assertEqual(self.claude_home.joinpath("settings.json").stat().st_mode & 0o777, 0o600)

    def test_existing_settings_are_merged_and_reruns_are_byte_stable(self):
        self.claude_home.mkdir()
        settings_path = self.claude_home / "settings.json"
        canonical_gate = {
            "matcher": "Grep|Glob",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{self.claude_home}/hooks/cbm-code-discovery-gate",
                    "timeout": 5,
                }
            ],
        }
        original = {
            "model": "opus",
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Write|Edit", "hooks": [{"type": "command", "command": "safe-hook"}]},
                    canonical_gate,
                    canonical_gate,
                ],
                "Stop": [{"hooks": [{"type": "command", "command": "stop-hook"}]}],
            },
        }
        settings_path.write_text(json.dumps(original), encoding="utf-8")
        settings_path.chmod(0o640)

        first = self.install()

        self.assertEqual(first.returncode, 0, first.stderr)
        merged = self.settings()
        self.assertEqual(merged["model"], "opus")
        self.assertEqual(merged["hooks"]["Stop"], original["hooks"]["Stop"])
        self.assertEqual(merged["hooks"]["PreToolUse"][0], original["hooks"]["PreToolUse"][0])
        self.assertEqual(merged["hooks"]["PreToolUse"].count(canonical_gate), 1)
        self.assertEqual(settings_path.stat().st_mode & 0o777, 0o640)
        first_bytes = {
            path.name: path.read_bytes()
            for path in [settings_path, *sorted((self.claude_home / "hooks").iterdir())]
        }

        second = self.install()

        self.assertEqual(second.returncode, 0, second.stderr)
        second_bytes = {
            path.name: path.read_bytes()
            for path in [settings_path, *sorted((self.claude_home / "hooks").iterdir())]
        }
        self.assertEqual(second_bytes, first_bytes)

    def test_explicit_settings_target_takes_the_registrations_alone(self):
        versioned = self.scratch / "dotfiles"
        versioned.mkdir()
        settings_path = versioned / "settings.json"

        result = self.install(settings_file=settings_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        hooks = self.claude_home / "hooks"
        for name in (
            "cbm-code-discovery-gate",
            "cbm-session-reminder",
            "cbm-code-discovery-reminder.md",
        ):
            self.assertTrue((hooks / name).is_file(), name)
        self.assertFalse((self.claude_home / "settings.json").exists())

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        commands = [
            hook["command"]
            for entries in settings["hooks"].values()
            for entry in entries
            for hook in entry["hooks"]
        ]
        self.assertTrue(commands)
        for command in commands:
            self.assertTrue(command.startswith(f"{hooks}/"), command)
        self.assertEqual(settings_path.stat().st_mode & 0o777, 0o600)

    def test_explicit_settings_target_is_merged_and_reruns_are_byte_stable(self):
        versioned = self.scratch / "dotfiles"
        versioned.mkdir()
        settings_path = versioned / "settings.json"
        original = {
            "model": "opus",
            "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "stop-hook"}]}]},
        }
        settings_path.write_text(json.dumps(original), encoding="utf-8")

        first = self.install(settings_file=settings_path)

        self.assertEqual(first.returncode, 0, first.stderr)
        merged = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(merged["model"], "opus")
        self.assertEqual(merged["hooks"]["Stop"], original["hooks"]["Stop"])
        self.assertIn("SessionStart", merged["hooks"])
        first_bytes = settings_path.read_bytes()

        second = self.install(settings_file=settings_path)

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(settings_path.read_bytes(), first_bytes)

    def test_explicit_settings_target_installs_through_a_symlinked_directory(self):
        real = self.scratch / "checkout"
        real.mkdir()
        link = self.scratch / "linked-checkout"
        link.symlink_to(real, target_is_directory=True)

        result = self.install(settings_file=link / "settings.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        settings = json.loads((real / "settings.json").read_text(encoding="utf-8"))
        self.assertIn("SessionStart", settings["hooks"])

    def test_symlinked_explicit_settings_target_fails_before_any_write(self):
        versioned = self.scratch / "dotfiles"
        versioned.mkdir()
        external = self.scratch / "external-settings.json"
        original = b'{"external": true}\n'
        external.write_bytes(original)
        settings_path = versioned / "settings.json"
        settings_path.symlink_to(external)

        result = self.install(settings_file=settings_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be a regular non-symlink file", result.stderr)
        self.assertIn(str(settings_path), result.stderr)
        self.assertTrue(settings_path.is_symlink())
        self.assertEqual(external.read_bytes(), original)
        self.assertFalse((self.claude_home / "hooks").exists())

    def test_an_unusable_explicit_parent_is_a_no_write_failure(self):
        cases = ["missing", "regular-file", "mode-500", "mode-600"]
        for name in cases:
            with self.subTest(parent=name):
                claude_home = self.scratch / f"claude-home-{name}"
                container = self.scratch / f"container-{name}"
                if name == "regular-file":
                    container.write_text("not a directory", encoding="utf-8")
                elif name != "missing":
                    container.mkdir()
                    container.chmod(0o500 if name == "mode-500" else 0o600)
                settings_path = container / "settings.json"

                try:
                    result = self.install(claude_home, settings_file=settings_path)
                finally:
                    if name in ("mode-500", "mode-600"):
                        container.chmod(0o700)

                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(str(container), result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((claude_home / "hooks").exists())
                self.assertFalse(settings_path.exists())

    def test_malformed_settings_fail_before_any_write(self):
        self.claude_home.mkdir()
        settings_path = self.claude_home / "settings.json"
        malformed = b'{"hooks": '
        settings_path.write_bytes(malformed)

        result = self.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("settings.json is not valid JSON", result.stderr)
        self.assertEqual(settings_path.read_bytes(), malformed)
        self.assertFalse((self.claude_home / "hooks").exists())

    def test_conflicting_managed_registration_fails_before_any_write(self):
        self.claude_home.mkdir()
        settings_path = self.claude_home / "settings.json"
        conflicting = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Grep|Glob",
                        "hooks": [
                            {
                                "type": "command",
                                "command": f"{self.claude_home}/hooks/cbm-code-discovery-gate",
                                "timeout": 10,
                            }
                        ],
                    }
                ]
            }
        }
        original = (json.dumps(conflicting) + "\n").encode()
        settings_path.write_bytes(original)

        result = self.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflicting managed hook registration", result.stderr)
        self.assertEqual(settings_path.read_bytes(), original)
        self.assertFalse((self.claude_home / "hooks").exists())

    def test_legacy_tilde_registration_target_is_a_conflict(self):
        home = self.scratch / "home"
        claude_home = home / ".claude"
        claude_home.mkdir(parents=True)
        settings_path = claude_home / "settings.json"
        legacy = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Grep|Glob",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "~/.claude/hooks/cbm-code-discovery-gate",
                                "timeout": 5,
                            }
                        ],
                    }
                ]
            }
        }
        original = (json.dumps(legacy) + "\n").encode()
        settings_path.write_bytes(original)
        environment = os.environ.copy()
        environment["HOME"] = str(home)

        result = subprocess.run(
            ["python3", str(INSTALLER), "--claude-home", str(claude_home)],
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflicting managed hook registration", result.stderr)
        self.assertEqual(settings_path.read_bytes(), original)
        self.assertFalse((claude_home / "hooks").exists())

    def test_managed_command_with_arguments_is_a_conflict(self):
        self.claude_home.mkdir()
        settings_path = self.claude_home / "settings.json"
        command = f"{self.claude_home}/hooks/cbm-code-discovery-gate --unexpected"
        conflicting = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Grep|Glob",
                        "hooks": [{"type": "command", "command": command, "timeout": 5}],
                    }
                ]
            }
        }
        original = (json.dumps(conflicting) + "\n").encode()
        settings_path.write_bytes(original)

        result = self.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflicting managed hook registration", result.stderr)
        self.assertEqual(settings_path.read_bytes(), original)
        self.assertFalse((self.claude_home / "hooks").exists())

    def test_symlinked_settings_fail_without_following_the_external_target(self):
        self.claude_home.mkdir()
        external = self.scratch / "external-settings.json"
        original = b'{"external": true}\n'
        external.write_bytes(original)
        settings_path = self.claude_home / "settings.json"
        settings_path.symlink_to(external)

        result = self.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("settings.json must be a regular non-symlink file", result.stderr)
        self.assertTrue(settings_path.is_symlink())
        self.assertEqual(external.read_bytes(), original)
        self.assertFalse((self.claude_home / "hooks").exists())

    def test_symlinked_hooks_directory_fails_without_writing_through_it(self):
        self.claude_home.mkdir()
        external = self.scratch / "external-hooks"
        external.mkdir()
        sentinel = external / "sentinel"
        sentinel.write_text("unchanged", encoding="utf-8")
        (self.claude_home / "hooks").symlink_to(external, target_is_directory=True)

        result = self.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hooks must be a real non-symlink directory", result.stderr)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "unchanged")
        self.assertEqual(sorted(path.name for path in external.iterdir()), ["sentinel"])
        self.assertFalse((self.claude_home / "settings.json").exists())

    def test_every_non_regular_or_unowned_managed_node_is_a_no_write_failure(self):
        cases = [
            ("settings-directory", "settings", "directory"),
            ("settings-fifo", "settings", "fifo"),
            ("hooks-file", "hooks", "file"),
        ]
        for managed_name in (
            "cbm-code-discovery-gate",
            "cbm-session-reminder",
            "cbm-code-discovery-reminder.md",
        ):
            for node_kind in ("file", "symlink", "broken-symlink", "directory", "fifo"):
                cases.append((f"{managed_name}-{node_kind}", managed_name, node_kind))
        for name, target, node_kind in cases:
            with self.subTest(name=name):
                claude_home = self.scratch / name
                claude_home.mkdir()
                external = self.scratch / f"{name}-external"
                external.write_bytes(b"external unchanged")
                if target == "settings":
                    path = claude_home / "settings.json"
                elif target == "hooks":
                    path = claude_home / "hooks"
                else:
                    hooks = claude_home / "hooks"
                    hooks.mkdir()
                    path = hooks / target

                if node_kind == "directory":
                    path.mkdir()
                elif node_kind == "fifo":
                    os.mkfifo(path)
                elif node_kind == "symlink":
                    path.symlink_to(external)
                elif node_kind == "broken-symlink":
                    path.symlink_to(self.scratch / "does-not-exist")
                else:
                    path.write_text("not managed", encoding="utf-8")

                before = filesystem_snapshot(claude_home)
                result = self.install(claude_home)

                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(filesystem_snapshot(claude_home), before)
                self.assertEqual(external.read_bytes(), b"external unchanged")

    def test_complete_managed_files_converge_when_settings_are_absent(self):
        hooks = self.claude_home / "hooks"
        hooks.mkdir(parents=True)
        source_by_name = {
            "cbm-code-discovery-gate": SKILL / "hooks" / "cbm-code-discovery-gate",
            "cbm-session-reminder": SKILL / "hooks" / "cbm-session-reminder",
            "cbm-code-discovery-reminder.md": SKILL / "reminder.md",
        }
        for name, source in source_by_name.items():
            shutil.copyfile(source, hooks / name)
        unfinished = hooks / ".codebase-memory-install-unfinished"
        unfinished.write_text("ignored", encoding="utf-8")

        result = self.install()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(unfinished.read_text(encoding="utf-8"), "ignored")
        self.assertIsInstance(self.settings(), dict)

    def test_changed_targets_are_atomically_replaced_with_valid_complete_files(self):
        hooks = self.claude_home / "hooks"
        hooks.mkdir(parents=True)
        targets = [
            hooks / "cbm-code-discovery-gate",
            hooks / "cbm-session-reminder",
            hooks / "cbm-code-discovery-reminder.md",
        ]
        for target in targets:
            target.write_text(f"# {OWNERSHIP}\nstale\n", encoding="utf-8")
        settings_path = self.claude_home / "settings.json"
        settings_path.write_text('{"unrelated": true}\n', encoding="utf-8")
        targets.append(settings_path)
        old_inodes = {path: path.stat().st_ino for path in targets}

        result = self.install()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.settings()["unrelated"])
        for target in targets:
            self.assertNotEqual(target.stat().st_ino, old_inodes[target], target)
        for target in targets[:-1]:
            content = target.read_bytes()
            self.assertTrue(content)
            self.assertIn(OWNERSHIP.encode(), content)

    def test_hooks_delegate_fail_open_and_emit_the_single_reminder_policy(self):
        self.assertEqual(self.install().returncode, 0)
        hooks = self.claude_home / "hooks"
        gate = hooks / "cbm-code-discovery-gate"
        fake = self.scratch / "fake-codebase-memory"
        fake.write_text(
            "#!/bin/sh\n[ \"$1\" = hook-augment ] || exit 2\nsed 's/^/augmented:/'\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        environment = os.environ.copy()
        environment["CODEBASE_MEMORY_BIN"] = str(fake)

        success = subprocess.run(
            [str(gate)], input="needle\n", text=True, capture_output=True, env=environment
        )

        self.assertEqual(success.returncode, 0)
        self.assertEqual(success.stdout, "augmented:needle\n")
        fake.write_text("#!/bin/sh\nprintf 'must not leak'\nexit 1\n", encoding="utf-8")
        failed = subprocess.run([str(gate)], text=True, capture_output=True, env=environment)
        self.assertEqual((failed.returncode, failed.stdout), (0, ""))
        environment["CODEBASE_MEMORY_BIN"] = str(self.scratch / "missing")
        missing = subprocess.run([str(gate)], text=True, capture_output=True, env=environment)
        self.assertEqual((missing.returncode, missing.stdout), (0, ""))

        reminder = (SKILL / "reminder.md").read_bytes()
        installed_reminder = hooks / "cbm-code-discovery-reminder.md"
        self.assertEqual(installed_reminder.read_bytes(), reminder)
        session = subprocess.run(
            [str(hooks / "cbm-session-reminder")], capture_output=True, check=False
        )
        self.assertEqual((session.returncode, session.stdout), (0, reminder))

    def test_rendered_commands_are_shell_safe_for_caller_supplied_paths(self):
        claude_home = self.scratch / "claude home;$(touch SHOULD_NOT_EXIST);'quote"
        result = self.install(claude_home)

        self.assertEqual(result.returncode, 0, result.stderr)
        settings = self.settings(claude_home)
        commands = [
            hook["command"]
            for entries in settings["hooks"].values()
            for entry in entries
            for hook in entry["hooks"]
        ]
        environment = os.environ.copy()
        environment["CODEBASE_MEMORY_BIN"] = str(self.scratch / "missing")
        outputs = [
            subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                env=environment,
                cwd=self.scratch,
            )
            for command in commands
        ]
        self.assertTrue(all(item.returncode == 0 for item in outputs))
        self.assertEqual(outputs[0].stdout, "")
        expected_reminder = (SKILL / "reminder.md").read_text(encoding="utf-8")
        self.assertTrue(all(item.stdout == expected_reminder for item in outputs[1:]))
        self.assertFalse((self.scratch / "SHOULD_NOT_EXIST").exists())

    def test_copied_skill_uses_home_for_the_default_claude_home(self):
        home = self.scratch / "home"
        installed_skill = home / ".claude" / "skills" / "codebase-memory"
        installed_skill.parent.mkdir(parents=True)
        shutil.copytree(SKILL, installed_skill)
        environment = os.environ.copy()
        environment["HOME"] = str(home)

        result = subprocess.run(
            ["python3", str(installed_skill / "scripts" / "install.py")],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((home / ".claude" / "settings.json").is_file())
        for relative in (
            "SKILL.md",
            "scripts/install.py",
            "config/claude-settings.json",
            "reminder.md",
            "hooks/cbm-code-discovery-gate",
            "hooks/cbm-session-reminder",
        ):
            self.assertEqual(
                installed_skill.joinpath(relative).read_bytes(),
                SKILL.joinpath(relative).read_bytes(),
            )

    def test_pack_guidance_points_to_the_single_discovery_policy_and_activation(self):
        reminder = (SKILL / "reminder.md").read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        profile = (ROOT / "profile" / "base.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        overlay = (ROOT / "docs" / "overlay.md").read_text(encoding="utf-8")
        validator = (ROOT / "scripts" / "validate.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        normalized_reminder = " ".join(reminder.split())
        for phrase in (
            "against exactly one project",
            "configuration, non-code files, and unindexed projects",
            "Activating this skill never indexes a project",
        ):
            self.assertIn(phrase, normalized_reminder)
        self.assertIn("[reminder.md](reminder.md)", skill)
        self.assertNotIn("Use the graph for structural code discovery", skill)
        self.assertNotIn("Use `index_repository` only", skill)
        self.assertIn("~/.claude/skills/codebase-memory/reminder.md", profile)
        self.assertIn("python3 ~/.claude/skills/codebase-memory/scripts/install.py", readme)
        self.assertIn("--settings-file", skill)
        self.assertIn("portable skill-owned hooks", overlay.lower())
        self.assertIn('"tools/codebase-memory"', validator)
        self.assertIn("tests.test_codebase_memory_install", workflow)
        self.assertIn("skills/tools/codebase-memory/scripts/install.py", workflow)
        self.assertIn("tests.test_codebase_memory_install", agents)


if __name__ == "__main__":
    unittest.main()
