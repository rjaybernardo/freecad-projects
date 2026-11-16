"""Illustrated module order generated from actual labelled FreeCAD parts."""
from pathlib import Path
import base64
import html
import json
import copy
import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
from workshop_documents import svg_start, text, native_page, spreadsheet

BED=[
('Head lift-up boxes — build two','Head_Box_L','fixed',True,[
 'Lay out the L and R head-box panels by their IDs; clamp each case on a flat surface.',
 'Fit Head and Foot BETWEEN the two full-depth sides. Fit the raised Bottom inside.',
 'Check equal diagonals before fastening. Fit the square lid with 3 mm gaps between adjacent lids.',
 'Fit the selected lid hinges and stays only after checking their supplier template.']),
('Side drawer bay frames — build four','Side_Box_1L','fixed',True,[
 'Build rows 1 and 2, left and right. Match the IDs: these are mirrored cases.',
 'Join full-width Head/Foot ends to Inner Side. Rear Base Brace stays behind the drawer.',
 'Leave the floor under the drawer OPEN: the 1-inch wheels run on the room floor.',
 'Fit short Guide strips; rout only the internal L recess. Keep outside end panels solid.']),
('Foot drawer bay frames — build two','Foot_Box_L','fixed',True,[
 'Join Head between Side L/R; fit rear brace and Top. Repeat for the other side.',
 'Leave the wheel path open to the room floor. Do not add the old full bay bottom.',
 'Fit the plywood L strips between sides. Leave the 25 mm finger gap above the front.',
 'Dry-fit the drawer before joining this module to the rest of the platform.']),
('Wheeled drawers — build six','Drawer_Assembly_Side_Box_1L','all',True,[
 'Use the four side and two foot drawer ID sets: widths differ; do not swap fronts.',
 'Join Bottom between Sides, then Back. Clamp square before fixing Front.',
 'Fix four plywood pads under Bottom, then four fixed-direction 25.4 mm wheels.',
 'Assumed total caster height is 35 mm. Measure actual height and plate before cutting.',
 'Align wheel rolling direction with drawer travel. Test on the actual level room floor.']),
('Join the eight storage modules','Storage_Bed','all',False,[
 'Place the 2 head boxes at the wall, 4 side bays in the middle, 2 foot bays at the foot.',
 'Level, clamp and bolt neighbouring case panels together; align all tops at 300 mm.',
 'Install drawers and adjustable removable retention straps: side 337 mm, foot 450 mm.',
 'Pull each drawer fully out and return it. Wheels must track without guide rubbing.',
 'Do not load the bed until the final fastening and support arrangement is confirmed.']),
('Nightstands — build two','Nightstand_Left','all',True,[
 'Build each recessed plinth from FOUR actual strips; level with the case above.',
 'Join case back, sides, bottom and top. Rout grip recesses only on internal panels.',
 'Fit plywood L under Top and C between the two fronts; ends stop inside the sides.',
 'Fit two drawer boxes per case with the retained 350 mm runners and equal gaps.']),
('Upper side cabinets — build two','Upper_Left','all',True,[
 'Assemble Back and full-height Sides, then Bottom, Top and niche shelves.',
 'Fit shelf cable passages and aluminium LED profile under the lit-niche shelf.',
 'Keep door-only panel edges plain; retain the approved front setback for fingers.',
 'Fit the tall door after wall anchoring. Leave the left upper driver compartment accessible.']),
('Split headboard and upholstery','Headboard','all',True,[
 'Use two Backer halves and two Upholstered Panel Base halves; each fits 4 x 8 stock.',
 'Fix each backer half independently to suitable wall fixings. Align the centre seam.',
 'Join substrate halves with the upholstery system chosen by the upholsterer.',
 'Continuous foam/fabric conceals the seam. Maintain the modelled 50 mm total depth.']),
('Four-compartment bridge cabinet','Bridge','all',True,[
 'Build the case on the floor: Back, Sides, Bottom, Top, then THREE full-height dividers.',
 'Fit the FOUR separate shelf panels; do not replace them with one wide shelf.',
 'Drill modelled cable passages, fit under-bridge LED profile and route DC cables.',
 'Lift with assistance and temporary support. Fix to the wall and adjacent towers.',
 'Select fixings for the wall and expected load before removing temporary support.']),
('Final fit, doors and lighting test','ALL','all',False,[
 'Anchor and level both towers; install bridge and headboard, then position bed platform.',
 'Adjust hinges/front gaps. Fit ceiling scribe on site; maintain finger access.',
 'Test each lighting branch before fitting diffusers. Follow the wiring page next.',
 'Install mattress only after drawer travel, retention straps and final fixings pass.'])]

