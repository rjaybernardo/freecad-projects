# Cut list + materials workbook and cutting diagrams for Kitchen v2 (3/4" PVC board).
# Reads the CSVs written by build_kitchen_v2.py (run that in FreeCAD first), then:
#   - nests every PVC part onto 4x8 sheets (guillotine, best-area fit, parts may rotate: PVC has no grain)
#   - writes Kitchen_v2_CutList_Materials.xlsx and kitchen_v2_cutting_diagram.pdf
# Run:  python3 make_kitchen_cutlist.py   (needs openpyxl + matplotlib)

import os

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

from kitchen_cutlist_core import (CTOP, KERF, OUT_DIR, PVC6, PVC18, SHEET_L, SHEET_W, TRIM, WALL_CABINETS,
                                  hw_category, hw_qty_unit, layout, read_hardware, read_rows)

XLSX = os.path.join(OUT_DIR, "Kitchen_v2_CutList_Materials.xlsx")
PDF = os.path.join(OUT_DIR, "kitchen_v2_cutting_diagram.pdf")

rows = read_rows()
hw = read_hardware()
layouts, sheet_of = layout(rows)

# ---------------------------------------------------------------- workbook
F = "Arial"
H_FILL = PatternFill("solid", fgColor="1F3A5F")
H_FONT = Font(name=F, bold=True, color="FFFFFF")
B_FONT = Font(name=F)
BOLD = Font(name=F, bold=True)
TITLE = Font(name=F, bold=True, size=14)
NOTE = Font(name=F, italic=True, color="666666", size=9)
INPUT = Font(name=F, color="0000FF")
LINK = Font(name=F, color="008000")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()


def header(ws, row, names, widths):
    for c, (n, w) in enumerate(zip(names, widths), 1):
        cell = ws.cell(row=row, column=c, value=n)
        cell.font, cell.fill, cell.border = H_FONT, H_FILL, BOX
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.freeze_panes = ws.cell(row=row + 1, column=1)


def put(ws, row, col, val, font=B_FONT, fmt=None):
    c = ws.cell(row=row, column=col, value=val)
    c.font, c.border = font, BOX
    if fmt:
        c.number_format = fmt
    return c


# ---- Cut List
cl = wb.active
cl.title = "Cut List"
cl["A1"] = "Kitchen v2 - Cut List (all sizes in mm, finished size, no edge allowance)"
cl["A1"].font = TITLE
cl["A2"] = ("From build_kitchen_v2.py. PVC has no grain: parts may be rotated on the sheet. "
            "'Notched' parts: cut the full rectangle, then the notch shown in the FreeCAD model.")
cl["A2"].font = NOTE
HR = 4
header(cl, HR, ["Ref #", "Module", "Part", "Qty", "Length", "Width", "Thickness", "Material", "Area m²",
                "Note", "On sheet(s)"], [7, 24, 30, 6, 9, 9, 10, 18, 9, 34, 14])
first = HR + 1
for i, r in enumerate(rows):
    rr = first + i
    ref, mod, part, q, L, W, th, mat, note = r
    put(cl, rr, 1, ref)
    put(cl, rr, 2, mod)
    put(cl, rr, 3, part)
    put(cl, rr, 4, q, fmt="0")
    put(cl, rr, 5, L, fmt="0.0")
    put(cl, rr, 6, W, fmt="0.0")
    put(cl, rr, 7, th, fmt="0")
    put(cl, rr, 8, mat)
    put(cl, rr, 9, f"=D{rr}*E{rr}*F{rr}/1000000", fmt="0.000")
    put(cl, rr, 10, note)
    put(cl, rr, 11, ", ".join(sorted(set(sheet_of.get(ref, [])))))
last = first + len(rows) - 1
tr = last + 1
put(cl, tr, 3, "Total pieces / area", BOLD)
put(cl, tr, 4, f"=SUM(D{first}:D{last})", BOLD, "0")
put(cl, tr, 9, f"=SUM(I{first}:I{last})", BOLD, "0.00")
cl.auto_filter.ref = f"A{HR}:K{last}"
RNG = lambda col: f"'Cut List'!${col}${first}:${col}${last}"

# ---- Fronts & Hinges
fr = wb.create_sheet("Fronts & Hinges")
fr["A1"] = "Doors and drawer fronts"
fr["A1"].font = TITLE
fr["A2"] = ("Hinges: 35 mm cup, soft-close, clip-on. Rule used: door long side <= 900 mm -> 2 hinges, "
            "<= 1600 mm -> 3, longer -> 4 (typical hinge-maker guidance; check your hinge brand).")
