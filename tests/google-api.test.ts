import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { writeFileSync, copyFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { createTempWorkspace, cleanupWorkspace } from './helpers.js';

let root: string;
let port: number;
let serverHandle: { close: () => void } | null = null;

function getRandomPort() {
  return 10000 + Math.floor(Math.random() * 50000);
}

beforeAll(async () => {
  root = createTempWorkspace();
  port = getRandomPort();

  mkdirSync(join(root, 'workspace', 'snapshots', 'watch'), { recursive: true });
  mkdirSync(join(root, 'workspace', 'research'), { recursive: true });
  mkdirSync(join(root, 'workspace', 'config'), { recursive: true });
  mkdirSync(join(root, 'scripts'), { recursive: true });
  mkdirSync(join(root, 'displays'), { recursive: true });

  const realRoot = join(import.meta.dirname, '..');
  copyFileSync(join(realRoot, 'scripts', 'watch.py'), join(root, 'scripts', 'watch.py'));
  copyFileSync(join(realRoot, 'scripts', 'google_api.py'), join(root, 'scripts', 'google_api.py'));

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


// ── Google Auth Status ────────────────────────────────────────

describe('GET /api/google/status', () => {
  it('returns authentication status', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/status`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data).toHaveProperty('authenticated');
    expect(data.authenticated).toBe(false);
  });
});


// ── Google Logout ─────────────────────────────────────────────

describe('POST /api/google/logout', () => {
  it('returns ok', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/logout`, {
      method: 'POST',
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.ok).toBe(true);
  });
});


// ── Google URL Resolution ─────────────────────────────────────

describe('POST /api/google/resolve', () => {
  it('resolves a Google Docs URL', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://docs.google.com/document/d/abc123/edit' }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.type).toBe('doc');
    expect(data.id).toBe('abc123');
  });

  it('resolves a Google Sheets URL', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://docs.google.com/spreadsheets/d/xyz789/edit#gid=0' }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.type).toBe('sheet');
    expect(data.id).toBe('xyz789');
  });

  it('returns 400 without url', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(400);
  });
});


// ── Google Docs Read (unauthenticated) ────────────────────────

describe('POST /api/google/docs/read', () => {
  it('returns auth error when not authenticated', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/docs/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documentId: 'fake-doc-id' }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.error).toBeDefined();
    expect(data.error.toLowerCase()).toContain('not authenticated');
  });

  it('returns 400 without documentId', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/docs/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(400);
  });
});


// ── Google Docs Write (unauthenticated) ───────────────────────

describe('POST /api/google/docs/write', () => {
  it('returns auth error when not authenticated', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/docs/write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        documentId: 'fake-doc-id',
        operations: [{ insertText: { location: { index: 1 }, text: 'test' } }],
      }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.error).toBeDefined();
  });

  it('returns 400 without required fields', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/docs/write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documentId: 'test' }),
    });
    expect(res.status).toBe(400);
  });
});


// ── Google Sheets Read (unauthenticated) ──────────────────────

describe('POST /api/google/sheets/read', () => {
  it('returns auth error when not authenticated', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/sheets/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spreadsheetId: 'fake-sheet-id', range: 'A1:B2' }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.error).toBeDefined();
  });

  it('returns 400 without spreadsheetId', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/sheets/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(400);
  });
});


// ── Google Sheets Write (unauthenticated) ─────────────────────

describe('POST /api/google/sheets/write', () => {
  it('returns auth error when not authenticated', async () => {
    const res = await fetch(`http://localhost:${port}/api/google/sheets/write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        spreadsheetId: 'fake-sheet-id',
        range: 'A1:B2',
        values: [['a', 'b'], ['c', 'd']],
      }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.error).toBeDefined();
  });
});
