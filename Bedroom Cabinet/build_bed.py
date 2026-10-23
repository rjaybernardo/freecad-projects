# Bed frame for a 5 ft x 6 ft mattress, matching the v3 cabinet (3/4" marine plywood, HPL both faces).
# Placed against the wall OPPOSITE the cabinet, centred so the space left and right of the bed is equal.
# Units: mm.
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet/build_bed.py").read())
# or headless:  freecadcmd build_bed.py
# Change the parameters below and re-run to regenerate the model + cut list.
#
# Axes are the same as build_cabinet_v3.py: X = width (left->right, facing the cabinet wall),
# Y = depth (0 = cabinet door face, +Y = towards the cabinet wall), Z = up.
# The opposite wall therefore sits at negative Y.
#
# Construction: box frame of four laminated rails down to the floor, 18 mm ply slats on
# cleats, a centre spine + two cross ribs underneath, and a laminated headboard against the wall.
# The mattress sits RECESS mm inside the rails so it can't slide.

import csv
import os
import FreeCAD as App
import Part

# ---------------- parameters ----------------
WALL_W = 2080          # room width wall-to-wall (same walls as the cabinet)
WALL_H = 2380
CAB_DEPTH = 470        # cabinet depth: its wall is at Y = CAB_DEPTH
ROOM_L = 3000          # cabinet wall -> opposite wall (MEASURE ON SITE and change this)

MAT_W = 1524           # 5 ft mattress width
MAT_L = 1829           # 6 ft mattress length
MAT_H = 200            # mattress thickness (visual only)
CLR = 10               # clearance around the mattress inside the rails

PLY = 18               # 3/4" marine plywood core
LAM = 0.8              # laminate (HPL) per face
T = PLY + 2 * LAM      # finished visible panel thickness (19.6)

RAIL_H = 330           # side / foot / head rail height (floor to top)
RECESS = 50            # mattress sits this far below the rail top
SLAT_W = 90            # slat width (ply strip)
SLAT_GAP = 60          # gap between slats (<= 70 mm for foam / spring mattresses)
CLEAT_H = 40           # cleat under the slat ends, glued + screwed to the rails
HEADBOARD_H = 1100     # headboard height from the floor
TOE = 3                # headboard / rails stand on 3 mm felt pads (floor protection)

FRAME_W = MAT_W + 2 * CLR + 2 * T       # outside width of the box frame
FRAME_L = MAT_L + 2 * CLR + 2 * T       # outside length of the box frame
IN_W = FRAME_W - 2 * T                  # inside width (mattress + clearance)
IN_L = FRAME_L - 2 * T
SLAT_TOP = RAIL_H - RECESS              # top of the slats = underside of the mattress
SLAT_Z = SLAT_TOP - PLY
SIDE_GAP = (WALL_W - FRAME_W) / 2       # equal space left and right of the bed

Y_WALL = CAB_DEPTH - ROOM_L             # face of the opposite wall
X0 = SIDE_GAP                           # left edge of the bed
Y_HB = Y_WALL                           # headboard back face against the wall
Y0 = Y_HB + T                           # head end of the box frame
Y1 = Y0 + FRAME_L                       # foot end of the box frame

DOC_NAME = "Bed_Frame_5x6"
CUT_LIST = "cut_list_bed.csv"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet"

# ---------------- colours ----------------
C_FRAME = (0.97, 0.97, 0.95)     # white laminate, same as the cabinet doors
C_PLY = (0.93, 0.89, 0.80)       # raw birch-ply look (hidden parts)
C_MATTRESS = (0.85, 0.87, 0.90)
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


def box(grp, name, x, y, z, dx, dy, dz, colour=C_FRAME, cut=True, note=""):
    """Axis-aligned panel, recorded in the cut list."""
    o = doc.addObject("Part::Box", name)
    o.Length, o.Width, o.Height = dx, dy, dz
    o.Placement.Base = App.Vector(x, y, z)
    grp.addObject(o)
    _colours[o.Name] = colour
    if cut:
        dims = sorted([dx, dy, dz], reverse=True)
        cut_list.append((grp.Label, name, round(dims[0], 1), round(dims[1], 1), round(dims[2], 1), note))
    return o


root = group("Bed_Frame_5x6")

# ================= BOX FRAME (laminated, visible) =================
# Side rails run the full length; head / foot rails sit between them.
gF = group("Box_Frame", root)
box(gF, "Rail_Side_L", X0, Y0, TOE, T, FRAME_L, RAIL_H - TOE, note="HPL both faces, edge-band top")
box(gF, "Rail_Side_R", X0 + FRAME_W - T, Y0, TOE, T, FRAME_L, RAIL_H - TOE, note="HPL both faces, edge-band top")
box(gF, "Rail_Head", X0 + T, Y0, TOE, IN_W, T, RAIL_H - TOE, note="HPL both faces")
box(gF, "Rail_Foot", X0 + T, Y1 - T, TOE, IN_W, T, RAIL_H - TOE, note="HPL both faces, edge-band top")

