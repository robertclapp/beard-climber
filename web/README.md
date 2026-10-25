# Beard Climber - playable web game (World 1 Whiskerton Woods, World 2 North Pole, World 3 Fairy-Tale Forest + the Wizard)

`index.html` is the whole game: one file (~805 KB) with all art, sound, font and level data
embedded as base64. No server needed (works from `file://` or any static host), no build step
to *play* it. Open it on iPhone Safari / Android Chrome (portrait) or a desktop browser.

## Worlds + level select
| world | levels | status |
|---|---|---|
| **World 1: Whiskerton Woods** | 1-1 **Grandpa** (tutorial), 1-2 **The Goat**, 1-3 **The Lumberjack**, 1-4 **Mountain Man**, 1-5 **Bigfoot** (boss) | all playable, unlock in order |
| **World 2: North Pole** | 2-1 **The Elf**, 2-2 **Rudolph**, 2-3 **The Ice Giant**, 2-4 **The Yeti**, 2-5 **Santa** (boss) | all playable, unlock in order after Bigfoot |
| World 3 | 3-5 **The Wizard** (boss) | locked: "CHEER UP SANTA FIRST" (players who had him before keep him) |

Unlock chain (`CHAIN` / `UNLOCK_BY` in game.js): Grandpa -> Goat -> Lumberjack -> Mountain Man -> Bigfoot -> Elf -> Rudolph ->
Ice Giant -> Yeti -> Santa -> Wizard. Cheering a giant up (first ending) unlocks the next one and that giant's shop set.
Old saves: on the first load of the World 1 build (`bc_w1` not set) anyone who had cheered Grandpa or the Wizard, and on the
first load of the World 2 build (`bc_w2` not set) anyone who had cheered Bigfoot (who used to open the Wizard), gets
`bc_wiz_open=1`, so the Wizard stays reachable. On short screens the world select uses compact one-line rows.
The **LEVELS** button (title + results, key `L`) opens the world select (tap / click a row, or up/down + Enter, Esc = back);
locked rows say who to cheer up first, coming-soon rows answer with a friendly message. The last picked level is
remembered (`bc_level`); after an ending the results PLAY button reads **NEXT: <GIANT>**.
`?level=<id>` forces a level (tests). Per-level data lives in `ASSETS.levels.<id>` (built by `build_web.py` from
`web/build/<id>/raw`); `game.js` `loadLevel(id)` swaps the level image, tile map, sprites, z constants and tuning.

## World 1: the giants after the tutorial
Each follows the full story flow: intro (townsfolk cheer while Pip packs the gift) -> climb -> calming ending ->
parachute coin run -> the bird carries Pip to the next giant. Each has its own Blender level (`levels/<id>.py`),
cinematic vignette + portrait, collectible, shop set and `T_LEVELS` tuning (difficulty ramps through the world).

| level | beard | hazards | gift / ending | collectible | hold-tight event | shop set |
|---|---|---|---|---|---|---|
| 1-2 Goat | 24 rows, long pointy white chin beard, horns + floppy ears | tin can, hay bale, boot, bell | big turnip - he munches it, "MEHHH!" | lucky clovers (4) | none | goat horns, farm bandana |
| 1-3 Lumberjack | 26 rows, ginger + plaid toque (prototype level refit) | rolling log, chainsaw (off, sputtering), pancakes, axe, pinecone | syrupy pancake stack - chomp, big belly laugh | maple leaves (5) | sneeze | trapper hat, lumberjack plaid |
| 1-4 Mountain Man | 28 rows, huge wild brown beard, knit hat | rock, snowball, frying pan, fish | his lost compass, tucked back in | feathers (5) | **wind gust**: hold or get blown a column sideways | fur cap, buckskin jacket |
| 1-5 Bigfoot (boss) | 30 rows of shaggy chest fur, furry face on top | pinecone, marshmallow, camera, tent pole | a selfie together (flash!), he grins | berry bunches (5) | **stomp**: fur shakes (hold!) + pinecones rain down | Bigfoot hood, shaggy fur suit |

