# Kitchen ALU: the v2 kitchen (same room, same run REF -> SINK -> STOVE -> WASHER, same island) built as
# ALUMINIUM cabinets from 4 basic materials:
#   - 2x1      : 1" x 2" aluminium tube (25.4 x 50.8) - every carcass frame, panel frame, shelf support,
#                runner rail, plinth and toe-kick drawer box
#   - Cladding : 4 mm aluminium cladding sheet (4x8 ft) - sides, backs, bottoms, tops, shelves, front inserts
#   - Profile  : door / front frame profile - stiles + plain rails, 45 deg mitred corners
#   - Profile with handle : integrated-handle rail - top rail of base doors / drawer fronts,
#                bottom rail of wall-cabinet doors (no separate handles)
# Units: mm. Separate model from build_kitchen_v2.py (PVC); the lighting and appliances are the same.
#
# Run inside FreeCAD:  exec(open("/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet/build_kitchen_alu.py").read())
# Then:  python3 make_kitchen_alu_cutlist.py  (Excel workbook, cutting PDF, cutlistoptimizer.com CSV)
#
# Construction (each cabinet is a self-contained box, like the PVC modules):
#   carcass = 2x1 box frame (4 posts + 4 width rails + 4 side rails) with cladding on the outside;
#   wall cabinets: shelves = cladding on two 2x1 supports (+ a 2x1 front rail under shelves wider than 600);
#   base cabinets: 2x1 runner rails between the front and back posts carry the stainless racks;
#   fronts = profile frame + cladding insert in the profile groove; toe-kick drawers = 2x1 box + cladding bottom.
# An aluminium side (2x1 + cladding) is 29.4 thick vs 18 PVC, so to keep the wall run fitting the room:
#   sink base 870 (was 900), the rack base stays 400 wide (takes a 350-size rack: 341 clear inside),
#   free-standing panels are 2x1 + cladding on the visible face. Island modules are widened so they keep
#   the standard 450 / 750 racks (the island has room to grow).
#
# Axes: X = out from the left wall (0 = masonry), Y = room length (0 = open front -> back wall), Z = up.

import csv
import math
import os
import re
import FreeCAD as App
import Part

IN = 25.4

# ---------------- room ----------------
ROOM_W = 148 * IN
ROOM_L = 142 * IN
ROOM_H = 92 * IN
WALL_T = 4.5 * IN

# ---------------- appliances (W x H x D) ----------------
FRIDGE = (36 * IN, 1780, 25 * IN)
STOVE = (24 * IN, 850, 24 * IN)
WASHER = (600, 850, 550)
SINK = (770, 420)
INDUCTION = (730, 430, 6)
INDUCTION_CUT = (700, 400)
INDUCTION_BODY = 60

# ---------------- aluminium materials (measure yours and change these) ----------------
M_TUBE, M_CLAD, M_PROF, M_HANDLE, M_CTOP = "2x1", "Cladding", "Profile", "Profile with handle", "Countertop"
TA, TB = 25.4, 50.8    # 2x1 tube section (1" x 2")
CLAD = 4               # cladding sheet thickness
PROF_W = 20            # profile face width (stiles / plain rails)
PROF_D = 20            # profile depth = front thickness
GROOVE = 8             # insert depth into the profile groove
HANDLE_W = 45          # profile-with-handle face height
PANEL_BAY = 600        # max stud / rail spacing in framed panels
S = CLAD + TA          # cabinet side build-up (29.4)
T = CLAD + TA          # free-standing panel on the wall run: 2x1 frame + cladding one face (29.4)
T2 = TA + 2 * CLAD     # island panels: cladding both faces (33.4)
GAP = 3

PLINTH_H = 100
PLINTH_SETBACK = 60
KICK_D = 400
KICK_FLOOR = 10
BASE_D = 610
BASE_TOP = 876
CTOP_T = 38
CTOP_D = 635
COUNTER_Z = BASE_TOP + CTOP_T

UPPER_D = 330
UPPER_Z = 1372
UPPER_TOP = 2286
HOOD_Z = COUNTER_Z + 700
HOOD = (560, 280, 180)
HOOD_VISOR_W = 598
HOOD_FLAT_DUCT = (204, 60)

SHELF_PITCH = 320
RUNNER_CLR = 12.5
RACK_D = 500
SINK_RACK_D = 450
RACK_EXTRA = 2 * S - 36   # 22.8: a nominal-W rack needs W - 36 clear

PIPE_OD = 114
PIPE_U = [(T + 10, T + 10 + PIPE_OD), (ROOM_L - PIPE_OD, ROOM_L)]
PIPE_CLR = PIPE_OD + 15

# ---------------- run along the left wall ----------------
START_AT_OPEN_END = True
REF_FILLER = 30
FRIDGE_BAY = 950
SINK_W = 870
RACK_W = 400
STOVE_BAY = 620
STOVE_PLATFORM = TB + CLAD   # 54.8: 2x1 on edge + cladding top; stove feet up ~9 to meet the counter
TOWER_D = PIPE_CLR + FRIDGE[2] + 20

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
assert WASHER_BAY >= WASHER[0] + 15 and WASHER[1] <= BASE_TOP - 10, f"washer bay too small: {WASHER_BAY:.0f}"

# ---------------- island ----------------
ISLAND_AISLE = 1100
ISLAND_OH = 25
ISLAND_SEAT_OH = 300
ISLAND_END_OH = 20
ISLAND_MODULES = [(450 + RACK_EXTRA, "racks"), (750 + RACK_EXTRA, "induction"), (450 + RACK_EXTRA, "racks")]
STOOLS = 3

DOC_NAME = "Kitchen_Alu"
CUT_LIST = "kitchen_alu_cut_list.csv"
HARDWARE = "kitchen_alu_hardware.csv"
OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Kitchen Cabinet"

# ---------------- colours ----------------
C_TUBE = (0.62, 0.64, 0.67)
C_CLAD = (0.86, 0.87, 0.88)
C_FRAME = (0.72, 0.73, 0.75)      # front profiles
C_HANDLE = (0.40, 0.41, 0.44)
C_DOOR = (0.95, 0.95, 0.94)       # front inserts
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
C_DRAWER = (0.80, 0.80, 0.82)
C_LED = (1.0, 0.85, 0.30)
C_24V = (0.10, 0.30, 0.90)
C_230V = (0.85, 0.10, 0.10)

# ---------------- helpers ----------------
if App.listDocuments().get(DOC_NAME):
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)
rec = {}        # object name -> [module, part, material, length, width, note]
extra = []      # cut-list rows without a model object (countertops)
hardware = []   # (module, item, size, qty)
fronts = []     # (module, kind, width, height) for hinges
_colours = {}
_hidden = []


def group(name, parent=None):
    g = doc.addObject("App::DocumentObjectGroup", name)
    if parent:
        parent.addObject(g)
    return g


