"""A4 large-print cutting documents, rendered from the saved nesting data.

Run with freecadcmd, never rebuild the furniture to change print formatting.
The sheet placement, part IDs, band allowances and kerf are retained verbatim.
"""
from pathlib import Path
import html
import json
import math
import os
import sys

WIDTH, HEIGHT = 297, 210
BODY = 4.3  # mm in SVG user coordinates: 12.2 pt on an actual-size A4 print
PALETTE = ['#e4eff5', '#eee6f5', '#e8f0dd', '#f7ead4', '#dcf0e8', '#f6e3e8']


def label(svg, x, y, value, size=BODY, **attrs):
    extra = ' '.join(f'{k.replace("_", "-")}="{html.escape(str(v))}"' for k, v in attrs.items())
    svg.append(f'<text x="{x:g}" y="{y:g}" font-size="{size:g}" {extra}>{html.escape(str(value))}</text>')


def start(title, subtitle, footer):
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">',
           '<rect width="297" height="210" fill="white"/>',
           '<style>text {font-family:DejaVu Sans,sans-serif;fill:#172a38}</style>']
    label(svg, 10, 16, title, 6.2, font_weight='bold')
    label(svg, 10, 25, subtitle)
    label(svg, 10, 201, footer)
    return svg


def save(svg, path):
    path.write_text('\n'.join(svg + ['</svg>']))
    return path


def overview(path, si, sheet, panels, settings, total, project=''):
    """Use sheet-local numbers; narrow strips get external full-size callouts."""
    svg = start(f'{project.upper()} | SHEET {si:02d} / {total:02d} | CUTTING MAP',
                f'Stock {settings["StockLength"]:g} x {settings["StockWidth"]:g} mm | kerf {settings["Kerf"]:g} mm | trim {settings["Trim"]:g} mm each edge',
                'A4 landscape | Print at 100% / actual size | Revision 2026-11-17')
    label(svg, 10, 34, 'Numbers match the following parts table. Orange = edge band. Use table dimensions.')
    ox, oy = 10, 44
    scale = min(277/settings['StockLength'], 138/settings['StockWidth'])
    sw, sh = settings['StockLength']*scale, settings['StockWidth']*scale
    svg.append(f'<rect x="{ox}" y="{oy}" width="{sw}" height="{sh}" fill="#e7e7e7" stroke="#172a38" stroke-width=".4"/>')
    lookup = {p['id']: p for p in panels}
    callouts = []
    for number, p in enumerate(sheet['panels'], 1):
        x, y = ox+p['x']*scale, oy+p['y']*scale
        w, h = p['l']*scale, p['w']*scale
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PALETTE[(number-1)%len(PALETTE)]}" stroke="#52606b" stroke-width=".16"/>')
        bands = lookup[p['id']]['bands']
        if p['rotated']:
            bands = [bands[2], bands[3], bands[0], bands[1]]
        for enabled, line in zip(bands, [(x,y,x+w,y), (x,y+h,x+w,y+h), (x,y,x,y+h), (x+w,y,x+w,y+h)]):
            if enabled:
                svg.append(f'<path d="M{line[0]} {line[1]} L{line[2]} {line[3]}" stroke="#b8590e" stroke-width=".55"/>')
        # Never shrink text to squeeze it into a small part.
        min_width = 3.2 if number < 10 else 6.2
        if h >= 4.5 and w >= min_width:
            label(svg, x+w/2, y+h/2+1.5, number, text_anchor='middle', font_weight='bold')
        elif w >= 4.5 and h >= min_width:
            svg.append(f'<g transform="translate({x+w/2},{y+h/2}) rotate(-90)">')
            label(svg, 0, 1.5, number, text_anchor='middle', font_weight='bold')
            svg.append('</g>')
        else:
            callouts.append((number, x+w/2, y+h/2))
    # Distribute strip labels across the lower margin; leader lines identify them.
    for i, (number, x, y) in enumerate(sorted(callouts, key=lambda v: v[1])):
        lx = ox + sw*(i+.5)/len(callouts)
        svg.append(f'<path d="M{x} {y} L{lx} 188" fill="none" stroke="#52606b" stroke-width=".25"/>')
        svg.append(f'<rect x="{lx-4}" y="184" width="8" height="7" rx="1" fill="white" stroke="#52606b" stroke-width=".25"/>')
        label(svg, lx, 189.5, number, text_anchor='middle', font_weight='bold')
    return save(svg, path)


