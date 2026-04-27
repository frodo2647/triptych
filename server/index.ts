import 'dotenv/config';
import express from 'express';
import { createServer } from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import { existsSync, mkdirSync, writeFileSync, readdirSync, readFileSync, appendFileSync, statSync } from 'fs';
import { join, resolve, relative, extname } from 'path';
import { spawn, ChildProcess } from 'child_process';
import chokidar from 'chokidar';

// ── Logging ───────────────────────────────────────────────────
const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 } as const;
const LOG_LEVEL = (process.env.LOG_LEVEL ?? 'info') as keyof typeof LOG_LEVELS;

function log(level: keyof typeof LOG_LEVELS, tag: string, ...args: unknown[]) {
  if (LOG_LEVELS[level] < LOG_LEVELS[LOG_LEVEL]) return;
  const ts = new Date().toISOString().slice(11, 23);
  const prefix = `${ts} [${level.toUpperCase().padEnd(5)}] [${tag}]`;
  const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
  const line = `${prefix} ${msg}`;
  console.log(line);

  // Also write to file log for debugging
  try {
    const logDir = join(resolve(process.env.PROJECT_ROOT ?? process.cwd()), 'logs');
    mkdirSync(logDir, { recursive: true });
    appendFileSync(join(logDir, 'server.log'), line + '\n');
  } catch { /* ignore log write failures */ }
}

// ── Config ─────────────────────────────────────────────────────
const PORT = parseInt(process.env.PORT ?? '3000');
const PROJECT_ROOT = resolve(process.env.PROJECT_ROOT ?? process.cwd());
const WORKSPACE = join(PROJECT_ROOT, 'workspace');
const WORKSPACES_DIR = join(PROJECT_ROOT, 'workspaces');
const DISPLAYS_DIR = join(PROJECT_ROOT, 'core');
const CORE_DIR = join(PROJECT_ROOT, 'core');

// Ensure required directories exist
for (const dir of [
  WORKSPACE,
  join(WORKSPACE, 'snapshots'),
  join(WORKSPACE, 'output'),
  join(WORKSPACE, 'files'),
  join(WORKSPACE, 'research'),
  join(WORKSPACE, 'snapshots', 'watch'),
  WORKSPACES_DIR,
]) {
  mkdirSync(dir, { recursive: true });
}

// ── Express ────────────────────────────────────────────────────
const app = express();
app.use(express.json({ limit: '50mb' }));
app.use(express.raw({ type: 'image/*', limit: '50mb' }));

// Serve shell page
app.get('/', (_req, res) => {
  const shellPath = join(CORE_DIR, 'shell.html');
  if (existsSync(shellPath)) {
    res.sendFile(shellPath);
  } else {
    res.status(200).send('<html><body><h1>Triptych</h1><p>Shell not built yet.</p></body></html>');
  }
});

// Serve core static files (shell.js, shell.css, capture.js)
app.use('/core', express.static(CORE_DIR));

// Serve workspace addon HTML files
app.use('/workspaces', express.static(WORKSPACES_DIR));

// Serve workspace/output files (for display iframe to load directly)
app.use('/output', express.static(join(WORKSPACE, 'output')));

// List renderable files in workspace/output/ — used by default-display.html
// to build the display panel's tab bar. Each named display (from e.g.
// show_plotly(name="diag")) shows up as a file here.
const DISPLAY_EXTS = new Set(['.html', '.png', '.svg', '.jpg', '.jpeg', '.pdf']);
const DISPLAY_KIND: Record<string, string> = {
  '.html': 'html', '.pdf': 'pdf',
  '.png': 'image', '.svg': 'image', '.jpg': 'image', '.jpeg': 'image',
};

// First-seen map: filename -> ms timestamp we first observed this name in the
// pool. Gives stable tab order even when displays use atomic replace (which
// resets birthtime on Windows) or when mtime updates during training runs.
const poolFirstSeen = new Map<string, number>();

