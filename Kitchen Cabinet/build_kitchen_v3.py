# Kitchen v3 = v2 + a BACK-WALL run: base cabinets + countertop + hanging (wall) cabinets.
# The left-wall run (REF -> SINK -> STOVE + exhaust -> WASHER) is unchanged from v2: its outlets, drains and the
# hood duct are already installed. The back run starts WASHER_CLEAR past the washer front so the washer door
# and the person loading it keep clear floor in the back corner; the island moves toward the open front to
# keep a BACK_AISLE work aisle in front of the new counter.
# (v2 header follows.)
# Kitchen v2: left-wall run  REF -> SINK -> STOVE -> WASHER  +  island with a top-mount induction cooktop.
# Room: 148" W x 142" L x 92" ceiling, open front (no wall), back / left / right walls.
# All panels 3/4" PVC board (18 mm foam PVC, 4x8 sheets), no laminate; kick-drawer bottoms 6 mm PVC. Units: mm.
# Storage inside the base cabinets is stainless pull-out racks (no ply drawer boxes).
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet/build_kitchen_v3.py").read())
# Change the parameters below and re-run to regenerate the model, cut list and hardware list.
#
# Woodworking workbench ready: every panel is a Part::Box (notches = Part::Cut), so getDimensions (cut list),
# magicMove, magicResizer, showMeasurements etc. work on it. Doors carry the workbench front attributes
# (hinge edge + angle) for "fronts open / close"; drawers are App::Part containers.
# Kitchen_OpenClose.FCMacro toggles all doors + drawers open / closed in one click.
#
# Axes: X = out from the left wall (0 = masonry), Y = room length (0 = open front -> back wall), Z = up.
# Along the wall run, `u` = distance from the open front (ref end) toward the back wall.
#
# Left wall, 3607 mm (142"), from the open front toward the back wall:
#   18 end panel | 30 filler | 950 fridge bay | 18 tall panel | 900 sink base | 400 rack base
#   | 620 stove bay | 18 washer panel | 635 washer bay | 18 end panel  = 3607
# No offset wall: standard 610 base / 330 wall cabinets straight on the masonry. The two 4" PVC pipes
# (tight in the corners at both ends of the run) are hidden where an appliance needs space behind it anyway:
#   - open end : behind the fridge (stands 129 off the wall); the ref tower panels + over-ref cabinet are
#                deeper to match, and a small chase boxes the pipe inside the over-ref cabinet.
#   - back end : behind the washer (hoses); countertop notched; small chase inside the over-washer cabinet.
#                Between the counter and that cabinet the pipe is left open in the corner, painted /
#                wrapped to match the backsplash (no enclosure).

import csv
import os
import FreeCAD as App
import Part

IN = 25.4

# ---------------- room ----------------
ROOM_W = 148 * IN      # X (3759.2)
ROOM_L = 142 * IN      # Y = left wall length (3606.8)
ROOM_H = 92 * IN       # 2336.8
WALL_T = 4.5 * IN

# ---------------- appliances (W x H x D) ----------------
FRIDGE = (36 * IN, 1780, 25 * IN)          # 3 ft x 178 cm x 25 in
STOVE = (24 * IN, 850, 24 * IN)            # 2 ft x 85 cm x 2 ft
WASHER = (600, 850, 550)                   # 60 x 85 x 55 cm front loader, under the counter
SINK = (770, 420)                          # 770 x 420 mm top-mount sink
INDUCTION = (730, 430, 6)                  # 2-zone top-mount induction (glass size), on the island
INDUCTION_CUT = (700, 400)                 # counter cut-out (check the cooktop manual)
INDUCTION_BODY = 60                        # depth of the unit below the counter

# ---------------- construction ----------------
BOARD = 18             # 3/4" PVC board
T = BOARD              # finished panel thickness (no laminate)
GAP = 3                # reveal around doors / fronts

PLINTH_H = 100         # toe kick
PLINTH_SETBACK = 60
KICK_D = 400           # toe-kick drawer depth / runner length
KICK_FLOOR = 10        # toe-kick drawer bottom clearance above the floor
BASE_D = 610           # base depth incl. doors (24")
BASE_TOP = 876         # top of base carcass (34.5")
CTOP_T = 38            # countertop (1.5")  -> counter height 914 (36")
CTOP_D = 635           # 25"
COUNTER_Z = BASE_TOP + CTOP_T

UPPER_D = 330          # wall cabinets incl. doors
UPPER_Z = 1372         # 54": 458 above the counter
UPPER_TOP = 2286       # 90"; 51 mm crown/scribe to the ceiling
HOOD_Z = COUNTER_Z + 700          # hood underside 700 above the cooktop (check the hood manual: 650-750)
HOOD = (560, 280, 180)            # 60 cm built-in telescopic hood: body W x D x H (fits a 584 clear cabinet)
HOOD_VISOR_W = 598                # pull-out visor width (under the cabinet)
HOOD_FLAT_DUCT = (204, 60)        # flat duct W x D (= 150 round equivalent airflow)

# stainless racks: sized for 18 mm-side cabinets -> nominal W needs (W - 36) clear inside;
# with 18 mm PVC sides the rack cabinets are the standard nominal widths
SHELF_PITCH = 320      # one adjustable shelf per ~320 mm of clear cabinet height
RUNNER_CLR = 12.5      # side clearance per side for rack runners
RACK_D = 500           # pull-out rack depth / runner length (571 clear inside a 610 base)
SINK_RACK_D = 450      # under-sink tray stays in front of the drain
RACK_EXTRA = 2 * T - 36   # 0 with 18 mm PVC: standard rack cabinet widths

# ---------------- corner pipes ----------------
PIPE_OD = 114          # 4" PVC, tight in the corner at each end of the run
PIPE_U = [(T + 10, T + 10 + PIPE_OD), (ROOM_L - PIPE_OD, ROOM_L)]   # spans along the run
PIPE_CLR = PIPE_OD + 15                    # 129: appliances stand this far off the wall at the pipe ends

# ---------------- run along the left wall (from the open front: REF first) ----------------
START_AT_OPEN_END = True   # False = ref in the back-wall corner
REF_FILLER = 30        # fridge door clearance at the open-end panel
FRIDGE_BAY = 950       # 18 mm air gap each side of the 914 fridge
SINK_W = 900
RACK_W = 400 + RACK_EXTRA  # 403.2 -> standard "400" rack
STOVE_BAY = 620        # 5 mm each side of the 610 stove
STOVE_PLINTH = COUNTER_Z - STOVE[1]   # 64 mm platform so the cooktop is flush with the counter
TOWER_D = PIPE_CLR + FRIDGE[2] + 20   # 784: ref tower panels, flush just past the fridge doors

u_filler = T
u_fridge = u_filler + REF_FILLER
u_tall = u_fridge + FRIDGE_BAY
u_sink = u_tall + T
u_rack = u_sink + SINK_W
u_stove = u_rack + RACK_W
u_wpanel = u_stove + STOVE_BAY
u_washer = u_wpanel + T
u_end = ROOM_L - T
WASHER_BAY = u_end - u_washer
assert WASHER_BAY >= WASHER[0] + 20 and WASHER[1] <= BASE_TOP - 10, f"washer bay too small: {WASHER_BAY:.0f}"

# ---------------- island ----------------
ISLAND_AISLE = 1100    # run counter edge -> island counter edge (NKBA work aisle >= 1070 for 2 cooks)
ISLAND_OH = 25         # counter overhang on the work side
ISLAND_SEAT_OH = 300   # counter overhang on the seating side (knee space for stools)
ISLAND_END_OH = 20
ISLAND_MODULES = [(450 + RACK_EXTRA, "racks"), (750 + RACK_EXTRA, "induction"), (450 + RACK_EXTRA, "racks")]
STOOLS = 3
BACK_AISLE = 1100      # back-run counter edge -> island end (island moves toward the open front to keep it)

