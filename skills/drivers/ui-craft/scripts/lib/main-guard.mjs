/**
 * Decide whether a module is the process entry point ("was I run directly?").
 *
 * Why realpath on both sides: skill directories are reached through symlinks
 * (the normal install path links the pack into the agent's skills directory).
 * Node resolves `import.meta.url` to the real file while `process.argv[1]`
 * keeps the symlink path, so a raw string comparison is false through a link
 * and the CLI exits 0 without ever running — a silent no-op, not an error.
 *
 * Why realpath rather than `endsWith()`: a loose suffix match also fires for an
 * unrelated script whose filename ends the same way (any `*-context.mjs` would
 * satisfy an `endsWith('context.mjs')` test), running the wrong CLI.
 */

import fs from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

export function isMainModule(moduleUrl) {
  const entry = process.argv[1];
  if (!entry) return false;
  try {
    return fs.realpathSync(entry) === fs.realpathSync(fileURLToPath(moduleUrl));
  } catch {
    // pathToFileURL normalizes Windows paths; keep it as a fallback for any
    // environment where realpath is unavailable.
    return moduleUrl === pathToFileURL(entry).href;
  }
}
