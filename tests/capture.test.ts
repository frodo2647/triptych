import { describe, it, expect, vi, beforeEach } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

// Load the capture script source
const captureSource = readFileSync(join(__dirname, '..', 'core', 'capture.js'), 'utf-8');

function createMockWindow() {
  const fetchCalls: { url: string; options: any }[] = [];

  const mockWindow: any = {
    Capture: null,
    SpeechRecognition: null,
    webkitSpeechRecognition: null,
    html2canvas: null,
    fetch: vi.fn(async (url: string, options: any) => {
      fetchCalls.push({ url, options });
      return { ok: true, json: async () => ({ ok: true }) };
    }),
    document: {
      body: {},
      querySelector: vi.fn(() => null),
    },
    setInterval: vi.fn(() => 42),
    clearInterval: vi.fn(),
    setTimeout: vi.fn((_fn: Function) => 43), // Don't auto-execute — tests call now() explicitly
    console: { warn: vi.fn(), log: vi.fn() },
  };

  return { mockWindow, fetchCalls };
}

function loadCapture(mockWindow: any) {
  const fn = new Function(
    'window', 'document', 'fetch', 'setInterval', 'clearInterval', 'setTimeout', 'console', 'html2canvas',
    captureSource + '\nreturn window.Capture;'
  );
  return fn(
    mockWindow, mockWindow.document, mockWindow.fetch,
    mockWindow.setInterval, mockWindow.clearInterval,
    mockWindow.setTimeout, mockWindow.console, mockWindow.html2canvas,
  );
}

describe('Capture script', () => {
  let mockWindow: any;
  let fetchCalls: any[];
  let Capture: any;

  beforeEach(() => {
    const mock = createMockWindow();
    mockWindow = mock.mockWindow;
    fetchCalls = mock.fetchCalls;
    Capture = loadCapture(mockWindow);
  });

  it('exposes Capture API on window', () => {
    expect(Capture).toBeDefined();
    expect(typeof Capture.init).toBe('function');
    expect(typeof Capture.setContext).toBe('function');
    expect(typeof Capture.setCaptureImage).toBe('function');
    expect(typeof Capture.now).toBe('function');
    expect(typeof Capture.onVoice).toBe('function');
    expect(typeof Capture.destroy).toBe('function');
  });

  it('init starts periodic timer', () => {
    Capture.init({ interval: 5000 });
    expect(mockWindow.setInterval).toHaveBeenCalled();
  });

  it('now() sends a snapshot POST', async () => {
    Capture.init({ interval: 30000 });
    fetchCalls.length = 0;

    await Capture.now();

    expect(fetchCalls.length).toBe(1);
    expect(fetchCalls[0].url).toBe('/api/snapshot');
    const body = JSON.parse(fetchCalls[0].options.body);
    expect(body).toHaveProperty('context');
  });

  it('sends context data in snapshot', async () => {
    Capture.init({ interval: 30000 });
    fetchCalls.length = 0;

    Capture.setContext({ selectedText: 'F=ma', page: 42 });
    await Capture.now();

    const body = JSON.parse(fetchCalls[0].options.body);
    expect(body.context.selectedText).toBe('F=ma');
    expect(body.context.page).toBe(42);
  });

  it('sends voice transcript', async () => {
    // Don't call init (to avoid the _isCapturing race from the auto-initial capture)
    await Capture.now('explain this');

    expect(fetchCalls.length).toBe(1);
    const body = JSON.parse(fetchCalls[0].options.body);
    expect(body.voice).toBe('explain this');
  });

  it('uses custom capture image function', async () => {
    const customCapture = vi.fn(async () => 'custom-base64-data');
    Capture.init({ interval: 30000, captureImage: customCapture });
    fetchCalls.length = 0;

    await Capture.now();

    expect(customCapture).toHaveBeenCalled();
    const body = JSON.parse(fetchCalls[0].options.body);
    expect(body.image).toBe('custom-base64-data');
  });

  it('uses getContext to refresh context before capture', async () => {
    let counter = 0;
    Capture.init({
      interval: 30000,
      getContext: () => ({ counter: ++counter }),
    });
    fetchCalls.length = 0;

    await Capture.now();

    const body = JSON.parse(fetchCalls[0].options.body);
    expect(body.context.counter).toBeGreaterThanOrEqual(1);
  });

  it('destroy stops timer', () => {
    Capture.init({ interval: 5000 });
    Capture.destroy();
    expect(mockWindow.clearInterval).toHaveBeenCalled();
  });

  it('skips duplicate captures when nothing changed', async () => {
    Capture.init({ interval: 30000 });
    fetchCalls.length = 0;

    await Capture.now();
    await Capture.now(); // same context, no image => should be skipped

    // Second call should be skipped (same hash)
    expect(fetchCalls.length).toBe(1);
  });
});
