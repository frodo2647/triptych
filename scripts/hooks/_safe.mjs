/**
 * Shared defensive wrapper for all Triptych hook scripts. Any exception in
 * main() lands in workspace/research/hook-errors.log and the hook exits 0 —
 * hook failures must never block the agent or the prompt pipeline. The log
 * is for humans to diagnose later; no program reads it.
 *
 * Usage:
 *   import { safeMain } from './_safe.mjs';
 *   // ...define main()...
 *   safeMain(main, import.meta.url);
 */

import { appendFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');
const LOG_DIR = join(PROJECT_ROOT, 'workspace', 'research');
const LOG_PATH = join(LOG_DIR, 'hook-errors.log');

export function safeMain(main, hookUrl) {
  try {
    main();
  } catch (err) {
    try {
      mkdirSync(LOG_DIR, { recursive: true });
      appendFileSync(LOG_PATH, JSON.stringify({
        ts: Date.now(),
        hook: hookUrl,
        msg: String(err?.message || err),
        stack: String(err?.stack || ''),
      }) + '\n');
    } catch { /* diagnostic best-effort; swallow */ }
    process.exit(0);
  }
}
