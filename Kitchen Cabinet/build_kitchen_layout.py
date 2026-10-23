# Kitchen layout v1: L-shaped kitchen + island, room 148" wide x 142" long x 92" ceiling.
# This is a LAYOUT model (cabinet blocks, fronts, counters, appliances, clearances),
# not a construction / cut-list model yet. Units in the parameters are INCHES; FreeCAD works in mm.
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet/build_kitchen_layout.py").read())
# Change the parameters below and re-run to regenerate.
#
# Axes: X = room width (0 = left wall -> 148" right wall), Y = room length (0 = entry side -> 142" back wall), Z = up.
# Layout:
#   - back wall run  : corner lazy susan | dishwasher | sink | drawer base | fridge (+ cabinet above)
#   - left wall run  : corner | drawer base | range + hood | drawer base | door base
#   - island         : 48" x 37" with 12" seating overhang facing the entry side
#   - wall cabinets  : 36" tall, 18" above the counter, 2" crown/scribe to the 92" ceiling

import os
import FreeCAD as App
import Part

IN = 25.4

# ---------------- room ----------------
ROOM_W = 148           # X: left wall -> right wall
ROOM_L = 142           # Y: entry side -> back wall
ROOM_H = 92            # ceiling height

# ---------------- standard cabinet sizes ----------------
BASE_D = 24            # base cabinet depth (box + door)
BASE_H = 34.5          # base cabinet height incl. toe kick
TOE_H, TOE_D = 4, 3    # toe kick height / recess
CTOP_T = 1.5           # countertop thickness  -> counter height 36"
CTOP_OH = 1            # countertop overhang past the doors
FRONT_T = 0.75         # door / drawer front thickness
GAP = 0.125            # reveal between fronts

UPPER_D = 12
UPPER_Z = BASE_H + CTOP_T + 18      # 54": 18" above the counter
UPPER_H = 36                        # top at 90"
CROWN_H = ROOM_H - UPPER_Z - UPPER_H  # 2" crown / scribe to ceiling

FRIDGE_W, FRIDGE_D, FRIDGE_H = 36, 30, 70
OVER_FRIDGE_Z = 72                  # 24"-deep cabinet above the fridge, top flush with uppers

ISLAND = True
ISLAND_W = 48          # along X
ISLAND_CAB_D = 24
ISLAND_SEAT_OH = 12    # seating overhang toward the entry side
AISLE = 42             # NKBA recommended work aisle (one cook)

DOC_NAME = "Kitchen_Layout_v1"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet"

# ---------------- colours ----------------
C_CARCASS = (0.93, 0.89, 0.80)
C_FRONT = (0.97, 0.97, 0.95)
C_TOE = (0.30, 0.28, 0.26)
C_CTOP = (0.55, 0.55, 0.57)
C_STEEL = (0.75, 0.76, 0.78)
C_BLACK = (0.10, 0.10, 0.11)
C_WALL = (0.90, 0.90, 0.90)
C_FLOOR = (0.60, 0.50, 0.40)
C_ISLAND = (0.25, 0.35, 0.45)

# ---------------- helpers ----------------
if App.listDocuments().get(DOC_NAME):
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)
_colours = {}
schedule = []   # (run, item, width_in, note)


def group(name, parent=None):
    g = doc.addObject("App::DocumentObjectGroup", name)
    if parent:
        parent.addObject(g)
    return g


