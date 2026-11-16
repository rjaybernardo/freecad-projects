"""Illustrated per-module work packs from disposable saved-model copies (GUI)."""
from pathlib import Path
import base64,csv,json,math,shutil,tempfile
import FreeCAD as App
import FreeCADGui as Gui
from readable_cutlists import start,label,save,export_pdf,table_header
from make_manual_lists import band_diagram
from assembly_manual import camera
P=Path(__file__).resolve().parent
BED=['Head_Box_L','Head_Box_R','Side_Box_1L','Side_Box_1R','Side_Box_2L','Side_Box_2R','Foot_Box_L','Foot_Box_R','Nightstand_Left','Nightstand_Right','Upper_Left','Upper_Right','Headboard','Bridge','Scribe_Strips']
CAB=['Wardrobe_Left_Hanging','Tower_Right_Shelves','Drawer_Tower','Centre_TV_Makeup','Top_Box_Left','Top_Box_Centre','Top_Box_Right','Scribe_Strips']

def steps(name):
 if name=='Scribe_Strips':return ['Place the completed modules in their planned room positions; check level and alignment.','Join the bed bays / shared cabinet zones using the selected connector arrangement.','Anchor tall and overhead cases to suitable wall structure with temporary support.','Measure and cut the scribe strips to the actual wall / ceiling; the listed sizes are blanks.','Finish door gaps, drawer travel / retention, lighting and driver-access checks.']
 if name.startswith('Head_Box'):return ['Build the case: full-depth sides, then Head / Foot between them and the raised Bottom.','Check diagonals; dry-fit the lid with its scheduled gaps.','Fit the selected hinges and lid stays after checking their actual templates.','Mark this module complete; keep it separate until the platform joining stage.']
 if name.startswith(('Side_Box','Foot_Box')):return ['Build this bay frame, rear brace and Top. Keep the wheel path open to the floor.','Fit the short guides and plywood L grip inside the solid outside panels.','Build THIS module\'s drawer: sides, Bottom, Back, then square Front.','Attach four wheel plates directly beneath Bottom; NO plywood mounting pads.','Trial-fit drawer and retention strap; test its direction and travel before joining bays.']
 if name.startswith('Nightstand'):return ['Build this nightstand\'s four-strip plinth, then case back, sides, Bottom and Top.','Fit its plywood L / C grip members between the solid side panels.','Build both drawers belonging to THIS nightstand; use their individual part IDs.','Fit selected 350 mm runners; dry-fit fronts and check the gaps and movement.','Keep this completed nightstand ready for final levelling / joining / anchoring.']
 if name.startswith('Upper'):return ['Build the case: Back, full-height Sides, Bottom, Top and niche shelves.','Prepare cable passages and dry-fit this niche\'s LED profile.','Trial-fit the door with the selected hinges; retain access to the driver compartment.','Finish wall fixing and door adjustment during final installation; support it until secured.']
 if name=='Headboard':return ['Prepare the ONE plywood backboard and THREE solid-timber support battens.','Check site anchor positions; the battens are NOT additional plywood panels.','Fix battens to suitable wall structure, then attach the single backboard panel.','No foam, fabric or second plywood substrate is part of this revision.']
 if name=='Bridge':return ['Build on the floor: Back, Sides, Bottom, Top, then THREE full-height dividers.','Fit FOUR separate shelves and the internal cable passages / LED profile.','Trial-fit the four doors using their scheduled hinge types; check gaps.','Install with lifting help and temporary support; fix to wall and neighbouring towers.','Do not release temporary support until the selected wall fixing arrangement is secure.']
 if name=='Wardrobe_Left_Hanging':return ['Build the strip base, case Back / Sides, Bottom / Top, shelves and hanging rail.','Build this wardrobe\'s TWO drawers as its own subassemblies.','HOLD runner / hinge dependent drilling and sizing: the old 400 mm slides do not fit.','Confirm the proposed 350 mm slides and door clearance before completing those drawers.','Trial-fit door; level and anchor the wardrobe before loading it.']
 if name=='Tower_Right_Shelves':return ['Build strip base, Back, full-height Sides, Bottom / Top and shelves.','Keep the plain door-grip setback; do not add drawer-style grip channels.','Trial-fit its door and selected hinges, checking actual opening clearance.','Level and anchor the tower during installation before loading or final door fitting.']
 if name=='Drawer_Tower':return ['Build the base and drawer-tower case with its internal plywood L / C grip members.','Build all THREE drawers for THIS tower, keeping IDs with their respective drawers.','Check the selected runners against the modelled side gap before final drawer sizing.','Dry-fit fronts and test movement; do not notch the outside panels.','This tower shares the centre structure / back: complete its final fixing with the TV centre.']
 if name=='Centre_TV_Makeup':return ['Prepare centre back panels, Table Top, TV Ledge, divider and makeup shelves.','Fit between the tall units; the back / table structure is shared with the drawer tower.','Build and trial-fit THIS centre\'s single makeup drawer with its selected runner.','Prepare mirror / TV fixing and LED cable routes before closing access.','This is a shared assembly zone, not a separately freestanding cabinet.']
 return ['Build this top box separately on a flat surface: Back, Sides, Bottom and Top.','Fit its scheduled divider / shelf before trial-fitting the doors.','Check selected hinges and prepare LED-driver / cable access where shown.','Lift with help, temporarily support, then secure to suitable wall structure.','Finish its door adjustment only after the fixed case is level and anchored.']

