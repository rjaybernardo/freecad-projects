"""Plywood L/C grip recesses behind square-edged fronts. Dimensions in mm.

The reference's 42 mm depth and 60 mm L height are interpreted as overall
dimensions. C height is 80 mm, giving 40.8 mm internal height at T=19.6.
These are built-up plywood members, not metal extrusions.
"""
import FreeCAD as App
import Part


class PlywoodPullChannels:
    DEPTH = 42.0
    L_HEIGHT = 60.0
    C_HEIGHT = 80.0

    def __init__(self, doc, thickness, cut_list, colours, colour, closed_ends=False):
        self.doc, self.t = doc, thickness
        self.cut_list, self.colours, self.colour = cut_list, colours, colour
        self.closed_ends = closed_ends

    def _notch(self, parent, envelope, label):
        self.doc.recompute()
        objects = list(parent.OutListRecursive)
        for obj in objects:
            if not obj.isDerivedFrom('Part::Feature') or obj.Name.startswith(('Drawer', 'Door', 'Pull_', 'LED_')):
                continue
            if obj.Shape.isNull() or obj.Shape.common(envelope).Volume < 1e-6:
                continue
            shape = obj.Shape.cut(envelope).removeSplitter()
            if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
                raise ValueError(f'Invalid or disconnected recess in {obj.Name}')
            idx = obj.CutListRow if 'CutListRow' in obj.PropertiesList else None
            if idx is not None:
                row = list(self.cut_list[idx])
                row[-1] = '; '.join(filter(None, [row[-1], f'{label} plywood pull recess; see model']))
                self.cut_list[idx] = tuple(row)
            if obj.TypeId == 'Part::Feature' and 'OriginalPart' in obj.PropertiesList:
                obj.Shape = shape
                continue
            replacement = self.doc.addObject('Part::Feature', obj.Name + '_Recessed')
            replacement.Label = obj.Label + ' (recessed)'
            replacement.Shape = shape
            replacement.addProperty('App::PropertyString', 'OriginalPart', 'Fabrication')
            replacement.OriginalPart = obj.Name
            if idx is not None:
                replacement.addProperty('App::PropertyInteger', 'CutListRow', 'Fabrication')
                replacement.CutListRow = idx
            for group in list(obj.InList):
                if group.TypeId == 'App::DocumentObjectGroup':
                    group.addObject(replacement)
            self.colours[replacement.Name] = self.colours.pop(obj.Name, self.colour)
            self.doc.removeObject(obj.Name)

    def _part(self, group, name, origin, size):
        obj = self.doc.addObject('Part::Box', name)
        obj.Length, obj.Width, obj.Height = size
        obj.Placement.Base = App.Vector(*origin)
        group.addObject(obj)
        self.colours[obj.Name] = self.colour
        # Thickness is known explicitly, including narrow return strips.
        dims = list(size)
        axis = next(i for i, d in enumerate(dims) if abs(d - self.t) < 1e-6)
        dims.pop(axis)
        length, width = sorted(dims, reverse=True)
        self.cut_list.append((group.Label, name, round(length, 1), round(width, 1),
                              round(self.t, 1), 'HPL both faces; square edges; edge-band exposed edges'))
        return obj

    def horizontal(self, parent, label, x, inner_y, z0, width, facing=1, kind='L', opening='up'):
        if self.closed_ends:
            # The existing rectangular sides close the ends; no cover layer or
            # routing through the visible outside faces is needed.
            x += self.t
            width -= 2 * self.t
        height = self.C_HEIGHT if kind == 'C' else self.L_HEIGHT
        depth, t = self.DEPTH, self.t
        y0 = inner_y if facing == 1 else inner_y - depth
        # Route all the way to the carcass front, including inset-front side lips.
        route_y = y0 - t if facing == 1 else y0
        envelope = Part.makeBox(width, depth + t, height, App.Vector(x, route_y, z0))
        self._notch(parent, envelope, label)
        group = self.doc.addObject('App::DocumentObjectGroup', 'Pull_' + label)
        parent.addObject(group)
        back_y = y0 + depth - t if facing == 1 else y0
        return_y = y0 if facing == 1 else y0 + t
        self._part(group, 'Pull_' + label + '_Back', (x, back_y, z0), (width, t, height))
        if kind == 'C' or opening == 'up':
            self._part(group, 'Pull_' + label + '_Lower', (x, return_y, z0), (width, depth - t, t))
        if kind == 'C' or opening == 'down':
            self._part(group, 'Pull_' + label + '_Upper', (x, return_y, z0 + height - t), (width, depth - t, t))
        return group

    def vertical(self, parent, label, x0, inner_y, z0, height, opening='right'):
        depth, width, t = self.DEPTH, self.L_HEIGHT, self.t
        envelope = Part.makeBox(width, depth, height, App.Vector(x0, inner_y, z0))
        self._notch(parent, envelope, label)
        group = self.doc.addObject('App::DocumentObjectGroup', 'Pull_' + label)
        parent.addObject(group)
        self._part(group, 'Pull_' + label + '_Back', (x0, inner_y + depth - t, z0), (width, t, height))
        return_x = x0 if opening == 'right' else x0 + width - t
        self._part(group, 'Pull_' + label + '_Return', (return_x, inner_y, z0), (t, depth - t, height))
        return group
