#!/usr/bin/env node

// Triptych preflight check — run before `npm install` to verify prerequisites.
// Usage: node scripts/preflight.js

import { execSync } from 'child_process';
import { existsSync } from 'fs';
import { platform } from 'os';

const isWin = platform() === 'win32';
const isMac = platform() === 'darwin';
let ok = true;

function check(label, fn) {
  try {
    const result = fn();
    console.log(`  ✓ ${label}: ${result}`);
  } catch (e) {
    console.log(`  ✗ ${label}: ${e.message}`);
    ok = false;
  }
}

function warn(label, msg) {
  console.log(`  ⚠ ${label}: ${msg}`);
}

function run(cmd) {
  return execSync(cmd, { encoding: 'utf-8', timeout: 10000 }).trim();
}

console.log('\nTriptych Preflight Check\n');

// Node.js version
check('Node.js', () => {
  const version = process.version;
  const major = parseInt(version.slice(1));
  if (major < 18) throw new Error(`${version} — need 18+`);
  return version;
});

// Python
check('Python', () => {
  const cmds = isWin ? ['python --version', 'py --version'] : ['python3 --version', 'python --version'];
  for (const cmd of cmds) {
    try {
      const out = run(cmd);
      const match = out.match(/(\d+\.\d+)/);
      if (match && parseFloat(match[1]) >= 3.8) return out;
    } catch {}
  }
  throw new Error('not found — install Python 3.10+');
});

// Python packages
const packages = ['matplotlib', 'numpy', 'scipy', 'sympy', 'plotly', 'pandas'];
const pythonCmd = isWin ? 'python' : 'python3';

for (const pkg of packages) {
  try {
    run(`${pythonCmd} -c "import ${pkg}"`);
    // don't print success for each package, just check
  } catch {
    warn('Python package', `${pkg} not installed — run: pip install -r requirements.txt`);
  }
}

// C++ build tools (soft warning — only needed if prebuilt node-pty binaries fail)
try {
  if (isWin) {
    run('where cl.exe');
  } else {
    run('cc --version');
  }
} catch {
  warn('Build tools', 'C++ compiler not found — only needed if node-pty prebuilt binaries fail for your platform');
  if (isWin) warn('', 'Install Visual Studio Build Tools if needed: npm install -g windows-build-tools');
  else if (isMac) warn('', 'Install Xcode CLI tools if needed: xcode-select --install');
  else warn('', 'Install build-essential if needed: sudo apt install build-essential');
}

// Claude Code CLI
try {
  run('claude --version');
  check('Claude Code', () => 'installed');
} catch {
  warn('Claude Code', 'not found — install: npm install -g @anthropic-ai/claude-code');
}

// Workspace directories
const dirs = ['workspace/output', 'workspace/files', 'workspace/snapshots', 'workspace/research'];
for (const dir of dirs) {
  if (!existsSync(dir)) {
    warn('Directory', `${dir} missing — will be created on server start`);
  }
}

console.log('');
if (ok) {
  console.log('All required prerequisites met. Run: npm install && pip install -r requirements.txt && npm run dev\n');
} else {
  console.log('Some prerequisites are missing. Fix the issues above and run this check again.\n');
  process.exit(1);
}
