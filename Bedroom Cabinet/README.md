# Bedroom cabinet and bed frame

Two separate FreeCAD furniture designs, reviewed on CachyOS with FreeCAD 1.1.4.
Latest major design update: **2026-11-14 — plywood L/C handleless pulls; square-edged fronts**.

| Project | Current model | Cut list |
| --- | --- | --- |
| Bed frame with side and overhead cabinets | [Bed v5](Bed_Wall_Unit_v5.FCStd) | [Bed cut list](cut_list_bed_v5.csv) |
| Cabinet with makeup table and TV | [Cabinet v7](Bedroom_Cabinet_Modern_v7.FCStd) | [Cabinet cut list](cut_list_v7.csv) |

## Bed frame with cabinets — v5

The grips are built from laminated plywood: **L under the top and C between
stacked drawers**. All door and drawer fronts have square, edge-banded edges.

### Updated drawer pull detail — drawers open

![Bed v5 plywood L and C drawer recesses](screenshots/bedframe_v5_drawer_pulls.png)

The four-door overhead cabinet now has **three full-height dividers**, one
compartment behind each door, and four separate shelf panels. Shelf widths are
368.9 / 378.7 / 378.7 / 368.9 mm, replacing the former 1554 mm span.
The outside dimensions and existing door sizes are preserved.

### Overhead cabinet detail — doors hidden

![Bed v5 overhead cabinet with three dividers](screenshots/bedframe_v5_top_detail.png)

### Angled view

![Bed v5 with side and overhead cabinets](screenshots/bedframe_v5_perspective.png)

### Front view

![Bed v5 front view](screenshots/bedframe_v5_front.png)

### Cabinet interiors — doors and mattress hidden

![Bed v5 cabinet interiors](screenshots/bedframe_v5_interior.png)

[Build script](build_bed_v5.py) · [Three-sheet drawing](Bed_Wall_Unit_v5_Drawing.FCStd)
· [Drawing script](build_bed_drawing_v5.py) · [Hardware list](hardware_bed_v5.csv)

## Cabinet with makeup table and TV — v7

The drawer tower has a plywood **L recess at the top and C recesses between drawers**.
Tall doors have plywood vertical pull recesses. The side panels are routed to fit
the fixed recesses; drawer boxes clear them throughout the sampled opening travel.

### Updated drawer pull detail — drawers open

![Cabinet v7 plywood L and C drawer recesses](screenshots/cabinet_v7_drawer_pulls.png)

A **centre divider** now separates the two-door top box above the TV. Each side
top box already has its own compartment. Outside dimensions and door sizes are
preserved, including the 720 mm makeup table and 1650 mm hanging rail.

### Top cabinet detail — doors hidden

![Cabinet v7 top boxes with centre divider](screenshots/cabinet_v7_top_detail.png)

### Angled view

![Cabinet v7 with TV and makeup table](screenshots/cabinet_v7_perspective.png)

### Front view

![Cabinet v7 front view](screenshots/cabinet_v7_front.png)

### Cabinet interiors — doors hidden

![Cabinet v7 cabinet interiors](screenshots/cabinet_v7_interior.png)

[Build script](build_cabinet_v7.py) · [Plywood pull parts and routing](plywood_pull_parts.csv)

## Current design review and next revision

[Detailed design audit](DESIGN_REVIEW.md) · [Screenshot gallery](screenshots/README.md)

The L recess is 42 mm deep × 60 mm high, following the reference. The C recess
is 42 mm deep × 80 mm high, with 40.8 mm clear between 19.6 mm returns. Drawer
boxes were resized to clear the fixed channels. Wardrobe internal drawers are
60 mm narrower and use 350 mm runners beside a new mounting partition.
The single makeup drawer keeps its accessible lower square pull edge.

[Cabinet hardware list](hardware_cabinet_v7.csv) · [Plywood pull construction](PLYWOOD_PULLS.md)

Both saved revisions pass geometry and sampled drawer-travel checks. Earlier models remain available for
comparison. The following requests are recorded for the next revision:

- Use 3/4-inch plywood laminated on both faces, with edge banding. Reconcile
  older raw-panel thicknesses and verify the actual stock dimensions.
- Replace runners on the six under-bed drawers with 1-inch-diameter wheels.
  The rolling surface, wheel type, and total mounting height still need confirmation;
  the screenshots above still show the drawer design before this conversion.
- Add the required strip-light profiles, cable routes, and accessible driver space
  after confirming the lighting locations.
- Correct oversized headboard panels, composite
  plinth entries and edge-band allowances before final fabrication.
- Produce CutList Optimizer-style sheet diagrams with labelled parts, cutting
  dimensions, kerf, trim, edge banding, material utilization, and offcuts.

Current cut CSVs are reference lists; final optimized cutting layouts are pending
the remaining design corrections. The combined bedroom layout's empty links also
remain to be repaired.

**After every major design change, update both the session notes and this GitHub
README with fresh screenshots of each affected design.**
