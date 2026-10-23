# Cut list + materials + hardware as FreeCAD Spreadsheet objects inside a bedroom model (group "Cut_List_Materials").
# Called by build_bed_v2.py / build_cabinet_v4.py after they write their CSVs; same data as the CSVs.
# Totals are live spreadsheet formulas: edit a Qty in "Cut List" and the area / sheet counts follow.
# Re-run the build script after model changes.

import csv
import os

GROUP = "Cut_List_Materials"
HEAD_BG = (0.12, 0.23, 0.37)
TOTAL_BG = (0.90, 0.93, 0.97)
SHEET_L, SHEET_W = 2440, 1220          # 4 x 8 ft plywood sheet
WASTE = 0.25                           # cutting waste allowance
BAND_WASTE = 0.10                      # edge banding trim / waste allowance
BAND_ROLL = 10                         # edge banding sold in 10 m rolls (Shopee)
# laminated parts that stay hidden get no edge banding by default (backs, drawer boxes, plinths)
BAND_SKIP = ("Back", "Drawer_Back", "Drawer_Bottom", "Drawer_Side", "Plinth", "Scribe", "Headboard", "Upholstered")


def _col(i):
    return chr(ord("A") + i)


class _Sheet:
    def __init__(self, doc, grp, name, label, title, note):
        if doc.getObject(name) is not None:
            doc.removeObject(name)
        self.s = doc.addObject("Spreadsheet::Sheet", name)
        self.s.Label = label
        grp.addObject(self.s)
        self.text("A1", title)
        self.s.setStyle("A1", "bold")
        self.text("A2", note)
        self.s.setStyle("A2", "italic")
        self.s.setForeground("A2", (0.4, 0.4, 0.4))

    def text(self, cell, v):
        self.s.set(cell, "'" + str(v))

    def put(self, cell, v):
        if isinstance(v, str) and not v.startswith("="):
            self.text(cell, v)
        else:
            self.s.set(cell, str(v))

    def header(self, row, names, widths):
        for i, (n, w) in enumerate(zip(names, widths)):
            self.text(f"{_col(i)}{row}", n)
            self.s.setColumnWidth(_col(i), w)
        rng = f"A{row}:{_col(len(names) - 1)}{row}"
        self.s.setStyle(rng, "bold")
        self.s.setBackground(rng, HEAD_BG)
        self.s.setForeground(rng, (1, 1, 1))

    def total_row(self, row, ncols):
        rng = f"A{row}:{_col(ncols - 1)}{row}"
        self.s.setStyle(rng, "bold")
        self.s.setBackground(rng, TOTAL_BG)


def _num(v):
    f = float(v)
    return int(f) if f == int(f) else f


def _band_edges(row):
    """Default banded edges (long, short): all 4 edges of visible laminated panels, none on raw / hidden parts."""
    if float(row["Thickness_mm"]) < 19 or row["Part"].startswith(BAND_SKIP):
        return 0, 0
    return 2, 2