CAB=[
('Hanging wardrobe carcass','Wardrobe_Left_Hanging','fixed',True,[
 'Build the recessed base from Front/Back strips. Level and support the case.',
 'Fit Bottom and Top BETWEEN full-height Sides; fit the full-height Back behind them.',
 'Check diagonals, then fit the shelves. Keep the plain right-side finger setback.',
 'Set the hanging rail at 1650 mm above floor. Delay door fitting until anchored.']),
('Right shelving tower','Tower_Right_Shelves','fixed',True,[
 'Build the recessed base, then Sides, Bottom, Top and Back. Check square.',
 'Fit the shelves at the modelled elevations. Keep the left-side finger setback.',
 'Position 1300 mm from the hanging unit inner face; level and anchor both towers.',
 'Select anchoring hardware for the actual wall before loading or fitting tall doors.']),
('Drawer tower case and plywood grips','Drawer_Tower','fixed',True,[
 'Build the base, case sides, bottom and top; centre back panel later closes the rear.',
 'Fit the top plywood L and both intermediate C channels before fitting drawers.',
 'Channel ends stop between solid side panels. Do not notch the outside side faces.',
 'L is 42 x 60; C is 42 x 80. All fronts remain square and edge banded.']),
('Centre back, table and makeup shelves','Centre_TV_Makeup','centre_fixed',True,[
 'Fit the TWO centre Back panels between the tall units; seam is behind the TV.',
 'Fit Table Top at 720 mm and TV Ledge top at 1300 mm, using their modelled supports.',
 'Fit Divider at the drawer-tower edge, then the two Makeup Shelves to its right.',
 'TV bracket bolts must reach suitable wall structure; plywood alone is not the fixing.',
 'Keep all DC cables behind shelves and away from drawer and hinge travel.']),
('Drawer boxes — six sets','Drawer_Tower','drawers',True,[
 'Assemble each Bottom between Sides, then Back and square Front.',
 'Build three tower drawers, two wardrobe drawers and the single makeup drawer.',
 'Fit the six retained 400 mm runner pairs using the selected runner instructions.',
 'Adjust fronts to the modelled gaps. Check movement through the plywood channels.']),
('Three separate top boxes','Top_Boxes','all',True,[
 'Assemble left, centre and right top cases separately while on the floor.',
 'Fit the centre top-box divider BEFORE fitting its two doors; do not omit it.',
 'Left top box contains the accessible LED driver and distribution/dimmer space.',
 'Route DC wiring through modelled passages before lifting and anchoring the boxes.']),
('Mirror, lighting profiles and final doors','ALL','all',False,[
 'Fit the mirror with compatible mirror fixing; fit profiles beside it and under TV Ledge.',
 'Tall doors use half-overlay hinges; centre top doors use full-overlay as scheduled.',
 'Fit site-cut ceiling/right scribes. Verify all doors and drawers open without rubbing.',
 'The 630 mm chair armrests still exceed the 598.4 mm makeup drawer underside.',
 'Test all LED branches and fit diffusers using the following wiring page.'])]


def camera(doc,eye):
    view=Gui.activeDocument().activeView();view.setCameraType('Orthographic')
    z=App.Vector(*eye);z.normalize();x=App.Vector(0,0,1).cross(z);x.normalize();y=z.cross(x);y.normalize()
    bounds=App.BoundBox()
    for o in doc.Objects:
        if hasattr(o,'Shape') and o.ViewObject.Visibility:bounds.add(o.Shape.BoundBox)
    corners=[App.Vector(a,b,c) for a in [bounds.XMin,bounds.XMax] for b in [bounds.YMin,bounds.YMax] for c in [bounds.ZMin,bounds.ZMax]]
    w=max(v.dot(x) for v in corners)-min(v.dot(x) for v in corners);h=max(v.dot(y) for v in corners)-min(v.dot(y) for v in corners)
    height=max(h,w/(1800/1400))*1.22;dist=bounds.DiagonalLength*3;pos=bounds.Center+z*dist;n=view.getCameraNode()
    n.orientation.setValue(coin.SbRotation(*App.Rotation(x,y,z,'ZXY').Q));n.position.setValue(pos.x,pos.y,pos.z);n.focalDistance.setValue(dist);n.nearDistance.setValue(1);n.farDistance.setValue(dist*3);n.height.setValue(height)
    return view,bounds.Center,x,y,height


