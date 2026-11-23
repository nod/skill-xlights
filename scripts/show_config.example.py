"""The show's layout, as the generator sees it. Copy to show_config.py and fill in for your show
(`./run layout_report.py --draft-config > show_config.py` writes a starting point).

This example is the lol2026 show the skill was built on. Names must match xlights_rgbeffects.xml exactly.
The comments matter as much as the names: write down what each prop physically IS, because good sequencing
treats a tree-trunk wrap differently from a free-standing matrix wall.
"""

# where the show folder lives on the machine that runs xLights (media and shader paths are written with it).
# None = this folder. The lol2026 show is generated on Linux but rendered on a Mac:
MEDIA_ROOT = '/Users/you/xlights/show'

# optional: the folder under the show that holds the song folders, if it isn't 'seqs' (e.g. 'seq2026'). The media
# path written into each sequence uses it; on the agent's copy of the show, symlink seqs -> it for the scripts.
# SEQS_DIR = 'seq2026'

# optional: how layers blend. Unset (None) = xLights' Normal, the default since Max showed only the top layer on
# xLights 2026.19 (reference/xsq-format.md "Layer blending"). Set 'Max' only if your xLights renders it right.
# LAYER_BLEND = 'Max'

# the rows the generator writes, top to bottom in the sequencer. Groups are disjoint sets of models, so effects on
# different rows never fight; single models only where no group covers them.
ELEMENTS = ['AllModels', 'Verts', 'trees', 'arches_big', 'pix-evens', 'pix-odds', 'Spiral Trees',
            'fenceline', 'roofline-1', 'window-master', 'window-char', 'grinch-1', 'Nativity Spot']

ALL = 'AllModels'           # the whole-yard group, for "moments" (arches + sticks + Verts + spirals)
CANVAS = 'Verts'            # six free-standing 6x44 vertical matrices in a row: ONE canvas, never flash panels
TRUNKS = 'trees'            # three 264-node matrices wrapped around the street side of real tree trunks
ARCHES = 'arches_big'       # four 50-node arches across the yard
FOREST = ['pix-evens', 'pix-odds']      # 29 pixel sticks (8 px each, vertical), split alternately in two groups
MATRIX = [CANVAS, TRUNKS]
SPIRAL = 'Spiral Trees'     # four spiral trees (custom models), two big two little
FENCE = 'fenceline'         # one long single line across the whole front of the yard
HOUSE = ['roofline-1', 'window-master', 'window-char']
FLOODS = ['grinch-1', 'Nativity Spot']  # Nativity Spot is a single RGB spot on the manger: the story's light source
NON_MEMBERS = [TRUNKS, FENCE] + HOUSE + FLOODS   # rows the ALL group doesn't cover

# horizontal centre (% across the group's buffer) of each member, left to right - for aiming at one prop inside a
# group (a ripple on the 3rd Vert, a ring on tree 2). layout_report.py prints these for every group.
VERT_X = [1.2, 18.5, 38.6, 59.4, 80.2, 98.8]
TREE_X = [5.4, 35.0, 94.6]
ARCH_X = [5.1, 36.0, 69.8, 95.6]
