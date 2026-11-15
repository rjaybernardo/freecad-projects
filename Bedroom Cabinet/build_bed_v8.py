# Closed channel ends: use the existing unnotched side panels, no extra cover plywood.
# L/C channels are restricted to drawer units; door-only cabinets stay plain.
# Bed wall unit v8: square-edged fronts with built-up laminated-plywood L/C pull channels.
# L: 42 mm overall depth x 60 mm overall height, based on the user's reference.
# C: 42 mm depth x 80 mm height (40.8 mm clear between 19.6 mm returns).
# Existing dividers retained. All plywood uses the two-face laminated stock. Floor-running under-bed wheels added; actual hardware height is provisional.
# Run in FreeCAD: exec(open("/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet/build_bed_v8.py").read())
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
SHADOW_GAP = 25        # visible finger opening above drawer fronts
TOE = 3                # felt pads

# storage bed (modular boxes)
BOX_H = 300            # box height floor -> top of the lids (mattress lies on it; v2: 400)
N_COLS = 2             # boxes across the bed
DRAWER_ROW_L = 500     # foot-row box length (drawer depth + front)
DRAWER_BOX_D = 450     # floor-running drawer depth; no under-bed slide hardware
N_SIDE_ROWS = 2        # rows of side drawers between the head row and the foot row
SIDE_DRAWER_D = 450    # floor-running side drawer depth
FOOT_TRAVEL = 450
WHEEL_DIAMETER = 25.4
WHEEL_MOUNT_H = 35.0    # PROVISIONAL total caster height, not wheel diameter; replace with actual hardware measurement
SIDE_TRAVEL = 337      # how far the side drawers open (must stay inside the gap to the wall)
HEAD_CLR = 10          # side drawers start this far past the nightstand front
LIDS_OPEN_DEG = 0      # e.g. 60 to show the head-row lids open (mattress hidden)
DRAWERS_OPEN = 0       # e.g. 1 to show all drawers pulled fully out

# Optional plain backboard: one plywood layer; no foam or second plywood substrate.
INCLUDE_BACKBOARD = True
BACKBOARD_H = 1200
BACKBOARD_Z0 = BOX_H + MAT_H - 10
HEADBOARD_STANDOFF = 50  # retain the approved bed location and room clearances
BATTEN_DEPTH = HEADBOARD_STANDOFF
BATTEN_H = 40

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
Y0 = Y_WALL + T + HEADBOARD_STANDOFF  # unchanged bed location; board front flush with bed head
Y1 = Y0 + FRAME_L
HEAD_ROW_L = Y_WALL + NIGHT_D + HEAD_CLR - Y0                # bed length hidden behind the nightstands
SIDE_ROW_L = (FRAME_L - HEAD_ROW_L - DRAWER_ROW_L) / N_SIDE_ROWS

DOC_NAME = "Bed_Wall_Unit_v8"
CUT_LIST = "cut_list_bed_v8.csv"
HARDWARE = "hardware_bed_v8.csv"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet"
import sys
sys.path.insert(0, OUT_DIR)

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


def group(name, parent=None):
    g = doc.addObject("App::DocumentObjectGroup", name)
    if parent:
        parent.addObject(g)
    return g


def box(grp, name, x, y, z, dx, dy, dz, colour=C_FRAME, cut=True, note="", pull_edge=None):
    """Square-edged panel; record blank size and a fabrication row for recess routing."""
    o = doc.addObject("Part::Box", name)
    o.Length, o.Width, o.Height = dx, dy, dz
    o.Placement.Base = App.Vector(x, y, z)
    grp.addObject(o)
    _colours[o.Name] = colour
    if pull_edge:
        note = "; ".join(filter(None, [note, "Square pull edge; edge-band exposed edges"]))
    if cut:
        dims = [dx, dy, dz]
        axis = next((i for i, d in enumerate(dims) if abs(d - T) < 1e-6), None)
        if axis is not None:
            thickness = dims.pop(axis)
            length, width = sorted(dims, reverse=True)
        else:
            length, width, thickness = sorted(dims, reverse=True)
        o.addProperty("App::PropertyInteger", "CutListRow", "Fabrication")
        o.CutListRow = len(cut_list)
        cut_list.append((grp.Label, name, round(length, 1), round(width, 1), round(thickness, 1), note))
    return o


