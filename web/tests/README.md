# Stability regression tests

Run with Node.js 18 or newer, without installing anything:

```sh
npm test
# Equivalent:
node --test web/tests/*.test.cjs
```

`game-harness.cjs` executes the actual inline scripts in `web/index.html` and the
actual `web/assets/world2.js` / `web/assets/world3.js` packs in a fresh Node VM per test.
It provides a deterministic clock, queued timers, seeded randomness, DOM input
listeners, isolated localStorage, canvas stubs, and manually controllable pack
success/failure. No network, browser installation, or application build is used.

## Coverage

- A touch that becomes a swipe cannot undo a subsequent fatal collision, revive
  the climber, discard a collected page, or remove its score. An ordinary swipe
  still cancels its speculative reach before descending. A queued second
  swipe-up reach cannot survive pause/resume or leak into a newly started run.
- Paused keyboard, mouse, touch, double-tap, brace, hold and direct action paths
  leave gameplay unchanged. A pending long press is canceled on pause. Touch
  pause/resume must not also climb. Parachute inputs remain inert while paused.
- Settings button geometry fits without overlap at native canvas heights 256,
  266, 292, 300, 378 and 420. Clicking Easy does not also activate Back, and
  clicking Back does not also toggle Easy.
- Results arrows change selection, Enter/Space confirms, unrelated keys do not
  advance, and touch selection still works. Loss Retry, Levels and Settings
  work by keyboard and touch; returning from menus preserves the finished run.
- Delayed world loads cannot supersede newer screen/level choices. Tests cover
  ready-level replacement, different worlds completing out of order, multiple
  choices in one world, canceled loads, obsolete failures, current failures,
  successful retry, and saved-world startup readiness/fallback.
- All 15 shipped levels load and initialize, run earnings bank only once, and
  equipped boosts are consumed once per new run rather than on menu visits or
  duplicate confirm input.

## Test boundaries

These are logic and event-routing tests, not visual browser tests. Canvas drawing
is mocked; sprites are not decoded into real pixels, audio is not played, browser
security/network behavior is not modeled, and Safari/iPhone hardware behavior is
not validated. The native-height checks prove button bounds/hit-box separation,
not text rendering, safe-area insets or real-device touch comfort. A browser/device
smoke pass should still check those separately.

## Comparing another checkout

Point `BEARD_GAME_ROOT` at a directory containing that checkout's web `index.html`
and `assets/` to run the same tests against it:

```sh
BEARD_GAME_ROOT=/path/to/other/checkout node --test web/tests/*.test.cjs
```

The 58-test suite was checked against the original `de76f8d` snapshot on
2026-10-22: 13 passed and 45 failed, reproducing the five reported bug families
and the newly specified recovery/navigation behavior. The baseline is not
included in this repository; the tests always use the current files by default.


The Python standard-library suite covers the cached-runtime builder, release ZIP
allowlisting/path safety/reproducibility, and installed-browser selection.
Run `npm run test:build` for these, or `npm run check` for source/output
synchronization plus all fast tests. Browser selection tests do not launch a
browser and must not be reported as browser validation.

## Real-browser validation

The original `web/test_game.py` suite drives real CDP touch events and captures
screenshots/GIFs. It requires Playwright, Pillow, ffmpeg and an installed browser.
The runner never installs or downloads dependencies. It honors `CHROME_BINARY`
first, then searches for installed Chrome/Chromium, then Playwright's existing
browser cache. A bad explicit override fails rather than silently choosing a
different browser.

```sh
npm run test:browser
# Optional explicit installed browser:
CHROME_BINARY=/path/to/chrome npm run test:browser
# The original balance bot can run after the browser suite:
python3 web/balance_check.py grandpa
```

Run in a disposable working copy: original browser tests overwrite `web/shots/`
and GIF build frames; the balance bot appends `web/build/balance.jsonl`. The
balance output directory is now created on a fresh checkout.

On 2026-10-23 browser startup was attempted but blocked before any gameplay
checks ran: this environment prohibited Chromium's process socket, the supported
alternate launcher failed during sandbox setup, and the separate cloud browser
could not access the executor's loopback preview. The original browser/balance
suites, visual output, audio and Safari/device behavior are therefore still
unverified. No security restrictions were changed and no public preview was
created to work around the limit.
