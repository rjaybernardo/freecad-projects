# TechDraw drawing set for the bed wall unit (storage bed + side cabinets + bridge), in its own file.
# Reads Bed_Wall_Unit_v2.FCStd (re-run build_bed_v2.py first if you changed it) and writes
# Bed_Wall_Unit_v2_Drawing.FCStd with three A3 sheets:
#   1. General arrangement  - front elevation, plan, side view, 1:25
#   2. Storage bed           - plan of the 6 boxes, foot-end elevation, side view, 1:15
#   3. Side cabinets + bridge - tower front + side, bridge front, 1:15
#
# Run inside FreeCAD (Macro > Macros... or the Python console):
#   exec(open("/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet/build_bed_drawing.py").read())
# or headless:  freecadcmd build_bed_drawing.py
# In the GUI it runs the build through freecadcmd, then opens the drawing.
# Export PDFs from FreeCAD: select a sheet > File > Export PDF.

import datetime
import os
import re
import FreeCAD as App
import Part

OUT_DIR = "/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet"
SRC = os.path.join(OUT_DIR, "Bed_Wall_Unit_v2.FCStd")
DOC_NAME = "Bed_Wall_Unit_v2_Drawing"
TEMPLATE = os.path.join(App.getResourceDir(), "Mod/TechDraw/Templates/ISO/A3_Landscape_ISO5457_minimal.svg")

# viewer stands at the foot of the bed looking at the headboard wall (-Y), so +X runs to the left
FRONT = (App.Vector(0, 1, 0), App.Vector(-1, 0, 0))
PLAN = (App.Vector(0, 0, 1), App.Vector(-1, 0, 0))      # headboard wall at the top
SIDE = (App.Vector(1, 0, 0), App.Vector(0, 1, 0))       # from the right: wall left, foot right

# drawer travel, read from the bed script so the "drawers open" view always matches it
_bed_src = open(os.path.join(OUT_DIR, "build_bed_v2.py")).read()
SIDE_TRAVEL = float(re.search(r"^SIDE_TRAVEL = ([\d.]+)", _bed_src, re.M).group(1))
FOOT_TRAVEL = float(re.search(r"^DRAWER_BOX_D = ([\d.]+)", _bed_src, re.M).group(1))


