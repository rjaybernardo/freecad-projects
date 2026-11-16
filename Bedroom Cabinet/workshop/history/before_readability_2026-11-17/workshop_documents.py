"""Native FreeCAD cutting pages, one label per panel and guillotine saw sequence.
All lengths in mm. This is a deterministic heuristic, not a proof of optimum.
"""
from pathlib import Path
import csv
import json
import math
import random
import html
import FreeCAD as App

DEFAULTS={'StockLength':2440.,'StockWidth':1220.,'Trim':5.,'Kerf':4.,'EdgeBand':1.,'AllowRotation':1}
PALETTE=['#dce9ef','#e6dfed','#e5edd9','#f3e4cb','#d6e9e4','#f0dce1','#e4e6f0','#eee9d3']


def csv_write(path, headers, rows):
    with Path(path).open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(headers);w.writerows(rows)


def svg_start(title, subtitle=''):
    return ['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="420mm" height="297mm" viewBox="0 0 420 297">',
            '<rect width="420" height="297" fill="white"/>',
            '<style>text {font-family:DejaVu Sans,sans-serif;fill:#203446} .small{font-size:2.5px} .body{font-size:3.1px}</style>',
            f'<text x="12" y="15" font-size="6" font-weight="bold">{html.escape(title)}</text>',
            f'<text x="12" y="23" font-size="3.2">{html.escape(subtitle)}</text>',
            '<text x="12" y="290" class="small">BEDROOM WORKSHOP | mm | verify stock and purchased hardware before cutting | revision 2026-11-15</text>']


def text(svg,x,y,value,size=3.1,**attrs):
    extra=' '.join(f'{k.replace("_","-")}="{html.escape(str(v))}"' for k,v in attrs.items())
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{html.escape(str(value))}</text>')


def native_page(doc, group, path, name):
    # FreeCAD embeds the template file into the saved FCStd archive.
    page=doc.addObject('TechDraw::DrawPage',name)
    template=doc.addObject('TechDraw::DrawSVGTemplate',name+'_Template')
    template.Template=str(path.resolve());page.Template=template;group.addObject(page)
    page.Label=path.stem.replace('_',' ')
    if App.GuiUp:page.ViewObject.Visibility=False
    return page


def spreadsheet(doc, group, name, headers, rows, note=''):
    old=doc.getObject(name)
    if old:doc.removeObject(old.Name)
    s=doc.addObject('Spreadsheet::Sheet',name);group.addObject(s)
    s.set('A1',"'"+note)
    for c,h in enumerate(headers):
        col=chr(65+c);s.set(col+'3',"'"+h);s.setColumnWidth(col,110 if c else 160)
    s.setStyle('A3:'+chr(64+len(headers))+'3','bold')
    s.setBackground('A3:'+chr(64+len(headers))+'3',(0.82,0.9,0.94))
    for i,row in enumerate(rows,4):
        for c,value in enumerate(row):s.set(chr(65+c)+str(i),str(value) if isinstance(value,(float,int)) else "'"+str(value))
    return s


def default_band(row,obj,project):
    module,name,l,w,t,note=row
    if ('Door' in name or ('Drawer' in name and 'Front' in name) or 'edge-band 4 sides' in note):return [1,1,1,1]
    if any(k in name for k in ['Drawer_Side','Drawer_Back']):
        # Exposed top edge is parallel to X or Y, not Z.
        b=obj.Shape.BoundBox
        edge=max(b.XLength,b.YLength)
        return [1,0,0,0] if abs(edge-l)<abs(edge-w) else [0,0,1,0]
    if any(k in name for k in ['Back','Bottom','Plinth','Headboard','Upholstered','WheelPad','Guide','Scribe','Rear_Base']):return [0,0,0,0]
    b=obj.Shape.BoundBox; dims=[b.XLength,b.YLength,b.ZLength]
    normal=min(range(3),key=lambda i:abs(dims[i]-t))
    front_axis=0 if any('Side_Box' in g.Name for g in obj.InListRecursive) else 1
    if normal==front_axis:return [0,0,0,0]
    edge_axis=next(i for i in range(3) if i not in [normal,front_axis])
    edge=dims[edge_axis]
    return [1,0,0,0] if abs(edge-l)<abs(edge-w) else [0,0,1,0]