fr["A2"].font = NOTE
header(fr, 4, ["Ref #", "Module", "Part", "Qty", "Long side", "Short side", "Type", "Hinges", "Handle / latch",
               "Front edge length m"], [7, 24, 22, 6, 10, 10, 14, 9, 14, 16])
fronts = [r for r in rows if r[2].startswith(("Door", "DrawerFront", "Kick_DrawerFront"))]
f0 = 5
for i, r in enumerate(fronts):
    rr = f0 + i
    ref, mod, part, q, L, W = r[:6]
    kind = "Door" if part.startswith("Door") else ("Toe-kick drawer" if part.startswith("Kick") else "Drawer")
    put(fr, rr, 1, ref)
    put(fr, rr, 2, mod)
    put(fr, rr, 3, part)
    put(fr, rr, 4, q)
    put(fr, rr, 5, L, fmt="0.0")
    put(fr, rr, 6, W, fmt="0.0")
    put(fr, rr, 7, kind)
    put(fr, rr, 8, f'=IF(G{rr}="Door",D{rr}*IF(E{rr}<=900,2,IF(E{rr}<=1600,3,4)),0)', fmt="0")
    put(fr, rr, 9, f'=IF(G{rr}="Toe-kick drawer",0,D{rr})', fmt="0")
    put(fr, rr, 10, f"=D{rr}*2*(E{rr}+F{rr})/1000", fmt="0.00")
fl_ = f0 + len(fronts) - 1
ft = fl_ + 1
put(fr, ft, 3, "Totals", BOLD)
put(fr, ft, 4, f"=SUM(D{f0}:D{fl_})", BOLD, "0")
put(fr, ft, 8, f"=SUM(H{f0}:H{fl_})", BOLD, "0")
put(fr, ft, 9, f"=SUM(I{f0}:I{fl_})", BOLD, "0")
put(fr, ft, 10, f"=SUM(J{f0}:J{fl_})", BOLD, "0.00")

# ---- Sheet Layout
sl = wb.create_sheet("Sheet Layout")
sl["A1"] = "Nesting on 4x8 sheets (x, y from the sheet corner, mm) - see kitchen_v2_cutting_diagram.pdf"
sl["A1"].font = TITLE
sl["A2"] = f"Sheet {SHEET_L} x {SHEET_W}, {TRIM} mm edge trim, {KERF} mm saw kerf, guillotine cuts."
sl["A2"].font = NOTE
header(sl, 4, ["Sheet", "Material", "Ref #", "Module", "Part", "X", "Y", "Along 2440", "Along 1220", "Rotated"],
       [8, 18, 7, 24, 30, 8, 8, 11, 11, 9])
info = {r[0]: r for r in rows}
rr = 5
for mat, sheets in layouts.items():
    tag = "A" if mat == PVC18 else "B"
    for si, placed in enumerate(sheets, 1):
        for ref, x, y, l, w, rot in sorted(placed, key=lambda p: (p[2], p[1])):
            for c, v in enumerate([f"{tag}{si}", mat, ref, info[ref][1], info[ref][2], round(x), round(y),
                                   round(l, 1), round(w, 1), "yes" if rot else ""], 1):
                put(sl, rr, c, v)
            rr += 1

# ---- Summary (sheet counts come from the nesting above)
sm = wb.create_sheet("Summary", 0)
sm["A1"] = "Kitchen v2 - Cut list & materials summary"
sm["A1"].font = TITLE
sm["A2"] = "Material: 3/4\" PVC board (18 mm) for every cabinet panel; 6 mm PVC for toe-kick drawer bottoms."
sm["A2"].font = NOTE
header(sm, 4, ["Item", "Value", "Unit", "Basis"], [38, 12, 10, 70])
summary = [
    ("PVC 18 mm pieces", f"=SUMIFS({RNG('D')},{RNG('H')},\"{PVC18}\")", "pcs", "Cut List"),
    ("PVC 18 mm part area", f"=SUMIFS({RNG('I')},{RNG('H')},\"{PVC18}\")", "m²", "Cut List"),
    ("PVC 18 mm sheets (4x8)", len(layouts[PVC18]), "sheets",
     f"Nested by make_kitchen_cutlist.py ({KERF} mm kerf, {TRIM} mm trim) - see Sheet Layout / PDF"),
    ("PVC 18 mm sheet yield", "=B6/(B7*2.44*1.22)", "%", "part area / sheet area"),
    ("PVC 6 mm pieces", f"=SUMIFS({RNG('D')},{RNG('H')},\"{PVC6}\")", "pcs", "Cut List"),
    ("PVC 6 mm sheets (4x8)", len(layouts[PVC6]), "sheets", "Nested (toe-kick drawer bottoms)"),
    ("Countertop pieces", f"=SUMIFS({RNG('D')},{RNG('H')},\"{CTOP}\")", "pcs", "Fabricator templates on site"),
    ("Hinges", "='Fronts & Hinges'!H" + str(ft), "pcs", "Fronts & Hinges sheet"),
]
for i, (a, b, c, d) in enumerate(summary):
    r_ = 5 + i
    put(sm, r_, 1, a)
    cell = put(sm, r_, 2, b, INPUT if isinstance(b, int) else B_FONT, "0.0%" if c == "%" else "0.00" if c == "m²" else "0")
    put(sm, r_, 3, c)
    put(sm, r_, 4, d)
