# Version 3 = v2 with heights for Filipino users (average ~163 cm men / ~151 cm women): storage boxes 300
# (was 400) -> mattress top ~500, so feet reach the floor sitting on the edge; nightstands flush with the mattress
# top (500, was 600); bridge over the bed 650 tall (was 450) so its doors start ~1720, within reach, still to the ceiling.
# Version 2: over-bed wall unit + 5 ft x 6 ft storage bed built from modular storage boxes.
# Same material and handleless style as the v3 cabinet: 3/4" marine plywood, HPL both faces,
# 45 deg finger-pull bevels on the back of door / drawer pull edges. Units: mm.
#
# Against the wall OPPOSITE the cabinet, wall-to-wall and symmetric:
#
#   +--------+=========== bridge (4 doors) ===========+--------+
#   | tall   |   LED downlights                        | tall   |
#   | door   |                                         | door   |
#   |--------|      upholstered, diamond-tufted        |--------|
#   | LED lit|      headboard panel                    | LED lit|
#   | niche  |                                         | niche  |
#   |--------|                                         |--------|
#   | open   |                                         | open   |
#   +--------+  ---------- mattress 5x6 ------------   +--------+
#   | 2 drw  |  [ 6 storage boxes under the mattress ] | 2 drw  |
#   +--------+                                          +--------+
#
# Bed storage (plan view, 2 boxes across x 4 rows):
#
#   head  |  lift-up  |  lift-up  |   behind the nightstands: a drawer can't slide out there,
#         |           |           |   so these have lids hinged at the head side
#      <- | side drw  | side drw  | ->  slide out sideways into the gap beside the bed
#      <- | side drw  | side drw  | ->  (3/4-extension runners: the gap to the wall is ~350 mm)
#   foot  | drawer    | drawer    |   slide forward, towards the cabinet
#             v           v
#
# Each box is its own laminated carcass, joined to its neighbours with connector bolts; the
# mattress lies directly on the box tops.
#
# Handleless pulls (bevel faces open space or a reveal):
#   - nightstand drawers: bevel on the top edge, SHADOW_GAP above each front
#   - tower doors: bevel on the bottom edge, pulled from the lit niche below
#   - bridge doors: bevel on the bottom edge, pulled from below
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet/build_bed_v3.py").read())
# or headless:  freecadcmd build_bed_v3.py
#
# Axes are the same as build_cabinet_v3.py: X = width (left->right, facing the cabinet wall),
# Y = depth (0 = cabinet door face, +Y = towards the cabinet wall), Z = up.
# The opposite wall sits at negative Y; this unit faces +Y.

import csv
import os
import re
import FreeCAD as App
import Part

# ---------------- parameters ----------------
WALL_W = 2286          # room width wall-to-wall (90 in; room is 116 x 90 in)
WALL_H = 2380          # floor to ceiling
CAB_DEPTH = 470        # cabinet depth: its wall is at Y = CAB_DEPTH
ROOM_L = 2946          # cabinet wall -> opposite wall (116 in)
FIT = 5                # gap: tower to side wall, and tower to bed
FIT_H = 10             # unit lower than the ceiling, closed by a scribe strip

MAT_W = 1524           # 5 ft mattress width
MAT_L = 1829           # 6 ft mattress length
MAT_H = 200            # mattress thickness (visual only)
CLR = 10               # clearance around the mattress inside the rails

PLY = 18               # 3/4" marine plywood core
LAM = 0.8              # laminate (HPL) per face
T = PLY + 2 * LAM      # finished visible panel thickness (19.6)
GAP = 3                # gap around doors / drawer fronts
BEVEL = 15             # 45 deg finger-pull bevel
SHADOW_GAP = 25        # finger groove above drawer fronts
TOE = 3                # felt pads

