# Cut list + materials as FreeCAD Spreadsheet objects inside Kitchen_v2.FCStd (group "Cut_List_Materials").
# Called by build_kitchen_v2.py after it writes the CSVs; same data and nesting as make_kitchen_cutlist.py.
# Totals are live spreadsheet formulas (edit a Qty in "Cut List" and the Summary / Materials follow).
# Sheet counts come from the nesting at build time: re-run build_kitchen_v2.py after model changes.

from kitchen_cutlist_core import (CTOP, KERF, PVC6, PVC18, SHEET_L, SHEET_W, TRIM, WALL_CABINETS_REV, csv_paths, front_kind,
                                  hinges_for, hw_category, hw_qty_unit, layout, read_hardware, read_rows)

GROUP = "Cut_List_Materials"
HEAD_BG = (0.12, 0.23, 0.37)
TOTAL_BG = (0.90, 0.93, 0.97)
INPUT_FG = (0.0, 0.0, 1.0)          # blue = count taken from the model / rule of thumb


def _col(i):
    return chr(ord("A") + i)


class _Sheet:
    def __init__(self, doc, grp, name, label, title, note):
        old = doc.getObject(name)
        if old is not None:
            doc.removeObject(name)
        self.s = doc.addObject("Spreadsheet::Sheet", name)
        self.s.Label = label
        grp.addObject(self.s)
        self.name = self.s.Name
        self.text("A1", title)
        self.s.setStyle("A1", "bold")
        self.text("A2", note)
        self.s.setStyle("A2", "italic")
        self.s.setForeground("A2", (0.4, 0.4, 0.4))

    def text(self, cell, v):
        self.s.set(cell, "'" + str(v))

    def put(self, cell, v, blue=False):
        if isinstance(v, str) and not v.startswith("="):
            self.text(cell, v)
        else:
            self.s.set(cell, str(round(v, 1) if isinstance(v, float) else v))
            if blue:
                self.s.setForeground(cell, INPUT_FG)

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


