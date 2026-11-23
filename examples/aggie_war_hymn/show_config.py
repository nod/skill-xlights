"""lol2026 show layout as of 2026-11-21 (xlights_rgbeffects.xml), as the generator sees it.

Names must match xlights_rgbeffects.xml exactly. The comments say what each prop physically IS.
The sequences live in seq2026/ on the Mac; this Linux copy has `seqs -> seq2026` so the tooling's seqs/<song> paths work.
"""

# the show folder on the Mac that runs xLights (media and shader paths are written with it)
MEDIA_ROOT = '/Users/you/xlights/lol2026'
SEQS_DIR = 'seq2026'        # this show keeps its song folders in seq2026/ (the agent's copy symlinks seqs -> seq2026)

# rows the generator writes, top to bottom. Groups are disjoint, so effects on different rows never fight.
ELEMENTS = ['AllModels', 'Verts', 'trees', 'arches_big', 'pix-evens', 'pix-odds', 'Spiral Trees',
            'fenceline', 'roofline-1', 'window-master', 'window-char', 'grinch-1', 'Nativity Spot']

ALL = 'AllModels'           # the whole-yard group: 29 sticks + 10 arches + 9 Verts + 4 spirals (52 models)
CANVAS = 'Verts'            # nine free-standing 6x44 vertical matrices = ONE canvas, never flash panels.
                            # Staggered (layout of 2026-11-21 22:44): Vert-4, 1, 2, 5 in the front row; Vert-3, 7, 8,
                            # 9, 6 set back (3 and 6 moved in and back to close gaps). Left to right from the street:
                            # [3], 4, [7], 1, [8], 2, [9], 5, [6]   ([] = back row)
TRUNKS = 'trees'            # five 6x44 matrices wrapped around real tree trunks: tree-1, 2, 5, 3 clustered on the
                            # left of the yard, tree-4 alone far right. Rings up the trunk, poles, roots, drips.
ARCHES = 'arches_big'       # ten 50-node arches in a row across the front of the yard
FOREST = ['pix-evens', 'pix-odds']      # 29 pixel sticks (8 px each, vertical), split alternately in two groups
MATRIX = [CANVAS, TRUNKS]
SPIRAL = 'Spiral Trees'     # four spiral trees (custom models): Spiral Tree 3 (big, left), little spiral - left,
                            # little spiral - right, Spiral Tree 2 (big, right)
FENCE = 'fenceline'         # one 230 px line across the whole front of the yard (closest to the street)
HOUSE = ['roofline-1', 'window-master', 'window-char']   # roofline + two window frames on the house
FLOODS = ['grinch-1', 'Nativity Spot']  # single RGB nodes: a flood on the grinch; Nativity Spot on the manger
NON_MEMBERS = [TRUNKS, FENCE] + HOUSE + FLOODS   # rows the ALL group doesn't cover

# member centres across each group (% of its width), left to right (layout_report.py; approximate)
VERT_X = [0.0, 15.8, 24.8, 38.5, 50.7, 62.8, 74.7, 85.6, 100.0]     # 3, 4, 7, 1, 8, 2, 9, 5, 6
VERTS_LR = ['Vert-3', 'Vert-4', 'Vert-7', 'Vert-1', 'Vert-8', 'Vert-2', 'Vert-9', 'Vert-5', 'Vert-6']
VERTS_FRONT = ['Vert-4', 'Vert-1', 'Vert-2', 'Vert-5']
VERTS_BACK = ['Vert-3', 'Vert-7', 'Vert-8', 'Vert-9', 'Vert-6']
TREE_X = [0.0, 4.4, 12.2, 15.4, 100.0]                              # tree-1, 2, 5, 3, 4
TREES_LR = ['tree-1', 'tree-2', 'tree-5', 'tree-3', 'tree-4']
ARCH_X = [0.0, 11.1, 22.2, 33.3, 44.4, 55.6, 66.7, 77.8, 88.9, 100.0]
SPIRAL_X = [0.0, 46.5, 74.3, 100.0]