Tuning (seconds between throws bottom/top, fall speed, rows lost per hit): Grandpa 4.2/2.8, 2.0-2.7 (unfailable) < Goat 3.5/2.1, 2.4-3.3, 1.6 <
Lumberjack 3.4/1.85, 2.5-3.5, 1.7, sneezes every 14-20 s < Mountain 3.5/1.9, 2.4-3.5, 1.6 + gusts every 18-25 s (2.0 s warning), longer beard <
Bigfoot 3.0/1.5, 2.75-4.0, 1.9, stomps every 9-13 s (2.2 s warning, 1 pinecone) < Wizard 2.4/1.0, 3.4-5.2.
Bot results (4 seeds): good 4/4, 3/4, 4/4, 4/4; casual 4/4, 2/4, 3/4, 1/4 (Goat, Lumberjack, Mountain, Bigfoot).
`T.EVENT` picks the hold-tight event (`sneeze` / `gust` / `stomp`); the warning banner and wind streaks match it.

## World 2: North Pole
Same story flow, pipeline, shop sets and collectibles as World 1. Snowy side art (desktop letterbox) and snowy ground.
Difficulty restarts a little below Bigfoot and ramps up to Santa (the hardest climb before the Wizard).

| level | beard | hazards | gift / ending | collectible | mechanic | shop set |
|---|---|---|---|---|---|---|
| 2-1 Elf | 26 rows, small curly ginger beard, pointy hat + ears | presents, jingle bells, toy trains, candy canes | his lost toy hammer - a happy jig (the scene sways, music notes) | gingerbread (5) | sneeze | elf hat, elf tunic |
| 2-2 Rudolph | 28 rows of neck mane, antlers, big dim nose | sleigh bells, carrots, snow clumps, hoofprints | a warm lantern + a hug - **his nose glows** again | gold stars (5) | **dark stretches** (30-48 %, 64-82 % of the climb: only a light round Pip) + hoof stomps (hold) | antler headband, reindeer jumper |
| 2-3 Ice Giant | 24 rows, pointed icicle beard | icicles, snowballs, frost puffs, ice cubes | a knitted mitten | snowflakes (5) | **slippery** (slides down 0.35 rows/s after 0.8 s without a tap; x0.35 while holding) + **melt timer** (60 s, bar under the HUD, "IT MELTED!") | ice crown, frost cape |
| 2-4 Yeti | 30 rows of fluffy white / blue-grey fur (frosty palette, not Bigfoot's browns) | snowballs, icicles, mugs, a ski | cocoa + a scarf - he hugs it | ice crystals (5) | **roar**: fur shakes (hold!) + a snowball shaken loose | yeti earmuffs, yeti scarf |
| 2-5 Santa (boss) | 32 rows, big round fluffy beard (prototype refit) | presents, cookies, coal (+ the reindeer) | a big cookie: munch, yawn, **fast asleep** (Zzz) | letters to Santa (5) | **HO HO HO** belly laughs (hold!) alternating with a **reindeer swoop** that drops 2 presents (dodge) | Santa hat, Santa suit |

Tuning (throws s bottom/top, fall speed, rows lost per hit): Elf 3.4/1.85, 2.45-3.5, 1.6 (sneezes 15-21 s) | Rudolph 3.35/1.8,
2.5-3.6, 1.65 (hoof 15-21 s, dark) | Ice 3.3/1.8, 2.5-3.6, 1.65 (slide, 45 s melt) | Yeti 3.4/1.85, 2.45-3.55, 1.6 (roar 15-20 s,
30 rows; the shaken-loose snowball never lands in Pip's column) | Santa 2.95/1.45, 2.8-4.1, 1.9 (laugh / swoop 9-13 s, 32 rows).
Bot results (4 seeds, good / casual): Elf 4/4, 4/4 - Rudolph 4/4, 3/4 - Ice 4/4, 3/4 - Yeti 3/4, 1/4 - Santa 3/4, 1/4.
The bot reads the game state, so Rudolph's darkness does not slow it down (real players will find Rudolph a bit harder).
`T.EVENT` options are now sneeze / gust / stomp / hoof / roar / laugh; `T.SLIP`, `T.MELT_S`, `T.DARK`, `T.THROW_N`, `T.SWOOP_DROP`
are the new World 2 knobs. The opening cinematic has all 11 giants (vignettes 2.3 s each, ~32 s, skippable).

## World 3: Fairy-Tale Forest

| # | Giant | Gift (ending) | Collectible | Hazards | Unique mechanic | Shop set |
|---|---|---|---|---|---|---|
| 3-1 | Garden Gnome | lucky mushroom | ladybugs | watering cans, snails, acorns, trowels | bouncy red mushrooms in the beard: touch = BOING! up 2.5 rows (`T.MUSH`) | gnome hat + tunic |
| 3-2 | Rumpelstiltskin | name badge (he dances) | gold spools | straw, spindles, stools, spinning wheels | straw spins into gold mid-fall; catch it for +3 coins each (`T.GOLD_CHANCE`) | feather hat + spun-gold vest |
| 3-3 | Rapunzel | golden hairbrush | roses | flowerpots, frying pans, teacups, yarn | climb her braid up the tower: outer columns are stone wall, 4-column braid (`T.NARROW`) | tiara + tower gown |
| 3-4 | Dwarf King | crown | gems | pickaxes, mine carts, rocks, tankards | ROCKFALL: 2 columns flash red, then fast boulders come down them - dodge, holding won't help (`T.EVENT = "rockfall"`) | dwarf helm + chainmail |
| 3-5 | The Wizard (boss) | spell book, tuck in the sleepy cat | pages | (existing) | (existing) | - |

The Wizard now unlocks after the Dwarf King. Saves that had cheered Santa before World 3 existed keep the Wizard open (`bc_w3` migration).

## Lazy-loaded worlds

`index.html` holds World 1, the Wizard, Pip, props and the cinematic, so World 1 starts instantly. Each later world's level art + atlas lives in `assets/world<N>.js` (World 2: 190 KB, World 3: 155 KB). `game.js` loads one with a same-origin `<script>` tag (`ensureWorld`) when you pick a level, and prefetches the rest 1.5 s after start; it shows LOADING... if you're faster. There are no other network requests. `build_web.py` `WORLD_OF` sets which level goes in which pack. Ship the `assets/` folder next to `index.html`.

Load size: one 825 KB file before the split; now `index.html` is 694 KB (it includes the World 3 props, shop items and cinematic portraits) plus the packs on demand.

## World 1-1: Grandpa (the tutorial)
A sweet giant grandpa (`levels/grandpa.py`, Blender pipeline like every level): soft, scruffy grey-white wavy beard,
round gold reading glasses (new optional `face_extra` hook in `beard.py`), bushy brows, rosy cheeks, a tweed flat cap.
He is grumpy because **the grandkids haven't called**. Hazards fall gently from his mouth: **candies, silly dentures,
knitting yarn, reading glasses, a slipper**. Collectibles are 4 **family photos** (instead of spell-book pages).
* Intro: the townsfolk cheer, a **toy phone** hops into Pip's backpack, "TAKE HIM THIS TOY PHONE, PIP!".
* Ending: Pip hands the phone up, it goes RING! RING! - "IT'S THE GRANDKIDS!" - he smiles, then **beams**
  (closed happy eyes), waves a big hand and laughs "HO HO HO!". Then the parachute coin run and the bird: "NEXT: THE WIZARD!".
* **Impossible to fail**: hits never cost hearts or lives, they only knock Pip down 1 row (`KNOCK_HIT 1.0`). No sneezes.
* 16-row beard (12.75 units of climb vs. 36.4 on the Wizard), slow sparse hazards that ramp slightly
  (`THROW 4.2 -> 2.8 s`, `FALL 2.0 -> 2.7 u/s`, no pairs), its own tuning block `T_LEVELS.grandpa` in `game.js`
  (merged over the Wizard's `T`, so the Wizard is unchanged).
* Big pixel-font prompts, one at a time; each waits until the player has done it once:
  1. TAP LEFT, RIGHT, LEFT, RIGHT... TO CLIMB  2. BALD PATCH! DOUBLE-TAP (a hand-placed bald patch, `forced_tiles`, sits right above the start column)
  3. GRAB THE HARD HAT! (hazards only start after this)  4. GRAB THE PHOTO!  5. CLIMB INTO THE TANGLE! (one shelter; a hazard is dropped to show the BOING)
  6. NOW CLIMB TO GRANDPA!  7. TAP LEFT / RIGHT TO STEER (the parachute hangs, sinking at x0.2, until the first steer).
  Lesson items follow Pip's column and re-appear above if Pip climbs past them, so nothing can be missed.

## Desktop, tablet + portal groundwork
* **Letterbox**: the portrait play area is centred with integer scaling (`k = min(floor(w/224), floor(h/256))`,
  native height 256-420), e.g. 1280x720 -> x2 (448x720), 1920x1080 -> x4 (896x1080), iPad Pro 11 portrait x7, landscape x6.
  The side bars are a themed pixel pattern drawn at the same pixel scale (pine woods for World 1, a starry night for
  the Wizard), not black. Window resizing and rotation re-centre / re-scale.
* Keyboard: Left/Right or A/D = arms (double press = dyno), Space/Enter = menus/skip (Space = brace while climbing),
  Up/W hold tight, M mute, P pause, L level select, I intro. The mouse clicks every button; clicking the left/right
  half of the play area = arms.
* **No network at all** (everything embedded; tests fail on any non-`file:`/`data:` request), data only in
  `localStorage`, no real-money purchases, no ads, no external links. The "Crazy Climber" reference was removed.
* **Poki adapter** (`Poki` object in `game.js`): if a portal page has already loaded `window.PokiSDK`, the game calls
  `init()`, `gameLoadingFinished()` and `gameplayStart()/gameplayStop()` (climb + parachute = gameplay). Without the SDK
  it does nothing. For a Poki build, add their SDK `<script>` to the template (the only external file) - not done here.

## Story (kid-friendly)
The giants of **Whiskerton** have lost their treasures and got grumpy. **Pip** cheers them up instead of fighting them.
Flow: title -> how-to -> **character creator** -> **opening cinematic** (automatically only the first time ever, `bc_cine`) -> **level intro** (Grandpa first) -> climb ->
**ending** -> **parachute bonus** -> **bird carry** -> **results / thanks**.

| scene | what happens | length | skip |
|---|---|---|---|
| opening cinematic | Donkey Kong-style attract story: "WHISKERTON" card, then Grandpa (the phone never rings), Santa (empty cookie plate), the Lumberjack (burnt pancakes), the Viking (silent horn), the Pirate (map blows away), the Wizard (spell book flies off, cat won't settle). Each giant says HMPH!, tosses things down his beard, the townsfolk duck. Then Pip (in the creator look) steps up: "PIP WILL CHEER THEM UP!" (6 vignettes x 3.0 s) | 24.4 s | tap |
| Wizard intro | at the foot of the beard, cheering townsfolk (WebAudio crowd), the book and the sleepy cat hop into Pip's backpack, "BRING IT BACK, PIP!", Pip jumps onto the beard tip. The cat keeps peeking out of the backpack during the climb | 5.4 s | tap |
| climb | unchanged gameplay, plus 5 **spell-book pages** tucked in the beard (HUD `n/5`, 150 pts each) | | |
| ending | hazards go poof and stop; Pip hands back the book (+ the pages), tucks the cat into the beard; the Wizard smiles, yawns and falls asleep (closed eyes, floating Zzz, lullaby) | 5.9 s | tap |
| parachute bonus | Pip floats down the whole beard; tap (or hold) left / right to steer; coins (10) and stars (100); no hazards, no deaths | 12 s | - |
| bird | a friendly bird swoops in, Pip grabs its feet: "NEXT: THE WIZARD!" (after Grandpa) / "MORE GIANTS COMING SOON!" | 4.4 s | tap |
| results | score breakdown (height, time, lives, hat, pages, coins, stars), coins banked + wallet, "WIZARD SET UNLOCKED!" on the first win; PLAY AGAIN / NEXT: WIZARD (-> intro), LEVELS, SHOP, CHANGE PIP (-> creator), WATCH INTRO (-> cinematic) | | |

The title screen also has **WATCH INTRO** (key `I`), **LEVELS** (key `L`) and **SHOP** buttons and shows the wallet.
The table above describes the Wizard; the Grandpa scenes are described in "World 1-1" above.

## Character creator
Options: body (boy / girl), hair style (short / curly / bunches / long), hair colour (7), skin tone (6 real tones),
outfit colour (7), backpack/gear colour (6; also the parachute, hat and hair ties), headgear (none / beanie / cap / bow).
Big `<` `>` buttons (tapping a row also steps it), a live 2x preview (TURN shows the back view, with the cat),
RANDOM, SHOP and START (wallet top-right; the `<` `>` arrows are 30 native px wide and >= 26 tall = 50x57 CSS px on iPhone 14). Saved in `localStorage` (`bc_look`). The look is used in the cinematic, the intro, the climb
(including the hard-hat states), the ending, the parachute, the bird carry, the results and the how-to icons.
Keyboard: up/down pick a row, left/right change it, R random, T turn, Enter start.
All the original creator options stay free; the rows also cycle shop items you own (e.g. the HAT row cycles the
crown once bought, the Wizard hat once he's cheered up). Patterns, pack styles and parachutes are worn from the shop.

## Coin shop
Coins are **earned in the game only** (no real money, ads or links) and kept in a `localStorage` wallet (`bc_coins`).

| earned from | coins | (all in the `T` block) |
|---|---|---|
| each parachute coin / star | 1 / 5 | `EARN_COIN`, `EARN_STAR` |
| each spell-book page | 3 | `EARN_PAGE` |
| clearing the level | 15 | `EARN_WIN` |
| a lost climb | pages + up to 10 for height | `EARN_HEIGHT` |

A typical win banks **about 45-60 coins**, a lost climb 2-20. Tabs: **HATS, OUTFIT, PACKS, CHUTES, BOOSTS**. Tap a row to try it
on (live Pip preview; chutes show Pip under the canopy; packs alternate front/back), tap again or press BUY. BUY opens a
YES/NO confirm ("YOU'LL HAVE n LEFT"); without enough coins you get "NOT ENOUGH COINS YET! KEEP CLIMBING TO EARN MORE."
Bought items are worn straight away; WEAR / TAKE OFF later. Keyboard: left/right tabs, up/down items, Enter buy/wear,
U boost on/off, Esc back. Entry points: title, creator and results.

| tab | item | price | wins needed (~50/win) |
|---|---|---|---|
| hats | party hat / propeller cap / gold crown | 40 / 80 / 300 | 1 / 2 / 6 |
| outfit | stripy top / overalls / lilac hair / gold outfit | 50 / 90 / 60 / 200 | 1 / 2 / 2 / 4 |
| packs | teddy / rocket / wing pack / gold gear colour (classic pack free) | 100 / 150 / 220 / 150 | 2 / 3 / 5 / 3 |
| chutes | polka dots / starry / checkers / rainbow (classic stripes free) | 50 / 70 / 80 / 160 | 1 / 2 / 2 / 4 |
| boosts | hard hat start / extra life / coin magnet / slow-mo | 25 / 40 / 30 / 35 | each use |
| giant sets | Wizard hat + Wizard robe | free after cheering up the Wizard (first win) | |
| | Trapper hat + plaid, Viking helmet (soft horns) + vest, Santa hat + suit, pirate tricorn + sash | locked: "CHEER UP THE LUMBERJACK TO UNLOCK" etc. (try-on works) | |

Everything (~1800 coins of cosmetics) takes about 35 wins. **Boosts** are consumables: bought one at a time (max 9
held), switched on per climb (max `MAX_BOOSTS` = 2, of which only `MAX_DEFENSIVE` = 1 "helper": hard hat / extra
life / slow-mo; so the only legal pair is a helper + the coin magnet) and used up when the climb starts (shown
bottom-left in the HUD).
* hard hat start: a hat that blocks `START_HAT_HITS` = 2 hits (a found one blocks 3)
* extra life: 4 hearts for that climb (never stacks)
* coin magnet: pulls coins within 1.8 units in the **parachute bonus only**
* slow-mo: hazards x0.6 for the first 15 s

A helper boost also makes hazards 5% faster that climb (`DEF_BOOST_K`). State: `bc_coins`, `bc_owned`, `bc_cheered`,
`bc_boosts`, `bc_boost_eq`. `?debug=1&coins=500` grants coins on load; `C` adds +100 in debug mode.

**Art:** the new hats, outfit patterns (overlay layers between body and hair) and pack styles are extra Blender layers in
`web/pip.py` (`SHOP_HATS`, `PATTERNS`, `PACK_STYLES`), parachutes are keyed canopy props (`CHUTES`). The themed items use
new fixed (non-recoloured) colours (`EXTRA`: purple, gold, red, silver, brown, cream, rainbow); hat bands, party hat and
propeller and the wing pack follow the gear colour.

## Longer beard + shelters
The climb is `T.CLIMB_LENGTH` = **1.6x** the original Wizard beard (36.75 instead of 22.75 units, 40 rows). It's made
in `game.js` at load time by repeating original rows 8-19 (`LEN_BAND`) in both the tile map and the background image,
so the face, mouth and street are untouched. Pages, tangled hard hats, shelters and the hazard ramp are placed by climb
progress, so they spread over the whole length; the parachute keeps ~24 coins / 4 stars; the time bonus scales.
`?len=1` plays the original length.

**Shelters:** 2-3 thick knotted tangles per climb (`SHELTER_MIN/MAX`), spread between 18% and 90% of the climb
(`SHELTER_FIRST/LAST`). When Pip climbs into one it lights up with a blinking ring and a timer bar; falling hazards
bounce off ("BOING!"). After `SHELTER_S` = 3 s it unravels and can't be used again, so you can't camp in it.
`SHELTERS: false` or `?shelters=0` turns them off. Shot: `shots/32_shelter_boing.png`.

## Difficulty
All numbers are in the `T` block (commented). Throws and fall speed ramp with height (`THROW_SLOW/FAST`,
`FALL_SLOW/FAST`, aim `AIM` -> `AIM_TOP`); the top third (`UPPER_P` = 0.66) adds more throws (`UPPER_THROW_K`), faster
falls (`UPPER_FALL_K`) and sometimes a pair of items in two columns (`UPPER_PAIR`). The bottom is nearly unchanged (1.9 s instead of
2.0 s between throws) so first-time players still get a gentle start. `python3 web/balance_check.py [old none hardhat life slowmo]` plays bot climbs (a "good" bot that dodges 75%
of the hazards in its column and a "casual" one that dodges 45%) and writes `build/balance.jsonl`.

**How it is built:** Pip is a 3D model (`web/pip.py`, same Empty rig and poses as `climber.py`) split into layers:
2 bodies, 4 hair styles, 3 hats, 3 hard-hat states, backpack, cat. Recolourable parts use unique **key colours**.
Every layer is rendered in Blender (Workbench) with the body visible in a mask colour, so the body still hides what is
behind it (e.g. back hair seen from the front). `build_web.py` quantises the layers to the key palette and packs
them into a small atlas. `game.js` stacks the layers, swaps the key colours for the chosen preset colours
(curated pixel palettes) and adds the same 1px black outline as `postprocess.py`; results are cached per pose.
The townsfolk are the same rig (smaller, front view) recoloured with fixed looks.

## Controls
| Touch | Keyboard | Action |
|---|---|---|
| tap left / right half | Left / Right (or A / D) | reach with that arm; alternate L-R-L-R to climb (same arm twice = no climb) |
| same side twice within 250 ms | double press | dyno: leap one column sideways |
| two-finger tap | Down / Space (or S), right-click | brace (blocks one hit; 0.65 s, 1.1 s cooldown) |
| press and hold (>280 ms) | hold Up (or W) | hold tight (survive the sneeze) |
| tap / hold left / right half (parachute) | Left / Right | steer |
| tap (cutscenes) | Enter | skip |
| speaker icon | M | mute; P pauses on desktop |

URL params: `?debug=1` (hitboxes, bald/hold tile overlay, z/column/FPS; `&coins=N` grants coins), `?skip=top` (skips creator, cinematic and
intro, uses the saved look, starts near the face).

## Rebuilding
```
blender -b --python web/render_web_assets.py -- --level grandpa   # World 1-1: level, faces (smile / beam), waving hand
for l in goat lumberjack mountain bigfoot elf rudolph ice yeti santa gnome rumpel rapunzel dwarf; do blender -b --python web/render_web_assets.py -- --level $l --only level,faces; done
blender -b --python web/render_web_assets.py     # Blender 4.2 (~25 s): level images + tile map, hazards, hat items,
                                                  #   Wizard smile/sleep faces, Pip + townsfolk layers, story props,
                                                  #   the other 4 giants' portraits / tossed things / treasures
        # -- --only level,faces,pip,giants        #   (re-render just some passes)
python3 web/build_web.py                          # quantise + outline + atlases + embed -> web/index.html
python3 web/test_game.py                          # Playwright, iPhone 14 emulation -> web/shots/*.png, *.gif
python3 web/balance_check.py grandpa goat lumberjack mountain bigfoot   # World 1 bot runs (other configs = the Wizard)
```
Source: `web/src/game.js` (game; tuning block `T` at the top, incl. scene lengths and parachute steering),
`web/src/index.template.html` (page shell/meta), `web/pip.py` (Pip, townsfolk, props - Blender).
The test needs `pip install playwright` and uses the system Chrome at /usr/bin/google-chrome.
It covers the creator (arrows, randomize, persistence), the cinematic (and skipping it from the creator, title and
results), the intro skip, all the original climbing checks, pages, reaching the top (also via `?skip=top`), the ending
(hazards stop, Wizard asleep), the parachute (steering, coins, no deaths, 10-15 s), the bird, the results buttons,
the keyboard path and the file size, and the shop: earning (a win banks the exact coins), not enough coins, confirm NO/YES,
buying, reload persistence, `?debug=1&coins=`, items rendering in the climb (crown gold / Wizard purple pixels) and the
parachute (rainbow pixels), boosts (limits, applied, consumed, the hard hat absorbing a hit, the magnet), the Wizard set
unlocking after a win, 44 px creator arrows, the creator/results/title SHOP links and the cinematic showing only once ever. Screenshots: `shots/12_creator*.png`, `cinematic_*.png`, `13_intro*.png`,
`14_ending_sleeping_wizard.png`, `15_parachute.png`, `16_bird_carry_next_lumberjack.png`, `17_results_thanks.png`;
Shop: `18_results_coins_wizard_set.png`, `20_shop_not_enough_coins.png`, `21_shop_locked_lumberjack_set.png`,
`22_shop_purchase_confirm.png`, `23_shop_hats_crown.png`, `24_climb_wearing_crown.png`, `25_shop_chutes_rainbow.png`,
`26_parachute_rainbow.png`, `27_shop_boosts.png`, `28_hud_boosts.png`, `29_pip_new_hats.png` (try-on line-up),
`30_shop_outfits.png`, `31_shop_packs.png`, `12c_creator_shop_button.png`.
Grandpa / levels / layouts (`grandpa_tests`, `world_select_tests`, `layout_tests`): every tutorial prompt advancing with
real taps, 30 hits without losing a heart, the ending (phone, beam, wave, Wizard unlocked), the parachute lesson, the
world select (locked / soon / unlock / remembered / keyboard), 1280x720, 1920x1080, iPad portrait + landscape
(centred, integer scale, themed sides, keyboard play), mouse clicks on the menus, window resizing, and a request
listener proving zero network requests. Shots: `40_title_grandpa.png`, `41_grandpa_intro.png`,
`42_mid_climb_tutorial_prompt.png` (+ `42a/42b/42c`), `43_grandpa_top_phone_rings.png`, `44_grandpa_ending_beaming_wave.png`,
`45_grandpa_bird_next_wizard.png`, `46_grandpa_results.png`, `47_world_select.png` (+ `47b` unlocked, `47c` locked message),
`48_desktop_1920x1080.png`, `49_ipad_landscape.png`, `49b_ipad_portrait.png`, `cinematic_1_grandpa.png`. GIFs: `gameplay.gif` (bot-played climb) and `story.gif` (ending -> parachute -> bird).

World 1 (`world1_tests`): for each of Goat, Lumberjack, Mountain Man, Bigfoot - unlocked only after the previous giant,
intro from the world select, real-touch climbing, reaching the top, the ending (gift, beam, selfie), the next level + shop
set unlocking, the parachute, the bird and results NEXT loading the next giant; gusts / stomps with and without holding;
old saves keeping the Wizard. Shots: `60_<id>_intro.png` (+ `60b` packed), `61_<id>_mid_climb.png`, `62_<id>_ending.png`,
`63_world_select_world1.png`, `64_goat_bird_next_lumberjack.png`, `65_bigfoot_results_wizard_unlocked.png`,
`66_mountain_gust_warning.png`, `66_bigfoot_stomp_warning.png`.
World 2 (`world2_tests`): the same per-level checks for Elf, Rudolph, Ice Giant, Yeti, Santa (bird after Bigfoot = NEXT: THE ELF!,
Santa unlocks the Wizard), hoof / roar / laugh events, Santa's reindeer swoop, the Ice Giant's slide + melt timer, Rudolph's
dark stretch + nose glow, Santa asleep, old saves (Bigfoot cheered) keeping the Wizard. Shots: `70_<id>_intro.png` (+ `70b`),
`71_<id>_mid_climb.png`, `72_<id>_ending.png`, `73_world_select_world2.png`, `64b_bigfoot_bird_next_elf.png`,
`74_santa_bird_next_wizard.png`, `75_santa_results_wizard_unlocked.png`, `76_santa_swoop_warning.png`, `76b_santa_reindeer_swoop.png`,
`77_ice_sliding_melt_timer.png`, `77b_ice_melted.png`, `78_rudolph_dark_stretch.png`, `66_<id>_<event>_warning.png`.
Size: `build_web.py` stores every PNG as an exact indexed-colour PNG when that is lossless (~25% smaller overall).

## Notes / limitations
* Colour presets are curated, so each sprite stays a small fixed palette, but Pip's colours are not limited to the
  Wizard level's 16 colours (the townsfolk and the grass ground also add colours).
* The other giants in the cinematic are portraits rendered from their level files (face + 2 rows of beard, repeated
  down to the town); Grandpa and the Wizard are playable. Goat, Mountain Man and Bigfoot are names on the world
  select only (no models yet); the Lumberjack level file exists but isn't playable in the web build yet.
* The hazard list is unchanged (the Wizard still spits a black cat, a crystal ball and potions); the cinematic only
  uses kid-friendly thrown items for the other giants (coal/presents, logs/pancakes, a helmet, a cannonball).

### Balance check (bot, iPhone 14 emulation, 5 seeds each, `build/balance_final.jsonl`)
"good" bot = dodges 75% of hazards in its column, braces, holds for sneezes, leaps into shelters next to it;
"casual" = dodges 45%, slower taps. `orig` = the old short beard with the old numbers and no shelters.

| config | good: wins | clear time | hearts lost | height | casual: wins | hearts lost | height |
|---|---|---|---|---|---|---|---|
| orig (old short beard) | 3/5 | 19.9 s | 1.2 | 96% | 1/5 | 2.6 | 65% |
| new, no shelters, no boost | 1/5 | 34.3 s | 2.6 | 71% | 0/5 | 3.0 | 50% |
| new, shelters, no boost | 2/5 | 37.8 s | 2.4 | 90% | 0/5 | 3.0 | 44% |
| + hard hat start | 2/5 | 34.2 s | 2.0 | 90% | 0/5 | 3.0 | 67% |
| + extra life (4 hearts) | 2/5 | 36.4 s | 3.4 | 83% | 0/5 | 4.0 | 53% |
| + slow-mo | 1/5 | 30.8 s | 2.8 | 96% | 0/5 | 3.0 | 59% |

Five runs per row is noisy (the same config swung between 1/5 and 4/5 across runs). The bots are crude, so treat
this as relative, not as how a child plays.


## Controls setting: ONE HAND / TWO HANDS
Settings (title gear, or G) holds CONTROLS and SOUND; both are saved in localStorage (`bc_controls`, `bc_mute`).
Touch devices default to ONE HAND; `?controls=one|two` overrides without saving. The keyboard works in both modes.
- ONE HAND: tap anywhere = the next arm (alternates, so tapping climbs); swipe left/right = hop (dyno); swipe down = climb
  down 1 unit; swipe up = quick double reach; press + hold anywhere = hold tight; two-finger tap = brace.
- TWO HANDS: unchanged, plus swipe down = climb down. Keyboard: X / PageDown = climb down.
- Swipe = >= 28 CSS px within 320 ms, dominant axis >= 1.4x the other. A touch reaches instantly; if it becomes a swipe
  the reach is undone, so a swipe never also counts as a tap.
- Parachute: hold left/right half to steer, or swipe left/right.
- Grandpa tutorial adds a "SWIPE DOWN TO CLIMB DOWN" lesson; prompts and the how-to follow the active mode.


## Fast source-only stability workflow

For code/template changes that do not change art, run `python3 web/build_runtime.py`
then `npm run check` from the project root. This reuses the generated asset cache
in `web/index.html`; it does not require Blender or raw renders. See
[DEVELOPMENT.md](../DEVELOPMENT.md) for verified coverage and remaining
full-render/browser validation.
