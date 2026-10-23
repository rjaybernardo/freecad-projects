# Kitchen v1: left-wall run  REF -> SINK -> STOVE -> WASHING MACHINE, modular cabinets.
# Room: 148" W x 142" L x 92" ceiling, open front (no wall), back / left / right walls.
# All panels 3/4" marine plywood (18 mm) laminated both faces, same as the bedroom cabinet. Units: mm.
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet/build_kitchen.py").read())
# Change the parameters below and re-run to regenerate the model + cut list.
#
# Axes: X = out from the left wall (0 = masonry face; door / backsplash planes are measured from SERVICE_D), Y = room length (0 = open front -> back wall), Z = up.
# Along the run, `u` = distance from the open front (ref end) toward the back wall.
#
# Left wall, 3607 mm (142"), from the open front toward the back wall:
#   50 filler | 950 fridge bay | 19.6 tall panel | 900 sink base | 400 drawer base | 620 stove bay
#   | 19.6 washer panel | 628 washer bay | 19.6 end panel  = 3607
# The front-loading washer (60 x 85 x 55 cm) fits under the counter (876 mm underside): the bay is two
# side panels + a back rail carrying the countertop, with a standard wall cabinet above.
# Corner PVC pipes: the backsplash is set out SERVICE_D from the wall; cabinets go back to the wall.

import csv
import os
import FreeCAD as App
import Part

IN = 25.4

# ---------------- room ----------------
ROOM_W = 148 * IN      # X
ROOM_L = 142 * IN      # Y = left wall length (3606.8)
ROOM_H = 92 * IN       # 2336.8
WALL_T = 4.5 * IN

# ---------------- appliances (W x H x D) ----------------
FRIDGE = (36 * IN, 1780, 25 * IN)          # 3 ft x 178 cm x 25 in
STOVE = (24 * IN, 850, 24 * IN)            # 2 ft x 85 cm x 2 ft
WASHER = (600, 850, 550)                   # 60 x 85 x 55 cm (front loader, under counter)
SINK = (770, 420)                          # 770 x 420 mm top-mount sink

# ---------------- construction ----------------
PLY = 18
LAM = 0.8
T = PLY + 2 * LAM      # 19.6 finished panel
GAP = 3                # reveal around doors / drawer fronts

PLINTH_H = 100         # toe kick
PLINTH_SETBACK = 60
BASE_D = 610           # base depth incl. doors (24")
CARCASS_D = BASE_D - T
BASE_TOP = 876         # top of base carcass (34.5")
CTOP_T = 38            # countertop (1.5")  -> counter height 914 (36")
CTOP_D = 635           # 25"
COUNTER_Z = BASE_TOP + CTOP_T

RUNNER_CLR = 12.5       # side clearance per side for rack runners
RACK_D = 600            # stainless pull-out rack depth / runner length (carcass is 740 inside)
SINK_RACK_D = 450       # under-sink tray stays in front of the drain
UPPER_D = 330          # wall cabinets incl. doors
UPPER_Z = 1372         # 54": 458 above the counter
UPPER_TOP = 2286       # 90"; 51 mm crown/scribe to the ceiling
HOOD_Z = COUNTER_Z + 700

# ---------------- backsplash offset (straight wall face, hides the corner PVC pipes) ----------------
SERVICE_D = 150        # masonry wall -> backsplash face (incl. 19.6 panel); 130 mm cavity. Cabinets fill it.
PIPE_OD = 114          # 4" PVC, one in each corner of the run
PIPE_U = [(T + 10, T + 10 + PIPE_OD), (ROOM_L - PIPE_OD, ROOM_L)]   # pipe spans along the run, tight to the wall
RIB_MAX = 600          # max rib spacing behind the backsplash panels