app.get('/api/output-pool', (_req, res) => {
  const dir = join(WORKSPACE, 'output');
  if (!existsSync(dir)) { res.json({ files: [] }); return; }

  const now = Date.now();
  const liveNames = new Set<string>();

  const files = readdirSync(dir)
    .filter(f => !f.startsWith('.') && !f.startsWith('_') && !f.endsWith('.tmp'))
    .map(f => {
      try {
        const stat = statSync(join(dir, f));
        if (!stat.isFile()) return null;
        const ext = extname(f).toLowerCase();
        if (!DISPLAY_EXTS.has(ext)) return null;
        liveNames.add(f);
        // First time we see this name, seed with the older of {birthtime, mtime}
        // so freshly-observed files that already exist on disk keep their
        // historical ordering relative to each other.
        if (!poolFirstSeen.has(f)) {
          const seed = Math.min(
            stat.birthtimeMs || now,
            stat.mtimeMs || now,
            now,
          );
          poolFirstSeen.set(f, seed);
        }
        return {
          name: f,
          stem: f.slice(0, f.length - ext.length),
          kind: DISPLAY_KIND[ext] || 'html',
          mtime: stat.mtimeMs,
          firstSeen: poolFirstSeen.get(f)!,
          size: stat.size,
        };
      } catch { return null; }
    })
    .filter(Boolean) as Array<{ name: string; stem: string; kind: string; mtime: number; firstSeen: number; size: number }>;

  // Evict entries for files that have been deleted.
  for (const name of [...poolFirstSeen.keys()]) {
    if (!liveNames.has(name)) poolFirstSeen.delete(name);
  }

  // Stable ordering: index.html first (canonical "main"), then by firstSeen
  // ascending. Using first-seen (not mtime or birthtime) keeps tab order
  // stable when a display is re-written — e.g. show_progress() during
  // training shouldn't jitter its tab past siblings on every metric write,
  // even when atomic_write_text resets the filesystem birthtime.
  files.sort((a, b) => {
    if (a.name === 'index.html') return -1;
    if (b.name === 'index.html') return 1;
    if (a.name === 'research.html') return -1;
    if (b.name === 'research.html') return 1;
    return a.firstSeen - b.firstSeen;
  });

  // Piggyback the current focus marker on the pool response so the display
  // iframe only needs one polling endpoint. The marker is written by
  // displays._base.focus_display(); null when nothing has requested focus.
  let focus: { stem: string; ts: number } | null = null;
  const focusPath = join(dir, '.focus');
  if (existsSync(focusPath)) {
    try { focus = JSON.parse(readFileSync(focusPath, 'utf8')); } catch {}
  }

  // userFocus is the *user's* actual current tab, written by the display
  // iframe on click/keyboard switch via POST /api/display-state. Distinct
  // from focus (last programmatic request) — the asymmetry lets Python
  // callers detect "user navigated away from the tab the agent opened."
  let userFocus: { stem: string; ts: number } | null = null;
  const userFocusPath = join(dir, '.userFocus');
  if (existsSync(userFocusPath)) {
    try { userFocus = JSON.parse(readFileSync(userFocusPath, 'utf8')); } catch {}
  }

  res.json({ files, focus, userFocus });
});

// POST /api/display-state — display iframe reports the user's active tab
// on every click + keyboard switch. Persisted to workspace/output/.userFocus
// so Python callers (displays.active_display()) can read it directly without
// an HTTP round-trip.
app.post('/api/display-state', (req, res) => {
  const stem = typeof req.body?.stem === 'string' ? req.body.stem : null;
  if (!stem) { res.status(400).json({ error: 'No stem specified' }); return; }
  // Allow only [A-Za-z0-9_.-] to avoid writing anything interpretable as a
  // path fragment; the pool uses stems from real filenames so this is the
  // same character class enforced in resolve_display_path().
  if (!/^[A-Za-z0-9_.-]+$/.test(stem)) {
    res.status(400).json({ error: 'Invalid stem' });
    return;
  }
  const dir = join(WORKSPACE, 'output');
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, '.userFocus'), JSON.stringify({ stem, ts: Date.now() / 1000 }));
  res.json({ ok: true });
});

// ── File Proxy ─────────────────────────────────────────────────
// GET /api/files/* — serve any file from workspace/
// Path traversal protection: resolved path must stay within workspace
app.get('/api/files/*', (req, res) => {
  const requestedPath = req.params[0];
  if (!requestedPath) {
    res.status(400).json({ error: 'No path specified' });
    return;
  }

  const fullPath = resolve(WORKSPACE, requestedPath);
  const relPath = relative(WORKSPACE, fullPath);

  // Path traversal check: relative path must not start with '..'
  if (relPath.startsWith('..') || relPath.startsWith('/')) {
    res.status(403).json({ error: 'Access denied' });
    return;
  }

  if (!existsSync(fullPath)) {
    res.status(404).json({ error: 'File not found' });
    return;
  }

  res.sendFile(fullPath);
});

