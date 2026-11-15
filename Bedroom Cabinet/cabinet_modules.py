"""Nested cabinet/drawer groups and reversible GUI isolation. No panel placement changes."""
import re
import FreeCAD as App

GROUP='App::DocumentObjectGroup'


def _role(obj,value):
    if 'AssemblyRole' not in obj.PropertiesList:obj.addProperty('App::PropertyString','AssemblyRole','Assembly')
    obj.AssemblyRole=value


def _group(doc,parent,name,label,role):
    obj=doc.getObject(name) or doc.addObject(GROUP,name)
    obj.Label=label;_role(obj,role)
    if obj not in parent.Group:parent.addObject(obj)
    return obj


def _move(source,target,objects):
    for obj in objects:
        if obj in source.Group:source.removeObject(obj)
        if obj not in target.Group:target.addObject(obj)


def _wheel_sets(doc,drawer):
    wheels=[o for o in drawer.Group if o.isDerivedFrom('Part::Feature') and o.Name.startswith('Wheel_')]
    if not wheels:return
    supports=[o for o in drawer.Group if o.isDerivedFrom('Part::Feature') and o.Name.startswith(('Drawer_WheelPad','CasterPlate','CasterFork'))]
    for i,wheel in enumerate(sorted(wheels,key=lambda o:o.Name),1):
        nearest=[]
        for part in supports:
            p=part.Shape.BoundBox.Center
            closest=min(wheels,key=lambda w:(w.Shape.BoundBox.Center.x-p.x)**2+(w.Shape.BoundBox.Center.y-p.y)**2)
            if closest==wheel:nearest.append(part)
        assert len(nearest)==4,(drawer.Name,wheel.Name,len(nearest))
        group=_group(doc,drawer,drawer.Name+'_Wheel_'+str(i),f'Wheel set {i} — pad + fixed wheel','Wheel assembly')
        _move(drawer,group,[wheel]+nearest)


def _drawer(doc,parent,folder,name,number,parts,travel,direction,label=None):
    group=_group(doc,folder,name,label or f'Drawer {number}','Drawer assembly')
    if 'OpenDirection' not in group.PropertiesList:group.addProperty('App::PropertyVector','OpenDirection','Drawer')
    if 'OpenTravel' not in group.PropertiesList:group.addProperty('App::PropertyLength','OpenTravel','Drawer')
    group.OpenDirection=App.Vector(*direction);group.OpenTravel=travel
    _move(parent,group,parts)
    for p in parts:
        if 'MovingDrawer' not in p.PropertiesList:p.addProperty('App::PropertyBool','MovingDrawer','Drawer')
        p.MovingDrawer=True
    return group


