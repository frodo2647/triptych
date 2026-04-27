import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { readFileSync, existsSync, writeFileSync } from 'fs';
import { join } from 'path';
import {
  createTempWorkspace,
  cleanupWorkspace,
  addWorkspace,
  addDisplay,
  addWorkspaceFile,
  connectWs,
  wsSend,
  wsRecv,
  wait,
} from './helpers.js';

// We need to dynamically start the server with a temp workspace.
// Override environment before importing.
let root: string;
let port: number;
let serverHandle: { close: () => void } | null = null;

// Use a random port to avoid conflicts
function getRandomPort() {
  return 10000 + Math.floor(Math.random() * 50000);
}

beforeAll(async () => {
  root = createTempWorkspace();
  port = getRandomPort();

  // Add some test fixtures
  addWorkspace(root, 'tldraw', '<html><body>tldraw workspace</body></html>');
  addWorkspace(root, 'pdf', '<html><body>pdf workspace</body></html>');
  addDisplay(root, 'matplotlib');
  addDisplay(root, 'research');
  addWorkspaceFile(root, 'test.txt', 'hello world');
  addWorkspaceFile(root, 'subdir/nested.txt', 'nested file');
  writeFileSync(join(root, 'core', 'shell.html'), '<html><body>shell</body></html>');

  // Set environment and start server
  process.env.PROJECT_ROOT = root;
  process.env.PORT = String(port);

  // Dynamically import to pick up env vars
  const { startServer } = await import('../server/index.js');
  serverHandle = await startServer(port);
});

afterAll(() => {
  serverHandle?.close();
  cleanupWorkspace(root);
});

// ── HTTP Route Tests ───────────────────────────────────────────

describe('GET /', () => {
  it('serves the shell page', async () => {
    const res = await fetch(`http://localhost:${port}/`);
    expect(res.status).toBe(200);
    const body = await res.text();
    expect(body).toContain('shell');
  });
});

describe('GET /api/files/*', () => {
  it('serves a workspace file', async () => {
    const res = await fetch(`http://localhost:${port}/api/files/files/test.txt`);
    expect(res.status).toBe(200);
    const body = await res.text();
    expect(body).toBe('hello world');
  });

  it('serves nested files', async () => {
    const res = await fetch(`http://localhost:${port}/api/files/files/subdir/nested.txt`);
    expect(res.status).toBe(200);
    const body = await res.text();
    expect(body).toBe('nested file');
  });

  it('returns 404 for missing files', async () => {
    const res = await fetch(`http://localhost:${port}/api/files/files/nope.txt`);
    expect(res.status).toBe(404);
  });

  it('blocks path traversal (does not serve files outside workspace)', async () => {
    // Express normalizes `..` in URLs, so /api/files/../package.json becomes /api/package.json -> 404
    // The important thing is the file is NOT served, regardless of status code
    const res = await fetch(`http://localhost:${port}/api/files/../package.json`);
    expect(res.ok).toBe(false);
  });

  it('blocks path traversal with encoded dots', async () => {
    const res = await fetch(`http://localhost:${port}/api/files/..%2F..%2Fpackage.json`);
    expect(res.ok).toBe(false);
  });
});

describe('PUT /api/files/*', () => {
  it('writes a file to workspace', async () => {
    const res = await fetch(`http://localhost:${port}/api/files/files/new-file.txt`, {
      method: 'PUT',
      headers: { 'Content-Type': 'text/plain' },
      body: 'written by test',
    });
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.ok).toBe(true);

    // Verify file exists on disk
    const content = readFileSync(join(root, 'workspace', 'files', 'new-file.txt'), 'utf-8');
    expect(content).toBe('written by test');
  });

  it('creates parent directories', async () => {
    const res = await fetch(`http://localhost:${port}/api/files/files/deep/path/file.txt`, {
      method: 'PUT',
      headers: { 'Content-Type': 'text/plain' },
      body: 'deep file',
    });
    expect(res.status).toBe(200);
    expect(existsSync(join(root, 'workspace', 'files', 'deep', 'path', 'file.txt'))).toBe(true);
  });

  it('blocks path traversal on write (does not write outside workspace)', async () => {
    const res = await fetch(`http://localhost:${port}/api/files/../evil.txt`, {
      method: 'PUT',
      headers: { 'Content-Type': 'text/plain' },
      body: 'evil',
    });
    expect(res.ok).toBe(false);
    // Verify the file was NOT created outside workspace
    const { existsSync } = await import('fs');
    const { join } = await import('path');
    expect(existsSync(join(root, 'evil.txt'))).toBe(false);
  });
});

describe('GET /api/browse', () => {
  it('lists files in workspace/files', async () => {
    const res = await fetch(`http://localhost:${port}/api/browse`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.type).toBe('dir');
    expect(data.entries).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ name: 'test.txt', type: 'file' }),
      ])
    );
  });

  it('lists subdirectories', async () => {
    const res = await fetch(`http://localhost:${port}/api/browse/subdir`);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.entries).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ name: 'nested.txt', type: 'file' }),
      ])
    );
  });

  it('returns 404 for missing paths', async () => {
    const res = await fetch(`http://localhost:${port}/api/browse/nonexistent`);
    expect(res.status).toBe(404);
  });
});