// PUT /api/files/* — write a file to workspace/
app.put('/api/files/*', express.raw({ type: '*/*', limit: '50mb' }), (req, res) => {
  const requestedPath = req.params[0];
  if (!requestedPath) {
    res.status(400).json({ error: 'No path specified' });
    return;
  }

  const fullPath = resolve(WORKSPACE, requestedPath);
  const relPath = relative(WORKSPACE, fullPath);

  if (relPath.startsWith('..') || relPath.startsWith('/')) {
    res.status(403).json({ error: 'Access denied' });
    return;
  }

  // Ensure parent directory exists
  const parentDir = resolve(fullPath, '..');
  mkdirSync(parentDir, { recursive: true });

  writeFileSync(fullPath, req.body);
  res.json({ ok: true, path: relPath });
});

// ── Snapshot Endpoint ──────────────────────────────────────────
// POST /api/snapshot — receives captures from viewer's capture.js
app.post('/api/snapshot', (req, res) => {
  log('debug', 'snap', `Snapshot received (image: ${!!req.body.image}, voice: ${!!req.body.voice})`);
  const { image, context, voice } = req.body;

  if (image) {
    // image is base64 PNG
    const buf = Buffer.from(image, 'base64');
    writeFileSync(join(WORKSPACE, 'snapshots', 'latest.png'), buf);
  }

  const contextData = {
    ...(context ?? {}),
    timestamp: Date.now(),
    ...(voice ? { voice } : {}),
  };
  writeFileSync(
    join(WORKSPACE, 'snapshots', 'latest.json'),
    JSON.stringify(contextData, null, 2)
  );

  res.json({ ok: true });
});

// POST /api/snapshot/now — trigger an immediate capture from the viewer
app.post('/api/snapshot/now', (_req, res) => {
  log('info', 'snap', 'Capture-now triggered');
  broadcastToRole('viewer', { type: 'capture-now' });
  res.json({ ok: true });
});

// ── File Browser ──────────────────────────────────────────────
const FILES_DIR = join(WORKSPACE, 'files');

app.get('/api/browse', (_req, res) => {
  res.json(browseDir(FILES_DIR));
});

app.get('/api/browse/*', (req, res) => {
  const requested = req.params[0] || '';
  const fullPath = resolve(FILES_DIR, requested);
  const relPath = relative(FILES_DIR, fullPath);

  if (relPath.startsWith('..') || relPath.startsWith('/')) {
    res.status(403).json({ error: 'Access denied' });
    return;
  }

  if (!existsSync(fullPath)) {
    res.status(404).json({ error: 'Not found' });
    return;
  }

  const stat = statSync(fullPath);
  if (stat.isFile()) {
    res.json({ type: 'file', name: requested.split('/').pop(), size: stat.size, ext: extname(requested) });
    return;
  }

  res.json(browseDir(fullPath));
});