def _case(doc,module):
    if 'ModuleGroupingVersion' in module.PropertiesList and module.ModuleGroupingVersion==1:return
    _role(module,'Cabinet module')
    direct=[o for o in module.Group if o.isDerivedFrom('Part::Feature')]
    drawings={}
    for part in direct:
        match=re.match(r'^Drawer_([123])_(Front|Side_L|Side_R|Back|Bottom)(?:\d{3})?$',part.Name)
        if match:drawings.setdefault(int(match.group(1)),[]).append(part)
        elif part.Name.startswith('Table_Drawer_'):drawings.setdefault(1,[]).append(part)
    existing=[o for o in module.Group if o.TypeId==GROUP and o.Name.startswith('Drawer_Assembly_')]
    if drawings or existing:
        folder=_group(doc,module,module.Name+'_Drawers','Drawers','Drawer collection')
        for number,parts in sorted(drawings.items()):
            assert len(parts)==5,(module.Name,number,[p.Name for p in parts])
            is_bed=module.Name.startswith('Nightstand_')
            _drawer(doc,module,folder,module.Name+'_Drawer_'+str(number).zfill(2),number,parts,
                    350 if is_bed else 400,(0,1,0) if is_bed else (0,-1,0),
                    'Makeup table drawer' if module.Name=='Centre_TV_Makeup' else None)
        for number,drawer in enumerate(existing,1):
            _move(module,folder,[drawer]);drawer.Label=f'Drawer {number} — four floor wheels';_role(drawer,'Drawer assembly')
            _wheel_sets(doc,drawer)
    remaining=[o for o in module.Group if o.isDerivedFrom('Part::Feature')]
    plinth=[o for o in remaining if o.Name.startswith('Plinth_')]
    doors=[o for o in remaining if o.Name.startswith(('Door','Lid'))]
    fixed=[o for o in remaining if o not in plinth+doors]
    pulls=[o for o in module.Group if o.TypeId==GROUP and o.Name.startswith('Pull_')]
    if fixed or pulls:
        label='Panel + timber supports' if module.Name=='Headboard' else 'Carcass — fixed panels and shelves'
        group=_group(doc,module,module.Name+'_Carcass',label,'Carcass')
        _move(module,group,fixed+pulls)
    if plinth:
        group=_group(doc,module,module.Name+'_Plinth','Plinth / base','Plinth');_move(module,group,plinth)
    if doors:
        group=_group(doc,module,module.Name+'_Doors','Lift-up lid' if all(o.Name.startswith('Lid') for o in doors) else 'Doors','Doors / lids');_move(module,group,doors)
    # Keep the visual tree predictable: fixed case, base, drawers, then doors.
    priority={'Carcass':0,'Plinth':1,'Drawer collection':2,'Doors / lids':3}
    module.Group=sorted(module.Group,key=lambda o:priority.get(o.AssemblyRole if 'AssemblyRole' in o.PropertiesList else '',4))
    module.addProperty('App::PropertyInteger','ModuleGroupingVersion','Assembly');module.ModuleGroupingVersion=1