# ---------------- run along the left wall (from the open front: REF first) ----------------
START_AT_OPEN_END = True   # False = ref in the back-wall corner
BACK_FILLER = 50       # filler at the ref end (fridge door clearance)
FRIDGE_BAY = 950       # 18 mm air gap each side of the 914 fridge
SINK_W = 900
DRAWER_W = 404        # 364.8 clear inside = standard "400" stainless rack (made for 18 mm sides)
STOVE_BAY = 620        # 5 mm each side of the 610 stove
STOVE_PLINTH = COUNTER_Z - STOVE[1]   # 64 mm platform so the cooktop is flush with the counter

u_fridge = BACK_FILLER
u_tall = u_fridge + FRIDGE_BAY
u_sink = u_tall + T
u_drawer = u_sink + SINK_W
u_stove = u_drawer + DRAWER_W
u_wpanel = u_stove + STOVE_BAY
u_washer = u_wpanel + T
u_end = ROOM_L - T
WASHER_BAY = u_end - u_washer
assert WASHER_BAY >= WASHER[0] + 20 and WASHER[1] <= BASE_TOP - 10, f"washer bay too small: {WASHER_BAY:.0f}"

DOC_NAME = "Kitchen_v1"
CUT_LIST = "kitchen_cut_list_v1.csv"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet"

# ---------------- colours ----------------
C_CARCASS = (0.93, 0.89, 0.80)
C_DOOR = (0.97, 0.97, 0.95)
C_DRAWER = (0.85, 0.78, 0.65)
C_PLINTH = (0.35, 0.33, 0.30)
C_CTOP = (0.55, 0.55, 0.57)
C_STEEL = (0.78, 0.79, 0.81)
C_BLACK = (0.10, 0.10, 0.11)
C_WASHER = (0.96, 0.96, 0.98)
C_WALL = (0.90, 0.90, 0.88)
C_FLOOR = (0.60, 0.50, 0.40)

# ---------------- helpers ----------------
if App.listDocuments().get(DOC_NAME):
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)
cut_list = []   # (module, part, length, width, thickness)
hardware = []   # (module, item, size, qty)
_colours = {}


def group(name, parent=None):
    g = doc.addObject("App::DocumentObjectGroup", name)
    if parent:
        parent.addObject(g)
    return g


def gbox(grp, name, x, y, z, dx, dy, dz, colour=C_CARCASS, cut=True, shape=None):
    """Global axis-aligned box (mm)."""
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape if shape is not None else Part.makeBox(dx, dy, dz, App.Vector(x, y, z))
    grp.addObject(o)
    _colours[o.Name] = colour
    if cut:
        dims = sorted([dx, dy, dz], reverse=True)
        cut_list.append((grp.Label, name, round(dims[0], 1), round(dims[1], 1), round(dims[2], 1)))
    return o


def ry(u, du):
    """Room Y of a span [u, u + du] along the run (u = 0 at the open front, REF end)."""
    return u if START_AT_OPEN_END else ROOM_L - u - du


def wbox(grp, name, u, a, d, z, du, dd, dz, colour=C_CARCASS, cut=True):
    """Box on the run. u/du along the run from the ref end, d/dd out from the service-wall face."""
    return gbox(grp, name, SERVICE_D + d, ry(u + a, du), z, dd, du, dz, colour, cut)