def image(s,path,x,y,w,h):
 data=base64.b64encode(path.read_bytes()).decode()
 s.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{data}" xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="data:image/png;base64,{data}"/>')

def render(objects,path,project,explode=False,interior=False):
 scene=App.newDocument('Module_Guide_Render');bb=App.BoundBox()
 for o in objects:bb.add(o.Shape.BoundBox)
 for src in objects:
  if interior and src.Name.startswith(('Door','Lid')):continue
  dst=scene.addObject('Part::Feature',src.Name);dst.Shape=src.Shape.copy()
  dst.ViewObject.ShapeColor=src.ViewObject.ShapeColor;dst.ViewObject.DisplayMode='Flat Lines'
  dst.ViewObject.LineColor=(.22,.24,.26)
  if explode and 'PartID' in src.PropertiesList:
   b=src.Shape.BoundBox;dims=[b.XLength,b.YLength,b.ZLength];axis=min(range(3),key=lambda i:abs(dims[i]-19.6))
   offset=[0,0,0];offset[axis]=(1 if (b.Center-bb.Center)[axis]>=0 else -1)*max(45,bb.DiagonalLength*.07)
   dst.Placement.Base+=App.Vector(*offset)
 scene.recompute();App.setActiveDocument(scene.Name)
 view,*_=camera(scene,(.65,1 if project=='bed' else -1,.65));Gui.updateGui();view.saveImage(str(path),1800,1400,'White')
 App.closeDocument(scene.Name)

