"""Read-only audit of delivered model geometry, drawer travel and cutting layouts.
Run with system Python on CachyOS (FreeCAD libs installed), or freecadcmd.
This validates model fit and layout completeness, not hardware or structural ratings.
"""
from pathlib import Path
import sys,json,itertools,hashlib,zipfile,xml.etree.ElementTree as ET
sys.path.insert(0,'/usr/lib/freecad/lib')
import FreeCAD as App
P=Path(__file__).resolve().parent


def volume(a,b):
    u,v=a.BoundBox,b.BoundBox
    if min(min(getattr(u,k+'Max'),getattr(v,k+'Max'))-max(getattr(u,k+'Min'),getattr(v,k+'Min')) for k in 'XYZ')<1e-6:return 0
    return a.common(b).Volume


def validate():
    report={}
    for filename,project in [('Bed_Wall_Unit_v8.FCStd','bed'),('Bedroom_Cabinet_Modern_v9.FCStd','cabinet')]:
        d=App.openDocument(str(P/filename));refs=set(d.Reference_Room.OutListRecursive)
        objects=[o for o in d.Objects if o.isDerivedFrom('Part::Feature') and o not in refs]
        assert all(not o.Shape.isNull() and o.Shape.isValid() for o in objects)
        wood=[o for o in objects if 'CutListRow' in o.PropertiesList]
        lights=[o for o in objects if o.Name.startswith('LED_')]
        furniture=[o for o in objects if o not in lights]
        for a,b in itertools.combinations(furniture,2):assert volume(a.Shape,b.Shape)<.01,('closed collision',a.Name,b.Name)
        for a in lights:
            for b in wood:assert volume(a.Shape,b.Shape)<.01,('LED/wood collision',a.Name,b.Name)
        moving=[o for o in furniture if ('MovingDrawer' in o.PropertiesList and o.MovingDrawer) or (o.Name.startswith(('Drawer_','Table_Drawer_')) and 'Partition' not in o.Name)]
        fixed=[o for o in furniture if o not in moving and not o.Name.startswith('Door')]+lights
        for o in moving:
            if 'MovingDrawer' in o.PropertiesList and o.MovingDrawer:
                g=next(g for g in o.InListRecursive if 'OpenDirection' in g.PropertiesList);direction=g.OpenDirection;travel=g.OpenTravel.Value
            else:direction=App.Vector(0,1 if project=='bed' else -1,0);travel=350 if project=='bed' else 400
            for distance in [1,20,42,80,150,travel]:
                sh=o.Shape.copy();sh.translate(direction*distance)
                for other in fixed:assert volume(sh,other.Shape)<.01,('motion collision',o.Name,other.Name,distance)
        fronts=[o for o in furniture if o.Name.startswith('Door') or ('Drawer' in o.Name and '_Front' in o.Name)]
        for o in fronts:
            b=o.Shape.BoundBox;assert len(o.Shape.Faces)==6 and abs(o.Shape.Volume-b.XLength*b.YLength*b.ZLength)<.0001
        for g in d.Objects:
            if g.TypeId=='App::DocumentObjectGroup' and g.Name.startswith('Pull_'):
                assert any(p.Name=='Drawer_Tower' or p.Name.startswith(('Nightstand_','Side_Box_','Foot_Box_')) for p in g.InListRecursive)
        if project=='bed':
            wheels=[o for o in furniture if o.Name.startswith('Wheel_')];assert len(wheels)==24
            assert all(abs(o.Shape.BoundBox.ZMin)<1e-5 for o in wheels)
            assert all(not o.Name.startswith('Bottom') for g in d.Storage_Bed.Group if not g.Name.startswith('Head_Box') for o in g.Group)
            lids=[next(o for o in g.Group if o.Name.startswith('Lid')) for g in d.Storage_Bed.Group if g.Name.startswith('Head_Box')]
            lids.sort(key=lambda o:o.Shape.BoundBox.XMin);assert abs(lids[1].Shape.BoundBox.XMin-lids[0].Shape.BoundBox.XMax-3)<1e-5
        if project=='bed':
            head=list(d.Headboard.OutListRecursive)
            panel=[o for o in head if 'CutListRow' in o.PropertiesList]
            assert len(panel)==1 and panel[0].Name=='Plain_Backboard'
            b=panel[0].Shape.BoundBox
            assert abs(b.XLength-1587.2)<.001 and abs(b.YLength-19.6)<.001 and abs(b.ZLength-1200)<.001
            assert len([o for o in head if o.Name.startswith('Timber_Backboard_Batten')])==3
            assert not any(o.Name.startswith(('Upholstered_Panel_Base','Upholstery_Foam')) for o in objects)
        data=json.loads((P/'workshop'/project/'layout.json').read_text());settings=data['settings'];panels={p['id']:p for p in data['panels']}
        assert len(wood)==len(panels) and set(panels)=={o.PartID for o in wood}
        used=[]
        for sheet in data['sheets']:
            for p in sheet['panels']:
                used.append(p['id']);original=panels[p['id']]
                assert abs(original['blank_l']-(original['finished_l']-settings['EdgeBand']*sum(original['bands'][2:])))<.001
                assert abs(original['blank_w']-(original['finished_w']-settings['EdgeBand']*sum(original['bands'][:2])))<.001
                assert p['x']>=settings['Trim']-.001 and p['y']>=settings['Trim']-.001
                assert p['x']+p['l']<=settings['StockLength']-settings['Trim']+.001
                assert p['y']+p['w']<=settings['StockWidth']-settings['Trim']+.001
                for q in sheet['panels']:
                    if p is q:continue
                    dx=max(q['x']-p['x']-p['l'],p['x']-q['x']-q['l']);dy=max(q['y']-p['y']-p['w'],p['y']-q['y']-q['w'])
                    assert max(dx,dy)>=settings['Kerf']-.001
        assert sorted(used)==sorted(panels)
        assert len([o for o in d.Objects if o.TypeId=='TechDraw::DrawPage' and o.Name.startswith('Cutting_')])==data['sheet_count']
        expected_manual=12 if project=='bed' else 9
        assert len([o for o in d.Assembly_Manual.Group if o.TypeId=='TechDraw::DrawPage'])==expected_manual
        with zipfile.ZipFile(P/filename) as archive:
            for path in archive.namelist():
                if path.endswith('.svg'):ET.fromstring(archive.read(path))
        report[project]={'valid_solids':len(objects),'plywood_panels':len(wood),'square_fronts':len(fronts),'sheets':data['sheet_count'],'manual_pages':expected_manual,
            'closed_collisions':0,'sampled_drawer_motion_collisions':0,'led_wood_collisions':0,'panel_layout_bounds_and_kerf':'passed','embedded_svg_pages':'valid'}
        App.closeDocument(d.Name)
    originals={'Bed_Wall_Unit_v6.FCStd':'c7fa9ecd7e18cd24827cf34c420f6018fc55706cee058eff97c054e9b4709a04','Bedroom_Cabinet_Modern_v8.FCStd':'7b74b25fb54b0f7c82156d6e9f0d6818339f8107c73bfa724e761df22effd748'}
    for f,sha in originals.items():assert hashlib.sha256((P/f).read_bytes()).hexdigest()==sha
    (P/'workshop-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print('WORKSHOP AUDIT PASSED; previous approved models unchanged')


if __name__=='__main__':validate()
