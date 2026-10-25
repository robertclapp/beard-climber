# Beard Climber handoff (Oct 22, 2026)

Historical handoff imported from the source archive. The repository robertclapp/beard-climber is now private; this draft co-locates source with the unchanged root release snapshot. See DEVELOPMENT.md for the current workflow, validation and merge/deployment privacy guard. ROADMAP.md preserves the original content roadmap.
Status: Worlds 1-3 are live, plus Easy mode, one-hand and two-hand controls, the coin shop and the character creator.

## Layout
- levels/*.py: data-driven giant/level definitions (Blender scenes)
- web/render_web_assets.py: renders the Blender 4.2 models headless (Workbench renderer) into palette-quantised pixel art
- web/pip.py: hero sprites, with a key-colour recolour system for customisation
- web/src/game.js: all game code. Per-level tuning is in the T / T_LEVELS blocks.
- web/build_web.py: builds web/index.html (World 1 + core, base64) plus the lazy-loaded assets/world2.js and world3.js
- web/test_game.py: Playwright tests (about 336 checks, run in chunks, slow)
- web/balance_check.py: "good" and "casual" bots that measure win rates
- Screenshots/GIF references remain in the separately supplied archive; session-only progress logs are not imported.
- Saves use localStorage only (bc_controls, bc_easy, coins, purchases, looks). The game makes no network calls except loading its own local files.

## To publish
Do not publish from this draft. Follow DEVELOPMENT.md and obtain separate merge/deployment approval after choosing a release-only publishing strategy. Keep root release files unchanged until then.

## Next
World 4 High Seas (Pirate, Viking, boss Sea King), then Worlds 5-8 and the Finale (see ROADMAP.md).
Later: a daily beard and share cards, a Poki release (no in-app purchases or chat, never use the "Crazy Climber" name), then Android and iOS.
Known issues: the Wizard's art is still in the base file; the Elf has no unique mechanic; hats are cropped at the top; mouse drags don't swipe on desktop; Easy mode balance hasn't been bot-tested.
