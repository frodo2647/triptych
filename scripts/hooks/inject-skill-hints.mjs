#!/usr/bin/env node
/**
 * UserPromptSubmit hook — match the user's prompt against skill-rules.json
 * and inject one-line "use skill X" hints for every matching rule.
 *
 * Input (stdin, JSON): { session_id, prompt, ... }
 * Output (stdout, JSON): { hookSpecificOutput: { hookEventName: 'UserPromptSubmit', additionalContext: '...' } }
 *
 * Rules live in `.claude/skills/skill-rules.json`. Each rule has a regex
 * `pattern`, a `skill` name, and a short `hint`. The hook dedupes by skill
 * name so a prompt that matches three patterns all pointing at /verifier
 * gets one /verifier hint, not three.
 *
 * Budget: up to MAX_HINTS hints per prompt, up to MAX_TOTAL_CHARS injected
 * context. Runs on every prompt, so stay under a millisecond on the happy
 * path (no matches -> exit 0 silently).
 */

import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { safeMain } from './_safe.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const RULES_FILE = join(PROJECT_ROOT, '.claude', 'skills', 'skill-rules.json');
const MAX_HINTS = 3;
const MAX_TOTAL_CHARS = 400;

function readStdinSync() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

function main() {
  const raw = readStdinSync();
  let prompt = '';
  try { prompt = (JSON.parse(raw).prompt || '').toString(); }
  catch { prompt = raw; }
  if (!prompt) { process.exit(0); }

  if (!existsSync(RULES_FILE)) { process.exit(0); }

  let rulesDoc;
  try { rulesDoc = JSON.parse(readFileSync(RULES_FILE, 'utf8')); }
  catch { process.exit(0); }

  const rules = Array.isArray(rulesDoc?.rules) ? rulesDoc.rules : [];
  if (!rules.length) { process.exit(0); }

  const seen = new Set();
  const matches = [];
  for (const rule of rules) {
    if (!rule?.pattern || !rule?.skill) continue;
    if (seen.has(rule.skill)) continue;
    let re;
    try { re = new RegExp(rule.pattern, 'i'); }
    catch { continue; }
    if (!re.test(prompt)) continue;
    seen.add(rule.skill);
    matches.push(rule);
    if (matches.length >= MAX_HINTS) break;
  }

  if (!matches.length) { process.exit(0); }

  const lines = matches.map(m =>
    `  ${m.skill}${m.hint ? ' — ' + m.hint : ''}`
  );
  let additionalContext = `Relevant skills for this prompt:\n${lines.join('\n')}`;
  if (additionalContext.length > MAX_TOTAL_CHARS) {
    additionalContext = additionalContext.slice(0, MAX_TOTAL_CHARS - 1) + '…';
  }

  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext,
    },
  }));
  process.exit(0);
}

safeMain(main, import.meta.url);
