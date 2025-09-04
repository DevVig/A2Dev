#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const { existsSync } = require('node:fs');
const { join, resolve } = require('node:path');

function which(cmd) {
  const sep = process.platform === 'win32' ? ';' : ':';
  const exts = process.platform === 'win32' ? (process.env.PATHEXT || '.EXE').split(';') : [''];
  for (const p of (process.env.PATH || '').split(sep)) {
    const base = join(p, cmd);
    for (const ext of exts) {
      const f = base + ext.toLowerCase();
      try { require('node:fs').accessSync(f); return f; } catch {}
    }
  }
  return null;
}

function run(cmd, args) {
  const res = spawnSync(cmd, args, { stdio: 'inherit' });
  process.exit(res.status ?? 1);
}

(function main() {
  const cwd = process.cwd();
  const args = process.argv.slice(2);
  const pkgRoot = resolve(__dirname, '..');
  // Special-case "install" first to ensure init works even if local pyz is stale
  if (args[0] === 'install') {
    const cliLocal = join(cwd, 'a2dev_cli.py');
    const cliPkg = join(pkgRoot, 'a2dev_cli.py');
    const cli = existsSync(cliLocal) ? cliLocal : cliPkg;
    const py = which('python3') || which('python') || process.env.PYTHON || 'python3';
    return run(py, [cli, 'install', '--dest', cwd]);
  }
  // Prefer pyz if present for portability
  const pyzLocal = join(cwd, 'a2dev.pyz');
  const pyzPkg = join(pkgRoot, 'a2dev.pyz');
  if (existsSync(pyzLocal)) {
    const py = which('python3') || which('python') || process.env.PYTHON || 'python3';
    return run(py, [pyzLocal, ...args]);
  }
  if (existsSync(pyzPkg)) {
    const py = which('python3') || which('python') || process.env.PYTHON || 'python3';
    return run(py, [pyzPkg, ...args]);
  }
  // Fallback to CLI script
  const cliLocal = join(cwd, 'a2dev_cli.py');
  const cliPkg = join(pkgRoot, 'a2dev_cli.py');
  const py = which('python3') || which('python') || process.env.PYTHON || 'python3';
  if (existsSync(cliLocal)) {
    return run(py, [cliLocal, ...args]);
  }
  if (existsSync(cliPkg)) {
    return run(py, [cliPkg, ...args]);
  }
  // Last resort: a2a/cli module if installed as a package
  // node cannot import python; instruct user.
  console.error('Could not find a2dev runner. Try:\n  - npx a2dev install\n  - or run in a project with a2dev_cli.py / a2dev.pyz available');
  process.exit(1);
})();
