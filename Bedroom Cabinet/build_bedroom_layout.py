# Bedroom layout: the v5 cabinet + the v3 bed wall unit (Filipino heights; v4 + v2 are in git history) in one room, and a dimensioned floor plan.
# Both models already share one coordinate system (X = width, Y = 0 at the cabinet door face,
# cabinet wall at +Y, bed wall at -Y), so they are simply linked into one document.
# Links (App::Link) keep each model's colours and follow it when you re-run its build script.
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet/build_bedroom_layout.py").read())
# or headless:  freecadcmd build_bedroom_layout.py
# Re-run build_cabinet_v5.py / build_bed_v3.py first if you changed them.

import os
import FreeCAD as App

OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet"
CABINET = os.path.join(OUT_DIR, "Bedroom_Cabinet_Modern_v5.FCStd")
BED = os.path.join(OUT_DIR, "Bed_Wall_Unit_v3.FCStd")
DOC_NAME = "Bedroom_Layout"
PLAN = os.path.join(OUT_DIR, "bedroom_layout_plan.png")

ROOM_W_IN, ROOM_L_IN = 90, 116          # as measured (inches), shown on the plan
IN = 25.4


def open_doc(path):
    for d in App.listDocuments().values():
        if d.FileName == path:
            return d
    return App.openDocument(path)


cab, bed = open_doc(CABINET), open_doc(BED)
if App.listDocuments().get(DOC_NAME):
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)
doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))   # external links need a saved owner document


def link(src_doc, name, parent):
    o = src_doc.getObject(name)
    lk = doc.addObject("App::Link", "Link_" + name)
    parent.Group = parent.Group + [lk]     # addObject() would follow the link to the external object
    lk.Label = o.Label
    parent.addObject(lk)
    return lk


g_cab = doc.addObject("App::DocumentObjectGroup", "Cabinet_v5")
for name in ("Wardrobe_Left_Hanging", "Tower_Right_Shelves", "Centre_TV_Makeup", "Top_Boxes", "Scribe_Strips"):
    link(cab, name, g_cab)
g_bed = doc.addObject("App::DocumentObjectGroup", "Bed_Wall_Unit_v3")
bed_root = bed.getObject("Bed_Wall_Unit_v3")
for o in bed_root.Group:
    if o.Name != "Reference_Room":
        link(bed, o.Name, g_bed)
g_room = doc.addObject("App::DocumentObjectGroup", "Room")
for name in ("Mattress_5x6", "Wall_Opposite", "Wall_Cabinet", "Wall_Left", "Wall_Right", "Floor"):
    link(bed, name, g_room)
doc.recompute()

if App.GuiUp:
    import FreeCADGui as Gui
    for name in ("Wall_Opposite", "Wall_Cabinet", "Wall_Left", "Wall_Right"):
        doc.getObject("Link_" + name).ViewObject.Transparency = 70
    Gui.activeDocument().activeView().viewIsometric()
    Gui.activeDocument().activeView().fitAll()

doc.save()

# ================= floor plan (top view) =================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc


def bb(d, name):
    return d.getObject(name).Shape.BoundBox


def group_bb(d, name):
    """Bounding box of every solid under a group (groups have no shape of their own in the GUI)."""
    box = App.BoundBox()
    o = d.getObject(name)
    for x in [o] + o.OutListRecursive:
        if x.TypeId != "App::DocumentObjectGroup" and hasattr(x, "Shape") and x.Shape.Solids:
            box.add(x.Shape.BoundBox)
    return box


def rect(ax, b, **kw):
    ax.add_patch(Rectangle((b.XMin, b.YMin), b.XLength, b.YLength, **kw))


def dim(ax, x0, y0, x1, y1, text, off=0, colour="#333"):
    """Dimension line with arrows; off shifts the text sideways."""
    ax.annotate("", (x0, y0), (x1, y1), arrowprops=dict(arrowstyle="<->", color=colour, lw=0.9))
    ax.text((x0 + x1) / 2 + (off if x0 == x1 else 0), (y0 + y1) / 2 + (off if y0 == y1 else 0), text,
            ha="center", va="center", fontsize=8, color=colour,
            rotation=90 if x0 == x1 else 0, bbox=dict(fc="white", ec="none", pad=1))


def mm_in(v):
    return f"{v:.0f} mm ({v / IN:.1f} in)"


walls = {n: bb(bed, n) for n in ("Wall_Opposite", "Wall_Cabinet", "Wall_Left", "Wall_Right")}
x_l, x_r = walls["Wall_Left"].XMax, walls["Wall_Right"].XMin
y_bed_wall, y_cab_wall = walls["Wall_Opposite"].YMax, walls["Wall_Cabinet"].YMin

fig, ax = plt.subplots(figsize=(8.5, 11))
for b in walls.values():
    rect(ax, b, fc="#888", ec="none")
ax.add_patch(Rectangle((x_l, y_bed_wall), x_r - x_l, y_cab_wall - y_bed_wall, fc="#f4efe6", ec="none", zorder=0))