class Module:
    """One modular cabinet at run position u (width w). Local a = along the run, d = from the wall."""

    def __init__(self, parent, name, u, w, dshift=0):
        self.g, self.u, self.w, self.dshift = group(name, parent), u, w, dshift
        self.objs = []

    def box(self, name, a, d, z, da, dd, dz, colour=C_CARCASS, cut=True):
        o = wbox(self.g, name, self.u, a, d + self.dshift, z, da, dd, dz, colour, cut)
        self.objs.append(o)
        return o

    def carcass(self, z, h, depth, back=True, stretchers=False):
        """Sides full height, bottom between the sides, top (or two 100 mm stretchers), 19.6 back."""
        w, d0 = self.w, 0
        inner = depth - (T if back else 0)
        dfront = (T if back else 0)
        self.box("Side_A", 0, dfront, z, T, inner, h)
        self.box("Side_B", w - T, dfront, z, T, inner, h)
        self.box("Bottom", T, dfront, z, w - 2 * T, inner, T)
        if stretchers:
            self.box("Stretcher_Front", T, depth - 100, z + h - T, w - 2 * T, 100, T)
            self.box("Stretcher_Back", T, dfront, z + h - T, w - 2 * T, 100, T)
        else:
            self.box("Top", T, dfront, z + h - T, w - 2 * T, inner, T)
        if back:
            self.box("Back", 0, d0, z, w, T, h)

    def plinth(self, depth=BASE_D):
        self.box("Plinth_Front", 0, depth - PLINTH_SETBACK - T, 0, self.w, T, PLINTH_H, C_PLINTH)
        self.box("Plinth_Back", 0, 60, 0, self.w, T, PLINTH_H, C_PLINTH)

    def doors(self, n, z, h, front_d, label="Door"):
        dw = self.w / n
        for i in range(n):
            self.box(f"{label}_{i + 1}", i * dw + GAP / 2, front_d, z + GAP / 2, dw - GAP, T, h - GAP, C_DOOR)

    def shelf(self, name, z, depth, setback=20):
        self.box(name, T, T, z, self.w - 2 * T, depth - 2 * T - setback, T)


def ss_basket(m, name, a, d, z, w, dep, h, item, wall=2):
    """Stainless wire basket / tray (open-top shell) in module m's local coords; goes to the hardware list."""
    x = SERVICE_D + d + m.dshift
    y = ry(m.u + a, w)
    shell = Part.makeBox(dep, w, h, App.Vector(x, y, z)).cut(
        Part.makeBox(dep - 2 * wall, w - 2 * wall, h, App.Vector(x + wall, y + wall, z + wall)))
    gbox(m.g, name, 0, 0, 0, 0, 0, 0, C_STEEL, cut=False, shape=shell)
    hardware.append((m.g.Label, item, f"{w:.0f} W x {dep:.0f} D x {h:.0f} H", 1))


def base_cabinet(parent, name, u, w, kind):
    """Runs back to the masonry wall: front in the usual place, carcass SERVICE_D deeper.
    No fixed shelves / ply drawer boxes: the whole inside is for stainless pull-out racks."""
    m = Module(parent, name, u, w, dshift=-SERVICE_D)
    bd_full = BASE_D + SERVICE_D
    cd = bd_full - T
    m.plinth(bd_full)
    h = BASE_TOP - PLINTH_H
    inner = w - 2 * T
    rack_w = inner - 2 * RUNNER_CLR
    if kind == "sink":
        m.carcass(PLINTH_H, h, cd, back=False, stretchers=True)   # open back for plumbing
        m.doors(2, PLINTH_H, h, cd)
        # door-hinged cabinet: low pull-out tray on the bottom, kept in front of the trap / P-trap
        ss_basket(m, "SS_UnderSink_Tray", T + RUNNER_CLR, cd - SINK_RACK_D, PLINTH_H + T + 10,
                  rack_w, SINK_RACK_D, 120, "Under-sink pull-out tray (on 450 runners)")
    elif kind == "racks":
        m.carcass(PLINTH_H, h, cd, stretchers=True)
        # 3 pull-outs, each its own front: cutlery tray / bowl+plate basket / pot basket
        tiers = [(0.40, 200, "Pot / pan basket"), (0.35, 150, "Bowl + plate basket"),
                 (0.25, 70, "Cutlery / utensil tray")]                  # bottom -> top: share of height
        fz = PLINTH_H
        for i, (share, bh, item) in enumerate(tiers):
            ph = h * share
            m.box(f"Front_{i + 1}", GAP / 2, cd, fz + GAP / 2, w - GAP, T, ph - GAP, C_DOOR)
            ss_basket(m, f"SS_{item.split()[0]}_Basket", T + RUNNER_CLR, cd - RACK_D, fz + 30,
                      rack_w, RACK_D, min(bh, ph - 60), item + f" ({round((inner + 36) / 50) * 50:.0f} cabinet size, {inner:.0f} clear, {RACK_D} runners)")
            fz += ph
    return m