def carcass(grp, x, z, w, h, d, prefix=""):
    """Box against the wall facing +Y: sides full height, top/bottom between, 18 mm back at the wall."""
    yb = Y_WALL + T
    box(grp, prefix + "Back", x, Y_WALL, z, w, T, h, C_PLY)
    box(grp, prefix + "Side_L", x, yb, z, T, d - T, h, C_FRAME, note="HPL both faces")
    box(grp, prefix + "Side_R", x + w - T, yb, z, T, d - T, h, C_FRAME, note="HPL both faces")
    box(grp, prefix + "Bottom", x + T, yb, z, w - 2 * T,
        d - T - (25 if grp.Name == "Bridge" else 0), T, C_CARCASS,
        note="HPL both faces; plain front setback 25 mm for square door grip" if grp.Name == "Bridge" else "HPL both faces")
    box(grp, prefix + "Top", x + T, yb, z + h - T, w - 2 * T, d - T, T, C_CARCASS, note="HPL both faces")


def shelf(grp, name, x, z, w, d, note="HPL both faces, edge-band front"):
    box(grp, name, x + T, Y_WALL + T, z, w - 2 * T, d - T - (25 if name == "Shelf_Lit_Niche" else 10), T, C_CARCASS, note=note)


def door(grp, name, x, z, w, h, d, pull_edge):
    """Overlay door on the front of a carcass of depth d."""
    box(grp, name, x + GAP / 2, Y_WALL + d, z + GAP / 2, w - GAP, T, h - GAP, pull_edge=pull_edge, note="HPL both faces")


def drawer(grp, name, x_in, w_in, z, h, front, front_y, bd=350):
    """Drawer box (12.5 mm runner clearance) behind an inset front=(x, z, w, h) flush with the carcass front.
    Returns its parts so they can be shown pulled out."""
    clr = 12.5
    bw = w_in - 2 * clr
    ceiling = z + 15 + h - 40
    if grp.Name.startswith("Nightstand"):
        ceiling = NIGHT_H - T - 60 - 2 if name.endswith("2") else (NIGHT_PLINTH + T + (NIGHT_H - NIGHT_PLINTH - 2 * T) / 2 - SHADOW_GAP / 2) - 40 - 2
    elif grp.Name.startswith("Foot_Box"):
        ceiling = BOX_H - T - 60 - 2
    body_z = z + 15
    if grp.Name.startswith("Nightstand") and name.endswith("2"):
        seam = NIGHT_PLINTH + T + (NIGHT_H - NIGHT_PLINTH - 2 * T) / 2 - SHADOW_GAP / 2
        body_z = max(body_z, seam + 40 + 2)
    bh = ceiling - body_z
    assert bh > T + 20
    fx, fz, fw, fh = front
    by = front_y - T - bd
    return [box(grp, name + "_Front", fx, front_y - T, fz, fw, T, fh, pull_edge="T", note="HPL both faces"),
            box(grp, name + "_Side_L", x_in + clr, by, body_z, T, bd, bh, C_DRAWER),
            box(grp, name + "_Side_R", x_in + clr + bw - T, by, body_z, T, bd, bh, C_DRAWER),
            box(grp, name + "_Back", x_in + clr + T, by, body_z, bw - 2 * T, T, bh, C_DRAWER),
            box(grp, name + "_Bottom", x_in + clr + T, by + T, body_z, bw - 2 * T, bd - T, T, C_DRAWER)]


def led(grp, name, x, y, z, dx, dy, dz=8):
    box(grp, name, x, y, z, dx, dy, dz, C_LED, cut=False)


root = group("Bed_Wall_Unit_v8")
root.addProperty("App::PropertyString", "HardwareAssumptions", "Review")
root.HardwareAssumptions = "1-inch fixed wheels; total mounting height assumed 35 mm. Measure actual hardware before cutting drawer parts."