# ---------------- back-wall run (v3) ----------------
WASHER_CLEAR = 915     # 36" clear floor in front of the front-loader washer before the back run starts
PREP_W = 600           # prep counter: base racks + wall cabinet
APPL_W = 900           # appliance station: base racks + appliance garage on the counter + wall cabinet
PANTRY_W = 600         # pantry tower against the right wall, floor to UPPER_TOP, BASE_D deep
GARAGE_D = 400         # appliance garage + the wall cabinet over it (microwave needs ~370 + plug)
PANTRY_PITCH = 350     # pantry shelf spacing
PANTRY_SPLIT = 1372    # pantry lower / upper door split (= wall-cabinet bottom line)

DOC_NAME = "Kitchen_v3"
REV = "v3"
CUT_LIST = "kitchen_cut_list_v3.csv"
HARDWARE = "kitchen_hardware_v3.csv"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet"

# ---------------- colours ----------------
C_CARCASS = (0.93, 0.89, 0.80)
C_DOOR = (0.97, 0.97, 0.95)
C_PLINTH = (0.35, 0.33, 0.30)
C_CTOP = (0.55, 0.55, 0.57)
C_STEEL = (0.78, 0.79, 0.81)
C_METAL = (0.45, 0.45, 0.48)
C_BLACK = (0.10, 0.10, 0.11)
C_WASHER = (0.96, 0.96, 0.98)
C_PIPE = (0.85, 0.85, 0.90)
C_WALL = (0.90, 0.90, 0.88)
C_FLOOR = (0.60, 0.50, 0.40)
C_ISLAND = (0.25, 0.35, 0.45)
C_DRAWER = (0.85, 0.78, 0.65)
C_LED = (1.0, 0.85, 0.30)
C_24V = (0.10, 0.30, 0.90)
C_230V = (0.85, 0.10, 0.10)

# ---------------- helpers ----------------
if App.listDocuments().get(DOC_NAME):
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)
cut_list = []   # (module, part, length, width, thickness)
hardware = []   # (module, item, size, qty)
_colours = {}
_hidden = []    # Part::Cut bases / tools, hidden in the GUI
_cut_idx = {}   # object name -> cut_list row (for notes)


def group(name, parent=None):
    g = doc.addObject("App::DocumentObjectGroup", name)
    if parent:
        parent.addObject(g)
    return g


def gbox(grp, name, x, y, z, dx, dy, dz, colour=C_CARCASS, cut=True, shape=None):
    """Global axis-aligned panel (mm) as a Part::Box = native Woodworking workbench panel
    (getDimensions cut list, magicMove, magicResizer, showMeasurements ... work on it).
    With `shape`: a plain Part::Feature (appliances, baskets, cut counters)."""
    if shape is None:
        o = doc.addObject("Part::Box", name)
        o.Length, o.Width, o.Height = dx, dy, dz
        o.Placement.Base = App.Vector(x, y, z)
    else:
        o = doc.addObject("Part::Feature", name)
        o.Shape = shape
    grp.addObject(o)
    _colours[o.Name] = colour
    if cut:
        dims = sorted([dx, dy, dz], reverse=True)
        cut_list.append([grp.Label, name, round(dims[0], 1), round(dims[1], 1), round(dims[2], 1), ""])
        _cut_idx[o.Name] = len(cut_list) - 1
    return o


def cut_panel(grp, o, tool_shape, why):
    """Notch a panel the Woodworking way: Part::Cut(Base = the Part::Box panel, Tool = hidden shape)."""
    tool = doc.addObject("Part::Feature", o.Name + "_Tool")
    tool.Shape = tool_shape
    c = doc.addObject("Part::Cut", o.Name + "_Cut")
    c.Base, c.Tool = o, tool
    c.Label = o.Label + f" ({why})"
    if o.Name in _cut_idx:
        cut_list[_cut_idx[o.Name]][5] = why + " - see model"
    grp.removeObject(o)
    grp.addObject(c)
    grp.addObject(tool)
    _hidden.extend([o.Name, tool.Name])
    _colours[c.Name] = _colours.get(o.Name, C_CARCASS)
    return c


def make_drawer(grp, name, objs, slide, axis="X"):
    """Group one drawer (front + box / basket) in an App::Part so it slides out as one piece.
    Kitchen_Slide = pull-out distance along X, or along Y when axis = "Y" (sign = opening direction)."""
    p = doc.addObject("App::Part", name)
    grp.addObject(p)
    for o in objs:
        grp.removeObject(o)
        p.addObject(o)
    p.addProperty("App::PropertyFloat", "Kitchen_Slide", "Kitchen", "Pull-out distance along X (mm)")
    p.Kitchen_Slide = slide
    if axis != "X":
        p.addProperty("App::PropertyString", "Kitchen_SlideAxis", "Kitchen", "Pull-out axis (X or Y)")
        p.Kitchen_SlideAxis = axis
    return p


def set_front(o, sgn, hinge_low, back=False):
    """Door hinge attributes read by the Woodworking 'fronts open / close' tool (rotates about Z).
    hinge_low: hinge on the low-Y side (low-X side for a back-wall door, which faces -Y)."""
    if back:
        edge = ("Edge3", -90) if hinge_low else ("Edge7", 90)
    else:
        edge = {(1, True): ("Edge1", -90), (1, False): ("Edge3", 90),
                (-1, True): ("Edge5", 90), (-1, False): ("Edge7", -90)}[(sgn, hinge_low)]
    for prop, typ, val in (("Woodworking_Type", "App::PropertyString", "Front"),
                           ("Woodworking_Open", "App::PropertyBool", True),
                           ("Woodworking_OpenObj", "App::PropertyString", o.Name),
                           ("Woodworking_OpenEdge", "App::PropertyString", edge[0]),
                           ("Woodworking_OpenAxis", "App::PropertyString", "Z"),
                           ("Woodworking_OpenAngleStep", "App::PropertyFloat", edge[1])):
        o.addProperty(typ, prop, "Woodworking")
        setattr(o, prop, val)


def ry(u, du):
    """Room Y of a span [u, u + du] along the wall run (u = 0 at the open front, REF end)."""
    return u if START_AT_OPEN_END else ROOM_L - u - du


def wbox(grp, name, u, a, d, z, du, dd, dz, colour=C_CARCASS, cut=True):
    """Box on the wall run. u/du along the run from the ref end, d/dd out from the wall."""
    return gbox(grp, name, d, ry(u + a, du), z, dd, du, dz, colour, cut)