def wall_cabinet(parent, name, u, w, z0, z1, depth=UPPER_D, ndoors=2, pipe=None, shelf=True):
    """Carcass runs back to the masonry (front unchanged by SERVICE_D).
    pipe=(u0, u1): a corner pipe passes through the back corner -> the side, back, top, bottom and
    shelf are notched around it and a small L-shaped chase (2 panels) boxes it in."""
    depth += SERVICE_D
    m = Module(parent, name, u, w, dshift=-SERVICE_D)
    cd = depth - T
    m.carcass(z0, z1 - z0, cd)
    if shelf and z1 - z0 > 600:
        m.shelf("Shelf", z0 + (z1 - z0) / 2, cd)
    m.doors(ndoors, z0, z1 - z0, cd)
    if pipe:
        cu0, cu1 = max(pipe[0] - 10, u), min(pipe[1] + 10, u + w)   # chase interior along the run
        cdp = PIPE_OD + 10                                          # chase interior depth from the wall
        at_start = cu0 <= u + 1
        nu0, nu1 = (cu0, cu1 + T) if at_start else (cu0 - T, cu1)
        notch = Part.makeBox(cdp + T, nu1 - nu0, z1 - z0, App.Vector(0, ry(nu0, nu1 - nu0), z0))
        for o in m.objs:
            if o.Shape.common(notch).Volume > 1:
                o.Shape = o.Shape.cut(notch)
                o.Label = o.Label + " (notched for pipe)"
        # module d already starts at the masonry (dshift = -SERVICE_D)
        m.box("Pipe_Chase_Front", nu0 - u, cdp, z0, nu1 - nu0, T, z1 - z0)
        m.box("Pipe_Chase_Side", (cu1 if at_start else cu0 - T) - u, 0, z0, T, cdp, z1 - z0)
    return m


root = group(DOC_NAME)
run = group("Left_Wall_Run", root)

# ================= REF =================
gF = group("Ref_Bay", run)
wbox(gF, "End_Panel_Ref", 0, 0, -SERVICE_D, 0, T, CTOP_D + SERVICE_D, UPPER_TOP, C_DOOR)       # closes the fridge side at the open end
wbox(gF, "Filler_Ref_End", T, 0, BASE_D - T, 0, BACK_FILLER - T, T, UPPER_TOP, C_DOOR)
fw, fh, fd = FRIDGE
wbox(gF, "Ref_3ft", u_fridge + (FRIDGE_BAY - fw) / 2, 0, 25, 0, fw, fd, fh, C_STEEL, cut=False)
wbox(gF, "Tall_Panel", u_tall, 0, -SERVICE_D, 0, T, CTOP_D + SERVICE_D, UPPER_TOP, C_DOOR)
over_z = max(fh + 40, 1829)
wall_cabinet(gF, "Over_Ref_Cabinet", u_fridge, FRIDGE_BAY, over_z, UPPER_TOP, depth=BASE_D, pipe=PIPE_U[0])