# ================= SIDE TOWERS =================
for side, x in (("Left", FIT), ("Right", WALL_W - FIT - TOWER_W)):
    g = group(f"Tower_{side}", root)
    # --- nightstand: recessed plinth + 2 handleless drawers ---
    gn = group(f"Nightstand_{side}", g)
    pw, pd, ph = TOWER_W - 40, NIGHT_D - 50, NIGHT_PLINTH - TOE
    for suffix, px in [("L", x + 20), ("R", x + 20 + pw - T)]:
        box(gn, "Plinth_Side_" + suffix, px, Y_WALL, TOE, T, pd, ph, C_PLINTH, note="HPL both faces; plinth ring member")
    for suffix, py in [("Rear", Y_WALL), ("Front", Y_WALL + pd - T)]:
        box(gn, "Plinth_" + suffix, x + 20 + T, py, TOE, pw - 2*T, T, ph, C_PLINTH, note="HPL both faces; plinth ring member")
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
    for i, z in enumerate((z_lit + (UNIT_H - T - z_lit) / 2,)):
        shelf(gu, f"Shelf_Behind_Door_{i + 1}", x, z, TOWER_W, UPPER_D)
    door(gu, "Door", x, z_lit, TOWER_W, UNIT_H - z_lit, UPPER_D, pull_edge="B")

# ================= BRIDGE OVER THE BED =================
gB = group("Bridge", root)
carcass(gB, XT_IN, BRIDGE_Z, BRIDGE_W, BRIDGE_H, UPPER_D)
# Dividers follow the existing door seams, preserving the four cut door fronts.
# Full-height dividers fit between top and bottom; shelves terminate at them.
dw = BRIDGE_W / N_BRIDGE_DOORS
bridge_edges = [XT_IN + T]
for i in range(1, N_BRIDGE_DOORS):
    cx = XT_IN + i * dw
    box(gB, f"Bridge_Divider_{i}", cx - T / 2, Y_WALL + T, BRIDGE_Z + T,
        T, UPPER_D - T, BRIDGE_H - 2 * T, C_CARCASS,
        note="HPL both faces; edge-band front; full height between top and bottom")
    bridge_edges.extend([cx - T / 2, cx + T / 2])
bridge_edges.append(XT_IN + BRIDGE_W - T)
for i in range(N_BRIDGE_DOORS):
    left, right = bridge_edges[2 * i:2 * i + 2]
    box(gB, f"Bridge_Shelf_{i + 1}", left, Y_WALL + T, BRIDGE_Z + BRIDGE_H / 2,
        right - left, UPPER_D - T - 10, T, C_CARCASS,
        note="HPL both faces, edge-band front; fits between vertical dividers")
    door(gB, f"Door_{i + 1}", XT_IN + i * dw, BRIDGE_Z, dw, BRIDGE_H, UPPER_D, pull_edge="B")
    front = gB.Group[-1]
    front.addProperty("App::PropertyString", "HingeMount", "Assembly")
    front.HingeMount = ["Left outer side; full overlay",
                        "Centre divider, left face; half overlay",
                        "Centre divider, right face; half overlay",
                        "Right outer side; full overlay"][i]

# ================= OPTIONAL SINGLE-LAYER BACKBOARD =================
gH = group("Headboard", root)
root.addProperty("App::PropertyBool", "IncludeBackboard", "Headboard")
root.IncludeBackboard = INCLUDE_BACKBOARD
if INCLUDE_BACKBOARD:
    board_w = BRIDGE_W - 2*GAP
    face = box(gH, "Plain_Backboard", XT_IN + GAP, Y_WALL+BATTEN_DEPTH,
        BACKBOARD_Z0, board_w, T, BACKBOARD_H, C_FRAME,
        note="HPL both faces; ONE plywood panel, ONE layer; edge-band 4 sides; no upholstery")
    face.addProperty("App::PropertyString","PartID","Fabrication");face.PartID="B073"
    # Narrow solid-timber wall battens replace the redundant full-sheet plywood layer.
    # Their front faces support the backboard at the previous headboard-front datum.
    for i,z in enumerate([600,1100,1600],1):
        o=box(gH, "Timber_Backboard_Batten_"+str(i), XT_IN+GAP+40, Y_WALL, z,
              board_w-80, BATTEN_DEPTH, BATTEN_H, C_DRAWER, cut=False)
        o.addProperty("App::PropertyString", "Material", "Hardware")
        o.Material="Solid timber; NOT plywood; 3 support battens only"
        o.addProperty("App::PropertyString", "Fixing", "Hardware")
        o.Fixing="Fix to suitable wall anchors; backboard does not support bridge or towers"

