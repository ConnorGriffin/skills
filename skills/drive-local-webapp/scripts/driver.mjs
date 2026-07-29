#!/usr/bin/env node
// Read one browser command per line from stdin and execute it against one page.
//
// Commands:
//   nav <url>
//   wait-for <selector>
//   click <selector>
//   fill <selector> :: <value>
//   set <selector> :: <value>
//   press <key>
//   wait <milliseconds>
//   eval <javascript-expression>
//   screenshot [absolute-path]
//   console --errors

import { chromium } from "playwright";
import { createInterface } from "node:readline";
import { mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const screenshotDir =
  process.env.DRIVER_SCREENSHOT_DIR ||
  path.join(tmpdir(), "drive-local-webapp");
const consoleErrors = [];
let shotCount = 0;

function selector(value) {
  return value.startsWith("text=") ? `text=${value.slice(5)}` : value;
}

async function launchBrowser() {
  try {
    return await chromium.launch();
  } catch (error) {
    const detail = String(error?.message || error);
    const macPermissionError =
      process.platform === "darwin" &&
      /MachPortRendezvous|bootstrap_check_in/.test(detail) &&
      /Permission denied \(1100\)/.test(detail);
    if (!macPermissionError) throw error;

    try {
      return await chromium.launch({
        args: ["--no-sandbox", "--single-process"],
      });
    } catch (fallbackError) {
      console.error(
        "HEADLESS-SANDBOX-BLOCKED: rerun this driver with the host client's " +
          "narrow approval for starting Chromium.\n" +
          String(fallbackError?.message || fallbackError),
      );
      process.exit(77);
    }
  }
}

async function main() {
  const browser = await launchBrowser();
  const page = await browser.newPage();
  let failed = false;

  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(String(error)));

  const input = createInterface({ input: process.stdin, terminal: false });
  for await (const rawLine of input) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;

    const firstSpace = line.indexOf(" ");
    const command = firstSpace === -1 ? line : line.slice(0, firstSpace);
    const argument =
      firstSpace === -1 ? "" : line.slice(firstSpace + 1).trim();

    try {
      if (command === "nav") {
        await page.goto(argument, { waitUntil: "domcontentloaded" });
        console.log(`OK nav ${argument}`);
      } else if (command === "wait-for") {
        await page.waitForSelector(selector(argument), { timeout: 15000 });
        console.log(`OK wait-for ${argument}`);
      } else if (command === "click") {
        await page.click(selector(argument), { timeout: 15000 });
        console.log(`OK click ${argument}`);
      } else if (command === "fill" || command === "set") {
        const separator = argument.indexOf(" :: ");
        if (separator === -1) {
          throw new Error(`${command} needs "<selector> :: <value>"`);
        }
        const target = argument.slice(0, separator).trim();
        const value = argument.slice(separator + 4);
        await page.fill(selector(target), value, { timeout: 15000 });
        if (command === "set") {
          await page.dispatchEvent(selector(target), "change");
        }
        console.log(`OK ${command} ${target}`);
      } else if (command === "press") {
        await page.keyboard.press(argument);
        console.log(`OK press ${argument}`);
      } else if (command === "wait") {
        const milliseconds = Number(argument);
        if (!Number.isFinite(milliseconds) || milliseconds < 0) {
          throw new Error("wait needs a non-negative number");
        }
        await page.waitForTimeout(milliseconds);
        console.log(`OK wait ${milliseconds}ms`);
      } else if (command === "eval") {
        const result = await page.evaluate(argument);
        console.log(`OK eval -> ${JSON.stringify(result)}`);
      } else if (command === "screenshot") {
        await mkdir(screenshotDir, { recursive: true });
        shotCount += 1;
        const file =
          argument || path.join(screenshotDir, `${shotCount}.png`);
        if (!path.isAbsolute(file)) {
          throw new Error("screenshot path must be absolute");
        }
        await page.screenshot({ path: file, fullPage: true });
        console.log(`OK screenshot ${file}`);
      } else if (command === "console" && argument === "--errors") {
        console.log(`CONSOLE_ERRORS ${JSON.stringify(consoleErrors)}`);
      } else {
        throw new Error(`unknown command: ${command}`);
      }
    } catch (error) {
      failed = true;
      const summary = String(error?.message || error).split("\n")[0];
      console.log(`FAIL ${line} :: ${summary}`);
    }
  }

  await browser.close();
  process.exit(failed ? 1 : 0);
}

main();