# ================= SINK + DRAWERS + COUNTER =================
gS = group("Sink_Counter", run)
base_cabinet(gS, "Base_Sink_900", u_sink, SINK_W, "sink")
base_cabinet(gS, f"Base_Racks_{DRAWER_W}", u_drawer, DRAWER_W, "racks")
ctop_len = SINK_W + DRAWER_W
ctop = Part.makeBox(CTOP_D, ctop_len, CTOP_T, App.Vector(SERVICE_D, ry(u_sink, ctop_len), BASE_TOP))
sw, sd = SINK
sink_y = ry(u_sink + SINK_W / 2 - sw / 2, sw)
sink_x = SERVICE_D + CTOP_D - 60 - sd                                  # 60 mm from the counter front edge
ctop = ctop.cut(Part.makeBox(sd, sw, CTOP_T + 2, App.Vector(sink_x, sink_y, BASE_TOP - 1)))
gbox(gS, "Countertop", 0, 0, 0, CTOP_D, ctop_len, CTOP_T, C_CTOP, cut=False, shape=ctop)
cut_list.append(("Sink_Counter", "Countertop (solid surface / granite, sink cut-out)", ctop_len, CTOP_D, CTOP_T))
gbox(gS, "Sink_770x420", sink_x + 10, sink_y + 10, BASE_TOP - 200, sd - 20, sw - 20, 200 + CTOP_T + 5,
     C_STEEL, cut=False,
     shape=Part.makeBox(sd + 20, sw + 20, 3, App.Vector(sink_x - 10, sink_y - 10, COUNTER_Z)).fuse(
         Part.makeBox(sd - 20, sw - 20, 200, App.Vector(sink_x + 10, sink_y + 10, COUNTER_Z - 200))))

# ================= STOVE =================
gC = group("Stove_Bay", run)
sw_, sh_, sd_ = STOVE
sy = ry(u_stove + STOVE_BAY / 2 - sw_ / 2, sw_)
gbox(gC, "Stove_Platform", SERVICE_D, sy, 0, sd_, sw_, STOVE_PLINTH, C_PLINTH)
gbox(gC, "Stove_2ft", SERVICE_D, sy, STOVE_PLINTH, sd_, sw_, sh_, C_STEEL, cut=False)
gbox(gC, "Stove_Top", SERVICE_D + 30, sy + 20, COUNTER_Z, sd_ - 60, sw_ - 40, 8, C_BLACK, cut=False)
hood_w = STOVE_BAY
gbox(gC, "Hood", SERVICE_D, ry(u_stove, hood_w), HOOD_Z, 500, hood_w, 120, C_STEEL, cut=False)
gbox(gC, "Hood_Chimney", SERVICE_D, ry(u_stove + hood_w / 2 - 150, 300), HOOD_Z + 120, 250, 300,
     ROOM_H - HOOD_Z - 120, C_STEEL, cut=False)

# ================= WASHING MACHINE =================
gW = group("Washer_Bay", run)
wbox(gW, "Panel_Stove_Side", u_wpanel, 0, -SERVICE_D, 0, T, BASE_D + SERVICE_D, BASE_TOP, C_DOOR)
wbox(gW, "End_Panel", u_end, 0, 0, 0, T, BASE_D, BASE_TOP, C_DOOR)
wbox(gW, "Back_Rail", u_washer, 0, 0, BASE_TOP - 100, WASHER_BAY, T, 100)
wbox(gW, "Front_Rail", u_washer, 0, BASE_D - 100, BASE_TOP - T, WASHER_BAY, 100, T)
ww, wh, wd = WASHER
wbox(gW, "Washer_60x55", u_washer + (WASHER_BAY - ww) / 2, 0, 40, 0, ww, wd, wh, C_WASHER, cut=False)
w_ctop = ROOM_L - u_wpanel
wbox(gW, "Countertop_Washer", u_wpanel, 0, 0, BASE_TOP, w_ctop, CTOP_D, CTOP_T, C_CTOP, cut=False)
cut_list.append(("Washer_Bay", "Countertop (solid surface / granite)", round(w_ctop, 1), CTOP_D, CTOP_T))
wall_cabinet(gW, "Upper_Over_Washer", u_washer, ROOM_L - u_washer, UPPER_Z, UPPER_TOP, pipe=PIPE_U[1])