def render_module(src,group_name,mode,explode,path,project):
    reference=set(src.Reference_Room.OutListRecursive)
    g=src.getObject(group_name)
    objects=[o for o in (src.Objects if group_name=='ALL' else g.OutListRecursive+[g]) if o.isDerivedFrom('Part::Feature') and o not in reference]
    if mode=='fixed':objects=[o for o in objects if not ('MovingDrawer' in o.PropertiesList and o.MovingDrawer) and not o.Name.startswith(('Drawer_','Table_Drawer_'))]
    if mode=='drawers':objects=[o for o in objects if o.Name.startswith('Drawer_')]
    if mode=='centre_fixed':objects=[o for o in objects if not any(a.Name=='Drawer_Tower' for a in o.InListRecursive) and not o.Name.startswith(('Table_Drawer','TV_'))]
    objects=[o for o in objects if not o.Name.startswith('LED_Cable')]
    scene=App.newDocument('Assembly_Render');bb=App.BoundBox()
    for o in objects:bb.add(o.Shape.BoundBox)
    center=bb.Center; labels=[]
    for source in objects:
        o=scene.addObject('Part::Feature',source.Name);o.Shape=source.Shape.copy();o.ViewObject.ShapeColor=source.ViewObject.ShapeColor;o.ViewObject.LineColor=(.22,.24,.26)
        o.ViewObject.DisplayMode='Flat Lines'
        if explode and 'PartID' in source.PropertiesList:
            b=o.Shape.BoundBox;v=b.Center-center
            # Separate along the panel thickness axis, keeping mating edges recognizable.
            dims=[b.XLength,b.YLength,b.ZLength];axis=min(range(3),key=lambda i:abs(dims[i]-19.6));sign=1 if [v.x,v.y,v.z][axis]>=0 else -1
            offset=[0,0,0];offset[axis]=sign*max(45,bb.DiagonalLength*.065)
            o.Placement.Base+=App.Vector(*offset)
        if 'PartID' in source.PropertiesList:labels.append((source.PartID,o.Shape.BoundBox.Center))
    scene.recompute();App.setActiveDocument(scene.Name)
    eye=(.65,1,.65) if project=='bed' else (.65,-1,.65)
    view,center,x,y,height=camera(scene,eye);Gui.updateGui();view.saveImage(str(path),1800,1400,'White')
    projected=[(identifier,900+(point-center).dot(x)*1400/height,700-(point-center).dot(y)*1400/height) for identifier,point in labels]
    App.closeDocument(scene.Name);App.setActiveDocument(src.Name)
    return objects,projected


def wrap(line,limit=65):
    words=line.split();lines=[];current=''
    for word in words:
        if len(current)+len(word)+1>limit:lines.append(current);current=word
        else:current=(current+' '+word).strip()
    if current:lines.append(current)
    return lines


