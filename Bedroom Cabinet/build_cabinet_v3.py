# Version 3: modern handleless bedroom cabinet + TV niche + makeup table, IKEA PAX-style modular design.
# All panels 3/4" marine plywood (18 mm) laminated both faces. Units: mm.
# Runs wall-to-wall: no filler strips, carcasses flush to the left and right walls.
#
# Handleless: every door / drawer front has a 45 deg bevel cut on the BACK of its pull edge.
# Fingers reach behind that edge, so each bevel faces open space or a reveal gap:
#   - tall doors hinge on the wall side; the bevelled edge faces the open centre (mirror / TV area)
#   - top-box doors: bevel on the bottom edge; side top boxes get a SHADOW_GAP groove below them
#   - drawer-tower fronts: bevel on the top edge with a SHADOW_GAP above each front
#   - makeup-table drawer: bevel on the bottom edge, pulled from the knee space
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet/build_cabinet_v3.py").read())
# Change the parameters below and re-run to regenerate the model + cut list.
#
# Axes: X = width (left->right, facing the wall), Y = depth (0 = door face, +Y = towards wall), Z = up.

import csv
import re
import os
import FreeCAD as App
import Part

# ---------------- parameters ----------------
WALL_W = 2080          # wall width
WALL_H = 2380          # wall height (floor to ceiling)
FIT_W = 10             # install allowance: cabinet narrower than the wall, closed by a scribe strip at the right wall
FIT_H = 10             # install allowance: cabinet lower than the ceiling, closed by a scribe strip at the top
CAB_W = WALL_W - FIT_W
CAB_H = WALL_H - FIT_H
DEPTH = 470            # total depth incl. doors
PLY = 18               # 3/4" marine plywood core
LAM = 0.8              # laminate (HPL) per face
T = PLY + 2 * LAM      # finished panel thickness (19.6)
GAP = 3                # gap around doors / drawer fronts

BEVEL = 15             # 45 deg finger-pull bevel (leaves a ~4.6 mm front lip)
SHADOW_GAP = 25        # finger groove above drawer fronts / below side top-box doors
WALL_REVEAL = 10       # door edge kept off the side wall; leaves ~8 mm overlay = half-overlay hinge

PLINTH_H = 80          # toe-kick base under wardrobes
PLINTH_SETBACK = 50    # toe-kick recess from the door face
TOP_BOX_H = 300        # top cabinets (IKEA-style top boxes)

LEFT_W = 520           # hanging wardrobe
CENTRE_W = 1300        # TV niche (top) + makeup table (bottom)
RIGHT_W = CAB_W - LEFT_W - CENTRE_W    # 250 narrow shelf tower

TV_W, TV_H, TV_D = 1230, 700, 40       # flat screen
TV_GAP_WALL = 20                       # bracket gap between TV and back panel
NICHE_Z0 = 1300        # top surface of the TV ledge (bottom of TV niche)
TV_Z0 = NICHE_Z0 + 40  # bottom edge of the TV

DESK_Z = 750           # makeup table top height (top surface)
VANITY_W = 800         # knee space of the makeup table (left part of centre)
TOWER_W = CENTRE_W - VANITY_W          # 500 drawer tower under the right of the table
VANITY_DRAWER_H = 120  # drawer under the table top
MIRROR_Z0, MIRROR_Z1 = 850, 1250

CARCASS_D = DEPTH - T                    # carcass depth behind the doors (450.4)
TALL_H = CAB_H - PLINTH_H - TOP_BOX_H    # tall carcass height (1990)
TALL_Z = PLINTH_H
TOP_Z = TALL_Z + TALL_H

DOC_NAME = "Bedroom_Cabinet_Modern_v3"
CUT_LIST = "cut_list_v3.csv"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet"

# ---------------- colours ----------------
C_CARCASS = (0.93, 0.89, 0.80)   # birch-ply look
C_DOOR = (0.97, 0.97, 0.95)      # white doors
C_DRAWER = (0.85, 0.78, 0.65)
C_METAL = (0.55, 0.55, 0.58)
C_MIRROR = (0.75, 0.88, 0.95)
C_PLINTH = (0.35, 0.33, 0.30)
C_TV = (0.08, 0.08, 0.09)

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
    """Box with a 45 deg chamfer on the back (+Y) edge named by `edge` (front panels only, dy = T)."""
    shape = Part.makeBox(dx, dy, dz)
    target = {"L": (0, dy, None), "R": (dx, dy, None), "B": (None, dy, 0), "T": (None, dy, dz)}[edge]
    for e in shape.Edges:
        c = e.CenterOfMass
        if all(v is None or abs(getattr(c, a) - v) < 1e-6 for a, v in zip("xyz", target)) \
                and abs(e.Length - (dz if edge in "LR" else dx)) < 1e-6:
            return shape.makeChamfer(BEVEL, [e])
    raise ValueError("bevel edge not found")