# ================= WALL CABINETS over the counter =================
gU = group("Wall_Cabinets", run)
mu = wall_cabinet(gU, "Upper_Sink_900", u_sink, SINK_W, UPPER_Z, UPPER_TOP, shelf=False)
# 2-tier stainless dish drainer above the sink: plates low, cups / bowls high, drip tray under
dr_w, dr_d = SINK_W - 2 * T - 10, UPPER_D + SERVICE_D - 2 * T - 20
ss_basket(mu, "SS_Drip_Tray", T + 5, T, UPPER_Z + T + 5, dr_w, dr_d, 25, "Dish drainer drip tray")
ss_basket(mu, "SS_Plate_Rack", T + 5, T, UPPER_Z + T + 60, dr_w, dr_d, 120, "Dish drainer, plate tier (900 cabinet)")
ss_basket(mu, "SS_Cup_Rack", T + 5, T, UPPER_Z + 520, dr_w, dr_d, 80, "Dish drainer, cup / bowl tier (900 cabinet)")
wall_cabinet(gU, f"Upper_{DRAWER_W}", u_drawer, DRAWER_W, UPPER_Z, UPPER_TOP, ndoors=1)

# crown / ceiling scribe over the full run (cut to fit on site)
crown_h = ROOM_H - UPPER_TOP
gK = group("Scribe_Strips", run)
wbox(gK, "Crown_Ref", 0, 0, BASE_D - T, UPPER_TOP, u_tall + T, T, crown_h, C_DOOR)
wbox(gK, "Crown_Uppers", u_sink, 0, UPPER_D - T, UPPER_TOP, SINK_W + DRAWER_W, T, crown_h, C_DOOR)
wbox(gK, "Crown_Washer", u_washer, 0, UPPER_D - T, UPPER_TOP, WASHER_BAY + T, T, crown_h, C_DOOR)

# ================= BACKSPLASH OFFSET =================
# The 150 mm offset exists ONLY where the wall shows: between the counter and the wall cabinets, plus
# floor-to-ceiling behind the stove + hood. Base and wall cabinets run back to the masonry (the offset
# becomes cabinet depth). Ply ribs on the wall carry laminated face panels; the corner pipes run in the
# cavity behind the washer-bay panel (removable) and through small chases in the end wall cabinets.
gV = group("Backsplash_Offset", root)
cav = SERVICE_D - T
pipe_zone = (PIPE_OD + 40, ROOM_L - PIPE_OD - 40 - T)


