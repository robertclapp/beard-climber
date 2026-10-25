# Development and release boundaries

## Repository layout

- `web/src/game.js` and `web/src/index.template.html`: canonical editable game.
- `web/index.html`, `web/assets/world2.js`, `web/assets/world3.js`: generated
  development candidate. This is where the five stability fixes are previewed.
- Root `index.html`, `assets/`, `.nojekyll`, and `LICENSE`: existing release
  snapshot, preserved byte-for-byte from main ca2fc828 in this draft.
- `levels/`, `common.py`, `beard.py`, `climber.py`, `web/pip.py`: procedural
  Blender model source. There are 17 definitions, including the 15 playable
  levels and Pirate/Viking prototypes. No model or art content is changed here.
- `web/render_web_assets.py`, `web/build_web.py`: full art rendering/packing.
- `web/tests/`: new fast regression suite; `web/test_game.py` and
  `web/balance_check.py`: preserved original browser and balance tests.
- `docs/ASSET_PIPELINE.md`: original modeling documentation; `ROADMAP.md`: the
  historical content roadmap. Native-app work is a separate milestone/branch.

The uploaded HTML and both packs matched main
`ca2fc82824f08bc97f47da0f78df2418aa83cb85` exactly. The uploaded runtime/template
also reconstructed that HTML exactly. This import preserves the original
procedural source, but omits generated render caches, separate screenshot/GIF
references, bytecode, and session-only progress logs. The original handoff
archives remain available separately.

## Fast code/template workflow

Python 3.8+ and Node.js 18+ are required; no npm dependencies or install step:

```sh
python3 web/build_runtime.py
npm run check
python3 -m http.server 8000 --directory web
```

Preview http://localhost:8000/. Do not serve the repository root when testing the
fixes: its index is intentionally the unchanged release snapshot.

The runtime builder parses the existing `web/index.html` asset JSON and icon as
data, then combines them with the editable template and runtime. It never
evaluates cached scripts, changes world packs, or promotes output to the root.
Keep the generated HTML present as its asset cache. `--check` verifies source/
output synchronization; it does not verify artwork against edited Blender models.

## Stability changes

1. Touch-to-swipe cancellation no longer restores an entire stale player state,
   erases collected points, or cancels a fatal hit. Queued reaches are scoped to
   their run and invalidated by pause.
2. Pause blocks gameplay input and clears held/pending controls, including
   parachute steering; touch users have Pause/Resume controls.
3. Settings controls fit the supported native canvas heights and no longer
   overlap or activate Easy and Back together.
4. Results arrows select an action; Enter/Space confirms. Game over provides
   Retry, Levels and Settings with safe returns to the finished run.
5. Stale world-load callbacks cannot replace a newer screen/level selection.
   Current load failures and saved-world startup have explicit recovery.

## Verification

`npm run check` combines code/output synchronization, 58 gameplay regression
tests, and 36 Python tests (eight cached-builder, 21 release-packaging, and
seven browser-selection tests). All pass on the final import. Both world
packs, embedded asset JSON and home-screen icons are unchanged. Python and
JavaScript syntax and Git whitespace checks pass.

The gameplay harness uses actual runtime/world-pack code with mocked DOM, audio
and canvas, deterministic clocks and controllable pack completion. These are
logic and event-routing tests, not a real-device playthrough. See
`web/tests/README.md`. The original browser suite's historical 336-check claim
is not a fresh validation result.

Outstanding: full art regeneration, original browser/balance suites, Safari and
physical-device touch/audio/lifecycle testing. The reviewed environment has
Blender 4.3.2 rather than the documented 4.2.3 LTS and no raw art-render
`web/build/` cache. The browser runners now select an installed Chrome/Chromium
(or an explicit `CHROME_BINARY`) rather than hardcoding one Linux path. Browser
startup was attempted on 2026-10-23, but this executor prohibited Chromium's
process socket; the supported alternate launcher failed during sandbox setup.
The separate cloud browser could not reach the executor's loopback preview.
No browser gameplay checks ran. See `web/tests/README.md` for the runnable
browser/balance commands and their output-overwrite boundaries. Exact
Python/Pillow/numpy/Playwright/browser dependency versions are not pinned in
the original handoff. No installations or external services are required by
the new fast checks. No deployment or CI workflow is added by this draft.