def box(grp, name, x, y, z, dx, dy, dz, colour=C_CARCASS, cut=True, bevel=None):
    """Axis-aligned panel, optionally with a finger-pull bevel. Recorded in the cut list."""
    if bevel:
        o = doc.addObject("Part::Feature", name)
        o.Shape = _bevelled(dx, dy, dz, bevel)
    else:
        o = doc.addObject("Part::Box", name)
        o.Length, o.Width, o.Height = dx, dy, dz
    o.Placement.Base = App.Vector(x, y, z)
    grp.addObject(o)
    _colours[o.Name] = colour
    if cut:
        dims = sorted([dx, dy, dz], reverse=True)
        note = f"45deg bevel {BEVEL_NAMES[bevel]} edge (back)" if bevel else ""
        cut_list.append((grp.Label, name, round(dims[0], 1), round(dims[1], 1), round(dims[2], 1), note))
    return o


def rail(grp, name, x0, x1, y, z):
    o = doc.addObject("Part::Cylinder", name)
    o.Radius, o.Height = 12.5, x1 - x0
    o.Placement = App.Placement(App.Vector(x0, y, z), App.Rotation(App.Vector(0, 1, 0), 90))
    grp.addObject(o)
    _colours[o.Name] = C_METAL
    return o


def carcass(grp, x, z, w, h, d=CARCASS_D, prefix="", back=True):
    """IKEA-style box: sides full height, top/bottom between sides, 18 mm back at the rear."""
    y0 = DEPTH - d                 # front edge of carcass
    inner_d = d - T                # depth in front of the back panel
    box(grp, prefix + "Side_L", x, y0, z, T, inner_d, h)
    box(grp, prefix + "Side_R", x + w - T, y0, z, T, inner_d, h)
    box(grp, prefix + "Bottom", x + T, y0, z, w - 2 * T, inner_d, T)
    box(grp, prefix + "Top", x + T, y0, z + h - T, w - 2 * T, inner_d, T)
    if back:
        box(grp, prefix + "Back", x, DEPTH - T, z, w, T, h)
    return y0


def shelf(grp, name, x, z, w, setback=20):
    y0 = DEPTH - CARCASS_D + setback
    box(grp, name, x + T, y0, z, w - 2 * T, CARCASS_D - T - setback, T)


def door(grp, name, x, z, w, h, bevel, trim_l=0, trim_r=0, trim_top=0):
    """Overlay door with GAP all round; trim_* shortens it for wall reveals / shadow gaps."""
    x0, z0 = x + GAP / 2 + trim_l, z + GAP / 2
    box(grp, name, x0, 0, z0, w - GAP - trim_l - trim_r, T, h - GAP - trim_top, C_DOOR, bevel=bevel)


def drawer(grp, name, x_in, w_in, z, h, front_y, front=None, bevel=None):
    """Drawer box (12.5 mm runner clearance each side) with its own front.
    front=(x, z, w, h) overrides the front panel for overlay fronts in the door plane."""
    clr = 12.5
    bw = w_in - 2 * clr
    bd = 400
    y0 = front_y + T
    fx, fz, fw, fh = front or (x_in + 2, z, w_in - 4, h)
    box(grp, name + "_Front", fx, front_y, fz, fw, T, fh, C_DOOR if front else C_DRAWER, bevel=bevel)
    box(grp, name + "_Side_L", x_in + clr, y0, z + 10, T, bd - T, h - 30, C_DRAWER)
    box(grp, name + "_Side_R", x_in + clr + bw - T, y0, z + 10, T, bd - T, h - 30, C_DRAWER)
    box(grp, name + "_Back", x_in + clr + T, y0 + bd - 2 * T, z + 10, bw - 2 * T, T, h - 30, C_DRAWER)
    box(grp, name + "_Bottom", x_in + clr + T, y0, z + 10, bw - 2 * T, bd - 2 * T, T, C_DRAWER)


