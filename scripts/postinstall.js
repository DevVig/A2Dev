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

  // Policies, semgrep, templates
  for (const sub of ['policies', 'semgrep', 'templates']) {
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
  // Codex harness assets (system prompt + tools)
  try {
    const codexDir = path.join(dest, '.a2dev', 'codex');
    fs.mkdirSync(codexDir, { recursive: true });
    const sysPrompt = [
      'You are the A2Dev PM/Analyst/sPM assistant. Tools are available. Routing policy:',
      '- If a user message starts with @analyst/@pm/@spm/@dev or with *, ALWAYS call the route tool with the full text unchanged.',
      '- If the message is not prefixed and an active role exists in .a2dev/state.json, prepend @<active_role> and call route.',
      "- If no active role exists, call route with '@analyst' to begin assessment.",
      'Keep responses concise, include next‑step options, and never simulate tool behavior.',
      'Always print one short status line and persist artifacts under docs/* and docs/timeline/.',
      ''
    ].join('\n');
    const spPath = path.join(codexDir, 'system-prompt.txt');
    if (!fs.existsSync(spPath)) fs.writeFileSync(spPath, sysPrompt);
    const nodeTools = {
      route: {
        name: 'route',
        description: 'Conversational router for @role and *commands',
        parameters: { type: 'object', properties: { text: { type: 'string' } }, required: ['text'] },
        run: 'node node_modules/a2dev/bin/a2dev.js route "{{text}}"',
        env: { A2DEV_OUTPUT: 'json' }
      },
      pm_next: {
        name: 'pm_next', description: 'PM picks the next story and prepares it',
        parameters: { type: 'object', properties: { scaffold: { type: 'boolean', default: false } } },
        run: 'node node_modules/a2dev/bin/a2dev.js pm next {{#if scaffold}}--scaffold{{/if}}'
      },
      pm_continue: {
        name: 'pm_continue', description: 'PM continues the current story or picks next',
        parameters: { type: 'object', properties: { scaffold: { type: 'boolean', default: false } } },
        run: 'node node_modules/a2dev/bin/a2dev.js pm continue {{#if scaffold}}--scaffold{{/if}}'
      },
      pm_story: {
        name: 'pm_story', description: 'PM prepares a specific story id',
        parameters: { type: 'object', properties: { id: { type: 'integer' }, scaffold: { type: 'boolean', default: false } }, required: ['id'] },
        run: 'node node_modules/a2dev/bin/a2dev.js pm story {{id}} {{#if scaffold}}--scaffold{{/if}}'
      },
      assess: {
        name: 'assess', description: 'Analyst produces brief + backlog; advances phase',
        parameters: { type: 'object', properties: { prd_path: { type: 'string' } }, required: ['prd_path'] },
        run: 'node node_modules/a2dev/bin/a2dev.js assess {{prd_path}}'
      },
      develop: {
        name: 'develop', description: 'PM runs full develop pipeline for a story',
        parameters: { type: 'object', properties: { story_id: { type: 'integer' } }, required: ['story_id'] },
        run: 'node node_modules/a2dev/bin/a2dev.js develop {{story_id}}'
      },
      sustain: {
        name: 'sustain', description: 'sPM runs sustainment gate',
        parameters: { type: 'object', properties: { story_id: { type: 'integer' } }, required: ['story_id'] },
        run: 'node node_modules/a2dev/bin/a2dev.js sustain {{story_id}}'
      },
      gate_check: {
        name: 'gate_check', description: 'Check gates and return issues',
        parameters: { type: 'object', properties: { story_id: { type: 'integer' } }, required: ['story_id'] },
        run: 'node node_modules/a2dev/bin/a2dev.js gate {{story_id}}'
      },
      timeline: {
        name: 'timeline', description: 'Show assess or story timeline',
        parameters: { type: 'object', properties: { target: { type: 'string' } }, required: ['target'] },
        run: 'node node_modules/a2dev/bin/a2dev.js timeline {{target}}'
      },
      pm_sprints: {
        name: 'pm_sprints', description: 'Plan sprints from the backlog',
        parameters: { type: 'object', properties: { capacity: { type: 'number', default: 20 }, weeks: { type: 'integer', default: 2 } } },
        run: 'node node_modules/a2dev/bin/a2dev.js pm-sprints --capacity {{capacity}} --weeks {{weeks}}'
      }
    };
    const nodePath = path.join(codexDir, 'tools.node.json');
    if (!fs.existsSync(nodePath)) fs.writeFileSync(nodePath, JSON.stringify(nodeTools, null, 2));
    const pyTools = JSON.parse(JSON.stringify(nodeTools));
    for (const k of Object.keys(pyTools)) {
      pyTools[k].run = pyTools[k].run.replace('node node_modules/a2dev/bin/a2dev.js', 'python3 a2dev_cli.py');
    }
    const pyPath = path.join(codexDir, 'tools.python.json');
    if (!fs.existsSync(pyPath)) fs.writeFileSync(pyPath, JSON.stringify(pyTools, null, 2));
    const readme = [
      '# Codex Integration (A2Dev)',
      '',
      'This project is preconfigured for Codex (CLI/Web). Import these once, then just chat with `@analyst`, `@pm`, `@spm`.',
      '',
      '## System Prompt',
      'Use: `.a2dev/codex/system-prompt.txt` as your system message.',
      '',
      '## Tools',
      'Prefer Node tools: `.a2dev/codex/tools.node.json` (runs `node node_modules/a2dev/bin/a2dev.js ...`).',
      '',
      'Alternative Python tools: `.a2dev/codex/tools.python.json` (runs `python3 a2dev_cli.py ...`).',
      '',
      'Required tool: `route` — forward any message starting with `@analyst/@pm/@spm/@dev` or `*` to this tool with the full text.',
      '',
      '## Behavior',
      '- The router persists the active role in `.a2dev/state.json`.',
      '- Unprefixed messages should be forwarded to `@<active_role>` via the route tool.',
      '- After setup, users simply type `@analyst` to get the greeting and options.'
    ].join('\n');
    const readmePath = path.join(codexDir, 'README.md');
    if (!fs.existsSync(readmePath)) fs.writeFileSync(readmePath, readme);
  } catch (e) {
    console.warn('[A2Dev] Could not write Codex assets:', e.message);
  }
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