# storage bed (modular boxes)
BOX_H = 300            # box height floor -> top of the lids (mattress lies on it; v2: 400)
N_COLS = 2             # boxes across the bed
DRAWER_ROW_L = 500     # foot-row box length (drawer depth + front)
DRAWER_BOX_D = 450     # foot drawer depth = 450 mm full-extension runners
N_SIDE_ROWS = 2        # rows of side drawers between the head row and the foot row
SIDE_DRAWER_D = 450    # side drawer depth = 450 mm 3/4-extension runners (~337 mm travel)
SIDE_TRAVEL = 337      # how far the side drawers open (must stay inside the gap to the wall)
HEAD_CLR = 10          # side drawers start this far past the nightstand front
LIDS_OPEN_DEG = 0      # e.g. 60 to show the head-row lids open (mattress hidden)
DRAWERS_OPEN = 0       # e.g. 1 to show all drawers pulled fully out

# headboard
UPH_T = 50             # upholstered panel thickness (12 mm ply base + foam + fabric)
UPH_Z0 = BOX_H - 30    # bottom of the upholstered panel (tucked just behind the mattress)
TUFT = 180             # diamond tuft pitch (visual)

# towers + bridge
NIGHT_D = 450          # nightstand (lower part) depth from the wall
NIGHT_H = BOX_H + MAT_H # nightstand top flush with the mattress top (500; v2: 600)
NIGHT_PLINTH = 60
UPPER_D = 350          # upper tower + bridge depth from the wall
OPEN_NICHE_H = 280     # open shelf right above the nightstand
LIT_NICHE_H = 300      # LED lit niche above that
BRIDGE_H = 650         # cabinets over the bed (v2: 450): bottom ~1720, reachable
N_BRIDGE_DOORS = 4

UNIT_H = WALL_H - FIT_H
FRAME_W = MAT_W + 2 * CLR + 2 * T       # storage-box platform outside width
FRAME_L = MAT_L + 2 * CLR + 2 * T
BOX_W = FRAME_W / N_COLS
TOWER_W = (WALL_W - FRAME_W) / 2 - 2 * FIT
XT_IN = FIT + TOWER_W                   # inner face of the left tower
BRIDGE_W = WALL_W - 2 * XT_IN
BRIDGE_Z = UNIT_H - BRIDGE_H

Y_WALL = CAB_DEPTH - ROOM_L             # face of the opposite wall
X0 = (WALL_W - FRAME_W) / 2             # left edge of the bed
Y0 = Y_WALL + PLY + UPH_T               # head of the bed, against the upholstered panel
Y1 = Y0 + FRAME_L
HEAD_ROW_L = Y_WALL + NIGHT_D + HEAD_CLR - Y0                # bed length hidden behind the nightstands
SIDE_ROW_L = (FRAME_L - HEAD_ROW_L - DRAWER_ROW_L) / N_SIDE_ROWS

DOC_NAME = "Bed_Wall_Unit_v3"
CUT_LIST = "cut_list_bed_v3.csv"
HARDWARE = "hardware_bed_v3.csv"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet"

# ---------------- colours ----------------
C_FRAME = (0.80, 0.74, 0.68)     # warm taupe laminate (as in the reference photo)
C_CARCASS = (0.93, 0.89, 0.80)
C_PLY = (0.93, 0.89, 0.80)
C_DRAWER = (0.85, 0.78, 0.65)
C_PLINTH = (0.30, 0.27, 0.25)
C_UPH = (0.62, 0.55, 0.50)
C_LED = (1.00, 0.85, 0.50)
C_METAL = (0.55, 0.55, 0.58)
C_MATTRESS = (0.90, 0.88, 0.80)
C_CAB = (0.80, 0.80, 0.80)

# ---------------- helpers ----------------
if App.listDocuments().get(DOC_NAME):
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)

cut_list = []   # (module, part, length, width, thickness, note)
_colours = {}
BEVEL_NAMES = {"L": "left", "R": "right", "T": "top", "B": "bottom"}