def plinth(grp, x, w):
    box(grp, "Plinth_Front", x, PLINTH_SETBACK, 0, w, T, PLINTH_H, C_PLINTH)
    box(grp, "Plinth_Back", x, DEPTH - 2 * T - 60, 0, w, T, PLINTH_H, C_PLINTH)


xC = LEFT_W                 # centre section start
xR = LEFT_W + CENTRE_W      # right tower start
xTower = xC + VANITY_W      # drawer tower start

root = group("Bedroom_Cabinet_v3")

# ================= LEFT WARDROBE (hanging) =================
# Hinged on the wall side (door kept WALL_REVEAL off the wall); bevel on the right edge,
# pulled from the open mirror / TV area next to it.
gL = group("Wardrobe_Left_Hanging", root)
plinth(gL, 0, LEFT_W)
y0 = carcass(gL, 0, TALL_Z, LEFT_W, TALL_H)
in_top = TALL_Z + TALL_H - T
shelf(gL, "Shelf_Top", 0, in_top - 250, LEFT_W)                       # hat shelf
rail(gL, "Hanging_Rail", T, LEFT_W - T, y0 + (CARCASS_D - T) / 2, in_top - 250 - 50)
dz = TALL_Z + T
for i, h in enumerate([160, 160]):
    drawer(gL, f"Drawer_{i + 1}", T, LEFT_W - 2 * T, dz, h, y0 + 30, bevel="T")
    dz += h + 10
shelf(gL, "Shelf_Above_Drawers", 0, dz + 10, LEFT_W)
door(gL, "Door", 0, TALL_Z, LEFT_W, TALL_H, bevel="R", trim_l=WALL_REVEAL, trim_top=SHADOW_GAP)

# ================= RIGHT NARROW TOWER (shelves) =================
gR = group("Tower_Right_Shelves", root)
plinth(gR, xR, RIGHT_W)
carcass(gR, xR, TALL_Z, RIGHT_W, TALL_H)
z = TALL_Z + T + 280
i = 1
while z < TALL_Z + TALL_H - 200:
    shelf(gR, f"Shelf_{i}", xR, z, RIGHT_W)
    z += 300
    i += 1
door(gR, "Door", xR, TALL_Z, RIGHT_W, TALL_H, bevel="L", trim_r=WALL_REVEAL, trim_top=SHADOW_GAP)

# ================= CENTRE: TV NICHE + MAKEUP TABLE =================
gC = group("Centre_TV_Makeup", root)
# back panel between the side units, floor to the top boxes (TV bracket bolts THROUGH it into the wall).
# Two pieces: 1300 is wider than a 1220 mm sheet; the seam sits behind the TV.
for i, side in enumerate("LR"):
    box(gC, f"Back_Panel_{side}", xC + i * CENTRE_W / 2, DEPTH - T, 0, CENTRE_W / 2, T, TOP_Z)
# TV ledge = floor of the TV niche, spans side unit to side unit
box(gC, "TV_Ledge", xC, 0, NICHE_Z0 - T, CENTRE_W, DEPTH - T, T)
box(gC, "TV_123x70", xC + (CENTRE_W - TV_W) / 2, DEPTH - T - TV_GAP_WALL - TV_D, TV_Z0,
    TV_W, TV_D, TV_H, C_TV, cut=False)
# table top across the full centre width
box(gC, "Table_Top", xC, 0, DESK_Z - T, CENTRE_W, DEPTH - T, T)

# makeup knee space: drawer under the table, pulled from below (bevel on bottom edge)
drawer(gC, "Table_Drawer", xC, VANITY_W, DESK_Z - T - VANITY_DRAWER_H - 2, VANITY_DRAWER_H, 0, bevel="B")
box(gC, "Mirror_4mm", xC + 60, DEPTH - T - 4, MIRROR_Z0, VANITY_W - 120, 4, MIRROR_Z1 - MIRROR_Z0,
    C_MIRROR, cut=False)