def main():
 report={}
 with tempfile.TemporaryDirectory(prefix='module-guide-copies-') as tmp:
  for project,filename,names in [('bed','Bed_Wall_Unit_v9.FCStd',BED),('cabinet','Bedroom_Cabinet_Modern_v9.FCStd',CAB)]:
   src=Path(tmp)/filename;shutil.copy2(P/filename,src);doc=App.openDocument(str(src))
   data=json.loads((P/'workshop'/project/'layout.json').read_text());lookup={p['id']:p for p in data['panels']}
   out=P/'workshop'/project/'modules';out.mkdir(exist_ok=True)
   allpages=[];assigned=[];index=[]
   cover=start(project.upper()+' | BUILD ONE MODULE AT A TIME','Finish the current module and its drawers, then move to the next numbered module.','Assembly order is separate from sheet cutting order; keep part IDs on every piece.')
   for i,name in enumerate(names,1):label(cover,10,37+(i-1)*9.5,f'{i:02d}. {doc.getObject(name).Label}')
   label(cover,10,187,'Complete doors / hardware fitting only when selected hardware and site fixing are confirmed.')
   allpages.append(save(cover,out/'00_Order.svg'))
   for number,name in enumerate(names,1):
    g=doc.getObject(name)
    objects=[o for o in g.OutListRecursive if o.isDerivedFrom('Part::Feature') and not o.Name.startswith('LED_Cable')]
    if name=='Centre_TV_Makeup':objects=[o for o in objects if not any(a.Name=='Drawer_Tower' for a in o.InListRecursive)]
    ids=sorted(o.PartID for o in objects if 'PartID' in o.PropertiesList);assigned+=ids
    stem=f'{number:02d}_{name}';pics=[]
    for suffix,expl,inter in [('Assembled',False,False),('Exploded',True,False),('Interior',False,True)]:
     path=out/(stem+'_'+suffix+'.png')
     visual=objects if name!='Scribe_Strips' else [o for o in doc.Objects if o.isDerivedFrom('Part::Feature') and o not in doc.Reference_Room.OutListRecursive and not o.Name.startswith('LED_Cable')]
     if not path.exists():render(visual,path,project,expl,inter)
     pics.append(path)
    pages=[]
    s=start(f'{number:02d} | {g.Label}', 'THIS module: case, its own drawers / wheels, and scheduled doors.','Images show actual saved model geometry; exploded views are identification aids.')
    image(s,pics[0],10,31,136,106);image(s,pics[1],151,31,136,106)
    label(s,10,143,'COMPLETE THIS MODULE',font_weight='bold')
    for j,line in enumerate(steps(name)):label(s,10,153+j*8,str(j+1)+'. '+line,4.1)
    pages.append(save(s,out/(stem+'_01_Assembly.svg')))
    s=start(f'{number:02d} | INTERIOR / COMPLETION CHECK','Use this view to check parts hidden by doors. Hardware envelopes are provisional.','Do not load or install unsupported overhead cabinets.')
    image(s,pics[2],10,32,170,132)
    for j,line in enumerate(['[ ] Part IDs matched','[ ] Case square','[ ] Exposed edges checked','[ ] Drawers trial-fitted','[ ] Hardware fit confirmed','[ ] Ready for joining']):label(s,187,55+j*17,line)
    label(s,10,183,'Cut sizes in the next pages are rounded whole-mm targets; dry-fit before final sizing.')
    label(s,10,192,'Use the CAD model for orientation. Connection / anchor patterns require selected hardware.')
    pages.append(save(s,out/(stem+'_02_Check.svg')))
    for page in range(math.ceil(len(ids)/6)):
     s=start(f'{number:02d} | {g.Label} | PARTS {page+1}', 'Qty = 1 per ID | Whole-mm blank targets before banding | Orange = scheduled band.','Band flags follow the existing CAD schedule; verify exposed faces during dry-fit.')
     table_header(s,[20,100,35,65,57],['ID','Part / subassembly','Cut L / W','Edge diagram','Band instruction'])
     for row,identifier in enumerate(ids[page*6:(page+1)*6]):
      p=lookup[identifier];b=p['bands'];y=49+row*22
      label(s,12,y+8,identifier,font_weight='bold');label(s,32,y+8,p['part'].replace('_',' '));label(s,32,y+15,p['module'].replace('_',' '))
      label(s,132,y+8,math.floor(p['blank_l']+.5));label(s,132,y+15,math.floor(p['blank_w']+.5));band_diagram(s,184,y+6,b)
      label(s,232,y+8,'NONE' if not any(b) else 'ALL FOUR' if all(b) else f'{sum(b[:2])} long + {sum(b[2:])} short')
     label(s,10,190,'Rounded targets are not a checked redesign. Keep CAD saw coordinates separate.')
     pages.append(save(s,out/(stem+f'_Parts_{page+1:02d}.svg')))
    export_pdf(pages,out/(stem+'.pdf'))
    allpages+=pages;index.append({'number':number,'module':name,'label':g.Label,'ids':ids,'pdf':stem+'.pdf'})
   assert len(assigned)==len(set(assigned)) and set(assigned)==set(lookup),(project,len(assigned),len(lookup),set(lookup)-set(assigned))
   export_pdf(allpages,P/'workshop'/project/'Module_by_Module.pdf')
   (out/'index.json').write_text(json.dumps(index,indent=2)+'\n')
   md='# '+project.title()+' — build one module at a time\n\n'
   for item in index:md+=f"- [ ] [{item['number']:02d}. {item['label']}]({item['pdf']}) — {len(item['ids'])} plywood parts\n"
   md+='\nAfter the modules: level and join the bed bays / cabinet zones, secure selected wall fixings, finish doors, test drawers and lighting. Centre TV / makeup and drawer tower share structure; they are not independently freestanding.\n'
   (out/'README.md').write_text(md)
   report[project]={'modules':len(names)-1,'final_installation_stages':1,'panels_assigned_once':len(assigned),'geometry_rebuilt':False}
   App.closeDocument(doc.Name)
 (P/'workshop/module-guide-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report)