def build(doc,project,output):
    out=Path(output)/'workshop'/project;data=json.loads((out/'layout.json').read_text());panels={p['id']:p for p in data['panels']}
    for pattern in ['Assembly_[0-9][0-9].svg','Module_[0-9][0-9].png']:
        for stale in out.glob(pattern):stale.unlink()
    plans=copy.deepcopy(BED if project=='bed' else CAB)
    if project=='bed' and 'IncludeBackboard' in doc.getObject(doc.Name).PropertiesList:
        if doc.getObject(doc.Name).IncludeBackboard:
            plans[7]=('Plain backboard — ONE plywood layer','Headboard','all',True,[
                'Cut ONE laminated plywood panel 1587.2 x 1200 mm. It fits a single 4 x 8 sheet.',
                'Use THREE narrow solid-timber battens 1507.2 x 50 x 40 mm, fixed to suitable wall anchors.',
                'Fix the ONE laminated panel to the three battens; do not add another plywood layer.',
                'No extra full-sheet plywood backing, foam, fabric or buttons. Upholstery can be added later.'])
        else:
            plans.pop(7)
    revision='BED v8' if doc.Name.startswith('Bed_Wall_Unit_v8') else ('BED v7' if project=='bed' else 'TV / MAKEUP CABINET v9')
    group=doc.getObject('Assembly_Manual') or doc.addObject('App::DocumentObjectGroup','Assembly_Manual')
    cover=svg_start('BEFORE YOU CUT — workshop assembly pack',f'{project.upper()} | reference modules and matching panel IDs | hardware dimensions still provisional')
    text(cover,12,42,'1. Confirm the physical stock and hardware',5,font_weight='bold')
    for i,line in enumerate([
        'Stock assumption: 18 mm plywood core + 0.8 mm laminate on EACH face = 19.6 mm finished thickness.',
        'The 3/4-inch description is nominal. Measure the delivered laminated sheets before releasing these sizes.',
        'Sheet 2440 x 1220 mm; trim 5 mm each edge; saw kerf 4 mm; finished edge band assumed 1 mm.',
        'Plain laminate permits rotation. For directional grain, change AllowRotation to 0 and regenerate.',
        'Bed only: 25.4 mm WHEEL diameter is confirmed; 35 mm TOTAL caster mounting height is an assumption.',
        'Measure wheel height, plate, fasteners and load rating before cutting the wheel-dependent drawer parts.',
        'LEDs: 24 V / 10 W per metre, 16 x 10 mm profile and 30 W driver per project are design assumptions.',
        'Choose actual hinge / runner / caster / wall-fixing hardware before drilling supplier-specific holes.'
    ]):text(cover,12,54+i*8,line,3.6)
    text(cover,12,132,'2. Cut, label, band and machine',5,font_weight='bold')
    for i,line in enumerate([
        'Open Workshop Documents > Cutting 01 etc. in FreeCAD; follow native SawCuts and label every panel Bxxx / Cxxx.',
        'CutSchedule lists one physical panel per ID. FINISHED sizes include edge band; BLANK sizes already deduct it.',
        'Apply band only to the flagged edges. Match the exposed edge against the model before trimming it flush.',
        'Drill modelled cable passages and rout internal plywood grip recesses after cutting the rectangular blanks.',
        'Outside case sides stay solid at the grip ends. No extra cover panels and no 45-degree bevels.',
        'Dry-fit modules before final fastening. Laminated mating faces need appropriate mechanical joinery; plain wood glue',
        'on laminate is not a substitute for fixings. Predrill and countersink to suit the chosen screws / connectors.'
    ]):text(cover,12,144+i*8,line,3.6)
    text(cover,12,213,'3. Build small modules first; install heavy units last',5,font_weight='bold')
    for i,line in enumerate([
        'The next pages show the actual FreeCAD parts separated for identification; images are not drilling templates.',
        'Use a flat assembly surface and clamps. Compare the two diagonals before fastening each rectangular case.',
        'Repeat or mirror the illustrated module using its own IDs from CutSchedule; do not substitute the pictured IDs.',
        'Fixings, lifting support, wall anchoring and load capacity require the actual site and hardware details.',
        'Keep driver and connectors accessible. The last page shows the low-voltage parallel wiring and test order.'
    ]):text(cover,12,225+i*8,line,3.6)
    cover.append('</svg>');cover_path=out/'Assembly_00.svg';cover_path.write_text('\n'.join(cover));native_page(doc,group,cover_path,'Assembly_00')
    order=[]
    for no,(title,group_name,mode,explode,steps) in enumerate(plans,1):
        png=out/f'Module_{no:02d}.png';objects,labels=render_module(doc,group_name,mode,explode,png,project)
        identifiers=sorted(o.PartID for o in objects if 'PartID' in o.PropertiesList)
        order.append([no,title,group_name,', '.join(identifiers)])
        svg=svg_start(f'{no:02d}  {title}',f'{revision} | build order | '+('exploded reference module; mirror/repeat as stated below' if explode else 'assembly / installation view'))
        encoded=base64.b64encode(png.read_bytes()).decode()
        svg.append(f'<image x="10" y="32" width="264" height="205.33" xlink:href="data:image/png;base64,{encoded}"/>')
        if explode:
            for identifier,x,y in labels:
                px,py=10+x*264/1800,32+y*205.33/1400
                svg.append(f'<rect x="{px-5}" y="{py-2.5}" width="12" height="4" rx=".5" fill="white" stroke="#405665" stroke-width=".15"/>')
                text(svg,px-4.5,py+.5,identifier,2.8)
        if project=='bed' and no==8 and doc.Name.startswith('Bed_Wall_Unit_v8'):
            text(svg,282,87,'SIDE VIEW: ONE PLYWOOD LAYER',3.2,font_weight='bold')
            svg.append('<path d="M288 103 V188" stroke="#85918c" stroke-width="2"/>')
            svg.append('<rect x="288" y="132" width="35" height="20" fill="#ccb99a" stroke="#746a58" stroke-width=".5"/>')
            svg.append('<rect x="323" y="105" width="13.72" height="78" fill="#d8d1c3" stroke="#4e5d55" stroke-width=".5"/>')
            text(svg,282,99,'WALL',2.8)
            text(svg,340,125,'19.6 mm',3.2)
            text(svg,340,131,'plywood',3.2)
            text(svg,282,198,'Timber support: 50 mm deep x 40 mm high',2.8)
            text(svg,282,205,'B073 = one continuous plywood face',3)
        text(svg,282,36,'PARTS IN THIS VIEW',3.5,font_weight='bold')
        if len(identifiers)<=42:
            for i,identifier in enumerate(identifiers):
                p=panels[identifier];desc=p['part'].replace('Drawer_','Dr ').replace('Pull_','Grip ')
                text(svg,282,43+i*4.2,f'{identifier}  {p["finished_l"]:g} x {p["finished_w"]:g}  {desc[:27]}',2.55)
        else:
            for i,line in enumerate(wrap('All pictured panel IDs are listed in the native BuildOrder sheet and CutSchedule. This is the assembled module, not an exploded part detail.',49)):text(svg,282,44+i*5,line,3)
        y=244
        # Bottom numbered actions use the full page width, with two columns.
        for i,step in enumerate(steps):
            col=i%2;row=i//2;xx=12+col*204;yy=y+row*14
            for j,line in enumerate(wrap(f'{i+1}. {step}',91)):text(svg,xx,yy+j*4.6,line,3.4)
        svg.append('</svg>');path=out/f'Assembly_{no:02d}.svg';path.write_text('\n'.join(svg));native_page(doc,group,path,f'Assembly_{no:02d}')
    spreadsheet(doc,group,'BuildOrder',['Step','Module','FreeCAD group','Panel IDs'],order,'Build from small cases to joined assemblies. Cutting sheets use the same B/C panel IDs. Representative mirrored modules show one side; use each module-specific ID set.')
    lighting=json.loads(Path(output,project+'_lighting.json').read_text());wiring_page(doc,group,out,lighting)
    for name,label in [('Workshop_Documents','Workshop Documents'),('Assembly_Manual','Assembly Manual'),('LED_Lighting','LED Lighting'),('Cut_List_Materials','Hardware schedules')]:
        obj=doc.getObject(name)
        if obj:obj.Label=label
    for obj in doc.Reference_Room.OutListRecursive:
        if obj.isDerivedFrom('Part::Feature'):obj.ViewObject.Visibility=obj.Name=='Mattress_5x6'
    for obj in doc.Objects:
        if obj.TypeId=='TechDraw::DrawPage':obj.ViewObject.Visibility=False
    doc.recompute();doc.save()


