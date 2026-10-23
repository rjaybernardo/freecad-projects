# Cut list + materials spreadsheets inside Kitchen_Alu.FCStd (group "Alu_Cut_List_Materials").
# Called by build_kitchen_alu.py after it writes the CSVs. Totals are live formulas; bar / sheet counts come from
# the cutting plan at build time (re-run build_kitchen_alu.py after model changes).

import math

from kitchen_alu_core import (BAR_KERF, BAR_L, BAR_TRIM, BARS, KERF, M_CLAD, M_CTOP, M_HANDLE, M_PROF, M_TUBE, SPARE_BARS,
                              SHEET_L, SHEET_W, SPEC, TRIM, bar_used, counts, plan_all, read_hardware, read_rows)
from kitchen_cutlist_core import hw_category, hw_qty_unit
from kitchen_spreadsheets import _Sheet

GROUP = "Alu_Cut_List_Materials"


def add(doc):
    rows = read_rows()
    hw = read_hardware(__import__("kitchen_alu_core").HW_CSV)
    bars, sheets, where = plan_all(rows)
    wall, base, tube_pcs, clad_perim = counts(rows)

    grp = doc.getObject(GROUP) or doc.addObject("App::DocumentObjectGroup", GROUP)
    grp.Label = "Cut List & Materials (Aluminium)"

    # ---------------- Cut List
    cl = _Sheet(doc, grp, "AluCutList", "Cut List", "Cut list - aluminium kitchen (mm)",
                "Bars are listed at cut length (mitred profiles: long point). 'Bar / sheet' = cutting plan: "
                "T = 2x1, P = profile, H = profile with handle, C = cladding sheet.")
    cl.header(4, ["Ref #", "Module", "Part", "Material", "Qty", "Length", "Width", "Note", "Bar / sheet",
                  "Total m", "Area m2"], [50, 170, 190, 120, 40, 65, 65, 230, 130, 60, 60])
    first, span = 5, {}
    for i, r in enumerate(rows):
        rr = first + i
        ref, mod, part, mat, q, L, W, note = r
        for c, v in zip("ABCDEFGH", (ref, mod, part, mat, q, L, W, note)):
            if v != "":
                cl.put(f"{c}{rr}", v)
        cl.put(f"I{rr}", ", ".join(sorted(set(where.get(ref, [])))))
        if mat in BARS:
            cl.put(f"J{rr}", f"=round(E{rr} * F{rr}) / 1000")
        elif mat in (M_CLAD, M_CTOP):
            cl.put(f"K{rr}", f"=round(E{rr} * F{rr} * G{rr} / 1000) / 1000")
        a, _ = span.get(mat, (rr, rr))
        span[mat] = (a, rr)
    last = first + len(rows) - 1
    sub = {}
    for k, (mat, (a, b)) in enumerate(span.items()):
        r_ = last + 2 + k
        sub[mat] = r_
        cl.put(f"C{r_}", f"Subtotal {mat}")
        cl.put(f"E{r_}", f"=sum(E{a}:E{b})")
        col = "J" if mat in BARS else "K"
        cl.put(f"{col}{r_}", f"=sum({col}{a}:{col}{b})")
        cl.total_row(r_, 11)
    C = cl.name

    # ---------------- Bar Plan
    bp = _Sheet(doc, grp, "AluBarPlan", "Bar Plan",
                "Cutting plan for the bars (2x1, profile, profile with handle)",
                f"First-fit decreasing; {BAR_TRIM} mm squared off each bar end, {BAR_KERF} mm blade. "
                "Cut list: 'Ref #: length'. Keep offcuts > 300 for cleats / repairs.")
    bp.header(4, ["Bar", "Material", "Stock", "Pieces", "Cuts (Ref #: length)", "Used", "Offcut"],
              [55, 130, 55, 50, 700, 60, 60])
    rr = 5
    tag = {M_TUBE: "T", M_PROF: "P", M_HANDLE: "H"}
    for mat in BARS:
        for bi, bar in enumerate(bars[mat], 1):
            bp.put(f"A{rr}", f"{tag[mat]}{bi}")
            bp.put(f"B{rr}", mat)
            bp.put(f"C{rr}", BAR_L[mat])
            bp.put(f"D{rr}", len(bar))
            bp.put(f"E{rr}", ", ".join(f"{ref}: {L:g}" for ref, L in bar))
            bp.put(f"F{rr}", round(bar_used(bar), 1))
            bp.put(f"G{rr}", f"=C{rr} - F{rr} - {2 * BAR_TRIM}")
            rr += 1

    # ---------------- Cladding Layout
    sl = _Sheet(doc, grp, "AluCladLayout", "Cladding Layout",
                "Cladding nesting on 4x8 sheets (x, y from the sheet corner, mm) - see kitchen_alu_cutting_diagram.pdf",
                f"Sheet {SHEET_L} x {SHEET_W}, {TRIM} mm edge trim, {KERF} mm blade, guillotine cuts.")
    sl.header(4, ["Sheet", "Ref #", "Module", "Part", "X", "Y", "Along 2440", "Along 1220", "Rotated"],
              [55, 50, 170, 190, 55, 55, 75, 75, 60])
    info = {r[0]: r for r in rows}
    rr = 5
    for si, placed in enumerate(sheets, 1):
        for ref, x, y, l, w, rot in sorted(placed, key=lambda p: (p[2], p[1])):
            for c, v in zip("ABCDEFGHI", (f"C{si}", ref, info[ref][1], info[ref][2], round(x), round(y),
                                          round(l, 1), round(w, 1), "yes" if rot else "")):
                if v != "":
                    sl.put(f"{c}{rr}", v)
            rr += 1

    # ---------------- Summary
    sm = _Sheet(doc, grp, "AluSummary", "Summary", "Aluminium kitchen - cut list & materials summary",
                "Basic materials: 2x1 tube, cladding 4 mm, profile, profile with handle. Blue = from the cutting plan "
                "at build time.")
    sm.header(4, ["Item", "Value", "Unit", "Basis"], [260, 70, 60, 420])
    lines = []
    for mat in BARS:
        lines += [(f"{mat} pieces", f"={C}.E{sub[mat]}", "pcs", "Cut List"),
                  (f"{mat} total length", f"={C}.J{sub[mat]}", "m", "Cut List"),
                  (f"{mat} stock bars ({BAR_L[mat] / 1000:.2f} m)", len(bars[mat]), "bars", "Bar Plan"),
                  (f"{mat} yield", None, "%", "cut length / stock length")]
    lines += [("Cladding pieces", f"={C}.E{sub[M_CLAD]}", "pcs", "Cut List"),
              ("Cladding part area", f"={C}.K{sub[M_CLAD]}", "m2", "Cut List"),
              ("Cladding sheets (4x8)", len(sheets), "sheets", "Cladding Layout / PDF"),
              ("Cladding yield", None, "%", "part area / sheet area"),
              ("Countertop pieces", f"={C}.E{sub[M_CTOP]}" if M_CTOP in span else 0, "pcs", "fabricator templates")]
    cells = {}
    for i, (a, b, c, d) in enumerate(lines):
        r_ = 5 + i
        cells[a] = r_
        sm.put(f"A{r_}", a)
        if b is None:                                   # yield rows reference the 3 rows above
            if a == "Cladding yield":
                b = f"=round(B{r_ - 2} / (B{r_ - 1} * {SHEET_L * SHEET_W / 1e6}) * 100)"
            else:
                stock = BAR_L[a.replace(" yield", "")] / 1000
                b = f"=round(B{r_ - 2} / (B{r_ - 1} * {stock}) * 100)"
        sm.put(f"B{r_}", b, blue=isinstance(b, int))
        sm.put(f"C{r_}", c)
        sm.put(f"D{r_}", d)
    S = sm.name

    # ---------------- Materials
    mt = _Sheet(doc, grp, "AluMaterials", "Materials", "List of materials - aluminium",
                "Black qty = formula; blue = count from the model or rule of thumb (see Basis). Fill unit prices in "
                "column G (yellow).")
    mt.header(4, ["Category", "Item", "Specification", "Qty", "Unit", "Basis / note", "Unit price"],
              [110, 330, 260, 55, 50, 330, 80])
    M = []
    for mat in BARS:
        M.append(("Aluminium", mat, f"{SPEC[mat]}, {BAR_L[mat] / 1000:.2f} m",
                  f"={S}.B{cells[f'{mat} stock bars ({BAR_L[mat] / 1000:.2f} m)']} + {SPARE_BARS[mat]}", "bars",
                  f"Bar Plan + {SPARE_BARS[mat]} spare for mis-cuts"))
    M.append(("Aluminium", "Cladding", SPEC[M_CLAD], f"={S}.B{cells['Cladding sheets (4x8)']} + 1", "sheets",
              "Cladding Layout + 1 spare"))
    for r in rows:
        if r[3] == M_CTOP:
            M.append(("Countertop", f"Countertop - {r[1]}", f"{r[5]:.0f} x {r[6]:.0f} x 38, {r[2]}", r[4], "pc",
                      "fabricator measures on site"))
    M.append(("Fasteners", "Blind (pop) rivets 4 mm (5/32\") x 12 - frame joints", "aluminium",
              f"=ceil(4 * {S}.B{cells['2x1 pieces']} / 100) * 100", "pcs", "4 per 2x1 piece (2 per end)"))
    M.append(("Fasteners", "Rivets / self-drilling screws - cladding to frame", "every ~200 mm",
              math.ceil(clad_perim / 0.2 / 100) * 100, "pcs", f"cladding edge length {clad_perim:.0f} m / 0.2"))
    M.append(("Fasteners", "Internal corner cleats (1\" aluminium angle, ~40 mm, or 2x1 offcuts)", "frame joints",
              f"=ceil(2 * {S}.B{cells['2x1 pieces']} / 10) * 10", "pcs", "2 per 2x1 piece; from bar offcuts"))
    M.append(("Fasteners", "Panel adhesive / VHB tape for cladding (keeps panels flat)", "",
              math.ceil(clad_perim), "m", "cladding edge length"))
    M.append(("Wall mount", "Masonry anchors 8 mm through the 2x1 back rails", "wall cabinets x 4, base x 2",
              4 * wall + 2 * base + 8, "pcs", f"{wall} wall + {base} base cabinets + 4 framed panels x 2"))
    M.append(("Finishing", "Neutral-cure silicone, clear", "sink, counter joints, backsplash", 3, "tubes",
              "rule of thumb"))
    for (item, size), (q, mods) in hw.items():
        q, spec, unit = hw_qty_unit(size, q)
        cat = "Fittings" if "hinge" in item.lower() or "levelling" in item.lower() else hw_category(item, mods)
        M.append((cat, item, spec, q, unit, ", ".join(sorted(set(mods)))[:120]))
    for i, (cat, item, spec, q, unit, basis) in enumerate(M):
        r_ = 5 + i
        for c, v in zip("ABC", (cat, item, spec)):
            if v != "":
                mt.put(f"{c}{r_}", v)
        mt.put(f"D{r_}", q, blue=not (isinstance(q, str) and q.startswith("=")))
        mt.put(f"E{r_}", unit)
        mt.put(f"F{r_}", basis)
        mt.put(f"G{r_}", 0, blue=True)
    mtl = 4 + len(M)
    mt.s.setBackground(f"G5:G{mtl}", (1.0, 1.0, 0.6))
    mt.put(f"F{mtl + 1}", "Total (fill unit prices in column G)")
    mt.put(f"G{mtl + 1}", "=" + " + ".join(f"D{r} * G{r}" for r in range(5, mtl + 1)))
    mt.total_row(mtl + 1, 7)

    doc.recompute()
    print(f"Alu spreadsheets: {len(rows)} rows; bars " +
          ", ".join(f"{m} {len(bars[m])}" for m in BARS) + f"; cladding sheets {len(sheets)}")
    return grp
