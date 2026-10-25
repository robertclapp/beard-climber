'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { boot } = require('./game-harness.cjs');

const HEIGHTS = [256, 266, 292, 300, 378, 420];
const ALL_LEVELS = ['grandpa', 'goat', 'lumberjack', 'mountain', 'bigfoot', 'elf', 'rudolph', 'ice', 'yeti', 'santa', 'gnome', 'rumpel', 'rapunzel', 'dwarf', 'wizard'];
const unlocked = { bc_cheered: JSON.stringify(ALL_LEVELS) };
const plain = (value) => JSON.parse(JSON.stringify(value));
const gameplay = (B) => plain({ cl: B.S.cl, t: B.S.t, score: B.S.score, maxZ: B.S.maxZ, downs: B.S.downs || 0 });

async function play(options = {}) {
  const g = await boot(options);
  const B = g.BC;
  B.loadLevel('goat'); B.start(); B.calm(); g.step(400);
  B.set({ z: 6, x: 2.5, col: 2, arm: null, lastSide: null });
  B.S.maxZ = 6; B.S.items = []; B.S.shelters = [];
  return g;
}
function beginTouch(g) {
  const tc = g.touchAt(100, 100);
  g.fire('touchstart', { changedTouches: [tc], touches: [tc] });
  return tc;
}
function swipeDown(g, tc) {
  const moved = { ...tc, clientY: tc.clientY + 40 };
  g.fire('touchmove', { changedTouches: [moved], touches: [moved] });
  g.fire('touchend', { changedTouches: [moved], touches: [] });
}
async function lose(options = {}) {
  const g = await play(options); const B = g.BC;
  B.S.lives = 1; B.spawn(0, B.S.cl.col, B.S.cl.z + 1);
  g.step(2000);
  assert.equal(B.S.result?.won, false, 'fixture must reach a real loss');
  return g;
}
async function results(options = {}) {
  const g = await play(options);
  g.BC.win(); g.BC.showResults(); g.step(1000);
  assert.equal(g.BC.screen, 'results');
  return g;
}

// Touch rollback must undo only its speculative reach, never subsequent events.
test('fatal collision remains a fall and reaches loss after a touch becomes a swipe', async () => {
  const g = await play({ touch: true }); const B = g.BC;
  B.S.lives = 1;
  const tc = beginTouch(g);
  B.spawn(0, B.S.cl.col, B.S.cl.z + 1); g.tick();
  assert.equal(B.S.lives, 0); assert.equal(B.S.cl.mode, 'fall');
  const invulnerableUntil = B.S.cl.invulnUntil;
  swipeDown(g, tc);
  assert.equal(B.S.cl.mode, 'fall', 'swipe must not resurrect the pre-hit climb');
  assert.equal(B.S.cl.invulnUntil, invulnerableUntil);
  g.step(800);
  assert.equal(B.S.result?.won, false);
});

test('swipe cancellation preserves a collected page and its 150 points', async () => {
  const g = await play({ touch: true }); const B = g.BC;
  const tc = beginTouch(g);
  B.S.items.push({ kind: 'page', x: B.S.cl.x, z: B.S.cl.z + B.T.HAND, t: 0 });
  g.tick();
  assert.equal(B.S.pages, 1); assert.equal(B.S.items.length, 0);
  swipeDown(g, tc);
  assert.equal(B.S.pages, 1); assert.equal(B.S.items.length, 0);
  assert.ok(B.S.score >= 150, 'only speculative climb points can be removed');
});

test('an ordinary down swipe cancels the speculative reach before descending', async () => {
  const g = await play({ touch: true }); const B = g.BC;
  const tc = beginTouch(g); swipeDown(g, tc); g.step(250);
  assert.equal(B.S.cl.z, 5); assert.equal(B.S.score, 0); assert.equal(B.S.downs, 1);
});

