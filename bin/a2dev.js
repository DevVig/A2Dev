#!/usr/bin/env node
// Minimal Node wrapper to invoke the Python CLI so users can run: npx a2dev <cmd>
// Tries python from env or falls back to 'python3'.

const { spawnSync } = require('child_process');
const { join } = require('path');
const { existsSync } = require('fs');

function main() {
  const py = process.env.PYTHON || 'python3';
  const pkgRoot = join(__dirname, '..');
  const cliPy = join(pkgRoot, 'a2dev_cli.py');
  const pyz = join(pkgRoot, 'a2dev.pyz');

  let cmdArgs;
  if (existsSync(pyz)) {
    cmdArgs = [pyz, ...process.argv.slice(2)];
  } else if (existsSync(cliPy)) {
    cmdArgs = [cliPy, ...process.argv.slice(2)];
  } else {
    console.error('Could not find a2dev runner. Expected a2dev_cli.py or a2dev.pyz in package root.');
    process.exit(1);
  }

  const res = spawnSync(py, cmdArgs, { stdio: 'inherit' });
  if (res.error) {
    console.error('[a2dev] Failed to start Python:', res.error.message);
    process.exit(1);
  }
  process.exit(res.status ?? 0);
}

main();

