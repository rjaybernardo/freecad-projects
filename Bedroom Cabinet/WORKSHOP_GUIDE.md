# Cutting layouts and module assembly pack

Current models: **Bed_Wall_Unit_v8.FCStd** and **Bedroom_Cabinet_Modern_v9.FCStd**. Their native FreeCAD pages contain the cutting layouts, illustrated module build order and LED wiring diagram. PDFs and CSVs are in `workshop/bed/` and `workshop/cabinet/`.

## Open the cut layouts inside FreeCAD

1. Open the relevant model.
2. Expand **Workshop Documents**, then double-click **Sheet 01** (internal object `Cutting_01`). Continue through the numbered stock sheets.
3. Open **CutSchedule** for every panel's ID, module, quantity, finished dimensions, band flags, blank dimensions and assigned sheet. Each row is one physical panel.
4. **SawCuts** gives the guillotine cutting sequence, stock coordinates, cut span and parent rectangle bounds. Trim the stock first, keep the X/Y origin marked and follow each sheet's steps in order. Dimensions are not inferred from the screen scale.
5. **SheetSummary** shows actual achieved sheet count/use, offcut area, trim and kerf/sliver area; **Offcuts** records rectangular remainders. **Materials** shows the corresponding sheet and edge-band quantities; **Hardware** retains the hardware schedule.

The layouts provide the requested CutList Optimizer-style stock diagrams, labels, dimensions, quantities, kerf, trim, edge-banding marks and remainders. They use a 24-trial guillotine heuristic for each project separately. **The achieved sheet count is not a guarantee of the mathematical minimum**, and the two projects have not been combined into one mixed cutting batch. Do not add a generic 25% waste allowance on top of the shown sheet count.

| Project | Individual plywood panels | Stock sheets in this layout | Net edge band | Band with 10% trim allowance |
| --- | ---: | ---: | ---: | ---: |
| Bed and surrounding cabinets | 204 | 11 | 92.727 m | 101.999 m |
| TV / makeup / wardrobe cabinet | 97 | 9 | 52.414 m | 57.656 m |

The backboard is one 1587.2 x 1200 x 19.6 mm plywood panel on three narrow 1507.2 x 50 x 40 mm solid-timber battens. Extra plywood, foam and fabric are removed; upholstery is deferred. The nightstand plinths are four-strip rings, not solid blocks. All recorded furniture plywood now uses the same two-face-laminated stock assumption.

## Cutting assumptions and editing

- Nominal 3/4-inch plywood is assumed **18 mm core + 0.8 mm laminate per face = 19.6 mm finished**. Measure the actual supplied board. The model does not assume a literal 19.05 mm core.
- Stock **2440 × 1220 mm**, trim **5 mm each edge**, saw kerf **4 mm**, finished edge band **1 mm**. Band width must cover the finished board thickness.
- Model dimensions are **finished sizes**. Blank Length deducts band thickness at W1/W2; blank Width deducts it at L1/L2. Orange marks identify banded edges. Review defaults against the actual exposed edges before cutting.
- Plain laminate permits rotation by default. For directional grain, set `AllowRotation` to 0; long panel dimension then stays along stock X. The wood-coloured rendering does not confirm the supplied laminate's grain direction.
- Edit **CuttingSettings** values and **CutSchedule H–K** band flags (0 or 1), then run `regenerate_workshop.FCMacro`. Inspect the regenerated pages and save. They do **not** repack automatically when you type in a cell.
- Run `export_workshop.FCMacro` afterward to update PDFs/previews. The printable exports are snapshots of the SVG pages.
- Changing stock/core/laminate thickness requires rebuilding the geometry with the corresponding `PLY`/`LAM` parameters, then regenerating documents. Editing the stock-sheet dimensions does not resize furniture.
- `Panels_for_optimizer.csv` provides labelled blank rectangles for import/review in another optimizer. The detailed `CutSchedule.csv` carries per-edge information and module names.

## What to build first

Each **Assembly Manual** page contains an actual FreeCAD module image, matching part IDs, a panel table and numbered actions. Repeat the illustrated reference module using the other module's IDs; the image alone is not a drilling template.

**Bed:** two head lift-up boxes → four side drawer bay frames → two foot bay frames → six wheeled drawer assemblies → bolt the eight storage modules together → two nightstands → two upper side cabinets → plain one-panel backboard → four-compartment bridge → wall anchoring, doors, lighting and mattress.

**TV/makeup cabinet:** hanging wardrobe case → right shelving tower → drawer-tower case and plywood grips → centre back/table/shelves → six drawer boxes → three top cases, including the centre divider → mirror, lights, doors and site-fit scribes.

Use the preparation page before cutting. The bed's four side drawers retain 337 mm travel and two foot drawers retain 450 mm travel, limited by removable retention straps. Four fixed-direction **25.4 mm wheels per drawer (24 total)** run on the room floor. The six bays have no raised full floors in the wheel path; short plywood guides control lateral movement. **Total caster mounting height is provisionally 35 mm**, distinct from the wheel diameter. Verify the actual hardware, floor and load rating before cutting wheel-dependent parts. Nightstand runners remain 350 mm; the six TV/makeup/wardrobe drawer runner pairs remain 400 mm.

The head lift-up lids now have 3 mm gaps between neighbouring finished lids. Square fronts, retained overhead dividers and concealed-end plywood L/C drawer grips remain. Door-only units have plain panels and front setbacks, not drawer-style notches or bevels.

This is a dimensioned planning and assembly pack. Supplier-specific hinge cups, runner fixings, caster plates, screw/connector patterns and wall anchors still require the selected hardware and actual wall. No load rating is claimed. Keep overhead modules temporarily supported until suitable wall fixing is complete. Do not substitute ordinary wood glue on laminate for mechanical joinery.

[Bed assembly PDF](workshop/bed/Assembly_Manual.pdf) · [Cabinet assembly PDF](workshop/cabinet/Assembly_Manual.pdf) · [Bed cutting PDF](workshop/bed/Cutting_Layouts.pdf) · [Cabinet cutting PDF](workshop/cabinet/Cutting_Layouts.pdf) · [LED locations and wiring](LIGHTING_AND_WIRING.md).

Build both complete packs with `build_workshop.FCMacro` in FreeCAD. The source builders preserve earlier revision files. The separate three-sheet `Bed_Wall_Unit_v8_Drawing.FCStd` is a general arrangement companion; the stock-sheet cutting pages and illustrated manuals are inside each main model.