describe('POST /api/snapshot', () => {
  it('saves snapshot image and context', async () => {
    // Create a small test image (1x1 red pixel PNG as base64)
    const testImageBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==';

    const res = await fetch(`http://localhost:${port}/api/snapshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image: testImageBase64,
        context: { selectedText: 'F=ma', page: 42 },
        voice: 'explain this',
      }),
    });

    expect(res.status).toBe(200);

    // Verify PNG was saved
    const pngPath = join(root, 'workspace', 'snapshots', 'latest.png');
    expect(existsSync(pngPath)).toBe(true);
    const png = readFileSync(pngPath);
    expect(png.length).toBeGreaterThan(0);

    // Verify context JSON was saved
    const jsonPath = join(root, 'workspace', 'snapshots', 'latest.json');
    expect(existsSync(jsonPath)).toBe(true);
    const ctx = JSON.parse(readFileSync(jsonPath, 'utf-8'));
    expect(ctx.selectedText).toBe('F=ma');
    expect(ctx.page).toBe(42);
    expect(ctx.voice).toBe('explain this');
    expect(ctx.timestamp).toBeTypeOf('number');
  });

  it('saves context-only snapshot (no image)', async () => {
    const res = await fetch(`http://localhost:${port}/api/snapshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ context: { note: 'just context' } }),
    });
    expect(res.status).toBe(200);

    const ctx = JSON.parse(readFileSync(join(root, 'workspace', 'snapshots', 'latest.json'), 'utf-8'));
    expect(ctx.note).toBe('just context');
  });
});

describe('GET /api/workspaces', () => {
  it('lists workspace addon HTML files', async () => {
    const res = await fetch(`http://localhost:${port}/api/workspaces`);
    expect(res.status).toBe(200);
    const workspaces = await res.json();
    expect(workspaces).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: 'tldraw' }),
        expect.objectContaining({ id: 'pdf' }),
      ])
    );
  });
});

describe('GET /api/displays', () => {
  it('lists public Python modules from displays/', async () => {
    const res = await fetch(`http://localhost:${port}/api/displays`);
    expect(res.status).toBe(200);
    const displays = await res.json();
    expect(displays).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: 'matplotlib' }),
        expect.objectContaining({ id: 'research' }),
      ])
    );
  });
});

describe('POST /api/workspace/command', () => {
  it('returns 400 without a command', async () => {
    const res = await fetch(`http://localhost:${port}/api/workspace/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(400);
  });

  it('times out when no viewer responds', async () => {
    const res = await fetch(`http://localhost:${port}/api/workspace/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: 'test', timeout: 500 }),
    });
    expect(res.status).toBe(504);
  });

  it('routes command to viewer and returns response', async () => {
    // Register a fake viewer that responds to commands
    const wsViewer = await connectWs(port);
    wsSend(wsViewer, { type: 'register', role: 'viewer' });
    await wsRecv(wsViewer); // consume registration response

    // Listen for command and respond
    const commandPromise = wsRecv(wsViewer, 3000).then(msg => {
      expect(msg.type).toBe('workspace-command');
      expect(msg.command).toBe('get-selection');
      wsSend(wsViewer, { type: 'command-response', requestId: msg.requestId, data: { selectedText: 'hello' } });
    });

    // Send command via HTTP
    const res = await fetch(`http://localhost:${port}/api/workspace/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: 'get-selection', timeout: 3000 }),
    });

    await commandPromise;
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.ok).toBe(true);
    expect(json.data.selectedText).toBe('hello');

    wsViewer.close();
  });
});

// ── WebSocket Tests ────────────────────────────────────────────

describe('WebSocket', () => {
  it('accepts connections and handles registration', async () => {
    const ws = await connectWs(port);
    wsSend(ws, { type: 'register', role: 'panel-a' });
    const msg = await wsRecv(ws);
    expect(msg.type).toBe('registered');
    expect(msg.role).toBe('panel-a');
    ws.close();
  });

  it('routes messages between panels', async () => {
    const wsA = await connectWs(port);
    const wsB = await connectWs(port);

    wsSend(wsA, { type: 'register', role: 'panel-a' });
    await wsRecv(wsA); // consume registration response

    wsSend(wsB, { type: 'register', role: 'panel-b' });
    await wsRecv(wsB); // consume registration response

    // Send a message from A targeting B
    wsSend(wsA, { type: 'custom-data', to: 'panel-b', payload: 'hello from A' });
    const msg = await wsRecv(wsB);
    expect(msg.type).toBe('custom-data');
    expect(msg.payload).toBe('hello from A');

    wsA.close();
    wsB.close();
  });

  it('handles switch-workspace command', async () => {
    const wsA = await connectWs(port);
    const wsControl = await connectWs(port);

    wsSend(wsA, { type: 'register', role: 'panel-a' });
    await wsRecv(wsA);

    wsSend(wsControl, { type: 'register', role: 'control' });
    await wsRecv(wsControl);

    // Send switch-workspace command
    wsSend(wsControl, { type: 'switch-workspace', workspace: 'pdf' });
    const msg = await wsRecv(wsA);
    expect(msg.type).toBe('switch-workspace');
    expect(msg.workspace).toBe('pdf');

    wsA.close();
    wsControl.close();
  });

  it('sends reload when output files change', async () => {
    const wsB = await connectWs(port);
    wsSend(wsB, { type: 'register', role: 'panel-b' });
    await wsRecv(wsB); // consume registration

    // Write a file to workspace/output
    writeFileSync(join(root, 'workspace', 'output', 'test-output.html'), '<p>result</p>');

    // Wait for chokidar debounce (300ms stabilityThreshold + 500ms debounce + buffer)
    const msg = await wsRecv(wsB, 5000);
    expect(msg.type).toBe('reload');

    wsB.close();
  });
});
