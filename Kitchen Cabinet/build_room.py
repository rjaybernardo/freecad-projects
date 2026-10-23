# Kitchen room shell only (no cabinets yet): 148" wide x 142" long x 92" ceiling.
# Units in the parameters are INCHES; FreeCAD works in mm.
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet/build_room.py").read())
#
# Axes: X = width (0 = left wall -> 148"), Y = length (0 = open front side, no wall -> 142" back wall), Z = up.
# Doors / windows / openings get added here once their sizes and positions are known.

import os
import FreeCAD as App
import Part

IN = 25.4

ROOM_W = 148      # X
ROOM_L = 142      # Y
ROOM_H = 92       # ceiling
WALL_T = 4.5      # 2x4 stud + drywall, shown outside the room so inside dims stay exact

DOC_NAME = "Kitchen_Room"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet"

C_WALL = (0.90, 0.90, 0.88)
C_FLOOR = (0.60, 0.50, 0.40)
C_CEIL = (0.97, 0.97, 0.97)

if App.listDocuments().get(DOC_NAME):
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)
_colours = {}


def box(grp, name, x, y, z, dx, dy, dz, colour):
    o = doc.addObject("Part::Feature", name)
    o.Shape = Part.makeBox(dx * IN, dy * IN, dz * IN, App.Vector(x * IN, y * IN, z * IN))
    grp.addObject(o)
    _colours[o.Name] = colour
    return o


root = doc.addObject("App::DocumentObjectGroup", "Kitchen_Room")
t = WALL_T
box(root, "Floor", -t, 0, -1, ROOM_W + 2 * t, ROOM_L + t, 1, C_FLOOR)
box(root, "Wall_Back", -t, ROOM_L, 0, ROOM_W + 2 * t, t, ROOM_H, C_WALL)
box(root, "Wall_Left", -t, 0, 0, t, ROOM_L, ROOM_H, C_WALL)
box(root, "Wall_Right", ROOM_W, 0, 0, t, ROOM_L, ROOM_H, C_WALL)
box(root, "Ceiling", -t, 0, ROOM_H, ROOM_W + 2 * t, ROOM_L + t, 1, C_CEIL)
doc.recompute()

# ---------------- floor-plan dimensions + wall labels ----------------
import Draft

dims = doc.addObject("App::DocumentObjectGroup", "Layout_Dimensions")
root.addObject(dims)
V = lambda x, y, z=0: App.Vector(x * IN, y * IN, z * IN)
Z = ROOM_H + 2          # draw the plan annotations just above the ceiling so they read in top view
plan = [
    ("Dim_Width", V(0, 0, Z), V(ROOM_W, 0, Z), V(0, -24, Z), f'{ROOM_W}" ({ROOM_W // 12}\'-{ROOM_W % 12}")'),
    ("Dim_Length", V(0, 0, Z), V(0, ROOM_L, Z), V(-24, 0, Z), f'{ROOM_L}" ({ROOM_L // 12}\'-{ROOM_L % 12}")'),
    ("Dim_Ceiling", V(ROOM_W, ROOM_L, 0), V(ROOM_W, ROOM_L, ROOM_H), V(ROOM_W + 24, ROOM_L, 0),
     f'{ROOM_H}" ceiling'),
]
for name, a, b, at, text in plan:
    d = Draft.make_linear_dimension(a, b, at)
    d.Label = name
    if App.GuiUp:
        vo = d.ViewObject
        for prop, val in [("Override", text), ("FontSize", 4 * IN), ("ArrowSize", 1.5 * IN),
                          ("ArrowSizeStart", 1.5 * IN), ("ArrowSizeEnd", 1.5 * IN)]:
            if hasattr(vo, prop):
                setattr(vo, prop, val)
    dims.addObject(d)

for name, x, y in [("BACK WALL", ROOM_W / 2 - 15, ROOM_L - 10), ("OPEN (NO WALL)", ROOM_W / 2 - 22, 6),
                   ("LEFT", 4, ROOM_L / 2), ("RIGHT", ROOM_W - 22, ROOM_L / 2)]:
    t_ = Draft.make_text([name], V(x, y, Z))
    if App.GuiUp:
        t_.ViewObject.FontSize = 4 * IN
    dims.addObject(t_)
doc.recompute()

print(f"Room inside: {ROOM_W}\" W x {ROOM_L}\" L x {ROOM_H}\" H "
      f"({ROOM_W / 12:.2f} ft x {ROOM_L / 12:.2f} ft, {ROOM_W * ROOM_L / 144:.1f} sq ft)")

if App.GuiUp:
    import FreeCADGui as Gui
    for name, c in _colours.items():
        doc.getObject(name).ViewObject.ShapeColor = c
    for name in ("Wall_Left", "Ceiling"):
        doc.getObject(name).ViewObject.Transparency = 75
    v = Gui.activeDocument().activeView()
    doc.getObject("Ceiling").ViewObject.Visibility = False
    v.viewTop()
    v.fitAll()
    Gui.updateGui()
    v.saveImage(os.path.join(OUT_DIR, "room_plan_top.png"), 1600, 1400, "White")
    v.viewIsometric()
    v.fitAll()
    Gui.updateGui()
    v.saveImage(os.path.join(OUT_DIR, "room_iso.png"), 1600, 1200, "White")
    doc.getObject("Ceiling").ViewObject.Visibility = True
    doc.getObject("Ceiling").ViewObject.Visibility = False   # keep it hidden while laying out

doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))
