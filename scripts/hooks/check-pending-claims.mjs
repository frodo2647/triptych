#!/usr/bin/env node
/**
 * Stop hook — when the main agent stops for the turn, check whether there
 * are claims in the verification log that don't yet have a matching result.
 * If so, inject a reminder so the final response makes the state visible
 * rather than letting the agent silently wind down with a dirty queue.
 *
 * Input (stdin, JSON): { session_id, stop_hook_active, ... }
 * Output (stdout, JSON): { systemMessage: '...' }
 *
 * Stop hooks don't support hookSpecificOutput -- the validator rejects it.
 * systemMessage is the visible-but-non-blocking field, which matches what
 * we want: nudge the agent, don't block the stop.
 *
 * This is the end-of-turn complement to inject-verifier-hint.mjs (which
 * nudges at the start of a turn). Together they close the loop: the agent
 * is reminded to start the verifier when claims land, and reminded that
 * unverified claims remain when the turn ends.
 *
 * Behavior: non-blocking (never returns decision: 'block'), silent when
 * the queue is empty. The audit that prompted this hook explicitly noted
 * the risk of the verifier loop not running -- we surface the state, the
 * agent decides what to do.
 */

import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { safeMain } from './_safe.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const VERIFICATION_LOG = join(PROJECT_ROOT, 'workspace', 'research', 'verification.log');

function readStdinSync() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

function main() {
  // Respect stop_hook_active to avoid infinite loops if the agent
  // continues work because of our reminder.
  let payload;
  try { payload = JSON.parse(readStdinSync()); } catch { payload = {}; }
  if (payload?.stop_hook_active) { process.exit(0); }

  if (!existsSync(VERIFICATION_LOG)) { process.exit(0); }

  let entries;
  try {
    entries = readFileSync(VERIFICATION_LOG, 'utf8')
      .split('\n')
      .filter(Boolean)
      .map(line => { try { return JSON.parse(line); } catch { return null; } })
      .filter(Boolean);
  } catch { process.exit(0); }

  const claims = new Set();
  const resolved = new Set();
  for (const e of entries) {
    if (e.type === 'claim' && e.id) claims.add(e.id);
    if (e.type === 'result' && e.claimId) resolved.add(e.claimId);
  }

  const pending = [...claims].filter(id => !resolved.has(id));
  if (!pending.length) { process.exit(0); }

  const list = pending.length <= 5 ? pending.join(', ') : pending.slice(0, 5).join(', ') + `, … (+${pending.length - 5})`;
  const systemMessage =
    `Before ending: ${pending.length} claim(s) still unverified — ${list}. ` +
    `If the /verifier loop isn't running, start it (\`/loop 60s /verifier\`) ` +
    `or acknowledge the pending state in your final message.`;

  process.stdout.write(JSON.stringify({ systemMessage }));
  process.exit(0);
}

safeMain(main, import.meta.url);
