# Bedroom cabinet and bed frame

Two separate FreeCAD furniture designs, reviewed on CachyOS with FreeCAD 1.1.4.
Latest major design update: **2026-11-14 — overhead cabinet dividers**.

| Project | Current model | Cut list |
| --- | --- | --- |
| Bed frame with side and overhead cabinets | [Bed v4](Bed_Wall_Unit_v4.FCStd) | [Bed cut list](cut_list_bed_v4.csv) |
| Cabinet with makeup table and TV | [Cabinet v6](Bedroom_Cabinet_Modern_v6.FCStd) | [Cabinet cut list](cut_list_v6.csv) |

## Bed frame with cabinets — v4

The four-door overhead cabinet now has **three full-height dividers**, one
compartment behind each door, and four separate shelf panels. Shelf widths are
368.9 / 378.7 / 378.7 / 368.9 mm, replacing the former 1554 mm span.
The outside dimensions and existing door sizes are preserved.

### Overhead cabinet detail — doors hidden

![Bed v4 overhead cabinet with three dividers](screenshots/bedframe_v4_top_detail.png)

### Angled view

![Bed v4 with side and overhead cabinets](screenshots/bedframe_v4_perspective.png)

### Front view

![Bed v4 front view](screenshots/bedframe_v4_front.png)

### Cabinet interiors — doors and mattress hidden

![Bed v4 cabinet interiors](screenshots/bedframe_v4_interior.png)

[Build script](build_bed_v4.py) · [Three-sheet drawing](Bed_Wall_Unit_v4_Drawing.FCStd)
· [Drawing script](build_bed_drawing_v4.py) · [Hardware list](hardware_bed_v4.csv)

## Cabinet with makeup table and TV — v6

A **centre divider** now separates the two-door top box above the TV. Each side
top box already has its own compartment. Outside dimensions and door sizes are
preserved, including the 720 mm makeup table and 1650 mm hanging rail.

### Top cabinet detail — doors hidden

![Cabinet v6 top boxes with centre divider](screenshots/cabinet_v6_top_detail.png)

### Angled view

![Cabinet v6 with TV and makeup table](screenshots/cabinet_v6_perspective.png)

### Front view

![Cabinet v6 front view](screenshots/cabinet_v6_front.png)

### Cabinet interiors — doors hidden

![Cabinet v6 cabinet interiors](screenshots/cabinet_v6_interior.png)

[Build script](build_cabinet_v6.py) · [Changed overhead parts](overhead_revision_parts.csv)

## Current design review and next revision

[Detailed design audit](DESIGN_REVIEW.md) · [Screenshot gallery](screenshots/README.md)

Both saved revisions pass geometry checks. Earlier models remain available for
comparison. The following requests are recorded for the next revision:

- Use 3/4-inch plywood laminated on both faces, with edge banding. Reconcile
  older raw-panel thicknesses and verify the actual stock dimensions.
- Replace runners on the six under-bed drawers with 1-inch-diameter wheels.
  The rolling surface, wheel type, and total mounting height still need confirmation;
  the screenshots above still show the drawer design before this conversion.
- Add the required strip-light profiles, cable routes, and accessible driver space
  after confirming the lighting locations.
- Correct oversized headboard panels, scribe-strip thickness entries, composite
  plinth entries, and edge-band allowances before final fabrication.
- Produce CutList Optimizer-style sheet diagrams with labelled parts, cutting
  dimensions, kerf, trim, edge banding, material utilization, and offcuts.

Current cut CSVs are reference lists; final optimized cutting layouts are pending
the remaining design corrections. The combined bedroom layout's empty links also
remain to be repaired.

**After every major design change, update both the session notes and this GitHub
README with fresh screenshots of each affected design.**