def group(name, parent=None):
    g = doc.addObject("App::DocumentObjectGroup", name)
    if parent:
        parent.addObject(g)
    return g


def _bevelled(dx, dy, dz, edge):
    """Box with a 45 deg chamfer on the back edge named by `edge`. This unit faces +Y, so the back is y = 0."""
    shape = Part.makeBox(dx, dy, dz)
    target = {"L": (0, 0, None), "R": (dx, 0, None), "B": (None, 0, 0), "T": (None, 0, dz)}[edge]
    for e in shape.Edges:
        c = e.CenterOfMass
        if all(v is None or abs(getattr(c, a) - v) < 1e-6 for a, v in zip("xyz", target)) \
                and abs(e.Length - (dz if edge in "LR" else dx)) < 1e-6:
            return shape.makeChamfer(BEVEL, [e])
    raise ValueError("bevel edge not found")


def box(grp, name, x, y, z, dx, dy, dz, colour=C_FRAME, cut=True, note="", bevel=None):
    """Axis-aligned panel, optionally with a finger-pull bevel. Recorded in the cut list."""
    if bevel:
        o = doc.addObject("Part::Feature", name)
        o.Shape = _bevelled(dx, dy, dz, bevel)
        note = (note + "; " if note else "") + f"45deg bevel {BEVEL_NAMES[bevel]} edge (back)"
    else:
        o = doc.addObject("Part::Box", name)
        o.Length, o.Width, o.Height = dx, dy, dz
    o.Placement.Base = App.Vector(x, y, z)
    grp.addObject(o)
    _colours[o.Name] = colour
    if cut:
        dims = sorted([dx, dy, dz], reverse=True)
        cut_list.append((grp.Label, name, round(dims[0], 1), round(dims[1], 1), round(dims[2], 1), note))
    return o


def carcass(grp, x, z, w, h, d, prefix=""):
    """Box against the wall facing +Y: sides full height, top/bottom between, 18 mm back at the wall."""
    yb = Y_WALL + PLY
    box(grp, prefix + "Back", x, Y_WALL, z, w, PLY, h, C_PLY)
    box(grp, prefix + "Side_L", x, yb, z, T, d - PLY, h, C_FRAME, note="HPL both faces")
    box(grp, prefix + "Side_R", x + w - T, yb, z, T, d - PLY, h, C_FRAME, note="HPL both faces")
    box(grp, prefix + "Bottom", x + T, yb, z, w - 2 * T, d - PLY, T, C_CARCASS, note="HPL both faces")
    box(grp, prefix + "Top", x + T, yb, z + h - T, w - 2 * T, d - PLY, T, C_CARCASS, note="HPL both faces")


def shelf(grp, name, x, z, w, d, note="HPL both faces, edge-band front"):
    box(grp, name, x + T, Y_WALL + PLY, z, w - 2 * T, d - PLY - 10, T, C_CARCASS, note=note)


def door(grp, name, x, z, w, h, d, bevel):
    """Overlay door on the front of a carcass of depth d."""
    box(grp, name, x + GAP / 2, Y_WALL + d, z + GAP / 2, w - GAP, T, h - GAP, bevel=bevel, note="HPL both faces")


def drawer(grp, name, x_in, w_in, z, h, front, front_y, bd=350):
    """Drawer box (12.5 mm runner clearance) behind an inset front=(x, z, w, h) flush with the carcass front.
    Returns its parts so they can be shown pulled out."""
    clr = 12.5
    bw, bh = w_in - 2 * clr, h - 40
    fx, fz, fw, fh = front
    by = front_y - T - bd
    return [box(grp, name + "_Front", fx, front_y - T, fz, fw, T, fh, bevel="T", note="HPL both faces"),
            box(grp, name + "_Side_L", x_in + clr, by, z + 15, PLY, bd, bh, C_DRAWER),
            box(grp, name + "_Side_R", x_in + clr + bw - PLY, by, z + 15, PLY, bd, bh, C_DRAWER),
            box(grp, name + "_Back", x_in + clr + PLY, by, z + 15, bw - 2 * PLY, PLY, bh, C_DRAWER),
            box(grp, name + "_Bottom", x_in + clr + PLY, by + PLY, z + 15, bw - 2 * PLY, bd - PLY, PLY, C_DRAWER)]


