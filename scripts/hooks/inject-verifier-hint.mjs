#!/usr/bin/env node
/**
 * UserPromptSubmit hook — nudge the agent to start the verifier loop when
 * claims have been emitted but no loop is draining them.
 *
 * Input (stdin, JSON): { session_id, prompt, ... }
 * Output (stdout, JSON): { hookSpecificOutput: { hookEventName: 'UserPromptSubmit', additionalContext: '...' } }
 *
 * Signal flow:
 *  - core/verify.py::emit_claim writes workspace/research/verifier-wanted
 *    ({ ts, claimId }) each time a claim is recorded.
 *  - This hook writes workspace/research/.verifier-informed after nudging.
 *  - We only nudge when wanted.ts > informed.ts — that silences the hook
 *    between prompts within the same claim burst, while still firing on
 *    every fresh claim if the agent hasn't started the loop yet.
 *
 * The hook cannot start a /loop directly (that's a slash command the
 * main agent invokes); it just surfaces the hint.
 */

import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { safeMain } from './_safe.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const RESEARCH_DIR = join(PROJECT_ROOT, 'workspace', 'research');
const WANTED = join(RESEARCH_DIR, 'verifier-wanted');
const INFORMED = join(RESEARCH_DIR, '.verifier-informed');

function readStdinSync() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

function readJson(path) {
  if (!existsSync(path)) return null;
  try { return JSON.parse(readFileSync(path, 'utf8')); } catch { return null; }
}

function main() {
  readStdinSync();

  const wanted = readJson(WANTED);
  if (!wanted || typeof wanted.ts !== 'number') { process.exit(0); }

  const informed = readJson(INFORMED);
  const informedTs = informed && typeof informed.ts === 'number' ? informed.ts : 0;

  if (informedTs >= wanted.ts) { process.exit(0); }

  const claimPart = wanted.claimId ? ` (latest: ${wanted.claimId})` : '';
  const additionalContext =
    `Verifier queue has pending claim(s)${claimPart}. ` +
    `If no /verifier loop is running yet this session, start one: ` +
    `\`/loop 60s /verifier\`. It drains the queue via isolated subagents.`;

  writeFileSync(INFORMED, JSON.stringify({ ts: wanted.ts }));

  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext,
    },
  }));
  process.exit(0);
}

safeMain(main, import.meta.url);
