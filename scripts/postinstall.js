#!/usr/bin/env node
/*
 Postinstall to initialize A2Dev files into the consuming project.
 - Uses npm's INIT_CWD to detect the caller's project root.
 - Copies baseline artifacts only if missing (idempotent).
*/
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');

function loadEnvLocal() {
  try {
    const candidates = [path.join(process.cwd(), '.env.local'), path.join(__dirname, '..', '.env.local')];
    for (const p of candidates) {
      try {
        if (!fs.existsSync(p)) continue;
        const content = fs.readFileSync(p, 'utf8');
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

function copyIfAbsent(src, dst) {
  if (!fs.existsSync(src)) return;
  if (fs.existsSync(dst)) return;
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  if (fs.statSync(src).isDirectory()) {
    fs.mkdirSync(dst, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      copyIfAbsent(path.join(src, entry), path.join(dst, entry));
    }
  } else {
    fs.copyFileSync(src, dst);
  }
}

function main() {
  loadEnvLocal();
  const dest = process.env.INIT_CWD || process.cwd();
  const pkgRoot = __dirname ? path.resolve(__dirname, '..') : process.cwd();

  // Core dirs at dest
  fs.mkdirSync(path.join(dest, '.a2dev'), { recursive: true });
  fs.mkdirSync(path.join(dest, 'docs'), { recursive: true });
  fs.mkdirSync(path.join(dest, 'docs', 'ux'), { recursive: true });

  // Policies & semgrep
  for (const sub of ['policies', 'semgrep']) {
    const srcDir = path.join(pkgRoot, '.a2dev', sub);
    if (fs.existsSync(srcDir)) {
      for (const entry of fs.readdirSync(srcDir)) {
        copyIfAbsent(path.join(srcDir, entry), path.join(dest, '.a2dev', sub, entry));
      }
    }
  }

  // PR template
  copyIfAbsent(path.join(pkgRoot, '.github', 'pull_request_template.md'), path.join(dest, '.github', 'pull_request_template.md'));

  // Sample PRD -> PRD.md (if missing)
  const prdDst = path.join(dest, 'docs', 'PRD.md');
  if (!fs.existsSync(prdDst)) {
    copyIfAbsent(path.join(pkgRoot, 'docs', 'PRD_SAMPLE.md'), prdDst);
  }

  // CLI shims
  copyIfAbsent(path.join(pkgRoot, 'a2dev_cli.py'), path.join(dest, 'a2dev_cli.py'));
  copyIfAbsent(path.join(pkgRoot, 'a2a_cli.py'), path.join(dest, 'a2a_cli.py'));
  // AGENTS.md
  copyIfAbsent(path.join(pkgRoot, 'AGENTS.md'), path.join(dest, 'AGENTS.md'));
  // Env example (do not auto‑create .env.local)
  copyIfAbsent(path.join(pkgRoot, '.env.example'), path.join(dest, '.env.example'));

  console.log(`[A2Dev] Initialized into ${dest}`);

  // Optional: run a local smoke test after install when enabled
  if (process.env.A2DEV_POSTINSTALL_SMOKE === 'true') {
    try {
      console.log('[A2Dev] Running postinstall smoke test (A2DEV_POSTINSTALL_SMOKE=true)');
      const py = process.env.PYTHON || 'python3';
      const res = spawn(py, [path.join(dest, 'a2dev_cli.py'), 'smoke'], { cwd: dest, stdio: 'inherit' });
      res.on('close', (code) => {
        if (code !== 0) {
          console.warn('[A2Dev] Smoke test exited non-zero. See output above.');
        }
      });
    } catch (e) {
      console.warn('[A2Dev] Postinstall smoke failed to start:', e.message);
    }
  }
}

try { main(); } catch (e) { console.error('[A2Dev] postinstall error:', e); }