def solid(grp, name, shape, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    grp.addObject(o)
    _colours[o.Name] = colour
    return o


def mk(x, y, z, dx, dy, dz):
    """Box from inch coordinates."""
    return Part.makeBox(dx * IN, dy * IN, dz * IN, App.Vector(x * IN, y * IN, z * IN))


def box(grp, name, x, y, z, dx, dy, dz, colour=C_CARCASS):
    return solid(grp, name, mk(x, y, z, dx, dy, dz), colour)


class Run:
    """A straight run of cabinets. Local coords: u = along the run, front faces -v.
    wall='back' : u -> +X, cabinet backs on the back wall (Y = ROOM_L)
    wall='left' : u -> -Y (from the back corner toward the entry), backs on the left wall (X = 0)"""

    def __init__(self, grp, wall):
        self.g, self.wall = grp, wall

    def place(self, u, v, z, du, dv, dz):
        """u from the run start, v = distance out from the wall."""
        if self.wall == "back":
            return mk(u, ROOM_L - v - dv, z, du, dv, dz)
        return mk(v, ROOM_L - u - du, z, dv, du, dz)

    def put(self, name, u, v, z, du, dv, dz, colour=C_CARCASS):
        return solid(self.g, name, self.place(u, v, z, du, dv, dz), colour)

    def fronts(self, name, u, w, z0, z1, layout):
        """layout: list of (kind, n) rows bottom->top, heights split evenly; or ('doors', n) etc."""
        rows = len(layout)
        rh = (z1 - z0) / rows
        for r, (kind, n) in enumerate(layout):
            fw = w / n
            for i in range(n):
                self.put(f"{name}_{kind}{r + 1}_{i + 1}", u + i * fw + GAP / 2, BASE_D - FRONT_T,
                         z0 + r * rh + GAP / 2, fw - GAP, FRONT_T, rh - GAP, C_FRONT)

    def base(self, name, u, w, fronts, note=""):
        self.put(name + "_Toe", u, 0, 0, w, BASE_D - TOE_D, TOE_H, C_TOE)
        self.put(name + "_Box", u, 0, TOE_H, w, BASE_D - FRONT_T, BASE_H - TOE_H)
        if fronts:
            self.fronts(name, u, w, TOE_H, BASE_H, fronts)
        schedule.append((self.wall, name, w, note))

    def upper(self, name, u, w, doors=2, z=UPPER_Z, h=UPPER_H, d=UPPER_D, note=""):
        self.put(name + "_Box", u, 0, z, w, d - FRONT_T, h)
        fw = w / doors
        for i in range(doors):
            self.put(f"{name}_Door{i + 1}", u + i * fw + GAP / 2, d - FRONT_T, z + GAP / 2,
                     fw - GAP, FRONT_T, h - GAP, C_FRONT)
        schedule.append((self.wall + " upper", name, w, note))

    def counter(self, name, u, w, depth=BASE_D + CTOP_OH, cut=None):
        shape = self.place(u, 0, BASE_H, w, depth, CTOP_T)
        if cut:
            shape = shape.cut(cut)
        return solid(self.g, name, shape, C_CTOP)

    def crown(self, name, u, w, d=UPPER_D):
        if CROWN_H > 0:
            self.put(name, u, 0, UPPER_Z + UPPER_H, w, d, CROWN_H, C_FRONT)


root = group(DOC_NAME)

# ================= BACK WALL RUN (148") =================
# 36 corner | 24 DW | 36 sink | 15 drawers | 36 fridge | 1 filler  = 148
gB = group("Run_Back_Wall", root)
B = Run(gB, "back")
CORNER = 36
u = 0
# corner lazy susan: back part here, return leg built with the left run
B.put("Corner_Box", 0, 0, TOE_H, CORNER, BASE_D - FRONT_T, BASE_H - TOE_H)
B.put("Corner_Toe", 0, 0, 0, CORNER, BASE_D - TOE_D, TOE_H, C_TOE)
B.fronts("Corner", BASE_D, CORNER - BASE_D, TOE_H, BASE_H, [("Door", 1)])
schedule.append(("back", "Corner_LazySusan_36x36", 36, "bi-fold corner doors"))
u = CORNER

DW_U = u
B.put("Dishwasher", DW_U + GAP / 2, 0, TOE_H, 24 - GAP, BASE_D - FRONT_T, BASE_H - TOE_H, C_STEEL)
B.put("Dishwasher_Panel", DW_U + GAP / 2, BASE_D - FRONT_T, TOE_H + GAP, 24 - GAP, FRONT_T,
      BASE_H - TOE_H - 2 * GAP, C_STEEL)
schedule.append(("back", "Dishwasher", 24, "appliance"))
u += 24

SINK_U = u
B.base("Sink_Base_36", u, 36, [("Door", 2)], "false drawer front + 2 doors")
u += 36

B.base("Drawer_Base_15", u, 15, [("Drawer", 1)] * 3, "3 drawers")
u += 15

FRIDGE_U = u
B.put("Fridge", u + 0.5, BASE_D + 6 - FRIDGE_D, 0, FRIDGE_W - 1, FRIDGE_D, FRIDGE_H, C_STEEL)
B.put("Fridge_Cab_Box", u, 0, OVER_FRIDGE_Z, FRIDGE_W, BASE_D - FRONT_T, UPPER_Z + UPPER_H - OVER_FRIDGE_Z)
for i in range(2):
    B.put(f"Fridge_Cab_Door{i + 1}", u + i * FRIDGE_W / 2 + GAP / 2, BASE_D - FRONT_T, OVER_FRIDGE_Z + GAP / 2,
          FRIDGE_W / 2 - GAP, FRONT_T, UPPER_Z + UPPER_H - OVER_FRIDGE_Z - GAP, C_FRONT)
B.crown("Fridge_Crown", u, FRIDGE_W, BASE_D)
schedule.append(("back", "Fridge_36 (opening)", 36, "counter-depth recommended; 30\" deep shown"))
schedule.append(("back upper", "Over_Fridge_36x18x24", 36, "24\" deep"))
u += FRIDGE_W
B.put("Filler_Wall", u, 0, 0, ROOM_W - u, BASE_D, ROOM_H, C_FRONT)   # door-swing filler at the right wall
schedule.append(("back", "Filler", ROOM_W - u, "full height, fridge door clearance"))

# countertop: corner -> drawer base, sink cut-out
sink_cut = B.place(SINK_U + 4.5, 3, BASE_H - 8, 27, 18, 8 + CTOP_T + 1)
B.counter("Countertop", 0, FRIDGE_U, cut=sink_cut)
solid(gB, "Sink_Bowl", B.place(SINK_U + 4.5, 3, BASE_H - 8, 27, 18, 0.25), C_STEEL)

# uppers: 24 corner | 36 | 36 over sink | 15  (ends at the fridge)
B.upper("Upper_Corner_24", 0, 24, 1, note="blind corner")
B.upper("Upper_36_A", 24, 36)
B.upper("Upper_36_Sink", 60, 36)
B.upper("Upper_15", 96, 15, 1)
B.crown("Crown", 0, FRIDGE_U)

# ================= LEFT WALL RUN =================
# from the back corner toward the entry: 36 corner | 18 drawers | 30 range | 18 drawers | 24 door base
gL = group("Run_Left_Wall", root)
L = Run(gL, "left")
L.put("Corner_Return_Box", BASE_D, 0, TOE_H, CORNER - BASE_D, BASE_D - FRONT_T, BASE_H - TOE_H)
L.put("Corner_Return_Toe", BASE_D, 0, 0, CORNER - BASE_D, BASE_D - TOE_D, TOE_H, C_TOE)
L.fronts("Corner", BASE_D, CORNER - BASE_D, TOE_H, BASE_H, [("Door", 1)])
u = CORNER
L.base("Drawer_Base_18_A", u, 18, [("Drawer", 1)] * 3, "3 drawers")
u += 18
RANGE_U = u
L.put("Range", u + GAP / 2, 0, 0, 30 - GAP, BASE_D + 1, BASE_H + CTOP_T, C_STEEL)
L.put("Range_Cooktop", u + 1, 2, BASE_H + CTOP_T, 28, 21, 0.3, C_BLACK)
L.put("Range_Oven_Door", u + 1, BASE_D + 1, 6, 28, 1, 22, C_BLACK)
schedule.append(("left", "Range_30", 30, "freestanding / slide-in"))
u += 30
L.base("Drawer_Base_18_B", u, 18, [("Drawer", 1)] * 3, "3 drawers")
u += 18
L.base("Door_Base_24", u, 24, [("Door", 1), ("Drawer", 1)], "1 drawer + 1 door")
u += 24
LEFT_END = u
L.put("End_Panel", u, 0, 0, FRONT_T, BASE_D, BASE_H, C_FRONT)
schedule.append(("left", "End_Panel", FRONT_T, "finished end"))

# countertop starts at the back run's counter edge (they meet in the corner)
L.counter("Countertop_A", BASE_D + CTOP_OH, RANGE_U - BASE_D - CTOP_OH)
L.counter("Countertop_B", RANGE_U + 30, LEFT_END + FRONT_T - RANGE_U - 30)

# uppers: corner side uses the back run's 12" return -> start at u = UPPER_D
L.upper("Upper_24_A", UPPER_D, 24, 1)
L.upper("Upper_18_A", UPPER_D + 24, RANGE_U - UPPER_D - 24, 1)
# range hood (chimney style) over the range
HOOD_Z = BASE_H + CTOP_T + 30       # 30" above the cooktop
L.put("Hood", RANGE_U, 0, HOOD_Z, 30, 20, 6, C_STEEL)
L.put("Hood_Chimney", RANGE_U + 9, 0, HOOD_Z + 6, 12, 10, ROOM_H - HOOD_Z - 6, C_STEEL)
schedule.append(("left upper", "Hood_30", 30, "vent to exterior"))
L.upper("Upper_18_B", RANGE_U + 30, 18, 1)
L.upper("Upper_24_B", RANGE_U + 48, LEFT_END - RANGE_U - 48, 1)
L.crown("Crown_A", UPPER_D, RANGE_U - UPPER_D)
L.crown("Crown_B", RANGE_U + 30, LEFT_END - RANGE_U - 30)

# ================= ISLAND =================
clear = {}
if ISLAND:
    gI = group("Island", root)
    back_counter_front = ROOM_L - BASE_D - CTOP_OH
    left_counter_front = BASE_D + CTOP_OH
    ctop_y1 = back_counter_front - AISLE                     # work side of the island counter
    cab_y1 = ctop_y1 - CTOP_OH
    cab_y0 = cab_y1 - ISLAND_CAB_D
    ctop_y0 = cab_y0 - ISLAND_SEAT_OH
    ctop_x0 = left_counter_front + AISLE
    ctop_x1 = ctop_x0 + ISLAND_W
    cab_x0, cab_x1 = ctop_x0 + CTOP_OH, ctop_x1 - CTOP_OH
    cw = cab_x1 - cab_x0
    box(gI, "Island_Toe", cab_x0 + TOE_D, cab_y0, 0, cw - 2 * TOE_D, ISLAND_CAB_D - TOE_D, TOE_H, C_TOE)
    box(gI, "Island_Box", cab_x0, cab_y0, TOE_H, cw, ISLAND_CAB_D - FRONT_T, BASE_H - TOE_H, C_ISLAND)
    n = 2
    for i in range(n):
        fw = cw / n
        for r, (z0, z1) in enumerate([(TOE_H, TOE_H + 10), (TOE_H + 10, BASE_H)]):
            box(gI, f"Island_Front{r + 1}_{i + 1}", cab_x0 + i * fw + GAP / 2, cab_y1 - FRONT_T, z0 + GAP / 2,
                fw - GAP, FRONT_T, z1 - z0 - GAP, C_ISLAND)
    box(gI, "Island_Countertop", ctop_x0, ctop_y0, BASE_H, ISLAND_W, ctop_y1 - ctop_y0, CTOP_T, C_CTOP)
    # two bar stools on the seating side
    for i in range(2):
        sx = ctop_x0 + ISLAND_W * (i + 1) / 3
        stool = Part.makeCylinder(7 * IN, 1.5 * IN, App.Vector(sx * IN, (ctop_y0 - 4) * IN, 24 * IN))
        leg = Part.makeCylinder(1 * IN, 24 * IN, App.Vector(sx * IN, (ctop_y0 - 4) * IN, 0))
        solid(gI, f"Stool_{i + 1}", stool.fuse(leg), C_BLACK)
    schedule.append(("island", "Island_Base_46 (2 x 23)", cw, "drawers + doors, work side faces back wall"))
    clear = {
        "Aisle island <-> back counter": back_counter_front - ctop_y1,
        "Aisle island <-> left counter": ctop_x0 - left_counter_front,
        "Island -> right wall": ROOM_W - ctop_x1,
        "Island seating edge -> entry wall": ctop_y0,
        "Island <-> fridge front": ROOM_L - (BASE_D + 6) - ctop_y1,
    }

# ================= ROOM (reference) =================
gRef = group("Room", root)
WT = 4
box(gRef, "Floor", -WT, -WT, -1, ROOM_W + 2 * WT, ROOM_L + 2 * WT, 1, C_FLOOR)
box(gRef, "Wall_Back", -WT, ROOM_L, 0, ROOM_W + 2 * WT, WT, ROOM_H, C_WALL)
box(gRef, "Wall_Left", -WT, -WT, 0, WT, ROOM_L + WT, ROOM_H, C_WALL)
box(gRef, "Wall_Right", ROOM_W, -WT, 0, WT, ROOM_L + WT, ROOM_H, C_WALL)

doc.recompute()

# ---------------- report ----------------
print(f"Room {ROOM_W}\" W x {ROOM_L}\" L x {ROOM_H}\" H")
print(f"Back run uses {FRIDGE_U + FRIDGE_W:.2f}\" + filler; left run {LEFT_END + FRONT_T:.2f}\" of {ROOM_L}\"")
print(f"Counter height {BASE_H + CTOP_T}\", uppers {UPPER_Z}\"-{UPPER_Z + UPPER_H}\", crown {CROWN_H}\"")
for k, v in clear.items():
    print(f"  {k}: {v:.1f}\"")
# work triangle: sink centre, range centre, fridge centre (on the cabinet fronts)
sink_c = (SINK_U + 18, ROOM_L - BASE_D)
range_c = (BASE_D, ROOM_L - RANGE_U - 15)
fridge_c = (FRIDGE_U + FRIDGE_W / 2, ROOM_L - BASE_D - 6)
legs = [((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for a, b in
        [(sink_c, range_c), (range_c, fridge_c), (fridge_c, sink_c)]]
print("Work triangle legs: " + ", ".join(f"{l:.0f}\"" for l in legs) + f"  total {sum(legs) / 12:.1f} ft")

with open(os.path.join(OUT_DIR, "layout_schedule.csv"), "w") as f:
    f.write("Run,Item,Width_in,Note\n")
    for r, item, w, note in schedule:
        f.write(f"{r},{item},{w:g},{note}\n")

# ---------------- colours (GUI only) ----------------
if App.GuiUp:
    import FreeCADGui as Gui
    for name, c in _colours.items():
        doc.getObject(name).ViewObject.ShapeColor = c
    for w in ("Wall_Back", "Wall_Left", "Wall_Right"):
        doc.getObject(w).ViewObject.Transparency = 70
    Gui.activeDocument().activeView().viewIsometric()
    Gui.activeDocument().activeView().fitAll()

doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))