for (const [name, action] of [
  ['alternating keyboard reaches', (g) => { for (let n = 0; n < 8; n++) g.key(n % 2 ? 'ArrowRight' : 'ArrowLeft'); }],
  ['same-side keyboard dyno', (g) => { g.key('ArrowLeft'); g.key('ArrowLeft'); }],
  ['keyboard brace', (g) => g.key('Space')],
  ['keyboard climb down', (g) => g.key('KeyX')],
  ['keyboard hold', (g) => g.fire('keydown', { code: 'ArrowUp' })],
  ['mouse reach and long hold', (g) => { g.fire('mousedown', { ...g.point(100, 100), button: 0 }); }],
  ['touch reach, swipe and long hold', (g) => { const tc = beginTouch(g); g.fire('touchmove', { changedTouches: [{ ...tc, clientY: tc.clientY + 40 }], touches: [tc] }); }],
  ['two-finger brace', (g) => { const a = g.touchAt(80, 100, 1), b = g.touchAt(140, 100, 2); g.fire('touchstart', { changedTouches: [a, b], touches: [a, b] }); }],
  ['direct reach', (g) => g.BC.reach('L')],
  ['direct dyno', (g) => g.BC.dyno('L')],
  ['direct brace', (g) => g.BC.brace()],
  ['direct climb down', (g) => g.BC.climbDown()],
  ['direct hold', (g) => g.BC.setHold(true)],
]) {
  test(`paused play ignores ${name}`, async () => {
    const g = await play({ touch: true });
    g.key('KeyP'); const before = gameplay(g.BC);
    action(g); g.step(600);
    assert.deepEqual(gameplay(g.BC), before);
  });
}

test('pausing cancels an already pending long-press timer', async () => {
  const g = await play({ touch: true }); beginTouch(g);
  g.key('KeyP'); g.step(500);
  assert.equal(g.BC.S.cl.hold, false);
  g.key('KeyP'); g.step(400);
  assert.equal(g.BC.S.cl.hold, false, 'resuming must not revive a stale held touch');
});

for (const H of HEIGHTS) {
  test(`Settings controls fit and do not overlap at native H=${H}`, async () => {
    const g = await boot({ width: 224, height: H }); const B = g.BC;
    assert.equal(B.H, H);
    const boxes = Object.entries(B.settingsLayout()).filter(([, box]) => box && typeof box === 'object' && 'w' in box);
    for (const [name, box] of boxes) {
      assert.ok(box.x >= 0 && box.y >= 0 && box.x + box.w <= 224 && box.y + box.h <= H, `${name} must fit`);
      assert.ok(box.w > 0 && box.h > 0, `${name} needs a positive hit area`);
    }
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      const [aName, a] = boxes[i], [bName, b] = boxes[j];
      assert.ok(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y, `${aName} and ${bName} overlap`);
    }
  });
  test(`Settings Easy and Back each invoke only their action at native H=${H}`, async () => {
    const g = await boot({ width: 224, height: H }); const B = g.BC;
    B.openSettings('title'); g.step(400);
    const before = B.easy; g.click(B.settingsLayout().easy);
    assert.equal(B.easy, !before); assert.equal(B.screen, 'settings', 'Easy must not also activate Back');
    g.click(B.settingsLayout().back);
    assert.equal(B.screen, 'title'); assert.equal(B.easy, !before, 'Back must not also toggle Easy');
  });
}

test('results arrows select without advancing; Enter opens the selected Levels action', async () => {
  const g = await results(); const B = g.BC; const level = B.LEVEL;
  g.key('ArrowRight');
  assert.equal(B.screen, 'results'); assert.equal(B.LEVEL, level);
  g.key('Enter');
  assert.equal(B.screen, 'levels', 'Enter must confirm the selected action, not always Play');
});

test('results ignores unrelated keys and touch still opens the requested action', async () => {
  const g = await results({ touch: true });
  g.key('KeyZ'); assert.equal(g.BC.screen, 'results');
  g.tap(g.BC.resultsLayout().levels); assert.equal(g.BC.screen, 'levels');
});

for (const [name, steps, expected] of [['Retry', 0, 'play'], ['Levels', 1, 'levels'], ['Settings', 2, 'settings']]) {
  test(`loss keyboard ${name} works without reloading`, async () => {
    const g = await lose(); const B = g.BC; const oldRun = B.S;
    for (let i = 0; i < steps; i++) { g.key('ArrowRight'); assert.equal(B.screen, 'play'); assert.equal(B.S, oldRun); }
    g.key('Enter'); assert.equal(B.screen, expected);
    if (name === 'Retry') { assert.notEqual(B.S, oldRun); assert.equal(B.S.result, null); assert.equal(B.LEVEL, 'goat'); }
    else assert.equal(B.S, oldRun, 'menu navigation must preserve the completed run');
  });
}

