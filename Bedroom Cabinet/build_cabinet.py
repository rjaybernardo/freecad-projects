# Bedroom cabinet + makeup vanity, IKEA PAX-style modular design.
# All panels 3/4" marine plywood (18 mm) laminated both faces. Units: mm.
# Runs wall-to-wall: no filler strips, left side panel flush to the left wall, right to the right wall.
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet/build_cabinet.py").read())
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
DEPTH = 470            # total depth incl. doors
PLY = 18               # 3/4" marine plywood core
LAM = 0.8              # laminate (HPL) per face
T = PLY + 2 * LAM      # finished panel thickness (19.6)
GAP = 3                # gap around doors / drawer fronts

PLINTH_H = 80          # toe-kick base under wardrobes
PLINTH_SETBACK = 50    # toe-kick recess from the door face
TOP_BOX_H = 400        # top cabinets (IKEA-style top boxes)

SIDE_W = 640           # each wardrobe column width
VANITY_W = WALL_W - 2 * SIDE_W   # 800 makeup-table niche

DESK_Z = 750           # makeup table top height (top surface)
VANITY_DRAWER_H = 120  # drawer under the table top
VANITY_UPPER_Z = 1600  # bottom of the cabinet above the mirror
MIRROR_Z0, MIRROR_Z1 = 900, 1550

CARCASS_D = DEPTH - T                    # carcass depth behind the doors (452)
TALL_H = WALL_H - PLINTH_H - TOP_BOX_H   # tall carcass height (1900)
TALL_Z = PLINTH_H
TOP_Z = TALL_Z + TALL_H

DOC_NAME = "Bedroom_Cabinet_IKEA"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet"

# ---------------- colours ----------------
C_CARCASS = (0.93, 0.89, 0.80)   # birch-ply look
C_DOOR = (0.97, 0.97, 0.95)      # white doors
C_DRAWER = (0.85, 0.78, 0.65)
C_METAL = (0.55, 0.55, 0.58)
C_MIRROR = (0.75, 0.88, 0.95)
C_PLINTH = (0.35, 0.33, 0.30)

# ---------------- helpers ----------------
if App.listDocuments().get(DOC_NAME):
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)

cut_list = []   # (module, part, length, width, thickness)
_colours = {}


def group(name, parent=None):
    g = doc.addObject("App::DocumentObjectGroup", name)
    if parent:
        parent.addObject(g)
    return g


def box(grp, name, x, y, z, dx, dy, dz, colour=C_CARCASS, cut=True):
    """Axis-aligned panel. Records it in the cut list when one dimension equals T."""
    o = doc.addObject("Part::Box", name)
    o.Length, o.Width, o.Height = dx, dy, dz
    o.Placement.Base = App.Vector(x, y, z)
    grp.addObject(o)
    _colours[o.Name] = colour
    if cut:
        dims = sorted([dx, dy, dz], reverse=True)
        cut_list.append((grp.Label, name, round(dims[0], 1), round(dims[1], 1), round(dims[2], 1)))
    return o


def rail(grp, name, x0, x1, y, z):
    o = doc.addObject("Part::Cylinder", name)
    o.Radius, o.Height = 12.5, x1 - x0
    o.Placement = App.Placement(App.Vector(x0, y, z), App.Rotation(App.Vector(0, 1, 0), 90))
    grp.addObject(o)
    _colours[o.Name] = C_METAL
    return o


def handle(grp, name, x, z, length=160, vertical=True):
    dx, dz = (12, length) if vertical else (length, 12)
    return box(grp, name, x - dx / 2, -25, z - dz / 2, dx, 25, dz, C_METAL, cut=False)


def carcass(grp, x, z, w, h, d=CARCASS_D, prefix=""):
    """IKEA-style box: sides full height, top/bottom between sides, 18 mm back at the rear."""
    y0 = DEPTH - d                 # front edge of carcass
    inner_d = d - T                # depth in front of the back panel
    box(grp, prefix + "Side_L", x, y0, z, T, inner_d, h)
    box(grp, prefix + "Side_R", x + w - T, y0, z, T, inner_d, h)
    box(grp, prefix + "Bottom", x + T, y0, z, w - 2 * T, inner_d, T)
    box(grp, prefix + "Top", x + T, y0, z + h - T, w - 2 * T, inner_d, T)
    box(grp, prefix + "Back", x, DEPTH - T, z, w, T, h)
    return y0