def panel_rows(doc, rows, project):
    objects={o.CutListRow:o for o in doc.Objects if 'CutListRow' in o.PropertiesList}
    assert set(objects)==set(range(len(rows))),('Unmapped fabrication rows',set(range(len(rows)))-set(objects))
    data=[];prefix='B' if project=='bed' else 'C'
    assigned={o.PartID for o in objects.values() if 'PartID' in o.PropertiesList and o.PartID}
    next_id=max([int(value[1:]) for value in assigned if value.startswith(prefix)]+[0])+1
    for i,row in enumerate(rows):
        o=objects[i]
        if 'PartID' in o.PropertiesList and o.PartID:
            identifier=o.PartID
        else:
            identifier=f'{prefix}{next_id:03d}';next_id+=1
        if 'PartID' not in o.PropertiesList:o.addProperty('App::PropertyString','PartID','Fabrication')
        o.PartID=identifier
        o.Label=identifier+' '+o.Label
        band=default_band(row,o,project)
        data.append({'id':identifier,'module':row[0],'part':row[1],'object':o.Name,'finished_l':row[2],'finished_w':row[3],
                     'thickness':row[4],'bands':band,'note':row[5]})
    return data


def nest(panels,settings):
    sw,sh,trim,kerf=(round(settings[k]*10) for k in ['StockLength','StockWidth','Trim','Kerf'])
    usable=(sw-2*trim,sh-2*trim)
    items=[]
    for p in panels:
        assert abs(p['thickness']-19.6)<0.01,('Mixed stock',p)
        p['blank_l']=round(p['finished_l']-settings['EdgeBand']*sum(p['bands'][2:]),1)
        p['blank_w']=round(p['finished_w']-settings['EdgeBand']*sum(p['bands'][:2]),1)
        items.append((p,round(p['blank_l']*10),round(p['blank_w']*10)))
    rng=random.Random(20261115); best=None
    for trial in range(24):
        if trial==0:ordered=sorted(items,key=lambda z:z[1]*z[2],reverse=True)
        elif trial==1:ordered=sorted(items,key=lambda z:(max(z[1:]),min(z[1:])),reverse=True)
        else:ordered=sorted(items,key=lambda z:z[1]*z[2]*rng.uniform(.7,1.3),reverse=True)
        sheets=[]
        for p,l,w in ordered:
            choices=[]
            for si,sheet in enumerate(sheets):
                for ni,node in enumerate(sheet['free']):
                    for rotated,(pw,ph) in enumerate([(l,w),(w,l)] if settings['AllowRotation'] else [(l,w)]):
                        if pw<=node['w'] and ph<=node['h']:
                            choices.append(((node['w']*node['h']-pw*ph,min(node['w']-pw,node['h']-ph)),si,ni,rotated,pw,ph))
            if not choices:
                options=[(l,w,False)]
                if settings['AllowRotation']:options.append((w,l,True))
                valid=[v for v in options if v[0]<=usable[0] and v[1]<=usable[1]]
                assert valid,('Panel cannot fit stock',p['id'],l/10,w/10)
                sheet={'free':[{'x':trim,'y':trim,'w':usable[0],'h':usable[1],'node':'S'+str(len(sheets)+1)}], 'panels':[],'cuts':[]}
                sheets.append(sheet);pw,ph,rot=valid[0];choices=[((0,0),len(sheets)-1,0,rot,pw,ph)]
            _,si,ni,rotated,pw,ph=min(choices,key=lambda z:z[0])
            s=sheets[si];n=s['free'].pop(ni); x,y=n['x'],n['y'];rw,rh=n['w'],n['h'];nid=n['node']
            vertical=(rw-pw > rh-ph) if trial%2==0 else (rw*ph > rh*pw)
            def free(xx,yy,ww,hh,node):
                if ww>0 and hh>0:s['free'].append({'x':xx,'y':yy,'w':ww,'h':hh,'node':node})
            def cut(axis,at,span,child):
                region=[x,y,rw,rh] if child=='1' else ([x,y,pw,rh] if vertical else [x,y,rw,ph])
                s['cuts'].append({'parent':nid if child=='1' else nid+'a','axis':axis,'at':at/10,'span':span/10,'kerf':kerf/10,'panel':p['id'],'region':[v/10 for v in region]})
            if vertical:
                if rw>pw:cut('X',x+pw,rh,'1')
                if rh>ph:cut('Y',y+ph,pw,'2')
                free(x+pw+kerf,y,rw-pw-kerf,rh,nid+'b')
                free(x,y+ph+kerf,pw,rh-ph-kerf,nid+'c')
            else:
                if rh>ph:cut('Y',y+ph,rw,'1')
                if rw>pw:cut('X',x+pw,ph,'2')
                free(x,y+ph+kerf,rw,rh-ph-kerf,nid+'b')
                free(x+pw+kerf,y,rw-pw-kerf,ph,nid+'c')
            s['panels'].append({'id':p['id'],'x':x/10,'y':y/10,'l':pw/10,'w':ph/10,'rotated':bool(rotated)})
        score=(len(sheets),sum(len(s['cuts']) for s in sheets),-sum(max([f['w']*f['h'] for f in s['free']] or [0]) for s in sheets))
        if best is None or score<best[0]:best=(score,sheets)
    sheets=best[1]
    used=[]
    for si,s in enumerate(sheets,1):
        for p in s['panels']:
            assert p['x']>=trim/10 and p['y']>=trim/10
            assert p['x']+p['l']<=(sw-trim)/10+.001
            assert p['y']+p['w']<=(sh-trim)/10+.001
            used.append(p['id'])
            for q in s['panels']:
                if p is q:continue
                dx=max(q['x']-(p['x']+p['l']),p['x']-(q['x']+q['l']))
                dy=max(q['y']-(p['y']+p['w']),p['y']-(q['y']+q['w']))
                assert max(dx,dy)>=kerf/10-.001,('Kerf/overlap',p,q)
        for f in s['free']:
            for k in ['x','y','w','h']:f[k]/=10
    assert sorted(used)==sorted(p['id'] for p in panels)
    return sheets