def build():
    for d in list(App.listDocuments().values()):
        if d.FileName == SRC or d.Name == DOC_NAME:
            App.closeDocument(d.Name)
    src = App.openDocument(SRC)
    doc = App.newDocument(DOC_NAME)


    def solids(group_name):
        """All solids under a source group (recursive), tufted foam replaced by its plain block."""
        out = []
        for o in src.getObject(group_name).OutListRecursive + [src.getObject(group_name)]:
            if o.TypeId == "App::DocumentObjectGroup" or not hasattr(o, "Shape") or not o.Shape.Solids:
                continue
            if o.Name == "Upholstery_Foam":
                b = o.Shape.BoundBox
                out.append(Part.makeBox(b.XLength, b.YLength, b.ZLength, App.Vector(b.XMin, b.YMin, b.ZMin)))
            elif not o.Name.startswith(("LED_", "Lift_Mechanism")):
                out.append(o.Shape.copy())
        return out


    def feature(name, shapes):
        f = doc.addObject("Part::Feature", name)
        f.Shape = Part.makeCompound(shapes)
        return f


    V = App.Vector
    tower_l = feature("Tower_Left", solids("Tower_Left"))
    towers = feature("Towers", solids("Tower_Left") + solids("Tower_Right"))
    bridge = feature("Bridge", solids("Bridge"))
    headboard = feature("Headboard", solids("Headboard"))
    bed = feature("Storage_Bed", solids("Storage_Bed"))
    # same boxes with every drawer pulled out (side drawers sideways, foot drawers forward)
    opened = []
    for g in src.getObject("Storage_Bed").Group:
        for o in g.Group:
            sh = o.Shape.copy()
            if o.Name.startswith("Drawer"):
                if g.Name.startswith("Side_Box"):
                    sh.translate(V(-SIDE_TRAVEL if g.Name.endswith("L") else SIDE_TRAVEL, 0, 0))
                elif g.Name.startswith("Foot_Box"):
                    sh.translate(V(0, FOOT_TRAVEL, 0))
            opened.append(sh)
    bed_open = feature("Storage_Bed_Open", opened)
    mattress = feature("Mattress", [src.getObject("Mattress_5x6").Shape.copy()])
    scribe = feature("Scribe", solids("Scribe_Strips"))
    unit = [towers, bridge, headboard, bed, mattress, scribe]
    doc.recompute()

    # key points from the source model
    def B(name):
        """Bounding box of an object, or of every solid under a group."""
        bb = App.BoundBox()
        o = src.getObject(name)
        for x in [o] + o.OutListRecursive:
            if x.TypeId != "App::DocumentObjectGroup" and hasattr(x, "Shape") and x.Shape.Solids \
                    and not x.Name.startswith(("LED_", "Lift_Mechanism")):
                bb.add(x.Shape.BoundBox)
        return bb


    tl, tr = B("Tower_Left"), B("Tower_Right")
    nsl, upl = B("Nightstand_Left"), B("Upper_Left")
    br, hb, sb, mt = B("Bridge"), B("Headboard"), B("Storage_Bed"), B("Mattress_5x6")
    head = B("Head_Box_L")
    side1, side2 = B("Side_Box_1L"), B("Side_Box_2L")
    drw = B("Foot_Box_L")
    shelf_open = B("Shelf_Open_Niche").ZMax
    shelf_lit = B("Shelf_Lit_Niche").ZMax


    # ---------------- page + view helpers ----------------
    def page(name, title, scale_txt, number):
        p = doc.addObject("TechDraw::DrawPage", name)
        t = doc.addObject("TechDraw::DrawSVGTemplate", name + "_Template")
        t.Template = TEMPLATE
        p.Template = t
        texts = t.EditableTexts
        texts.update({"title": title, "creator": "rjaybernardo", "scale": scale_txt,
                      "date_of_issue": datetime.date.today().isoformat(), "drawing_number": "BED-V2",
                      "sheet_number": f"{number}/3", "document_type": "Shop drawing",
                      "part_material": '3/4" marine plywood, HPL both faces',
                      "general_tolerances": "+/- 1 mm", "legal_owner_1": "Bedroom - 116 x 90 in room"})
        t.EditableTexts = texts
        return p


    view_page = {}


    def view(p, name, sources, direction, x, y, scale, label=None):
        v = doc.addObject("TechDraw::DrawViewPart", name)
        p.addView(v)
        v.Source = sources
        v.Direction, v.XDirection = direction
        v.ScaleType = "Custom"
        v.Scale = scale
        v.X, v.Y = x, y
        v.HardHidden = False
        v.SmoothVisible = False
        v.Caption = label or name.replace("_", " ")
        view_page[v.Name] = p
        return v


    def note(p, name, x, y, lines, size=3.5):
        a = doc.addObject("TechDraw::DrawViewAnnotation", name)
        p.addView(a)
        a.Text = lines
        a.TextSize = size
        a.X, a.Y = x, y
        return a


    dims = []   # (dim, view, p1, p2, kind, offset) resolved after the views are computed


    def dim(v, p1, p2, kind, offset):
        """Dimension between two 3D points; kind 'h' / 'v' = horizontal / vertical on the sheet,
        offset = distance (sheet mm) of the dimension line from the measured edge."""
        dims.append((v, p1, p2, kind, offset))


    # ================= SHEET 1: general arrangement 1:25 =================
    s = 1 / 25
    p1 = page("Sheet1_General", "Bed wall unit - general arrangement", "1:25", 1)
    vf = view(p1, "Front_Elevation", unit, FRONT, 95, 85, s, "FRONT ELEVATION (from foot of bed)")
    vp = view(p1, "Plan", unit, PLAN, 95, 210, s, "PLAN")
    vs = view(p1, "Side_View", unit, SIDE, 250, 85, s, "SIDE VIEW (from right)")
    # Sheet sides: in FRONT views model +X runs to the sheet LEFT, so the right tower (tr) is drawn on
    # the left and the left tower (tl) on the right. Offsets: 'h' + = up, 'v' + = sheet right.
    # front: widths below / above, height chain on the sheet right (tl side), bed height on the left
    dim(vf, V(tl.XMin, 0, tl.ZMax), V(tr.XMax, 0, tr.ZMax), "h", 8)
    dim(vf, V(tl.XMin, 0, 0), V(tl.XMax, 0, 0), "h", -6)
    dim(vf, V(sb.XMin, 0, 0), V(sb.XMax, 0, 0), "h", -6)
    dim(vf, V(tr.XMin, 0, 0), V(tr.XMax, 0, 0), "h", -6)
    dim(vf, V(tl.XMin, 0, 0), V(tl.XMin, 0, nsl.ZMax), "v", 6)
    dim(vf, V(tl.XMin, 0, 0), V(tl.XMin, 0, br.ZMin), "v", 13)
    dim(vf, V(tl.XMin, 0, 0), V(tl.XMin, 0, tl.ZMax), "v", 20)
    dim(vf, V(tr.XMax, 0, 0), V(tr.XMax, 0, sb.ZMax), "v", -6)
    # plan (wall at the top): bed width below the foot, bed length + tower depth on the sheet right
    dim(vp, V(sb.XMin, sb.YMax, sb.ZMax), V(sb.XMax, sb.YMax, sb.ZMax), "h", -6)
    dim(vp, V(tl.XMin, sb.YMin, sb.ZMax), V(tl.XMin, sb.YMax, sb.ZMax), "v", 13)
    dim(vp, V(tl.XMin, nsl.YMin, 0), V(tl.XMin, nsl.YMax, 0), "v", 6)
    # side (wall on the left, foot on the right)
    dim(vs, V(0, nsl.YMin, 0), V(0, nsl.YMax, 0), "h", -6)
    dim(vs, V(0, sb.YMin, 0), V(0, sb.YMax, 0), "h", -13)
    dim(vs, V(0, upl.YMin, upl.ZMax), V(0, upl.YMax, upl.ZMax), "h", 6)
    dim(vs, V(0, sb.YMax, 0), V(0, sb.YMax, sb.ZMax), "v", 6)
    note(p1, "Notes1", 300, 215, [
        "BED WALL UNIT v2 - storage bed 5 x 6 ft + side cabinets",
        "Room 116 x 90 in (2946 x 2286 mm); unit on the 90 in wall",
        "opposite the cabinet, centred, headboard against the wall.",
        "",
        "Side towers: 2-drawer nightstand, open niche, LED lit niche,",
        "tall door; bridge with 4 doors + 2 LED downlights.",
        "Storage bed: 4 side drawers, 2 foot drawers, 2 head lift-up (sheet 2).",
        "Handleless: 45 deg finger bevel on the back of pull edges.",
        "All dimensions in mm. Check room on site before cutting.",
    ])

    # ================= SHEET 2: storage bed 1:15 =================
    s2 = 1 / 15
    p2 = page("Sheet2_Storage_Bed", "Storage bed - side + foot drawers", "1:15", 2)
    bed_only = [bed]
    v2p = view(p2, "Bed_Plan", bed_only, PLAN, 80, 180, s2, "PLAN - BOXES (closed)")
    v2f = view(p2, "Bed_Foot_Elevation", bed_only, FRONT, 80, 55, s2, "FOOT END")
    v2s = view(p2, "Bed_Side", bed_only, SIDE, 250, 245, s2, "SIDE (side drawers)")
    s3 = 1 / 25
    v2o = view(p2, "Bed_Plan_Open", [bed_open], PLAN, 215, 145, s3, "PLAN - ALL DRAWERS OPEN 1:25")
    # closed plan (wall at the top, so +X runs to the sheet left; tl side = sheet right)
    dim(v2p, V(sb.XMin, sb.YMax, sb.ZMax), V(sb.XMax, sb.YMax, sb.ZMax), "h", -12)
    dim(v2p, V(drw.XMin, sb.YMax, sb.ZMax), V(drw.XMax, sb.YMax, sb.ZMax), "h", -6)
    dim(v2p, V(sb.XMin, sb.YMin, sb.ZMax), V(sb.XMin, sb.YMax, sb.ZMax), "v", 14)
    for bx in (head, side1, side2, drw):
        dim(v2p, V(sb.XMin, bx.YMin, sb.ZMax), V(sb.XMin, bx.YMax, sb.ZMax), "v", 6)
    dim(v2f, V(sb.XMin, sb.YMax, 0), V(sb.XMin, sb.YMax, sb.ZMax), "v", 6)
    dim(v2f, V(drw.XMin, sb.YMax, 0), V(drw.XMax, sb.YMax, 0), "h", -6)
    dim(v2s, V(0, sb.YMin, 0), V(0, sb.YMax, 0), "h", -6)
    for bx in (head, side1, side2, drw):
        dim(v2s, V(0, bx.YMin, sb.ZMax), V(0, bx.YMax, sb.ZMax), "h", 6)
    # open plan: drawer travel
    dim(v2o, V(sb.XMin - SIDE_TRAVEL, side1.YMin, sb.ZMax), V(sb.XMin, side1.YMin, sb.ZMax), "h", 4)
    dim(v2o, V(sb.XMin, sb.YMax, sb.ZMax), V(sb.XMin, sb.YMax + FOOT_TRAVEL, sb.ZMax), "v", 6)
    note(p2, "Notes2", 343, 150, [
        "STORAGE BED - 8 boxes, 19.6 mm laminated ply, bolted together",
        "Side drawers (4): slide out sideways into the gap beside",
        f"  the bed, 450 mm 3/4-extension runners = {SIDE_TRAVEL:.0f} mm travel;",
        "  the gap to the wall is ~351 mm - do not use longer travel.",
        f"Foot drawers (2): slide forward, 450 mm full-extension runners.",
        "Head row (2): behind the nightstands, where a drawer can't",
        "  open - lift-up lids hinged at the head edge, lid stays.",
        "Fronts: 45 deg bevel on the top edge, 25 mm finger gap.",
        "Box bottoms 18 mm ply on 20 mm cleats, 2x 30 mm vent holes.",
        "Non-slip mat under the mattress.",
        "See cut_list_bed_v2.csv + hardware_bed_v2.csv.",
    ], size=3.0)

    # ================= SHEET 3: side cabinets + bridge 1:15 =================
    p3 = page("Sheet3_Cabinets", "Side cabinets + bridge", "1:15", 3)
    v3f = view(p3, "Tower_Front", [tower_l], FRONT, 60, 135, s2, "LEFT TOWER - FRONT")
    v3s = view(p3, "Tower_Side", [tower_l], SIDE, 150, 135, s2, "TOWER - SIDE")
    v3b = view(p3, "Bridge_Front", [bridge], FRONT, 290, 230, s2, "BRIDGE - FRONT")
    dim(v3f, V(tl.XMin, 0, 0), V(tl.XMax, 0, 0), "h", -6)
    dim(v3f, V(tl.XMin, 0, 0), V(tl.XMin, 0, nsl.ZMax), "v", 6)
    dim(v3f, V(tl.XMin, 0, nsl.ZMax), V(tl.XMin, 0, shelf_open), "v", 6)
    dim(v3f, V(tl.XMin, 0, shelf_open), V(tl.XMin, 0, shelf_lit), "v", 6)
    dim(v3f, V(tl.XMin, 0, shelf_lit), V(tl.XMin, 0, tl.ZMax), "v", 6)
    dim(v3f, V(tl.XMin, 0, 0), V(tl.XMin, 0, tl.ZMax), "v", 13)
    dim(v3s, V(0, nsl.YMin, 0), V(0, nsl.YMax, 0), "h", -6)
    dim(v3s, V(0, upl.YMin, upl.ZMax), V(0, upl.YMax, upl.ZMax), "h", 6)
    dim(v3b, V(br.XMin, 0, br.ZMin), V(br.XMax, 0, br.ZMin), "h", -6)
    dim(v3b, V(br.XMin, 0, br.ZMin), V(br.XMin, 0, br.ZMax), "v", 6)
    note(p3, "Notes3", 300, 130, [
        f"TOWERS (x2, mirrored): {tl.XLength:.0f} W",
        f"  nightstand {nsl.YLength:.0f} D x {nsl.ZMax:.0f} H on 60 mm recessed plinth,",
        "  2 drawers, bevel top edge, 350 mm runners",
        f"  upper part {upl.YLength:.0f} D: open niche + power socket,",
        "  LED lit niche (strip under shelf), tall door to the top,",
        "  bevel bottom edge = pulled from the lit niche.",
        f"BRIDGE: {br.XLength:.0f} x {br.ZLength:.0f} x {br.YLength:.0f} D, 4 doors, bevel bottom edge,",
        "  2 LED downlights aimed at the headboard.",
        "HEADBOARD: 18 mm backer + 50 mm diamond-tufted upholstery.",
        "Fix towers + bridge to the wall (anti-tip).",
    ])

    doc.recompute()


    # ---------------- dimensions ----------------
    # Drawn as architectural tick dimensions: cosmetic lines on the view (dimension line, extension
    # lines, 45 deg ticks) + a text annotation. Unlike associative TechDraw dimensions they don't
    # depend on vertex numbering, so they stay correct whenever the views are recomputed.
    TEXT = 3.0          # text height, sheet mm
    EXT_GAP = 1.5       # gap between the part and the extension line, sheet mm
    EXT_OVER = 1.5      # extension line runs past the dimension line, sheet mm
    TICK = 1.2          # half length of the 45 deg tick, sheet mm


    def on_sheet(v, p):
        """Sheet position of a 3D point in view v (TechDraw keeps view y flipped)."""
        tag = v.makeCosmeticVertex3d(p)
        q = v.getCosmeticVertex(tag).Point
        v.removeCosmeticVertex(tag)
        return float(v.X) + q.x * v.Scale, float(v.Y) - q.y * v.Scale


    for n, (v, a, b, kind, off) in enumerate(dims):
        k = 1 / v.Scale                                     # sheet mm -> model mm
        xd = v.XDirection.normalize()
        up = v.Direction.cross(v.XDirection).normalize()
        t, nrm = (xd, up) if kind == "h" else (up, xd)      # along the dimension / offset direction
        sign = 1 if off >= 0 else -1
        # both ends on the same offset level (the one of the outermost point), then shifted by `off`
        base = max(a.dot(nrm), b.dot(nrm)) if sign > 0 else min(a.dot(nrm), b.dot(nrm))
        a2 = a + nrm * (base - a.dot(nrm) + off * k)
        b2 = b + nrm * (base - b.dot(nrm) + off * k)
        lines = [(a2, b2)]
        for p, p2 in ((a, a2), (b, b2)):
            lines.append((p + nrm * (sign * EXT_GAP * k) if abs((p2 - p).dot(nrm)) > EXT_GAP * k else p,
                          p2 + nrm * (sign * EXT_OVER * k)))
            tick = (t + nrm).normalize() * (TICK * k)
            lines.append((p2 - tick, p2 + tick))
        for p, q in lines:
            v.makeCosmeticLine3D(p, q, 1, 0.18)
        value = abs((b - a).dot(t))
        tx, ty = on_sheet(v, (a2 + b2) * 0.5 + nrm * (sign * (TEXT * 0.9) * k))
        txt = doc.addObject("TechDraw::DrawViewAnnotation", f"Dim_{v.Name}_{n}")
        view_page[v.Name].addView(txt)
        txt.Text = [f"{value:.0f}"]
        txt.TextSize = TEXT
        txt.X, txt.Y = tx, ty
        txt.Rotation = 0 if kind == "h" else 90

    doc.recompute()
    doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))
    App.closeDocument(src.Name)

    print(f"Saved {DOC_NAME}.FCStd: 3 sheets, {len(dims)} dimensions")


if App.GuiUp:
    # TechDraw computes views in a background thread in the GUI, which this script can't wait
    # for from a macro, so build headless with freecadcmd and open the result.
    import subprocess
    r = subprocess.run(["freecadcmd", os.path.join(OUT_DIR, "build_bed_drawing.py")], capture_output=True, text=True)
    print("\n".join(l for l in r.stdout.splitlines() if l.startswith("Saved")) or r.stdout[-500:])
    for d in list(App.listDocuments().values()):
        if d.Name == DOC_NAME:
            App.closeDocument(d.Name)
    App.openDocument(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))
else:
    build()