def shelf(grp, name, x, z, w, setback=20):
    y0 = DEPTH - CARCASS_D + setback
    box(grp, name, x + T, y0, z, w - 2 * T, CARCASS_D - T - setback, T)


def door(grp, name, x, z, w, h, hinge_left=True):
    box(grp, name, x + GAP / 2, 0, z + GAP / 2, w - GAP, T, h - GAP, C_DOOR)
    hx = x + w - 40 if hinge_left else x + 40
    return hx


def drawer(grp, name, x_in, w_in, z, h, front_y):
    """Internal drawer box (12.5 mm runner clearance each side) with its own front."""
    clr = 12.5
    bw = w_in - 2 * clr
    bd = 400
    y0 = front_y + T
    box(grp, name + "_Front", x_in + 2, front_y, z, w_in - 4, T, h, C_DRAWER)
    box(grp, name + "_Side_L", x_in + clr, y0, z + 10, T, bd - T, h - 30, C_DRAWER)
    box(grp, name + "_Side_R", x_in + clr + bw - T, y0, z + 10, T, bd - T, h - 30, C_DRAWER)
    box(grp, name + "_Back", x_in + clr + T, y0 + bd - 2 * T, z + 10, bw - 2 * T, T, h - 30, C_DRAWER)
    box(grp, name + "_Bottom", x_in + clr + T, y0, z + 10, bw - 2 * T, bd - 2 * T, T, C_DRAWER)


def plinth(grp, x, w):
    box(grp, "Plinth_Front", x, PLINTH_SETBACK, 0, w, T, PLINTH_H, C_PLINTH)
    box(grp, "Plinth_Back", x, DEPTH - 2 * T - 60, 0, w, T, PLINTH_H, C_PLINTH)


root = group("Bedroom_Cabinet")

# ================= LEFT WARDROBE (hanging) =================
gL = group("Wardrobe_Left_Hanging", root)
xL = 0
plinth(gL, xL, SIDE_W)
y0 = carcass(gL, xL, TALL_Z, SIDE_W, TALL_H)
in_top = TALL_Z + TALL_H - T
shelf(gL, "Shelf_Top", xL, in_top - 250, SIDE_W)                     # hat shelf
rail(gL, "Hanging_Rail", xL + T, xL + SIDE_W - T, y0 + (CARCASS_D - T) / 2, in_top - 250 - 50)
# two internal drawers at the bottom for underwear / folded items
inner_x, inner_w = xL + T, SIDE_W - 2 * T
dz = TALL_Z + T
for i, h in enumerate([160, 160]):
    drawer(gL, f"Drawer_{i + 1}", inner_x, inner_w, dz, h, y0 + 30)
    dz += h + 10
shelf(gL, "Shelf_Above_Drawers", xL, dz + 10, SIDE_W)
hx = door(gL, "Door", xL, TALL_Z, SIDE_W, TALL_H, hinge_left=True)
handle(gL, "Door_Handle", hx, TALL_Z + 1000, 300)

# ================= RIGHT WARDROBE (shelves + drawers) =================
gR = group("Wardrobe_Right_Shelves", root)
xR = SIDE_W + VANITY_W
plinth(gR, xR, SIDE_W)
y0 = carcass(gR, xR, TALL_Z, SIDE_W, TALL_H)
inner_x, inner_w = xR + T, SIDE_W - 2 * T
dz = TALL_Z + T
for i, h in enumerate([200, 200, 160, 160]):
    drawer(gR, f"Drawer_{i + 1}", inner_x, inner_w, dz, h, y0 + 30)
    dz += h + 10
for i, z in enumerate([dz + 10, dz + 340, dz + 640, dz + 940]):
    if z < TALL_Z + TALL_H - 150:
        shelf(gR, f"Shelf_{i + 1}", xR, z, SIDE_W)