def gbox(grp, name, x, y, z, dx, dy, dz, colour=C_CLAD, mat=None, shape=None, note="", length=None):
    """Global axis-aligned part as a Part::Box (Woodworking-workbench panel), or a Part::Feature for `shape`.
    mat: cut-list material (None = not cut: appliances, baskets, cables). Bars are listed by length,
    cladding by its two largest sides; `length` overrides (mitred profile cut length)."""
    if shape is None:
        o = doc.addObject("Part::Box", name)
        o.Length, o.Width, o.Height = dx, dy, dz
        o.Placement.Base = App.Vector(x, y, z)
    else:
        o = doc.addObject("Part::Feature", name)
        o.Shape = shape
    grp.addObject(o)
    _colours[o.Name] = colour
    if mat:
        d = sorted([dx, dy, dz], reverse=True)
        L = round(length if length else d[0], 1)
        W = round(d[1], 1) if mat == M_CLAD else ""
        rec[o.Name] = [grp.Label, name, mat, L, W, note]
    return o


def cut_obj(grp, o, tool_shape, why):
    """Notch / shorten a part: Part::Cut(Base = the Part::Box, Tool = hidden shape)."""
    tool = doc.addObject("Part::Feature", o.Name + "_Tool")
    tool.Shape = tool_shape
    c = doc.addObject("Part::Cut", o.Name + "_Cut")
    c.Base, c.Tool = o, tool
    c.Label = o.Label + f" ({why})"
    if o.Name in rec:
        rec[o.Name][5] = why + " - see model"
    grp.removeObject(o)
    grp.addObject(c)
    grp.addObject(tool)
    _hidden.extend([o.Name, tool.Name])
    _colours[c.Name] = _colours.get(o.Name, C_CLAD)
    return c


def drop(o):
    """Remove a frame member that an appliance needs the space of (cut list follows)."""
    rec.pop(o.Name, None)
    _colours.pop(o.Name, None)
    doc.removeObject(o.Name)


def make_drawer(grp, name, objs, slide):
    p = doc.addObject("App::Part", name)
    grp.addObject(p)
    for o in objs:
        grp.removeObject(o)
        p.addObject(o)
    p.addProperty("App::PropertyFloat", "Kitchen_Slide", "Kitchen", "Pull-out distance along X (mm)")
    p.Kitchen_Slide = slide
    return p


def set_front(o, sgn, hinge_low_y, hinge_obj):
    """Woodworking 'fronts open / close' attributes. Every piece of an aluminium door points at the same
    hinge-side stile edge, so the whole door (4 profiles + insert) swings as one."""
    edge = {(1, True): ("Edge1", -90), (1, False): ("Edge3", 90),
            (-1, True): ("Edge5", 90), (-1, False): ("Edge7", -90)}[(sgn, hinge_low_y)]
    for prop, typ, val in (("Woodworking_Type", "App::PropertyString", "Front"),
                           ("Woodworking_Open", "App::PropertyBool", True),
                           ("Woodworking_OpenObj", "App::PropertyString", hinge_obj.Name),
                           ("Woodworking_OpenEdge", "App::PropertyString", edge[0]),
                           ("Woodworking_OpenAxis", "App::PropertyString", "Z"),
                           ("Woodworking_OpenAngleStep", "App::PropertyFloat", edge[1])):
        o.addProperty(typ, prop, "Woodworking")
        setattr(o, prop, val)


def ry(u, du):
    return u if START_AT_OPEN_END else ROOM_L - u - du


def framed_panel(grp, name, x, y, z, dx, dy, dz, faces, colour=C_CLAD):
    """Free-standing panel: 2x1 frame (1" through the panel, studs / rails <= PANEL_BAY apart) with cladding
    on `faces` ('lo' / 'hi' side of the thin axis). dx or dy = thickness = 25.4 + 4 per clad face."""
    thin_x = dx < dy
    span = dy if thin_x else dx
    t0 = x if thin_x else y
    ft = t0 + (CLAD if "lo" in faces else 0)          # frame starts here on the thin axis

    def put(nm, s0, ds, zz, dzz, mat, col, ts, tl, note=""):
        if thin_x:
            return gbox(grp, nm, ts, y + s0, zz, tl, ds, dzz, col, mat, note=note)
        return gbox(grp, nm, x + s0, ts, zz, ds, tl, dzz, col, mat, note=note)

    nv = max(1, math.ceil((span - TB) / PANEL_BAY))
    xs = [i * (span - TB) / nv for i in range(nv + 1)]
    for i, s in enumerate(xs):
        put(f"{name}_Stud_{i + 1}", s, TB, z, dz, M_TUBE, C_TUBE, ft, TA)
    nh = max(1, math.ceil((dz - TB) / PANEL_BAY))
    for j in range(nh + 1):
        zz = z + j * (dz - TB) / nh
        for i in range(nv):
            put(f"{name}_Rail_{j + 1}_{i + 1}", xs[i] + TB, xs[i + 1] - xs[i] - TB, zz, TB, M_TUBE, C_TUBE, ft, TA)
    for f in faces:
        put(f"{name}_Clad_{f}", 0, span, z, dz, M_CLAD, colour, t0 if f == "lo" else ft + TA, CLAD)


def run_panel(grp, name, u, d0, z0, dd, dz, face_u):
    """Framed panel standing on the wall run (thickness T along the run), cladding on the 'lo' / 'hi' u side."""
    face = face_u if START_AT_OPEN_END else {"lo": "hi", "hi": "lo"}[face_u]
    framed_panel(grp, name, d0, ry(u, T), z0, dd, T, dz, (face,), C_DOOR)