def wiring_page(doc,group,out,data):
    s=svg_start('LED WIRING — parallel low-voltage branches',f'{data["project"].upper()} | PROVISIONAL {data["voltage_assumption"]} V constant-voltage, {data["watts_per_m_assumption"]:g} W/m | confirm purchased products')
    def box(x,y,w,h,lines,fill='#e4edf0'):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{fill}" stroke="#334d5b" stroke-width=".4"/>')
        for i,line in enumerate(lines):text(s,x+3,y+7+i*5,line,3.2)
    def line(x1,y1,x2,y2,colour='#415566'):
        s.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{colour}" stroke-width=".7" fill="none"/>')
    box(12,37,57,24,['Existing outlet','Use certified plug-in supply'])
    box(83,37,75,34,[f'{data["voltage_assumption"]} V DC driver',f'{data["provisional_driver_w"]} W provisional','Accessible + ventilated'])
    box(176,37,90,34,['DC fuse / distribution','Compatible dimmer or switch','Ratings per actual products'])
    line(69,49,83,49);line(158,48,176,48,'#c54b36');line(158,60,176,60,'#1e2730')
    text(s,159,44,'+24 V',2.6);text(s,159,67,'0 V (-)',2.6)
    line(276,48,276,175,'#c54b36');line(282,60,282,181,'#1e2730');line(266,48,276,48,'#c54b36');line(266,60,282,60,'#1e2730')
    for i,b in enumerate(data['branches']):
        y=79+i*35
        box(311,y,94,26,[f'{b["id"]}  strip {b["length_mm"]:g} mm',f'{b["watts"]:.2f} W / {b["watts"]/data["voltage_assumption"]:.3f} A','+ to +   /   - to -'],'#fff0cf')
        s.append(f'<path d="M276 {y+7} L280 {y+7} Q282 {y+3} 284 {y+7} L311 {y+7}" stroke="#c54b36" stroke-width=".7" fill="none"/>')
        line(282,y+18,311,y+18,'#1e2730')
        s.append(f'<circle cx="276" cy="{y+7}" r="1.1" fill="#c54b36"/><circle cx="282" cy="{y+18}" r="1.1" fill="#1e2730"/>')
    text(s,12,91,'MODEL LOCATIONS / CABLE ALLOWANCES',3.8,font_weight='bold')
    for i,b in enumerate(data['branches']):
        y=101+i*13
        loc={'B_L':'left bed niche','B_R':'right bed niche','B_H':'under bridge / headboard wash','C_T':'under TV ledge / vanity','C_L':'left of mirror','C_R':'right of mirror'}[b['id']]
        text(s,12,y,f'{b["id"]}: {loc} — profile {b["length_mm"]:g} mm',3.2)
        text(s,12,y+5,f'2-core route {b["cable_route_mm"]:g} mm + 200 mm service allowance = {b["cable_allowance_mm"]:g} mm',2.8)
    text(s,12,151,f'Total strip {data["total_length_m"]:.3f} m x {data["watts_per_m_assumption"]:g} W/m = {data["load_w"]:.2f} W ({data["load_a"]:.3f} A at 24 V).',3.3)
    text(s,12,159,f'With 25% design margin: {data["minimum_capacity_with_margin_w"]:.2f} W minimum; 30 W is a provisional selection, not a purchased specification.',3)
    instructions=[
      '1. Confirm strip voltage, actual W/m and cut interval. The driver output voltage MUST match the strip.',
      '2. Mount aluminium U profiles with end caps and diffuser. Confirm the actual extrusion fits the 16 x 10 mm allowance.',
      '3. Drill the modelled cable passages BEFORE assembly; fit matching grommets so plywood edges cannot cut cable insulation.',
      '4. Secure the two-core DC cable along the back of fixed panels. Keep away from hinges, runners, wheels and moving fronts.',
      '5. With power unplugged, connect driver DC to rated distribution / dimmer, then each strip on its OWN parallel + / - branch.',
      '6. Cut strip only at its marked copper pads. Use compatible connectors or insulated solder joints; leave a service loop.',
      '7. Select wire gauge / fuse / connectors for actual current, route length and voltage drop; no gauge or fuse is finalized here.',
      '8. Test polarity and every branch before fitting diffusers. Check driver temperature and ventilation against its datasheet.',
      '9. Place driver behind an accessible door. Do not seal it into plywood or cover it with bedding. Keep mains and DC separate.',
      '10. Use a certified plug-in supply at an existing outlet; any fixed mains outlet or wiring work is for a qualified electrician.'
    ]
    for i,instruction in enumerate(instructions):text(s,12,176+i*7,instruction,2.9)
    text(s,12,253,'If the purchased strips are 12 V: update the model assumption and use a 12 V constant-voltage driver; recheck current, cable and fuse sizing.',2.9)
    text(s,12,261,'Sources: Waveform Lighting, “How to Connect An LED Strip to a Power Supply”; “Connecting LED Strips in Series vs Parallel”.',2.5)
    text(s,12,268,'See LIGHTING_AND_WIRING.md for source links and all hardware assumptions. Orange CAD lines represent two-core DC cable sheaths.',2.5)
    s.append('</svg>');path=out/'LED_Wiring.svg';path.write_text('\n'.join(s));native_page(doc,group,path,'LED_Wiring')
    spreadsheet(doc,group,'LightingSchedule',['Branch','Location','Profile mm','Strip W','DC A','Cable route mm','Cable + slack mm'],
        [[b['id'],str(b['location']),b['length_mm'],b['watts'],round(b['watts']/data['voltage_assumption'],3),b['cable_route_mm'],b['cable_allowance_mm']] for b in data['branches']],
        'PROVISIONAL 24 V / 10 W/m. Aluminium 16 x 10 profile envelope. Cable and fuse ratings require actual product data. Power load excludes any extra lights.')
