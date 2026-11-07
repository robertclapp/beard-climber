# Beard Climber

A retro 80s-style vertical climbing game where Pip scales giant beards to cheer up grumpy giants. Demo: World 1 Whiskerton Woods, World 2 North Pole, and the Wizard.

Play: https://robertclapp.github.io/beard-climber/

Controls: one-hand mode (default on phones) — tap to climb, swipe left/right to hop, swipe down to climb down. Two-hand mode in Settings: tap left/right alternately, double-tap to hop.

## License

Copyright (c) 2026 Robert Clapp. All rights reserved. See LICENSE.

## Private development source

The complete procedural Blender and web source is now kept with this private
repository. The existing root `index.html` and `assets/` remain the unchanged
release snapshot. The stability-fixed development candidate is `web/index.html`
with `web/assets/`; edit `web/src/game.js` and `web/src/index.template.html`.

From the repository root, using Python 3.8+ and Node.js 18+:

```sh
python3 web/build_runtime.py
npm run check
python3 -m http.server 8000 --directory web
```

Open http://localhost:8000/ to preview the fixed development candidate. No package
installation is needed for the fast checks. The code-only builder preserves the
checked-in artwork cache; it is not a model/art rebuild.

See [DEVELOPMENT.md](DEVELOPMENT.md) for the source map, full art pipeline and
verification limits, and [docs/ASSET_PIPELINE.md](docs/ASSET_PIPELINE.md) for the
original modeling documentation.

`npm run release:package` makes a local, allowlisted five-file ZIP after the fast
checks, without uploading it or changing Pages. See DEVELOPMENT.md for its exact
contents and safety boundaries.

**Do not merge or deploy this source tree until the release-only publishing
configuration described in DEVELOPMENT.md is separately approved and verified.** A private GitHub repository
does not by itself make a Pages site private. No Pages settings or deployment
workflow are changed by this draft.
