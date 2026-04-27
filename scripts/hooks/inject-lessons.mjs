#!/usr/bin/env node
/**
 * UserPromptSubmit hook — prepend a compact summary of recent tool-lessons
 * to the conversation context so the agent stays aware of past mistakes.
 *
 * Input (stdin, JSON): { session_id, prompt, ... }
 * Output (stdout, JSON): { hookSpecificOutput: { hookEventName: 'UserPromptSubmit', additionalContext: '...' } }
 *
 * Budget: each lesson file contributes at most its first 3 post-header bullet
 * points; total injection is capped at ~500 chars across all tools. If nothing
 * useful exists, we emit nothing and exit 0.
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { join, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { safeMain } from './_safe.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const LESSONS_DIR = join(PROJECT_ROOT, 'memory', 'tool-lessons');
const MAX_TOTAL_CHARS = 500;
const MAX_PER_TOOL = 3;

function readStdinSync() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

function extractBullets(md) {
  // Grab the first MAX_PER_TOOL lines starting with '- ' or '* '.
  const bullets = [];
  for (const line of md.split('\n')) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      bullets.push(trimmed.slice(2).trim());
      if (bullets.length >= MAX_PER_TOOL) break;
    }
  }
  return bullets;
}

function main() {
  // Consume any stdin so the hook machinery doesn't hang, then ignore it.
  readStdinSync();

  if (!existsSync(LESSONS_DIR)) { process.exit(0); }

  const files = readdirSync(LESSONS_DIR).filter(f => f.endsWith('.md')).sort();
  if (!files.length) { process.exit(0); }

  const sections = [];
  let total = 0;
  for (const f of files) {
    const toolName = basename(f, '.md');
    let content;
    try { content = readFileSync(join(LESSONS_DIR, f), 'utf8'); } catch { continue; }
    const bullets = extractBullets(content);
    if (!bullets.length) continue;
    const section = `**${toolName}**: ${bullets.join(' | ')}`;
    if (total + section.length > MAX_TOTAL_CHARS) break;
    sections.push(section);
    total += section.length + 2;
  }

  if (!sections.length) { process.exit(0); }

  const additionalContext = `Lessons from prior sessions — avoid repeating these:\n${sections.join('\n')}`;

  const output = {
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext,
    },
  };
  process.stdout.write(JSON.stringify(output));
  process.exit(0);
}

safeMain(main, import.meta.url);
