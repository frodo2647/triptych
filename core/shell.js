/* ── Triptych Shell — v2 ──────────────────────────────────
   Three-panel chrome: pane toggles, ghost reopeners, tabs,
   seam drag, popovers, theme toggle, command bar, toasts,
   hotkeys. Plus: WS protocol, xterm session multiplexing,
   multi-tab workspace, hoisted display tabs.
   ──────────────────────────────────────────────────────── */

(function () {
  'use strict';

  /* ── Globals & DOM refs ──────────────────────────────── */
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  const isMac = /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent || '');
  const cmdKeyLabel = isMac ? '⌘K' : 'Ctrl+K';
  const altKeyLabel = isMac ? '⌥' : 'Alt';
  $('#cmd-hint-key').textContent = cmdKeyLabel;
  $('#hk-cmd').textContent = cmdKeyLabel;
  // Swap "Alt" → "⌥" labels on Mac in the help popover hotkey table
  if (isMac) {
    document.querySelectorAll('#help-menu .hk-table kbd').forEach(kbd => {
      if (kbd.textContent === 'Alt') kbd.textContent = '⌥';
    });
  }

  const PANEL_NAMES = ['workspace', 'display', 'terminal'];
  const panels = PANEL_NAMES.map(name => $(`.panel[data-panel="${name}"]`));
  const seams  = $$('.seam');
  const stage  = $('#stage');
  const ghostToggles = $('#ghost-toggles');
  const toastEl = $('#toast');
  const cmdBar = $('#cmd-bar');
  const cmdOverlay = $('#cmd-overlay');
  const cmdInput = $('#cmd-input');
  const cmdResults = $('#cmd-results');
  const sendHint = $('#send-hint');

  /* ── Layout (flex-grow proportions) ──────────────────── */
  const flex = panels.map(() => 1);
  function applyFlex() {
    panels.forEach((p, i) => {
      if (!p.classList.contains('closed')) p.style.flexGrow = flex[i];
    });
  }
  applyFlex();

  /* ── Toast ───────────────────────────────────────────── */
  let toastTimer;
  function showToast(html) {
    toastEl.innerHTML = html;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 1800);
  }

  /* ── Pane focus ──────────────────────────────────────── */
  let focusedIdx = panels.findIndex(p => p.classList.contains('focused'));
  if (focusedIdx < 0) focusedIdx = 1;

  function focusPanel(idx, silent = false) {
    if (idx < 0 || idx >= panels.length) return;
    if (panels[idx].classList.contains('closed')) return;
    panels.forEach(p => p.classList.remove('focused'));
    panels[idx].classList.add('focused');
    focusedIdx = idx;
    if (panels[idx].dataset.panel === 'terminal' && term) {
      try { term.focus(); } catch {}
    }
    if (!silent) {
      showToast(`focus → <span class="accent">${panels[idx].dataset.panel}</span>`);
    }
  }
  panels.forEach((p, i) => {
    p.addEventListener('mousedown', e => {
      if (e.target.closest('.tab-x')) return;
      focusPanel(i, true);
    });
    p.addEventListener('mouseenter', () => {
      if (!document.hasFocus() || document.activeElement === document.body) {
        focusPanel(i, true);
      }
    });
  });

  /* ── Counts and ghost toggles ────────────────────────── */
  function refreshCounts() {
    panels.forEach(p => {
      const c = p.querySelectorAll('.tabstrip .tab').length;
      const cEl = p.querySelector('.pt-count');
      if (cEl) cEl.textContent = c;
    });
  }
  function updateEmptyStates() {
    panels.forEach(p => {
      const name = p.dataset.panel;
      const content = p.querySelector('.panel-content');
      const tabs = p.querySelectorAll('.tabstrip .tab');
      if (name === 'workspace') {
        const hasActive = !!p.querySelector('.panel-content > .view.active:not([data-view="ws-empty"])');
        const empty = content.querySelector('.view[data-view="ws-empty"]');
        if (empty) empty.classList.toggle('active', tabs.length === 0 && !hasActive);
      }
    });
  }

  const GHOST_DEFS = {
    workspace: { letter: 'W', icon: '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4a1 1 0 011-1h3.5l1 1.2H13a1 1 0 011 1V12a1 1 0 01-1 1H3a1 1 0 01-1-1V4z"/></svg>' },
    display:   { letter: 'D', icon: '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="12" height="9" rx="1"/><path d="M6 14h4M8 12v2"/></svg>' },
    terminal:  { letter: 'T', icon: '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4l4 4-4 4M9 12h4"/></svg>' },
  };
  function refreshGhostToggles() {
    ghostToggles.innerHTML = '';
    panels.forEach(p => {
      if (!p.classList.contains('closed')) return;
      const name = p.dataset.panel;
      const def = GHOST_DEFS[name];
      const btn = document.createElement('button');
      btn.className = 'ghost-toggle';
      btn.dataset.pane = name;
      btn.title = `Open ${name} pane`;
      btn.innerHTML = `<span class="pt-icon">${def.icon}</span><span class="pt-letter">${def.letter}</span>`;
      btn.addEventListener('click', () => togglePane(name));
      ghostToggles.appendChild(btn);
    });
    positionGhosts();
  }
  function positionGhosts() {
    const ghosts = [...ghostToggles.querySelectorAll('.ghost-toggle')];
    if (!ghosts.length) return;
    const leftAnchor = 180;
    const rightAnchor = 110;
    const wsClosed   = panels[0].classList.contains('closed');
    const dispClosed = panels[1].classList.contains('closed');
    const termClosed = panels[2].classList.contains('closed');
    ghosts.forEach(g => {
      const name = g.dataset.pane;
      g.style.left = ''; g.style.right = ''; g.style.transform = '';
      if (name === 'workspace') g.style.left = leftAnchor + 'px';
      else if (name === 'terminal') g.style.right = rightAnchor + 'px';
      else if (name === 'display') {
        if (wsClosed && !termClosed) g.style.left = (leftAnchor + 70) + 'px';
        else if (termClosed && !wsClosed) g.style.right = (rightAnchor + 70) + 'px';
        else { g.style.left = '50%'; g.style.transform = 'translateX(-50%)'; }
      }
    });
  }

  /* ── Pane toggle ─────────────────────────────────────── */
  function togglePane(name) {
    const panel = panels.find(p => p.dataset.panel === name);
    if (!panel) return;
    if (panel.classList.contains('closed')) {
      panel.classList.remove('closed');
      focusPanel(panels.indexOf(panel), true);
      showToast(`open → <span class="accent">${name}</span>`);
    } else {
      const visible = panels.filter(p => !p.classList.contains('closed'));
      if (visible.length <= 1) { showToast(`can't close last pane`); return; }
      panel.classList.add('closed');
      if (panel.classList.contains('focused')) {
        const next = panels.find(p => !p.classList.contains('closed'));
        if (next) focusPanel(panels.indexOf(next), true);
      }
      showToast(`hide → <span class="accent">${name}</span>`);
    }
    refreshGhostToggles();
    applyFlex();
    if (name === 'terminal' || !panel.classList.contains('closed')) {
      setTimeout(fitTerminal, 50);
    }
  }
  $$('.pane-toggle').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      togglePane(btn.dataset.toggle);
    });
  });

  /* ── Tabs (generic) ──────────────────────────────────── */
  function makeTabEl({ id, name, closeable, kind }) {
    const tab = document.createElement('button');
    tab.className = 'tab' + (closeable ? ' closeable' : '');
    tab.dataset.id = id;
    if (kind) tab.dataset.kind = kind;
    tab.innerHTML = `
      <span class="tab-bracket">[</span>
      <span class="tab-name">${escapeHtml(name)}</span>
      <span class="tab-bracket">]</span>
      ${closeable ? '<span class="tab-x">×</span>' : ''}`;
    return tab;
  }

  function activateTab(panel, tabId) {
    const strip = panel.querySelector('.tabstrip');
    const content = panel.querySelector('.panel-content');
    strip.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.id === tabId));
    content.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.dataset.view === tabId));
    updateEmptyStates();
  }

  // Wire delegated clicks for each panel's tabstrip
  panels.forEach(panel => {
    const strip = panel.querySelector('.tabstrip');
    if (!strip) return;
    strip.addEventListener('click', e => {
      const xBtn = e.target.closest('.tab-x');
      if (xBtn) {
        const tab = xBtn.closest('.tab');
        if (!tab || !tab.classList.contains('closeable')) return;
        e.stopPropagation();
        handleTabClose(panel, tab);
        return;
      }
      const tab = e.target.closest('.tab');
      if (tab) {
        handleTabClick(panel, tab);
        focusPanel(panels.indexOf(panel), true);
        return;
      }
      const add = e.target.closest('.tab-add');
      if (add) handleTabAdd(panel);
    });
  });

  function handleTabClick(panel, tab) {
    const name = panel.dataset.panel;
    const id = tab.dataset.id;
    if (name === 'workspace') activateTab(panel, id);
    else if (name === 'display') {
      activateTab(panel, 'ds-frame');
      tab.classList.remove('has-unread');
      // Re-paint active styling on the clicked tab (activateTab targets ds-frame view, not the tab)
      panel.querySelectorAll('.tabstrip .tab').forEach(t => t.classList.toggle('active', t === tab));
      const fname = tab.dataset.fname || tab.querySelector('.tab-name')?.textContent;
      const dispFrame = panel.querySelector('iframe.panel-frame');
      if (dispFrame?.contentWindow && fname) {
        dispFrame.contentWindow.postMessage({ type: 'triptych-display-select', name: fname }, '*');
      }
      activeDisplayName = fname || activeDisplayName;
    }
    else if (name === 'terminal') {
      if (id !== activeSessionId) setActiveSession(id);
    }
  }

  function handleTabClose(panel, tab) {
    const name = panel.dataset.panel;
    const id = tab.dataset.id;
    if (name === 'workspace') closeWorkspaceTab(id);
    else if (name === 'terminal') wsSend({ type: 'session-kill', sessionId: id });
  }

  function handleTabAdd(panel) {
    const name = panel.dataset.panel;
    if (name === 'workspace') openWorkspaceFM();
    else if (name === 'terminal') wsSend({ type: 'session-create' });
  }

  /* ── Workspace multi-tab ─────────────────────────────── */
  // openTabs[id] = { id, kind: 'fm'|'file', workspace, file, name }
  const wsPanel = panels[0];
  const wsStrip = wsPanel.querySelector('.tabstrip');
  const wsContent = wsPanel.querySelector('.panel-content');
  const wsAddBtn = wsStrip.querySelector('.tab-add');
  const openTabs = new Map();
  let activeWsId = null;

  function tabIdForFile(workspace, file) {
    return 'ws-' + (file || workspace).replace(/[^a-zA-Z0-9_-]/g, '_');
  }

  function ensureWorkspaceTab({ kind, workspace, file, name }) {
    const id = kind === 'fm' ? 'ws-fm' : tabIdForFile(workspace, file);
    if (openTabs.has(id)) return id;

    const tabEl = makeTabEl({ id, name, closeable: true, kind });
    wsStrip.insertBefore(tabEl, wsAddBtn);

    const view = document.createElement('div');
    view.className = 'view';
    view.dataset.view = id;
    const iframe = document.createElement('iframe');
    iframe.className = 'panel-frame';
    iframe.title = name;
    iframe.src = kind === 'fm' ? '/workspaces/files.html' : `/workspaces/${workspace}.html?file=${encodeURIComponent(file)}`;
    view.appendChild(iframe);
    wsContent.appendChild(view);
    bindIframeShortcuts(iframe);

    openTabs.set(id, { id, kind, workspace, file, name });
    return id;
  }

  function activateWorkspaceTab(id) {
    activeWsId = id;
    activateTab(wsPanel, id);
    refreshCounts();
    saveSession();
  }

  function closeWorkspaceTab(id) {
    const tab = wsStrip.querySelector(`.tab[data-id="${id}"]`);
    const view = wsContent.querySelector(`.view[data-view="${id}"]`);
    if (!tab) return;
    const sibs = [...wsStrip.querySelectorAll('.tab')];
    const idx = sibs.indexOf(tab);
    tab.remove();
    if (view) view.remove();
    openTabs.delete(id);
    if (activeWsId === id) {
      const remaining = [...wsStrip.querySelectorAll('.tab')];
      const next = remaining[Math.max(0, idx - 1)] || remaining[0];
      if (next) activateWorkspaceTab(next.dataset.id);
      else { activeWsId = null; updateEmptyStates(); saveSession(); }
    }
    refreshCounts();
  }

  function openWorkspaceFM() {
    // The + button always opens a fresh Files tab. If a Files tab already
    // exists, just activate it.
    if (openTabs.has('ws-fm')) { activateWorkspaceTab('ws-fm'); return; }
    const id = ensureWorkspaceTab({ kind: 'fm', name: 'Files' });
    activateWorkspaceTab(id);
  }

  function openWorkspaceFile(workspace, file) {
    const newId = tabIdForFile(workspace, file);
    const newName = file ? file.split('/').pop() : workspace;
    // Already open → just activate
    if (openTabs.has(newId)) { activateWorkspaceTab(newId); return; }
    // If there's an active workspace tab, REPLACE it (browser-style: click a
    // file in the Files browser → Files tab transforms into the file tab).
    // For a separate tab, the user hits the + button first.
    if (activeWsId && openTabs.has(activeWsId)) {
      replaceWorkspaceTab(activeWsId, { kind: 'file', workspace, file, name: newName });
      return;
    }
    // Otherwise create new
    ensureWorkspaceTab({ kind: 'file', workspace, file, name: newName });
    activateWorkspaceTab(newId);
  }

  function replaceWorkspaceTab(oldId, spec) {
    const newId = spec.kind === 'fm' ? 'ws-fm' : tabIdForFile(spec.workspace, spec.file);
    const tab = wsStrip.querySelector(`.tab[data-id="${oldId}"]`);
    const view = wsContent.querySelector(`.view[data-view="${oldId}"]`);
    if (!tab || !view) return;
    tab.dataset.id = newId;
    if (spec.kind) tab.dataset.kind = spec.kind;
    const nameEl = tab.querySelector('.tab-name');
    if (nameEl) nameEl.textContent = spec.name;
    view.dataset.view = newId;
    const iframe = view.querySelector('iframe');
    const newSrc = spec.kind === 'fm'
      ? '/workspaces/files.html'
      : `/workspaces/${spec.workspace}.html?file=${encodeURIComponent(spec.file)}`;
    if (iframe) {
      iframe.src = newSrc;
      iframe.title = spec.name;
    }
    openTabs.delete(oldId);
    openTabs.set(newId, { id: newId, ...spec });
    if (activeWsId === oldId) activeWsId = newId;
    activateTab(wsPanel, newId);
    refreshCounts();
    saveSession();
  }

  // Files.html and other workspace addons send open-file messages
  window.addEventListener('message', (e) => {
    const data = e.data;
    if (!data || typeof data !== 'object') return;
    if (data.type === 'open-file' && data.workspace) {
      openWorkspaceFile(data.workspace, data.file);
    }
  });

  /* ── Display tabs (hoisted from default-display) ─────── */
  const dispPanel = panels[1];
  const dispStrip = dispPanel.querySelector('.tabstrip');
  let activeDisplayName = null;
  let displayPollTimer = null;

  function renderDisplayTabs(files) {
    const existing = new Map();
    dispStrip.querySelectorAll('.tab').forEach(t => existing.set(t.dataset.fname, t));
    const wantNames = new Set(files.map(f => f.name));
    // Remove tabs no longer in the pool
    for (const [name, tab] of existing) if (!wantNames.has(name)) tab.remove();
    // Add tabs that are new (preserve order)
    files.forEach(f => {
      let tab = existing.get(f.name);
      if (!tab) {
        const id = 'disp-' + f.name.replace(/[^a-zA-Z0-9_-]/g, '_');
        tab = makeTabEl({ id, name: f.name, closeable: false, kind: 'display' });
        tab.dataset.fname = f.name;
        dispStrip.appendChild(tab);
      }
    });
    // Reorder strip to match files order
    files.forEach(f => {
      const t = dispStrip.querySelector(`.tab[data-fname="${CSS.escape(f.name)}"]`);
      if (t) dispStrip.appendChild(t);
    });
    // If no active selection yet, pick the first
    if (!activeDisplayName && files.length) activeDisplayName = files[0].name;
    // Mark active
    dispStrip.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.fname === activeDisplayName));
    refreshCounts();
  }

  async function pollDisplayPool() {
    try {
      const res = await fetch('/api/output-pool');
      if (!res.ok) return;
      const data = await res.json();
      const files = data.files || [];
      renderDisplayTabs(files);
    } catch {}
  }
  function startDisplayPoll() {
    pollDisplayPool();
    if (displayPollTimer) return;
    displayPollTimer = setInterval(pollDisplayPool, 1500);
  }

  /* ── Seam drag (flex-grow, proportion-preserving) ────── */
  seams.forEach(seam => {
    seam.addEventListener('pointerdown', e => {
      e.preventDefault();
      seam.classList.add('dragging');
      document.body.classList.add('resizing');
      seam.setPointerCapture(e.pointerId);
      const startX = e.clientX;
      const leftName = seam.dataset.left;
      const rightName = seam.dataset.right;
      let leftIdx = panels.findIndex(p => p.dataset.panel === leftName);
      let rightIdx = panels.findIndex(p => p.dataset.panel === rightName);
      // Skip closed neighbors
      while (leftIdx >= 0 && panels[leftIdx].classList.contains('closed')) leftIdx--;
      while (rightIdx < panels.length && panels[rightIdx].classList.contains('closed')) rightIdx++;
      if (leftIdx < 0 || rightIdx >= panels.length) {
        seam.classList.remove('dragging');
        document.body.classList.remove('resizing');
        return;
      }
      const stageW = stage.getBoundingClientRect().width;
      const startFlexL = flex[leftIdx];
      const startFlexR = flex[rightIdx];
      const totalFlex  = startFlexL + startFlexR;
      const onMove = ev => {
        const dx = ev.clientX - startX;
        const dxFrac = dx / stageW * 3;
        const newL = Math.max(0.15, Math.min(totalFlex - 0.15, startFlexL + dxFrac));
        flex[leftIdx]  = newL;
        flex[rightIdx] = totalFlex - newL;
        applyFlex();
        debouncedFit();
      };
      const onUp = () => {
        seam.classList.remove('dragging');
        document.body.classList.remove('resizing');
        seam.removeEventListener('pointermove', onMove);
        seam.removeEventListener('pointerup', onUp);
        clearTimeout(fitDebounce);
        fitTerminal();
      };
      seam.addEventListener('pointermove', onMove);
      seam.addEventListener('pointerup', onUp);
    });
  });

  /* ── WebSocket (preserved from v1) ───────────────────── */
  let ws = null;
  let wsReconnectTimer = null;
  const visiblePanels = ['workspace', 'display', 'terminal'];

  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}`);
    ws.onopen = () => {
      setWsStatus(true);
      wsSend({ type: 'register', role: 'panel-a' });
      wsSend({ type: 'register', role: 'panel-b' });
      wsSend({ type: 'register', role: 'terminal' });
    };
    ws.onmessage = (event) => {
      let msg;
      try { msg = JSON.parse(event.data); } catch { return; }
      switch (msg.type) {
        case 'terminal-data': {
          const sid = msg.sessionId;
          if (sid && termInstances.has(sid)) termInstances.get(sid).term.write(msg.data);
          else if (term) term.write(msg.data);
          break;
        }
        case 'session-list': {
          const prevActive = activeSessionId;
          sessionsOrder = msg.sessions || [];
          if (msg.attached && !activeSessionId) activeSessionId = msg.attached;
          sessionsOrder.forEach(s => ensureTermInstance(s.id));
          for (const [id] of termInstances) {
            if (!sessionsOrder.find(s => s.id === id)) {
              const rec = termInstances.get(id);
              rec?.container?.remove();
              termInstances.delete(id);
            }
          }
          const activeDied = !sessionsOrder.find(s => s.id === activeSessionId);
          if (activeDied && sessionsOrder.length) activeSessionId = sessionsOrder[0].id;
          if (activeSessionId) setActiveSession(activeSessionId, activeDied && activeSessionId !== prevActive);
          renderTerminalTabs();
          break;
        }
        case 'session-created': {
          sessionsOrder = msg.sessions || sessionsOrder;
          if (msg.sessionId) setActiveSession(msg.sessionId, false);
          renderTerminalTabs();
          break;
        }
        case 'session-switched': {
          if (msg.sessionId) setActiveSession(msg.sessionId, false);
          break;
        }
        case 'session-kill-rejected': {
          showToast(`can't close last terminal`);
          break;
        }
        case 'reload':
          reloadDisplay();
          break;
        case 'files-reload':
          reloadFilesView();
          break;
        case 'switch-workspace':
          if (msg.workspace) openWorkspaceFile(msg.workspace, msg.file);
          break;
        case 'switch-display':
          break; // legacy — display is now driven by tab list
      }
    };
    ws.onclose = () => {
      setWsStatus(false);
      if (!wsReconnectTimer) {
        wsReconnectTimer = setTimeout(() => { wsReconnectTimer = null; connectWs(); }, 2000);
      }
    };
    ws.onerror = () => ws.close();
  }
  function wsSend(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
  }
  function setWsStatus(connected) {
    const ind = $('#sync-indicator');
    if (!ind) return;
    ind.classList.toggle('connected', connected);
    ind.title = connected ? 'Connected' : 'Disconnected';
  }

  /* ── Terminal (xterm.js, multi-session) — preserved ──── */
  const termInstances = new Map();
  let term = null;
  let fitAddon = null;
  let activeSessionId = null;
  let sessionsOrder = [];

  // xterm.js doesn't read CSS variables, so themes are objects we apply
  // imperatively whenever the document theme flips.
  const XTERM_THEMES = {
    dark: {
      background: '#0d0c0b',
      foreground: '#d8d2c8',
      cursor: '#f08355',
      cursorAccent: '#0d0c0b',
      selectionBackground: 'rgba(240, 131, 85, 0.22)',
      black: '#0d0c0b',
      brightBlack: '#605a54',
      white: '#d8d2c8',
      brightWhite: '#f3eee5',
      blue: '#7e8ad9',
      brightBlue: '#9aa3e0',
      green: '#6ec79a',
      brightGreen: '#8fd6b1',
      red: '#e07158',
      brightRed: '#ea8e7a',
      yellow: '#d8a64a',
      brightYellow: '#e6bc70',
      cyan: '#6ec5c7',
      brightCyan: '#90d3d4',
      magenta: '#b896d4',
      brightMagenta: '#cdb0e0',
    },
    light: {
      background: '#fbf8f2',
      foreground: '#1f1a14',
      cursor: '#d96640',
      cursorAccent: '#fbf8f2',
      selectionBackground: 'rgba(217, 102, 64, 0.22)',
      black: '#1f1a14',
      brightBlack: '#5e564b',
      white: '#1f1a14',
      brightWhite: '#0f0c08',
      blue: '#5b66c0',
      brightBlue: '#7a86d4',
      green: '#3a8b6a',
      brightGreen: '#52a682',
      red: '#c25040',
      brightRed: '#d56b5a',
      yellow: '#a87a26',
      brightYellow: '#c79945',
      cyan: '#3e8c8e',
      brightCyan: '#5fa9aa',
      magenta: '#7e5e9a',
      brightMagenta: '#9c7cb8',
    },
  };
  function currentXtermTheme() {
    return XTERM_THEMES[document.documentElement.dataset.theme] || XTERM_THEMES.dark;
  }
  function applyXtermTheme(theme) {
    const t = XTERM_THEMES[theme] || XTERM_THEMES.dark;
    for (const rec of termInstances.values()) {
      try {
        rec.term.options.theme = t;
        // xterm.js v5 doesn't repaint the inline .xterm-viewport bg on
        // theme swap, so set it ourselves and force a refresh.
        const vp = rec.container?.querySelector('.xterm-viewport');
        if (vp) vp.style.backgroundColor = t.background;
        if (typeof rec.term.refresh === 'function' && rec.term.rows) {
          rec.term.refresh(0, rec.term.rows - 1);
        }
      } catch {}
    }
  }
  // Back-compat alias for code below
  const XTERM_THEME = XTERM_THEMES.dark;

  function ensureTermInstance(sessionId) {
    if (termInstances.has(sessionId)) return termInstances.get(sessionId);
    const host = $('#terminals');
    if (!host) return null;
    const container = document.createElement('div');
    container.className = 'terminal-instance';
    container.dataset.sessionId = sessionId;
    container.hidden = true;
    host.appendChild(container);
    const t = new Terminal({
      fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Menlo', 'Consolas', monospace",
      fontSize: 13,
      lineHeight: 1.1,
      letterSpacing: 0,
      cursorBlink: true,
      cursorStyle: 'bar',
      allowProposedApi: true,
      customGlyphs: true,
      theme: currentXtermTheme(),
    });
    t.attachCustomKeyEventHandler((e) => {
      if (e.type === 'keydown' && isTriptychShortcut(e)) return false;
      // Native paste: Ctrl+V (Win/Linux), Cmd+V (mac), Shift+Insert (Win).
      // xterm.js by default only honors Ctrl+Shift+V, which most users
      // don't know — so we intercept the OS-native combo, read the
      // clipboard ourselves, and feed bytes through the same path xterm
      // would use for a paste event.
      if (e.type === 'keydown') {
        const isCtrlV = (e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && e.code === 'KeyV';
        const isShiftInsert = e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey && e.code === 'Insert';
        if (isCtrlV || isShiftInsert) {
          e.preventDefault();
          if (navigator.clipboard && navigator.clipboard.readText) {
            navigator.clipboard.readText().then((text) => {
              if (text) wsSend({ type: 'terminal-input', sessionId, data: text });
            }).catch(() => {});
          }
          return false;
        }
      }
      return true;
    });
    const fit = new FitAddon.FitAddon();
    t.loadAddon(fit);
    t.open(container);
    t.onData((data) => wsSend({ type: 'terminal-input', sessionId, data }));
    const rec = { term: t, fitAddon: fit, container };
    termInstances.set(sessionId, rec);
    return rec;
  }

  function setActiveSession(sessionId, remote = true) {
    const rec = ensureTermInstance(sessionId);
    if (!rec) return;
    activeSessionId = sessionId;
    term = rec.term;
    fitAddon = rec.fitAddon;
    for (const [id, r] of termInstances) r.container.hidden = (id !== sessionId);
    if (remote) wsSend({ type: 'session-switch', sessionId });
    try { rec.term.focus(); } catch {}
    setTimeout(fitTerminal, 30);
    renderTerminalTabs();
  }

  function renderTerminalTabs() {
    const tPanel = panels[2];
    const tStrip = tPanel.querySelector('.tabstrip');
    const addBtn = tStrip.querySelector('.tab-add');
    // Remove existing terminal tabs
    tStrip.querySelectorAll('.tab').forEach(t => t.remove());
    sessionsOrder.forEach(s => {
      const tabEl = makeTabEl({ id: s.id, name: s.name || `claude #${s.id}`, closeable: true, kind: 'term' });
      if (s.id === activeSessionId) tabEl.classList.add('active');
      tStrip.insertBefore(tabEl, addBtn);
    });
    refreshCounts();
  }

  function cycleSession(dir) {
    if (sessionsOrder.length < 2) return;
    const idx = sessionsOrder.findIndex(s => s.id === activeSessionId);
    if (idx === -1) return;
    const next = sessionsOrder[(idx + dir + sessionsOrder.length) % sessionsOrder.length];
    setActiveSession(next.id);
  }

  let fitDebounce = null;
  function fitTerminal() {
    if (fitAddon && term) {
      try {
        fitAddon.fit();
        wsSend({ type: 'terminal-resize', sessionId: activeSessionId, cols: term.cols, rows: term.rows });
      } catch {}
    }
  }
  function debouncedFit() {
    clearTimeout(fitDebounce);
    fitDebounce = setTimeout(fitTerminal, 80);
  }
  window.addEventListener('resize', () => { positionGhosts(); debouncedFit(); });

  /* ── Display reload (chokidar broadcast) ─────────────── */
  function reloadDisplay() {
    const iframe = panels[1].querySelector('iframe.panel-frame');
    if (iframe?.contentWindow) {
      iframe.contentWindow.postMessage({ type: 'triptych-display-reload' }, '*');
    }
  }

  /* ── Files reload (chokidar broadcast on workspace/files/) ──
     Forward to every iframe in panel-a so the file manager
     (and any future workspace that cares) can re-fetch listings
     without a full page reload. */
  function reloadFilesView() {
    panels[0].querySelectorAll('iframe').forEach(f => {
      if (f?.contentWindow) {
        f.contentWindow.postMessage({ type: 'triptych-files-reload' }, '*');
      }
    });
  }

  /* ── Session save / restore ──────────────────────────── */
  function saveSession() {
    const tabs = [...openTabs.values()].map(t => ({ id: t.id, kind: t.kind, workspace: t.workspace, file: t.file, name: t.name }));
    const state = { tabs, activeId: activeWsId };
    // Use text/plain so express.raw catches the body as a Buffer.
    // express.json() (registered globally) hijacks application/json bodies
    // and parses them into objects, which the PUT /api/files/* route
    // then can't write to disk.
    fetch('/api/files/files/.session.json', {
      method: 'PUT',
      body: JSON.stringify(state),
      headers: { 'Content-Type': 'text/plain' },
    }).catch(() => {});
  }

  async function restoreSession() {
    try {
      const res = await fetch('/api/files/files/.session.json');
      if (res.ok) {
        const text = await res.text();
        if (text) {
          const state = JSON.parse(text);
          if (Array.isArray(state.tabs) && state.tabs.length) {
            state.tabs.forEach(t => ensureWorkspaceTab(t));
            const activeId = state.activeId && openTabs.has(state.activeId) ? state.activeId : state.tabs[0].id;
            activateWorkspaceTab(activeId);
            return;
          }
          // Legacy single-file session: lastFile + lastWorkspace
          if (state.lastFile && state.lastWorkspace) {
            openWorkspaceFile(state.lastWorkspace, state.lastFile);
            return;
          }
        }
      }
    } catch {}
    // Default: open file manager
    openWorkspaceFM();
  }

  /* ── Iframe shortcut binding (preserved) ─────────────── */
  function attachShortcuts(target) {
    if (!target || target.__triptychShortcutsBound) return;
    target.__triptychShortcutsBound = true;
    target.addEventListener('keydown', handleShortcut, true);
  }
  // Walk an iframe document recursively, attaching focus + shortcut handlers
  // to each level. Iframes don't propagate events to their parent document,
  // so each nested document needs its own listeners (e.g. default-display
  // hosts a #content-frame whose mousedowns we still want to focus the pane).
  function attachToDocTree(doc, panelIdx) {
    if (!doc) return;
    try {
      if (!doc.__triptychBound) {
        doc.__triptychBound = true;
        attachShortcuts(doc.defaultView);
        attachShortcuts(doc);
        if (panelIdx >= 0) {
          doc.addEventListener('mousedown', () => focusPanel(panelIdx, true), true);
        }
      }
      // Sync theme
      doc.documentElement.dataset.theme = document.documentElement.dataset.theme || 'dark';
      // Recurse into nested iframes
      doc.querySelectorAll('iframe').forEach(nested => {
        const visit = () => { try { attachToDocTree(nested.contentDocument, panelIdx); } catch {} };
        visit();
        nested.addEventListener('load', visit);
      });
    } catch {}
  }
  function bindIframeShortcuts(iframe) {
    if (!iframe) return;
    const panel = iframe.closest('.panel');
    const idx = panel ? panels.indexOf(panel) : -1;
    const tryBind = () => attachToDocTree(iframe.contentDocument, idx);
    tryBind();
    iframe.addEventListener('load', tryBind);
  }
  attachShortcuts(window);
  attachShortcuts(document);
  // Bind to display iframe + any future iframes
  bindIframeShortcuts(panels[1].querySelector('iframe.panel-frame'));
  new MutationObserver((muts) => {
    for (const m of muts) {
      for (const n of m.addedNodes) {
        if (n.nodeType === 1 && n.tagName === 'IFRAME') bindIframeShortcuts(n);
        if (n.nodeType === 1 && n.querySelectorAll) n.querySelectorAll('iframe').forEach(bindIframeShortcuts);
      }
    }
  }).observe(document.body, { childList: true, subtree: true });

  /* ── Hotkeys ──────────────────────────────────────────────
     Cross-platform via e.code (the physical key) instead of e.key.
     On macOS, Option+letter produces dead characters ("Œ" for Q,
     "œ" for q, "˙" for h, etc.), so e.key is unreliable for Alt
     shortcuts. e.code is layout-and-modifier independent.
     ──────────────────────────────────────────────────────── */
  const PANEL_TOGGLE_CODES = { Digit1: 'workspace', Digit2: 'display', Digit3: 'terminal' };
  const TAB_PREV = new Set(['KeyQ']);
  const TAB_NEXT = new Set(['KeyW']);
  const FOCUS_PREV = new Set(['KeyA', 'BracketLeft']);
  const FOCUS_NEXT = new Set(['KeyS', 'BracketRight']);
  const NEW_IN_PANEL = new Set(['KeyN']);
  const CLOSE_IN_PANEL = new Set(['KeyX']);
  const TRIPTYCH_CODES = new Set([
    ...Object.keys(PANEL_TOGGLE_CODES),
    ...TAB_PREV, ...TAB_NEXT, ...FOCUS_PREV, ...FOCUS_NEXT,
    ...NEW_IN_PANEL, ...CLOSE_IN_PANEL,
  ]);

  function isTriptychShortcut(e) {
    if (!e.altKey || e.ctrlKey || e.metaKey) return false;
    return TRIPTYCH_CODES.has(e.code);
  }

  function handleShortcut(e) {
    // Cmd (mac) / Ctrl (win) + K — open command bar
    if ((e.metaKey || e.ctrlKey) && !e.altKey && !e.shiftKey && e.code === 'KeyK') {
      e.preventDefault();
      e.stopImmediatePropagation();
      openCmdBar();
      return;
    }
    if (e.code === 'Escape') {
      if (cmdBar.classList.contains('open')) { closeCmdBar(); return; }
      const open = $$('.menu-pop.open');
      if (open.length) { open.forEach(m => { m.classList.remove('open'); m.classList.remove('shown'); }); return; }
    }
    if (cmdBar.classList.contains('open')) return;
    // Only bail for plain typing in form fields. With Alt/Ctrl/Meta held
    // the user isn't typing — and importantly, xterm uses a hidden
    // <textarea> to capture input, so this guard otherwise eats every
    // shortcut while focus is on the terminal (which is most of the time).
    const inForm = e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA');
    const noMods = !e.altKey && !e.ctrlKey && !e.metaKey;
    if (inForm && noMods) return;
    if (!isTriptychShortcut(e)) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const code = e.code;
    if (PANEL_TOGGLE_CODES[code]) { togglePane(PANEL_TOGGLE_CODES[code]); return; }
    if (TAB_PREV.has(code))   { dispatchTabKey(-1); return; }
    if (TAB_NEXT.has(code))   { dispatchTabKey(+1); return; }
    if (FOCUS_PREV.has(code)) { cycleFocus(-1); return; }
    if (FOCUS_NEXT.has(code)) { cycleFocus(+1); return; }
    if (NEW_IN_PANEL.has(code))   { handleNewInPanel(); return; }
    if (CLOSE_IN_PANEL.has(code)) { handleCloseInPanel(); return; }
  }

  function dispatchTabKey(dir) {
    const panel = panels[focusedIdx];
    const name = panel.dataset.panel;
    if (name === 'terminal') { cycleSession(dir); return; }
    const tabs = [...panel.querySelectorAll('.tabstrip .tab')];
    if (!tabs.length) return;
    const cur = tabs.findIndex(t => t.classList.contains('active'));
    const next = tabs[(Math.max(0, cur) + dir + tabs.length) % tabs.length];
    if (!next) return;
    handleTabClick(panel, next);
  }

  function cycleFocus(dir) {
    const visible = panels.map((p, i) => ({ p, i })).filter(x => !x.p.classList.contains('closed'));
    if (visible.length <= 1) return;
    const cur = visible.findIndex(x => x.i === focusedIdx);
    const nxt = visible[(cur + dir + visible.length) % visible.length];
    focusPanel(nxt.i);
  }

  function handleNewInPanel() {
    const panel = panels[focusedIdx];
    const name = panel.dataset.panel;
    if (name === 'terminal') wsSend({ type: 'session-create' });
    else if (name === 'workspace') openWorkspaceFM();
  }
  function handleCloseInPanel() {
    const panel = panels[focusedIdx];
    const name = panel.dataset.panel;
    if (name === 'terminal') {
      if (activeSessionId) wsSend({ type: 'session-kill', sessionId: activeSessionId });
    } else if (name === 'workspace') {
      if (activeWsId) closeWorkspaceTab(activeWsId);
    }
  }

  /* ── Command bar ─────────────────────────────────────── */
  let selectedIdx = 0;
  let cachedResults = [];

  function buildResults(query) {
    const q = (query || '').trim().toLowerCase();
    const results = [];
    // Workspace tabs (currently open)
    for (const t of openTabs.values()) {
      results.push({
        kind: 'tab', name: t.name, ctx: 'workspace',
        action: () => { focusPanel(0, true); activateWorkspaceTab(t.id); }
      });
    }
    // Display files
    dispStrip.querySelectorAll('.tab').forEach(t => {
      const fname = t.dataset.fname;
      if (!fname) return;
      results.push({
        kind: 'display', name: fname, ctx: 'display',
        action: () => { focusPanel(1, true); handleTabClick(panels[1], t); }
      });
    });
    // Terminal sessions
    sessionsOrder.forEach(s => {
      results.push({
        kind: 'session', name: s.name || `claude #${s.id}`, ctx: 'terminal',
        action: () => { focusPanel(2, true); setActiveSession(s.id); }
      });
    });
    // Static actions
    results.push({ kind: 'action', name: 'open file manager', ctx: 'Alt+N', action: () => { focusPanel(0, true); openWorkspaceFM(); } });
    results.push({ kind: 'action', name: 'new claude session', ctx: 'Alt+N (term)', action: () => { focusPanel(2, true); wsSend({ type: 'session-create' }); } });
    if (!q) return results.slice(0, 10);
    return results.map(r => ({ r, score: scoreMatch(r, q) }))
      .filter(x => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(x => x.r);
  }

  function scoreMatch(r, q) {
    const hay = (r.name + ' ' + r.ctx + ' ' + r.kind).toLowerCase();
    if (hay.includes(q)) return 10 + (r.name.toLowerCase().startsWith(q) ? 5 : 0);
    let i = 0;
    for (const c of q) {
      const f = hay.indexOf(c, i);
      if (f < 0) return 0;
      i = f + 1;
    }
    return 1;
  }

  function renderResults(query) {
    cachedResults = buildResults(query);
    cmdResults.innerHTML = cachedResults.length
      ? cachedResults.map((r, i) => `
          <div class="cmd-result ${i === 0 ? 'selected' : ''}" data-i="${i}">
            <span class="r-kind">${escapeHtml(r.kind)}</span>
            <span class="r-name">${escapeHtml(r.name)}</span>
            <span class="r-context">${escapeHtml(r.ctx)}</span>
          </div>`).join('')
      : `<div class="cmd-result" style="cursor:default;color:var(--text-dim);"><span class="r-kind">·</span><span class="r-name">no matches — <kbd style="font-family:var(--font-mono);background:var(--chrome);padding:1px 5px;border-radius:3px;border:1px solid var(--hairline);">⇧⏎</kbd> sends to claude</span></div>`;
    selectedIdx = 0;
    if ((query || '').trim().length > 2) sendHint.classList.add('show');
    else sendHint.classList.remove('show');
  }

  function openCmdBar() {
    cmdBar.hidden = false;
    cmdOverlay.classList.add('open');
    requestAnimationFrame(() => cmdBar.classList.add('open'));
    cmdInput.value = '';
    renderResults('');
    setTimeout(() => cmdInput.focus(), 60);
  }
  function closeCmdBar() {
    cmdBar.classList.remove('open');
    cmdOverlay.classList.remove('open');
    setTimeout(() => { cmdBar.hidden = true; }, 200);
  }
  cmdOverlay.addEventListener('click', closeCmdBar);
  $('#cmd-hint').addEventListener('click', openCmdBar);
  cmdInput.addEventListener('input', e => renderResults(e.target.value));
  cmdInput.addEventListener('keydown', e => {
    const items = [...cmdResults.querySelectorAll('.cmd-result[data-i]')];
    if (e.key === 'ArrowDown') { e.preventDefault(); selectedIdx = Math.min(items.length - 1, selectedIdx + 1); updateSelected(items); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); selectedIdx = Math.max(0, selectedIdx - 1); updateSelected(items); }
    else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const m = cachedResults[selectedIdx];
      if (m) { closeCmdBar(); m.action(); }
      else if (cmdInput.value.trim()) showToast(`no match — try <span class="accent">⇧⏎</span> to send to claude`);
    }
    else if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      const q = cmdInput.value.trim();
      if (!q) return;
      sendToTerminal(q);
      closeCmdBar();
    }
  });
  function updateSelected(items) {
    items.forEach((it, i) => it.classList.toggle('selected', i === selectedIdx));
    items[selectedIdx]?.scrollIntoView({ block: 'nearest' });
  }
  cmdResults.addEventListener('click', e => {
    const r = e.target.closest('.cmd-result[data-i]');
    if (!r) return;
    const m = cachedResults[parseInt(r.dataset.i, 10)];
    if (m) { closeCmdBar(); m.action(); }
  });
  function sendToTerminal(query) {
    const tPanel = panels[2];
    if (tPanel.classList.contains('closed')) togglePane('terminal');
    focusPanel(2, true);
    wsSend({ type: 'terminal-input', sessionId: activeSessionId, data: query + '\r' });
    showToast(`sent → <span class="accent">claude</span>`);
  }

  /* ── Settings & Help popovers ────────────────────────── */
  function openMenu(menu) {
    $$('.menu-pop.open').forEach(m => { if (m !== menu) { m.classList.remove('open'); m.classList.remove('shown'); } });
    menu.classList.add('open');
    requestAnimationFrame(() => requestAnimationFrame(() => menu.classList.add('shown')));
    setTimeout(() => document.addEventListener('mousedown', closeOnOutside, { once: true }), 0);
  }
  function closeOnOutside(e) {
    let closedAny = false;
    $$('.menu-pop.open').forEach(m => {
      if (!m.contains(e.target) && !e.target.closest('#settings-btn') && !e.target.closest('#help-btn')) {
        m.classList.remove('open'); m.classList.remove('shown'); closedAny = true;
      }
    });
    if (!closedAny) setTimeout(() => document.addEventListener('mousedown', closeOnOutside, { once: true }), 0);
  }
  $('#settings-btn').addEventListener('click', e => {
    e.stopPropagation();
    const menu = $('#settings-menu');
    if (menu.classList.contains('open')) { menu.classList.remove('open'); menu.classList.remove('shown'); }
    else openMenu(menu);
  });
  $('#help-btn').addEventListener('click', e => {
    e.stopPropagation();
    const menu = $('#help-menu');
    if (menu.classList.contains('open')) { menu.classList.remove('open'); menu.classList.remove('shown'); }
    else openMenu(menu);
  });

  /* ── Theme toggle ────────────────────────────────────── */
  function propagateThemeToIframes(theme, root) {
    (root || document).querySelectorAll('iframe').forEach(f => {
      try {
        if (f.contentDocument) {
          f.contentDocument.documentElement.dataset.theme = theme;
          // Recurse into nested iframes (default-display has its own
          // #content-frame loading the actual output file)
          propagateThemeToIframes(theme, f.contentDocument);
        }
      } catch {}
    });
  }
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('triptych-theme', theme); } catch {}
    const t = $('#theme-toggle');
    if (t) t.dataset.value = theme;
    propagateThemeToIframes(theme);
    applyXtermTheme(theme);
  }
  let savedTheme = 'dark';
  try { savedTheme = localStorage.getItem('triptych-theme') || 'dark'; } catch {}
  applyTheme(savedTheme);
  document.addEventListener('click', e => {
    const opt = e.target.closest('#theme-toggle [data-set]');
    if (opt) applyTheme(opt.dataset.set);
  });

  /* ── escapeHtml ──────────────────────────────────────── */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  /* ── Init ────────────────────────────────────────────── */
  refreshCounts();
  refreshGhostToggles();
  connectWs();
  startDisplayPoll();
  restoreSession();
  setTimeout(() => showToast(`triptych · <span class="accent">${cmdKeyLabel}</span> for command bar`), 800);

})();