def organize(doc):
    """Called after the original geometry/cut schedule is complete; safe to repeat."""
    bed=doc.Name.startswith('Bed_Wall')
    if bed:
        names=['Nightstand_Left','Nightstand_Right','Upper_Left','Upper_Right','Bridge','Headboard']
        names += [o.Name for o in doc.Objects if o.TypeId==GROUP and re.fullmatch(r'(Head_Box_[LR]|Side_Box_[12][LR]|Foot_Box_[LR])',o.Name)]
    else:
        names=['Wardrobe_Left_Hanging','Tower_Right_Shelves','Centre_TV_Makeup','Drawer_Tower','Top_Box_Left','Top_Box_Centre','Top_Box_Right']
    for name in names:
        obj=doc.getObject(name)
        if obj:_case(doc,obj)
    labels={'Storage_Bed':'Bed platform — 8 modules','Tower_Left':'Left bedside cabinet set','Tower_Right':'Right bedside cabinet set',
            'Nightstand_Left':'Left nightstand','Nightstand_Right':'Right nightstand','Upper_Left':'Left upper cabinet','Upper_Right':'Right upper cabinet',
            'Bridge':'Overhead bridge cabinet','Headboard':'Plain backboard','Wardrobe_Left_Hanging':'Left wardrobe',
            'Tower_Right_Shelves':'Right shelf cabinet','Centre_TV_Makeup':'TV + makeup centre','Drawer_Tower':'Makeup drawer cabinet',
            'Top_Boxes':'Overhead cabinet modules','Top_Box_Left':'Left top cabinet','Top_Box_Centre':'Centre top cabinet','Top_Box_Right':'Right top cabinet'}
    for name,label in labels.items():
        if doc.getObject(name):doc.getObject(name).Label=label
    for name in names:
        if re.fullmatch(r'Side_Box_[12][LR]',name):doc.getObject(name).Label=('Left' if name.endswith('L') else 'Right')+' side drawer bay '+name[-2]
        elif re.fullmatch(r'(Head|Foot)_Box_[LR]',name):doc.getObject(name).Label=('Left' if name.endswith('L') else 'Right')+(' head lift-up box' if name.startswith('Head') else ' foot drawer bay')
    # Context labels remain unique without enabling global duplicate-label preferences.
    context={'Nightstand_Left':'nightstand L','Nightstand_Right':'nightstand R','Upper_Left':'upper L','Upper_Right':'upper R',
             'Wardrobe_Left_Hanging':'wardrobe','Tower_Right_Shelves':'shelf tower','Centre_TV_Makeup':'TV + makeup',
             'Drawer_Tower':'makeup cabinet','Bridge':'bridge','Headboard':'backboard',
             'Top_Box_Left':'top L','Top_Box_Centre':'top centre','Top_Box_Right':'top R'}
    def owner_module(obj):
        queue=[(p,1) for p in obj.InList if p.TypeId==GROUP];seen=set()
        while queue:
            current,depth=queue.pop(0)
            if current.Name in seen:continue
            seen.add(current.Name)
            if 'AssemblyRole' in current.PropertiesList and current.AssemblyRole=='Cabinet module':return current
            queue.extend((p,depth+1) for p in current.InList if p.TypeId==GROUP)
    for obj in doc.Objects:
        if obj.TypeId!=GROUP:continue
        if not any(p.TypeId==GROUP for p in obj.InList) and obj.Name.startswith(('Bed_Wall_Unit','Bedroom_Cabinet_v')):
            obj.Label='Bed + surrounding cabinets' if bed else 'TV + makeup + wardrobe'
        if 'AssemblyRole' not in obj.PropertiesList:continue
        module=owner_module(obj)
        if module is None:continue
        short=context.get(module.Name,module.Label)
        if module.Name.startswith('Side_Box_'):short='side bay '+module.Name.removeprefix('Side_Box_')
        elif module.Name.startswith('Foot_Box_'):short='foot bay '+module.Name[-1]
        elif module.Name.startswith('Head_Box_'):short='head box '+module.Name[-1]
        role=obj.AssemblyRole
        if role=='Drawer assembly':
            number=int(obj.Name.rsplit('_',1)[-1]) if re.search(r'_0[123]$',obj.Name) else 1
            obj.Label='Makeup table drawer' if module.Name=='Centre_TV_Makeup' else f'Drawer {number} · {short}'
        elif role=='Wheel assembly':obj.Label=f'Wheel {obj.Name.rsplit("_",1)[-1]} · {short}'
        elif role=='Carcass':obj.Label='Panel + timber supports' if module.Name=='Headboard' else 'Carcass · '+short
        elif role=='Drawer collection':obj.Label='Drawers · '+short
        elif role=='Plinth':obj.Label='Base · '+short
        elif role=='Doors / lids':obj.Label=('Lift-up lid · ' if module.Name.startswith('Head_Box_') else 'Doors · ')+short
    if doc.getObject('Cut_List_Materials'):doc.getObject('Cut_List_Materials').Label='Hardware schedules'
    doc.recompute()
    return {'modules':len(names),'drawers':len([o for o in doc.Objects if 'AssemblyRole' in o.PropertiesList and o.AssemblyRole=='Drawer assembly'])}


def _geometry_groups(doc):
    return [g for g in doc.Objects if g.TypeId==GROUP and any(o.isDerivedFrom('Part::Feature') for o in g.OutListRecursive)]


def _state_store():
    if not hasattr(App,'_BedroomIsolation'):App._BedroomIsolation={}
    return App._BedroomIsolation