hx = door(gR, "Door", xR, TALL_Z, SIDE_W, TALL_H, hinge_left=False)
handle(gR, "Door_Handle", hx, TALL_Z + 1000, 300)

# ================= CENTRE: MAKEUP VANITY =================
gV = group("Vanity_Makeup_Table", root)
xV = SIDE_W
# full-height back panel between the wardrobes (mirror is mounted on it)
box(gV, "Back_Panel", xV, DEPTH - T, 0, VANITY_W, T, VANITY_UPPER_Z)
# table top spans wall to door face, fixed to both wardrobe sides
box(gV, "Table_Top", xV, 0, DESK_Z - T, VANITY_W, DEPTH - T, T)
# drawer under the table: runners on the wardrobe sides
drawer(gV, "Table_Drawer", xV, VANITY_W, DESK_Z - T - VANITY_DRAWER_H - 2, VANITY_DRAWER_H, 0)
handle(gV, "Table_Drawer_Handle", xV + VANITY_W / 2, DESK_Z - T - VANITY_DRAWER_H / 2 - 2, 200, vertical=False)
# mirror
m = box(gV, "Mirror_4mm", xV + 60, DEPTH - T - 4, MIRROR_Z0, VANITY_W - 120, 4, MIRROR_Z1 - MIRROR_Z0,
        C_MIRROR, cut=False)
# small open shelf for makeup above the table, below mirror
box(gV, "Makeup_Shelf", xV, DEPTH - T - 150, MIRROR_Z0 - 80, VANITY_W, 150, T)
# upper cabinet above mirror (between wardrobes, up to the top-box line)
up_h = TOP_Z - VANITY_UPPER_Z
gVU = group("Vanity_Upper_Cabinet", gV)
y0 = carcass(gVU, xV, VANITY_UPPER_Z, VANITY_W, up_h, prefix="")
shelf(gVU, "Shelf", xV, VANITY_UPPER_Z + up_h / 2, VANITY_W)
door(gVU, "Door_L", xV, VANITY_UPPER_Z, VANITY_W / 2, up_h)
door(gVU, "Door_R", xV + VANITY_W / 2, VANITY_UPPER_Z, VANITY_W / 2, up_h)
handle(gVU, "Handle_L", xV + VANITY_W / 2 - 30, VANITY_UPPER_Z + 60, 120)
handle(gVU, "Handle_R", xV + VANITY_W / 2 + 30, VANITY_UPPER_Z + 60, 120)

# ================= TOP BOXES (full width, to the ceiling) =================
gT = group("Top_Boxes", root)
for name, x, w, ndoors in [("Left", 0, SIDE_W, 1), ("Centre", SIDE_W, VANITY_W, 2), ("Right", xR, SIDE_W, 1)]:
    g = group(f"Top_Box_{name}", gT)
    carcass(g, x, TOP_Z, w, TOP_BOX_H)
    dw = w / ndoors
    for i in range(ndoors):
        door(g, f"Door_{i + 1}", x + i * dw, TOP_Z, dw, TOP_BOX_H)
        hx = x + (i + 1) * dw - 40 if i == 0 and ndoors == 1 else (x + dw - 30 if i == 0 else x + dw + 30)
        handle(g, f"Handle_{i + 1}", hx, TOP_Z + 60, 120)

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
for mod, part, l, w, t in cut_list:
    key = (mod, re.sub(r"Drawer_\d+_", "Drawer_", part), l, w, t)
    agg[key] = agg.get(key, 0) + 1
with open(os.path.join(OUT_DIR, "cut_list.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Part", "Qty", "Length_mm", "Width_mm", "Thickness_mm"])
    for (mod, part, l, w, t), q in sorted(agg.items()):
        wr.writerow([mod, part, q, l, w, t])

area = sum(l * w for _, _, l, w, _ in cut_list) / 1e6
print(f"Panels: {len(cut_list)}, total ply area {area:.2f} m2 "
      f"(~{area / (1.22 * 2.44) * 1.25:.1f} sheets 4x8 incl. 25% waste)")