def sheet_svg(path,si,sheet,panels,settings,total):
    lookup={p['id']:p for p in panels};s=svg_start(f'CUTTING LAYOUT {si:02d} / {total}',
       f'{settings["StockLength"]:g} x {settings["StockWidth"]:g} | 19.6 finished plywood, HPL both faces | kerf {settings["Kerf"]:g} | trim {settings["Trim"]:g} each edge')
    ox,oy,scale=12,39,0.126
    s.append(f'<rect x="{ox}" y="{oy}" width="{settings["StockLength"]*scale}" height="{settings["StockWidth"]*scale}" fill="#eeeeee" stroke="#203446" stroke-width=".4"/>')
    for n,p in enumerate(sheet['panels']):
        x,y=ox+p['x']*scale,oy+p['y']*scale;w,h=p['l']*scale,p['w']*scale;panel=lookup[p['id']]
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PALETTE[n%len(PALETTE)]}" stroke="#465667" stroke-width=".18"/>')
        if h>6 and w>12:
            text(s,x+1,y+min(h/2,5),p['id'],min(3.5,h*.35))
            if h>12 and w>30:text(s,x+1,y+9,f'{p["l"]:g} x {p["w"]:g}',2.5)
        elif w>12:text(s,x+1,y+max(h/2,1.6),p['id'],1.8)
        else:
            s.append(f'<text transform="translate({x+w/2},{y+1}) rotate(90)" font-size="1.9">{p["id"]}</text>')
        bands=panel['bands']
        if p['rotated']:bands=[bands[2],bands[3],bands[0],bands[1]]
        for enabled,line in zip(bands,[(x,y,x+w,y),(x,y+h,x+w,y+h),(x,y,x,y+h),(x+w,y,x+w,y+h)]):
            if enabled:s.append(f'<path d="M{line[0]} {line[1]} L{line[2]} {line[3]}" stroke="#cf6a21" stroke-width=".65"/>')
    area=sum(p['l']*p['w'] for p in sheet['panels']);stock=settings['StockLength']*settings['StockWidth']
    text(s,12,205,f'{len(sheet["panels"])} panels | blank area {area/1e6:.3f} m2 | sheet use {100*area/stock:.1f}% | {len(sheet["cuts"])} guillotine cuts',3.5)
    text(s,12,213,'Orange = banded edge. Dimensions = laminated blank BEFORE edge band. Grey = kerf, trim or offcut.',3)
    text(s,12,220,'L1/L2 are the two edges parallel to finished Length; W1/W2 parallel to Width. Orange thickness is symbolic.',2.8)
    text(s,12,227,'Grain: rotation allowed by default for plain laminate. Set AllowRotation = 0 for directional laminate and regenerate.',2.8)
    text(s,12,234,'Follow SawCuts.csv / native SawCuts sheet for the cutting sequence; label each piece immediately.',2.8)
    text(s,12,241,'Trim all four edges first. Origin is the stock lower-left corner; X along 2440, Y along 1220.',2.8)
    text(s,12,248,'Drill cable passages, rout internal grip recesses, and cut scribe strips to fit AFTER the rectangular blanks are cut.',2.8)
    text(s,12,255,'Heuristic nesting of each project separately; sheet count is the achieved layout, not a guaranteed minimum.',2.8)
    text(s,330,36,'PART / BLANK L x W',3.5,font_weight='bold')
    for n,p in enumerate(sheet['panels'][:46]):
        source=lookup[p['id']];text(s,330,43+n*4.9,f'{p["id"]}  {source["blank_l"]:g} x {source["blank_w"]:g}',2.6)
    if len(sheet['panels'])>46:text(s,330,275,'More IDs: see CutSchedule',2.5)
    s.append('</svg>');path.write_text('\n'.join(s))


