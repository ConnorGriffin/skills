#!/usr/bin/env node

import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const directory = path.dirname(fileURLToPath(import.meta.url));
const driver = path.join(directory, "driver.mjs");
const page =
  "data:text/html," +
  encodeURIComponent(
    '<h1 id="ready">Ready</h1><button id="go" onclick="this.textContent=\'Clicked\'">Go</button>',
  );
const commands = [
  `nav ${page}`,
  "wait-for #ready",
  "click #go",
  'eval document.querySelector("#go").textContent',
  "console --errors",
  "",
].join("\n");

const child = spawn(process.execPath, [driver], {
  stdio: ["pipe", "pipe", "inherit"],
});
let output = "";
child.stdout.setEncoding("utf8");
child.stdout.on("data", (chunk) => {
  output += chunk;
  process.stdout.write(chunk);
});
child.stdin.end(commands);

child.on("exit", (status) => {
  const expected = [
    "OK wait-for #ready",
    'OK eval -> "Clicked"',
    "CONSOLE_ERRORS []",
  ];
  if (status !== 0 || expected.some((line) => !output.includes(line))) {
    console.error("SELF_CHECK_FAILED");
    process.exit(1);
  }
  console.log("SELF_CHECK_OK");
});