# ================= STORAGE BED: floor-running drawers =================
gP = group("Storage_Bed", root)
hw = BOX_H - T - TOE
FRONT_Z = 41.0       # retain the approved visible fronts and finger gap
from bed_wheel_drawers import FloorDrawers
floor_drawers = FloorDrawers(doc, box, group, _colours, T, WHEEL_DIAMETER, WHEEL_MOUNT_H)
lids, pulled_y, pulled_x = [], [], []
for c in range(N_COLS):
    x = X0 + c*BOX_W
    side = "LR"[c]
    g = group("Head_Box_" + side, gP)
    box(g, "Side_L", x, Y0, TOE, T, HEAD_ROW_L, hw, note="HPL both faces")
    box(g, "Side_R", x+BOX_W-T, Y0, TOE, T, HEAD_ROW_L, hw, note="HPL both faces")
    box(g, "Head", x+T, Y0, TOE, BOX_W-2*T, T, hw, note="HPL both faces")
    box(g, "Foot", x+T, Y0+HEAD_ROW_L-T, TOE, BOX_W-2*T, T, hw, note="HPL both faces")
    box(g, "Bottom", x+T, Y0+T, TOE+20, BOX_W-2*T, HEAD_ROW_L-2*T, T, C_PLY, note="HPL both faces; lift-up bay bottom")
    lids.append((box(g, "Lid", x+GAP/2, Y0+GAP/2, BOX_H-T, BOX_W-GAP, HEAD_ROW_L-GAP, T,
                     note="HPL both faces, edge-band 4 sides; hinged at head"), Y0))
    left = c == 0
    outer = X0 if left else X0+FRAME_W
    def xs(a, dx):
        return outer+a if left else outer-a-dx
    for r in range(N_SIDE_ROWS):
        y = Y0+HEAD_ROW_L+r*SIDE_ROW_L
        g = group(f"Side_Box_{r+1}{side}", gP)
        box(g, "Head", x, y, TOE, BOX_W, T, hw, note="HPL both faces")
        box(g, "Foot", x, y+SIDE_ROW_L-T, TOE, BOX_W, T, hw, note="HPL both faces")
        box(g, "Inner_Side", xs(BOX_W-T,T), y+T, TOE, T, SIDE_ROW_L-2*T, hw, note="HPL both faces")
        # Rear brace ties the case together but stays behind the entire wheel path.
        rear_depth = BOX_W-T-(T+SIDE_DRAWER_D+30)
        box(g, "Rear_Base_Brace", xs(T+SIDE_DRAWER_D+30,rear_depth), y+T, TOE,
            rear_depth, SIDE_ROW_L-2*T, T, C_PLY, note="HPL both faces; keep wheel lane open to the room floor")
        box(g, "Top", x, y, BOX_H-T, BOX_W, SIDE_ROW_L, T, note="HPL both faces, edge-band 4 sides")
        floor_drawers.build(g, g.Name, (outer+T if left else outer-T,y+T,0),
            (1,0,0) if left else (-1,0,0), (0,1,0), SIDE_ROW_L-2*T,
            SIDE_DRAWER_D, SIDE_ROW_L-2*T-GAP, FRONT_Z, BOX_H-T-FRONT_Z-SHADOW_GAP,
            BOX_H-T-60-2, SIDE_TRAVEL, C_FRAME, C_DRAWER, C_METAL)
    y = Y1-DRAWER_ROW_L
    g = group("Foot_Box_" + side, gP)
    box(g, "Side_L", x, y, TOE, T, DRAWER_ROW_L, hw, note="HPL both faces")
    box(g, "Side_R", x+BOX_W-T, y, TOE, T, DRAWER_ROW_L, hw, note="HPL both faces")
    box(g, "Head", x+T, y, TOE, BOX_W-2*T, T, hw, note="HPL both faces")
    box(g, "Rear_Base_Brace", x+T, y+T, TOE, BOX_W-2*T, 50, T, C_PLY,
        note="HPL both faces; rear brace clear of closed-position rear wheels")
    box(g, "Top", x, y, BOX_H-T, BOX_W, DRAWER_ROW_L, T, note="HPL both faces, edge-band 4 sides")
    floor_drawers.build(g, g.Name, (x+T,Y1-T,0), (0,-1,0), (1,0,0), BOX_W-2*T,
        DRAWER_BOX_D, BOX_W-2*T-GAP, FRONT_Z, BOX_H-T-FRONT_Z-SHADOW_GAP,
        BOX_H-T-60-2, FOOT_TRAVEL, C_FRAME, C_DRAWER, C_METAL)

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
    for moving in floor_drawers.groups:
        for o in moving.Group:
            o.Placement.Base += moving.OpenDirection * moving.OpenTravel.Value
    for o in pulled_y:
        o.Placement.Base.y += DRAWER_BOX_D
    for parts, out in pulled_x:
        for o in parts:
            o.Placement.Base.x += out * SIDE_TRAVEL