def table_header(svg, columns, headings):
    svg.append('<rect x="10" y="39" width="277" height="10" fill="#dce8ef"/>')
    x = 10
    for width, heading in zip(columns, headings):
        label(svg, x+1.5, 45.7, heading, font_weight='bold')
        x += width


def part_pages(folder, si, sheet, panels, settings, project):
    lookup = {p['id']: p for p in panels}
    entries = list(enumerate(sheet['panels'], 1))
    paths = []
    count = math.ceil(len(entries)/11)
    for page in range(count):
        batch = entries[page*11:(page+1)*11]
        svg = start(f'{project.upper()} | SHEET {si:02d} | PARTS {page+1} / {count}',
                    'All sizes in mm. Qty = 1 per ID. Cut BLANK size; finished size includes edge band.',
                    'A4 landscape | 12 pt tables | Print at 100% / actual size | 2026-11-17')
        label(svg, 10, 34, 'Material: 19.6 mm laminated plywood = assumed 18 mm core + 0.8 mm each face.')
        columns = [12, 22, 96, 43, 43, 61]
        table_header(svg, columns, ['No.', 'ID', 'Part / module', 'BLANK L x W', 'Finished L x W', 'Band edges'])
        for row, (number, placed) in enumerate(batch):
            p = lookup[placed['id']]
            y = 49+row*12
            svg.append(f'<rect x="10" y="{y}" width="277" height="12" fill="{"#f1f5f7" if row%2==0 else "white"}"/>')
            values = [number, p['id'], p['part'].replace('_', ' '),
                      f'{p["blank_l"]:g} x {p["blank_w"]:g}',
                      f'{p["finished_l"]:g} x {p["finished_w"]:g}',
                      ' '.join(n for n,b in zip(['L1','L2','W1','W2'],p['bands']) if b) or 'None']
            if 'WheelPad' in p['part']:
                values[2] = p['part'].replace('_', ' ')+' [HOLD]'
            x = 10
            for width, value in zip(columns, values):
                label(svg, x+1.5, y+5, value, font_weight='bold' if x in [22,140] else 'normal')
                x += width
            label(svg, 45.5, y+10.3, p['module'].replace('_',' '))
        label(svg, 10, 187, f'Edge band: {settings["EdgeBand"]:g} mm thick. L1/L2 parallel to Length; W1/W2 parallel to Width.')
        label(svg, 10, 194, 'Wheels mount directly under drawer bottoms. Verify actual bracket height and fixings.' if project=='bed' else 'Measure actual board and hardware before cutting. Full notes remain in CutSchedule.csv.')
        paths.append(save(svg, folder/f'Sheet_{si:02d}_Parts_{page+1:02d}.svg'))
    return paths