# drawer tower under the right part of the table (no back: centre back panel closes it)
gD = group("Drawer_Tower", gC)
plinth(gD, xTower, TOWER_W)
tower_h = DESK_Z - T - TALL_Z
y0 = carcass(gD, xTower, TALL_Z, TOWER_W, tower_h, back=False)
slot = (tower_h - 2 * T) / 3
pitch = tower_h / 3
for i in range(3):
    fz = TALL_Z + i * pitch + GAP / 2
    drawer(gD, f"Drawer_{i + 1}", xTower + T, TOWER_W - 2 * T, TALL_Z + T + i * slot, slot, 0,
           front=(xTower + GAP / 2, fz, TOWER_W - GAP, pitch - GAP - SHADOW_GAP), bevel="T")

# open makeup shelves above the tower, beside the mirror
box(gC, "Divider", xTower, 0, DESK_Z, T, DEPTH - T, NICHE_Z0 - T - DESK_Z)
for i, z in enumerate([DESK_Z + 180, DESK_Z + 360]):
    box(gC, f"Makeup_Shelf_{i + 1}", xTower + T, DEPTH - T - 300, z, TOWER_W - T, 300, T)

# ================= TOP BOXES (full width, to the ceiling) =================
# Bevel on the bottom edge. Centre doors are pulled from the TV niche below; the side
# ones from the SHADOW_GAP groove left above the tall doors.
gT = group("Top_Boxes", root)
for name, x, w, ndoors, tl, tr in [("Left", 0, LEFT_W, 1, WALL_REVEAL, 0),
                                   ("Centre", xC, CENTRE_W, 2, 0, 0),
                                   ("Right", xR, RIGHT_W, 1, 0, WALL_REVEAL)]:
    g = group(f"Top_Box_{name}", gT)
    carcass(g, x, TOP_Z, w, TOP_BOX_H)
    dw = w / ndoors
    for i in range(ndoors):
        door(g, f"Door_{i + 1}", x + i * dw, TOP_Z, dw, TOP_BOX_H, bevel="B",
             trim_l=tl if i == 0 else 0, trim_r=tr if i == ndoors - 1 else 0)

# ================= scribe strips: cut to fit on site, close the install allowance =================
gS = group("Scribe_Strips", root)
if FIT_W:
    box(gS, "Scribe_Right_Wall", CAB_W, 0, 0, FIT_W, T, WALL_H, C_DOOR)
if FIT_H:
    box(gS, "Scribe_Ceiling", 0, 0, CAB_H, CAB_W, T, FIT_H, C_DOOR)

# ================= reference wall + floor (not part of cut list) =================
gRef = group("Reference_Room", root)
box(gRef, "Wall", -200, DEPTH, -10, WALL_W + 400, 10, WALL_H + 10, (0.9, 0.9, 0.9), cut=False)
box(gRef, "Wall_Left", -100, -600, -10, 100, 600 + DEPTH, WALL_H + 10, (0.9, 0.9, 0.9), cut=False)
box(gRef, "Wall_Right", WALL_W, -600, -10, 100, 600 + DEPTH, WALL_H + 10, (0.9, 0.9, 0.9), cut=False)
box(gRef, "Floor", -200, -1200, -10, WALL_W + 400, 1200 + DEPTH, 10, (0.6, 0.5, 0.4), cut=False)

doc.recompute()

# ---------------- colours (GUI only) ----------------
if App.GuiUp:
    import FreeCADGui as Gui
    for name, c in _colours.items():
        vo = doc.getObject(name).ViewObject
        vo.ShapeColor = c
    for w in ("Wall", "Wall_Left", "Wall_Right"):
        doc.getObject(w).ViewObject.Transparency = 60
    Gui.activeDocument().activeView().viewIsometric()
    Gui.activeDocument().activeView().fitAll()

# ---------------- save + cut list ----------------
doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))

agg = {}
for mod, part, l, w, t, note in cut_list:
    key = (mod, re.sub(r"Drawer_\d+_", "Drawer_", part), l, w, t, note)
    agg[key] = agg.get(key, 0) + 1
with open(os.path.join(OUT_DIR, CUT_LIST), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Part", "Qty", "Length_mm", "Width_mm", "Thickness_mm", "Edge_Work"])
    for (mod, part, l, w, t, note), q in sorted(agg.items()):
        wr.writerow([mod, part, q, l, w, t, note])

area = sum(l * w for _, _, l, w, _, _ in cut_list) / 1e6
print(f"Panels: {len(cut_list)}, total ply area {area:.2f} m2 "
      f"(~{area / (1.22 * 2.44) * 1.25:.1f} sheets 4x8 incl. 25% waste)")