# Built-up plywood L and C channels; no metal pull profiles are required.
import sys
sys.path.insert(0, OUT_DIR)
from plywood_pull_channels import PlywoodPullChannels
pulls = PlywoodPullChannels(doc, T, cut_list, _colours, C_FRAME, closed_ends=True)
for side in ("Left", "Right"):
    g = doc.getObject("Nightstand_" + side)
    fronts = [o for o in g.Group if "Drawer_" in o.Name and "_Front" in o.Name]
    fronts.sort(key=lambda o: o.Shape.BoundBox.ZMin)
    x = FIT if side == "Left" else WALL_W - FIT - TOWER_W
    inner_y = Y_WALL + NIGHT_D - T
    pulls.horizontal(g, "Nightstand_" + side + "_L", x, inner_y, NIGHT_H - T - 60, TOWER_W, facing=-1)
    seam = (fronts[0].Shape.BoundBox.ZMax + fronts[1].Shape.BoundBox.ZMin) / 2
    pulls.horizontal(g, "Nightstand_" + side + "_C", x, inner_y, seam - 40, TOWER_W, facing=-1, kind="C")
# One top L recess for each foot drawer. Side drawers use the same construction rotated 90 degrees.
for g in gP.Group:
    if g.Name.startswith("Foot_Box"):
        b = next(o for o in g.Group if o.Name.startswith("Top")).Shape.BoundBox
        pulls.horizontal(g, g.Name + "_L", b.XMin, Y1 - T, BOX_H - T - 60, BOX_W, facing=-1)
    elif g.Name.startswith("Side_Box"):
        # Build in an auxiliary coordinate frame, then rotate the channel parts and routing envelopes.
        # The rear and return strips themselves are created below in world coordinates.
        top = next(o for o in g.Group if o.Name.startswith("Top"))
        b = top.Shape.BoundBox
        left = g.Name.endswith("L")
        outer = X0 if left else X0 + FRAME_W
        y = b.YMin + T
        channel_length = SIDE_ROW_L - 2 * T
        x0 = outer + T if left else outer - T - 42
        route_x = outer if left else x0
        envelope = Part.makeBox(42 + T, channel_length, 60, App.Vector(route_x, y, BOX_H - T - 60))
        pulls._notch(g, envelope, g.Name + "_L")
        channel = group("Pull_" + g.Name + "_L", g)
        back_x = x0 + 42 - T if left else x0
        return_x = x0 if left else x0 + T
        pulls._part(channel, "Pull_" + g.Name + "_Back", (back_x, y, BOX_H - T - 60), (T, channel_length, 60))
        pulls._part(channel, "Pull_" + g.Name + "_Lower", (return_x, y, BOX_H - T - 60), (42 - T, channel_length, T))

from cabinet_lighting import add as add_lighting
lighting = add_lighting(doc, root, cut_list, _colours, 'bed', globals(), OUT_DIR)

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
    wr = csv.writer(f, lineterminator="\n")
    wr.writerow(["Module", "Part", "Qty", "Length_mm", "Width_mm", "Thickness_mm", "Edge_Work"])
    for (mod, part, l, w, t, note), q in sorted(agg.items()):
        wr.writerow([mod, part, q, l, w, t, note])

