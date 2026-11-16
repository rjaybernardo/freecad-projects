from pathlib import Path
import json,re,subprocess
import xml.etree.ElementTree as ET
from PySide6 import QtGui
app=QtGui.QGuiApplication([])
P=Path('/home/rjaybernardo/Documents/FreeCAD/Bedroom Cabinet')
report={}
for project in ['bed','cabinet']:
 folder=P/'workshop'/project
 pages=sorted(folder.glob('Sheet_*.svg'));ids=[];errors=[]
 for path in pages:
  root=ET.parse(path).getroot()
  assert root.attrib['viewBox']=='0 0 297 210'
  for t in root.findall('.//{*}text'):
   size=float(t.get('font-size'));assert size>=4.3
   if 'transform' in t.attrib or t.get('text-anchor')=='middle':continue
   # Millimetre user units: measure at 100x resolution to avoid rounding.
   font=QtGui.QFont('DejaVu Sans');font.setPixelSize(round(size*100));font.setBold(t.get('font-weight')=='bold')
   width=QtGui.QFontMetricsF(font).horizontalAdvance(t.text or '')/100
   x=float(t.get('x'));y=float(t.get('y'))
   if not (0<=x and x+width<=294 and 0<y<=203):errors.append((path.name,t.text,round(x+width,2)))
   if '_Parts_' in path.stem:
    if re.fullmatch('[BC][0-9]{3}',t.text or ''):ids.append(t.text)
    if 49<y<182:
     limit=next((v for v in [22,44,140,183,226,287] if v>x),287)
     if x+width>limit-.25:errors.append((path.name,'cell overflow: '+str(t.text),round(x+width,2),limit))
  if '_Saw_' in path.stem:
   for t in root.findall('.//{*}text'):
    if 49<float(t.get('y'))<187:
     font=QtGui.QFont('DejaVu Sans');font.setPixelSize(430)
     x=float(t.get('x'));width=QtGui.QFontMetricsF(font).horizontalAdvance(t.text or '')/100
     limit=next((v for v in [25,40,75,110,135,287] if v>x),287)
     if x+width>limit-.25:errors.append((path.name,'saw cell overflow: '+str(t.text),round(x+width,2),limit))
 data=json.loads((folder/'layout.json').read_text())
 assert sorted(ids)==sorted(p['id'] for p in data['panels'])
 assert not errors,errors
 info=subprocess.check_output(['pdfinfo',str(folder/'Cutting_Layouts.pdf')],text=True)
 assert int(re.search(r'Pages:\s+(\d+)',info)[1])==len(pages)
 assert '(A4)' in info
 report[project]={'pages':len(pages),'parts_listed_once':len(ids),'minimum_body_pt':round(4.3*72/25.4,1),'page_and_cell_text_bounds':'passed','paper':'A4 landscape'}
(P/'workshop/readability-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
