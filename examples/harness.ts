// Minimal Codex-like harness example for A2Dev tools.
// - Imports tool definitions from codex-tools.ts
// - Provides a simple CLI to invoke tools
// - Demo: route @pm develop 2
//
// Run (with ts-node): npx ts-node examples/harness.ts route '{"text":"@pm develop 2"}'
// Or (interactive): npx ts-node examples/harness.ts
// Note: tools prefer the Node wrapper `a2dev` (via npx or global),
// and will fall back to `python3 a2dev_cli.py` if not available.

import { tools } from './codex-tools';

type Tool = (typeof tools)[number];

const toolMap: Record<string, Tool> = Object.fromEntries(tools.map((t) => [t.name, t]));

async function runTool(name: string, args: Record<string, any>) {
  const t = toolMap[name];
  if (!t) throw new Error(`Unknown tool: ${name}`);
  return t.run(args);
}

async function main() {
  const [,, name, jsonArgs] = process.argv;
  if (name) {
    const args = jsonArgs ? JSON.parse(jsonArgs) : {};
    const { stdout, stderr } = await runTool(name, args);
    if (stderr) process.stderr.write(stderr);
    process.stdout.write(stdout);
    return;
  }

  // Interactive (very simple): route all lines
  process.stdout.write('A2Dev harness interactive mode. Type lines (Ctrl+C to exit)\n');
  process.stdout.write('Examples: @analyst assess docs/PRD.md | @pm develop 2 | *develop 3\n');
  process.stdout.write('> ');
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', async (chunk) => {
    const text = String(chunk).trim();
    if (!text) { process.stdout.write('> '); return; }
    const { stdout, stderr } = await runTool('route', { text });
    if (stderr) process.stderr.write(stderr);
    process.stdout.write(stdout + '\n> ');
  });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
