/**
 * Triptych Capture Script
 *
 * Include in any viewer HTML via <script src="/core/capture.js"></script>
 * Then call Capture.init({ interval: 30000 }) to start periodic captures.
 *
 * Screenshot behavior:
 *   - Default: auto-loads html2canvas from CDN and captures the full page.
 *     Works for any viewer with zero config.
 *   - Override: pass captureImage to Capture.init() for viewer-specific capture.
 *     Example: workspaces/tldraw.html uses tldraw's getSvgString() for full-canvas export.
 *
 * The viewer can:
 *   Capture.setContext(data)      — attach metadata (selected text, page, etc.)
 *   Capture.setCaptureImage(fn)   — override the default screenshot function
 *   Capture.now()                 — trigger an immediate capture
 *   Capture.onVoice(fn)           — register callback for voice transcripts
 *
 * The terminal can trigger an instant capture via:
 *   curl -X POST http://localhost:3000/api/snapshot/now
 */
(function () {
  'use strict';

  const API_URL = '/api/snapshot';

  let _interval = 30000;
  let _timer = null;
  let _context = {};
  let _captureImageFn = null;
  let _voiceCallback = null;
  let _lastCaptureHash = null;
  let _recognition = null;
  let _isCapturing = false;
  let _html2canvasPromise = null;
  let _ws = null;
  let _commandHandlers = {};

  // ── html2canvas Lazy Loading ────────────────────────────────

  function loadHtml2Canvas() {
    if (typeof html2canvas === 'function') return Promise.resolve();
    if (_html2canvasPromise) return _html2canvasPromise;

    _html2canvasPromise = new Promise(function (resolve) {
      var script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
      script.onload = resolve;
      script.onerror = function () {
        console.warn('[capture] Failed to load html2canvas from CDN');
        resolve(); // resolve anyway — fallback to canvas capture
      };
      document.head.appendChild(script);
    });
    return _html2canvasPromise;
  }

  // ── Screenshot ─────────────────────────────────────────────

  /** Default screenshot: lazy-load html2canvas, else capture canvas elements. */
  async function defaultCaptureImage() {
    // Try to load and use html2canvas
    await loadHtml2Canvas();
    if (typeof html2canvas === 'function') {
      try {
        const canvas = await html2canvas(document.body, {
          useCORS: true,
          scale: 1,
          logging: false,
        });
        return canvasToBase64(canvas);
      } catch (err) {
        console.warn('[capture] html2canvas failed:', err);
      }
    }

    // Fallback: find the first <canvas> element and export it
    const canvasEl = document.querySelector('canvas');
    if (canvasEl) {
      try {
        return canvasToBase64(canvasEl);
      } catch (err) {
        console.warn('[capture] Canvas export failed:', err);
      }
    }

    // No screenshot available
    return null;
  }

  function canvasToBase64(canvas) {
    const dataUrl = canvas.toDataURL('image/png');
    // Strip the data:image/png;base64, prefix
    return dataUrl.split(',')[1] || null;
  }

  // ── Capture Logic ──────────────────────────────────────────

  async function doCapture(voice) {
    if (_isCapturing) return;
    _isCapturing = true;

    try {
      const captureFn = _captureImageFn || defaultCaptureImage;
      let image = null;

      try {
        image = await captureFn();
      } catch (err) {
        console.warn('[capture] Screenshot failed:', err);
      }

      // Skip duplicate captures (unless voice-triggered)
      if (!voice) {
        const contextStr = JSON.stringify(_context);
        const hash = image ? image.slice(0, 100) + contextStr : contextStr;
        if (hash === _lastCaptureHash) {
          return; // Nothing changed
        }
        _lastCaptureHash = hash;
      }

      const body = {
        image: image,
        context: _context,
      };
      if (voice) {
        body.voice = voice;
      }

      await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
    } catch (err) {
      console.warn('[capture] Failed to send snapshot:', err);
    } finally {
      _isCapturing = false;
    }
  }

  // ── WebSocket (capture-now trigger) ─────────────────────────

  function connectWebSocket() {
    try {
      var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      _ws = new WebSocket(protocol + '//' + location.host);

      _ws.onopen = function () {
        _ws.send(JSON.stringify({ type: 'register', role: 'viewer' }));
      };

      _ws.onmessage = function (event) {
        try {
          var msg = JSON.parse(event.data);
          if (msg.type === 'capture-now') {
            doCapture(null);
          } else if (msg.type === 'workspace-command') {
            handleCommand(msg);
          }
        } catch (e) { /* ignore */ }
      };

      _ws.onclose = function () {
        _ws = null;
        setTimeout(connectWebSocket, 3000);
      };
    } catch (e) {
      console.warn('[capture] WebSocket connect failed:', e);
    }
  }

  // ── Command Handling ───────────────────────────────────────

  function handleCommand(msg) {
    var command = msg.command;
    var params = msg.params || {};
    var requestId = msg.requestId;

    // Built-in: query-context
    if (command === 'query-context') {
      sendCommandResponse(requestId, _context);
      return;
    }

    var handler = _commandHandlers[command];
    if (!handler) {
      sendCommandResponse(requestId, { error: 'Unknown command: ' + command });
      return;
    }

    try {
      var result = handler(params);
      // Handle async handlers
      if (result && typeof result.then === 'function') {
        result.then(function (data) {
          sendCommandResponse(requestId, data);
        }).catch(function (err) {
          sendCommandResponse(requestId, { error: String(err) });
        });
      } else {
        sendCommandResponse(requestId, result);
      }
    } catch (err) {
      console.warn('[capture] Command handler error:', err);
      sendCommandResponse(requestId, { error: String(err) });
    }
  }

  function sendCommandResponse(requestId, data) {
    if (_ws && _ws.readyState === WebSocket.OPEN) {
      _ws.send(JSON.stringify({ type: 'command-response', requestId: requestId, data: data }));
    }
  }

  // ── Voice Input ────────────────────────────────────────────

  function setupVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('[capture] Speech recognition not available');
      return;
    }

    _recognition = new SpeechRecognition();
    _recognition.lang = 'en-US';
    _recognition.continuous = false;
    _recognition.interimResults = false;

    _recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript;
      if (_voiceCallback) _voiceCallback(transcript);
      // Trigger immediate capture with voice
      doCapture(transcript);
    };

    _recognition.onerror = function (event) {
      console.warn('[capture] Voice error:', event.error);
    };
  }

  // ── Periodic Timer ─────────────────────────────────────────

  function startTimer() {
    stopTimer();
    _timer = setInterval(() => doCapture(null), _interval);
  }

  function stopTimer() {
    if (_timer) {
      clearInterval(_timer);
      _timer = null;
    }
  }

  // ── Public API ─────────────────────────────────────────────

  const Capture = {
    /**
     * Initialize capture with options.
     * @param {Object} options
     * @param {number} [options.interval=30000] Capture interval in ms
     * @param {Function} [options.captureImage] Custom async function returning base64 PNG
     * @param {Function} [options.getContext] Function called before each capture to get fresh context
     * @param {boolean} [options.voice=false] Enable voice input
     */
    init: function (options) {
      options = options || {};
      _interval = options.interval || 30000;

      if (options.captureImage) {
        _captureImageFn = options.captureImage;
      }

      if (options.getContext) {
        // Wrap context getter: update _context before each capture
        const originalCapture = doCapture;
        const getCtx = options.getContext;
        // Override doCapture to refresh context first
        const wrappedCapture = async function (voice) {
          try {
            _context = { ..._context, ...getCtx() };
          } catch (e) {
            console.warn('[capture] getContext failed:', e);
          }
          return originalCapture(voice);
        };
        // Patch the timer to use wrapped version
        doCapture = wrappedCapture;
      }

      if (options.voice) {
        setupVoice();
      }

      // Start periodic captures
      startTimer();

      // Do an initial capture after a short delay (let the viewer render)
      setTimeout(() => doCapture(null), 1000);

      // Connect WebSocket for capture-now triggers
      connectWebSocket();
    },

    /** Update context metadata. Merged with existing context. */
    setContext: function (data) {
      _context = { ..._context, ...data };
    },

    /** Override the screenshot capture function. Should return base64 PNG string. */
    setCaptureImage: function (fn) {
      _captureImageFn = fn;
    },

    /** Trigger an immediate capture. Returns a promise. */
    now: function (voice) {
      return doCapture(voice || null);
    },

    /** Register a callback for when voice input is received. */
    onVoice: function (fn) {
      _voiceCallback = fn;
    },

    /** Start voice listening (call on button press). */
    startListening: function () {
      if (_recognition) {
        try {
          _recognition.start();
        } catch (e) {
          // May already be started
        }
      }
    },

    /** Stop voice listening (call on button release). */
    stopListening: function () {
      if (_recognition) {
        try {
          _recognition.stop();
        } catch (e) {
          // May already be stopped
        }
      }
    },

    /** Register command handlers for workspace commands from Claude. */
    registerCommands: function (handlers) {
      Object.assign(_commandHandlers, handlers);
    },

    /** Stop all capture activity. */
    destroy: function () {
      stopTimer();
      if (_recognition) {
        try { _recognition.abort(); } catch (e) { /* noop */ }
        _recognition = null;
      }
      if (_ws) {
        try { _ws.close(); } catch (e) { /* noop */ }
        _ws = null;
      }
      _context = {};
      _captureImageFn = null;
      _voiceCallback = null;
    },
  };

  // Expose globally
  window.Capture = Capture;
})();