class Module:
    """One modular cabinet at position u (width w). Local a = along the run, d = from the cabinet back.
    Wall run: back on the masonry (x0 = 0), fronts face +X.  Island: back at x0, fronts face -X (sgn = -1).
    Back-wall run (back=True): u = room X of the cabinet's low-X side, a along +X, fronts face -Y."""

    def __init__(self, parent, name, u, w, x0=0, sgn=1, on_run=True, back=False):
        self.g, self.u, self.w = group(name, parent), u, w
        self.x0, self.sgn, self.on_run, self.back = x0, sgn, on_run, back
        self.objs = []

    def place(self, a, d, da, dd):
        """Global (x, y, dx, dy) of a local box."""
        if self.back:
            return self.u + a, ROOM_L - d - dd, da, dd
        x = self.x0 + d if self.sgn > 0 else self.x0 - d - dd
        y = ry(self.u + a, da) if self.on_run else self.u + a
        return x, y, dd, da

    def drawer(self, name, objs, dist):
        if self.back:
            return make_drawer(self.g, name, objs, -dist, "Y")
        return make_drawer(self.g, name, objs, self.sgn * dist)

    def box(self, name, a, d, z, da, dd, dz, colour=C_CARCASS, cut=True):
        x, y, dx, dy = self.place(a, d, da, dd)
        o = gbox(self.g, name, x, y, z, dx, dy, dz, colour, cut)
        self.objs.append(o)
        return o

    def carcass(self, z, h, depth, back=True, stretchers=False):
        """Sides full height, bottom between the sides, top (or two 100 mm stretchers), 18 mm back."""
        w = self.w
        inner = depth - (T if back else 0)
        dfront = T if back else 0
        self.box("Side_A", 0, dfront, z, T, inner, h)
        self.box("Side_B", w - T, dfront, z, T, inner, h)
        self.box("Bottom", T, dfront, z, w - 2 * T, inner, T)
        if stretchers:
            self.box("Stretcher_Front", T, depth - 100, z + h - T, w - 2 * T, 100, T)
            self.box("Stretcher_Back", T, dfront, z + h - T, w - 2 * T, 100, T)
        else:
            self.box("Top", T, dfront, z + h - T, w - 2 * T, inner, T)
        if back:
            self.box("Back", 0, 0, z, w, T, h)

    def plinth(self, depth=BASE_D, kick=False):
        """Plinth under a base cabinet. kick=True: the toe-kick space is a push-to-open drawer
        (front = the plinth face, box on low-profile runners between two plinth side panels)."""
        w = self.w
        fd = depth - PLINTH_SETBACK - T                 # plinth / kick-drawer front plane
        self.box("Plinth_Back", 0, 60, 0, w, T, PLINTH_H, C_PLINTH)
        if not kick:
            self.box("Plinth_Front", 0, fd, 0, w, T, PLINTH_H, C_PLINTH)
            return
        self.box("Plinth_Side_A", 0, 60 + T, 0, T, fd - 60 - T, PLINTH_H, C_PLINTH)
        self.box("Plinth_Side_B", w - T, 60 + T, 0, T, fd - 60 - T, PLINTH_H, C_PLINTH)
        kick = [self.box("Kick_DrawerFront", GAP / 2, fd, KICK_FLOOR, w - GAP, T, PLINTH_H - KICK_FLOOR - GAP, C_PLINTH)]
        bw = w - 2 * T - 2 * RUNNER_CLR
        a0, d0 = T + RUNNER_CLR, fd - KICK_D
        bz, bh = KICK_FLOOR + 6, PLINTH_H - KICK_FLOOR - GAP - 6 - 8
        kick += [self.box("Kick_Side_A", a0, d0, bz, T, KICK_D, bh, C_DRAWER),
                 self.box("Kick_Side_B", a0 + bw - T, d0, bz, T, KICK_D, bh, C_DRAWER),
                 self.box("Kick_Back", a0 + T, d0, bz, bw - 2 * T, T, bh, C_DRAWER),
                 self.box("Kick_Inner_Front", a0 + T, fd - T, bz, bw - 2 * T, T, bh, C_DRAWER),
                 self.box("Kick_Bottom_6mm_PVC", a0, d0, KICK_FLOOR, bw, KICK_D, 6, C_DRAWER)]
        self.drawer("Drawer_ToeKick", kick, KICK_D * 0.75)
        for side, ra in (("A", a0 - RUNNER_CLR), ("B", a0 + bw)):
            rx, ry_, rdx, rdy = self.place(ra, d0, RUNNER_CLR, KICK_D)
            gbox(self.g, f"Kick_Runner_{side}", rx, ry_, bz + 10, rdx, rdy, 35, C_METAL, cut=False)
        hardware.append((self.g.Label, f"Toe-kick drawer runner pair {KICK_D} mm, low profile, push-to-open", "-", 1))

    def doors(self, n, z, h, front_d, label="Door", colour=C_DOOR):
        dw = self.w / n
        for i in range(n):
            o = self.box(f"{label}_{i + 1}", i * dw + GAP / 2, front_d, z + GAP / 2, dw - GAP, T, h - GAP, colour)
            set_front(o, self.sgn, i == 0, self.back)    # 2 doors: hinges on the outer sides; 1 door: hinge on the low-Y side

    def shelf(self, name, z, depth, setback=20):
        self.box(name, T, T, z, self.w - 2 * T, depth - 2 * T - setback, T)

    def basket(self, name, a, d, z, da, dd, h, item, wall=2, runners=False):
        """Stainless wire basket / tray (open-top shell, not in the cut list) -> hardware list.
        runners: pull-out on a pair of full-extension soft-close side runners (in the RUNNER_CLR gaps)."""
        x, y, dx, dy = self.place(a, d, da, dd)
        shell = Part.makeBox(dx, dy, h, App.Vector(x, y, z)).cut(
            Part.makeBox(dx - 2 * wall, dy - 2 * wall, h, App.Vector(x + wall, y + wall, z + wall)))
        o = gbox(self.g, name, 0, 0, 0, 0, 0, 0, C_STEEL, cut=False, shape=shell)
        hardware.append((self.g.Label, item, f"{da:.0f} W x {dd:.0f} D x {h:.0f} H", 1))
        if runners:
            for side, ra in (("A", a - RUNNER_CLR), ("B", a + da)):
                rx, ry_, rdx, rdy = self.place(ra, d, RUNNER_CLR, dd)
                gbox(self.g, f"{name}_Runner_{side}", rx, ry_, z + 10, rdx, rdy, 40, C_METAL, cut=False)
            hardware.append((self.g.Label, f"Full-extension soft-close runner pair, {dd:.0f} mm", "-", 1))
        return o


def base_cabinet(parent, name, u, w, kind, colour=C_DOOR, **frame):
    """610 base on a plinth; inside is free for stainless pull-out racks."""
    m = Module(parent, name, u, w, **frame)
    cd = BASE_D - T
    m.plinth(kick=True)
    h = BASE_TOP - PLINTH_H
    inner = w - 2 * T
    rack_w = inner - 2 * RUNNER_CLR
    size = f"{round((inner + 36) / 50) * 50:.0f} cabinet size, {inner:.0f} clear, {RACK_D} runners"

    def tiers(spec, z0):
        fz = z0
        for i, (fh, bh, item) in enumerate(spec):
            fr = m.box(f"DrawerFront_{i + 1}", GAP / 2, cd, fz + GAP / 2, w - GAP, T, fh - GAP, colour)
            if bh:
                bk = m.basket(f"SS_Basket_{i + 1}", T + RUNNER_CLR, cd - RACK_D, fz + 30, rack_w, RACK_D,
                              min(bh, fh - 60), f"{item} ({size})", runners=True)
                m.drawer(f"Drawer_{i + 1}", [fr, bk], RACK_D * 0.75)
            fz += fh

    if kind == "sink":
        m.carcass(PLINTH_H, h, cd, back=False, stretchers=True)   # open back for plumbing
        m.doors(2, PLINTH_H, h, cd, colour=colour)
        tray = m.basket("SS_UnderSink_Tray", T + RUNNER_CLR, cd - SINK_RACK_D, PLINTH_H + T + 10, rack_w,
                        SINK_RACK_D, 120, "Under-sink pull-out tray (door-mounted cabinet)", runners=True)
        m.drawer("Drawer_UnderSink", [tray], SINK_RACK_D * 0.75)
    elif kind == "racks":
        m.carcass(PLINTH_H, h, cd, stretchers=True)
        tiers([(h * 0.40, 200, "Pot / pan basket"), (h * 0.35, 150, "Bowl + plate basket"),
               (h * 0.25, 70, "Cutlery / utensil tray")], PLINTH_H)
    elif kind == "induction":
        # top 120 mm stays free under the cooktop (unit body + air gap): fixed vent front, no drawer
        m.carcass(PLINTH_H, h, cd, stretchers=True)
        vent = 120
        tiers([((h - vent) / 2, 250, "Deep pot basket"), ((h - vent) / 2, 200, "Pot / pan basket"),
               (vent, 0, "")], PLINTH_H)
        hardware.append((m.g.Label, "Vent grille / 6 mm gap behind the top fixed front (induction air)", "-", 1))
    elif kind == "shelf":                                       # 2 doors, 1 adjustable shelf (pots, small appliances)
        m.carcass(PLINTH_H, h, cd, stretchers=True)
        m.shelf("Shelf_1", PLINTH_H + T + (h - 3 * T) / 2, cd)
        hardware.append((m.g.Label, "Shelf pins (5 mm, 32 mm system)", "-", 4))
        m.doors(2, PLINTH_H, h, cd, colour=colour)
    return m