class Module:
    """One cabinet at u (width w). a = along the run, d = from the cabinet back. Island: sgn = -1."""

    def __init__(self, parent, name, u, w, x0=0, sgn=1, on_run=True):
        self.g, self.u, self.w = group(name, parent), u, w
        self.x0, self.sgn, self.on_run = x0, sgn, on_run
        self.objs = []
        self.frame = None

    def place(self, a, d, da, dd):
        x = self.x0 + d if self.sgn > 0 else self.x0 - d - dd
        y = ry(self.u + a, da) if self.on_run else self.u + a
        return x, y

    def box(self, name, a, d, z, da, dd, dz, colour=C_CLAD, mat=None, note="", length=None):
        x, y = self.place(a, d, da, dd)
        o = gbox(self.g, name, x, y, z, dd, da, dz, colour, mat, note=note, length=length)
        self.objs.append(o)
        return o

    def tube(self, name, a, d, z, da, dd, dz, note=""):
        return self.box(name, a, d, z, da, dd, dz, C_TUBE, M_TUBE, note)

    def clad(self, name, a, d, z, da, dd, dz, colour=C_CLAD, note=""):
        return self.box(name, a, d, z, da, dd, dz, colour, M_CLAD, note)

    def carcass(self, z, h, depth, back=True, top=True):
        """2x1 box frame, cladding outside: sides full size, back between the sides, bottom (+ top)."""
        w = self.w
        d0 = CLAD if back else 0
        self.clad("Side_A_Clad", 0, 0, z, CLAD, depth, h)
        self.clad("Side_B_Clad", w - CLAD, 0, z, CLAD, depth, h)
        if back:
            self.clad("Back_Clad", CLAD, 0, z, w - 2 * CLAD, CLAD, h)
        self.clad("Bottom_Clad", CLAD, d0, z, w - 2 * CLAD, depth - d0, CLAD)
        zt = z + h - (CLAD if top else 0)
        if top:
            self.clad("Top_Clad", CLAD, d0, zt, w - 2 * CLAD, depth - d0, CLAD)
        zf = z + CLAD
        for nm, a in (("A", CLAD), ("B", w - CLAD - TA)):
            for nd, d in (("Back", d0), ("Front", depth - TB)):
                self.tube(f"Post_{nd}_{nm}", a, d, zf, TA, TB, zt - zf)
            for lvl, zz in (("Bottom", zf), ("Top", zt - TB)):
                self.tube(f"Rail_Side_{nm}_{lvl}", a, d0 + TB, zz, TA, depth - d0 - 2 * TB, TB)
        for nd, d in (("Back", d0), ("Front", depth - TB)):
            for lvl, zz in (("Bottom", zf), ("Top", zt - TA)):
                self.tube(f"Rail_{nd}_{lvl}", CLAD + TA, d, zz, w - 2 * CLAD - 2 * TA, TB, TA)
        self.frame = (zf, zt, d0, depth)

    def runner_rails(self, name, z):
        """2x1 between the front and back posts (in the post plane) for a pair of rack runners."""
        zf, zt, d0, dep = self.frame
        for nm, a in (("A", CLAD), ("B", self.w - CLAD - TA)):
            self.tube(f"{name}_Runner_Rail_{nm}", a, d0 + TB, z, TA, dep - d0 - 2 * TB, TB)

    def shelf(self, name, z, d_start=None, setback=20):
        """Cladding shelf (top at z + CLAD) on two 2x1 supports fixed to the posts; 2x1 front rail if > 600 wide."""
        zf, zt, d0, dep = self.frame
        ds = d0 if d_start is None else d_start
        for nm, a in (("A", CLAD + TA), ("B", self.w - CLAD - 2 * TA)):
            self.tube(f"{name}_Support_{nm}", a, d0, z - TB, TA, dep - d0, TB)
        sw, sd = self.w - 2 * CLAD - 2 * TA, dep - ds - setback
        self.clad(name, CLAD + TA, ds, z, sw, sd, CLAD)
        if sw > 600:
            self.tube(f"{name}_Front_Rail", CLAD + 2 * TA, ds + sd - TA, z - TB, sw - 2 * TA, TA, TB)

    def front(self, name, a, d, z, fw, fh, handle=None, colour=C_DOOR):
        """Profile frame + cladding insert. handle='top' / 'bottom': that rail is the profile with handle
        (full width, square cut; stiles square at that end). Plain corners are mitred 45 deg; mitred
        pieces are listed at their long-point (outside) length."""
        rb = HANDLE_W if handle == "bottom" else PROF_W
        rt = HANDLE_W if handle == "top" else PROF_W
        sz = z + (HANDLE_W if handle == "bottom" else 0)
        sh = fh - (HANDLE_W if handle else 0)
        snote = "45 deg one end, square at the handle" if handle else "45 deg both ends"
        ps = [self.box(f"{name}_Stile_{nm}", aa, d, sz, PROF_W, PROF_D, sh, C_FRAME, M_PROF, snote)
              for nm, aa in (("A", a), ("B", a + fw - PROF_W))]
        for pos, zz, hh in (("Bottom", z, rb), ("Top", z + fh - rt, rt)):
            if handle == pos.lower():
                ps.append(self.box(f"{name}_Handle_Rail", a, d, zz, fw, PROF_D, hh, C_HANDLE, M_HANDLE,
                                   "square cut, full width"))
            else:
                ps.append(self.box(f"{name}_Rail_{pos}", a + PROF_W, d, zz, fw - 2 * PROF_W, PROF_D, hh, C_FRAME,
                                   M_PROF, "45 deg both ends", length=fw))
        ps.append(self.clad(f"{name}_Insert", a + PROF_W - GROOVE, d + (PROF_D - CLAD) / 2, z + rb - GROOVE,
                            fw - 2 * (PROF_W - GROOVE), CLAD, fh - rb - rt + 2 * GROOVE, colour, "in the profile groove"))
        return ps

    def doors(self, n, z, h, front_d, handle, colour=C_DOOR):
        dw = self.w / n
        for i in range(n):
            ps = self.front(f"Door_{i + 1}", i * dw + GAP / 2, front_d, z + GAP / 2, dw - GAP, h - GAP, handle, colour)
            for p in ps:
                set_front(p, self.sgn, i == 0, ps[0] if i == 0 else ps[1])
            fronts.append((self.g.Label, "Door", dw - GAP, h - GAP))

    def plinth(self, depth=BASE_D):
        """2x1 legs + rails, cladding on the back and sides; the toe-kick space is a push-to-open drawer
        (2x1 box, cladding bottom, profile-framed front) on runners screwed to the plinth side rails."""
        w = self.w
        pb = 60
        fd = depth - PLINTH_SETBACK - PROF_D
        self.clad("Plinth_Back_Clad", CLAD, pb - CLAD, 0, w - 2 * CLAD, CLAD, PLINTH_H, C_PLINTH)
        for nm, a in (("A", 0), ("B", w - CLAD)):
            self.clad(f"Plinth_Side_{nm}_Clad", a, pb - CLAD, 0, CLAD, fd - pb + CLAD, PLINTH_H, C_PLINTH)
        for nm, a in (("A", CLAD), ("B", w - CLAD - TA)):
            for nd, d in (("Back", pb), ("Front", fd - TB)):
                self.tube(f"Plinth_Leg_{nd}_{nm}", a, d, 0, TA, TB, PLINTH_H)
            self.tube(f"Plinth_Rail_Side_{nm}", a, pb + TB, 0, TA, fd - pb - 2 * TB, TB)
        self.tube("Plinth_Rail_Back", CLAD + TA, pb, PLINTH_H - TA, w - 2 * CLAD - 2 * TA, TB, TA)
        bw = w - 2 * S - 2 * RUNNER_CLR
        a0, d0 = S + RUNNER_CLR, fd - KICK_D
        bz = KICK_FLOOR + 6
        kick = self.front("Kick_Front", GAP / 2, fd, KICK_FLOOR, w - GAP, PLINTH_H - KICK_FLOOR - GAP, None, C_PLINTH)
        kick += [self.tube("Kick_Side_A", a0, d0, bz, TA, KICK_D, TB),
                 self.tube("Kick_Side_B", a0 + bw - TA, d0, bz, TA, KICK_D, TB),
                 self.tube("Kick_Back", a0 + TA, d0, bz, bw - 2 * TA, TA, TB),
                 self.tube("Kick_Inner_Front", a0 + TA, fd - TA, bz, bw - 2 * TA, TA, TB),
                 self.clad("Kick_Bottom_Clad", a0, d0, bz - CLAD, bw, KICK_D, CLAD, C_DRAWER)]
        make_drawer(self.g, "Drawer_ToeKick", kick, self.sgn * KICK_D * 0.75)
        for side, ra in (("A", a0 - RUNNER_CLR), ("B", a0 + bw)):
            rx, ry_ = self.place(ra, d0, RUNNER_CLR, KICK_D)
            gbox(self.g, f"Kick_Runner_{side}", rx, ry_, bz + 10, KICK_D, RUNNER_CLR, 35, C_METAL)
        hardware.append((self.g.Label, f"Toe-kick drawer runner pair {KICK_D} mm, low profile, push-to-open", "-", 1))

    def basket(self, name, a, d, z, da, dd, h, item, wall=2, runners=False):
        x, y = self.place(a, d, da, dd)
        shell = Part.makeBox(dd, da, h, App.Vector(x, y, z)).cut(
            Part.makeBox(dd - 2 * wall, da - 2 * wall, h, App.Vector(x + wall, y + wall, z + wall)))
        o = gbox(self.g, name, 0, 0, 0, 0, 0, 0, C_STEEL, shape=shell)
        hardware.append((self.g.Label, item, f"{da:.0f} W x {dd:.0f} D x {h:.0f} H", 1))
        if runners:
            for side, ra in (("A", a - RUNNER_CLR), ("B", a + da)):
                rx, ry_ = self.place(ra, d, RUNNER_CLR, dd)
                gbox(self.g, f"{name}_Runner_{side}", rx, ry_, z + 10, dd, RUNNER_CLR, 40, C_METAL)
            hardware.append((self.g.Label, f"Full-extension soft-close runner pair, {dd:.0f} mm", "-", 1))
        return o


