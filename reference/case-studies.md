# Case studies: the songs, what was built, what the user said

The user (a home light-show builder, xLights on a Mac) judges by watching renders. Their verdicts, newest first,
are the real spec. Each song has `examples/<name>/build.py` (the generator) and `notes.md` (full handoff).

| Song | Concept | Verdict |
|---|---|---|
| **Aggie War Hymn (Fightin' Texas Aggie Band)** - `aggie_war_hymn` | Band-only recording; the words placed by the tune (user confirmed the map). Maroon and white builds Aggieland; burnt orange only for t.u. (swept off, the "eyes of Texas" burned on "sounds like hell!", a longhorn sawed off chant by chant while the whole yard sways); SHORT in the band's silences; TEXAS A&M one letter per Vert; the A&M logo redrawn as per-Vert pixel art. First build on Normal blending and picture pixel art, checked by render read-back. | **"that's pretty great"** |
| **Wizards in Winter, from scratch (TSO)** - `tso_wizards_winter` | "The notes literally dance like winter": the band's stab freezes the yard, the piano answers in snowflakes hopping across the wall; the theme plays the pixel forest like a frozen xylophone; the lead is northern lights; an orb dances through the yard now and then (the user's idea). Built overnight on "make your best guess". | pending |
| **Where Is My Mind? (Pixies)** - `pixies` | Lyrics told as a story: a pink-white "mind" light that drifts, is lost under water, is searched for with sonar pings, and floats away. Upside-down world on "feet in the air", spin, collapse, "nothing in it". Kim Deal's oohs = lavender ghosts rising; lead guitar scrolls across the wall. Band played without a click (`--loose`). | **"legit your best work so far. it's fantastic"** |
| **Joy to the World (Big Daddy Weave)** - `bdw_joy` | The yard spells the news: pixel-font words on the Verts as they're sung; the manger sends out each "the Lord is come", a star comes down on "God sent His Son", heralds run on "go tell the world"; crowns for every "He shall reign forever", climbing in the chant; JOY on all panels at the climax. | "the colors are looking more subdued than they should" → fixed: saturated family blends instead of white/red-green gradients, wall background 18 → 40 %, brighter house/trunks/sticks |
| **Shine Your Way (Owl City & Yuna)** - `owl_shine` | The whole song is one sunrise: a sky clock changes every bar from night to day; a firefly spark builds a fire, leaps, becomes the sun; the fence lights a stretch per "your way"; key change = daybreak. | **"i like it!"** |
| **In Christ (Big Daddy Weave)** - `bdw_inchrist` | A light passed heart to heart: 29 pixel sticks as a crowd lit one by one on lyric cues; pixel-art hearts that beat in the band stops; the manger as the source; per-line chorus visuals; key-change lift. | Liked, but "pixies is better - because the song is just better" |
| **Wizards in Winter (TSO)** - `tso_wizards` | A rainbow-trailed sprite dancing across the yard; call-and-response stop bars where the sprite answers the band alone; jewel colours. | **"that looked great!"** |
| **Sign of the Times (Project Hail Mary)** - `hailmary_signtimes` | Space theme from ISF shaders (starfield, solar flare, hyperspace, galaxy), cold palette warming to gold. | built; reworked for the canvas/trunk rules |
| **Little Drummer Boy (for KING & COUNTRY)** - `kc_drummer` | Candle-warm verses, nativity breakdowns, a jagged VU-waveform signature on every "pa rum pum pum pum", sticks bounce with drums. | iterated with the user; the "amber" feedback came here |
| **Oh Come All Ye Faithful (punk)** - `punk_ohcome` | First song: the instrument map, AllModels moments, peppermint pinwheel. | v1 "impressed", then the groups/canvas feedback below |

## Feedback that became rules (in the order it was given)
1. "favor using the groups instead of individual models" - and "do certain effects across the AllModels group for a
   really cool encompassing feel every so often".
2. "having [the Verts] do the same thing gets a bit monotonous" - patterns that move across them side to side or
   diagonally draw in the whole canvas.
3. Gradients for colour variety (pointed at their tobymac-marysboy sequence); sine waves across the pixel sticks.
4. A repeating, *pronounced* signature for a repeated lyric ("pa rum pum pum pum") - a straight sweep was too weak;
   the song's own jagged waveform across the wall worked.
5. "you're using a lot of that amber color" - #FFAA00 reads amber on pixels. Use #FFC832 for gold, keep amber out
   of gradients, reserve gold for meaningful moments.
6. "avoid using [the Verts] as just a solid panel of light... doesn't treat all of them combined as a canvas". Solid
   colour that *moves* across is fine. All three canvas styles (melody scroll, drum hits launching motion, rolling
   washes) "are worth keeping in the repertoire" - choose per song.
7. "the tree verts are different than the 6 free standing verts and should be used differently" - they're flat
   panels wrapped around real trunks: rings up the trunk, barber poles, rising from the roots, drips. No flashing.
8. Reference sequences the user pointed to and what was taken: punk-joy (spinning peppermint pinwheel),
   DreamsOfFireflies (3D whirl, swinging spirals), interstellar_cornfield (shaders, long fades),
   joy_daddyweave (call-and-response timing, big lights breathing).
9. "Get creative. Use more color. Make it feel like there's a sprite dancing across the yard" → characters.
10. "a light show inspired by the lyrics in this song and by the distinct sound" → the Pixies approach, now the
    reference: find the story, give it a character, time literal moments to the words, give each signature sound
    one consistent motif.
11. "the colors are looking more subdued than they should" (Joy): pastel gradients to white, a muddy red→green blend
    on the arches and an 18 % canvas background. Keep colours saturated; measure with `scripts/color_check.py`.
12. "Be sure to use the maroon and white colors of the school" + "I found a free to use logo… could we do something
    with that?" (Aggie War Hymn): the school's colours are the palette (white is a real colour here, not a pastel;
    don't blend maroon into white - that's pink). The logo file didn't read on the panels, so it was redrawn as
    pixel art from its proportions - say so plainly rather than shipping an unreadable picture.
13. "I changed the scene layout a bit because of some gaps" → re-fetch the layout, diff the model positions
    (two Verts moved in and back), recompute the panel positions, rebuild, re-render, check. Order unchanged =
    the single-panel art is unaffected; group-buffer aim points (`VERT_X`) move.
14. "Some sphere or orb that dances across the scene occasionally would feel lively" → `seqlib.orb` (techniques.md).
15. "Don't forget if you add anything that could improve the skill… put it in a worktree" → skill changes go on a
    branch in a git worktree, never onto the checkout the skill is installed from.