## Full art rebuild

Use a reviewed Blender toolchain (originally tested with 4.2.3 LTS/Workbench),
Pillow and numpy. The original recipe requires all 15 playable levels:

```sh
blender -b --python web/render_web_assets.py -- --level grandpa
for level in goat lumberjack mountain bigfoot elf rudolph ice yeti santa gnome rumpel rapunzel dwarf; do
  blender -b --python web/render_web_assets.py -- --level "$level" --only level,faces
done
blender -b --python web/render_web_assets.py
python3 web/build_web.py
npm run check
```

This recipe was source-reviewed, not executed during the import. Run it in a
disposable working copy first: it overwrites generated outputs and resets
Blender scenes. `run_all.sh` is the separate prototype `out/` preview pipeline.
Original browser tests also overwrite screenshots/GIFs and require Playwright,
Chrome and ffmpeg.

## Release-only packaging (local artifact, not deployment)

On POSIX Python (Linux/macOS), prepare a private review artifact with:

```sh
npm run release:package
# For another candidate, choose a new name; existing outputs are never replaced:
npm run release:package -- --output out/release/candidate-2.zip
```

This first runs all fast checks, then writes `out/release/beard-climber-web.zip`.
The archive has exactly five explicitly named files:

- `index.html`, copied from the fixed `web/index.html`, not root's old snapshot;
- `assets/world2.js` and `assets/world3.js`, copied from `web/assets/`;
- the unchanged `LICENSE`;
- an empty `.nojekyll` marker.

No directory recursion, glob expansion, or configurable input list is used.
Extra source files, documentation, `.git`, `.env`, tests, native work, cached
renders and old outputs cannot enter the archive through a directory copy.
ZIP metadata and ordering are normalized; identical inputs produce identical
bytes independent of timestamps and compression-library versions. Only output
names under `out/release/` are accepted. Existing destinations are refused
without deletion; source/output symlinks, hardlinked inputs, nonregular inputs,
and unsafe paths fail closed. The project must be accessed through its canonical
filesystem path rather than a symlink. Unsupported filesystem safety operations
fail instead of weakening the checks.

This is an allowlist, not a secret scanner or copy-protection mechanism. The
shipped JavaScript and artwork remain visible to anyone who receives a browser
build. Review changes inside allowlisted files before any release. The release
ZIP itself is a private candidate until separately approved for publication.
The helper does not copy output to root, modify Pages settings, push or deploy.

The candidate ZIP was inspected for exactly these five names and matching bytes,
and its extracted contents passed all 58 gameplay regressions. Those are still
mocked-runtime checks, not a real browser or physical-device pass.

## Merge/deployment privacy guard

**This draft is not ready to merge or deploy.** The repository is private, but
a Pages site is not automatically private. Its prior deployments came from
main's root with `.nojekyll`. Deploying the complete source tree that way could
make Python source and project documentation downloadable from Pages.

The tested allowlisted ZIP supplies the release-only artifact, but it does not
change the current publishing source. Before merge/release, explicitly choose
and approve a release-only branch or artifact publishing strategy that uses
only the five packaged files, never the source tree. Then review privacy and run browser/
device checks. Changing Pages settings, publishing, merging and enabling
auto-merge are outside this draft's scope.

Once a release process is separately approved, promote only the tested
`web/index.html` and `web/assets/` to the chosen release destination. Nothing
in the new build/check commands copies files to root, pushes, merges or deploys.

GitHub guidance: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
