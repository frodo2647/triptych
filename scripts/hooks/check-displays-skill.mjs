#!/usr/bin/env node
/**
 * PreToolUse hook — on the first Write/Edit under displays/ in a session,
 * inject a one-line reminder that /display-design-workflow has the
 * six-step checklist. Silent on subsequent edits in the same session so
 * iterative display work doesn't accumulate redundant reminders.
 *
 * Input (stdin, JSON): { session_id, tool_name, tool_input, ... }
 * Output (stdout, JSON): { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext: '...' } }
 *
 * Session tracking: .displays-hinted holds the last session_id we
 * reminded. Different session_id -> inject, update. Same -> silent.
 * Write-only; never referenced by agent code.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { safeMain } from './_safe.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const MARKER = join(PROJECT_ROOT, 'workspace', 'research', '.displays-hinted');

function readStdinSync() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

function main() {
  const raw = readStdinSync();
  let payload;
  try { payload = JSON.parse(raw); } catch { process.exit(0); }

  const toolName = payload?.tool_name || '';
  // Only Write — Edit fires constantly during iterative work and the
  // reminder is targeted at new-display authoring, not tweaks.
  if (toolName !== 'Write') { process.exit(0); }

  const filePath = (payload?.tool_input?.file_path || '').toString();
  if (!filePath) { process.exit(0); }

  const normalized = filePath.replace(/\\/g, '/');
  if (!/\/displays\//.test(normalized)) { process.exit(0); }
  if (/\/displays\/(_[a-z]|__)/.test(normalized)) { process.exit(0); }

  // Dedupe per session: if we've already nudged this session, stay silent.
  const sessionId = payload?.session_id || '';
  if (sessionId && existsSync(MARKER)) {
    try {
      if (readFileSync(MARKER, 'utf8').trim() === sessionId) { process.exit(0); }
    } catch { /* fall through to nudge */ }
  }

  // Record that we've reminded this session.
  try {
    mkdirSync(dirname(MARKER), { recursive: true });
    writeFileSync(MARKER, sessionId || String(Date.now()));
  } catch { /* best effort */ }

  const additionalContext =
    `Heads-up: writing to ${filePath}. ` +
    `/display-design-workflow has a six-step checklist (scope, sketch, wire, ` +
    `pressure-test, register, clean up). First nudge this session — won't repeat.`;

  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      additionalContext,
    },
  }));
  process.exit(0);
}

safeMain(main, import.meta.url);