def restore(doc=None):
    import FreeCADGui as Gui
    doc=doc or App.ActiveDocument
    if doc is None:return False
    state=_state_store().pop(doc.Name,None)
    if state is None:return False
    groups=_geometry_groups(doc)
    for g in sorted(groups,key=lambda g:len(g.InListRecursive)):
        if g.Name in state['visibility']:g.ViewObject.Visibility=state['visibility'][g.Name]
    for obj in doc.Objects:
        if obj.isDerivedFrom('Part::Feature') and obj.Name in state['visibility']:obj.ViewObject.Visibility=state['visibility'][obj.Name]
    if Gui.activeDocument() and Gui.activeDocument().Document.Name==doc.Name and hasattr(Gui.activeDocument().activeView(),'setCamera'):Gui.activeDocument().activeView().setCamera(state['camera'])
    Gui.updateGui();return True


def isolate(doc,objects):
    import FreeCADGui as Gui
    selected=set()
    for obj in objects:
        if obj.Document!=doc:continue
        for part in [obj]+obj.OutListRecursive:
            if part.isDerivedFrom('Part::Feature'):selected.add(part.Name)
    if not selected:raise ValueError('Select a cabinet module, drawer group or panel in the model tree.')
    groups=_geometry_groups(doc);view=Gui.activeDocument().activeView();store=_state_store()
    if not hasattr(view,'getCamera'):raise ValueError('Activate the 3D model tab, then select the group.')
    if doc.Name not in store:
        store[doc.Name]={'visibility':{o.Name:o.ViewObject.Visibility for o in doc.Objects if o.isDerivedFrom('Part::Feature') or o in groups},'camera':view.getCamera()}
    # Showing ancestors first avoids hidden parent groups hiding the selected drawer.
    for group in sorted(groups,key=lambda g:len(g.InListRecursive)):group.ViewObject.Visibility=True
    for obj in doc.Objects:
        if obj.isDerivedFrom('Part::Feature'):obj.ViewObject.Visibility=obj.Name in selected
    Gui.Selection.clearSelection();Gui.updateGui()
    # Use the established deterministic CAD camera helper without animation.
    from assembly_manual import camera
    camera(doc,(.65,1 if doc.Name.startswith('Bed_Wall') else -1,.65));Gui.updateGui()
    return selected


def launch_isolation_tool():
    import FreeCADGui as Gui
    from PySide import QtWidgets
    old=getattr(App,'_BedroomIsolationDialog',None)
    if old is not None:
        try:old.show();old.raise_();return old
        except RuntimeError:pass
    class IsolationTool(QtWidgets.QDialog):
        def __init__(self):
            super().__init__(Gui.getMainWindow());self.setWindowTitle('Work on one module');self.setMinimumWidth(310)
            layout=QtWidgets.QVBoxLayout(self);layout.addWidget(QtWidgets.QLabel('Select a cabinet, drawer or panel in the model tree.'))
            show=QtWidgets.QPushButton('SHOW ONLY SELECTED');back=QtWidgets.QPushButton('RESTORE PREVIOUS VIEW')
            layout.addWidget(show);layout.addWidget(back);self.status=QtWidgets.QLabel('No geometry or cut sizes are changed.');layout.addWidget(self.status)
            show.clicked.connect(self.focus);back.clicked.connect(self.back)
        def focus(self):
            try:
                doc=App.ActiveDocument
                if doc is None:raise ValueError('Open a bedroom furniture model first.')
                chosen=Gui.Selection.getSelection();names=isolate(doc,chosen)
                self.status.setText(f'Isolated {len(names)} parts. Select another group to switch.')
            except ValueError as e:self.status.setText(str(e))
        def back(self):
            self.status.setText('Previous view restored.' if restore() else 'No isolated view to restore.')
        def closeEvent(self,event):
            active=App.ActiveDocument.Name if App.ActiveDocument else None
            for name in list(_state_store()):
                doc=App.listDocuments().get(name)
                if doc:App.setActiveDocument(name);restore(doc)
                else:_state_store().pop(name,None)
            if active and App.listDocuments().get(active):App.setActiveDocument(active)
            event.accept()
    dialog=IsolationTool();App._BedroomIsolationDialog=dialog;dialog.show();return dialog