sm["B7"].comment = Comment("Computed by the nesting in make_kitchen_cutlist.py; re-run it after model changes.", "Claude")
sm["A15"] = "Tip: buy 1 spare 18 mm sheet for cutting mistakes and future repairs."
sm["A15"].font = NOTE

# ---- Materials
mt = wb.create_sheet("Materials", 1)
mt["A1"] = "List of materials"
mt["A1"].font = TITLE
mt["A2"] = ("Quantities in black are formulas; blue are counts taken from the model or rules of thumb (see Basis). "
            "Add a Unit Price column for your supplier quotes.")
mt["A2"].font = NOTE
header(mt, 4, ["Category", "Item", "Specification", "Qty", "Unit", "Basis / note"], [16, 46, 34, 8, 8, 60])
M = []
M.append(("Board", "PVC board 3/4\" (18 mm), 4x8 ft", "1220 x 2440 x 18", "=Summary!B7", "sheets",
          "Nested sheets (Summary). +1 spare recommended"))
M.append(("Board", "PVC board 6 mm, 4x8 ft", "1220 x 2440 x 6", "=Summary!B10", "sheets",
          "Toe-kick drawer bottoms; offcuts usable for small parts"))
for r in rows:
    if r[7] == CTOP:
        M.append(("Countertop", f"Countertop - {r[1]}", f"{r[4]:.0f} x {r[5]:.0f} x 38, {r[8]}", r[3], "pc",
                  "Solid surface / granite / quartz; fabricator measures on site"))
M.append(("Fittings", "Concealed hinge 35 mm, soft-close, clip-on", "full overlay", "=Summary!B12", "pcs",
          "Fronts & Hinges sheet"))
M.append(("Fittings", "Handles or push-to-open latches", "per door / drawer front", f"='Fronts & Hinges'!I{ft}", "pcs",
          "Toe-kick drawers excluded (push-to-open runners)"))
M.append(("Fasteners", "Screws for PVC board (confirmat 7x50 or 4x40 coarse-thread)", "carcass joints",
          f"=ROUND(4*Summary!B5,-1)", "pcs", "~4 per panel (rule of thumb); pre-drill PVC"))
M.append(("Fasteners", "Short screws 4x16 (hinges, runners, rails)", "fittings",
          f"=8*Summary!B12+12*SUMIFS(D:D,B:B,\"*runner pair*\")", "pcs", "4 per hinge plate+cup, 6 per runner side"))
M.append(("Wall mount", "Wall-cabinet hanging bracket (adjustable) + rail", "pair per cabinet", 2 * WALL_CABINETS, "pcs",
          f"{WALL_CABINETS} wall cabinets in the model x 2"))
M.append(("Wall mount", "Masonry anchors / screws 8 mm", "for brackets + rails", 4 * WALL_CABINETS, "pcs",
          "2 per bracket"))
M.append(("Finishing", "PVC edge band 22 mm (optional)", "door / drawer front edges",
          f"=ROUNDUP('Fronts & Hinges'!J{ft}*1.1,0)", "m", "PVC board edges can stay bare; +10% waste"))
M.append(("Finishing", "Neutral-cure silicone, white/clear", "sink, countertop joints, backsplash", 3, "tubes",
          "rule of thumb"))
for (item, size), (q, mods) in hw.items():
    cat = hw_category(item, mods)
    q, spec, unit = hw_qty_unit(size, q)
    M.append((cat, item, spec, q, unit, ", ".join(sorted(set(mods)))))