def led(grp, name, x, y, z, dx, dy, dz=8):
    box(grp, name, x, y, z, dx, dy, dz, C_LED, cut=False)


root = group("Bed_Wall_Unit_v3")

# ================= SIDE TOWERS =================
for side, x in (("Left", FIT), ("Right", WALL_W - FIT - TOWER_W)):
    g = group(f"Tower_{side}", root)
    # --- nightstand: recessed plinth + 2 handleless drawers ---
    gn = group(f"Nightstand_{side}", g)
    box(gn, "Plinth", x + 20, Y_WALL, TOE, TOWER_W - 40, NIGHT_D - 50, NIGHT_PLINTH - TOE, C_PLINTH,
        note="4 strips glued as a ring; sizes = outside of the ring")
    hc = NIGHT_H - NIGHT_PLINTH
    carcass(gn, x, NIGHT_PLINTH, TOWER_W, hc, NIGHT_D)
    in_w = TOWER_W - 2 * T
    slot = (hc - 2 * T) / 2
    for i in range(2):
        z = NIGHT_PLINTH + T + i * slot
        drawer(gn, f"Drawer_{i + 1}", x + T, in_w, z, slot,
               front=(x + T + GAP / 2, z + GAP / 2, in_w - GAP, slot - GAP - SHADOW_GAP),
               front_y=Y_WALL + NIGHT_D)
    # --- upper tower: open niche, LED lit niche, tall door to the top ---
    gu = group(f"Upper_{side}", g)
    hu = UNIT_H - NIGHT_H
    carcass(gu, x, NIGHT_H, TOWER_W, hu, UPPER_D)
    z_open = NIGHT_H + OPEN_NICHE_H
    z_lit = z_open + LIT_NICHE_H
    shelf(gu, "Shelf_Open_Niche", x, z_open, TOWER_W, UPPER_D)
    shelf(gu, "Shelf_Lit_Niche", x, z_lit, TOWER_W, UPPER_D, note="HPL both faces, edge-band front; LED groove underside")
    led(gu, f"LED_Niche_{side}", x + T + 10, Y_WALL + UPPER_D - 60, z_lit - 8, in_w - 20, 12)
    for i, z in enumerate((z_lit + (UNIT_H - T - z_lit) / 2,)):
        shelf(gu, f"Shelf_Behind_Door_{i + 1}", x, z, TOWER_W, UPPER_D)
    door(gu, "Door", x, z_lit, TOWER_W, UNIT_H - z_lit, UPPER_D, bevel="B")

# ================= BRIDGE OVER THE BED =================
gB = group("Bridge", root)
carcass(gB, XT_IN, BRIDGE_Z, BRIDGE_W, BRIDGE_H, UPPER_D)
shelf(gB, "Shelf", XT_IN, BRIDGE_Z + BRIDGE_H / 2, BRIDGE_W, UPPER_D)
dw = BRIDGE_W / N_BRIDGE_DOORS
for i in range(N_BRIDGE_DOORS):
    door(gB, f"Door_{i + 1}", XT_IN + i * dw, BRIDGE_Z, dw, BRIDGE_H, UPPER_D, bevel="B")
for i, f in enumerate((0.3, 0.7)):        # two LED downlights washing the headboard
    o = doc.addObject("Part::Cylinder", f"LED_Downlight_{i + 1}")
    o.Radius, o.Height = 35, 6
    o.Placement.Base = App.Vector(XT_IN + BRIDGE_W * f, Y_WALL + PLY + UPH_T + 60, BRIDGE_Z - 6)
    gB.addObject(o)
    _colours[o.Name] = C_LED