for (const [name, expected] of [['retry', 'play'], ['levels', 'levels'], ['settings', 'settings']]) {
  test(`loss touch ${name} works without reloading`, async () => {
    const g = await lose({ touch: true }); const B = g.BC; const oldRun = B.S;
    assert.equal(typeof B.lossLayout, 'function', 'loss needs exposed button geometry for touch regression tests');
    const box = B.lossLayout()[name]; assert.ok(box, `${name} button exists`);
    g.tap(box); assert.equal(B.screen, expected);
    if (name === 'retry') { assert.notEqual(B.S, oldRun); assert.equal(B.S.result, null); }
    else assert.equal(B.S, oldRun);
  });
}

test('leaving level select prevents a delayed pack from hijacking the newer screen', async () => {
  const g = await boot({ deferPacks: true, storage: unlocked }); const B = g.BC;
  B.openLevels('title'); g.step(400); B.Levels.sel = 5; g.key('Enter');
  assert.ok(g.loading());
  g.key('Escape'); g.key('KeyG'); const level = B.LEVEL;
  assert.equal(B.screen, 'settings');
  await g.settlePack(2);
  assert.equal(B.screen, 'settings'); assert.equal(B.LEVEL, level); assert.equal(g.loading(), false);
});

test('a newer already-loaded selection wins against an older delayed world', async () => {
  const g = await boot({ deferPacks: true, storage: unlocked }); const B = g.BC;
  let staleCallbacks = 0;
  B.goLevel('elf', () => { staleCallbacks++; B.startIntro(); });
  B.goLevel('goat', () => B.startIntro());
  assert.equal(B.LEVEL, 'goat'); assert.equal(g.loading(), false);
  await g.settlePack(2);
  assert.equal(B.LEVEL, 'goat'); assert.equal(B.screen, 'intro'); assert.equal(staleCallbacks, 0);
});

test('latest level request wins when two world packs finish out of order', async () => {
  const g = await boot({ deferPacks: true }); const B = g.BC;
  const callbacks = [];
  B.goLevel('elf', () => { callbacks.push('elf'); B.startIntro(); });
  B.goLevel('gnome', () => { callbacks.push('gnome'); B.startIntro(); });
  await g.settlePack(3); assert.equal(B.LEVEL, 'gnome'); assert.equal(g.loading(), false);
  await g.settlePack(2); assert.equal(B.LEVEL, 'gnome'); assert.equal(B.screen, 'intro');
  assert.deepEqual(callbacks, ['gnome']);
});

test('an obsolete completion does not clear the current loading indicator', async () => {
  const g = await boot({ deferPacks: true }); const B = g.BC;
  B.goLevel('elf', () => B.startIntro()); B.goLevel('gnome', () => B.startIntro());
  await g.settlePack(2);
  assert.equal(g.loading(), true); assert.notEqual(B.LEVEL, 'elf');
  await g.settlePack(3);
  assert.equal(B.LEVEL, 'gnome'); assert.equal(g.loading(), false);
});

test('a failed current pack exits loading, reports failure and can be retried', async () => {
  const g = await boot({ deferPacks: true }); const B = g.BC;
  let completed = 0;
  B.goLevel('elf', () => { completed++; B.startIntro(); }); assert.equal(g.loading(), true);
  await g.settlePack(2, true);
  assert.equal(g.loading(), false); assert.equal(completed, 0); assert.notEqual(B.LEVEL, 'elf');
  assert.match((B.loadError?.lines || B.Levels.toast || []).join(' '), /COULD NOT LOAD/i);
  B.goLevel('elf', () => { completed++; B.startIntro(); }); await g.settlePack(2);
  assert.equal(B.LEVEL, 'elf'); assert.equal(completed, 1); assert.equal(g.loading(), false);
});

test('a failed obsolete pack cannot clear or replace a newer pending request', async () => {
  const g = await boot({ deferPacks: true }); const B = g.BC;
  B.goLevel('elf', () => B.startIntro()); B.goLevel('gnome', () => B.startIntro());
  await g.settlePack(2, true);
  assert.equal(g.loading(), true); assert.ok(!B.loadError && !B.Levels.toast, 'obsolete failure must not show a current error');
  await g.settlePack(3); assert.equal(B.LEVEL, 'gnome'); assert.equal(g.loading(), false);
});

