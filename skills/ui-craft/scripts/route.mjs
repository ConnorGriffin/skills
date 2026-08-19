const VALID_EMBODIMENTS = new Set(['greenfield', 'shipped']);
const VALID_DECLARATIONS = new Set(['absent', 'complete', 'incomplete', 'ambiguous']);
const SAFE_DATA_SOURCES = new Set(['manufactured', 'synthetic']);

export function routeSurface({ embodiment, declaration, dataSource }) {
  if (!VALID_EMBODIMENTS.has(embodiment)) {
    return refusal('embodiment must be greenfield or shipped');
  }

  if (embodiment === 'greenfield') {
    return { mode: 'lock', reason: 'the app has no shipped embodiment' };
  }

  if (!VALID_DECLARATIONS.has(declaration)) {
    return refusal('declaration must be absent, complete, incomplete, or ambiguous');
  }

  if (declaration === 'absent') {
    return {
      mode: 'lock-fallback',
      reason: 'no dev-server declaration; record the weaker predecessor fallback',
    };
  }

  if (declaration !== 'complete') {
    return refusal('the declared entrypoint is incomplete or ambiguous');
  }

  if (!SAFE_DATA_SOURCES.has(dataSource)) {
    return refusal('revise requires a manufactured fixture or synthetic database');
  }

  return { mode: 'revise', reason: `safe ${dataSource} data source declared` };
}

function refusal(reason) {
  return { mode: 'refuse', reason };
}

function parseArgs(argv) {
  const parsed = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag?.startsWith('--') || value === undefined) {
      throw new Error('usage: route.mjs --embodiment <greenfield|shipped> --declaration <absent|complete|incomplete|ambiguous> --data-source <manufactured|synthetic|unknown>');
    }
    parsed[flag.slice(2)] = value;
  }
  return {
    embodiment: parsed.embodiment,
    declaration: parsed.declaration,
    dataSource: parsed['data-source'],
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const result = routeSurface(parseArgs(process.argv.slice(2)));
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (result.mode === 'refuse') process.exitCode = 2;
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 2;
  }
}