# ================= HEADBOARD =================
gH = group("Headboard", root)
box(gH, "Headboard_Backer", XT_IN, Y_WALL, TOE, BRIDGE_W, PLY, BRIDGE_Z - TOE, C_PLY,
    note="screw to wall + towers; behind the upholstery")
up_h = BRIDGE_Z - UPH_Z0
box(gH, "Upholstered_Panel_Base", XT_IN + GAP, Y_WALL + PLY, UPH_Z0, BRIDGE_W - 2 * GAP, 12, up_h, C_PLY,
    note="12 mm ply; 38 mm foam + fabric, diamond tufted, buttons on a "
         f"{TUFT} mm grid")
pad = Part.makeBox(BRIDGE_W - 2 * GAP, UPH_T - 12, up_h)
# diamond tufting: buttons pressed into the foam on two offset grids
for row in range(int(up_h // (TUFT / 2)) + 1):
    for col in range(int((BRIDGE_W - 2 * GAP) // TUFT) + 2):
        bx = col * TUFT + (TUFT / 2 if row % 2 else 0)
        bz = row * TUFT / 2
        if 20 < bx < BRIDGE_W - 2 * GAP - 20 and 20 < bz < up_h - 20:
            pad = pad.cut(Part.makeSphere(22, App.Vector(bx, UPH_T - 12 + 10, bz)))
uph = doc.addObject("Part::Feature", "Upholstery_Foam")
uph.Shape = pad
uph.Placement.Base = App.Vector(XT_IN + GAP, Y_WALL + PLY + 12, UPH_Z0)
gH.addObject(uph)
_colours[uph.Name] = C_UPH

# ================= STORAGE BED: modular boxes =================
gP = group("Storage_Bed", root)
hw = BOX_H - T - TOE                    # wall height under the top / lid
zd = TOE + 20 + PLY                     # drawers run above the box bottom
dh = BOX_H - T - zd                     # drawer slot height
lids, pulled_y, pulled_x = [], [], []


def box_walls(g, x, y, w, l, front=True):
    """Laminated carcass on the floor: sides run head -> foot, head/foot panels between, ply bottom."""
    box(g, "Side_L", x, y, TOE, T, l, hw, note="HPL both faces")
    box(g, "Side_R", x + w - T, y, TOE, T, l, hw, note="HPL both faces")
    box(g, "Head", x + T, y, TOE, w - 2 * T, T, hw, note="HPL both faces")
    if front:
        box(g, "Foot", x + T, y + l - T, TOE, w - 2 * T, T, hw, note="HPL both faces")
    box(g, "Bottom", x + T, y + T, TOE + 20, w - 2 * T, l - (2 if front else 1) * T, PLY, C_PLY,
        note="on 20 mm cleats; 2x 30 mm vent holes")


def side_front(g, name, x, y, z, dy, dz, back_x):
    """Side-facing drawer front (T thick in X) with the 45 deg bevel on its top back edge."""
    shape = Part.makeBox(T, dy, dz)
    edge = next(e for e in shape.Edges if abs(e.CenterOfMass.z - dz) < 1e-6
                and abs(e.CenterOfMass.x - back_x) < 1e-6 and abs(e.Length - dy) < 1e-6)
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape.makeChamfer(BEVEL, [edge])
    o.Placement.Base = App.Vector(x, y, z)
    g.addObject(o)
    _colours[o.Name] = C_FRAME
    cut_list.append((g.Label, name, round(max(dy, dz), 1), round(min(dy, dz), 1), round(T, 1),
                     "HPL both faces; 45deg bevel top edge (back)"))
    return o


for c in range(N_COLS):
    x = X0 + c * BOX_W
    side = "LR"[c]
    # --- head row: lift-up box behind the nightstand ---
    g = group(f"Head_Box_{side}", gP)
    box_walls(g, x, Y0, BOX_W, HEAD_ROW_L)
    lids.append((box(g, "Lid", x, Y0, BOX_H - T, BOX_W, HEAD_ROW_L, T,
                     note="HPL both faces, edge-band 4 sides; hinged at the head edge"), Y0))
    # --- side rows: drawers slide out sideways, away from the centre of the bed ---
    out = -1 if c == 0 else 1                       # opening direction in X
    x_out = X0 if c == 0 else X0 + FRAME_W          # outer face of the bed on this side

    def xs(a, dx):
        """X start of a part lying a..a+dx in from this side's outer face."""
        return x_out + a if out < 0 else x_out - a - dx

    for r in range(N_SIDE_ROWS):
        y = Y0 + HEAD_ROW_L + r * SIDE_ROW_L
        g = group(f"Side_Box_{r + 1}{side}", gP)
        # carcass open on the outer side: head + foot walls run across, inner wall closes the back
        box(g, "Head", x, y, TOE, BOX_W, T, hw, note="HPL both faces")
        box(g, "Foot", x, y + SIDE_ROW_L - T, TOE, BOX_W, T, hw, note="HPL both faces")
        box(g, "Inner_Side", xs(BOX_W - T, T), y + T, TOE, T, SIDE_ROW_L - 2 * T, hw, note="HPL both faces")
        box(g, "Bottom", xs(0, BOX_W - T), y + T, TOE + 20, BOX_W - T, SIDE_ROW_L - 2 * T, PLY, C_PLY,
            note="on 20 mm cleats; 2x 30 mm vent holes")
        box(g, "Top", x, y, BOX_H - T, BOX_W, SIDE_ROW_L, T, note="HPL both faces, edge-band 4 sides")
        # drawer: front flush with the bed side, finger gap under the top, box SIDE_DRAWER_D deep
        in_l = SIDE_ROW_L - 2 * T
        clr = 12.5
        bw, bh = in_l - 2 * clr, dh - 40
        parts = [side_front(g, "Drawer_Front", xs(0, T), y + T + GAP / 2, zd, in_l - GAP, dh - SHADOW_GAP,
                            T if out < 0 else 0)]
        y_in = y + T + clr
        parts += [box(g, "Drawer_Side_Head", xs(T, SIDE_DRAWER_D), y_in, zd + 15, SIDE_DRAWER_D, PLY, bh, C_DRAWER),
                  box(g, "Drawer_Side_Foot", xs(T, SIDE_DRAWER_D), y_in + bw - PLY, zd + 15, SIDE_DRAWER_D, PLY,
                      bh, C_DRAWER),
                  box(g, "Drawer_Back", xs(T + SIDE_DRAWER_D - PLY, PLY), y_in + PLY, zd + 15, PLY, bw - 2 * PLY,
                      bh, C_DRAWER),
                  box(g, "Drawer_Bottom", xs(T, SIDE_DRAWER_D - PLY), y_in + PLY, zd + 15, SIDE_DRAWER_D - PLY,
                      bw - 2 * PLY, PLY, C_DRAWER)]
        pulled_x.append((parts, out))
    # --- foot row: drawer slides forward, towards the cabinet ---
    y = Y1 - DRAWER_ROW_L
    g = group(f"Foot_Box_{side}", gP)
    box_walls(g, x, y, BOX_W, DRAWER_ROW_L, front=False)
    box(g, "Top", x, y, BOX_H - T, BOX_W, DRAWER_ROW_L, T, note="HPL both faces, edge-band 4 sides")
    in_w = BOX_W - 2 * T
    pulled_y += drawer(g, "Drawer", x + T, in_w, zd, dh,
                       front=(x + T + GAP / 2, zd, in_w - GAP, dh - SHADOW_GAP), front_y=Y1, bd=DRAWER_BOX_D)

# ================= scribe strip at the ceiling =================
gS = group("Scribe_Strips", root)
box(gS, "Scribe_Ceiling", FIT, Y_WALL + UPPER_D, UNIT_H, WALL_W - 2 * FIT, T, FIT_H, note="cut to fit on site")

# ================= mattress + room reference (not in cut list) =================
gRef = group("Reference_Room", root)
if not LIDS_OPEN_DEG:
    box(gRef, "Mattress_5x6", X0 + T + CLR, Y0 + T + CLR, BOX_H, MAT_W, MAT_L, MAT_H, C_MATTRESS, cut=False)
grey = (0.9, 0.9, 0.9)
box(gRef, "Wall_Opposite", -200, Y_WALL - 10, -10, WALL_W + 400, 10, WALL_H + 10, grey, cut=False)
box(gRef, "Wall_Cabinet", -200, CAB_DEPTH, -10, WALL_W + 400, 10, WALL_H + 10, grey, cut=False)
box(gRef, "Wall_Left", -100, Y_WALL - 10, -10, 100, ROOM_L + 20, WALL_H + 10, grey, cut=False)
box(gRef, "Wall_Right", WALL_W, Y_WALL - 10, -10, 100, ROOM_L + 20, WALL_H + 10, grey, cut=False)
box(gRef, "Floor", -200, Y_WALL - 10, -10, WALL_W + 400, ROOM_L + 20, 10, (0.6, 0.5, 0.4), cut=False)
box(gRef, "Cabinet_v3_Envelope", 0, 0, 0, WALL_W, CAB_DEPTH, WALL_H, C_CAB, cut=False)

for lid, y in lids:
    if LIDS_OPEN_DEG:                   # swing each lid up about its head-edge hinge
        hinge = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(1, 0, 0), LIDS_OPEN_DEG),
                              App.Vector(0, y, BOX_H))
        lid.Placement = hinge.multiply(lid.Placement)
if DRAWERS_OPEN:
    for o in pulled_y:
        o.Placement.Base.y += DRAWER_BOX_D
    for parts, out in pulled_x:
        for o in parts:
            o.Placement.Base.x += out * SIDE_TRAVEL

doc.recompute()

# ---------------- colours (GUI only) ----------------
if App.GuiUp:
    import FreeCADGui as Gui
    for name, c in _colours.items():
        doc.getObject(name).ViewObject.ShapeColor = c
    for w in ("Wall_Opposite", "Wall_Cabinet", "Wall_Left", "Wall_Right", "Cabinet_v3_Envelope"):
        doc.getObject(w).ViewObject.Transparency = 70
    Gui.activeDocument().activeView().viewIsometric()
    Gui.activeDocument().activeView().fitAll()

# ---------------- save + cut list + hardware ----------------
doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))

