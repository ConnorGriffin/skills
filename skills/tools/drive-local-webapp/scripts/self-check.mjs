#!/usr/bin/env node

import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import path from "node:path";

const directory = path.dirname(fileURLToPath(import.meta.url));
const driver = path.join(directory, "driver.mjs");
const page =
  "data:text/html," +
  encodeURIComponent(
    '<h1 id="ready">Ready</h1><button id="go" onclick="this.textContent=\'Clicked\'">Go</button>',
  );

function runDriver(commands) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [driver], {
      stdio: ["pipe", "pipe", "inherit"],
    });
    let output = "";
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      output += chunk;
      process.stdout.write(chunk);
    });
    child.on("error", reject);
    child.on("exit", (status) => resolve({ output, status }));
    child.stdin.end([...commands, ""].join("\n"));
  });
}

const success = await runDriver([
  `nav ${page}`,
  "wait-for #ready",
  "click #go",
  'eval document.querySelector("#go").textContent',
  "console --errors",
]);
const expected = [
  "OK wait-for #ready",
  'OK eval -> "Clicked"',
  "CONSOLE_ERRORS []",
];
if (
  success.status !== 0 ||
  expected.some((line) => !success.output.includes(line))
) {
  console.error("SELF_CHECK_FAILED");
  process.exit(1);
}

const scratch = await mkdtemp(path.join(tmpdir(), "drive-local-webapp-check-"));
const existing = path.join(scratch, "existing.png");
await writeFile(existing, "sentinel", "utf8");
const overwrite = await runDriver([
  `nav ${page}`,
  `screenshot ${existing}`,
]);
const unchanged = await readFile(existing, "utf8");
await rm(scratch, { recursive: true });
if (
  overwrite.status === 0 ||
  !overwrite.output.includes("screenshot path already exists") ||
  unchanged !== "sentinel"
) {
  console.error("SELF_CHECK_OVERWRITE_FAILED");
  process.exit(1);
}

console.log("SELF_CHECK_OK");