hardware = [
    ("Lid stay / gas lift support, pair", N_COLS, "head-row lift-up boxes (behind the nightstands)"),
    ("Piano hinge or 2x heavy butt hinges per lid", N_COLS, "head-row lid, head edge"),
    ("Fixed-direction caster / roller, 1 inch (25.4 mm) wheel", 24,
     "4 per under-bed drawer; provisional overall height 35 mm; verify purchased hardware and load rating"),
    ("Adjustable removable drawer retention strap", 6,
     "set side travel to 337 mm and foot travel to 450 mm; detach for drawer removal"),
    ("Caster plate fixing set", 24, "match actual caster mounting plate; do not use screws longer than the mounting pad permits"),
    ("Soft-close drawer runners 350 mm, pair", 4, "nightstand drawers"),
    ("Cabinet connector bolts (joining screws)", 4 * (2 + N_SIDE_ROWS) * N_COLS, "join the storage boxes into one platform"),
    ("Non-slip mattress mat", 1, "stops the mattress sliding on the laminated tops"),
    ("Full-overlay concealed hinges 110 deg, soft-close", 10,
     "tower doors x3 each; bridge outer doors 1 and 4 x2 each"),
    ("Half-overlay concealed hinges 110 deg, soft-close", 4,
     "bridge middle doors 2 and 3 x2 each, mounted on opposite faces of the centre divider"),
    ("LED strip, provisional 24 V / 10 W per metre", 1, "see bed_lighting.json for three parallel branches; cut only at marked strip pads"),
    ("Aluminium LED profile with diffuser, provisional 16 x 10 mm", 3, "cut lengths in bed_lighting.json; surface-mounted, not plywood grip rails"),
    ("Constant-voltage driver + fused DC distribution and dimmer", 1, "provisional 24 V / 30 W; verify actual strip load and driver datasheet; accessible upper-left cabinet"),
    ("Double power socket", 2, "inside each open niche (phone charging)"),
    *([("Solid-timber backboard support batten", 3,
        f"{BRIDGE_W-2*GAP-80:.1f} x {BATTEN_DEPTH} x {BATTEN_H} mm; not plywood; confirm wall anchors"),
       ("Backboard wall-anchor / panel-fixing set", 1,
        "3 battens with fixings selected for actual wall; backboard is independent of overhead cabinet support")]
      if INCLUDE_BACKBOARD else []),
    ("Felt pads 3 mm", 16, "plinths"),
    ("Wall fixings / anti-tip brackets", 6, "towers x2 each, bridge x2"),
]
with open(os.path.join(OUT_DIR, HARDWARE), "w", newline="") as f:
    wr = csv.writer(f, lineterminator="\n")
    wr.writerow(["Item", "Qty", "Note"])
    wr.writerows(hardware)

# ---------------- cut list as FreeCAD spreadsheets inside the model ----------------
import importlib
import sys
sys.path.insert(0, OUT_DIR)
import bedroom_spreadsheets
importlib.reload(bedroom_spreadsheets)
bedroom_spreadsheets.add(doc, os.path.join(OUT_DIR, CUT_LIST), os.path.join(OUT_DIR, HARDWARE), "Cut list - bed wall unit v8 (storage bed + side cabinets, Filipino heights)")
for obsolete in ['CutList', 'Materials']:
    if doc.getObject(obsolete): doc.removeObject(obsolete)
# Keep existing Bxxx labels on unchanged plywood parts.
baseline=App.openDocument(os.path.join(OUT_DIR,"Bed_Wall_Unit_v7.FCStd"))
ids={o.Name:o.PartID for o in baseline.Objects if "CutListRow" in o.PropertiesList and "PartID" in o.PropertiesList}
for o in doc.Objects:
    if "CutListRow" in o.PropertiesList and o.Name in ids:
        o.addProperty("App::PropertyString","PartID","Fabrication");o.PartID=ids[o.Name]
App.closeDocument(baseline.Name)
App.setActiveDocument(doc.Name)
from workshop_documents import add as add_workshop
workshop = add_workshop(doc, cut_list, 'bed', OUT_DIR)
from cabinet_modules import organize
organize(doc)
doc.save()

area = sum(l * w for _, _, l, w, _, _ in cut_list) / 1e6
inner_h = BOX_H - T - TOE - 20 - T
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
print(f"Panels: {len(cut_list)}, finished area {area:.2f} m2; actual nested sheets {workshop['sheet_count']}")