test('all 15 shipped levels load, initialize and render a gameplay frame', async () => {
  const g = await boot(); const B = g.BC;
  assert.deepEqual(Array.from(B.CHAIN), ALL_LEVELS);
  for (const id of ALL_LEVELS) {
    await new Promise((resolve) => B.goLevel(id, resolve));
    B.start(); B.calm(); g.step(100);
    assert.equal(B.LEVEL, id); assert.equal(B.screen, 'play');
    assert.ok(B.ROWS > 0 && Number.isFinite(B.S.cl.z)); assert.ok(Array.isArray(B.S.items));
  }
});

test('revisiting win results banks the completed run only once', async () => {
  const g = await play(); const B = g.BC;
  B.S.pages = 2; B.win(); B.Para.coins = 4; B.Para.stars = 1;
  const before = B.wallet; B.showResults(); const after = B.wallet;
  assert.ok(after > before); assert.equal(after - before, B.S.result.earned);
  B.showResults(); g.step(1000); B.showResults();
  assert.equal(B.wallet, after); assert.equal(Number(g.localStorage.getItem('bc_coins')), after);
});

test('equipped boosts are consumed once per started run, not on menu navigation', async () => {
  const g = await boot(); const B = g.BC;
  B.setBoosts({ b_life: 3, b_magnet: 3 }, ['b_life', 'b_magnet']); B.loadLevel('goat'); B.start(); B.calm();
  assert.equal(B.boosts.b_life, 2); assert.equal(B.boosts.b_magnet, 2);
  assert.equal(B.S.lives, 4); assert.equal(B.S.magnet, true);
  B.openSettings('play'); g.step(400); g.key('Escape'); g.step(400);
  assert.equal(B.screen, 'play'); assert.equal(B.boosts.b_life, 2); assert.equal(B.boosts.b_magnet, 2);
  B.start(); assert.equal(B.boosts.b_life, 1); assert.equal(B.boosts.b_magnet, 1);
});


test('loss Settings and Levels return to the same loss and do not bank again', async () => {
  const g = await lose(); const B = g.BC;
  const completedRun = B.S, wallet = B.wallet;
  for (const [name, expected] of [['settings', 'settings'], ['levels', 'levels']]) {
    g.click(B.lossLayout()[name]); assert.equal(B.screen, expected); g.step(400);
    g.key('Escape'); assert.equal(B.screen, 'play'); assert.equal(B.S, completedRun);
    assert.equal(B.S.result.won, false); assert.equal(B.wallet, wallet); g.step(400);
  }
});

test('arrows on loss select rather than triggering an automatic retry', async () => {
  const g = await lose(); const B = g.BC; const completedRun = B.S;
  g.key('ArrowRight'); assert.equal(B.S, completedRun); assert.equal(B.Loss.sel, 1);
  g.key('ArrowRight'); assert.equal(B.S, completedRun); assert.equal(B.Loss.sel, 2);
  g.key('Enter'); assert.equal(B.screen, 'settings');
});

test('results selections wrap and only confirm the selected action', async () => {
  const g = await results(); const B = g.BC;
  g.key('ArrowLeft'); assert.equal(B.screen, 'results'); assert.equal(B.Results.sel, 4);
  g.key('Space'); assert.equal(B.screen, 'cine');
});

test('latest selection within a single pending pack wins and runs only once', async () => {
  const g = await boot({ deferPacks: true }); const B = g.BC; const callbacks = [];
  B.goLevel('elf', () => { callbacks.push('elf'); B.startIntro(); });
  B.goLevel('rudolph', () => { callbacks.push('rudolph'); B.startIntro(); });
  assert.equal(g.pendingScripts.length, 1, 'a shared world should be fetched only once');
  await g.settlePack(2);
  assert.equal(B.LEVEL, 'rudolph'); assert.deepEqual(callbacks, ['rudolph']);
  assert.equal(g.loading(), false);
});

