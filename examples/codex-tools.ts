// Example: Wiring A2Dev tools in a Codex harness (TypeScript-ish pseudo-code)
// Assumes your harness supports tool registration with a run shell hook.

type Tool = {
  name: string;
  description: string;
  parameters: any;
  run: (args: Record<string, any>) => Promise<{ stdout: string; stderr?: string }>;
};

import { spawn } from 'node:child_process';

function spawnCollect(cmd: string, args: string[]) {
  return new Promise<{ stdout: string; stderr?: string; code: number }>((resolve) => {
    const p = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '';
    let err = '';
    p.stdout.on('data', (d) => (out += d.toString()));
    p.stderr.on('data', (d) => (err += d.toString()));
    p.on('error', () => resolve({ stdout: out, stderr: err, code: 127 }));
    p.on('close', (code) => resolve({ stdout: out, stderr: err, code: code ?? 1 }));
  });
}

async function runCli(args: string[]): Promise<{ stdout: string; stderr?: string }> {
  // Prefer Node wrapper (a2dev). Fallback to Python shim if not installed.
  const nodeTry = await spawnCollect('a2dev', args);
  if (nodeTry.code === 0 || nodeTry.code === 2 /* argparse usage */) return { stdout: nodeTry.stdout, stderr: nodeTry.stderr };
  const pyTry = await spawnCollect('python3', ['a2dev_cli.py', ...args]);
  return { stdout: pyTry.stdout, stderr: pyTry.stderr };
}

export const tools: Tool[] = [
  {
    name: 'route',
    description: 'Conversational router (@role/*)',
    parameters: { type: 'object', properties: { text: { type: 'string' } }, required: ['text'] },
    run: ({ text }) => runCli(['route', String(text)]),
  },
  {
    name: 'pm_next',
    description: 'PM picks next story and prepares it',
    parameters: { type: 'object', properties: { scaffold: { type: 'boolean', default: false } } },
    run: ({ scaffold }) => runCli(['pm', 'next', ...(scaffold ? ['--scaffold'] : [])]),
  },
  {
    name: 'pm_continue',
    description: 'PM continues current story or picks next',
    parameters: { type: 'object', properties: { scaffold: { type: 'boolean', default: false } } },
    run: ({ scaffold }) => runCli(['pm', 'continue', ...(scaffold ? ['--scaffold'] : [])]),
  },
  {
    name: 'pm_story',
    description: 'PM prepares a specific story id',
    parameters: { type: 'object', properties: { id: { type: 'integer' }, scaffold: { type: 'boolean' } }, required: ['id'] },
    run: ({ id, scaffold }) => runCli(['pm', 'story', String(id), ...(scaffold ? ['--scaffold'] : [])]),
  },
  {
    name: 'assess',
    description: 'Analyst produces brief + backlog; advances phase',
    parameters: { type: 'object', properties: { prd_path: { type: 'string' } }, required: ['prd_path'] },
    run: ({ prd_path }) => runCli(['assess', String(prd_path)]),
  },
  {
    name: 'develop',
    description: 'PM runs full develop pipeline for a story',
    parameters: { type: 'object', properties: { story_id: { type: 'integer' } }, required: ['story_id'] },
    run: ({ story_id }) => runCli(['develop', String(story_id)]),
  },
  {
    name: 'sustain',
    description: 'sPM runs sustainment gate',
    parameters: { type: 'object', properties: { story_id: { type: 'integer' } }, required: ['story_id'] },
    run: ({ story_id }) => runCli(['sustain', String(story_id)]),
  },
  {
    name: 'gate_check',
    description: 'Check gates and return issues',
    parameters: { type: 'object', properties: { story_id: { type: 'integer' } }, required: ['story_id'] },
    run: ({ story_id }) => runCli(['gate', String(story_id)]),
  },
  {
    name: 'timeline',
    description: 'Show assess or story timeline',
    parameters: { type: 'object', properties: { target: { type: 'string' } }, required: ['target'] },
    run: ({ target }) => runCli(['timeline', String(target)]),
  },
  {
    name: 'pm_sprints',
    description: 'Plan sprints from the backlog',
    parameters: { type: 'object', properties: { capacity: { type: 'number', default: 20 }, weeks: { type: 'integer', default: 2 } } },
    run: ({ capacity = 20, weeks = 2 }) => runCli(['pm-sprints', '--capacity', String(capacity), '--weeks', String(weeks)]),
  },
];

// In your harness: register these tools, and in your system prompt instruct the model
// to call `route` for messages starting with @analyst/@pm/@dev/@spm or *.
