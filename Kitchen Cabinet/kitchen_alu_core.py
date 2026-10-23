# Shared data for the aluminium kitchen (build_kitchen_alu.py -> kitchen_alu_cut_list.csv / kitchen_alu_hardware.csv).
# Standard library only: used inside FreeCAD (kitchen_alu_sheets.py) and by make_kitchen_alu_cutlist.py.
#   - bars (2x1, profile, profile with handle): first-fit-decreasing cutting plan on stock lengths
#   - cladding: guillotine nesting on 4x8 sheets (same nester as the PVC version)

import csv
import os

from kitchen_cutlist_core import nest, read_hardware, SHEET_L, SHEET_W, KERF, TRIM  # noqa: F401

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
CUT_CSV = os.path.join(OUT_DIR, "kitchen_alu_cut_list.csv")
HW_CSV = os.path.join(OUT_DIR, "kitchen_alu_hardware.csv")

M_TUBE, M_CLAD, M_PROF, M_HANDLE, M_CTOP = "2x1", "Cladding", "Profile", "Profile with handle", "Countertop"
BARS = (M_TUBE, M_PROF, M_HANDLE)
ORDER = {M_TUBE: 0, M_PROF: 1, M_HANDLE: 2, M_CLAD: 3, M_CTOP: 4}

# stock lengths (mm) - 21 ft (6.40 m) is the usual length for aluminium bars; change to your supplier's
BAR_L = {M_TUBE: 6400, M_PROF: 6400, M_HANDLE: 6400}
SPARE_BARS = {M_TUBE: 2, M_PROF: 1, M_HANDLE: 1}   # mis-cuts: several planned bars have ~0 offcut
BAR_KERF = 3          # mitre-saw blade
BAR_TRIM = 10         # squared off each bar end before cutting
SPEC = {M_TUBE: '1" x 2" aluminium tube (25.4 x 50.8)',
        M_PROF: "cabinet door / front frame profile (20 face x 20 deep, with insert groove)",
        M_HANDLE: "profile with integrated handle (45 face)",
        M_CLAD: "aluminium cladding sheet 4 mm, 4x8 ft",
        M_CTOP: "38 mm solid surface / granite / quartz"}


def read_rows(path=CUT_CSV):
    """[ref, module, part, material, qty, length, width, note] sorted by material, module, part."""
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            W = float(r["Width_mm"]) if r["Width_mm"] else ""
            rows.append([r["Module"], r["Part"], r["Material"], int(r["Qty"]), float(r["Length_mm"]), W,
                         r.get("Note", "")])
    rows.sort(key=lambda r: (ORDER.get(r[2], 9), r[0], r[1]))
    for i, r in enumerate(rows, 1):
        r.insert(0, i)
    return rows


def bar_plan(rows, mat):
    """First-fit decreasing. Returns [[(ref, length), ...], ...] one list per stock bar."""
    usable = BAR_L[mat] - 2 * BAR_TRIM
    pieces = sorted(((r[0], r[5]) for r in rows if r[3] == mat for _ in range(r[4])), key=lambda p: -p[1])
    bars, free = [], []
    for ref, L in pieces:
        if L > usable:
            raise ValueError(f"{mat} piece Ref {ref} ({L} mm) is longer than the stock bar")
        for i, f in enumerate(free):
            if L <= f:
                bars[i].append((ref, L))
                free[i] -= L + BAR_KERF
                break
        else:
            bars.append([(ref, L)])
            free.append(usable - L - BAR_KERF)
    return bars


def bar_used(bar):
    return sum(L for _, L in bar) + BAR_KERF * (len(bar) - 1)


def clad_layout(rows):
    """Nest the cladding parts. Returns (sheets, sheet_of {ref: [tags]})."""
    pieces = [(r[0], r[5], r[6]) for r in rows if r[3] == M_CLAD for _ in range(r[4])]
    sheets = nest(pieces)
    sheet_of = {}
    for si, placed in enumerate(sheets, 1):
        for p in placed:
            sheet_of.setdefault(p[0], []).append(f"C{si}")
    return sheets, sheet_of


def plan_all(rows):
    bars = {m: bar_plan(rows, m) for m in BARS}
    where = {}
    tag = {M_TUBE: "T", M_PROF: "P", M_HANDLE: "H"}
    for m, bl in bars.items():
        for bi, bar in enumerate(bl, 1):
            for ref, _ in bar:
                where.setdefault(ref, []).append(f"{tag[m]}{bi}")
    sheets, sheet_of = clad_layout(rows)
    for k, v in sheet_of.items():
        where.setdefault(k, []).extend(v)
    return bars, sheets, where


def counts(rows):
    """Module counts used by the fastener / anchor rules."""
    mods = {r[1] for r in rows}
    wall = sum(1 for m in mods if m.startswith(("Upper_", "Over_Ref")))
    base = sum(1 for m in mods if m.startswith(("Base_", "Island_")) and m.count("_") >= 2 and "Panel" not in m)
    tube_pcs = sum(r[4] for r in rows if r[3] == M_TUBE)
    clad_perim = sum(r[4] * 2 * (r[5] + r[6]) for r in rows if r[3] == M_CLAD) / 1000
    return wall, base, tube_pcs, clad_perim
