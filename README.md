# TerrainWorld

My favorite project, just minecraft without the blocks

## File structure:
```
.
├── __pycache__                    (Some optimization that github likes to do)
│   └── noiselib.cpython-313.cpc   (Pre-compiled files so that you don't have to)
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

## Dependencies

`arcade`
`numpy`
`pillow`
`pathlib` (parsers only, if you just want to play the game you can safely ignore this)
`matplotlib`
`ast`
`base64`
`time`

## Installation instructions:

1. Download all the files as a `.zip` and unzip
2. Read `LICENSE.txt` if you plan to share
3. Run `terrain2d.py`

Controls are explained in-game through the menu icon.

## Credits:

Font: [Dusk Free Fonts](https://dusk-games.itch.io/dusk-free-fonts)

Other: [Adventure Pack](https://o-lobster.itch.io/adventure-pack)

Users: CrazyCat30, fenl

## Gameplay and reference

When you first boot up this game by running `terrain2d.py`, you will be prompted for a screen size between 4 and 64.
If you choose 16 (the default), you will see something like this: (Don't worry about your cursor, this game implements a custom one)

![First screen](Terrainer%20Shots/Explainer%200.png)

The number on the bottom is your coordinates. See those ultramarine buttons? The one on the right shows your current mode. If you click on it, you will see something like this:

![Second screen](Terrainer%20Shots/Explainer%201.png)

Now, the three letters stand for Normal, Creative, and X-ray. Click on the X button in blue:

![Third screen](Terrainer%20Shots/Explainer%202.png)

There are now five icons on the left of the screen. Search bar is available in all modes except normal. If you play around a bit (move via arrow keys), you will figure out that there is no collision in this mode. In other modes, collision follows invisible boundaries because some tiles are transparent. You can click to mine stuff and shift-click to place it back down. 

Note: you sometimes can't place stuff because there is a miniscule amount of something else there that you can't see. Just try to mine it all up and then place again.

The inventory controls are as follows:

top row (1234567890-=) to switch slots (indicated by the hand)

enter to pick stuff up (indicated by the hand moving backwards)

enter to put it back down again (indicated by the hand moving forwards again)

shift+enter to only pick up or put down half as much (there will still be half remaining in the slot or your hand)

Now, after you gather some resources and wander around, you might see something moving. If it grows into something like this:

![Tree screen](Terrainer%20Shots/Explainer%203.png)

That's a tree! They grow back after you damage them. Now get some resources from it (Hint: to get leaves, you need to whack the leaves with a stone). Now, click on the first icon on the upper-left.

![Inventory screen](Terrainer%20Shots/Explainer%204.png)

It gives you a detailed overview of your inventory!