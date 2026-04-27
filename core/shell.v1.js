/* ── Triptych Shell ──────────────────────────────────────────
   Top bar with tab buttons. Panels below. No framework.
   ──────────────────────────────────────────────────────────── */

(function () {
  'use strict';

  // ── Parse URL params ────────────────────────────────────
  const params = new URLSearchParams(location.search);
  const showParam = (params.get('show') || 'all').toLowerCase();
  const ALL_PANELS = ['workspace', 'display', 'terminal'];
  const visiblePanels = showParam === 'all'
    ? [...ALL_PANELS]
    : showParam.split(',').map(s => s.trim()).filter(p => ALL_PANELS.includes(p));

  if (visiblePanels.length === 0) visiblePanels.push(...ALL_PANELS);

  // ── DOM refs ────────────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];
  const panels = {};
  const seams = {};
  const tabBtns = {};
  const panelLabels = {};

  ALL_PANELS.forEach(name => {
    panels[name] = $(`.panel[data-panel="${name}"]`);
    tabBtns[name] = $(`.tab-btn[data-panel="${name}"]`);
    panelLabels[name] = $(`.panel-label[data-panel="${name}"]`);
  });

  $$('.seam').forEach(el => {
    const key = el.dataset.left + '-' + el.dataset.right;
    seams[key] = el;
  });

  // ── Show/hide panels ───────────────────────────────────
  function applyLayout() {
    ALL_PANELS.forEach(name => {
      const show = visiblePanels.includes(name);
      panels[name].classList.toggle('hidden', !show);
      tabBtns[name].classList.toggle('active', show);
      tabBtns[name].classList.toggle('inactive', !show);
      tabBtns[name].setAttribute('aria-pressed', show);
      // Clear inline flex on toggle so panels return to equal distribution
      if (!panels[name].style.flex || !show) {
        panels[name].style.flex = '';
      }
    });

    // Show seams only between adjacent visible panels
    Object.entries(seams).forEach(([key, el]) => {
      const [left, right] = key.split('-');
      const leftVisible = visiblePanels.includes(left);
      const rightVisible = visiblePanels.includes(right);
      const leftIdx = ALL_PANELS.indexOf(left);
      const rightIdx = ALL_PANELS.indexOf(right);
      const between = ALL_PANELS.slice(leftIdx + 1, rightIdx);
      const hasVisibleBetween = between.some(p => visiblePanels.includes(p));
      el.classList.toggle('hidden', !(leftVisible && rightVisible && !hasVisibleBetween));
    });

    const url = new URL(location);
    if (visiblePanels.length === ALL_PANELS.length) {
      url.searchParams.delete('show');
    } else {
      url.searchParams.set('show', visiblePanels.join(','));
    }
    history.replaceState(null, '', url);

    syncLabels();

    if (visiblePanels.includes('terminal')) {
      setTimeout(fitTerminal, 50);
    }

    if (visiblePanels.includes('terminal') && !term) {
      initTerminal();
    }
  }

  // ── Sync label positions with panels ───────────────────
  function syncLabels() {
    ALL_PANELS.forEach(name => {
      const panel = panels[name];
      const label = panelLabels[name];
      if (!visiblePanels.includes(name)) {
        label.classList.add('collapsed');
        label.style.flex = '';
      } else {
        label.classList.remove('collapsed');
        // Copy inline flex from panel (if set by seam drag)
        label.style.flex = panel.style.flex || '';
      }
    });
  }

  function togglePanel(name) {
    const idx = visiblePanels.indexOf(name);
    if (idx !== -1) {
      if (visiblePanels.length <= 1) return;
      visiblePanels.splice(idx, 1);
    } else {
      visiblePanels.push(name);
    }
    applyLayout();
  }

  // ── Tab button clicks ──────────────────────────────────
  $$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => togglePanel(btn.dataset.panel));
  });

  // ── Seam drag (resize) ─────────────────────────────────
  $$('.seam').forEach(seam => {
    const isVertical = () => window.innerWidth <= 768;

    seam.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      seam.classList.add('dragging');
      document.body.classList.add('resizing');
      seam.setPointerCapture(e.pointerId);

      const leftPanel = panels[seam.dataset.left];
      const rightPanel = panels[seam.dataset.right];
      const container = document.getElementById('triptych');
      const containerRect = container.getBoundingClientRect();
      const MIN_PCT = 12;

      const onMove = (ev) => {
        if (isVertical()) {
          const y = ev.clientY - containerRect.top;
          const pct = (y / containerRect.height) * 100;
          if (pct < MIN_PCT || pct > (100 - MIN_PCT)) return;
          leftPanel.style.flex = `0 0 ${pct}%`;
          rightPanel.style.flex = `0 0 ${100 - pct}%`;
        } else {
          const leftRect = leftPanel.getBoundingClientRect();
          const rightRect = rightPanel.getBoundingClientRect();
          const combinedWidth = leftRect.width + rightRect.width;
          const x = ev.clientX - leftRect.left;
          const leftPct = (x / combinedWidth) * 100;
          const rightPct = 100 - leftPct;
          if (leftPct < MIN_PCT || rightPct < MIN_PCT) return;
          leftPanel.style.flex = `${leftPct} 1 0%`;
          rightPanel.style.flex = `${rightPct} 1 0%`;
        }
        syncLabels();
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

  // ── WebSocket ──────────────────────────────────────────
  let ws = null;
  let wsReconnectTimer = null;

  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}`);

    ws.onopen = () => {
      setWsStatus(true);
      if (visiblePanels.includes('workspace')) wsSend({ type: 'register', role: 'panel-a' });
      if (visiblePanels.includes('display'))   wsSend({ type: 'register', role: 'panel-b' });
      if (visiblePanels.includes('terminal'))  wsSend({ type: 'register', role: 'terminal' });
    };

    ws.onmessage = (event) => {
      let msg;
      try { msg = JSON.parse(event.data); } catch { return; }

      switch (msg.type) {
        case 'terminal-data': {
          // Route to the per-session terminal instance. Falls back to the
          // default (Phase 3 and earlier) terminal if no sessionId is present.
          const sid = msg.sessionId;
          if (sid && termInstances.has(sid)) {
            termInstances.get(sid).term.write(msg.data);
          } else if (term) {
            term.write(msg.data);
          }
          break;
        }
        case 'session-list': {
          const prevActive = activeSessionId;
          sessionsOrder = msg.sessions || [];
          if (msg.attached && !activeSessionId) activeSessionId = msg.attached;
          // Ensure each live session has a Terminal instance so data arrives
          // even for non-focused sessions (preserves scrollback on switch).
          sessionsOrder.forEach(s => ensureTermInstance(s.id));
          // Remove instances for sessions that have died.
          for (const [id] of termInstances) {
            if (!sessionsOrder.find(s => s.id === id)) {
              const rec = termInstances.get(id);
              rec?.container?.remove();
              termInstances.delete(id);
            }
          }
          const activeDied = !sessionsOrder.find(s => s.id === activeSessionId);
          if (activeDied && sessionsOrder.length) {
            activeSessionId = sessionsOrder[0].id;
          }
          // If our active session died, tell the server about the new one so
          // its attachedSessionId stays in sync (the server also re-attaches
          // orphans server-side, but this closes the window between the
          // client's UI switch and the next user input).
          if (activeSessionId) {
            setActiveSession(activeSessionId, /*remote*/ activeDied && activeSessionId !== prevActive);
          }
          renderTerminalTabs();
          break;
        }
        case 'session-created': {
          sessionsOrder = msg.sessions || sessionsOrder;
          if (msg.sessionId) setActiveSession(msg.sessionId, /*remote*/false);
          renderTerminalTabs();
          break;
        }
        case 'session-switched': {
          if (msg.sessionId) setActiveSession(msg.sessionId, /*remote*/false);
          break;
        }
        case 'session-kill-rejected': {
          // Currently only reason: last-session. No-op; keybind is idempotent.
          break;
        }
        case 'reload':
          reloadDisplay();
          break;
        case 'switch-workspace':
          if (msg.workspace) loadWorkspace(msg.workspace, msg.file);
          break;
        case 'switch-display':
          if (msg.display) loadDisplay(msg.display);
          break;
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
    const dot = $('#ws-dot');
    dot.className = connected ? 'dot dot-on' : 'dot dot-off';
    dot.title = connected ? 'Connected' : 'Disconnected';
  }

  // ── Terminal (xterm.js, multi-session) ─────────────────
  // termInstances: sessionId -> { term, fitAddon, container }
  // `term` alias tracks the active session for back-compat with other code
  // in this file that expects a singleton (e.g. fullscreen's fitTerminal).
  const termInstances = new Map();
  let term = null;
  let fitAddon = null;
  let activeSessionId = null;
  let sessionsOrder = [];  // [{id, name, createdAt}] from server

  const XTERM_THEME = {
    background: '#151210',
    foreground: '#d8d0c8',
    cursor: '#d8d0c8',
    cursorAccent: '#151210',
    selectionBackground: 'rgba(192, 128, 96, 0.2)',
    black: '#151210',
    brightBlack: '#605a54',
    white: '#d8d0c8',
    brightWhite: '#eae7e3',
    blue: '#7a80d5',
    brightBlue: '#9a9ee0',
    green: '#3cc497',
    brightGreen: '#68d4ad',
    red: '#d47567',
    brightRed: '#e09a8e',
    yellow: '#c4a045',
    brightYellow: '#dbb870',
    cyan: '#48b5c5',
    brightCyan: '#75c5d2',
    magenta: '#b080c5',
    brightMagenta: '#c298d5',
  };

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
      theme: XTERM_THEME,
    });
    // Let our Alt+* shortcuts bubble to the window handler instead of being
    // consumed as a PTY escape sequence. Returning false tells xterm to skip.
    t.attachCustomKeyEventHandler((e) => {
      if (e.type === 'keydown' && isTriptychShortcut(e)) return false;
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

  function initTerminal() {
    // Creates a *placeholder* terminal for the session-1 back-compat PTY.
    // The real wiring happens once the server sends us the session-list on
    // register, at which point we'll ensure instances for all live sessions.
    if (!termInstances.size) {
      const rec = ensureTermInstance('1');
      if (rec) {
        activeSessionId = '1';
        term = rec.term;
        fitAddon = rec.fitAddon;
        rec.container.hidden = false;
        setTimeout(fitTerminal, 30);
      }
    }
  }

  function setActiveSession(sessionId, remote = true) {
    const rec = ensureTermInstance(sessionId);
    if (!rec) return;
    activeSessionId = sessionId;
    term = rec.term;
    fitAddon = rec.fitAddon;
    for (const [id, r] of termInstances) {
      r.container.hidden = (id !== sessionId);
    }
    // Notify the server so input/resize routing matches our view.
    if (remote) wsSend({ type: 'session-switch', sessionId });
    // Focus synchronously — inside setTimeout the browser loses the user
    // gesture context and may refuse cross-frame focus moves, leaving the
    // terminal visible but unresponsive to typing. Size can wait a tick for
    // layout to settle; focus cannot.
    try { rec.term.focus(); } catch { /* noop */ }
    if (visiblePanels.includes('terminal')) setFocus('terminal');
    setTimeout(fitTerminal, 30);
    renderTerminalTabs();
  }

  function renderTerminalTabs() {
    const el = $('#terminal-tabs');
    if (!el) return;
    if (!sessionsOrder.length || sessionsOrder.length < 2) {
      el.hidden = true;
      el.innerHTML = '';
      return;
    }
    el.hidden = false;
    el.innerHTML = '';
    sessionsOrder.forEach((s, i) => {
      const tab = document.createElement('button');
      tab.className = 'term-tab' + (s.id === activeSessionId ? ' active' : '');
      tab.innerHTML = '<span>' + escapeHtml(s.name) + '</span>'
        + (i < 9 ? '<span class="term-tab-key">' + (i + 1) + '</span>' : '');
      tab.onclick = () => {
        if (s.id !== activeSessionId) setActiveSession(s.id);
      };
      el.appendChild(tab);
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g,
      c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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
        wsSend({ type: 'terminal-resize', sessionId: activeSessionId,
                 cols: term.cols, rows: term.rows });
      } catch { /* noop */ }
    }
  }

  function debouncedFit() {
    clearTimeout(fitDebounce);
    fitDebounce = setTimeout(fitTerminal, 80);
  }

  // ── Workspace navigation ─────────────────────────────
  let currentWorkspace = null;
  let currentFile = null;
  const backBtn = $('#back-btn');

  function loadWorkspace(id, file) {
    currentWorkspace = id;
    currentFile = file || null;
    const iframe = panels.workspace?.querySelector('.panel-frame');
    if (iframe) {
      let src = `/workspaces/${id}.html`;
      if (file) src += `?file=${encodeURIComponent(file)}`;
      iframe.src = src;
    }
    updateBackButton();
    saveSession();
  }

  function goToFiles() {
    currentWorkspace = null;
    currentFile = null;
    const iframe = panels.workspace?.querySelector('.panel-frame');
    if (iframe) iframe.src = '/workspaces/files.html';
    updateBackButton();
    saveSession();
  }

  function updateBackButton() {
    if (backBtn) {
      backBtn.classList.toggle('back-visible', currentWorkspace !== null);
    }
  }

  if (backBtn) {
    backBtn.addEventListener('click', goToFiles);
  }

  // Listen for messages from workspace iframes (files.html sends open-file)
  window.addEventListener('message', (e) => {
    if (e.data?.type === 'open-file') {
      loadWorkspace(e.data.workspace, e.data.file);
    }
  });

  // ── Session state ──────────────────────────────────────
  function saveSession() {
    try {
      const state = currentFile ? { lastFile: currentFile, lastWorkspace: currentWorkspace } : {};
      fetch('/api/files/files/.session.json', {
        method: 'PUT',
        body: JSON.stringify(state),
        headers: { 'Content-Type': 'application/json' },
      }).catch(() => {});
    } catch {}
  }

  async function restoreSession() {
    try {
      const res = await fetch('/api/files/files/.session.json');
      if (res.ok) {
        const state = await res.json();
        if (state.lastFile && state.lastWorkspace) {
          loadWorkspace(state.lastWorkspace, state.lastFile);
          return;
        }
      }
    } catch {}
    // Default: show file browser
    goToFiles();
  }

  // ── Display ────────────────────────────────────────────
  let currentDisplay = null;

  function loadDisplay(id) {
    currentDisplay = id;
    const iframe = panels.display?.querySelector('.panel-frame');
    if (iframe) iframe.src = `/core/${id}.html`;
  }

  function reloadDisplay() {
    const iframe = panels.display?.querySelector('.panel-frame');
    if (iframe && iframe.src) {
      const url = new URL(iframe.src);
      url.searchParams.set('_t', Date.now());
      iframe.src = url.toString();
    }
  }

  // ── Restore button clicks ──────────────────────────────
  $$('.restore-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      togglePanel(btn.dataset.panel);
    });
  });

  // ── Focus tracker ─────────────────────────────────────
  // Which panel last received user attention. Drives within-panel key routing
  // (Alt+Q/W/1/2/3) and Ctrl+Tab cycling. Defaults to first visible panel.
  let focusedPanel = visiblePanels[0] || 'workspace';

  function setFocus(name) {
    if (!visiblePanels.includes(name)) return;
    focusedPanel = name;
    ALL_PANELS.forEach(p => panels[p]?.classList.toggle('focused', p === name));
  }

  ALL_PANELS.forEach(name => {
    panels[name]?.addEventListener('pointerdown', () => setFocus(name), true);
    // Iframes swallow pointerdown after load; mouseenter is a decent fallback
    // when the user's cursor crosses into a panel. We only treat it as focus
    // if there's no current window focus competing.
    panels[name]?.addEventListener('mouseenter', () => {
      if (!document.hasFocus() || document.activeElement === document.body) {
        setFocus(name);
      }
    });
  });
  // Ensure initial state is reflected on the DOM
  setFocus(focusedPanel);

  function cycleFocus(dir) {
    // Cycle through visible panels in ALL_PANELS order.
    const visible = ALL_PANELS.filter(p => visiblePanels.includes(p));
    if (visible.length <= 1) return;
    const idx = visible.indexOf(focusedPanel);
    const next = visible[(idx + dir + visible.length) % visible.length];
    setFocus(next);
    // If focusing terminal, give xterm the keyboard; otherwise blur xterm.
    if (next === 'terminal' && term) term.focus();
    else if (term && document.activeElement && panels.terminal?.contains(document.activeElement)) {
      document.activeElement.blur?.();
    }
  }

  // Send an action into the focused panel. Iframe panels (workspace, display)
  // receive it via postMessage; the terminal panel handles it locally since
  // it's not an iframe (xterm.js renders directly into the shell DOM).
  function dispatchToFocused(action) {
    if (focusedPanel === 'terminal') {
      handleTerminalAction(action);
      return;
    }
    const panel = panels[focusedPanel];
    if (!panel) return;
    const iframe = panel.querySelector('iframe.panel-frame');
    if (iframe?.contentWindow) {
      iframe.contentWindow.postMessage({ type: 'triptych-key', action }, '*');
    }
  }

  function handleTerminalAction(action) {
    switch (action) {
      case 'new-session':
        wsSend({ type: 'session-create' });
        break;
      case 'kill-session':
        if (activeSessionId) wsSend({ type: 'session-kill', sessionId: activeSessionId });
        break;
      case 'prev-tab': cycleSession(-1); break;
      case 'next-tab': cycleSession(1); break;
      case 'tab-1': case 'tab-2': case 'tab-3': {
        const n = parseInt(action.slice(4), 10) - 1;
        const target = sessionsOrder[n];
        if (target && target.id !== activeSessionId) setActiveSession(target.id);
        break;
      }
    }
  }

  // ── Keyboard shortcuts ────────────────────────────────
  // All shortcuts are left-hand, single-handed reachable.
  //   Alt+1/2/3  toggle workspace / display / chat panel
  //   Alt+Q / W  prev / next tab inside the focused panel
  //   Alt+A / S  cycle panel focus (prev / next)
  //   Alt+N / X  new / close Claude session (global)
  const PANEL_TOGGLE_DIGITS = { '1': 'workspace', '2': 'display', '3': 'terminal' };
  const SHORTCUT_KEYS = new Set(['1', '2', '3', 'q', 'w', 'a', 's', 'n', 'x']);

  // Reliable modifier check — e.key='Alt' itself arrives with altKey=true, so
  // we also require the key to be something other than a modifier.
  function isTriptychShortcut(e) {
    if (!e.altKey || e.ctrlKey || e.metaKey) return false;
    const key = (e.key || '').toLowerCase();
    return SHORTCUT_KEYS.has(key);
  }

  function handleShortcut(e) {
    if (!isTriptychShortcut(e)) return;
    // Beat xterm, iframe handlers, and browser menu accelerators.
    e.preventDefault();
    e.stopImmediatePropagation();

    const key = (e.key || '').toLowerCase();

    if (PANEL_TOGGLE_DIGITS[key]) {
      const target = PANEL_TOGGLE_DIGITS[key];
      const wasVisible = visiblePanels.includes(target);
      togglePanel(target);
      if (!wasVisible && visiblePanels.includes(target)) setFocus(target);
      return;
    }

    if (key === 'q') { dispatchToFocused('prev-tab'); return; }
    if (key === 'w') { dispatchToFocused('next-tab'); return; }
    if (key === 'a') { cycleFocus(-1); return; }
    if (key === 's') { cycleFocus(1); return; }
    if (key === 'n') { handleTerminalAction('new-session'); return; }
    if (key === 'x') { handleTerminalAction('kill-session'); return; }
  }

  // Same-origin iframes (workspace, display) keep their own event loop — the
  // parent window never sees keydowns fired inside them. Bind the same handler
  // to every target that might own keyboard focus: parent window, parent
  // document, and each iframe document (re-bind on navigation since iframes
  // get a fresh document when src changes).
  function attachShortcuts(target) {
    if (!target || target.__triptychShortcutsBound) return;
    target.__triptychShortcutsBound = true;
    target.addEventListener('keydown', handleShortcut, true);
  }

  attachShortcuts(window);
  attachShortcuts(document);

  function bindIframeShortcuts(iframe) {
    if (!iframe) return;
    const tryBind = () => {
      try {
        attachShortcuts(iframe.contentWindow);
        attachShortcuts(iframe.contentDocument);
      } catch { /* cross-origin — can't reach */ }
    };
    tryBind();
    iframe.addEventListener('load', tryBind);
  }

  for (const p of ['workspace', 'display']) {
    bindIframeShortcuts(panels[p]?.querySelector('.panel-frame'));
  }

  // Some addons (e.g. d3 scaffolds) replace iframe.src at runtime via
  // shell.js API. MutationObserver catches any iframe added later.
  new MutationObserver((muts) => {
    for (const m of muts) {
      for (const n of m.addedNodes) {
        if (n.nodeType === 1 && n.tagName === 'IFRAME') bindIframeShortcuts(n);
        if (n.nodeType === 1 && n.querySelectorAll) {
          n.querySelectorAll('iframe').forEach(bindIframeShortcuts);
        }
      }
    }
  }).observe(document.body, { childList: true, subtree: true });

  // ── Shortcuts overlay ─────────────────────────────────
  const shortcutsBtn = $('#shortcuts-btn');
  const shortcutsOverlay = $('#shortcuts-overlay');
  const shortcutsClose = $('#shortcuts-close');
  function toggleShortcuts(show) {
    if (!shortcutsOverlay) return;
    const open = show ?? shortcutsOverlay.hasAttribute('hidden');
    if (open) shortcutsOverlay.removeAttribute('hidden');
    else shortcutsOverlay.setAttribute('hidden', '');
  }
  shortcutsBtn?.addEventListener('click', () => toggleShortcuts());
  shortcutsClose?.addEventListener('click', () => toggleShortcuts(false));
  shortcutsOverlay?.addEventListener('click', (e) => {
    if (e.target === shortcutsOverlay) toggleShortcuts(false);
  });

  // ── Fullscreen toggle ─────────────────────────────────
  const fullscreenBtn = $('#fullscreen-btn');
  const topbarEl = $('#topbar');
  let peekReady = false;

  function setFullscreen(on) {
    if (on) {
      document.body.classList.add('fullscreen');
      peekReady = false;
      topbarEl.style.top = `-${topbarEl.offsetHeight}px`;
      // Use browser Fullscreen API
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch(() => {});
      }
      setTimeout(() => { peekReady = true; }, 600);
    } else {
      document.body.classList.remove('fullscreen');
      peekReady = false;
      topbarEl.style.top = '';
      topbarEl.style.transition = '';
      // Exit browser fullscreen if active
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      }
    }
    setTimeout(fitTerminal, 50);
  }

  if (fullscreenBtn) {
    fullscreenBtn.addEventListener('click', () => {
      setFullscreen(!document.body.classList.contains('fullscreen'));
    });
  }

  // Sync if user exits fullscreen via Escape or browser controls
  document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement && document.body.classList.contains('fullscreen')) {
      document.body.classList.remove('fullscreen');
      peekReady = false;
      topbarEl.style.top = '';
      topbarEl.style.transition = '';
      setTimeout(fitTerminal, 50);
    }
  });

  // Peek zone: mouse near top edge reveals topbar in fullscreen
  document.addEventListener('mousemove', (e) => {
    if (!document.body.classList.contains('fullscreen') || !peekReady) return;
    if (e.clientY <= 6) {
      topbarEl.style.transition = 'top 0.2s ease-out';
      topbarEl.style.top = '0px';
    }
  });

  topbarEl.addEventListener('mouseleave', () => {
    if (document.body.classList.contains('fullscreen')) {
      topbarEl.style.transition = 'top 0.2s ease-out';
      topbarEl.style.top = `-${topbarEl.offsetHeight}px`;
    }
  });

  // ── Init ───────────────────────────────────────────────
  applyLayout();
  connectWs();
  if (visiblePanels.includes('terminal')) initTerminal();
  loadDisplay('default-display');
  restoreSession();

})();