def cut_pages(folder, si, sheet, settings, project):
    paths = []
    count = math.ceil(len(sheet['cuts'])/16)
    for page in range(count):
        svg = start(f'{project.upper()} | SHEET {si:02d} | SAW STEPS {page+1} / {count}',
                    f'Trim {settings["Trim"]:g} mm each edge first. Kerf = {settings["Kerf"]:g} mm; consumes positive X / Y after coordinate.',
                    'A4 landscape | 12 pt tables | Follow steps in order | 2026-11-17')
        label(svg, 10, 34, 'Coordinates from original stock origin. X along stock length; Y along stock width. All in mm.')
        table_header(svg, [15,15,35,35,25,152], ['Step','Axis','Coordinate','Cut span','Target','Parent region: X / Y / length / width'])
        for row, c in enumerate(sheet['cuts'][page*16:(page+1)*16]):
            y = 49+row*8.5
            svg.append(f'<rect x="10" y="{y}" width="277" height="8.5" fill="{"#f1f5f7" if row%2==0 else "white"}"/>')
            values = [page*16+row+1, c['axis'], f'{c["at"]:g}', f'{c["span"]:g}', c['panel'], ' / '.join(f'{v:g}' for v in c['region'])]
            x = 10
            for width, value in zip([15,15,35,35,25,152], values):
                label(svg, x+1.5, y+5.7, value)
                x += width
        label(svg, 10, 193, 'Label each panel with its target ID immediately. See SawCuts.csv for parent-region names.')
        paths.append(save(svg, folder/f'Sheet_{si:02d}_Saw_{page+1:02d}.svg'))
    return paths


def sheet_pack(folder, si, sheet, panels, settings, total, project):
    return ([overview(folder/f'Sheet_{si:02d}.svg', si, sheet, panels, settings, total, project)]
            + part_pages(folder, si, sheet, panels, settings, project)
            + cut_pages(folder, si, sheet, settings, project))


def export_pdf(paths, pdf, preview_stems=()):
    from PySide import QtCore, QtGui, QtSvg
    writer = QtGui.QPdfWriter(str(pdf))
    writer.setResolution(300)
    writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
    writer.setPageOrientation(QtGui.QPageLayout.Landscape)
    writer.setPageMargins(QtCore.QMarginsF(0,0,0,0))
    painter = QtGui.QPainter(writer)
    if not painter.isActive():
        raise RuntimeError(f'Cannot write {pdf}')
    for i, path in enumerate(paths):
        if i:
            writer.newPage()
        renderer = QtSvg.QSvgRenderer(str(path))
        assert renderer.isValid(), path
        renderer.render(painter, QtCore.QRectF(0,0,writer.width(),writer.height()))
        if path.stem in preview_stems:
            image = QtGui.QImage(1782,1260,QtGui.QImage.Format_ARGB32)
            image.fill(QtCore.Qt.white)
            ip = QtGui.QPainter(image)
            renderer.render(ip)
            ip.end()
            assert image.save(str(path.with_suffix('.png')))
    painter.end()


def main():
    import FreeCAD as App
    from PySide import QtGui
    from workshop_documents import native_page
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])
    project_root = Path(__file__).resolve().parent
    report = {}
    for project in ['bed','cabinet']:
        folder = project_root/'workshop'/project
        data = json.loads((folder/'layout.json').read_text())
        # Never open or save the furniture models. Make a standalone page document.
        doc = App.newDocument(project.title()+'_Readable_Cutting')
        group = doc.addObject('App::DocumentObjectGroup','Workshop_Documents')
        paths = []
        for si, sheet in enumerate(data['sheets'], 1):
            paths += sheet_pack(folder, si, sheet, data['panels'], data['settings'], len(data['sheets']), project)
        for i, path in enumerate(paths, 1):
            native_page(doc, group, path, f'Cutting_{i:03d}')
        doc.recompute()
        doc.saveAs(str(folder/'Readable_Cutting.FCStd'))
        App.closeDocument(doc.Name)
        export_pdf(paths, folder/'Cutting_Layouts.pdf', ['Sheet_01','Sheet_01_Parts_01','Sheet_10','Sheet_10_Parts_01'])
        report[project] = {'pages':len(paths), 'sheets':len(data['sheets']), 'panels':len(data['panels']), 'minimum_font_mm':BODY,
                           'source':'layout.json (unchanged)', 'native_document':'Readable_Cutting.FCStd',
                           'wheel_pad_status':'removed; wheels mount directly under drawer bottoms' if project=='bed' else 'not applicable'}
    (project_root/'workshop/readability-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