def base_cabinet(parent, name, u, w, kind, colour=C_DOOR, **frame):
    """610 base on a 2x1 plinth; stainless pull-out racks inside on runners."""
    m = Module(parent, name, u, w, **frame)
    cd = BASE_D - PROF_D
    m.plinth()
    h = BASE_TOP - PLINTH_H
    inner = w - 2 * S
    rack_w = inner - 2 * RUNNER_CLR
    size = f"{int((inner + 36) // 50 * 50)} cabinet size, {inner:.0f} clear, {RACK_D} runners"

    def tiers(spec, z0):
        fz = z0
        for i, (fh, bh, item) in enumerate(spec):
            fr = m.front(f"DrawerFront_{i + 1}", GAP / 2, cd, fz + GAP / 2, w - GAP, fh - GAP, "top", colour)
            fronts.append((m.g.Label, "Drawer", w - GAP, fh - GAP))
            if bh:
                if i:                                   # tier 1 runs on the bottom side rails
                    m.runner_rails(f"Tier_{i + 1}", fz + 30)
                bk = m.basket(f"SS_Basket_{i + 1}", S + RUNNER_CLR, cd - RACK_D, fz + 30, rack_w, RACK_D,
                              min(bh, fh - 60), f"{item} ({size})", runners=True)   # runners on the rail face
                make_drawer(m.g, f"Drawer_{i + 1}", fr + [bk], m.sgn * RACK_D * 0.75)
            fz += fh

    if kind == "sink":
        m.carcass(PLINTH_H, h, cd, back=False, top=False)       # open back for plumbing
        m.doors(2, PLINTH_H, h, cd, "top", colour)
        tray = m.basket("SS_UnderSink_Tray", S + RUNNER_CLR, cd - SINK_RACK_D, PLINTH_H + 30, rack_w,
                        SINK_RACK_D, 120, "Under-sink pull-out tray (door-mounted cabinet)", runners=True)
        make_drawer(m.g, "Drawer_UnderSink", [tray], m.sgn * SINK_RACK_D * 0.75)
    elif kind == "racks":
        m.carcass(PLINTH_H, h, cd, top=False)
        tiers([(h * 0.40, 200, "Pot / pan basket"), (h * 0.35, 150, "Bowl + plate basket"),
               (h * 0.25, 70, "Cutlery / utensil tray")], PLINTH_H)
    elif kind == "induction":
        m.carcass(PLINTH_H, h, cd, top=False)
        vent = 120
        tiers([((h - vent) / 2, 250, "Deep pot basket"), ((h - vent) / 2, 200, "Pot / pan basket"),
               (vent, 0, "")], PLINTH_H)
        hardware.append((m.g.Label, "Vent grille / 6 mm gap behind the top fixed front (induction air)", "-", 1))
    return m


