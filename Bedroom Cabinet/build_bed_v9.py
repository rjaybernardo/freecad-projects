"""Revise the saved v8 bed into v9: wheels attach directly to drawer bottoms.

Preserves the saved model and IDs. Run with freecadcmd; v8 is never saved.
The archived v8 layout supplies the original per-edge band flags and blank notes.
"""
from pathlib import Path
import copy
import csv
import hashlib
import json
import shutil
import sys
import tempfile
import FreeCAD as App

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
SIDE_TRAVEL = 337
DRAWER_BOX_D = 450
WHEEL_MOUNT_H = 35.0  # provisional; floor to plate top / drawer underside
REVISION = 'Bed_Wall_Unit_v9'


def build():
    from workshop_documents import generate, spreadsheet, csv_write
    source = PROJECT/'Bed_Wall_Unit_v8.FCStd'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    history = PROJECT/'workshop/history/bed_v8_before_direct_mount'
    baseline = json.loads((history/'layout.json').read_text())
    with tempfile.TemporaryDirectory(prefix='bed-v9-revision-') as temp:
        disposable = Path(temp)/(REVISION+'.FCStd')
        shutil.copy2(source, disposable)
        doc = App.openDocument(str(disposable))
        old_root = doc.getObject('Bed_Wall_Unit_v8')
        root = doc.addObject('App::DocumentObjectGroup', REVISION)
        children = list(old_root.Group)
        old_root.Group = []
        root.Group = children
        root.Label = 'Bed + surrounding cabinets v9 — direct wheel mounts'
        root.addProperty('App::PropertyBool', 'IncludeBackboard', 'Headboard')
        root.IncludeBackboard = old_root.IncludeBackboard
        root.addProperty('App::PropertyString', 'HardwareAssumptions', 'Hardware')
        root.HardwareAssumptions = '25.4 mm fixed wheels directly beneath 19.6 mm drawer bottoms; total mounting height assumed 35 mm; verify actual plate, fixings and height.'
        doc.removeObject(old_root.Name)
        drawers = [o for o in doc.Objects if o.TypeId=='App::DocumentObjectGroup' and o.Name.startswith('Drawer_Assembly_') and 'AssumedCasterHeight' in o.PropertiesList]
        assert len(drawers)==6
        removed, changed = [], []
        for drawer in drawers:
            objects = [o for o in drawer.OutListRecursive if o.isDerivedFrom('Part::Feature')]
            bottom = next(o for o in objects if o.Name.startswith('Drawer_Bottom'))
            delta = bottom.Shape.BoundBox.ZMin-WHEEL_MOUNT_H
            assert abs(delta-19.6)<.001
            for o in objects:
                if o.Name.startswith('Drawer_WheelPad'):
                    removed.append(o.PartID)
                    doc.removeObject(o.Name)
                elif o.Name.startswith(('Drawer_Side_', 'Drawer_Back')):
                    assert o.TypeId=='Part::Box'
                    o.Placement.Base.z -= delta
                    o.Height = o.Height.Value + delta
                    changed.append(o.PartID)
                elif o==bottom:
                    o.Placement.Base.z -= delta
            drawer.addProperty('App::PropertyString','WheelMounting','Hardware')
            drawer.WheelMounting = 'Direct to underside of Drawer_Bottom; no plywood pads'
            drawer.HardwareStatus = 'Direct fixed-wheel plates; 35 mm installed height and fixings provisional'
        assert len(removed)==24 and len(changed)==18
        for o in doc.Objects:
            if o.Name.startswith('Guide_') and o.isDerivedFrom('Part::Feature'):
                o.Placement.Base.z -= 19.6
        doc.recompute()
        panels = []
        for p in copy.deepcopy(baseline['panels']):
            if p['id'] in removed:
                continue
            obj = doc.getObject(p['object'])
            assert obj is not None and obj.PartID==p['id']
            obj.CutListRow = len(panels)
            if p['id'] in changed:
                dims = [obj.Length.Value,obj.Width.Value,obj.Height.Value]
                dims.pop(next(i for i,d in enumerate(dims) if abs(d-p['thickness'])<.001))
                p['finished_l'],p['finished_w'] = [round(d,1) for d in sorted(dims,reverse=True)]
            if p['module'].startswith('Drawer_Assembly_'):
                p['note'] += '; direct wheel mounts beneath 19.6 mm bottom; verify installed caster height and fixings'
            panels.append(p)
        # Replace cutting templates and obsolete assembly pages on the NEW model only.
        for group_name in ['Workshop_Documents','Assembly_Manual']:
            group = doc.getObject(group_name)
            if group:
                for page in list(group.Group):
                    if page.TypeId=='TechDraw::DrawPage':
                        template_name = page.Template.Name if page.Template else None
                        doc.removeObject(page.Name)
                        if template_name and doc.getObject(template_name):
                            doc.removeObject(template_name)
        payload = generate(doc,panels,'bed',str(PROJECT),baseline['settings'])
        csv_write(PROJECT/'cut_list_bed_v9.csv', ['Module','Part','Qty','Length_mm','Width_mm','Thickness_mm','Edge_Work'],
                  [[p['module'],p['part'],1,p['finished_l'],p['finished_w'],p['thickness'],p['note']] for p in panels])
        with (PROJECT/'hardware_bed_v8.csv').open() as f:
            hardware = list(csv.DictReader(f))
        for row in hardware:
            if row['Item']=='Caster plate fixing set':
                row['Note']='Fix directly beneath 19.6 mm drawer bottom; match actual plate; verify fastener engagement and projection; no plywood pads'
            elif 'Fixed-direction caster' in row['Item']:
                row['Note']='4 per under-bed drawer, directly attached to bottom; provisional installed height 35 mm; verify actual hardware and load rating'
        csv_write(PROJECT/'hardware_bed_v9.csv',['Item','Qty','Note'],[[r['Item'],r['Qty'],r['Note']] for r in hardware])
        spreadsheet(doc, doc.Cut_List_Materials, 'Hardware', ['Item','Qty','Note'],
                    [[r['Item'],int(r['Qty']),r['Note']] for r in hardware], 'Bed v9 — wheel plates mount directly to drawer bottoms; no plywood pads.')
        doc.recompute()
        doc.Label = 'Bed wall unit v9 — wheels directly beneath drawers'
        doc.saveAs(str(PROJECT/(REVISION+'.FCStd')))
        App.closeDocument(doc.Name)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
    report = {'source':'Bed_Wall_Unit_v8.FCStd','source_sha256':source_hash,'revision':REVISION,
              'removed_pad_ids':removed,'changed_side_back_ids':changed,'panels':len(panels),
              'drawer_bottom_underside_mm':WHEEL_MOUNT_H,'drawer_bottom_top_mm':WHEEL_MOUNT_H+19.6,
              'mounting_height_status':'35 mm assumed; verify purchased hardware',
              'sheets':payload['sheet_count'],'edge_band_net_m':payload['edge_band_net_m']}
    (PROJECT/'workshop/bed/direct-mount-revision.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report


build()