test('a saved-level startup request cannot replace a newer level choice', async () => {
  const g = await boot({ deferPacks: true, storage: { ...unlocked, bc_level: 'elf' } }); const B = g.BC;
  assert.equal(B.ready, false);
  B.goLevel('goat', () => B.openSettings('title'));
  await g.settlePack(2);
  assert.equal(B.LEVEL, 'goat'); assert.equal(B.screen, 'settings');
  assert.equal(B.ready, true); assert.equal(g.loading(), false);
});


for (const fail of [false, true]) {
  test(`saved-world startup ${fail ? 'failure' : 'success'} releases loading and input`, async () => {
    const g = await boot({ deferPacks: true, touch: true, storage: { ...unlocked, bc_level: 'elf' } }); const B = g.BC;
    assert.equal(B.ready, false); assert.equal(g.loading(), true);
    g.step(400); g.key('Enter'); g.key('KeyL'); g.tap(B.TITLE_GEAR_BTN());
    assert.equal(B.screen, 'title', 'startup controls wait for asset readiness');
    await g.settlePack(2, fail);
    assert.equal(B.ready, true); assert.equal(g.loading(), false);
    assert.equal(B.LEVEL, fail ? 'grandpa' : 'elf');
    if (fail) assert.match((B.loadError?.lines || []).join(' '), /COULD NOT LOAD/i);
    g.key('KeyL'); assert.equal(B.screen, 'levels', 'controls recover without reloading');
  });
}

test('loss retry consumes the next run boosts exactly once', async () => {
  const g = await lose({ storage: { bc_boosts: JSON.stringify({ b_life: 3 }), bc_boost_eq: JSON.stringify(['b_life']) } });
  const B = g.BC, wallet = B.wallet;
  assert.equal(B.boosts.b_life, 2);
  g.key('Enter'); g.key('Enter');
  assert.equal(B.S.result, null); assert.equal(B.S.lives, 4); assert.equal(B.boosts.b_life, 1);
  assert.equal(B.wallet, wallet);
});

test('touch pause and resume do not also climb or score', async () => {
  const g = await play({ touch: true }); const B = g.BC;
  const before = gameplay(B);
  g.tap(B.PAUSE_BTN()); assert.equal(B.paused, true); g.step(500);
  assert.deepEqual(gameplay(B), before);
  g.tap(B.pauseLayout().resume); assert.equal(B.paused, false);
  assert.deepEqual(gameplay(B), before);
  g.step(100); assert.ok(B.S.t > before.t);
});

test('paused parachute ignores new touch drags and keyboard steering', async () => {
  const g = await play({ touch: true }); const B = g.BC;
  B.win(); B.startPara(); g.step(400); g.key('KeyP');
  const before = plain(B.Para);
  const tc = beginTouch(g), moved = { ...tc, clientX: tc.clientX + 50 };
  g.fire('touchmove', { changedTouches: [moved], touches: [moved] });
  g.key('ArrowLeft'); g.step(500);
  assert.deepEqual(plain(B.Para), before);
});

function swipeUp(g, tc) {
  const moved = { ...tc, clientY: tc.clientY - 40 };
  g.fire('touchmove', { changedTouches: [moved], touches: [moved] });
  g.fire('touchend', { changedTouches: [moved], touches: [] });
}

test('queued second swipe-up reach is canceled by pause even after immediate resume', async () => {
  const g = await play({ touch: true }); const B = g.BC;
  swipeUp(g, beginTouch(g));
  const score = B.S.score, maxZ = B.S.maxZ, arm = B.S.cl.arm;
  assert.ok(score > 0, 'first reach executes before the delayed second reach');
  g.key('KeyP'); g.key('KeyP'); g.step(B.T.CLIMB_MS + 100);
  assert.equal(B.S.score, score); assert.equal(B.S.maxZ, maxZ); assert.equal(B.S.cl.arm, arm);
});

test('queued second swipe-up reach cannot leak into a newly started run', async () => {
  const g = await play({ touch: true }); const B = g.BC;
  swipeUp(g, beginTouch(g));
  const oldRun = B.S;
  B.start(); B.calm(); B.S.items = []; B.S.shelters = [];
  const score = B.S.score, maxZ = B.S.maxZ;
  assert.notEqual(B.S, oldRun);
  g.step(B.T.CLIMB_MS + 100);
  assert.equal(B.S.score, score); assert.equal(B.S.maxZ, maxZ); assert.equal(B.S.cl.arm, null);
});