def generate(doc,panels,project,output,settings=None):
    settings=dict(DEFAULTS if settings is None else settings)
    out=Path(output)/'workshop'/project;out.mkdir(parents=True,exist_ok=True)
    for stale in out.glob('Sheet_[0-9][0-9].svg'): stale.unlink()
    g=doc.getObject('Workshop_Documents') or doc.addObject('App::DocumentObjectGroup','Workshop_Documents')
    sheets=nest(panels,settings)
    spreadsheet(doc,g,'CuttingSettings',['Setting','Value','Meaning'],[
        (k,v,{'EdgeBand':'Finished band thickness, not roll width','Trim':'All four edges','AllowRotation':'1 plain laminate; 0 grain along stock X'}.get(k,'mm')) for k,v in settings.items()],
        'Edit settings / band flags, then run regenerate_workshop.FCMacro. Pages do not auto-repack. Model thickness assumed core 18 + 0.8 HPL each face.')
    cuts=[];placements=[];summaries=[];offcuts=[];mapping={}
    for si,s in enumerate(sheets,1):
        for p in s['panels']:mapping[p['id']]=si;placements.append([p['id'],si,p['x'],p['y'],p['l'],p['w'],int(p['rotated'])])
        for i,c in enumerate(s['cuts'],1):cuts.append([si,i,c['parent'],c['axis'],c['at'],c['span'],c['kerf'],c['panel'],*c['region']])
        for i,f in enumerate(s['free'],1):offcuts.append([si,i,f['x'],f['y'],f['w'],f['h']])
        area=sum(p['l']*p['w'] for p in s['panels']);stock=settings['StockLength']*settings['StockWidth'];waste=stock-area
        offcut=sum(f['w']*f['h'] for f in s['free'])
        trimmed=stock-(settings['StockLength']-2*settings['Trim'])*(settings['StockWidth']-2*settings['Trim'])
        kerf_area=stock-trimmed-area-offcut
        assert kerf_area>=-.01
        summaries.append([si,len(s['panels']),round(area/1e6,4),round(100*area/stock,2),round(waste/1e6,4),len(s['cuts']),round(offcut/1e6,4),round(trimmed/1e6,4),round(kerf_area/1e6,4)])
        path=out/f'Sheet_{si:02d}.svg';sheet_svg(path,si,s,panels,settings,len(sheets));native_page(doc,g,path,f'Cutting_{si:02d}')
    hdr=['ID','Module','Part','Qty','Finished L','Finished W','Thickness','Band L1','Band L2','Band W1','Band W2','Blank L','Blank W','Sheet','Note']
    rows=[[p['id'],p['module'],p['part'],1,p['finished_l'],p['finished_w'],p['thickness'],*p['bands'],p['blank_l'],p['blank_w'],mapping[p['id']],p['note']] for p in panels]
    spreadsheet(doc,g,'CutSchedule',hdr,rows,'FINISHED sizes include edge band. Blank L = finished L - band thickness*(W1+W2); Blank W = finished W - band thickness*(L1+L2). Each ID is one physical panel.')
    spreadsheet(doc,g,'SheetSummary',['Sheet','Panels','Blank m2','Use %','Remainder m2','Cuts','Offcut m2','Trim m2','Kerf and slivers m2'],summaries,'Actual achieved nesting; remainder includes kerf, trim and offcuts. No extra generic 25% added.')
    spreadsheet(doc,g,'SawCuts',['Sheet','Step','Parent region','Axis','Coordinate','Cut span','Kerf','Target ID','Region X','Region Y','Region L','Region W'],cuts,'Coordinates from original stock origin; trim first. Follow in order within each sheet. Kerf consumes positive X/Y after coordinate.')
    spreadsheet(doc,g,'Offcuts',['Sheet','No','X','Y','Length','Width'],offcuts,'Rectangular remaining regions after cuts; small strips may be impractical to save.')
    total_band=sum(sum(p['bands'][:2])*p['finished_l']+sum(p['bands'][2:])*p['finished_w'] for p in panels)/1000
    spreadsheet(doc,g,'Materials',['Material','Amount','Unit','Note'],[
        ['3/4 plywood, both faces laminated',len(sheets),'sheets','2440 x 1220, finished 19.6 mm assumption; measure actual stock'],
        ['Edge band, 1 mm thickness assumption',round(total_band,2),'m','Net lengths; width must cover finished thickness'],
        ['Edge band including 10% trimming allowance',round(total_band*1.1,2),'m','Round up to supplier roll length; review exposed-edge flags'],
        ['LED profiles / driver','see LightingSchedule','hardware','Excluded from plywood nesting']], 'Purchase quantities from achieved layouts. Panels requiring hardware confirmation remain provisional.')
    for filename,headers,values in [('CutSchedule',hdr,rows),('SawCuts',['Sheet','Step','Parent region','Axis','Coordinate','Cut span','Kerf','Target ID','Region X','Region Y','Region L','Region W'],cuts),('Placements',['ID','Sheet','X','Y','Length','Width','Rotated'],placements),('Offcuts',['Sheet','No','X','Y','Length','Width'],offcuts),('SheetSummary',['Sheet','Panels','Blank m2','Use %','Remainder m2','Cuts','Offcut m2','Trim m2','Kerf and slivers m2'],summaries)]:csv_write(out/(filename+'.csv'),headers,values)
    # Common CSV schema also makes it straightforward to import into other optimizers.
    csv_write(out/'Panels_for_optimizer.csv',['Length','Width','Qty','Label','Material'],[[p['blank_l'],p['blank_w'],1,p['id'],'19.6 mm HPL both faces'] for p in panels])
    payload={'project':project,'settings':settings,'panels':panels,'sheets':sheets,'sheet_count':len(sheets),'edge_band_net_m':round(total_band,3),'edge_band_with_trim_m':round(total_band*1.1,3)}
    (out/'layout.json').write_text(json.dumps(payload,indent=2))
    doc.recompute();return payload


def add(doc,rows,project,output):
    return generate(doc,panel_rows(doc,rows,project),project,output)