def add(doc, rev="v2"):
    cut_csv, hw_csv = csv_paths(rev)
    rows = read_rows(cut_csv)
    hw = read_hardware(hw_csv)
    WALL_CABINETS = WALL_CABINETS_REV[rev]
    name = f"Kitchen {rev}"
    layouts, sheet_of = layout(rows)

    grp = doc.getObject(GROUP) or doc.addObject("App::DocumentObjectGroup", GROUP)
    grp.Label = "Cut List & Materials"

    # ---------------- Cut List
    cl = _Sheet(doc, grp, "CutList", "Cut List", f"Cut list - {name}, 3/4\" PVC board (mm)",
                "PVC has no grain: parts may be rotated on the sheet. Notched parts: cut the full rectangle, "
                "then the notch shown in the model. 'On sheet' = cutting diagram page.")
    HR = 4
    cl.header(HR, ["Ref #", "Module", "Part", "Qty", "Length", "Width", "Thick", "Material", "Area m2", "Note",
                   "On sheet"], [50, 170, 190, 45, 65, 65, 50, 130, 70, 260, 110])
    first = HR + 1
    span = {}                                         # material -> (first row, last row)
    for i, r in enumerate(rows):
        rr = first + i
        ref, mod, part, q, L, W, th, mat, note = r
        for c, v in zip("ABCDEFGH", (ref, mod, part, q, L, W, th, mat)):
            cl.put(f"{c}{rr}", v)
        cl.put(f"I{rr}", f"=round(D{rr} * E{rr} * F{rr} / 1000) / 1000")
        cl.put(f"J{rr}", note)
        cl.put(f"K{rr}", ", ".join(sorted(set(sheet_of.get(ref, [])))))
        a, _ = span.get(mat, (rr, rr))
        span[mat] = (a, rr)
    last = first + len(rows) - 1
    tr = last + 1
    cl.put(f"C{tr}", "Total pieces / area")
    cl.put(f"D{tr}", f"=sum(D{first}:D{last})")
    cl.put(f"I{tr}", f"=sum(I{first}:I{last})")
    cl.total_row(tr, 11)
    # per-material subtotals here: FreeCAD can't sum a range on another sheet, so the Summary links these cells
    sub = {}
    for k, (mat, (a, b)) in enumerate(span.items()):
        r_ = tr + 2 + k
        sub[mat] = r_
        cl.put(f"C{r_}", f"Subtotal {mat}")
        cl.put(f"D{r_}", f"=sum(D{a}:D{b})")
        cl.put(f"I{r_}", f"=sum(I{a}:I{b})")
        cl.total_row(r_, 11)

    def cl_sum(col, mat):
        return f"{cl.name}.{col}{sub[mat]}"

    # ---------------- Fronts & Hinges
    fr = _Sheet(doc, grp, "Fronts", "Fronts & Hinges", "Doors and drawer fronts",
                "Hinges: 35 mm cup, soft-close, clip-on. Door long side <= 900 mm -> 2, <= 1600 -> 3, longer -> 4 "
                "(check your hinge brand).")
    fr.header(4, ["Ref #", "Module", "Part", "Qty", "Long side", "Short side", "Type", "Hinges/pc", "Hinges",
                  "Handles", "Edge m"], [50, 170, 150, 45, 70, 70, 110, 70, 60, 60, 60])
    f0, fi = 5, 0
    for r in rows:
        kind = front_kind(r[2])
        if kind is None:
            continue
        rr = f0 + fi
        fi += 1
        ref, mod, part, q, L, W = r[:6]
        long_, short = max(L, W), min(L, W)
        for c, v in zip("ABCDEFG", (ref, mod, part, q, long_, short, kind)):
            fr.put(f"{c}{rr}", v)
        fr.put(f"H{rr}", hinges_for(long_) if kind == "Door" else 0, blue=True)
        fr.put(f"I{rr}", f"=D{rr} * H{rr}")
        fr.put(f"J{rr}", f"=D{rr}" if kind != "Toe-kick drawer" else 0)
        fr.put(f"K{rr}", f"=round(D{rr} * 2 * (E{rr} + F{rr}) / 10) / 100")
    fl_ = f0 + fi - 1
    ft = fl_ + 1
    fr.put(f"C{ft}", "Totals")
    for c in "DIJK":
        fr.put(f"{c}{ft}", f"=sum({c}{f0}:{c}{fl_})")
    fr.total_row(ft, 11)

    # ---------------- Summary
    sm = _Sheet(doc, grp, "Summary", "Summary", f"{name} - cut list & materials summary",
                "3/4\" PVC (18 mm) for every cabinet panel; 6 mm PVC for toe-kick drawer bottoms. Blue = from the "
                "nesting at build time.")
    sm.header(4, ["Item", "Value", "Unit", "Basis"], [230, 70, 60, 420])
    n18, n6 = len(layouts[PVC18]), len(layouts.get(PVC6, []))
    summary = [
        ("PVC 18 mm pieces", f"={cl_sum('D', PVC18)}", "pcs", "Cut List"),
        ("PVC 18 mm part area", f"={cl_sum('I', PVC18)}", "m2", "Cut List"),
        ("PVC 18 mm sheets (4x8)", n18, "sheets", f"Nested ({KERF} mm kerf, {TRIM} mm trim) - Sheet Layout / PDF"),
        ("PVC 18 mm sheet yield", f"=round(B6 / (B7 * {SHEET_L * SHEET_W / 1e6}) * 100)", "%",
         "part area / sheet area"),
        ("PVC 6 mm pieces", f"={cl_sum('D', PVC6)}" if PVC6 in span else 0, "pcs", "Cut List"),
        ("PVC 6 mm sheets (4x8)", n6, "sheets", "Nested (toe-kick drawer bottoms)"),
        ("Countertop pieces", f"={cl_sum('D', CTOP)}" if CTOP in span else 0, "pcs", "Fabricator templates on site"),
        ("Hinges", f"={fr.name}.I{ft}", "pcs", "Fronts & Hinges"),
        ("Spare 18 mm sheet (recommended)", 1, "sheets", "cutting mistakes / repairs"),
    ]
    for i, (a, b, c, d) in enumerate(summary):
        r_ = 5 + i
        sm.put(f"A{r_}", a)
        sm.put(f"B{r_}", b, blue=isinstance(b, int))
        sm.put(f"C{r_}", c)
        sm.put(f"D{r_}", d)
    for alias, cell in (("pvc18_pieces", "B5"), ("pvc18_sheets", "B7"), ("pvc6_sheets", "B10"), ("hinges", "B12")):
        sm.s.setAlias(cell, alias)

    # ---------------- Materials
    mt = _Sheet(doc, grp, "Materials", "Materials", "List of materials",
                "Black qty = formula; blue = count from the model or rule of thumb (see Basis). Column G is free "
                "for unit prices.")
    mt.header(4, ["Category", "Item", "Specification", "Qty", "Unit", "Basis / note", "Unit price"],
              [100, 330, 200, 55, 50, 330, 80])
    S = sm.name
    M = [("Board", "PVC board 3/4\" (18 mm), 4x8 ft", "1220 x 2440 x 18", f"={S}.pvc18_sheets + {S}.B13", "sheets",
          "Nested sheets + 1 spare (Summary)"),
         ("Board", "PVC board 6 mm, 4x8 ft", "1220 x 2440 x 6", f"={S}.pvc6_sheets", "sheets",
          "Toe-kick drawer bottoms; offcuts usable for small parts")]
    for r in rows:
        if r[7] == CTOP:
            M.append(("Countertop", f"Countertop - {r[1]}", f"{r[4]:.0f} x {r[5]:.0f} x 38, {r[8]}", r[3], "pc",
                      "Solid surface / granite / quartz; fabricator measures on site"))
    M.append(("Fittings", "Concealed hinge 35 mm, soft-close, clip-on", "full overlay", f"={S}.hinges", "pcs",
              "Fronts & Hinges"))
    M.append(("Fittings", "Handles or push-to-open latches", "per door / drawer front", f"={fr.name}.J{ft}", "pcs",
              "Toe-kick drawers excluded (push-to-open runners)"))
    M.append(("Fasteners", "Screws for PVC board (confirmat 7x50 or 4x40 coarse-thread)", "carcass joints",
              f"=round(4 * {S}.pvc18_pieces / 10) * 10", "pcs", "~4 per panel (rule of thumb); pre-drill PVC"))
    short_screw_row = len(M)
    M.append(None)                                    # filled once the runner rows are known
    M.append(("Wall mount", "Wall-cabinet hanging bracket (adjustable) + rail", "pair per cabinet",
              2 * WALL_CABINETS, "pcs", f"{WALL_CABINETS} wall cabinets x 2"))
    M.append(("Wall mount", "Masonry anchors / screws 8 mm", "for brackets + rails", 4 * WALL_CABINETS, "pcs",
              "2 per bracket"))
    M.append(("Finishing", "PVC edge band 22 mm (optional)", "door / drawer front edges",
              f"=ceil({fr.name}.K{ft} * 1.1)", "m", "PVC board edges can stay bare; +10% waste"))
    M.append(("Finishing", "Neutral-cure silicone, white/clear", "sink, countertop joints, backsplash", 3, "tubes",
              "rule of thumb"))
    runner_rows = []
    for (item, size), (q, mods) in hw.items():
        q, spec, unit = hw_qty_unit(size, q)
        if "runner pair" in item:
            runner_rows.append(5 + len(M))
        M.append((hw_category(item, mods), item, spec, q, unit, ", ".join(sorted(set(mods)))))
    runners = " + ".join(f"D{r}" for r in runner_rows) or "0"
    M[short_screw_row] = ("Fasteners", "Short screws 4x16 (hinges, runners, rails)", "fittings",
                          f"=8 * {S}.hinges + 12 * ({runners})", "pcs", "4 per hinge plate+cup, 6 per runner side")
    for i, (cat, item, spec, q, unit, basis) in enumerate(M):
        r_ = 5 + i
        for c, v in zip("ABC", (cat, item, spec)):
            mt.put(f"{c}{r_}", v)
        mt.put(f"D{r_}", q, blue=not (isinstance(q, str) and q.startswith("=")))
        mt.put(f"E{r_}", unit)
        mt.put(f"F{r_}", basis)
    mtl = 4 + len(M)
    for r_ in range(5, mtl + 1):                      # unit price inputs (yellow), 0 until filled in
        mt.put(f"G{r_}", 0, blue=True)
    mt.s.setBackground(f"G5:G{mtl}", (1.0, 1.0, 0.6))
    mt.put(f"F{mtl + 1}", "Total (fill unit prices in column G)")
    mt.put(f"G{mtl + 1}", "=" + " + ".join(f"D{r} * G{r}" for r in range(5, mtl + 1)))
    mt.total_row(mtl + 1, 7)

    # ---------------- Sheet Layout
    sl = _Sheet(doc, grp, "SheetLayout", "Sheet Layout",
                f"Nesting on 4x8 sheets (x, y from the sheet corner, mm) - see kitchen_{rev}_cutting_diagram.pdf",
                f"Sheet {SHEET_L} x {SHEET_W}, {TRIM} mm edge trim, {KERF} mm saw kerf, guillotine cuts.")
    sl.header(4, ["Sheet", "Material", "Ref #", "Module", "Part", "X", "Y", "Along 2440", "Along 1220", "Rotated"],
              [55, 130, 50, 170, 190, 55, 55, 75, 75, 60])
    info = {r[0]: r for r in rows}
    rr = 5
    for mat, sheets in layouts.items():
        tag = "A" if mat == PVC18 else "B"
        for si, placed in enumerate(sheets, 1):
            for ref, x, y, l, w, rot in sorted(placed, key=lambda p: (p[2], p[1])):
                for c, v in zip("ABCDEFGHIJ", (f"{tag}{si}", mat, ref, info[ref][1], info[ref][2], round(x),
                                               round(y), round(l, 1), round(w, 1), "yes" if rot else "")):
                    if v != "":
                        sl.put(f"{c}{rr}", v)
                rr += 1

    doc.recompute()
    print(f"FreeCAD spreadsheets: {len(rows)} cut-list rows, {n18} x 18 mm + {n6} x 6 mm sheets, "
          f"{len(M)} material lines")
    return grp