agg = {}
for mod, part, l, w, t, note in cut_list:
    mod = re.sub(r"_(Left|Right)$", "", mod)                  # both towers are identical
    mod = re.sub(r"_(\d?)[LR]$", r"\1", mod)                 # left/right storage boxes are identical
    part = re.sub(r"(Drawer|Door)_\d+", r"\1", part)
    key = (mod, part, l, w, t, note)
    agg[key] = agg.get(key, 0) + 1
with open(os.path.join(OUT_DIR, CUT_LIST), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Part", "Qty", "Length_mm", "Width_mm", "Thickness_mm", "Edge_Work"])
    for (mod, part, l, w, t, note), q in sorted(agg.items()):
        wr.writerow([mod, part, q, l, w, t, note])

hardware = [
    ("Lid stay / gas lift support, pair", N_COLS, "head-row lift-up boxes (behind the nightstands)"),
    ("Piano hinge or 2x heavy butt hinges per lid", N_COLS, "head-row lid, head edge"),
    (f"Heavy-duty full-extension drawer runners {DRAWER_BOX_D} mm, pair, soft-close", N_COLS, "bed foot drawers"),
    (f"3/4-extension drawer runners {SIDE_DRAWER_D} mm (~{SIDE_TRAVEL} mm travel), pair, soft-close",
     N_COLS * N_SIDE_ROWS, "bed side drawers - must not open further than the gap to the wall"),
    ("Soft-close drawer runners 350 mm, pair", 4, "nightstand drawers"),
    ("Cabinet connector bolts (joining screws)", 4 * (2 + N_SIDE_ROWS) * N_COLS, "join the storage boxes into one platform"),
    ("Non-slip mattress mat", 1, "stops the mattress sliding on the laminated tops"),
    ("Concealed hinges 110 deg, soft-close", 2 * 3 + N_BRIDGE_DOORS * 2, "tower doors x3 each, bridge doors x2 each"),
    ("LED strip 12 V warm white 3000 K + aluminium profile", 2, f"under each lit-niche shelf, {TOWER_W - 2 * T - 20:.0f} mm"),
    ("LED puck downlight 12 V warm white, surface/recessed", 2, "underside of the bridge, aimed at the headboard"),
    ("12 V LED driver 30 W + dimmer / touch switch", 1, "hidden in the bridge; switches in each niche"),
    ("Double power socket", 2, "inside each open niche (phone charging)"),
    ("Upholstery foam 38 mm HD + fabric + covered buttons", 1,
     f"panel {BRIDGE_W - 2 * GAP:.0f} x {up_h:.0f} mm, buttons on a {TUFT} mm diamond grid"),
    ("Felt pads 3 mm", 16, "plinths"),
    ("Wall fixings / anti-tip brackets", 6, "towers x2 each, bridge x2"),
]
with open(os.path.join(OUT_DIR, HARDWARE), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Item", "Qty", "Note"])
    wr.writerows(hardware)

# ---------------- cut list as FreeCAD spreadsheets inside the model ----------------
import importlib
import sys
sys.path.insert(0, OUT_DIR)
import bedroom_spreadsheets
importlib.reload(bedroom_spreadsheets)
bedroom_spreadsheets.add(doc, os.path.join(OUT_DIR, CUT_LIST), os.path.join(OUT_DIR, HARDWARE), "Cut list - bed wall unit v3 (storage bed + side cabinets, Filipino heights)")
doc.save()

area = sum(l * w for _, _, l, w, _, _ in cut_list) / 1e6
inner_h = BOX_H - T - TOE - 20 - PLY
SIDE_GAP_REAL = X0
storage = N_COLS * inner_h * ((BOX_W - 2 * T) * (HEAD_ROW_L - 2 * T + DRAWER_BOX_D)
                              + N_SIDE_ROWS * SIDE_DRAWER_D * (SIDE_ROW_L - 2 * T - 25)) / 1e9
print(f"Towers {TOWER_W:.0f} mm wide; nightstand {NIGHT_D} deep x {NIGHT_H} high, upper {UPPER_D} deep")
print(f"Bridge {BRIDGE_W:.0f} x {BRIDGE_H} mm at {BRIDGE_Z:.0f} mm from the floor")
print(f"Bed platform {FRAME_W:.0f} x {FRAME_L:.0f} mm, mattress top at {BOX_H + MAT_H:.0f} mm")
print(f"Storage: {N_COLS} head lift-up {BOX_W:.0f} x {HEAD_ROW_L:.0f}, {N_COLS * N_SIDE_ROWS} side drawers "
      f"(rows {SIDE_ROW_L:.0f} long), {N_COLS} foot drawers {BOX_W:.0f} x {DRAWER_ROW_L}; {storage:.2f} m3")
print(f"Side drawers open {SIDE_TRAVEL} mm into a {SIDE_GAP_REAL:.0f} mm gap to the wall; "
      f"foot drawers open {DRAWER_BOX_D} mm")
print(f"Walkway between foot of bed and cabinet doors: {0 - Y1:.0f} mm")
print(f"Panels: {len(cut_list)}, total ply area {area:.2f} m2 "
      f"(~{area / (1.22 * 2.44) * 1.25:.1f} sheets 4x8 incl. 25% waste)")
