---
name: drive-local-webapp
description: Launch or connect to a local development web server and drive it with a reusable headless-Chromium command interface. Use when asked to render, smoke-test, interact with, verify, or screenshot a local frontend or HTML mockup.
---

# Drive a local web app

Use the bundled Playwright driver instead of writing a one-off browser script.
It keeps one page alive while reading commands from standard input and reports
each command as `OK` or `FAIL`.

## One-time setup

Resolve this installed skill's directory, then run:

```sh
cd <drive-local-webapp-skill-directory>
npm ci
npx playwright install chromium
```

Node.js 20 or newer is recommended. Browser binaries are cached by Playwright.
Verify the installation reproducibly:

```sh
npm run self-check
```

## Workflow

1. Start the target application's normal development or demo server. Use
   throwaway fixtures, never production or personal data. Check that the chosen
   port is free before binding it.
2. Run `node scripts/driver.mjs` from this skill directory and pipe one command
   per line:

   ```sh
   DRIVER_SCREENSHOT_DIR=/tmp/webapp-shots node scripts/driver.mjs <<'EOF'
   nav http://127.0.0.1:8766/
   wait-for text=Dashboard
   click button:text-is("Settings")
   fill input[placeholder="API token"] :: demo-token
   click button:text-is("Save")
   screenshot
   console --errors
   EOF
   ```

3. Treat any `FAIL` line or non-zero exit as a failed check. Treat a non-empty
   `CONSOLE_ERRORS` array as a failed check unless the error is explicitly
   expected.
4. Inspect the screenshot itself. File existence does not prove the intended UI
   rendered.

If the host sandbox blocks Chromium process creation, rerun the same driver
command with the client's narrowly scoped approval mechanism. Do not reinstall
Chromium or alter the application to work around a host permission error.

Only navigate to a local page you trust or a URL the user explicitly placed in
scope. Headless Chromium is not a security boundary: page JavaScript can make
network requests and exercise the permissions available to the browser process.
Do not use this driver as a general-purpose browser for untrusted sites.

## Commands

```text
nav <url>
wait-for <selector>
click <selector>
fill <selector> :: <value>
set <selector> :: <value>
press <key>
wait <milliseconds>
eval <javascript-expression>
screenshot [absolute-path]
console --errors
```

Use `:text-is("Label")` for exact text. Playwright's `:has-text()` is
case-insensitive substring matching and can silently click the wrong control.

Keep screenshots outside the target repository. The driver defaults to the
system temporary directory, or use `DRIVER_SCREENSHOT_DIR`. It refuses to
overwrite an existing screenshot path.

## Common failures

- Selectors containing spaces require the literal ` :: ` separator for
  `fill` and `set`.
- Hidden tab content may exist in the DOM; click the actual tab before waiting
  on its contents.
- Charts initialized inside `display:none` containers may have zero width.
  Activate the tab, wait, and verify the app resizes or lazily initializes the
  chart.
- A client-side token gate may leave the screen loading without a console
  error. Inspect the application's setup UI and use a demo token.
