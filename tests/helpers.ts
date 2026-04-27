import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import WebSocket from 'ws';

/** Create a temporary workspace directory with the expected structure. */
export function createTempWorkspace(): string {
  const dir = mkdtempSync(join(tmpdir(), 'triptych-test-'));
  for (const sub of [
    'workspace/snapshots',
    'workspace/output',
    'workspace/files',
    'workspaces',
    'displays',
    'core',
  ]) {
    mkdirSync(join(dir, sub), { recursive: true });
  }
  return dir;
}

/** Remove a temporary workspace directory. */
export function cleanupWorkspace(dir: string) {
  rmSync(dir, { recursive: true, force: true });
}

/** Create a test workspace addon HTML file. */
export function addWorkspace(root: string, name: string, content = '<html><body>test</body></html>') {
  writeFileSync(join(root, 'workspaces', `${name}.html`), content);
}

/** Create a test display Python module in displays/. */
export function addDisplay(root: string, name: string, content = '# test display\n') {
  writeFileSync(join(root, 'displays', `${name}.py`), content);
}

/** Create a file in workspace/files. */
export function addWorkspaceFile(root: string, path: string, content: string | Buffer) {
  const fullPath = join(root, 'workspace', 'files', path);
  const parent = join(fullPath, '..');
  mkdirSync(parent, { recursive: true });
  writeFileSync(fullPath, content);
}

/** Connect a WebSocket test client and wait for connection. */
export function connectWs(port: number, path = '/'): Promise<WebSocket> {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://localhost:${port}${path}`);
    ws.on('open', () => resolve(ws));
    ws.on('error', reject);
  });
}

/** Send a JSON message on a WebSocket. */
export function wsSend(ws: WebSocket, msg: object) {
  ws.send(JSON.stringify(msg));
}

/** Wait for next JSON message on a WebSocket. */
export function wsRecv(ws: WebSocket, timeoutMs = 3000): Promise<any> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('WS recv timeout')), timeoutMs);
    ws.once('message', (data) => {
      clearTimeout(timer);
      resolve(JSON.parse(data.toString()));
    });
  });
}

/** Wait a short time for async operations. */
export function wait(ms: number): Promise<void> {
  return new Promise(r => setTimeout(r, ms));
}