def add(doc, cut_csv, hardware_csv=None, title="Cut list"):
    grp = doc.getObject(GROUP) or doc.addObject("App::DocumentObjectGroup", GROUP)
    with open(cut_csv) as f:
        rows = list(csv.DictReader(f))

    # ---------------- Cut List ----------------
    cl = _Sheet(doc, grp, "CutList", "Cut List", title,
                f"From {os.path.basename(cut_csv)}. Laminated = 18 mm ply + HPL both faces (19.6); "
                "raw = plain 18 mm ply. Band L / Band W = banded edges along the length / width (0-2); "
                "edit them or Qty and the totals follow.")
    cols = ["Module", "Part", "Qty", "Length mm", "Width mm", "Thick mm", "Edge work / notes",
            "Laminated m2", "Raw ply m2", "Band L", "Band W", "Edge band m"]
    cl.header(4, cols, [150, 170, 50, 80, 80, 70, 330, 95, 85, 60, 60, 95])
    r0 = 5
    for i, row in enumerate(rows):
        r = r0 + i
        cl.put(f"A{r}", row["Module"])
        cl.put(f"B{r}", row["Part"])
        cl.put(f"C{r}", _num(row["Qty"]))
        cl.put(f"D{r}", _num(row["Length_mm"]))
        cl.put(f"E{r}", _num(row["Width_mm"]))
        cl.put(f"F{r}", _num(row["Thickness_mm"]))
        cl.put(f"G{r}", row["Edge_Work"])
        cl.put(f"H{r}", f"=F{r} > 19 ? C{r} * D{r} * E{r} / 1e6 : 0")
        cl.put(f"I{r}", f"=F{r} > 19 ? 0 : C{r} * D{r} * E{r} / 1e6")
        band_l, band_w = _band_edges(row)
        cl.put(f"J{r}", band_l)
        cl.put(f"K{r}", band_w)
        cl.put(f"L{r}", f"=C{r} * (J{r} * D{r} + K{r} * E{r}) / 1000")
    r1 = r0 + len(rows) - 1
    rt = r1 + 1
    cl.put(f"A{rt}", "TOTAL")
    cl.put(f"C{rt}", f"=sum(C{r0}:C{r1})")
    cl.put(f"H{rt}", f"=sum(H{r0}:H{r1})")
    cl.put(f"I{rt}", f"=sum(I{r0}:I{r1})")
    cl.put(f"L{rt}", f"=sum(L{r0}:L{r1})")
    cl.total_row(rt, len(cols))
    cl.s.setAlias(f"H{rt}", "lam_m2")
    cl.s.setAlias(f"I{rt}", "raw_m2")
    cl.s.setAlias(f"C{rt}", "parts")
    cl.s.setAlias(f"L{rt}", "band_m")

    # ---------------- Materials ----------------
    mt = _Sheet(doc, grp, "Materials", "Materials", "Materials summary",
                f"4 x 8 ft sheets ({SHEET_L} x {SHEET_W} mm) incl. {WASTE:.0%} cutting waste - "
                "check against a nesting run before buying.")
    mt.header(4, ["Material", "Area m2", "Sheets (4x8)", "Note"], [300, 80, 95, 330])
    sheet_m2 = SHEET_L * SHEET_W / 1e6
    for r, (name, alias, note) in enumerate([
            ('3/4" marine plywood, HPL both faces', "lam_m2", "visible panels: carcass, doors, fronts, rails"),
            ('3/4" marine plywood, raw', "raw_m2", "hidden parts: backs, bottoms, drawer boxes, plinths")], start=5):
        mt.put(f"A{r}", name)
        mt.put(f"B{r}", f"=CutList.{alias}")
        mt.put(f"C{r}", f"=ceil(B{r} / {sheet_m2:.4f} * {1 + WASTE})")
        mt.put(f"D{r}", note)
    mt.put("A7", "TOTAL")
    mt.put("B7", "=B5 + B6")
    mt.put("C7", "=C5 + C6")
    mt.put("D7", "=CutList.parts")
    mt.total_row(7, 4)
    mt.text("D8", "(D7 = number of parts)")
    mt.header(10, ["Edge banding", "Metres", f"Rolls ({BAND_ROLL} m)", "Note"], [300, 80, 95, 330])
    mt.put("A11", "PVC edge banding 22 mm x 1 mm, laminate colour")
    mt.put("B11", "=CutList.band_m")
    mt.put("C11", f"=ceil(B11 * {1 + BAND_WASTE} / {BAND_ROLL})")
    mt.put("D11", f"incl. {BAND_WASTE:.0%} trim waste; banded edges set per part in Cut List (Band L / Band W)")

    # ---------------- Hardware ----------------
    if hardware_csv and os.path.exists(hardware_csv):
        with open(hardware_csv) as f:
            hw = list(csv.DictReader(f))
        hs = _Sheet(doc, grp, "Hardware", "Hardware", "Hardware", f"From {os.path.basename(hardware_csv)}.")
        hs.header(4, ["Item", "Qty", "Note"], [420, 50, 420])
        for i, row in enumerate(hw):
            r = 5 + i
            hs.put(f"A{r}", row["Item"])
            hs.put(f"B{r}", _num(row["Qty"]))
            hs.put(f"C{r}", row["Note"])
    doc.recompute()
    return grp