# ================= SUPPORT (raw ply, hidden) =================
gS = group("Support", root)
xi, yi = X0 + T, Y0 + T                 # inside corner of the frame
# cleats along the side rails carry the slat ends
for side, x in (("L", xi), ("R", xi + IN_W - PLY)):
    box(gS, f"Cleat_{side}", x, yi, SLAT_Z - CLEAT_H, PLY, IN_L, CLEAT_H, C_PLY, note="glue + screw to rail")
# centre spine (floor to underside of slats) carries the slat middles
spine_x = X0 + FRAME_W / 2 - PLY / 2
box(gS, "Centre_Spine", spine_x, yi, TOE, PLY, IN_L, SLAT_Z - TOE, C_PLY)
# two cross ribs, each split by the spine, stop the rails from bowing out
for i, f in enumerate((1 / 3, 2 / 3)):
    y = yi + IN_L * f - PLY / 2
    for side, x0, x1 in (("L", xi + PLY, spine_x), ("R", spine_x + PLY, xi + IN_W - PLY)):
        box(gS, f"Cross_Rib_{i + 1}{side}", x0, y, TOE, x1 - x0, PLY, SLAT_Z - TOE, C_PLY)

# ================= SLATS =================
gL = group("Slats", root)
n = int((IN_L + SLAT_GAP) // (SLAT_W + SLAT_GAP))
gap = (IN_L - n * SLAT_W) / (n - 1)     # spread evenly, first + last slat touch the end rails
for i in range(n):
    box(gL, f"Slat_{i + 1:02d}", xi, yi + i * (SLAT_W + gap), SLAT_Z, IN_W, SLAT_W, PLY, C_PLY,
        note="screw to cleats + spine")

# ================= HEADBOARD =================
gH = group("Headboard", root)
box(gH, "Headboard", X0, Y_HB, TOE, FRAME_W, T, HEADBOARD_H - TOE,
    note="HPL both faces, edge-band top + sides; bolt to Rail_Head + wall")

# ================= mattress + room reference (not in cut list) =================
gRef = group("Reference_Room", root)
box(gRef, "Mattress_5x6", xi + CLR, yi + CLR, SLAT_TOP, MAT_W, MAT_L, MAT_H, C_MATTRESS, cut=False)
box(gRef, "Wall_Opposite", -200, Y_WALL - 10, -10, WALL_W + 400, 10, WALL_H + 10, (0.9, 0.9, 0.9), cut=False)
box(gRef, "Wall_Cabinet", -200, CAB_DEPTH, -10, WALL_W + 400, 10, WALL_H + 10, (0.9, 0.9, 0.9), cut=False)
box(gRef, "Wall_Left", -100, Y_WALL - 10, -10, 100, ROOM_L + 20, WALL_H + 10, (0.9, 0.9, 0.9), cut=False)
box(gRef, "Wall_Right", WALL_W, Y_WALL - 10, -10, 100, ROOM_L + 20, WALL_H + 10, (0.9, 0.9, 0.9), cut=False)
box(gRef, "Floor", -200, Y_WALL - 10, -10, WALL_W + 400, ROOM_L + 20, 10, (0.6, 0.5, 0.4), cut=False)
box(gRef, "Cabinet_v3_Envelope", 0, 0, 0, WALL_W, CAB_DEPTH, WALL_H, C_CAB, cut=False)

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

# ---------------- save + cut list ----------------
doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))

agg = {}
for mod, part, l, w, t, note in cut_list:
    key = (mod, part.rstrip("0123456789_LR") if mod in ("Slats", "Support") else part, l, w, t, note)
    agg[key] = agg.get(key, 0) + 1
with open(os.path.join(OUT_DIR, CUT_LIST), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Part", "Qty", "Length_mm", "Width_mm", "Thickness_mm", "Edge_Work"])
    for (mod, part, l, w, t, note), q in sorted(agg.items()):
        wr.writerow([mod, part, q, l, w, t, note])

area = sum(l * w for _, _, l, w, _, _ in cut_list) / 1e6
print(f"Frame {FRAME_W:.0f} x {FRAME_L + T:.0f} mm (incl. headboard), {n} slats")
print(f"Space left/right of bed: {SIDE_GAP:.0f} mm each")
print(f"Walkway between foot of bed and cabinet doors: {0 - Y1:.0f} mm")
print(f"Panels: {len(cut_list)}, total ply area {area:.2f} m2 "
      f"(~{area / (1.22 * 2.44) * 1.25:.1f} sheets 4x8 incl. 25% waste)")
