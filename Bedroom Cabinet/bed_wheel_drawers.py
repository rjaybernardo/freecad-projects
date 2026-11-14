"""Floor-running under-bed drawers. Caster hardware envelopes are provisional.

Wheel diameter is specified by the user. Overall mounting height is a separate,
editable assumption; measure the purchased hardware before releasing cutting sizes.
"""
import FreeCAD as App
import Part


class FloorDrawers:
    def __init__(self, doc, box, group, colours, thickness, wheel_diameter=25.4,
                 mounting_height=35.0, wheel_width=12.7):
        self.doc, self.box, self.group, self.colours = doc, box, group, colours
        self.t, self.diameter = thickness, wheel_diameter
        self.mount_h, self.wheel_w = mounting_height, wheel_width
        self.pad_t = thickness
        self.bottom_z = mounting_height + self.pad_t
        self.guide_gap, self.guide_t = 3.0, thickness
        self.clearance = self.guide_gap + self.guide_t
        self.groups = []

    def build(self, parent, label, inner_front, inward, across, opening_width,
              depth, front_width, front_z, front_height, body_top, travel,
              frame_colour, drawer_colour, metal_colour):
        origin = App.Vector(*inner_front)
        u, v = App.Vector(*inward), App.Vector(*across)
        moving = self.group('Drawer_Assembly_' + label, parent)
        moving.addProperty('App::PropertyVector', 'OpenDirection', 'Drawer')
        moving.OpenDirection = -u
        moving.addProperty('App::PropertyLength', 'OpenTravel', 'Drawer')
        moving.OpenTravel = travel
        moving.addProperty('App::PropertyLength', 'WheelDiameter', 'Hardware')
        moving.WheelDiameter = self.diameter
        moving.addProperty('App::PropertyLength', 'AssumedCasterHeight', 'Hardware')
        moving.AssumedCasterHeight = self.mount_h
        moving.addProperty('App::PropertyString', 'HardwareStatus', 'Hardware')
        moving.HardwareStatus = 'Provisional fixed-wheel envelope; measure actual installed height and plate before cutting'

        def panel(group, name, au, av, z, du, dv, dz, colour, note='', cut=True):
            p, q = origin + u * au + v * av, origin + u * (au + du) + v * (av + dv)
            obj = self.box(group, name, min(p.x, q.x), min(p.y, q.y), z,
                           abs(q.x-p.x), abs(q.y-p.y), dz, colour, cut=cut,
                           note=note)
            if group == moving:
                obj.addProperty('App::PropertyBool', 'MovingDrawer', 'Drawer')
                obj.MovingDrawer = True
            return obj

        bw = opening_width - 2 * self.clearance
        h = body_top - self.bottom_z
        assert h > self.t + 40
        # Front is outside the inner-front plane; a single front closes the box.
        panel(moving, 'Drawer_Front', -self.t, (opening_width-front_width)/2, front_z,
              self.t, front_width, front_height, frame_colour,
              'HPL both faces; square pull edge; edge-band exposed edges')
        for suffix, av in [('A', self.clearance), ('B', self.clearance+bw-self.t)]:
            panel(moving, 'Drawer_Side_' + suffix, 0, av, self.bottom_z,
                  depth, self.t, h, drawer_colour, 'HPL both faces; band exposed top edge')
        panel(moving, 'Drawer_Back', depth-self.t, self.clearance+self.t, self.bottom_z,
              self.t, bw-2*self.t, h, drawer_colour, 'HPL both faces; band exposed top edge')
        panel(moving, 'Drawer_Bottom', 0, self.clearance+self.t, self.bottom_z,
              depth-self.t, bw-2*self.t, self.t, drawer_colour, 'HPL both faces; floor-running drawer base')

        # Short fixed plywood guides, with a 3 mm running gap. These are not metal runners.
        for suffix, av in [('A', 0), ('B', opening_width-self.guide_t)]:
            panel(parent, 'Guide_' + label + '_' + suffix, 0, av,
                  self.bottom_z+self.t+10, 200, self.guide_t, 30, frame_colour,
                  'Plywood lateral guide; 3 mm clearance to drawer; do not fasten to moving drawer')

        for n, (au, av) in enumerate([(55, self.clearance+55), (depth-55, self.clearance+55),
                                      (55, self.clearance+bw-55), (depth-55, self.clearance+bw-55)], 1):
            panel(moving, f'Drawer_WheelPad_{n}', au-30, av-22.5, self.mount_h,
                  60, 45, self.pad_t, drawer_colour, 'Caster mounting pad; HPL both faces; verify plate and screw pattern')
            center = origin + u * au + v * av + App.Vector(0, 0, self.diameter/2)
            axle_start = center - v * (self.wheel_w/2)
            tire = Part.makeCylinder(self.diameter/2, self.wheel_w, axle_start, v)
            bore = Part.makeCylinder(2.6, self.wheel_w+2, axle_start-v, v)
            tire = tire.cut(bore)
            wheel = self.doc.addObject('Part::Feature', f'Wheel_{label}_{n}')
            wheel.Shape = tire
            moving.addObject(wheel)
            wheel.addProperty('App::PropertyBool', 'MovingDrawer', 'Drawer'); wheel.MovingDrawer=True
            wheel.addProperty('App::PropertyString', 'HardwareStatus', 'Hardware')
            wheel.HardwareStatus = '25.4 mm wheel diameter; generic envelope, not a specified supplier product'
            self.colours[wheel.Name] = (0.12, 0.12, 0.12)
            # Plate and fork cheeks remain separate from the wheel, with clearance.
            panel(moving, f'CasterPlate_{label}_{n}', au-17.5, av-15, self.mount_h-2,
                  35, 30, 2, metal_colour, cut=False)
            for side in [-1, 1]:
                cheek_v = av + (self.wheel_w/2+1 if side>0 else -self.wheel_w/2-2.5)
                cheek = panel(moving, f'CasterFork_{label}_{n}', au-9, cheek_v, self.diameter/2-5,
                              18, 1.5, self.mount_h-2-(self.diameter/2-5), metal_colour, cut=False)
                # The axle is an envelope only; fixing details depend on the purchased caster.
        self.groups.append(moving)
        return moving