function browseDir(dir: string) {
  if (!existsSync(dir)) return { type: 'dir', entries: [] };
  const entries = readdirSync(dir).map(name => {
    try {
      const s = statSync(join(dir, name));
      return {
        name,
        type: s.isDirectory() ? 'dir' as const : 'file' as const,
        size: s.size,
        mtime: s.mtimeMs,
        ext: s.isDirectory() ? '' : extname(name),
      };
    } catch { return null; }
  }).filter(Boolean);
  // Dirs first, then files, alphabetical within each group
  entries.sort((a: any, b: any) => {
    if (a.type !== b.type) return a.type === 'dir' ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  return { type: 'dir', entries };
}

// ── Workspace/Display Listing ─────────────────────────────────
app.get('/api/workspaces', (_req, res) => {
  // Authoritative source: HTML files in workspaces/
  if (!existsSync(WORKSPACES_DIR)) { res.json([]); return; }
  const workspaces = readdirSync(WORKSPACES_DIR)
    .filter(f => f.endsWith('.html'))
    .map(f => ({
      id: f.replace('.html', ''),
      name: f.replace('.html', '').replace(/-/g, ' '),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
  res.json(workspaces);
});

app.get('/api/displays', (_req, res) => {
  // Authoritative source: Python modules in displays/ (excluding private _* files)
  const displaysDir = join(PROJECT_ROOT, 'displays');
  if (!existsSync(displaysDir)) { res.json([]); return; }
  const displays = readdirSync(displaysDir)
    .filter(f => f.endsWith('.py') && !f.startsWith('_'))
    .map(f => ({
      id: f.replace('.py', ''),
      name: f.replace('.py', '').replace(/-/g, ' '),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
  res.json(displays);
});

// ── Google Workspace API ──────────────────────────────────────
function runGoogleApi(args: string[]): Promise<any> {
  return new Promise((resolve, reject) => {
    const proc = spawn('python', [join(PROJECT_ROOT, 'scripts', 'google_api.py'), ...args]);
    let stdout = '';
    let stderr = '';
    proc.stdout?.on('data', (d) => stdout += d.toString());
    proc.stderr?.on('data', (d) => stderr += d.toString());
    proc.on('close', (code) => {
      try { resolve(JSON.parse(stdout)); }
      catch { reject(new Error(stderr || stdout || 'Unknown error')); }
    });
    proc.on('error', (err) => reject(err));
  });
}

app.get('/api/google/status', async (_req, res) => {
  try { res.json(await runGoogleApi(['status'])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

app.post('/api/google/auth', async (_req, res) => {
  try { res.json(await runGoogleApi(['auth'])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

app.post('/api/google/logout', async (_req, res) => {
  try { res.json(await runGoogleApi(['logout'])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

app.post('/api/google/resolve', async (req, res) => {
  const { url } = req.body;
  if (!url) { res.status(400).json({ error: 'No url specified' }); return; }
  try { res.json(await runGoogleApi(['resolve', url])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

app.post('/api/google/docs/read', async (req, res) => {
  const { documentId } = req.body;
  if (!documentId) { res.status(400).json({ error: 'No documentId' }); return; }
  try { res.json(await runGoogleApi(['doc-read', documentId])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

app.post('/api/google/docs/write', async (req, res) => {
  const { documentId, operations } = req.body;
  if (!documentId || !operations) { res.status(400).json({ error: 'Need documentId and operations' }); return; }
  try { res.json(await runGoogleApi(['doc-write', documentId, JSON.stringify(operations)])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

app.post('/api/google/sheets/read', async (req, res) => {
  const { spreadsheetId, range = 'Sheet1' } = req.body;
  if (!spreadsheetId) { res.status(400).json({ error: 'No spreadsheetId' }); return; }
  try { res.json(await runGoogleApi(['sheet-read', spreadsheetId, range])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

app.post('/api/google/sheets/write', async (req, res) => {
  const { spreadsheetId, range, values } = req.body;
  if (!spreadsheetId || !range || !values) { res.status(400).json({ error: 'Need spreadsheetId, range, values' }); return; }
  try { res.json(await runGoogleApi(['sheet-write', spreadsheetId, range, JSON.stringify(values)])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

app.post('/api/google/sheets/info', async (req, res) => {
  const { spreadsheetId } = req.body;
  if (!spreadsheetId) { res.status(400).json({ error: 'No spreadsheetId' }); return; }
  try { res.json(await runGoogleApi(['sheet-info', spreadsheetId])); }
  catch (e: any) { res.status(500).json({ error: e.message }); }
});

// ── Window Watch ──────────────────────────────────────────────
let watchProcess: ChildProcess | null = null;
let watchMeta: { hwnd: number; title: string; interval: number } | null = null;

app.get('/api/watch/windows', (_req, res) => {
  const proc = spawn('python', [join(PROJECT_ROOT, 'scripts', 'watch.py'), 'list']);
  let stdout = '';
  let stderr = '';
  proc.stdout?.on('data', (d) => stdout += d.toString());
  proc.stderr?.on('data', (d) => stderr += d.toString());
  proc.on('close', (code) => {
    if (code !== 0) {
      log('error', 'watch', `list failed: ${stderr}`);
      res.status(500).json({ error: 'Failed to list windows', detail: stderr });
      return;
    }
    try { res.json(JSON.parse(stdout)); }
    catch { res.status(500).json({ error: 'Invalid output from watch script' }); }
  });
  proc.on('error', (err) => {
    res.status(500).json({ error: `Failed to run watch script: ${err.message}` });
  });
});

app.post('/api/watch/start', (req, res) => {
  const { hwnd, interval = 3 } = req.body;
  if (!hwnd) { res.status(400).json({ error: 'No hwnd specified' }); return; }

  // Kill existing watcher
  if (watchProcess) {
    watchProcess.kill();
    watchProcess = null;
    watchMeta = null;
  }

  const proc = spawn('python', [
    join(PROJECT_ROOT, 'scripts', 'watch.py'), 'watch',
    String(hwnd), String(interval),
  ]);
  watchProcess = proc;

  let firstLine = '';
  let responded = false;
  const onData = (data: Buffer) => {
    if (responded) return;
    firstLine += data.toString();
    if (firstLine.includes('\n')) {
      responded = true;
      proc.stdout?.off('data', onData);
      try {
        const status = JSON.parse(firstLine.split('\n')[0]);
        watchMeta = { hwnd: Number(hwnd), title: status.title ?? '', interval: Number(interval) };
        res.json({ ok: true, ...status });
      } catch {
        watchMeta = { hwnd: Number(hwnd), title: '', interval: Number(interval) };
        res.json({ ok: true, hwnd, interval });
      }
    }
  };
  proc.stdout?.on('data', onData);
  proc.stderr?.on('data', (d) => log('error', 'watch', d.toString()));
  proc.on('close', () => {
    log('info', 'watch', 'Watch process exited');
    watchProcess = null;
    watchMeta = null;
    broadcastToAll({ type: 'watch-stopped' });
  });
  proc.on('error', (err) => {
    log('error', 'watch', `spawn error: ${err.message}`);
    if (!responded) res.status(500).json({ error: err.message });
    watchProcess = null;
    watchMeta = null;
  });

  // Timeout: if no first line in 5s, respond anyway
  setTimeout(() => {
    if (!responded) {
      responded = true;
      watchMeta = { hwnd: Number(hwnd), title: '', interval: Number(interval) };
      res.json({ ok: true, hwnd, interval });
    }
  }, 5000);
});

app.post('/api/watch/stop', (_req, res) => {
  if (watchProcess) {
    watchProcess.kill();
    watchProcess = null;
    watchMeta = null;
  }
  res.json({ ok: true });
});

app.get('/api/watch/status', (_req, res) => {
  res.json({ active: !!watchProcess, ...(watchMeta ?? {}) });
});

app.post('/api/watch/capture', (req, res) => {
  // One-shot capture of a window
  const { hwnd } = req.body;
  if (!hwnd) { res.status(400).json({ error: 'No hwnd specified' }); return; }
  const proc = spawn('python', [join(PROJECT_ROOT, 'scripts', 'watch.py'), 'capture', String(hwnd)]);
  let stdout = '';
  proc.stdout?.on('data', (d) => stdout += d.toString());
  proc.stderr?.on('data', (d) => log('error', 'watch', d.toString()));
  proc.on('close', (code) => {
    try { res.json(JSON.parse(stdout)); }
    catch { res.status(500).json({ error: 'Capture failed' }); }
  });
});

// ── Workspace Command (HTTP → WS → response) ─────────────────
const pendingCommands = new Map<string, { resolve: (msg: any) => void }>();
let commandCounter = 0;

app.post('/api/workspace/command', (req, res) => {
  const { command, params, timeout = 2000 } = req.body;
  if (!command) {
    res.status(400).json({ error: 'No command specified' });
    return;
  }

  const requestId = `cmd-${++commandCounter}-${Date.now()}`;
  log('info', 'cmd', `HTTP command: ${command} (${requestId})`);

  // Set up response listener with timeout
  const timer = setTimeout(() => {
    pendingCommands.delete(requestId);
    res.status(504).json({ error: 'Command timeout', requestId });
  }, timeout);

  pendingCommands.set(requestId, {
    resolve: (msg) => {
      clearTimeout(timer);
      res.json({ ok: true, requestId, command, data: msg.data });
    },
  });

  // Broadcast command to workspace viewer
  broadcastToRole('viewer', { type: 'workspace-command', command, params: params ?? {}, requestId });
});

// ── HTTP Server ────────────────────────────────────────────────
const server = createServer(app);

// ── WebSocket ──────────────────────────────────────────────────
const wss = new WebSocketServer({ server });

interface ClientInfo {
  ws: WebSocket;
  role: string; // 'panel-a', 'panel-b', 'terminal', 'display'
  attachedSessionId?: string; // for terminal clients, which session they view
}

const clients = new Map<string, ClientInfo>();
let clientIdCounter = 0;

// ── Terminal sessions (Phase 4: multi-PTY) ───────────────────────
// Each session is an independent Claude Code PTY. Session 1 is
// auto-created on first terminal register (backward compat). Additional
// sessions are spawned on demand via `session-create`.
interface TerminalSession {
  id: string;
  name: string;
  pty: any;
  createdAt: number;
}

const sessions = new Map<string, TerminalSession>();
let ptyModule: any = null;

// Pick the lowest unused session id starting from 1. After a kill, the freed
// slot is reused on next create — so the user sees "session 2" come back
// instead of monotonically-growing numbers that never reset.
function nextSessionId(): string {
  for (let i = 1; i <= sessions.size + 1; i++) {
    if (!sessions.has(String(i))) return String(i);
  }
  return String(sessions.size + 1);
}

function sessionList() {
  return [...sessions.values()]
    .sort((a, b) => Number(a.id) - Number(b.id))
    .map(s => ({ id: s.id, name: s.name, createdAt: s.createdAt }));
}

function broadcastToSession(sessionId: string, msg: object) {
  const payload = JSON.stringify(msg);
  for (const [, client] of clients) {
    if (client.role === 'terminal' && client.attachedSessionId === sessionId
        && client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(payload);
    }
  }
}

function broadcastSessionList() {
  const list = sessionList();
  const payload = JSON.stringify({ type: 'session-list', sessions: list });
  for (const [, client] of clients) {
    if (client.role === 'terminal' && client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(payload);
    }
  }
}

function findClaude(): string {
  // Try common locations for the claude executable
  if (process.platform === 'win32') {
    const candidates = [
      join(process.env.USERPROFILE ?? '', '.local', 'bin', 'claude.exe'),
      join(process.env.USERPROFILE ?? '', '.local', 'bin', 'claude'),
      'claude.exe',
      'claude',
    ];
    for (const c of candidates) {
      if (c && existsSync(c)) {
        log('info', 'pty', `Found claude at: ${c}`);
        return c;
      }
    }
  }
  return 'claude'; // fallback, hope it's in PATH
}

async function createSession(name?: string): Promise<TerminalSession | null> {
  try {
    if (!ptyModule) ptyModule = await import('node-pty');
    const claudePath = findClaude();
    const id = nextSessionId();
    const displayName = name ?? `session ${id}`;

    log('info', 'pty', `Spawning session ${id} (${displayName}): ${claudePath}`);

    const pty = ptyModule.spawn(claudePath, ['--dangerously-skip-permissions'], {
      name: 'xterm-256color',
      cols: 120,
      rows: 40,
      cwd: PROJECT_ROOT,
      env: { ...process.env, FORCE_COLOR: '1' },
    });

    const session: TerminalSession = {
      id, name: displayName, pty, createdAt: Date.now(),
    };
    sessions.set(id, session);

    pty.onData((data: string) => {
      broadcastToSession(id, { type: 'terminal-data', sessionId: id, data });
    });

    pty.onExit(({ exitCode }: { exitCode: number }) => {
      log('warn', 'pty', `Session ${id} exited with code ${exitCode}`);
      sessions.delete(id);
      // Re-attach orphaned clients to the lowest-numbered remaining session so
      // input routing works immediately — otherwise terminal-input messages
      // that fall back to attachedSessionId have nowhere to go until the
      // client sends an explicit session-switch.
      const fallback = sessionList()[0]?.id;
      for (const [, client] of clients) {
        if (client.attachedSessionId === id) client.attachedSessionId = fallback;
      }
      broadcastSessionList();
    });

    log('info', 'pty', `Session ${id} spawned`);
    broadcastSessionList();
    return session;
  } catch (err: any) {
    log('error', 'pty', `Failed to spawn session: ${err?.message ?? err}`);
    return null;
  }
}

// Back-compat shim for old call sites (always resolves to session 1,
// creating it if missing). Preserves the original "auto-spawn Claude on first
// terminal register" behavior.
async function getOrSpawnDefaultSession(): Promise<TerminalSession | null> {
  const existing = sessions.get('1');
  if (existing) return existing;
  return createSession('session 1');
}

// Shell PTY (lazy-initialized, separate from Claude)
let shellProcess: any = null;

async function getOrSpawnShell() {
  if (shellProcess) return shellProcess;
  try {
    if (!ptyModule) ptyModule = await import('node-pty');
    const shell = process.platform === 'win32' ? 'powershell.exe' : 'bash';
    log('info', 'shell', `Spawning shell: ${shell}`);
    shellProcess = ptyModule.spawn(shell, [], {
      name: 'xterm-256color',
      cols: 80,
      rows: 24,
      cwd: join(WORKSPACE, 'files'),
      env: { ...process.env, FORCE_COLOR: '1' },
    });
    shellProcess.onData((data: string) => {
      broadcastToRole('shell', { type: 'shell-data', data });
    });
    shellProcess.onExit(() => {
      log('warn', 'shell', 'Shell exited');
      shellProcess = null;
    });
    return shellProcess;
  } catch (err: any) {
    log('error', 'shell', `Failed to spawn shell: ${err?.message ?? err}`);
    return null;
  }
}

function broadcastToRole(role: string, msg: object) {
  const payload = JSON.stringify(msg);
  for (const [, client] of clients) {
    if (client.role === role && client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(payload);
    }
  }
}

function broadcastToAll(msg: object) {
  const payload = JSON.stringify(msg);
  for (const [, client] of clients) {
    if (client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(payload);
    }
  }
}

wss.on('connection', (ws) => {
  const clientId = `client-${++clientIdCounter}`;
  clients.set(clientId, { ws, role: 'unknown' });
  log('info', 'ws', `Client connected: ${clientId}`);

  ws.on('message', async (raw) => {
    let msg: any;
    try {
      msg = JSON.parse(raw.toString());
    } catch {
      log('warn', 'ws', `Non-JSON message from ${clientId}`);
      return;
    }

    log('debug', 'ws', `${clientId} -> ${msg.type}`, msg.role ?? msg.to ?? '');

    switch (msg.type) {
      case 'register': {
        const role = msg.role ?? 'unknown';
        const info: ClientInfo = { ws, role };
        clients.set(clientId, info);
        log('info', 'ws', `${clientId} registered as ${role}`);
        ws.send(JSON.stringify({ type: 'registered', clientId, role }));

        if (role === 'terminal') {
          const session = await getOrSpawnDefaultSession();
          if (session) {
            info.attachedSessionId = session.id;
            // Tell the client which session they're viewing + the current list.
            ws.send(JSON.stringify({
              type: 'session-list',
              sessions: sessionList(),
              attached: session.id,
            }));
          } else {
            ws.send(JSON.stringify({
              type: 'terminal-data',
              data: 'Failed to start Claude Code. Check server logs.\r\n',
            }));
          }
        }
        if (role === 'shell') {
          const shell = await getOrSpawnShell();
          if (!shell) {
            ws.send(JSON.stringify({ type: 'shell-data', data: 'Failed to start shell.\r\n' }));
          }
        }
        break;
      }

      case 'terminal-input': {
        const info = clients.get(clientId);
        const sid = msg.sessionId ?? info?.attachedSessionId;
        const session = sid ? sessions.get(sid) : undefined;
        if (session && msg.data) session.pty.write(msg.data);
        break;
      }

      case 'terminal-resize': {
        const info = clients.get(clientId);
        const sid = msg.sessionId ?? info?.attachedSessionId;
        const session = sid ? sessions.get(sid) : undefined;
        if (session && msg.cols && msg.rows) {
          session.pty.resize(msg.cols, msg.rows);
        }
        break;
      }

      case 'session-create': {
        const session = await createSession(msg.name);
        const info = clients.get(clientId);
        if (session && info) {
          info.attachedSessionId = session.id;
          ws.send(JSON.stringify({
            type: 'session-created',
            sessionId: session.id,
            sessions: sessionList(),
          }));
        }
        break;
      }

      case 'session-switch': {
        const info = clients.get(clientId);
        const target = msg.sessionId && sessions.get(msg.sessionId);
        if (info && target) {
          info.attachedSessionId = target.id;
          ws.send(JSON.stringify({ type: 'session-switched', sessionId: target.id }));
        }
        break;
      }

      case 'session-kill': {
        const target = msg.sessionId && sessions.get(msg.sessionId);
        if (target) {
          // Refuse to kill the last session — prevents accidentally orphaning
          // the entire terminal panel (matches Quinn's spec).
          if (sessions.size <= 1) {
            ws.send(JSON.stringify({ type: 'session-kill-rejected', reason: 'last-session' }));
            break;
          }
          log('info', 'pty', `Killing session ${target.id}`);
          try { target.pty.kill(); } catch { /* pty might already be dead */ }
          // `onExit` handler will delete from map + broadcast.
        }
        break;
      }

      case 'session-list': {
        ws.send(JSON.stringify({ type: 'session-list', sessions: sessionList() }));
        break;
      }

      case 'shell-input': {
        const shell = await getOrSpawnShell();
        if (shell && msg.data) shell.write(msg.data);
        break;
      }

      case 'shell-resize': {
        if (shellProcess && msg.cols && msg.rows) {
          shellProcess.resize(msg.cols, msg.rows);
        }
        break;
      }

      case 'switch-workspace': {
        log('info', 'ws', `Switch workspace to: ${msg.workspace}`);
        broadcastToRole('panel-a', { type: 'switch-workspace', workspace: msg.workspace });
        break;
      }

      case 'workspace-command': {
        log('info', 'ws', `Workspace command: ${msg.command}`);
        broadcastToRole('viewer', { type: 'workspace-command', command: msg.command, params: msg.params, requestId: msg.requestId });
        break;
      }

      case 'command-response': {
        log('debug', 'ws', `Command response: ${msg.requestId}`);
        // Route to pending HTTP request if exists
        const pending = pendingCommands.get(msg.requestId);
        if (pending) {
          pendingCommands.delete(msg.requestId);
          pending.resolve(msg);
        }
        break;
      }

      case 'switch-display': {
        log('info', 'ws', `Switch display to: ${msg.display}`);
        broadcastToRole('panel-b', { type: 'switch-display', display: msg.display });
        break;
      }

      default: {
        if (msg.to) {
          log('debug', 'ws', `Routing message to role: ${msg.to}`);
          broadcastToRole(msg.to, msg);
        }
        break;
      }
    }
  });

  ws.on('close', () => {
    const info = clients.get(clientId);
    log('info', 'ws', `Client disconnected: ${clientId} (role: ${info?.role})`);
    clients.delete(clientId);
  });
});

// ── File Watcher (display output) ──────────────────────────────
const outputDir = join(WORKSPACE, 'output');
let reloadDebounce: ReturnType<typeof setTimeout> | null = null;

const watcher = chokidar.watch(outputDir, {
  ignoreInitial: true,
  // Python writers in displays/ use atomic os.replace, so no partial-write risk;
  // keep a short stability window for third-party/manual writers only.
  awaitWriteFinish: { stabilityThreshold: 100, pollInterval: 50 },
  usePolling: true,
  interval: 150,
});

watcher.on('all', (event, path) => {
  log('debug', 'watch', `Output change: ${event} ${path}`);
  if (reloadDebounce) clearTimeout(reloadDebounce);
  reloadDebounce = setTimeout(() => {
    log('info', 'watch', 'Broadcasting reload to display panels');
    broadcastToRole('panel-b', { type: 'reload' });
    broadcastToRole('display', { type: 'reload' });
  }, 150);
});

// Watch for new window captures → notify all clients
const watchDir = join(WORKSPACE, 'snapshots', 'watch');
let watchCaptureDebounce: ReturnType<typeof setTimeout> | null = null;

const watchCaptureWatcher = chokidar.watch(watchDir, {
  ignoreInitial: true,
  awaitWriteFinish: { stabilityThreshold: 300, pollInterval: 100 },
});

watchCaptureWatcher.on('all', (event, changedPath) => {
  if (!changedPath.endsWith('.png')) return;
  if (watchCaptureDebounce) clearTimeout(watchCaptureDebounce);
  watchCaptureDebounce = setTimeout(() => {
    broadcastToAll({ type: 'watch-capture', timestamp: Date.now() });
  }, 400);
});

// Also watch workspaces/ for new workspace addon files
const workspaceWatcher = chokidar.watch(WORKSPACES_DIR, {
  ignoreInitial: true,
  awaitWriteFinish: { stabilityThreshold: 300, pollInterval: 100 },
});

workspaceWatcher.on('all', () => {
  broadcastToAll({ type: 'workspaces-changed' });
});

// ── Start ──────────────────────────────────────────────────────
export function startServer(port = PORT) {
  return new Promise<{ server: typeof server; app: typeof app; wss: typeof wss; close: () => void }>((resolvePromise) => {
    const onListenError = (err: NodeJS.ErrnoException) => {
      if (err.code === 'EADDRINUSE') {
        console.error(`\nPort ${port} already in use.`);
        console.error(`Set PORT in .env (or your shell) to pick another, or free the port.\n`);
        process.exit(1);
      }
      throw err;
    };
    server.on('error', onListenError);
    wss.on('error', onListenError);
    server.listen(port, () => {
      console.log(`Triptych server: http://localhost:${port}`);
      console.log(`  Workspace: ${WORKSPACE}`);
      console.log(`  Workspaces: ${WORKSPACES_DIR}`);

      resolvePromise({
        server,
        app,
        wss,
        close: () => {
          watcher.close();
          watchCaptureWatcher.close();
          workspaceWatcher.close();
          if (watchProcess) { watchProcess.kill(); watchProcess = null; }
          for (const session of sessions.values()) {
            try { session.pty.kill(); } catch { /* ignore */ }
          }
          sessions.clear();
          if (shellProcess) {
            shellProcess.kill();
            shellProcess = null;
          }
          wss.clients.forEach(c => c.close());
          server.close();
        },
      });
    });
  });
}

// Start if run directly (not imported for tests)
const isDirectRun = process.argv[1]?.endsWith('index.ts') || process.argv[1]?.endsWith('index.js');
if (isDirectRun) {
  startServer();
}
