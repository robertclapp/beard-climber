'use strict';

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(process.env.BEARD_GAME_ROOT || path.join(__dirname, '..'));
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)]
  .map((match, i) => new vm.Script(match[1], { filename: `index-inline-${i}.js` }));
const noop = () => {};

/** Runs the shipped scripts and pack assets, not a copy of the game logic.
 * Canvas/DOM/audio are stubs; clocks, timers, storage and input are deterministic.
 * This verifies state transitions and hit boxes, not pixels or real-browser APIs.
 */
async function boot({ width = 1280, height = 800, dpr = 1, query = '',
  storage = {}, deferPacks = false, touch = false, seed = 1 } = {}) {
  let clock = 0;
  let frame;
  let nextTimer = 1;
  let randomState = seed >>> 0;
  const listeners = new Map();
  const timers = new Map();
  const pendingScripts = [];
  const drawCalls = [];
  const store = new Map(Object.entries(storage));
  const math = Object.create(Math);
  math.random = () => ((randomState = (1664525 * randomState + 1013904223) >>> 0) / 0x100000000);
  const addListener = (name, callback) => {
    if (!listeners.has(name)) listeners.set(name, []);
    listeners.get(name).push(callback);
  };
  const context = new Proxy({
    getImageData: (x, y, w, h) => ({ data: new Uint8ClampedArray(w * h * 4), width: w, height: h }),
    measureText: (s) => ({ width: String(s).length * 6 }),
    createLinearGradient: () => ({ addColorStop: noop }),
    createRadialGradient: () => ({ addColorStop: noop }),
    fillRect(x, y, w, h) { drawCalls.push({ fillStyle: this.fillStyle, x, y, w, h }); },
  }, { get: (target, key) => key in target ? target[key] : noop });
  const makeCanvas = () => ({
    width: 224, height: 256, style: {}, getContext: () => context, toDataURL: () => '',
    getBoundingClientRect() {
      const w = parseFloat(this.style.width) || this.width;
      const h = parseFloat(this.style.height) || this.height;
      return { left: (width - w) / 2, top: (height - h) / 2, width: w, height: h };
    },
  });
  const canvas = makeCanvas();
  let sandbox;
  const evaluatePack = (script) => {
    // Only repository-owned same-origin pack files can be executed by this harness.
    if (!/^assets\/world\d+\.js$/.test(script.src)) throw new Error(`Unexpected script: ${script.src}`);
    vm.runInContext(fs.readFileSync(path.join(root, script.src), 'utf8'), sandbox, { filename: script.src });
    if (script.onload) script.onload();
  };
  const document = {
    body: { style: {} }, hidden: false,
    getElementById: (id) => id === 'game' ? canvas : { clientWidth: width, clientHeight: height },
    createElement: (tag) => tag === 'canvas' ? makeCanvas() : {},
    addEventListener: addListener,
    head: { appendChild(script) {
      if (deferPacks) pendingScripts.push(script);
      else evaluatePack(script);
      return script;
    } },
  };
  class FakeImage {
    constructor() { this.complete = true; this.width = 1024; this.height = 1024; }
    decode() { return Promise.resolve(); }
  }
  const localStorage = {
    getItem: (key) => store.get(key) ?? null,
    setItem: (key, value) => store.set(key, String(value)),
    removeItem: (key) => store.delete(key),
    clear: () => store.clear(),
  };
  const setTimer = (callback, delay = 0) => {
    const id = nextTimer++;
    timers.set(id, { callback, at: clock + Number(delay) });
    return id;
  };
  sandbox = vm.createContext({
    console, document, Image: FakeImage,
    ImageData: class { constructor(w, h) { this.width = w; this.height = h; this.data = new Uint8ClampedArray(w * h * 4); } },
    localStorage, location: { search: query }, navigator: { maxTouchPoints: touch ? 1 : 0 },
    URLSearchParams, devicePixelRatio: dpr, Math: math, performance: { now: () => clock },
    requestAnimationFrame: (callback) => { frame = callback; return 1; },
    setTimeout: setTimer, clearTimeout: (id) => timers.delete(id),
    setInterval: noop, clearInterval: noop, addEventListener: addListener,
  });
  sandbox.window = sandbox;
  for (const script of scripts) script.runInContext(sandbox);
  const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
  const tick = (ms = 16) => {
    clock += ms;
    let due;
    let runs = 0;
    while ((due = [...timers.entries()].filter(([, t]) => t.at <= clock).sort((a, b) => a[1].at - b[1].at)[0])) {
      if (++runs > 1000) throw new Error('Timer loop did not settle');
      timers.delete(due[0]);
      due[1].callback();
    }
    drawCalls.length = 0;
    if (frame) frame(clock);
  };
  const step = (ms = 100) => { for (let n = 0; n < ms; n += 16) tick(Math.min(16, ms - n)); };
  const fire = (name, event = {}) => {
    for (const callback of listeners.get(name) || []) callback({ preventDefault: noop, repeat: false, ...event });
  };
  const key = (code) => { fire('keydown', { code }); fire('keyup', { code }); };
  const point = (x, y) => {
    const r = canvas.getBoundingClientRect();
    return { clientX: r.left + x / 224 * r.width, clientY: r.top + y / sandbox.BC.H * r.height };
  };
  const click = (box) => {
    const p = point(box.x + box.w / 2, box.y + box.h / 2);
    fire('mousedown', { ...p, button: 0 }); fire('mouseup', p);
  };
  const touchAt = (x, y, identifier = 1) => ({ identifier, ...point(x, y) });
  const tap = (box) => {
    const tc = touchAt(box.x + box.w / 2, box.y + box.h / 2);
    fire('touchstart', { changedTouches: [tc], touches: [tc] });
    fire('touchend', { changedTouches: [tc], touches: [] });
  };
  const settlePack = async (world, fail = false) => {
    const index = pendingScripts.findIndex((s) => s.src === `assets/world${world}.js`);
    if (index < 0) throw new Error(`No pending World ${world} request`);
    const [script] = pendingScripts.splice(index, 1);
    if (fail) script.onerror(new Error('Simulated pack network error'));
    else evaluatePack(script);
    await flush();
    tick();
  };
  const loading = () => {
    tick();
    if (typeof sandbox.BC.loading === 'boolean') return sandbox.BC.loading;
    return drawCalls.some((c) => c.fillStyle === 'rgba(10,8,30,0.85)' && c.w === 224 && c.h === 28);
  };
  await flush();
  tick();
  return { BC: sandbox.BC, step, tick, fire, key, point, click, touchAt, tap, flush,
    settlePack, pendingScripts, localStorage, store, canvas, sandbox, loading };
}

module.exports = { boot };