def splash(name, u0, u1, z0, z1, note=""):
    n = -(-(u1 - u0) // 2440)                       # panels <= 2440 long
    pw = (u1 - u0) / n
    for i in range(int(n)):
        gbox(gV, f"{name}_Panel_{i + 1}{note}", cav, ry(u0 + i * pw, pw), z0, T, pw, z1 - z0, C_DOOR)
    k = -(-(u1 - u0) // RIB_MAX)
    for j in range(int(k) + 1):
        y0 = min(max(u0 + j * (u1 - u0) / k - T / 2, u0), u1 - T)
        y0 = min(max(y0, pipe_zone[0]), pipe_zone[1])   # keep ribs clear of the corner pipes
        gbox(gV, f"{name}_Rib_{j + 1}", 0, ry(y0, T), z0, cav, T, z1 - z0)


splash("Splash_Sink", u_sink, u_stove, BASE_TOP, UPPER_Z)
splash("Splash_Stove", u_stove, u_wpanel, 0, ROOM_H, " (tile or SS sheet over it)")
splash("Splash_Washer", u_wpanel, ROOM_L, BASE_TOP, UPPER_Z, " (removable, pipe access)")
for nm, y in (("Pipe_Open_End", sum(PIPE_U[0]) / 2), ("Pipe_Back_Corner", sum(PIPE_U[1]) / 2)):
    pipe = Part.makeCylinder(PIPE_OD / 2, ROOM_H, App.Vector(PIPE_OD / 2, ry(y, 0), 0))
    gbox(gV, nm + "_4in_PVC", 0, 0, 0, 0, 0, 0, (0.85, 0.85, 0.9), cut=False, shape=pipe)

# ================= ROOM (reference, open front) =================
gR = group("Room", root)
t = WALL_T
gbox(gR, "Floor", -t, 0, -10, ROOM_W + 2 * t, ROOM_L + t, 10, C_FLOOR, cut=False)
gbox(gR, "Wall_Back", -t, ROOM_L, 0, ROOM_W + 2 * t, t, ROOM_H, C_WALL, cut=False)
gbox(gR, "Wall_Left", -t, 0, 0, t, ROOM_L, ROOM_H, C_WALL, cut=False)
gbox(gR, "Wall_Right", ROOM_W, 0, 0, t, ROOM_L, ROOM_H, C_WALL, cut=False)

doc.recompute()

# ---------------- report ----------------
print("Left wall run (from the open front), mm:")
for label, a, b in [("filler", 0, u_fridge), ("fridge bay", u_fridge, u_tall), ("tall panel", u_tall, u_sink),
                    ("sink base", u_sink, u_drawer), ("drawer base", u_drawer, u_stove),
                    ("stove bay", u_stove, u_wpanel), ("washer panel", u_wpanel, u_washer),
                    ("washer bay", u_washer, u_end), ("end panel", u_end, ROOM_L)]:
    print(f"  {label:13s} {a:7.1f} -> {b:7.1f}  ({b - a:6.1f})")
print(f"Counter height {COUNTER_Z} mm, stove platform {STOVE_PLINTH:.0f} mm, washer bay {WASHER_BAY:.0f} mm")

# ---------------- colours + views (GUI only) ----------------
if App.GuiUp:
    import FreeCADGui as Gui
    for name, c in _colours.items():
        doc.getObject(name).ViewObject.ShapeColor = c
    for w in ("Wall_Left", "Wall_Back"):
        doc.getObject(w).ViewObject.Transparency = 70
    v = Gui.activeDocument().activeView()
    v.setAnimationEnabled(False)

    def shot(fname, view, w, h, hide=()):
        for n in hide:
            doc.getObject(n).ViewObject.Visibility = False
        getattr(v, view)()
        v.fitAll()
        Gui.updateGui()
        v.saveImage(os.path.join(OUT_DIR, fname), w, h, "White")
        for n in hide:
            doc.getObject(n).ViewObject.Visibility = True

    # elevation: standing in the room looking at the left wall
    shot("kitchen_v1_elevation.png", "viewRight", 1800, 1000, hide=("Wall_Right", "Wall_Left", "Floor"))
    shot("kitchen_v1_plan.png", "viewTop", 1400, 1400)
    shot("kitchen_v1_iso.png", "viewIsometric", 1600, 1200, hide=("Wall_Right",))
    v.viewIsometric()
    v.fitAll()

# ---------------- save + cut list ----------------
doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))

agg = {}
for mod, part, l, w, th in cut_list:
    key = (mod, part.split("_", 2)[0] + "_" + part.split("_", 2)[-1] if part.startswith("Drawer_") else part, l, w, th)
    agg[key] = agg.get(key, 0) + 1
with open(os.path.join(OUT_DIR, CUT_LIST), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Part", "Qty", "Length_mm", "Width_mm", "Thickness_mm"])
    for (mod, part, l, w, th), q in sorted(agg.items()):
        wr.writerow([mod, part, q, l, w, th])

with open(os.path.join(OUT_DIR, "kitchen_hardware_v1.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Item", "Size_mm", "Qty"])
    for row in hardware:
        wr.writerow(row)

ply = [c for c in cut_list if abs(c[4] - T) < 0.01]
area = sum(l * w for _, _, l, w, _ in ply) / 1e6
print(f"Ply panels: {len(ply)}, area {area:.2f} m2 (~{area / (1.22 * 2.44) * 1.25:.1f} sheets 4x8 incl. 25% waste)")
