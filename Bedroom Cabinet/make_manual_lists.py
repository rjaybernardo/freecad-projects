"""Manual whole-mm worksheets with per-part edge diagrams; CAD fit data retained."""
from pathlib import Path
import csv,json,math
from readable_cutlists import start,label,save,export_pdf,table_header

def band_diagram(s,x,y,bands):
 w,h=26,10
 s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#edf2f5" stroke="#52606b" stroke-width=".3"/>')
 for on,line in zip(bands,[(x,y,x+w,y),(x,y+h,x+w,y+h),(x,y,x,y+h),(x+w,y,x+w,y+h)]):
  if on:s.append(f'<path d="M{line[0]} {line[1]} L{line[2]} {line[3]}" stroke="#b8590e" stroke-width="1.2"/>')
 for xx,yy,name in [(x+9,y-1.5,'L1'),(x+9,y+h+5,'L2'),(x-10,y+7,'W1'),(x+w+2,y+7,'W2')]:label(s,xx,yy,name)

def main():
 from PySide import QtGui
 app=QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])
 root=Path(__file__).resolve().parent
 for project in ['bed','cabinet']:
  folder=root/'workshop'/project
  panels=sorted(json.loads((folder/'layout.json').read_text())['panels'],key=lambda p:(p['module'],p['id']))
  pages=[];rows=[]
  s=start(project.upper()+' | MANUAL CUTTING + EDGE BANDING','Whole-mm cutting targets | Colour and edge names identify the banded edges.','Short bond / Letter: landscape, fit to printable area.')
  notes=['Do NOT edge-band every part. Follow each part ID and its orange edge marks.',
   'NONE means no edge band. ALL FOUR means both long and both short edges.',
   'L1 / L2 run along Length. W1 / W2 run along Width. Diagram is not to scale.',
   'Keep the edge names with the part when rotating it; they are reference labels,',
   'not necessarily the installed top / bottom / left / right. Mark the exposed face',
   'during dry-fit and check against the model before applying a single-edge band.',
   'Band flags come from the existing CAD schedule; they have not been re-audited',
   'as a new exposure / joinery design. Do not band a mating edge without checking.',
   'Sizes are blank targets BEFORE banding, rounded to the nearest whole mm.',
   'Dry-fit related parts and check final sizing: rounding is not a checked redesign.',
   'Do not substitute these targets into the original CAD saw-step coordinates.',
   'Stock assumptions: core 18 mm + laminate each face; measure actual thickness.',
   'Edge-band thickness assumed 1 mm. Saw kerf assumed 4 mm; trim 5 mm per edge.',
   'Ordinary wood glue needs bare wood. Bare edge to laminate needs an adhesive',
   'rated for that bond, plus mechanical joints. Wheel plates need fixings, not glue.']
  for i,t in enumerate(notes):label(s,10,40+i*9,t)
  pages.append(save(s,folder/'Manual_mm_00.svg'))
  for page in range(math.ceil(len(panels)/6)):
   s=start(project.upper()+' | WHOLE-mm CUT TARGETS | '+str(page+1),'Qty = 1 per ID | Cut blank size before edge band | Dimensions in mm','Short bond / Letter: landscape, fit to printable area.')
   label(s,10,34,'Orange = apply band. Grey = leave unbanded. Check exposed edge orientation during dry-fit.')
   table_header(s,[20,100,35,65,57],['ID','Part / module','Cut L / W','Edge diagram','Band instruction'])
   for i,p in enumerate(panels[page*6:(page+1)*6]):
    y=49+i*22;b=p['bands'];l=math.floor(p['blank_l']+.5);w=math.floor(p['blank_w']+.5)
    s.append(f'<rect x="10" y="{y}" width="277" height="22" fill="{"#f6f8fa" if i%2==0 else "white"}"/>')
    label(s,12,y+8,p['id'],font_weight='bold');label(s,32,y+8,p['part'].replace('_',' '));label(s,32,y+15,p['module'].replace('_',' '))
    label(s,132,y+8,l,font_weight='bold');label(s,132,y+15,w,font_weight='bold')
    band_diagram(s,184,y+6,b)
    instruction='NONE' if not any(b) else 'ALL FOUR' if all(b) else f'{sum(b[:2])} long + {sum(b[2:])} short'
    label(s,232,y+8,instruction,font_weight='bold')
    edges=' / '.join(n for n,on in zip(['L1','L2','W1','W2'],b) if on)
    if not all(b):label(s,232,y+15,edges)
    rows.append([p['id'],p['module'],p['part'],1,l,w,instruction,*b])
   label(s,10,188,'Rounded targets: check matching parts before final sizing. Follow the reference legend on page 1.')
   label(s,10,195,'Existing CAD layouts / coordinates remain separate references. Hardware-dependent parts need checking.')
   pages.append(save(s,folder/f'Manual_mm_{page+1:02d}.svg'))
  with (folder/'Manual_Whole_mm.csv').open('w',newline='') as f:
   writer=csv.writer(f,lineterminator="\n");writer.writerow(['ID','Module','Part','Qty','Target length mm','Target width mm','Band instruction','Band L1','Band L2','Band W1','Band W2']);writer.writerows(rows)
  export_pdf(pages,folder/'Manual_Whole_mm.pdf',['Manual_mm_01'])
  assert len(rows)==len(panels)
  print(project,len(rows),'parts with edge diagrams')