for i, (cat, item, spec, q, unit, basis) in enumerate(M):
    r_ = 5 + i
    put(mt, r_, 1, cat)
    put(mt, r_, 2, item)
    put(mt, r_, 3, spec)
    is_formula = isinstance(q, str) and q.startswith("=")
    put(mt, r_, 4, q, B_FONT if is_formula else INPUT, "0.0" if isinstance(q, float) else "0")
    put(mt, r_, 5, unit)
    put(mt, r_, 6, basis)
    mt.cell(row=r_, column=2).alignment = Alignment(wrap_text=True, vertical="top")
    mt.cell(row=r_, column=6).alignment = Alignment(wrap_text=True, vertical="top")
mt.auto_filter.ref = f"A4:F{4 + len(M)}"

wb.save(XLSX)

# ---------------------------------------------------------------- cutting diagrams (PDF)
with PdfPages(PDF) as pdf:
    for mat, sheets in layouts.items():
        tag = "A" if mat == PVC18 else "B"
        for si, placed in enumerate(sheets, 1):
            fig, ax = plt.subplots(figsize=(11.69, 8.27))
            ax.add_patch(Rectangle((0, 0), SHEET_L, SHEET_W, fill=False, lw=1.5))
            used = 0
            for ref, x, y, l, w, rot in placed:
                used += l * w
                ax.add_patch(Rectangle((x, y), l, w, facecolor="#e8dcc3", edgecolor="#333", lw=0.8))
                r = info[ref]
                big = min(l, w) > 120
                txt = f"#{ref}\n{r[2][:22]}\n{l:.0f} x {w:.0f}" if big else f"#{ref} {l:.0f}x{w:.0f}"
                ax.text(x + l / 2, y + w / 2, txt, ha="center", va="center", fontsize=6.5 if big else 5,
                        rotation=0 if l >= w or not big else 90)
            ax.set_xlim(-30, SHEET_L + 30)
            ax.set_ylim(-30, SHEET_W + 30)
            ax.set_aspect("equal")
            ax.set_title(f"Sheet {tag}{si} of {len(sheets)} - {mat}, {SHEET_L} x {SHEET_W} "
                         f"(yield {used / (SHEET_L * SHEET_W):.0%}, kerf {KERF} mm)", fontsize=11)
            ax.set_xticks(range(0, SHEET_L + 1, 244))
            ax.set_yticks(range(0, SHEET_W + 1, 244))
            ax.tick_params(labelsize=7)
            pdf.savefig(fig)
            plt.close(fig)

print(f"{len(rows)} cut-list rows; PVC 18 sheets: {len(layouts[PVC18])}, PVC 6 sheets: {len(layouts[PVC6])}")
print("wrote", XLSX, "and", PDF)

# ---------------------------------------------------------------- cutlistoptimizer.com import files
# Panels -> Import From CSV (menu in the Panels roll-up); stock sheets -> same menu in the Stock roll-up.
# Columns are matched by heading. Countertops are left out (fabricator-made).
import csv
CLO_MAT = {PVC18: "PVC 18mm", PVC6: "PVC 6mm"}
with open(os.path.join(OUT_DIR, "cutlistoptimizer_panels.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Length", "Width", "Qty", "Label", "Material"])
    for ref, mod, part, q, L, W, th, mat, note in rows:
        if mat in CLO_MAT:
            wr.writerow([f"{max(L, W):g}", f"{min(L, W):g}", q, f"{ref} {mod} {part}", CLO_MAT[mat]])
with open(os.path.join(OUT_DIR, "cutlistoptimizer_stock.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["Length", "Width", "Qty", "Label", "Material"])
    for mat, label in CLO_MAT.items():
        wr.writerow([SHEET_L, SHEET_W, len(layouts[mat]) + 3, f"4x8 {label}", label])
# one file per board thickness (Length, Width, Qty, Label only): import with that board as the only stock
for mat, label in CLO_MAT.items():
    with open(os.path.join(OUT_DIR, f"cutlistoptimizer_{label.replace(' ', '_')}_boards.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["Length", "Width", "Qty", "Label"])
        for ref, mod, part, q, L, W, th, m, note in rows:
            if m == mat:
                wr.writerow([f"{max(L, W):g}", f"{min(L, W):g}", q, f"{ref} {mod} {part}"])
print("wrote cutlistoptimizer_panels.csv, cutlistoptimizer_stock.csv and one boards CSV per thickness")
