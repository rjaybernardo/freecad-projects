"""Provisional constant-voltage lighting: replace envelopes with purchased products.
The aluminium light extrusion is unrelated to the plywood L/C drawer grips.
"""
import math
import json
from pathlib import Path
import FreeCAD as App
import Part

VOLTAGE = 24
WATTS_PER_M = 10.0
PROFILE_W, PROFILE_H = 16.0, 10.0


def add(doc, root, rows, colours, project, params, output):
    g = doc.addObject('App::DocumentObjectGroup', 'LED_Lighting')
    root.addObject(g)
    for name, value, typ in [('AssumedVoltage', VOLTAGE, 'Integer'), ('AssumedWattsPerMetre', WATTS_PER_M, 'Float'),
                              ('SpecificationStatus', 'PROVISIONAL: confirm voltage, W/m, cut pitch, extrusion and driver datasheets', 'String')]:
        g.addProperty('App::Property'+typ, name, 'Lighting'); setattr(g,name,value)
    specs, routes = [], []
    def feature(name, shape, colour):
        o=doc.addObject('Part::Feature', name); o.Shape=shape; g.addObject(o); colours[o.Name]=colour
        o.addProperty('App::PropertyString','SpecificationStatus','Lighting'); o.SpecificationStatus=g.SpecificationStatus
        return o
    def profile(label, origin, length, direction='X', face='down'):
        # Local coordinates: X along extrusion; Y across; Z from wall/backing towards diffuser.
        outer=Part.makeBox(length,16,9)
        cavity=Part.makeBox(length+2,13,8,App.Vector(-1,1.5,1.5))
        metal=outer.cut(cavity)
        diffuser=Part.makeBox(length,13,1,App.Vector(0,1.5,9))
        strip=Part.makeBox(length,10,0.5,App.Vector(0,3,1.5))
        rotation = App.Rotation(App.Vector(1,0,0),180) if face=='down' else App.Rotation(App.Vector(1,0,0),90)
        if direction=='Z':
            # X -> Z, Y -> X, Z -> Y (light towards room = -Y).
            rotation=App.Rotation(App.Vector(0,0,1),App.Vector(1,0,0),App.Vector(0,-1,0),'ZXY')
        placement=App.Placement(App.Vector(*origin),rotation)
        for suffix, shape, colour in [('Aluminium',metal,(0.65,0.68,0.70)),('Diffuser',diffuser,(1.0,0.95,0.78)),('Strip',strip,(1.0,0.75,0.28))]:
            shape.Placement=placement
            o=feature('LED_'+label+'_'+suffix,shape,colour)
            o.addProperty('App::PropertyLength','ProfileLength','Lighting'); o.ProfileLength=length
        specs.append({'id':label,'length_mm':round(length,1),'location':origin,'direction':direction,'watts':round(length/1000*WATTS_PER_M,3)})
    if project=='bed':
        t=params['T']; yw=params['Y_WALL']; width=params['TOWER_W']; xi=params['XT_IN']; bw=params['BRIDGE_W']
        dz=2150; driver=(65,yw+65,dz); hub=(270,yw+90,dz+12); rear=yw+t+8
        for side,x in [('L',5),('R',params['WALL_W']-5-width)]:
            start=x+t+10; length=width-2*t-20; z=params['NIGHT_H']+params['OPEN_NICHE_H']+params['LIT_NICHE_H']
            profile('B_'+side,(start,yw+params['UPPER_D']-44,z),length)
            route=[hub,(hub[0],rear,hub[2]),(start+5,rear,hub[2]),(start+5,rear,z-6),(start+5,yw+params['UPPER_D']-50,z-6)]
            routes.append(('B_'+side,route))
        start=xi+t+20; length=bw-2*t-40; z=params['BRIDGE_Z']
        profile('B_H',(start,yw+150,z),length)
        routes.append(('B_H',[hub,(hub[0],rear,hub[2]),(start+5,rear,hub[2]),(start+5,rear,z-6),(start+5,yw+145,z-6)]))
    else:
        t=params['T']; rear=params['DEPTH']-t-8; driver=(40,330,2110); hub=(240,360,2125)
        profile('C_T',(540,80,params['NICHE_Z0']-t),760)
        for label,x in [('C_L',550),('C_R',1284)]:
            profile(label,(x,params['DEPTH']-t-6,820),410,'Z')
            routes.append((label,[hub,(hub[0],rear,hub[2]),(x+8,rear,hub[2]),(x+8,rear,825),(x+8,params['DEPTH']-t-7,825)]))
        routes.append(('C_T',[hub,(hub[0],rear,hub[2]),(545,rear,hub[2]),(545,rear,params['NICHE_Z0']-t-6),(545,75,params['NICHE_Z0']-t-6)]))
    driver_obj=feature('LED_Driver_Envelope',Part.makeBox(180,60,35,App.Vector(*driver)),(0.22,0.35,0.5))
    driver_obj.addProperty('App::PropertyString','Access','Lighting'); driver_obj.Access='Open cabinet door; unplug before servicing; ventilated enclosure per actual driver datasheet. Reserve 200 x 80 x 70 mm. No sealed box.'
    feature('LED_Distribution_Dimmer_Envelope',Part.makeBox(35,25,12,App.Vector(hub[0]-10,hub[1]-10,hub[2]-6)),(0.25,0.3,0.32))
    # Short low-voltage feed from driver to distribution; AC outlet position is site-specific.
    a=App.Vector(driver[0]+180,driver[1]+30,driver[2]+17.5);b=App.Vector(*hub);v=b-a
    feature('LED_DC_Feed',Part.makeCylinder(1.8,v.Length,a,v),(0.9,0.36,0.1))
    # Drill only panels physically intersected by a cable. Preserve fabrication indices.
    drilled={}
    for label, points in routes:
        length=0
        for i,(a,b) in enumerate(zip(points,points[1:]),1):
            start,end=App.Vector(*a),App.Vector(*b); vector=end-start; distance=vector.Length
            if distance<0.01: continue
            vector.normalize(); length+=distance
            shape=Part.makeCylinder(1.5,distance,start,vector)
            o=feature('LED_Cable_'+label+'_'+str(i),shape,(0.9,0.36,0.1))
            o.addProperty('App::PropertyString','Circuit','Lighting'); o.Circuit=label+'; two-core DC sheath; + and - separate conductors; parallel feed'
            bore=Part.makeCylinder(4.5,distance+2,start-vector,vector)
            # Snapshot candidates because routing can replace a Part::Box.
            for panel in list(doc.Objects):
                if 'CutListRow' not in panel.PropertiesList or not panel.isDerivedFrom('Part::Feature'): continue
                if not panel.Shape.BoundBox.intersect(bore.BoundBox): continue
                common=panel.Shape.common(bore)
                if common.Volume<0.01:continue
                idx=panel.CutListRow
                if panel.TypeId!='Part::Feature':
                    new=doc.addObject('Part::Feature',panel.Name+'_CableDrilled');new.Shape=panel.Shape.copy()
                    new.Label=panel.Label+' (cable bore)'
                    for p in ['CutListRow','PartID']:
                        if p in panel.PropertiesList:
                            new.addProperty('App::PropertyInteger' if p=='CutListRow' else 'App::PropertyString',p,'Fabrication');setattr(new,p,getattr(panel,p))
                    new.addProperty('App::PropertyString','OriginalPart','Fabrication');new.OriginalPart=panel.Name
                    for parent in panel.InList:
                        if parent.TypeId=='App::DocumentObjectGroup':parent.addObject(new)
                    colours[new.Name]=colours.pop(panel.Name,(0.8,0.74,0.68));doc.removeObject(panel.Name);panel=new
                panel.Shape=panel.Shape.cut(bore)
                drilled.setdefault(idx,[]).append(label)
        next(s for s in specs if s['id']==label)['cable_route_mm']=round(length,1)
        next(s for s in specs if s['id']==label)['cable_allowance_mm']=round(length+200,1)
    for idx, branches in drilled.items():
        row=list(rows[idx]);row[-1]+='; 9 mm DC cable passage / grommet allowance at modelled route: '+','.join(sorted(set(branches)))+'; match actual grommet OD before drilling';rows[idx]=tuple(row)
    watts=sum(s['watts'] for s in specs)
    data={'project':project,'voltage_assumption':VOLTAGE,'watts_per_m_assumption':WATTS_PER_M,'profile_envelope_mm':[16,10],
          'total_length_m':round(sum(s['length_mm'] for s in specs)/1000,4),'load_w':round(watts,3),'load_a':round(watts/VOLTAGE,3),
          'design_margin':1.25,'minimum_capacity_with_margin_w':round(watts*1.25,3),'provisional_driver_w':30,
          'branches':specs,'drilled_cut_rows':sorted(drilled),'driver_location_mm':driver,
          'pending':['Strip voltage / W per metre / cut pitch','Actual profile and diffuser dimensions','Driver thermal / ventilation requirements','Wire gauge, fuse and connector ratings from actual cable lengths and products','Grommet OD and local mains outlet location']}
    doc.recompute()
    Path(output,project+'_lighting.json').write_text(json.dumps(data,indent=2))
    return data
