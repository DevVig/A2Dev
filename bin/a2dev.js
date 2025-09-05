#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const { existsSync, readFileSync } = require('node:fs');
const { join, resolve } = require('node:path');

function loadEnvLocal() {
  try {
    const candidates = [join(process.cwd(), '.env.local'), join(__dirname, '..', '.env.local')];
    for (const p of candidates) {
      try {
        if (!existsSync(p)) continue;
        const content = readFileSync(p, 'utf8');
        for (const raw of content.split(/\r?\n/)) {
          const line = raw.trim();
          if (!line || line.startsWith('#') || !line.includes('=')) continue;
          const idx = line.indexOf('=');
          const key = line.slice(0, idx).trim();
          let val = line.slice(idx + 1).trim();
          if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
            val = val.slice(1, -1);
          }
          if (!(key in process.env)) process.env[key] = val;
        }
      } catch {}
    }
  } catch {}
}

loadEnvLocal();

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
  // Special-case "install" first to ensure init works even if local copies are partial.
  // Always use the packaged CLI for install to avoid missing deps (e.g., local a2dev_cli.py without a2a/).
  if (args[0] === 'install') {
    const cliPkg = join(pkgRoot, 'a2dev_cli.py');
    const py = which('python3') || which('python') || process.env.PYTHON || 'python3';
    return run(py, [cliPkg, 'install', '--dest', cwd]);
  }
  // Prefer pyz if present for portability
  const pyzLocal = join(cwd, 'a2dev.pyz');
  const pyzPkg = join(pkgRoot, 'a2dev.pyz');
  const py = which('python3') || which('python') || process.env.PYTHON || 'python3';
  function tryRun(cmd, args) {
    const r = spawnSync(cmd, args, { stdio: 'pipe' });
    if ((r.status ?? 1) === 0) {
      if (r.stdout) process.stdout.write(r.stdout);
      if (r.stderr) process.stderr.write(r.stderr);
      process.exit(0);
    }
  }
  if (existsSync(pyzLocal)) {
    tryRun(py, [pyzLocal, ...args]);
  }
  if (existsSync(pyzPkg)) {
    tryRun(py, [pyzPkg, ...args]);
  }
  // Fallback to CLI script
  const cliLocal = join(cwd, 'a2dev_cli.py');
  const cliPkg = join(pkgRoot, 'a2dev_cli.py');
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