# cabinet (footprint + tall doors swinging into the room)
cab_bb = App.BoundBox()
for g in ("Wardrobe_Left_Hanging", "Tower_Right_Shelves", "Centre_TV_Makeup", "Top_Boxes"):
    rect(ax, group_bb(cab, g), fc="#e9e3d6", ec="#555", lw=0.8)
    cab_bb.add(group_bb(cab, g))
ax.text((x_l + x_r) / 2, cab_bb.YMax - 230, "CABINET v5\nwardrobe | TV + makeup table | shelves",
        ha="center", va="center", fontsize=8)
for grp, hinge_left in (("Wardrobe_Left_Hanging", True), ("Tower_Right_Shelves", False)):
    door = next(o for o in cab.getObject(grp).Group if o.Name.startswith("Door"))
    b = door.Shape.BoundBox
    hx = b.XMin if hinge_left else b.XMax
    ax.add_patch(Arc((hx, b.YMin), 2 * b.XLength, 2 * b.XLength,
                     theta1=270 if hinge_left else 180, theta2=360 if hinge_left else 270,
                     ec="#c33", lw=0.8, ls="--"))
    ax.plot([hx, hx], [b.YMin, b.YMin - b.XLength], color="#c33", lw=0.8)

# bed wall unit: towers (nightstand footprint), headboard, storage boxes, mattress, drawers pulled out
for side in ("Left", "Right"):
    b = group_bb(bed, f"Nightstand_{side}")
    rect(ax, b, fc="#d9cfc4", ec="#555", lw=0.8)
    ax.text(b.Center.x, b.Center.y, f"tower\n{b.XLength:.0f}", ha="center", va="center", fontsize=7)
rect(ax, bb(bed, "Headboard"), fc="#a8988c", ec="#555", lw=0.8)
store = group_bb(bed, "Storage_Bed")
labels = {"Head_Box": "lift-up", "Side_Box": "side drawer", "Foot_Box": "drawer"}
side_travel, drawer_out = 337, 450
for o in bed.getObject("Storage_Bed").Group:
    b = group_bb(bed, o.Name)
    kind = next(k for k in labels if o.Name.startswith(k))
    rect(ax, b, fc="#fbfaf7", ec="#555", lw=0.8)
    ax.text(b.Center.x, b.Center.y, labels[kind], ha="center", va="center", fontsize=7, color="#777")
    if kind == "Foot_Box":
        ax.add_patch(Rectangle((b.XMin + 25, store.YMax), b.XLength - 50, drawer_out,
                               fc="none", ec="#c33", lw=0.8, ls="--"))
    elif kind == "Side_Box":
        x = store.XMin - side_travel if o.Name.endswith("L") else store.XMax
        ax.add_patch(Rectangle((x, b.YMin + 25), side_travel, b.YLength - 50, fc="none", ec="#c33", lw=0.8, ls="--"))
mat = bb(bed, "Mattress_5x6")
rect(ax, mat, fc="none", ec="#36c", lw=1, ls=":")
ax.text(mat.Center.x, mat.Center.y + 250, "mattress 5 x 6 ft", ha="center", fontsize=8, color="#36c")
ax.text(store.Center.x, store.YMax + drawer_out / 2, "drawers fully open", ha="center", va="center",
        fontsize=7, color="#c33")

# dimensions
dim(ax, x_l, y_bed_wall - 150, x_r, y_bed_wall - 150, f"{mm_in(x_r - x_l)}")
dim(ax, x_l - 150, y_bed_wall, x_l - 150, y_cab_wall, mm_in(y_cab_wall - y_bed_wall))
dim(ax, x_r + 120, store.YMax, x_r + 120, cab_bb.YMin, f"walkway {cab_bb.YMin - store.YMax:.0f}",
    colour="#c33")
dim(ax, store.XMin, store.YMin + 120, store.XMax, store.YMin + 120, f"bed {store.XLength:.0f}")
dim(ax, store.XMin - 120, store.YMin, store.XMin - 120, store.YMax, f"{store.YLength:.0f}")

ax.set_title(f"Bedroom layout - plan view (room measured {ROOM_W_IN} x {ROOM_L_IN} in "
             f"= {ROOM_W_IN * IN:.0f} x {ROOM_L_IN * IN:.0f} mm)", fontsize=10)
ax.set_aspect("equal")
ax.set_xlim(x_l - 400, x_r + 400)
ax.set_ylim(y_bed_wall - 400, y_cab_wall + 250)
ax.axis("off")
fig.tight_layout()
fig.savefig(PLAN, dpi=150)
print(f"Saved {DOC_NAME}.FCStd and {os.path.basename(PLAN)}")
print(f"Walkway bed -> cabinet doors: {cab_bb.YMin - store.YMax:.0f} mm, drawers open leave "
      f"{cab_bb.YMin - store.YMax - drawer_out:.0f} mm")
