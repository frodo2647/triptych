import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { readFileSync, existsSync, writeFileSync, copyFileSync } from 'fs';
import { join } from 'path';
import {
  createTempWorkspace,
  cleanupWorkspace,
  addWorkspace,
  connectWs,
  wsSend,
  wsRecv,
  wait,
} from './helpers.js';

let root: string;
let port: number;
let serverHandle: { close: () => void } | null = null;

function getRandomPort() {
  return 10000 + Math.floor(Math.random() * 50000);
}

beforeAll(async () => {
  root = createTempWorkspace();
  port = getRandomPort();

  // Create required directories
  const { mkdirSync } = await import('fs');
  mkdirSync(join(root, 'workspace', 'snapshots', 'watch'), { recursive: true });
  mkdirSync(join(root, 'workspace', 'research'), { recursive: true });
  mkdirSync(join(root, 'scripts'), { recursive: true });
  mkdirSync(join(root, 'displays'), { recursive: true });

  // Copy watch.py to temp workspace so the server can find it
  const realRoot = join(import.meta.dirname, '..');
  copyFileSync(
    join(realRoot, 'scripts', 'watch.py'),
    join(root, 'scripts', 'watch.py')
  );

  // Create shell.html so server doesn't error
  writeFileSync(join(root, 'core', 'shell.html'), '<html><body>shell</body></html>');

  process.env.PROJECT_ROOT = root;
  process.env.PORT = String(port);

  const { startServer } = await import('../server/index.js');
  serverHandle = await startServer(port);
});

afterAll(() => {
  serverHandle?.close();
  cleanupWorkspace(root);
});


// ── Watch Status ──────────────────────────────────────────────

describe('GET /api/watch/status', () => {
  it('returns inactive when nothing is being watched', async () => {
    const res = await fetch(`http://localhost:${port}/api/watch/status`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.active).toBe(false);
  });
});


// ── Watch Stop ────────────────────────────────────────────────

describe('POST /api/watch/stop', () => {
  it('returns ok even when nothing is running', async () => {
    const res = await fetch(`http://localhost:${port}/api/watch/stop`, {
      method: 'POST',
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.ok).toBe(true);
  });
});


// ── Watch Start ───────────────────────────────────────────────

describe('POST /api/watch/start', () => {
  it('returns 400 without hwnd', async () => {
    const res = await fetch(`http://localhost:${port}/api/watch/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toContain('hwnd');
  });

  it('starts watching an invalid hwnd and reports status', async () => {
    // Even an invalid hwnd will start the process —
    // the Python script will detect the window doesn't exist and stop
    const res = await fetch(`http://localhost:${port}/api/watch/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hwnd: 999999999, interval: 1 }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.ok).toBe(true);

    // Wait for the watcher to detect invalid window and stop
    await wait(3000);

    // Status should be inactive after the invalid window is detected
    const statusRes = await fetch(`http://localhost:${port}/api/watch/status`);
    const status = await statusRes.json();
    expect(status.active).toBe(false);
  });
});


// ── Watch Windows List ────────────────────────────────────────

describe('GET /api/watch/windows', () => {
  it('returns a JSON array of windows', async () => {
    const res = await fetch(`http://localhost:${port}/api/watch/windows`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
  });

  it('each window has required fields', async () => {
    const res = await fetch(`http://localhost:${port}/api/watch/windows`);
    const data = await res.json();
    if (data.length === 0) return; // may be empty in headless env
    const win = data[0];
    expect(win).toHaveProperty('hwnd');
    expect(win).toHaveProperty('title');
    expect(win).toHaveProperty('width');
    expect(win).toHaveProperty('height');
  });
});


// ── Watch Capture (one-shot) ──────────────────────────────────

describe('POST /api/watch/capture', () => {
  it('returns error for invalid hwnd', async () => {
    const res = await fetch(`http://localhost:${port}/api/watch/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hwnd: 999999999 }),
    });
    expect(res.status).toBe(200); // Script returns JSON error, not HTTP error
    const data = await res.json();
    expect(data.error).toBeDefined();
  });

  it('returns 400 without hwnd', async () => {
    const res = await fetch(`http://localhost:${port}/api/watch/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(400);
  });

  it('captures a valid window', async () => {
    // Get a real window
    const listRes = await fetch(`http://localhost:${port}/api/watch/windows`);
    const windows = await listRes.json();
    if (windows.length === 0) return; // skip in headless

    const hwnd = windows[0].hwnd;
    const res = await fetch(`http://localhost:${port}/api/watch/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hwnd }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.ok).toBe(true);
    expect(data.width).toBeGreaterThan(0);
    expect(data.height).toBeGreaterThan(0);
  });
});


// ── WebSocket Watch Notifications ─────────────────────────────

describe('Watch WebSocket notifications', () => {
  it('broadcasts watch-capture when new screenshot arrives', async () => {
    const ws = await connectWs(port);
    wsSend(ws, { type: 'register', role: 'watch-ui' });
    await wsRecv(ws); // consume registration

    // Simulate a new capture by writing to the watch directory
    const watchDir = join(root, 'workspace', 'snapshots', 'watch');
    // Write a small PNG file
    const pngHeader = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
      'base64'
    );
    writeFileSync(join(watchDir, 'latest.png'), pngHeader);

    // Wait for chokidar to detect + debounce
    const msg = await wsRecv(ws, 5000);
    expect(msg.type).toBe('watch-capture');
    expect(msg.timestamp).toBeTypeOf('number');

    ws.close();
  });

  it('broadcasts watch-stopped when process exits', async () => {
    const ws = await connectWs(port);
    wsSend(ws, { type: 'register', role: 'watch-ui' });
    await wsRecv(ws); // consume registration

    // Start watching an invalid window (will exit quickly)
    await fetch(`http://localhost:${port}/api/watch/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hwnd: 999999999, interval: 1 }),
    });

    // Wait for watch-stopped message
    const msg = await wsRecv(ws, 5000);
    expect(msg.type).toBe('watch-stopped');

    ws.close();
  });
});