def wall_cabinet(parent, name, u, w, z0, z1, depth=UPPER_D, ndoors=2, pipe=None, shelf=True):
    """Wall cabinet: 2x1 frame + cladding, fixed cladding shelves, doors with the handle profile at the bottom.
    pipe=(u0, u1): corner pipe in its back corner -> cladding notched, frame members cut back / removed,
    an L-shaped cladding chase on a 2x1 corner post boxes the pipe."""
    m = Module(parent, name, u, w)
    cd = depth - PROF_D
    m.carcass(z0, z1 - z0, cd)
    if shelf:
        zf, zt, d0, dep = m.frame
        clear = zt - zf
        n = int(clear // SHELF_PITCH)
        for k in range(n):
            m.shelf(f"Shelf_{k + 1}", zf + (k + 1) * clear / (n + 1))
    m.doors(ndoors, z0, z1 - z0, cd, "bottom")
    if pipe:
        cu0, cu1 = max(pipe[0] - 10, u), min(pipe[1] + 10, u + w)
        cdp = PIPE_OD + 10
        at_start = cu0 <= u + 1
        nu0, nu1 = (cu0, cu1 + CLAD + TA) if at_start else (cu0 - CLAD - TA, cu1)
        notch = Part.makeBox(cdp + CLAD, nu1 - nu0, z1 - z0, App.Vector(0, ry(nu0, nu1 - nu0), z0))
        for o in list(m.objs):
            common = o.Shape.common(notch).Volume
            if common < 1:
                continue
            if rec.get(o.Name, [None] * 3)[2] == M_TUBE and common > 0.5 * o.Shape.Volume:
                m.objs.remove(o)
                drop(o)                                  # its job is taken by the chase post
            else:
                cut_obj(m.g, o, notch, "notched for pipe" if rec[o.Name][2] == M_CLAD else "cut back at pipe chase")
        h = z1 - z0
        m.clad("Pipe_Chase_Front_Clad", nu0 - u, cdp, z0, nu1 - nu0, CLAD, h)
        m.clad("Pipe_Chase_Side_Clad", (cu1 if at_start else cu0 - CLAD) - u, 0, z0, CLAD, cdp, h)
        m.tube("Pipe_Chase_Post", (cu1 + CLAD if at_start else cu0 - CLAD - TA) - u, cdp + CLAD - TB, z0 + CLAD,
               TA, TB, h - 2 * CLAD)
    return m


def crown(grp, name, u, du, d_front):
    """Ceiling scribe strip: cladding strip on a 2x1 ledger screwed to the cabinet tops (cut to fit on site)."""
    h = ROOM_H - UPPER_TOP
    gbox(grp, f"{name}_Clad", d_front - CLAD, ry(u, du), UPPER_TOP, CLAD, du, h, C_DOOR, M_CLAD)
    gbox(grp, f"{name}_Ledger", d_front - CLAD - TB, ry(u, du), UPPER_TOP, TB, du, TA, C_TUBE, M_TUBE)


root = group(DOC_NAME)
root.addProperty("App::PropertyBool", "Kitchen_Open", "Kitchen", "Fronts open (toggled by Kitchen_OpenClose)")
root.Kitchen_Open = False
run = group("Left_Wall_Run", root)

# ================= REF TOWER =================
gF = group("Ref_Tower", run)
run_panel(gF, "End_Panel_Ref", 0, 0, 0, TOWER_D, UPPER_TOP, "lo")             # cladding on the open-side face
gbox(gF, "Filler_Ref_Clad", TOWER_D - CLAD, ry(u_filler, REF_FILLER), 0, CLAD, REF_FILLER, UPPER_TOP, C_DOOR, M_CLAD)
gbox(gF, "Filler_Ref_Post", TOWER_D - CLAD - TB, ry(u_filler + (REF_FILLER - TA) / 2, TA), 0, TB, TA, UPPER_TOP,
     C_TUBE, M_TUBE)
fw, fh, fd = FRIDGE
gbox(gF, "Ref_3ft", PIPE_CLR, ry(u_fridge + (FRIDGE_BAY - fw) / 2, fw), 0, fd, fw, fh, C_STEEL)
run_panel(gF, "Tall_Panel", u_tall, 0, 0, TOWER_D, UPPER_TOP, "lo")          # cladding on the fridge side
over_z = max(fh + 40, 1829)
wall_cabinet(gF, "Over_Ref_Cabinet", u_fridge, FRIDGE_BAY, over_z, UPPER_TOP, depth=TOWER_D, pipe=PIPE_U[0])

# ================= SINK + RACK BASE + COUNTER =================
gS = group("Sink_Counter", run)
base_cabinet(gS, f"Base_Sink_{SINK_W}", u_sink, SINK_W, "sink")
base_cabinet(gS, f"Base_Racks_{RACK_W:.0f}", u_rack, RACK_W, "racks")
ctop_len = SINK_W + RACK_W
ctop = Part.makeBox(CTOP_D, ctop_len, CTOP_T, App.Vector(0, ry(u_sink, ctop_len), BASE_TOP))
sw, sd = SINK
sink_y = ry(u_sink + SINK_W / 2 - sw / 2, sw)
sink_x = CTOP_D - 60 - sd
ctop = ctop.cut(Part.makeBox(sd, sw, CTOP_T + 2, App.Vector(sink_x, sink_y, BASE_TOP - 1)))
gbox(gS, "Countertop", 0, 0, 0, 0, 0, 0, C_CTOP, shape=ctop)
extra.append(["Sink_Counter", "Countertop (sink cut-out 770x420)", M_CTOP, round(ctop_len, 1), CTOP_D,
              "solid surface / granite / quartz"])
gbox(gS, "Sink_770x420", 0, 0, 0, 0, 0, 0, C_STEEL,
     shape=Part.makeBox(sd + 20, sw + 20, 3, App.Vector(sink_x - 10, sink_y - 10, COUNTER_Z)).fuse(
         Part.makeBox(sd - 20, sw - 20, 200, App.Vector(sink_x + 10, sink_y + 10, COUNTER_Z - 200))))

# ================= STOVE =================
gC = group("Stove_Bay", run)
sw_, sh_, sd_ = STOVE
sy = ry(u_stove + STOVE_BAY / 2 - sw_ / 2, sw_)
for nm, x in (("Back", 0), ("Front", sd_ - TA)):                      # 2x1 on edge + cladding top
    gbox(gC, f"Platform_Rail_{nm}", x, sy, 0, TA, sw_, TB, C_TUBE, M_TUBE)
for i, yy in enumerate((sy, sy + sw_ / 2 - TA / 2, sy + sw_ - TA)):
    gbox(gC, f"Platform_Cross_{i + 1}", TA, yy, 0, sd_ - 2 * TA, TA, TB, C_TUBE, M_TUBE)
gbox(gC, "Platform_Top_Clad", 0, sy, TB, sd_, sw_, CLAD, C_PLINTH, M_CLAD)
gbox(gC, "Stove_2ft", 0, sy, STOVE_PLATFORM, sd_, sw_, sh_, C_STEEL)
gbox(gC, "Stove_Top", 30, sy + 20, STOVE_PLATFORM + sh_, sd_ - 60, sw_ - 40, 8, C_BLACK)
hardware.append(("Stove_Bay", "Stove levelling feet: raise ~9 mm so the cooktop meets the counter (platform 54.8)",
                 "-", 1))
# concealed hood in the bottom of the cabinet over the stove; flat duct up the back in front of the back rails
mh = wall_cabinet(gC, f"Upper_Hood_{STOVE_BAY}", u_stove, STOVE_BAY, HOOD_Z, UPPER_TOP, ndoors=1, shelf=False)
hw, hd, hh = HOOD
ha = (STOVE_BAY - hw) / 2
hood_box = Part.makeBox(hd, hw, hh, App.Vector(CLAD, ry(u_stove + ha, hw), HOOD_Z))
for o in list(mh.objs):
    if o.Shape.common(hood_box).Volume > 1:
        if rec[o.Name][2] == M_TUBE:
            mh.objs.remove(o)
            drop(o)                 # bottom width rails: the hood body sits between the bottom side rails
        else:
            cut_obj(mh.g, o, hood_box, "hood cut-out")
gbox(gC, "Hood_Telescopic_60cm", 0, 0, 0, 0, 0, 0, C_STEEL, shape=hood_box)
gbox(gC, "Hood_Visor", CLAD + hd - 10, ry(u_stove + (STOVE_BAY - HOOD_VISOR_W) / 2, HOOD_VISOR_W), HOOD_Z - 15, 10,
     HOOD_VISOR_W, 15, C_STEEL)
fdw, fdd = HOOD_FLAT_DUCT
duct_x = CLAD + TB                                   # in front of the back rails (they carry the cabinet)
duct_box = Part.makeBox(fdd, fdw, ROOM_H - HOOD_Z - hh, App.Vector(duct_x, ry(u_stove + STOVE_BAY / 2 - fdw / 2, fdw),
                                                                   HOOD_Z + hh))
for o in list(mh.objs):
    if o.Shape.common(duct_box).Volume > 1:
        cut_obj(mh.g, o, duct_box, "duct cut-out")
gbox(gC, "Hood_Duct_Flat_204x60", 0, 0, 0, 0, 0, 0, C_PIPE, shape=duct_box)
sd0 = duct_x + fdd + 5
z_s1 = HOOD_Z + hh + 10 + TB
for k, z in enumerate([z_s1, z_s1 + (UPPER_TOP - CLAD - z_s1) / 2]):
    mh.shelf(f"Shelf_{k + 1}", z, d_start=sd0, setback=5)
hardware.append((mh.g.Label, "Flat duct 204x60 + 150 round-to-flat adapter, up the cabinet back to the ceiling "
                 "(cut-out in the cabinet top)", "-", 1))
hardware.append((mh.g.Label, f"Built-in telescopic range hood 60 cm (body <= {STOVE_BAY - 2 * S:.0f} W), ducted, "
                 "150 outlet, fixed to the bottom side rails", f"{hw} W x {hd} D x {hh} H", 1))

# ================= WASHING MACHINE =================
gW = group("Washer_Bay", run)
run_panel(gW, "Panel_Stove_Side", u_wpanel, 0, 0, BASE_D, BASE_TOP, "lo")             # cladding on the stove side
run_panel(gW, "End_Panel", u_end, PIPE_CLR - 5, 0, BASE_D - PIPE_CLR + 5, BASE_TOP, "lo")  # clear of the pipe
gbox(gW, "Back_Rail", PIPE_CLR - 5, ry(u_washer, WASHER_BAY), BASE_TOP - TB, TA, WASHER_BAY, TB, C_TUBE, M_TUBE)
gbox(gW, "Rail_Front", BASE_D - PROF_D - TB, ry(u_washer, WASHER_BAY), BASE_TOP - TA, TB, WASHER_BAY, TA, C_TUBE,
     M_TUBE)
ww, wh, wd = WASHER
gbox(gW, "Washer_60x55", PIPE_CLR, ry(u_washer + (WASHER_BAY - ww) / 2, ww), 0, wd, ww, wh, C_WASHER)
w_ctop = ROOM_L - u_wpanel
pipe_notch = Part.makeBox(PIPE_OD + 10 + T, PIPE_U[1][1] - PIPE_U[1][0] + 10 + T, CTOP_T + 2,
                          App.Vector(0, ry(PIPE_U[1][0] - 10 - T, PIPE_OD + 10 + T), BASE_TOP - 1))
wshape = Part.makeBox(CTOP_D, w_ctop, CTOP_T, App.Vector(0, ry(u_wpanel, w_ctop), BASE_TOP)).cut(pipe_notch)
gbox(gW, "Countertop_Washer", 0, 0, 0, 0, 0, 0, C_CTOP, shape=wshape)
extra.append(["Washer_Bay", f"Countertop (corner notch {PIPE_OD + 10 + T:.0f}x{PIPE_OD + 10 + T:.0f} for pipe)",
              M_CTOP, round(w_ctop, 1), CTOP_D, "solid surface / granite / quartz"])
hardware.append(("Washer_Bay", "Paint / wrap the exposed pipe (counter -> wall cabinet) to match the backsplash",
                 "458 H", 1))
wall_cabinet(gW, "Upper_Over_Washer", u_washer, ROOM_L - u_washer, UPPER_Z, UPPER_TOP, pipe=PIPE_U[1])

# ================= WALL CABINETS over the counter =================
gU = group("Wall_Cabinets", run)
mu = wall_cabinet(gU, f"Upper_Sink_{SINK_W}", u_sink, SINK_W, UPPER_Z, UPPER_TOP, shelf=False)
dr_w, dr_d = SINK_W - 2 * S - 10, UPPER_D - PROF_D - CLAD - TB - 10
dz0 = UPPER_Z + CLAD + TB + 5
mu.basket("SS_Drip_Tray", S + 5, CLAD + 5, dz0, dr_w, dr_d, 25, "Dish drainer drip tray")
mu.basket("SS_Plate_Rack", S + 5, CLAD + 5, dz0 + 55, dr_w, dr_d, 120, f"Dish drainer, plate tier ({SINK_W} cabinet)")
mu.basket("SS_Cup_Rack", S + 5, CLAD + 5, UPPER_Z + 520, dr_w, dr_d, 80, f"Dish drainer, cup / bowl tier ({SINK_W} cabinet)")
wall_cabinet(gU, f"Upper_{RACK_W:.0f}", u_rack, RACK_W, UPPER_Z, UPPER_TOP, ndoors=1)

gK = group("Scribe_Strips", run)
crown(gK, "Crown_Ref", 0, u_tall + T, TOWER_D)
crown(gK, "Crown_Uppers", u_sink, SINK_W + RACK_W + STOVE_BAY + T, UPPER_D)
crown(gK, "Crown_Washer", u_washer, WASHER_BAY + T, UPPER_D)

gP = group("Corner_Pipes_4in_PVC", run)
for nm, (p0, p1) in (("Pipe_Open_End", PIPE_U[0]), ("Pipe_Back_Corner", PIPE_U[1])):
    yc = ry((p0 + p1) / 2, 0)
    gbox(gP, nm, 0, 0, 0, 0, 0, 0, C_PIPE, shape=Part.makeCylinder(PIPE_OD / 2, ROOM_H, App.Vector(PIPE_OD / 2, yc, 0)))

# ================= ISLAND =================
gI = group("Island", root)
cab_len = sum(w for w, _ in ISLAND_MODULES) + 2 * T2
isl_len = cab_len + 2 * ISLAND_END_OH
ctop_x0 = CTOP_D + ISLAND_AISLE
front_x = ctop_x0 + ISLAND_OH
back_x = front_x + BASE_D
ctop_x1 = back_x + T2 + ISLAND_SEAT_OH
isl_y0 = ROOM_L / 2 - isl_len / 2
cab_y0 = isl_y0 + ISLAND_END_OH
framed_panel(gI, "Island_End_Panel_A", front_x, cab_y0, 0, BASE_D + T2, T2, BASE_TOP, ("lo", "hi"), C_ISLAND)
framed_panel(gI, "Island_End_Panel_B", front_x, cab_y0 + cab_len - T2, 0, BASE_D + T2, T2, BASE_TOP, ("lo", "hi"),
             C_ISLAND)
framed_panel(gI, "Island_Back_Panel", back_x, cab_y0 + T2, 0, T2, cab_len - 2 * T2, BASE_TOP, ("lo", "hi"), C_ISLAND)
y = cab_y0 + T2
cook_y = None
for i, (w, kind) in enumerate(ISLAND_MODULES):
    base_cabinet(gI, f"Island_{i + 1}_{kind.title()}_{w:.0f}", y, w, kind, colour=C_ISLAND,
                 x0=back_x, sgn=-1, on_run=False)
    if kind == "induction":
        cook_y = y + w / 2
    y += w
iw, idp, it = INDUCTION
icw, icd = INDUCTION_CUT
cook_x = front_x + BASE_D / 2 - idp / 2
ishape = Part.makeBox(ctop_x1 - ctop_x0, isl_len, CTOP_T, App.Vector(ctop_x0, isl_y0, BASE_TOP)).cut(
    Part.makeBox(icd, icw, CTOP_T + 2, App.Vector(cook_x + (idp - icd) / 2, cook_y - icw / 2, BASE_TOP - 1)))
gbox(gI, "Island_Countertop", 0, 0, 0, 0, 0, 0, C_CTOP, shape=ishape)
extra.append(["Island", f"Countertop (cooktop cut-out {icw}x{icd})", M_CTOP, round(isl_len, 1),
              round(ctop_x1 - ctop_x0, 1), "solid surface / granite / quartz"])
gbox(gI, "Induction_Glass", cook_x, cook_y - iw / 2, COUNTER_Z, idp, iw, it, C_BLACK)
gbox(gI, "Induction_Body", cook_x + (idp - icd) / 2 + 5, cook_y - icw / 2 + 5, COUNTER_Z - INDUCTION_BODY,
     icd - 10, icw - 10, INDUCTION_BODY, C_BLACK)
hardware.append(("Island", "Induction power: dedicated circuit in floor conduit to the island", "-", 1))
for i in range(STOOLS):
    sy_ = isl_y0 + isl_len * (i + 1) / (STOOLS + 1)
    sx = ctop_x1 - ISLAND_SEAT_OH / 2
    seat = Part.makeCylinder(190, 40, App.Vector(sx, sy_, 650))
    leg = Part.makeCylinder(25, 650, App.Vector(sx, sy_, 0))
    gbox(gI, f"Stool_{i + 1}", 0, 0, 0, 0, 0, 0, C_BLACK, shape=seat.fuse(leg))

# ================= LED LIGHTING + WIRING (same 3 channels as v2) =================
gL = group("Lighting_LED", root)
LED_W, LED_H, LED_WPM = 16, 7, 10
led_len = {1: 0, 2: 0, 3: 0}
cable_len = {"24V": 0, "230V": 0}


def led(name, ch, x, y, z, dx, dy, grp=gL):
    gbox(grp, name, x, y, z, dx, dy, LED_H, C_LED)
    led_len[ch] += max(dx, dy)


def cable(name, pts, kind, grp=gL):
    shape = None
    for p0, p1 in zip(pts, pts[1:]):
        a, b = App.Vector(*p0), App.Vector(*p1)
        if (b - a).Length < 1:
            continue
        seg = Part.makeCylinder(6, (b - a).Length, a, b - a)
        shape = seg if shape is None else shape.fuse(seg)
        cable_len[kind] += (b - a).Length
    gbox(grp, name, 0, 0, 0, 0, 0, 0, C_24V if kind == "24V" else C_230V, shape=shape)


def Y(u):
    return ry(u, 0)


x_led = UPPER_D - PROF_D - 40 - LED_W
top_z = UPPER_TOP + 10
cx = 95
drv1 = (60, Y(u_tall - 80), over_z + CLAD + TB + 15)
gbox(gL, "Driver_1_UnderCabinet", 0, 0, 0, 0, 0, 0, C_METAL,
     shape=Part.makeBox(60, 200, 30, App.Vector(30, ry(u_tall - 230, 200), over_z + CLAD + TB)))
cable("Cable_24V_Ch1_Riser", [drv1, (cx, drv1[1], drv1[2]), (cx, drv1[1], top_z)], "24V")
under = [(f"Upper_Sink_{SINK_W}", u_sink, SINK_W), (f"Upper_{RACK_W:.0f}", u_rack, RACK_W),
         ("Upper_Over_Washer", u_washer, ROOM_L - u_washer)]
cable("Cable_24V_Ch1_Top", [(cx, drv1[1], top_z), (cx, Y(under[-1][1] + S + 30), top_z)], "24V")
for nm, u0, w in under:
    a0 = u0 + S + 5
    led(f"LED_{nm}", 1, x_led, ry(a0, w - 2 * S - 10), UPPER_Z - LED_H, LED_W, w - 2 * S - 10)
    ud = u0 + S + 30
    cable(f"Cable_24V_Ch1_{nm}", [(cx, Y(ud), top_z), (cx, Y(ud), UPPER_Z + CLAD + 3),
                                  (x_led + LED_W / 2, Y(ud), UPPER_Z + CLAD + 3),
                                  (x_led + LED_W / 2, Y(ud), UPPER_Z - LED_H / 2)], "24V")
sw_u = u_sink + 150
gbox(gL, "Switch_UnderCabinet", 0, ry(sw_u - 35, 70), 1150, 15, 70, 115, C_DOOR)
cable("Cable_230V_Ch1", [(-15, Y(sw_u), ROOM_H), (-15, Y(sw_u), 1150), (-15, Y(sw_u), 1950),
                         (-15, Y(u_tall - 130), 1950), (-15, Y(u_tall - 130), drv1[2]),
                         (30, Y(u_tall - 130), drv1[2])], "230V")

x_kick = BASE_D - PLINTH_SETBACK + 5
led("LED_Kick_Wall_Run", 2, x_kick, ry(u_sink + 5, SINK_W + RACK_W - 10), PLINTH_H - LED_H, LED_W,
    SINK_W + RACK_W - 10)
drv2 = (320, Y(u_rack - S - 60), 760)
gbox(gL, "Driver_2_Kick_Wall", 290, ry(u_rack - S - 160, 200), 745, 60, 200, 30, C_METAL)
cable("Cable_24V_Ch2", [drv2, (drv2[0], drv2[1], PLINTH_H + CLAD + 3), (x_kick + LED_W / 2, drv2[1], PLINTH_H + CLAD + 3),
                        (x_kick + LED_W / 2, drv2[1], PLINTH_H - LED_H / 2)], "24V")
cable("Cable_230V_Ch2", [(-15, Y(u_rack - 200), 450), (5, Y(u_rack - 200), 450), (5, Y(u_rack - 200), 760),
                         (290, Y(u_rack - 200), 760)], "230V")
gbox(gL, "Sensor_Kick_Wall", x_kick, ry(u_rack + 100, 40), PLINTH_H - 20, 20, 40, 20, C_BLACK)

gLI = group("Lighting_Island", gI)
xi_kick = back_x - (BASE_D - PLINTH_SETBACK + 5) - LED_W
led("LED_Kick_Island", 3, xi_kick, cab_y0 + T2 + 5, PLINTH_H - LED_H, LED_W, cab_len - 2 * T2 - 10, gLI)
yi = cab_y0 + T2 + 120
drv3 = (back_x - S - 40, yi, 500)
gbox(gLI, "Driver_3_Kick_Island", back_x - S - 60, yi - 100, 485, 40, 200, 30, C_METAL)
cable("Cable_24V_Ch3", [drv3, (drv3[0], yi, PLINTH_H + CLAD + 3), (xi_kick + LED_W / 2, yi, PLINTH_H + CLAD + 3),
                        (xi_kick + LED_W / 2, yi, PLINTH_H - LED_H / 2)], "24V", gLI)
cable("Cable_230V_Ch3_Floor", [(-15, yi, 300), (-15, yi, -5), (back_x - S - 40, yi, -5),
                               (back_x - S - 40, yi, 485)], "230V", gLI)
gbox(gLI, "Sensor_Kick_Island", xi_kick - 20, cab_y0 + cab_len / 2 - 20, PLINTH_H - 20, 20, 40, 20, C_BLACK)

for ch, label in ((1, "under-cabinet"), (2, "toe-kick wall run"), (3, "toe-kick island")):
    m_ = led_len[ch] / 1000
    drv = next(w for w in (20, 30, 60, 100) if w >= m_ * LED_WPM * 1.3)
    hardware.append(("Lighting_LED", f"Ch{ch} {label}: 24 V COB LED strip 4000K {LED_WPM} W/m + Al profile "
                                     f"{LED_W}x{LED_H} with diffuser", f"{m_:.2f} m", 1))
    hardware.append(("Lighting_LED", f"Ch{ch} {label}: 24 V LED driver {drv} W", "-", 1))
hardware.append(("Lighting_LED", "Wall switch (backsplash) for the under-cabinet lights", "-", 1))
hardware.append(("Lighting_LED", "PIR motion sensor for 24 V strip (toe-kick)", "-", 2))
hardware.append(("Lighting_LED", "24 V cable 2 x 0.75 mm2 (+20% spare)", f"{cable_len['24V'] * 1.2 / 1000:.1f} m", 1))
hardware.append(("Lighting_LED", "230 V feed to drivers / switch (electrician, in conduit)",
                 f"{cable_len['230V'] * 1.2 / 1000:.1f} m", 1))
hardware.append(("Lighting_LED", "Cable grommets 10 mm (cabinet top / bottom holes)", "-", 8))

# hinges: aluminium-frame doors take frame hinges (no cup boring), count by door height
for mod, kind, fw_, fh_ in fronts:
    if kind == "Door":
        hardware.append((mod, "Hinge for aluminium-frame doors, soft-close, clip-on", "-",
                         2 if fh_ <= 900 else 3 if fh_ <= 1600 else 4))

# ================= ROOM =================
gR = group("Room", root)
t = WALL_T
gbox(gR, "Floor", -t, 0, -10, ROOM_W + 2 * t, ROOM_L + t, 10, C_FLOOR)
gbox(gR, "Wall_Back", -t, ROOM_L, 0, ROOM_W + 2 * t, t, ROOM_H, C_WALL)
gbox(gR, "Wall_Left", -t, 0, 0, t, ROOM_L, ROOM_H, C_WALL)
gbox(gR, "Wall_Right", ROOM_W, 0, 0, t, ROOM_L, ROOM_H, C_WALL)

doc.recompute()

print("Aluminium kitchen - left wall run (from the open front), mm:")
for label, a, b in [("end panel", 0, u_filler), ("filler", u_filler, u_fridge), ("fridge bay", u_fridge, u_tall),
                    ("tall panel", u_tall, u_sink), ("sink base", u_sink, u_rack), ("rack base", u_rack, u_stove),
                    ("stove bay", u_stove, u_wpanel), ("washer panel", u_wpanel, u_washer),
                    ("washer bay", u_washer, u_end), ("end panel", u_end, ROOM_L)]:
    print(f"  {label:13s} {a:7.1f} -> {b:7.1f}  ({b - a:6.1f})")
print(f"Island {isl_len:.0f} x {ctop_x1 - ctop_x0:.0f}, Y {isl_y0:.0f}-{isl_y0 + isl_len:.0f}")

# ---------------- colours + views (GUI only) ----------------
if App.GuiUp:
    import FreeCADGui as Gui
    for name, c in _colours.items():
        if doc.getObject(name):
            doc.getObject(name).ViewObject.ShapeColor = c
    for w in ("Wall_Left", "Wall_Back"):
        doc.getObject(w).ViewObject.Transparency = 70
    for n in _hidden:
        doc.getObject(n).ViewObject.Visibility = False
    for o in doc.Objects:
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
            if o.Name not in _hidden:
                o.ViewObject.Visibility = True

    shot("kitchen_alu_elevation.png", "viewRight", 1800, 1000, hide=("Wall_Right", "Wall_Left", "Floor", "Island"))
    shot("kitchen_alu_iso.png", "viewIsometric", 1600, 1200, hide=("Wall_Right",))
    # cladding off: shows the 2x1 frames, shelves supports and racks
    skin = tuple(o.Name for o in doc.Objects if rec.get(o.Name, [None] * 3)[2] in (M_CLAD,)
                 or o.Label.startswith(("Countertop", "Island_Countertop")))
    shot("kitchen_alu_frames.png", "viewIsometric", 1600, 1200, hide=("Wall_Right", "Stool_1", "Stool_2", "Stool_3") + skin)
    exec(open(os.path.join(OUT_DIR, "Kitchen_OpenClose.FCMacro")).read().split("if __name__")[0])
    kitchen_fronts(doc, True)
    shot("kitchen_alu_iso_fronts_open.png", "viewIsometric", 1600, 1200, hide=("Wall_Right",))
    kitchen_fronts(doc, False)
    v.viewIsometric()
    v.fitAll()

# ---------------- cut list + hardware (CSV + FreeCAD spreadsheets) + save ----------------
agg = {}
for name, (mod, part, mat, L, W, note) in rec.items():
    if doc.getObject(name) is None:
        continue
    generic = re.sub(r"_(A|B|lo|hi|\d+)(?=_|$)", "", part)       # Post_Back_A + Post_Back_B -> Post_Back x2
    key = (mod, generic, mat, L, W, note)
    agg[key] = agg.get(key, 0) + 1
for mod, part, mat, L, W, note in extra:
    agg[(mod, part, mat, L, W, note)] = agg.get((mod, part, mat, L, W, note), 0) + 1
with open(os.path.join(OUT_DIR, CUT_LIST), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Part", "Material", "Qty", "Length_mm", "Width_mm", "Note"])
    for (mod, part, mat, L, W, note), q in sorted(agg.items()):
        wr.writerow([mod, part, mat, q, L, W, note])
with open(os.path.join(OUT_DIR, HARDWARE), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Module", "Item", "Size_mm", "Qty"])
    for row in hardware:
        wr.writerow(row)

import importlib, sys
sys.path.insert(0, OUT_DIR)
import kitchen_cutlist_core, kitchen_spreadsheets, kitchen_alu_core, kitchen_alu_sheets
for mod_ in (kitchen_cutlist_core, kitchen_spreadsheets, kitchen_alu_core, kitchen_alu_sheets):
    importlib.reload(mod_)
kitchen_alu_sheets.add(doc)
doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))
tot = {}
for (mod, part, mat, L, W, note), q in agg.items():
    tot[mat] = tot.get(mat, 0) + q
print("Cut list pieces by material:", tot)