def wall_cabinet(parent, name, u, w, z0, z1, depth=UPPER_D, ndoors=2, pipe=None, shelf=True, **frame):
    """Wall cabinet on the masonry. pipe=(u0, u1): a corner pipe runs through its back corner -> the side,
    back, top, bottom and shelf are notched around it and a small L-shaped chase (2 panels) boxes it in."""
    m = Module(parent, name, u, w, **frame)
    cd = depth - T
    m.carcass(z0, z1 - z0, cd)
    if shelf:                                    # adjustable shelves (pins), ~300 mm compartments
        clear = z1 - z0 - 2 * T
        n = int(clear // SHELF_PITCH)
        for k in range(n):
            m.shelf(f"Shelf_{k + 1}", z0 + T + (k + 1) * (clear - n * T) / (n + 1) + k * T, cd)
        if n:
            hardware.append((m.g.Label, "Shelf pins (5 mm, 32 mm system)", "-", 4 * n))
    m.doors(ndoors, z0, z1 - z0, cd)
    if pipe:
        cu0, cu1 = max(pipe[0] - 10, u), min(pipe[1] + 10, u + w)   # chase interior along the run
        cdp = PIPE_OD + 10                                          # chase interior depth from the wall
        at_start = cu0 <= u + 1
        nu0, nu1 = (cu0, cu1 + T) if at_start else (cu0 - T, cu1)
        notch = Part.makeBox(cdp + T, nu1 - nu0, z1 - z0, App.Vector(0, ry(nu0, nu1 - nu0), z0))
        for o in list(m.objs):
            if o.Shape.common(notch).Volume > 1:
                cut_panel(m.g, o, notch, "notched for pipe")
        m.box("Pipe_Chase_Front", nu0 - u, cdp, z0, nu1 - nu0, T, z1 - z0)
        m.box("Pipe_Chase_Side", (cu1 if at_start else cu0 - T) - u, 0, z0, T, cdp, z1 - z0)
    return m


root = group(DOC_NAME)
root.addProperty("App::PropertyBool", "Kitchen_Open", "Kitchen", "Fronts open (toggled by Kitchen_OpenClose)")
root.Kitchen_Open = False
run = group("Left_Wall_Run", root)

# ================= REF TOWER =================
gF = group("Ref_Tower", run)
wbox(gF, "End_Panel_Ref", 0, 0, 0, 0, T, TOWER_D, UPPER_TOP, C_DOOR)          # finished end at the open side
wbox(gF, "Filler_Ref", u_filler, 0, TOWER_D - T, 0, REF_FILLER, T, UPPER_TOP, C_DOOR)
fw, fh, fd = FRIDGE
wbox(gF, "Ref_3ft", u_fridge + (FRIDGE_BAY - fw) / 2, 0, PIPE_CLR, 0, fw, fd, fh, C_STEEL, cut=False)
wbox(gF, "Tall_Panel", u_tall, 0, 0, 0, T, TOWER_D, UPPER_TOP, C_DOOR)
over_z = max(fh + 40, 1829)
wall_cabinet(gF, "Over_Ref_Cabinet", u_fridge, FRIDGE_BAY, over_z, UPPER_TOP, depth=TOWER_D, pipe=PIPE_U[0])

# ================= SINK + RACK BASE + COUNTER =================
gS = group("Sink_Counter", run)
base_cabinet(gS, "Base_Sink_900", u_sink, SINK_W, "sink")
base_cabinet(gS, f"Base_Racks_{RACK_W:.0f}", u_rack, RACK_W, "racks")
ctop_len = SINK_W + RACK_W
ctop = Part.makeBox(CTOP_D, ctop_len, CTOP_T, App.Vector(0, ry(u_sink, ctop_len), BASE_TOP))
sw, sd = SINK
sink_y = ry(u_sink + SINK_W / 2 - sw / 2, sw)
sink_x = CTOP_D - 60 - sd                                  # 60 mm from the counter front edge
ctop = ctop.cut(Part.makeBox(sd, sw, CTOP_T + 2, App.Vector(sink_x, sink_y, BASE_TOP - 1)))
gbox(gS, "Countertop", 0, 0, 0, 0, 0, 0, C_CTOP, cut=False, shape=ctop)
cut_list.append(("Sink_Counter", "Countertop (solid surface / granite, sink cut-out 770x420)",
                 round(ctop_len, 1), CTOP_D, CTOP_T))
gbox(gS, "Sink_770x420", 0, 0, 0, 0, 0, 0, C_STEEL, cut=False,
     shape=Part.makeBox(sd + 20, sw + 20, 3, App.Vector(sink_x - 10, sink_y - 10, COUNTER_Z)).fuse(
         Part.makeBox(sd - 20, sw - 20, 200, App.Vector(sink_x + 10, sink_y + 10, COUNTER_Z - 200))))

# ================= STOVE =================
gC = group("Stove_Bay", run)
sw_, sh_, sd_ = STOVE
sy = ry(u_stove + STOVE_BAY / 2 - sw_ / 2, sw_)
gbox(gC, "Stove_Platform", 0, sy, 0, sd_, sw_, STOVE_PLINTH, C_PLINTH)
gbox(gC, "Stove_2ft", 0, sy, STOVE_PLINTH, sd_, sw_, sh_, C_STEEL, cut=False)
gbox(gC, "Stove_Top", 30, sy + 20, COUNTER_Z, sd_ - 60, sw_ - 40, 8, C_BLACK, cut=False)
# concealed hood: built-in telescopic hood in the bottom of a wall cabinet over the stove; only the slim
# pull-out visor shows under the door. A flat 204x60 duct runs up the cabinet back; 2 shelves in front of it.
mh = wall_cabinet(gC, f"Upper_Hood_{STOVE_BAY}", u_stove, STOVE_BAY, HOOD_Z, UPPER_TOP, ndoors=1, shelf=False)
hw, hd, hh = HOOD
ha = (STOVE_BAY - hw) / 2
hood_box = Part.makeBox(hd, hw, hh, App.Vector(T, ry(u_stove + ha, hw), HOOD_Z))
for o in list(mh.objs):                              # bottom panel cut out for the hood
    if o.Shape.common(hood_box).Volume > 1:
        cut_panel(mh.g, o, hood_box, "hood cut-out")
gbox(gC, "Hood_Telescopic_60cm", 0, 0, 0, 0, 0, 0, C_STEEL, cut=False, shape=hood_box)
gbox(gC, "Hood_Visor", T + hd - 10, ry(u_stove + (STOVE_BAY - HOOD_VISOR_W) / 2, HOOD_VISOR_W), HOOD_Z - 15, 10,
     HOOD_VISOR_W, 15, C_STEEL, cut=False)
# flat duct tight against the cabinet back (out of the way); shelves use the full width in front of it
fdw, fdd = HOOD_FLAT_DUCT
duct_y = ry(u_stove + STOVE_BAY / 2 - fdw / 2, fdw)
gbox(gC, "Hood_Duct_Flat_204x60", T, duct_y, HOOD_Z + hh, fdd, fdw, ROOM_H - HOOD_Z - hh, C_PIPE, cut=False)
sd0 = T + fdd + 5                                       # shelves start in front of the duct
s_clear = UPPER_TOP - T - (HOOD_Z + hh + 10)
for k, z in enumerate([HOOD_Z + hh + 10, HOOD_Z + hh + 10 + s_clear / 2]):
    mh.box(f"Shelf_{k + 1}", T, sd0, z, STOVE_BAY - 2 * T, UPPER_D - T - sd0 - 5, T)   # 1st = floor over the hood
hardware.append((mh.g.Label, "Flat duct 204x60 + 150 round-to-flat adapter, up the cabinet back to the ceiling "
                 "(cut-out in the cabinet top)", "-", 1))
hardware.append((mh.g.Label, "Shelf pins (5 mm, 32 mm system)", "-", 4))
hardware.append((mh.g.Label, "Built-in telescopic range hood 60 cm (body <= 560 W for a 584 clear cabinet), ducted, 150 outlet",
                 f"{hw} W x {hd} D x {hh} H", 1))

# ================= WASHING MACHINE =================
gW = group("Washer_Bay", run)
wbox(gW, "Panel_Stove_Side", u_wpanel, 0, 0, 0, T, BASE_D, BASE_TOP, C_DOOR)
wbox(gW, "End_Panel", u_end, 0, PIPE_CLR - 5, 0, T, BASE_D - PIPE_CLR + 5, BASE_TOP, C_DOOR)  # clear of the pipe
wbox(gW, "Back_Rail", u_washer, 0, PIPE_CLR - 5, BASE_TOP - 100, WASHER_BAY, T, 100)          # in front of the pipe
wbox(gW, "Rail_Front", u_washer, 0, BASE_D - 100, BASE_TOP - T, WASHER_BAY, 100, T)
ww, wh, wd = WASHER
wbox(gW, "Washer_60x55", u_washer + (WASHER_BAY - ww) / 2, 0, PIPE_CLR, 0, ww, wd, wh, C_WASHER, cut=False)
w_ctop = ROOM_L - u_wpanel
pipe_notch = Part.makeBox(PIPE_OD + 10 + T, PIPE_U[1][1] - PIPE_U[1][0] + 10 + T, CTOP_T + 2,
                          App.Vector(0, ry(PIPE_U[1][0] - 10 - T, PIPE_OD + 10 + T), BASE_TOP - 1))
wshape = Part.makeBox(CTOP_D, w_ctop, CTOP_T, App.Vector(0, ry(u_wpanel, w_ctop), BASE_TOP)).cut(pipe_notch)
gbox(gW, "Countertop_Washer", 0, 0, 0, 0, 0, 0, C_CTOP, cut=False, shape=wshape)
cut_list.append(("Washer_Bay", "Countertop (solid surface / granite, corner notch 144x144 for pipe)",
                 round(w_ctop, 1), CTOP_D, CTOP_T))
hardware.append(("Washer_Bay", "Paint / wrap the exposed pipe (counter -> wall cabinet) to match the backsplash", "458 H", 1))
wall_cabinet(gW, "Upper_Over_Washer", u_washer, ROOM_L - u_washer, UPPER_Z, UPPER_TOP, pipe=PIPE_U[1])

# ================= WALL CABINETS over the counter =================
gU = group("Wall_Cabinets", run)
mu = wall_cabinet(gU, "Upper_Sink_900", u_sink, SINK_W, UPPER_Z, UPPER_TOP, shelf=False)
# 2-tier stainless dish drainer above the sink: plates low, cups / bowls high, drip tray under
dr_w, dr_d = SINK_W - 2 * T - 10, UPPER_D - 2 * T - 20
mu.basket("SS_Drip_Tray", T + 5, T, UPPER_Z + T + 5, dr_w, dr_d, 25, "Dish drainer drip tray")
mu.basket("SS_Plate_Rack", T + 5, T, UPPER_Z + T + 60, dr_w, dr_d, 120, "Dish drainer, plate tier (900 cabinet)")
mu.basket("SS_Cup_Rack", T + 5, T, UPPER_Z + 520, dr_w, dr_d, 80, "Dish drainer, cup / bowl tier (900 cabinet)")
wall_cabinet(gU, f"Upper_{RACK_W:.0f}", u_rack, RACK_W, UPPER_Z, UPPER_TOP, ndoors=1)

# crown / ceiling scribe over the full run (cut to fit on site)
crown_h = ROOM_H - UPPER_TOP
gK = group("Scribe_Strips", run)
wbox(gK, "Crown_Ref", 0, 0, TOWER_D - T, UPPER_TOP, u_tall + T, T, crown_h, C_DOOR)
wbox(gK, "Crown_Uppers", u_sink, 0, UPPER_D - T, UPPER_TOP, SINK_W + RACK_W + STOVE_BAY + T, T, crown_h, C_DOOR)
wbox(gK, "Crown_Washer", u_washer, 0, UPPER_D - T, UPPER_TOP, WASHER_BAY + T, T, crown_h, C_DOOR)

gP = group("Corner_Pipes_4in_PVC", run)
for nm, (p0, p1) in (("Pipe_Open_End", PIPE_U[0]), ("Pipe_Back_Corner", PIPE_U[1])):
    yc = ry((p0 + p1) / 2, 0)
    gbox(gP, nm, 0, 0, 0, 0, 0, 0, C_PIPE, cut=False,
         shape=Part.makeCylinder(PIPE_OD / 2, ROOM_H, App.Vector(PIPE_OD / 2, yc, 0)))

# ================= BACK-WALL RUN (v3): prep counter | appliance station | pantry =================
# Fronts face -Y (toward the open front). From the washer side:
#   18 end panel | 600 prep base (racks) + wall cabinet | 900 appliance station | 600 pantry (floor to 90") | filler
# Appliance station: base with deep racks (mixer, blender, food processor) under the counter; on the counter an
# APPLIANCE GARAGE (coffee maker, microwave, mixer / toaster) between the counter and a 400-deep wall cabinet,
# 2 doors, outlets inside; its doors line up with the wall cabinet above.
# Starts WASHER_CLEAR past the washer front: the corner in front of the washer stays open floor.
gB = group("Back_Wall_Run", root)
xb0 = PIPE_CLR + WASHER[2] + WASHER_CLEAR          # end panel (washer side)
xb_prep = xb0 + T
xb_app = xb_prep + PREP_W
xb_pan = xb_app + APPL_W
xb_fill = xb_pan + PANTRY_W
BACK_FILLER = ROOM_W - xb_fill                     # door / drawer clearance at the right wall
assert 20 <= BACK_FILLER <= 150, f"back-run filler {BACK_FILLER:.0f}: change PREP_W / APPL_W / PANTRY_W"
gBB = group("Back_Base", gB)
gbox(gBB, "End_Panel_Back_Base", xb0, ROOM_L - BASE_D, 0, T, BASE_D, BASE_TOP, C_DOOR)
base_cabinet(gBB, f"Back_Prep_Racks_{PREP_W}", xb_prep, PREP_W, "racks", back=True)
base_cabinet(gBB, f"Back_Appliance_Racks_{APPL_W}", xb_app, APPL_W, "racks", back=True)
b_ctop = xb_pan - xb0                               # counter stops against the pantry side
gbox(gBB, "Countertop_Back", 0, 0, 0, 0, 0, 0, C_CTOP, cut=False,
     shape=Part.makeBox(b_ctop, CTOP_D, CTOP_T, App.Vector(xb0, ROOM_L - CTOP_D, BASE_TOP)))
cut_list.append(("Back_Base", "Countertop (solid surface / granite, back wall, no cut-outs)",
                 round(b_ctop, 1), CTOP_D, CTOP_T))
hardware.append(("Back_Base", "Backsplash outlet over the prep counter (electrician, new circuit)", "-", 1))

# --- appliance garage on the counter ---
gA = group("Appliance_Station", gB)
mg = Module(gA, f"Appliance_Garage_{APPL_W}", xb_app, APPL_W, back=True)
gh = UPPER_Z - COUNTER_Z                            # 458 clear: counter -> wall cabinet bottom
gd = GARAGE_D - T                                   # sides stop behind the doors
mg.box("Side_A", 0, 0, COUNTER_Z, T, gd, gh)
mg.box("Side_B", APPL_W - T, 0, COUNTER_Z, T, gd, gh)
mg.doors(2, COUNTER_Z, gh, gd)
hardware.append((mg.g.Label, "Appliance-garage outlets: double socket x2 on the back wall inside the garage "
                 "(coffee maker, microwave, mixer) - electrician, own 20 A circuit for the microwave", "-", 2))
hardware.append((mg.g.Label, "Garage doors: open the doors while the microwave / coffee maker runs (heat + steam); "
                 "max microwave ~ 500 W x 300 H x 370 D", "-", 1))
wall_cabinet(gA, f"Upper_Appliance_{APPL_W}", xb_app, APPL_W, UPPER_Z, UPPER_TOP, depth=GARAGE_D, back=True)

# --- pantry: floor to 90", 610 deep, adjustable shelves, 2 stacked doors hinged on the wall side ---
gPa = group("Pantry", gB)
mp = Module(gPa, f"Pantry_{PANTRY_W}", xb_pan, PANTRY_W, back=True)
cdp_ = BASE_D - T
mp.plinth(kick=True)
ph = UPPER_TOP - PLINTH_H
mp.carcass(PLINTH_H, ph, cdp_)
clear = ph - 2 * T
n_sh = int(clear // PANTRY_PITCH)
for k in range(n_sh):
    mp.shelf(f"Shelf_{k + 1}", PLINTH_H + T + (k + 1) * (clear - n_sh * T) / (n_sh + 1) + k * T, cdp_)
hardware.append((mp.g.Label, "Shelf pins (5 mm, 32 mm system)", "-", 4 * n_sh))
for nm, z0, z1 in (("Door_Lower", PLINTH_H, PANTRY_SPLIT), ("Door_Upper", PANTRY_SPLIT, UPPER_TOP)):
    o = mp.box(nm, GAP / 2, cdp_, z0 + GAP / 2, PANTRY_W - GAP, T, z1 - z0 - GAP, C_DOOR)
    set_front(o, 1, False, back=True)              # hinge on the right-wall side: opens toward the counter
hardware.append((mp.g.Label, "Door-mounted pantry racks (optional, lower door): check shelf setback", "-", 1))

# --- wall cabinet over the prep counter, end panel, fillers, crown ---
gBU = group("Back_Wall_Cabinets", gB)
gbox(gBU, "End_Panel_Back_Upper", xb0, ROOM_L - UPPER_D, UPPER_Z, T, UPPER_D, UPPER_TOP - UPPER_Z, C_DOOR)
wall_cabinet(gBU, f"Upper_Prep_{PREP_W}", xb_prep, PREP_W, UPPER_Z, UPPER_TOP, ndoors=1, back=True)
back_uppers = [(f"Upper_Prep_{PREP_W}", xb_prep, PREP_W, UPPER_D),
               (f"Upper_Appliance_{APPL_W}", xb_app, APPL_W, GARAGE_D)]     # strip under the appliance cabinet
fd_b = BASE_D - PLINTH_SETBACK - T                                           # lights the garage inside
gbox(gPa, "Filler_Pantry", xb_fill, ROOM_L - BASE_D, PLINTH_H, BACK_FILLER, T, UPPER_TOP - PLINTH_H, C_DOOR)
gbox(gPa, "Filler_Pantry_Plinth", xb_fill, ROOM_L - fd_b - T, 0, BACK_FILLER, T, PLINTH_H, C_PLINTH)
for nm, x0_, x1_, dep in (("Crown_Back_Prep", xb0, xb_app, UPPER_D), ("Crown_Back_Appliance", xb_app, xb_pan, GARAGE_D),
                          ("Crown_Pantry", xb_pan, ROOM_W, BASE_D)):
    gbox(gK, nm, x0_, ROOM_L - dep, UPPER_TOP, x1_ - x0_, T, crown_h, C_DOOR)

# ================= ISLAND =================
# Work side (cabinet fronts) faces the wall run; seating overhang on the far side.
gI = group("Island", root)
cab_len = sum(w for w, _ in ISLAND_MODULES) + 2 * T
isl_len = cab_len + 2 * ISLAND_END_OH
ctop_x0 = CTOP_D + ISLAND_AISLE                    # work-side counter edge
front_x = ctop_x0 + ISLAND_OH                      # cabinet door faces
back_x = front_x + BASE_D                          # cabinet backs
ctop_x1 = back_x + T + ISLAND_SEAT_OH              # seating-side counter edge
isl_y0 = min(ROOM_L / 2 - isl_len / 2,             # centred along the room (v2) ...
             ROOM_L - CTOP_D - BACK_AISLE - isl_len)  # ... unless that crowds the back-run counter (v3)
cab_y0 = isl_y0 + ISLAND_END_OH
gbox(gI, "Island_End_Panel_A", front_x, cab_y0, 0, BASE_D + T, T, BASE_TOP, C_ISLAND)
gbox(gI, "Island_End_Panel_B", front_x, cab_y0 + cab_len - T, 0, BASE_D + T, T, BASE_TOP, C_ISLAND)
gbox(gI, "Island_Back_Panel (seating side)", back_x, cab_y0 + T, 0, T, cab_len - 2 * T, BASE_TOP, C_ISLAND)
y = cab_y0 + T
cook_y = None
for i, (w, kind) in enumerate(ISLAND_MODULES):
    base_cabinet(gI, f"Island_{i + 1}_{kind.title()}_{w:.0f}", y, w, kind, colour=C_ISLAND,
                 x0=back_x, sgn=-1, on_run=False)
    if kind == "induction":
        cook_y = y + w / 2
    y += w
iw, idp, it = INDUCTION
icw, icd = INDUCTION_CUT
cook_x = front_x + BASE_D / 2 - idp / 2            # centred over the cabinet depth
ishape = Part.makeBox(ctop_x1 - ctop_x0, isl_len, CTOP_T, App.Vector(ctop_x0, isl_y0, BASE_TOP)).cut(
    Part.makeBox(icd, icw, CTOP_T + 2, App.Vector(cook_x + (idp - icd) / 2, cook_y - icw / 2, BASE_TOP - 1)))
gbox(gI, "Island_Countertop", 0, 0, 0, 0, 0, 0, C_CTOP, cut=False, shape=ishape)
cut_list.append(("Island", f"Countertop (solid surface / granite, cooktop cut-out {icw}x{icd})",
                 round(isl_len, 1), round(ctop_x1 - ctop_x0, 1), CTOP_T))
gbox(gI, "Induction_Glass", cook_x, cook_y - iw / 2, COUNTER_Z, idp, iw, it, C_BLACK, cut=False)
gbox(gI, "Induction_Body", cook_x + (idp - icd) / 2 + 5, cook_y - icw / 2 + 5, COUNTER_Z - INDUCTION_BODY,
     icd - 10, icw - 10, INDUCTION_BODY, C_BLACK, cut=False)
hardware.append(("Island", "Induction power: dedicated circuit in floor conduit to the island", "-", 1))
for i in range(STOOLS):
    sy_ = isl_y0 + isl_len * (i + 1) / (STOOLS + 1)
    sx = ctop_x1 - ISLAND_SEAT_OH / 2
    seat = Part.makeCylinder(190, 40, App.Vector(sx, sy_, 650))
    leg = Part.makeCylinder(25, 650, App.Vector(sx, sy_, 0))
    gbox(gI, f"Stool_{i + 1}", 0, 0, 0, 0, 0, 0, C_BLACK, cut=False, shape=seat.fuse(leg))

# ================= LED LIGHTING + WIRING =================
# 24 V COB LED strip in aluminium profiles with diffuser. Three channels, each with its own driver:
#   1. under-cabinet task light (front edge of the wall-cabinet bottoms) - wall switch in the backsplash
#      driver: inside the over-ref cabinet; 24 V cable runs on top of the wall cabinets (hidden by the
#      crown strip) and drops down each cabinet's back corner to its strip
#   2. toe-kick, wall run - motion sensor; driver inside the sink base (open back), fed from its outlet
#   3. toe-kick, island work side - motion sensor; driver behind the baskets in island cabinet 1, fed from
#      the island floor conduit (same conduit run as the induction circuit, separate cable)
# The hood cabinet has no strip: the hood has its own light.
gL = group("Lighting_LED", root)
LED_W, LED_H, LED_WPM = 16, 7, 10        # profile width / height (mm), strip watts per metre
led_len = {1: 0, 2: 0, 3: 0, 4: 0}
cable_len = {"24V": 0, "230V": 0}


def led(name, ch, x, y, z, dx, dy, grp=gL):
    gbox(grp, name, x, y, z, dx, dy, LED_H, C_LED, cut=False)
    led_len[ch] += max(dx, dy)


def cable(name, pts, kind, grp=gL):
    """Cable route through the points (global), drawn as a tube."""
    shape = None
    for p0, p1 in zip(pts, pts[1:]):
        a, b = App.Vector(*p0), App.Vector(*p1)
        if (b - a).Length < 1:
            continue
        seg = Part.makeCylinder(6, (b - a).Length, a, b - a)      # drawn 12 mm thick to read in the views
        shape = seg if shape is None else shape.fuse(seg)
        cable_len[kind] += (b - a).Length
    gbox(grp, name, 0, 0, 0, 0, 0, 0, C_24V if kind == "24V" else C_230V, cut=False, shape=shape)


def Y(u):
    return ry(u, 0)


# --- channel 1: under-cabinet strips ---
x_led = UPPER_D - T - 40 - LED_W                      # 40 mm behind the door, light falls on the counter front
top_z = UPPER_TOP + 10                                # cable tray on top of the wall cabinets
cx = 95                                               # cable line on the cabinet tops, in front of the flat duct
drv1 = (60, Y(u_tall - 80), over_z + T + 15)
gbox(gL, "Driver_1_UnderCabinet", 30, Y(u_tall - 30) - 0, over_z + T, 60, 200, 30, C_METAL, cut=False,
     shape=Part.makeBox(60, 200, 30, App.Vector(30, ry(u_tall - 230, 200), over_z + T)))
cable("Cable_24V_Ch1_Riser", [drv1, (cx, drv1[1], drv1[2]), (cx, drv1[1], top_z)], "24V")
under = [("Upper_Sink_900", u_sink, SINK_W), (f"Upper_{RACK_W:.0f}", u_rack, RACK_W),
         ("Upper_Over_Washer", u_washer, ROOM_L - u_washer)]
cable("Cable_24V_Ch1_Top", [(cx, drv1[1], top_z), (cx, Y(under[-1][1] + T + 30), top_z)], "24V")
for nm, u0, w in under:
    a0 = u0 + T + 5
    led(f"LED_{nm}", 1, x_led, ry(a0, w - 2 * T - 10), UPPER_Z - LED_H, LED_W, w - 2 * T - 10)
    ud = u0 + T + 30                                  # drop in the back corner on the stove / ref side
    cable(f"Cable_24V_Ch1_{nm}", [(cx, Y(ud), top_z), (cx, Y(ud), UPPER_Z + T + 3),
                                  (x_led + LED_W / 2, Y(ud), UPPER_Z + T + 3),
                                  (x_led + LED_W / 2, Y(ud), UPPER_Z - LED_H / 2)], "24V")
sw_u = u_sink + 150                                   # wall switch in the backsplash, near the sink
gbox(gL, "Switch_UnderCabinet", 0, ry(sw_u - 35, 70), 1150, 15, 70, 115, C_DOOR, cut=False)
cable("Cable_230V_Ch1", [(-15, Y(sw_u), ROOM_H), (-15, Y(sw_u), 1150), (-15, Y(sw_u), 1950),
                         (-15, Y(u_tall - 130), 1950), (-15, Y(u_tall - 130), drv1[2]),
                         (30, Y(u_tall - 130), drv1[2])], "230V")

# --- channel 2: toe-kick, wall run ---
x_kick = BASE_D - PLINTH_SETBACK + 5                  # just in front of the kick-drawer faces
led("LED_Kick_Wall_Run", 2, x_kick, ry(u_sink + 5, SINK_W + RACK_W - 10), PLINTH_H - LED_H, LED_W,
    SINK_W + RACK_W - 10)
drv2 = (320, Y(u_rack - T - 60), 760)
gbox(gL, "Driver_2_Kick_Wall", 290, ry(u_rack - T - 160, 200), 745, 60, 200, 30, C_METAL, cut=False)
cable("Cable_24V_Ch2", [drv2, (drv2[0], drv2[1], PLINTH_H + T + 3), (x_kick + LED_W / 2, drv2[1], PLINTH_H + T + 3),
                        (x_kick + LED_W / 2, drv2[1], PLINTH_H - LED_H / 2)], "24V")
cable("Cable_230V_Ch2", [(-15, Y(u_rack - 200), 450), (5, Y(u_rack - 200), 450), (5, Y(u_rack - 200), 760),
                         (290, Y(u_rack - 200), 760)], "230V")
gbox(gL, "Sensor_Kick_Wall", x_kick, ry(u_rack + 100, 40), PLINTH_H - 20, 20, 40, 20, C_BLACK, cut=False)

# --- channel 3: toe-kick, island work side (kept in the Island group) ---
gLI = group("Lighting_Island", gI)
xi_kick = back_x - (BASE_D - PLINTH_SETBACK + 5) - LED_W
led("LED_Kick_Island", 3, xi_kick, cab_y0 + T + 5, PLINTH_H - LED_H, LED_W, cab_len - 2 * T - 10, gLI)
yi = cab_y0 + T + 120
drv3 = (back_x - T - 40, yi, 500)
gbox(gLI, "Driver_3_Kick_Island", back_x - T - 60, yi - 100, 485, 40, 200, 30, C_METAL, cut=False)
cable("Cable_24V_Ch3", [drv3, (drv3[0], yi, PLINTH_H + T + 3), (xi_kick + LED_W / 2, yi, PLINTH_H + T + 3),
                        (xi_kick + LED_W / 2, yi, PLINTH_H - LED_H / 2)], "24V", gLI)
cable("Cable_230V_Ch3_Floor", [(-15, yi, 300), (-15, yi, -5), (back_x - T - 40, yi, -5),
                               (back_x - T - 40, yi, 485)], "230V", gLI)
gbox(gLI, "Sensor_Kick_Island", xi_kick - 20, cab_y0 + cab_len / 2 - 20, PLINTH_H - 20, 20, 40, 20, C_BLACK, cut=False)

# --- channel 4 (v3): under-cabinet, back-wall cabinets - own switch + driver (no cabinets link it to ch1) ---
cyb = ROOM_L - 95                                     # cable line on the back-cabinet tops
xd4 = xb_app + 100                                    # driver on top of the appliance cabinet, behind the crown
gbox(gL, "Driver_4_UnderCabinet_Back", xd4, cyb - 30, UPPER_TOP, 200, 60, 30, C_METAL, cut=False)
for nm, x0_, w, dep in back_uppers:
    yb_led = ROOM_L - (dep - T - 40 - LED_W) - LED_W
    led(f"LED_{nm}", 4, x0_ + T + 5, yb_led, UPPER_Z - LED_H, w - 2 * T - 10, LED_W)
    xd = x0_ + T + 30
    cable(f"Cable_24V_Ch4_{nm}", [(xd4, cyb, top_z), (xd, cyb, top_z), (xd, cyb, UPPER_Z + T + 3),
                                   (xd, yb_led + LED_W / 2, UPPER_Z + T + 3),
                                   (xd, yb_led + LED_W / 2, UPPER_Z - LED_H / 2)], "24V")
xs4 = xb_prep + 150                                   # wall switch in the back backsplash, washer end
gbox(gL, "Switch_UnderCabinet_Back", xs4 - 35, ROOM_L - 15, 1150, 70, 15, 115, C_DOOR, cut=False)
cable("Cable_230V_Ch4", [(xs4, ROOM_L + 15, ROOM_H), (xs4, ROOM_L + 15, 1150), (xs4, ROOM_L + 15, 2000),
                         (xd4 + 100, ROOM_L + 15, 2000), (xd4 + 100, ROOM_L + 15, top_z),
                         (xd4 + 100, cyb, top_z)], "230V")

for ch, label in ((1, "under-cabinet"), (2, "toe-kick wall run"), (3, "toe-kick island"),
                  (4, "under-cabinet back wall")):
    m = led_len[ch] / 1000
    watts = m * LED_WPM
    drv = next(w for w in (20, 30, 60, 100) if w >= watts * 1.3)
    hardware.append(("Lighting_LED", f"Ch{ch} {label}: 24 V COB LED strip 4000K {LED_WPM} W/m + Al profile "
                                     f"{LED_W}x{LED_H} with diffuser", f"{m:.2f} m", 1))
    hardware.append(("Lighting_LED", f"Ch{ch} {label}: 24 V LED driver {drv} W", "-", 1))
hardware.append(("Lighting_LED", "Wall switch (backsplash) for the under-cabinet lights (left run + back wall)", "-", 2))
hardware.append(("Lighting_LED", "PIR motion sensor for 24 V strip (toe-kick)", "-", 2))
hardware.append(("Lighting_LED", "24 V cable 2 x 0.75 mm2 (+20% spare)", f"{cable_len['24V'] * 1.2 / 1000:.1f} m", 1))
hardware.append(("Lighting_LED", "230 V feed to drivers / switch (electrician, in conduit)",
                 f"{cable_len['230V'] * 1.2 / 1000:.1f} m", 1))
hardware.append(("Lighting_LED", "Cable grommets 10 mm (cabinet top / bottom / carcass holes)", "-", 8))

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
for label, a, b in [("end panel", 0, u_filler), ("filler", u_filler, u_fridge), ("fridge bay", u_fridge, u_tall),
                    ("tall panel", u_tall, u_sink), ("sink base", u_sink, u_rack), ("rack base", u_rack, u_stove),
                    ("stove bay", u_stove, u_wpanel), ("washer panel", u_wpanel, u_washer),
                    ("washer bay", u_washer, u_end), ("end panel", u_end, ROOM_L)]:
    print(f"  {label:13s} {a:7.1f} -> {b:7.1f}  ({b - a:6.1f})")
print(f"Island {isl_len:.0f} x {ctop_x1 - ctop_x0:.0f}, X {ctop_x0:.0f}-{ctop_x1:.0f}, Y {isl_y0:.0f}-{isl_y0 + isl_len:.0f}")
print(f"  aisle run counter -> island {ISLAND_AISLE}, ref front -> island {ctop_x0 - PIPE_CLR - FRIDGE[2]:.0f}, "
      f"island -> right wall {ROOM_W - ctop_x1:.0f}, ends {isl_y0:.0f} / {ROOM_L - isl_y0 - isl_len:.0f}")
print(f"Washer front {PIPE_CLR + WASHER[2]:.0f} vs counter edge {CTOP_D}")
print(f"Back wall run X {xb0:.0f} -> {ROOM_W:.0f} ({ROOM_W - xb0:.0f}): end panel {T} | prep {PREP_W} | "
      f"appliance station {APPL_W} (garage {GARAGE_D} D x {UPPER_Z - COUNTER_Z} H) | pantry {PANTRY_W} | "
      f"filler {BACK_FILLER:.0f}; counter {xb_pan - xb0:.0f}")
print(f"  clear floor washer front -> back run {xb0 - PIPE_CLR - WASHER[2]:.0f}, "
      f"back counter -> island {ROOM_L - CTOP_D - isl_y0 - isl_len:.0f}, island moved "
      f"{ROOM_L / 2 - isl_len / 2 - isl_y0:.0f} toward the open front")

# ---------------- colours + views (GUI only) ----------------
if App.GuiUp:
    import FreeCADGui as Gui
    for name, c in _colours.items():
        doc.getObject(name).ViewObject.ShapeColor = c
    for w in ("Wall_Left", "Wall_Back"):
        doc.getObject(w).ViewObject.Transparency = 70
    for n in _hidden:
        doc.getObject(n).ViewObject.Visibility = False
    for o in doc.Objects:                           # drawer App::Part origins (axes / planes) off
        if o.TypeId == "App::Part" and o.Origin:
            o.Origin.ViewObject.Visibility = False
            for f in o.Origin.OriginFeatures:
                f.ViewObject.Visibility = False
    v = Gui.activeDocument().activeView()
    v.setAnimationEnabled(False)

    def shot(fname, view, w, h, hide=()):
        objs = [o for o in doc.Objects if o.Name in hide or any(g.Name in hide for g in o.InListRecursive)]
        for o in objs:
            o.ViewObject.Visibility = False
        for o in doc.Objects:
            if o.TypeId == "App::Part" and o.Origin:
                o.Origin.ViewObject.Visibility = False
        getattr(v, view)()
        v.fitAll()
        Gui.updateGui()
        v.saveImage(os.path.join(OUT_DIR, fname), w, h, "White")
        for o in objs:
            o.ViewObject.Visibility = True

    shot("kitchen_v3_back_elevation.png", "viewFront", 1800, 1000,
         hide=("Wall_Right", "Wall_Left", "Floor", "Island", "Left_Wall_Run"))
    shot("kitchen_v3_elevation.png", "viewRight", 1800, 1000, hide=("Wall_Right", "Wall_Left", "Floor", "Island", "Back_Wall_Run"))
    shot("kitchen_v3_plan.png", "viewTop", 1400, 1400)
    shot("kitchen_v3_iso.png", "viewIsometric", 1600, 1200, hide=("Wall_Right",))
    # doors / fronts off: shows the shelves, racks and runners inside
    fronts = tuple(o.Name for o in doc.Objects if o.Label.startswith(("Door", "DrawerFront_", "Kick_DrawerFront")))
    shot("kitchen_v3_lighting_elevation.png", "viewRight", 6400, 3000,
         hide=("Wall_Right", "Wall_Left", "Floor", "Island", "Back_Wall_Run") + fronts)
    shot("kitchen_v3_iso_open.png", "viewIsometric", 1600, 1200, hide=("Wall_Right", "Stool_1", "Stool_2", "Stool_3") + fronts)
    # same view with every door open on its hinge and every drawer pulled out (Kitchen_OpenClose macro)
    exec(open(os.path.join(OUT_DIR, "Kitchen_OpenClose.FCMacro")).read().split("if __name__")[0])
    kitchen_fronts(doc, True)
    shot("kitchen_v3_iso_fronts_open.png", "viewIsometric", 1600, 1200, hide=("Wall_Right",))
    kitchen_fronts(doc, False)                      # saved closed
    v.viewIsometric()
    v.fitAll()

# ---------------- cut list + hardware (CSV + FreeCAD spreadsheets) + save ----------------
agg = {}
for row in cut_list:
    key = tuple(row) if len(row) == 6 else tuple(row) + ("",)
    agg[key] = agg.get(key, 0) + 1
with open(os.path.join(OUT_DIR, CUT_LIST), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Part", "Qty", "Length_mm", "Width_mm", "Thickness_mm", "Note"])
    for (mod, part, l, w, th, note), q in sorted(agg.items()):
        wr.writerow([mod, part, q, l, w, th, note])

with open(os.path.join(OUT_DIR, HARDWARE), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Item", "Size_mm", "Qty"])
    for row in hardware:
        wr.writerow(row)

import importlib, sys
sys.path.insert(0, OUT_DIR)
import kitchen_cutlist_core, kitchen_spreadsheets
importlib.reload(kitchen_cutlist_core)
importlib.reload(kitchen_spreadsheets)
kitchen_spreadsheets.add(doc, REV)
doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))

ply = [c for c in cut_list if abs(c[4] - T) < 0.01]
area = sum(c[2] * c[3] for c in ply) / 1e6
print(f"Ply panels: {len(ply)}, area {area:.2f} m2 (~{area / (1.22 * 2.44) * 1.25:.1f} sheets 4x8 incl. 25% waste)")
