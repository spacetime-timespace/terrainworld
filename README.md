# TerrainWorld

File structure:
```
.
├── __pycache__                    (Some random github thing I never can understand)
│   └── noiselib.cpython-313.cpc   (Some random github thing I never can understand)
├── README.md                      (Readme file)
├── parser.py                      (Two helper scripts I wrote)
├── parser 2.py                     (This one will re-parse the textures when I add new ones)
├── noiselib.py                    (A simple simplex noise library I wrote)
├── terrain2d.py                   (The main file so far)
├── saves                          (My favorite worlds)
│   └── basicworld.txt             (A test world that's the default state)
├── Terrainer shots                (My favorite screenshots)
│   └── ...
├── textures                       (The old set of textures. Modify this and then run parser2.py)
│   ├── Background                 (My crafting UI backgrounds)
│   │   └── ...
│   ├── Tiles                      (The Inventory Icon textures)
│   │   └── ...
│   ├── Font                       (These are the Dusk Fonts I found on itch.io. *)
│   │   └── ...
│   ├── Font-white                 (The white fonts that are actually used in the game)
│   │   └── ...
│   ├── itembox.png                (itembox from adventure pack)
│   └── selector.png               (hand from adventure pack)
└── new-textures                   (The same thing but 64 by 64)
    └── ...
```
  
Dependencies

`arcade`
`numpy`
`pillow`
`pathlib` (parsers only)
`matplotlib`
`ast`
`base64`
`time`

Installation instructions:

1. Download all the files as a `.zip` and unzip
2. Read `LICENSE.txt` if you plan to share
3. Run `terrain2d.py`

Controls are explained in-game through the menu icon.

Credits:

Font: https://dusk-games.itch.io/dusk-free-fonts

Other: https://o-lobster.itch.io/adventure-pack

Gameplay and reference

