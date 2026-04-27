#!/usr/bin/env node
/**
 * SessionStart hook — inject a compact block of session context so the
 * agent opens each session knowing the active goal, phase, staleness,
 * verifier backlog, and output-pool state without having to ask.
 *
 * Input (stdin, JSON): { session_id, source, ... }
 * Output (stdout, JSON): { hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: '...' } }
 *
 * Signals (read from workspace/research/ and workspace/output/):
 *   1. session.json  -> goal, phase, staleness
 *   2. verification.log  -> pending-claims count (claims without results)
 *   3. workspace/output/ file count -> nudge cleanup when > OUTPUT_NUDGE_AT
 *
 * Always fires. Stays to one line when there's nothing active to decide
 * (per trial-1-report's invisibility principle — visible only when useful).
 */

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { safeMain } from './_safe.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const RESEARCH_DIR = join(PROJECT_ROOT, 'workspace', 'research');
const OUTPUT_DIR = join(PROJECT_ROOT, 'workspace', 'output');
const SESSION_PATH = join(RESEARCH_DIR, 'session.json');
const VERIFICATION_LOG = join(RESEARCH_DIR, 'verification.log');
const OUTPUT_NUDGE_AT = 8;
// More than 24h old = "stale" — prompt to re-confirm the goal.
const STALE_HOURS = 24;

function readStdinSync() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

function parseIsoToMs(iso) {
  const t = Date.parse(iso);
  return Number.isFinite(t) ? t : null;
}

function humanHoursAgo(ms) {
  const hours = (Date.now() - ms) / 3_600_000;
  if (hours < 1) {
    const mins = Math.max(1, Math.round(hours * 60));
    return `${mins}m ago`;
  }
  if (hours < 48) return `${Math.round(hours)}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function readSession() {
  if (!existsSync(SESSION_PATH)) return null;
  try { return JSON.parse(readFileSync(SESSION_PATH, 'utf8')); }
  catch { return null; }
}

function countPendingClaims() {
  if (!existsSync(VERIFICATION_LOG)) return 0;
  let lines;
  try {
    lines = readFileSync(VERIFICATION_LOG, 'utf8').split('\n').filter(Boolean);
  } catch { return 0; }
  const claims = new Set();
  const resolved = new Set();
  for (const line of lines) {
    let e;
    try { e = JSON.parse(line); } catch { continue; }
    if (e.type === 'claim' && e.id) claims.add(e.id);
    if (e.type === 'result' && e.claimId) resolved.add(e.claimId);
  }
  let count = 0;
  for (const id of claims) if (!resolved.has(id)) count += 1;
  return count;
}

function countOutputTabs() {
  if (!existsSync(OUTPUT_DIR)) return 0;
  let entries;
  try { entries = readdirSync(OUTPUT_DIR); } catch { return 0; }
  // Count only rendered-tab files (.html/.png/.svg/.pdf), skip dotfiles + subdirs.
  let n = 0;
  for (const name of entries) {
    if (name.startsWith('.')) continue;
    const full = join(OUTPUT_DIR, name);
    try {
      if (!statSync(full).isFile()) continue;
    } catch { continue; }
    if (/\.(html?|png|svg|jpe?g|pdf)$/i.test(name)) n += 1;
  }
  return n;
}

function buildContext() {
  const session = readSession();
  const pending = countPendingClaims();
  const tabs = countOutputTabs();

  const lines = [];
  let anyActive = false;

  if (session) {
    const lastMs = parseIsoToMs(session.lastActive || session.setAt);
    const ago = lastMs ? humanHoursAgo(lastMs) : 'unknown';
    const stale = lastMs ? (Date.now() - lastMs) / 3_600_000 > STALE_HOURS : false;
    const goal = (session.goal || '').slice(0, 140);
    const phase = session.phase || 'unknown';
    if (stale) {
      lines.push(`Previous goal: "${goal}" (phase: ${phase}, last active ${ago}) — still relevant, or new direction?`);
    } else {
      lines.push(`Goal: "${goal}" (phase: ${phase}, last active ${ago})`);
    }
    anyActive = true;
  } else {
    lines.push('No active goal. /first-boot Stage 2 elicits one; or dive in and it\'ll crystallize later.');
  }

  if (pending > 0) {
    lines.push(`Verifier queue: ${pending} pending claim${pending === 1 ? '' : 's'} — start /loop 60s /verifier to drain.`);
    anyActive = true;
  }

  if (tabs > OUTPUT_NUDGE_AT) {
    lines.push(`Output pool: ${tabs} tabs — consider cleanup_displays(keep=['research']) when this phase ends.`);
    anyActive = true;
  }

  // When nothing is active, keep it to a single line.
  if (!anyActive) return lines[0];
  return 'Session context:\n- ' + lines.join('\n- ');
}

function main() {
  readStdinSync();  // drain stdin; we don't need its content
  const additionalContext = buildContext();
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext,
    },
  }));
  process.exit(0);
}

safeMain(main, import.meta.url);
