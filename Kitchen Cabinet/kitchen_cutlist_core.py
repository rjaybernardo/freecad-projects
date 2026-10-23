# Shared cut-list data + sheet nesting for Kitchen v2 (3/4" PVC board). Standard library only, so it runs
# both inside FreeCAD (kitchen_spreadsheets.py) and in plain Python (make_kitchen_cutlist.py).
# Reads the CSVs written by build_kitchen_v2.py.

import csv
import os
from collections import OrderedDict

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
CUT_CSV = os.path.join(OUT_DIR, "kitchen_cut_list_v2.csv")
HW_CSV = os.path.join(OUT_DIR, "kitchen_hardware_v2.csv")

SHEET_L, SHEET_W = 2440, 1220      # 4 x 8 ft board
TRIM = 5                           # factory-edge trim each side
KERF = 4                           # saw blade
WALL_CABINETS = 5                  # over-ref, over-sink, over-rack, hood, over-washer (from the model)

PVC18 = "PVC board 18 mm"
PVC6 = "PVC board 6 mm"
CTOP = "Countertop 38 mm"


def read_rows(path=CUT_CSV):
    """Cut list rows [ref, module, part, qty, L, W, thickness, material, note], sorted by material."""
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            th = float(r["Thickness_mm"])
            part, mod = r["Part"], r["Module"]
            q, L, W = int(r["Qty"]), float(r["Length_mm"]), float(r["Width_mm"])
            note = r.get("Note", "")
            if part == "Stove_Platform":
                # 64 mm platform built from 18 mm PVC: top + 3 risers (front / middle / back)
                rows.append([mod, "Stove_Platform_Top", 1, L, W, 18, PVC18, "platform 64 H total"])
                rows.append([mod, "Stove_Platform_Riser", 3, L, 46, 18, PVC18, "under the platform top"])
                continue
            mat = {18: PVC18, 6: PVC6, 38: CTOP}.get(round(th), f"{th:g} mm")
            if mat == CTOP:
                part, cut = part.split(" (", 1) if " (" in part else (part, "")
                note = cut.rstrip(")")
            rows.append([mod, part, q, L, W, th, mat, note])
    order = {PVC18: 0, PVC6: 1, CTOP: 2}
    rows.sort(key=lambda r: (order.get(r[6], 9), r[0], r[1]))
    for i, r in enumerate(rows, 1):
        r.insert(0, i)                  # Ref#
    return rows


def read_hardware(path=HW_CSV):
    """{(item, size): (qty, [modules])}, same items merged."""
    hw = OrderedDict()
    with open(path) as f:
        for r in csv.DictReader(f):
            key = (r["Item"], r["Size_mm"])
            q, mods = hw.get(key, (0, []))
            hw[key] = (q + int(r["Qty"]), mods + [r["Module"]])
    return hw


def hw_category(item, mods):
    low = item.lower()
    return ("Lighting" if "Lighting_LED" in mods else
            "Electrical" if any(k in low for k in ("power", "circuit")) else
            "Appliance fit" if any(k in low for k in ("hood", "flat duct", "vent")) else
            "Finishing" if "paint" in low else
            "Racks & runners" if any(k in low for k in ("basket", "tray", "runner", "drainer", "rack")) else
            "Fittings")


def hw_qty_unit(size, q):
    """(qty, spec, unit): lengths like '12.3 m' become a quantity in metres."""
    spec, unit = ("" if size == "-" else size), "pcs"
    if size.endswith(" m"):
        q, spec, unit = float(size.split()[0]), "", "m"
    elif size.endswith(" H") and "W x" not in size:
        spec, unit = f"{size} section", "lot"
    return q, spec, unit


def front_kind(part):
    if part.startswith("Door"):
        return "Door"
    if part.startswith("Kick_DrawerFront"):
        return "Toe-kick drawer"
    if part.startswith("DrawerFront"):
        return "Drawer"
    return None


def hinges_for(long_side):
    """Hinge-maker rule of thumb: <= 900 mm -> 2, <= 1600 mm -> 3, longer -> 4."""
    return 2 if long_side <= 900 else 3 if long_side <= 1600 else 4


def nest(pieces):
    """Guillotine packing, best-area fit, rotation allowed. pieces: (ref, l, w). Returns list of sheets,
    each a list of (ref, x, y, l, w, rotated)."""
    UL, UW = SHEET_L - 2 * TRIM, SHEET_W - 2 * TRIM
    pieces = sorted(pieces, key=lambda p: (max(p[1], p[2]), p[1] * p[2]), reverse=True)
    sheets = []                                     # [free_rects, placed]
    for ref, l, w in pieces:
        best = None
        for si, (free, _) in enumerate(sheets):
            for fi, (fx, fy, fl, fw) in enumerate(free):
                for rot, (pl, pw) in enumerate(((l, w), (w, l))):
                    if pl <= fl and pw <= fw:
                        waste = fl * fw - pl * pw
                        if best is None or waste < best[0]:
                            best = (waste, si, fi, pl, pw, rot)
        if best is None:
            sheets.append([[(TRIM, TRIM, UL, UW)], []])
            free = sheets[-1][0]
            fx, fy, fl, fw = free[0]
            rot = 0 if (l <= fl and w <= fw) else 1
            pl, pw = (l, w) if rot == 0 else (w, l)
            si, fi = len(sheets) - 1, 0
        else:
            _, si, fi, pl, pw, rot = best
        free, placed = sheets[si]
        fx, fy, fl, fw = free.pop(fi)
        placed.append((ref, fx, fy, pl, pw, bool(rot)))
        # split along the shorter leftover axis (keeps big offcuts)
        rl, rw = fl - pl - KERF, fw - pw - KERF
        if rl < rw:
            a, b = (fx + pl + KERF, fy, rl, pw), (fx, fy + pw + KERF, fl, rw)
        else:
            a, b = (fx + pl + KERF, fy, rl, fw), (fx, fy + pw + KERF, pl, rw)
        free.extend(r for r in (a, b) if r[2] > 30 and r[3] > 30)
    return [s[1] for s in sheets]


def layout(rows):
    """Nest both PVC thicknesses. Returns (layouts {material: sheets}, sheet_of {ref: [sheet tags]})."""
    layouts = {}
    for mat in (PVC18, PVC6):
        pieces = [(r[0], r[4], r[5]) for r in rows if r[7] == mat for _ in range(r[3])]
        layouts[mat] = nest(pieces)
    sheet_of = {}
    for mat, sheets in layouts.items():
        tag = "A" if mat == PVC18 else "B"
        for si, placed in enumerate(sheets, 1):
            for p in placed:
                sheet_of.setdefault(p[0], []).append(f"{tag}{si}")
    return layouts, sheet_of
