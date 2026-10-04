#!/usr/bin/env python3
"""Render compact technical roadmaps as editable SVG (Python 3 + Pillow)."""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from PIL import ImageFont


PALETTES = {
    'reference': ('#FFEBB4', '#000000', '#000000'),
    'monochrome': ('#FFFFFF', '#000000', '#000000'),
    'blue': ('#E7EEF5', '#000000', '#000000'),
    'teal': ('#E5F0ED', '#000000', '#000000'),
    'purple': ('#EEEAF4', '#000000', '#000000'),
    'warm': ('#F4EBDF', '#000000', '#000000'),
}
COLOR_ROLES = ('title_fill', 'outer_frame', 'inner_frame', 'node_fill', 'text', 'line')


def contrast(a, b):
    def luminance(color):
        rgb = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
        linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        return sum(c*w for c, w in zip(linear, (.2126, .7152, .0722)))
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high+.05)/(low+.05)


def colors_for(scheme, overrides):
    title, outer, inner = PALETTES[scheme]
    colors = dict(zip(COLOR_ROLES, (title, outer, inner, '#FFFFFF', '#000000', '#000000')))
    if not isinstance(overrides, dict) or set(overrides)-set(COLOR_ROLES):
        raise ValueError('colors accepts only '+', '.join(COLOR_ROLES)+'.')
    for role, color in overrides.items():
        if not isinstance(color, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', color):
            raise ValueError('Every color override must use #RRGGBB: '+role)
        colors[role] = color.upper()
    for role in ('outer_frame', 'inner_frame', 'line'):
        if colors[role] != '#000000':
            raise ValueError(role+' must be #000000. All frames and connectors use black; customize fills instead.')
    for role in ('title_fill', 'node_fill'):
        if contrast(colors['text'], colors[role]) < 4.5:
            raise ValueError('Text contrast is below 4.5:1 against '+role+'. Choose a clearer text/background pair.')
    for role in ('outer_frame', 'inner_frame', 'line'):
        if contrast(colors[role], '#FFFFFF') < 3:
            raise ValueError('Line/frame contrast is below 3:1 on white: '+role)
    if contrast(colors['line'], colors['node_fill']) < 3 or contrast(colors['line'], colors['title_fill']) < 3:
        raise ValueError('line must contrast at least 3:1 with node_fill and title_fill.')
    return colors


def num(value):
    return f'{value:.6f}'.rstrip('0').rstrip('.')


def center(node):
    return node['x'] + node['w'] / 2


def bottom(node):
    return node['y'] + node['h']


class Roadmap:
    def __init__(self, font_size, chinese_font, latin_font, colors, layout='compact'):
        self.size = font_size
        self.song = ImageFont.truetype(str(chinese_font), font_size)
        self.times = ImageFont.truetype(str(latin_font), font_size)
        if self.song.getname()[0].replace(' ', '').lower() not in ('simsun', '宋体', '中易宋体'):
            raise ValueError('Chinese font must be SimSun (宋体).')
        if self.times.getname()[0].replace(' ', '').lower() != 'timesnewroman':
            raise ValueError('Latin font must be Times New Roman.')
        self.scale = font_size / 22
        self.yellow, self.red, self.blue = (colors[k] for k in COLOR_ROLES[:3])
        self.node_fill, self.text_color, self.line_color = (colors[k] for k in COLOR_ROLES[3:])
        self.proposal = layout == 'proposal'
        self.parts, self.counts = [], {}

    def u(self, value):
        return value * self.scale

    def runs(self, text):
        return [(s, self.times if s.isascii() else self.song,
                 'Times New Roman' if s.isascii() else 'SimSun')
                for s in re.findall(r'[\x20-\x7e]+|[^\x20-\x7e]+', text)]

    def measure(self, text):
        return sum(font.getlength(run) for run, font, _ in self.runs(text))

    def node_size(self, text):
        lines = text.split('\n')
        return max(self.measure(s) for s in lines) + self.u(12), len(lines) * self.size * 1.16 + self.u(8)

    def place(self, text, mid, y, fill=None):
        w, h = self.node_size(text)
        return dict(text=text, x=mid-w/2, y=y, w=w, h=h, fill=fill or self.node_fill)

    def layout(self, graph):
        specs = []
        for index, stage in enumerate(graph['stages']):
            split = index == len(graph['stages']) - 1
            horizontal = split or self.proposal
            gap = self.u((32 if len(stage['groups']) == 4 else 38) if split else 10)
            groups = []
            for group in stage['groups']:
                rows = [r if isinstance(r, list) else [r] for r in group['rows']]
                rh = [max(self.node_size(n)[1] for n in row) for row in rows]
                rw = [sum(self.node_size(n)[0] for n in row) + self.u(26)*(len(row)-1) for row in rows]
                stack_h = sum(rh) + self.u(8)*(len(rows)-1)
                label_h = len(group['label'])*self.u(24.3) + self.u(8)
                pw = max(rw) + self.u(12 if horizontal else 46)
                ph = max(stack_h+self.u(12), 0 if horizontal else label_h+self.u(8))
                hw, hh = self.node_size(group['label'])
                groups.append(dict(label=group['label'], rows=rows, chain=group.get('chain', False),
                                   rh=rh, rw=rw, stack_h=stack_h, label_h=label_h, pw=pw, ph=ph,
                                   w=max(pw+self.u(12), hw+self.u(12)) if horizontal else pw,
                                   h=self.u(18)+hh+ph if horizontal else ph))
            row_w = sum(p['w'] for p in groups) + gap*(len(groups)-1)
            hw, hh = self.node_size(stage['label'])
            specs.append(dict(label=stage['label'], split=split, gap=gap, groups=groups, row_w=row_w,
                              w=row_w if split and not self.proposal else max(row_w+self.u(12), hw+self.u(12)),
                              h=(0 if split and not self.proposal else self.u(19)+hh) + max(p['h'] for p in groups)))
        iw = max(sum(self.node_size(n)[0] for n in graph['inputs']) + self.u(26)*(len(graph['inputs'])-1),
                 self.node_size(graph['inputLabel'])[0]) + self.u(12)
        ow = sum(self.node_size(n)[0] for n in graph.get('outputs', [])) + self.u(22)*max(0, len(graph.get('outputs', []))-1)
        fw, _ = self.node_size(graph['final'])
        width = math.ceil(max(iw, ow, fw, *[s['w'] for s in specs])+self.u(24))
        inputs = dict(x=(width-iw)/2, y=self.u(12), w=iw)
        inputs['header'] = self.place(graph['inputLabel'], width/2, inputs['y']+self.u(5), self.yellow)
        ix, iy = inputs['x']+self.u(6), bottom(inputs['header'])+self.u(8)
        inputs['nodes'] = []
        for text in graph['inputs']:
            nw, _ = self.node_size(text)
            inputs['nodes'].append(self.place(text, ix+nw/2, iy))
            ix += nw+self.u(26)
        inputs['h'] = max(bottom(n) for n in inputs['nodes'])-inputs['y']+self.u(6)
        y, stages = bottom(inputs)+self.u(14), []
        for spec in specs:
            stage = dict(x=(width-spec['w'])/2, y=y, w=spec['w'], h=spec['h'], split=spec['split'], groups=[])
            if not stage['split'] or self.proposal:
                stage['header'] = self.place(spec['label'], width/2, y+self.u(5), self.yellow)
            gx = (width-spec['row_w'])/2
            gy = bottom(stage['header'])+self.u(8) if 'header' in stage else y
            for q in spec['groups']:
                horizontal = stage['split'] or self.proposal
                group = dict(x=gx+(q['w']-q['pw'])/2 if horizontal else gx, y=gy,
                             w=q['pw'], h=q['ph'], label=q['label'], chain=q['chain'], rows=[])
                if horizontal:
                    group['slot'] = dict(x=gx, y=gy, w=q['w'], h=q['h'])
                    if stage['split'] and not self.proposal:
                        group['outer'] = group['slot']
                    group['header'] = self.place(q['label'], gx+q['w']/2, gy+self.u(4), self.yellow)
                    group['y'] = bottom(group['header'])+self.u(8)
                group['flow_x'] = group['x'] + (group['w']/2 if horizontal else (group['w']+self.u(34))/2)
                ry = group['y']+(group['h']-q['stack_h'])/2
                for j, row in enumerate(q['rows']):
                    nx, placed = group['flow_x']-q['rw'][j]/2, []
                    for text in row:
                        nw, nh = self.node_size(text)
                        placed.append(self.place(text, nx+nw/2, ry+(q['rh'][j]-nh)/2))
                        nx += nw+self.u(26)
                    group['rows'].append(placed)
                    ry += q['rh'][j]+self.u(8)
                if not horizontal:
                    group['strip'] = dict(text=q['label'], x=group['x']+self.u(6), y=group['y']+(group['h']-q['label_h'])/2,
                                          w=self.u(28), h=q['label_h'], fill=self.yellow)
                group['top'] = group['header']['y'] if horizontal else group['y']
                group['bottom'] = bottom(group['outer']) if 'outer' in group else bottom(group)
                stage['groups'].append(group)
                gx += q['w']+spec['gap']
            stages.append(stage)
            y += stage['h']+self.u(14)
        final = self.place(graph['final'], width/2, y+self.u(8), self.yellow)
        y, outputs = bottom(final), []
        if graph.get('outputs'):
            y += self.u(24)
            x = (width-ow)/2
            for text in graph['outputs']:
                nw, _ = self.node_size(text)
                outputs.append(self.place(text, x+nw/2, y))
                x += nw+self.u(22)
            y = max(bottom(n) for n in outputs)
        return dict(W=width, H=math.ceil(y+self.u(12)), inputs=inputs, stages=stages, final=final, outputs=outputs)

    def ident(self, kind):
        self.counts[kind] = self.counts.get(kind, 0)+1
        return f'{kind}-{self.counts[kind]:03d}'

    def group(self, kind, body, label=''):
        self.parts.append(f'<g id="{self.ident(kind)}" data-object-type="{kind}" aria-label={quoteattr(label)}>{body}</g>')

    def rect(self, r, fill='#FFFFFF', stroke=None, width=1.25, dash=''):
        stroke = stroke or self.line_color
        return (f'<rect id="{self.ident("rectangle")}" x="{num(r["x"])}" y="{num(r["y"])}" width="{num(r["w"])}" height="{num(r["h"])}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{num(self.u(width))}" stroke-linecap="{"round" if dash else "butt"}" stroke-linejoin="miter"'
                + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')

    def boundary(self, rect, outer):
        dash = ' '.join(num(self.u(n)) for n in ((12, 6) if outer else (5, 3)))
        self.group('module-frame' if outer else 'submodule-frame', self.rect(rect, 'none', self.red if outer else self.blue, 2 if outer else 1.65, dash))

    def line(self, points, arrow=False):
        d = ' '.join(('M' if i == 0 else 'L')+num(x)+' '+num(y) for i, (x, y) in enumerate(points))
        body = f'<path id="{self.ident("line")}" d="{d}" fill="none" stroke="{self.line_color}" stroke-width="{num(self.u(1.25))}" stroke-linejoin="miter" stroke-linecap="butt"/>'
        if arrow:
            x, y = points[-1]
            px, py = points[-2]
            a, z, k = math.atan2(y-py, x-px), self.u(6), self.u(3)
            vertices = [(x, y), (x-z*math.cos(a)+k*math.sin(a), y-z*math.sin(a)-k*math.cos(a)),
                        (x-z*math.cos(a)-k*math.sin(a), y-z*math.sin(a)+k*math.cos(a))]
            pairs = ' '.join(num(x)+','+num(y) for x, y in vertices)
            body += f'<polygon id="{self.ident("arrowhead")}" points="{pairs}" fill="{self.line_color}" stroke="none"/>'
        self.group('connector', body)

    def fan(self, before, after):
        y = (max(bottom(n) for n in before)+min(n['y'] for n in after))/2
        for n in before:
            self.line([(center(n), bottom(n)), (center(n), y)])
        xs = [center(n) for n in before+after]
        if max(xs) > min(xs):
            self.line([(min(xs), y), (max(xs), y)])
        for n in after:
            self.line([(center(n), y), (center(n), n['y'])], True)

    def enter(self, x, y, group, stage):
        header, upper = stage.get('header'), stage['y']-self.u(6)
        fx = group['flow_x']
        if header and header['x']-self.u(7) <= fx <= header['x']+header['w']+self.u(7):
            rx = header['x']-self.u(8) if fx < center(header) else header['x']+header['w']+self.u(8)
            turn = group['top']-self.u(6)
            points = [(x, y), (x, upper), (rx, upper), (rx, turn), (fx, turn), (fx, group['top'])]
        else:
            points = [(x, y), (x, upper), (fx, upper), (fx, group['top'])]
        self.line(points, True)

    def text_line(self, text, mid, top):
        runs = self.runs(text)
        x, asc, desc = mid-self.measure(text)/2, 0, 0
        for run, font, _ in runs:
            _, y0, _, y1 = font.getbbox(run, anchor='ls')
            asc, desc = max(asc, -y0), max(desc, y1)
        y = top+(self.size*1.16-asc-desc)/2+asc
        spans = []
        for run, font, family in runs:
            spans.append(f'<tspan id="{self.ident("text-run")}" x="{num(x)}" y="{num(y)}" font-family="{family}" font-size="{self.size}" fill="{self.text_color}" '
                         f'style="font-family:\'{family}\';font-size:{self.size}px;font-weight:normal;font-style:normal">{escape(run)}</tspan>')
            x += font.getlength(run)
        return ''.join(spans)

    def box(self, node, vertical=False):
        lines = list(node['text']) if vertical else node['text'].split('\n')
        line_h = self.u(24.3) if vertical else self.size*1.16
        body = ''.join(self.text_line(s, center(node), node['y']+self.u(4)+i*line_h) for i, s in enumerate(lines))
        body = (self.rect(node, node['fill']) + f'<text id="{self.ident("text")}" xml:space="preserve" font-family="SimSun" font-size="{self.size}" '
                f'font-weight="normal" font-style="normal" fill="{self.text_color}">{body}</text>')
        self.group('text-box', body, node['text'].replace('\n', ' / '))

    def plus(self, x, y, size, color):
        k, r = size*.23/2, size/2
        pts = [(-k,-r),(k,-r),(k,-k),(r,-k),(r,k),(k,k),(k,r),(-k,r),(-k,k),(-r,k),(-r,-k),(-k,-k)]
        d = ' '.join(('M' if i == 0 else 'L')+num(x+px)+' '+num(y+py) for i, (px, py) in enumerate(pts))+' Z'
        self.group('plus', f'<path id="{self.ident("plus-shape")}" d="{d}" fill="{color}" stroke="none"/>')

    def render(self, graph):
        self.parts, self.counts = [], {}
        l = self.layout(graph)
        self.boundary(l['inputs'], True)
        for stage in l['stages']:
            if not stage['split'] or self.proposal:
                self.boundary(stage, True)
            for group in stage['groups']:
                if 'outer' in group:
                    self.boundary(group['outer'], True)
                self.boundary(group, False)
        first = l['stages'][0]
        bus_y = (bottom(l['inputs'])+first['y'])/2
        xs = [center(n) for n in l['inputs']['nodes']]+[g['flow_x'] for g in first['groups']]
        for node in l['inputs']['nodes']:
            self.line([(center(node), bottom(node)), (center(node), bus_y)])
        self.line([(min(xs), bus_y), (max(xs), bus_y)])
        for group in first['groups']:
            self.enter(group['flow_x'], bus_y, group, first)
        for before, after in zip(l['stages'], l['stages'][1:]):
            for a, b in zip(before['groups'], after['groups']):
                self.enter(a['flow_x'], a['bottom'], b, after)
        for stage in l['stages']:
            for group in stage['groups']:
                if 'header' in group:
                    self.fan([group['header']], group['rows'][0])
                if group['chain']:
                    for before, after in zip(group['rows'], group['rows'][1:]):
                        self.fan(before, after)
        last, merge = l['stages'][-1]['groups'], l['final']['y']-self.u(12)
        for group in last:
            self.line([(group['flow_x'], group['bottom']), (group['flow_x'], merge)])
        self.line([(min(g['flow_x'] for g in last), merge), (max(g['flow_x'] for g in last), merge)])
        self.line([(center(l['final']), merge), (center(l['final']), l['final']['y'])], True)
        if l['outputs']:
            self.fan([l['final']], l['outputs'])
        nodes = [l['inputs']['header']]+l['inputs']['nodes']
        for stage in l['stages']:
            if 'header' in stage:
                nodes.append(stage['header'])
            for group in stage['groups']:
                if 'header' in group:
                    nodes.append(group['header'])
                if 'strip' in group:
                    self.box(group['strip'], True)
                nodes += [n for row in group['rows'] for n in row]
        nodes += [l['final']]+l['outputs']
        for node in nodes:
            if node['x'] < 0 or node['y'] < 0 or node['x']+node['w'] > l['W'] or bottom(node) > l['H']:
                raise ValueError('A text box falls outside the canvas.')
            self.box(node)
        for a, b in zip(l['inputs']['nodes'], l['inputs']['nodes'][1:]):
            self.plus((a['x']+a['w']+b['x'])/2, a['y']+a['h']/2, self.u(18), self.blue)
        for stage in l['stages']:
            if stage['split']:
                for a, b in zip(stage['groups'], stage['groups'][1:]):
                    self.plus((a['slot']['x']+a['slot']['w']+b['slot']['x'])/2, stage['y']+stage['h']/2,
                              self.u(24 if len(stage['groups']) == 4 else 30), self.red)
            for group in stage['groups']:
                for row in group['rows']:
                    for a, b in zip(row, row[1:]):
                        self.plus((a['x']+a['w']+b['x'])/2, a['y']+a['h']/2, self.u(20), self.blue)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{l["W"]}px" height="{l["H"]}px" viewBox="0 0 {l["W"]} {l["H"]}" version="1.1">\n'
                '<metadata>Editable native vectors. Chinese: SimSun; Latin: Times New Roman. All text uses one font size. One text object per box.</metadata>\n'
                +'\n'.join(self.parts)+'\n</svg>\n')


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get('diagrams'), list) or not data['diagrams']:
        raise ValueError('Input requires a nonempty diagrams array.')
    ids = set()
    def words(value):
        if not isinstance(value, str) or not value.strip() or any(not line.strip() for line in value.split('\n')):
            raise ValueError('Labels/nodes must be nonempty strings without blank lines.')
        if any(ord(c) < 32 and c != '\n' for c in value):
            raise ValueError('Only newline is permitted as a control character.')
    for graph in data['diagrams']:
        name = graph.get('id', '')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', name) or name in ids:
            raise ValueError('Each diagram needs a unique filename-safe id.')
        ids.add(name)
        for key in ('inputLabel', 'final'):
            words(graph.get(key))
        for key in ('inputs', 'outputs'):
            if key == 'outputs' and key not in graph:
                continue
            if not isinstance(graph.get(key), list) or not graph[key]:
                raise ValueError(key+' must be a nonempty array.')
            for word in graph[key]:
                words(word)
        if not isinstance(graph.get('stages'), list) or not graph['stages']:
            raise ValueError('Each diagram requires nonempty stages.')
        count = None
        for stage in graph['stages']:
            words(stage.get('label'))
            groups = stage.get('groups')
            if not isinstance(groups, list) or not groups or (count is not None and len(groups) != count):
                raise ValueError('Stage groups must be nonempty and keep the same branch count/order.')
            count = len(groups)
            for group in groups:
                words(group.get('label'))
                if '\n' in group['label']:
                    raise ValueError('Group labels must be one line.')
                if not isinstance(group.get('chain', False), bool):
                    raise ValueError('chain must be true or false.')
                if not isinstance(group.get('rows'), list) or not group['rows']:
                    raise ValueError('Each group needs nonempty rows.')
                for row in group['rows']:
                    cells = row if isinstance(row, list) else [row]
                    if not cells:
                        raise ValueError('Rows may not be empty.')
                    for word in cells:
                        words(word)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='UTF-8 roadmap JSON')
    parser.add_argument('--output', '--output-dir', dest='output_dir', required=True, type=Path, help='Directory for editable SVG files')
    parser.add_argument('--chinese-font', type=Path, help='SimSun font file (.ttc/.ttf)')
    parser.add_argument('--latin-font', type=Path, help='Times New Roman font file (.ttf)')
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding='utf-8-sig'))
        validate(data)
        style = data.get('style', {})
        if not isinstance(style, dict) or set(style)-{'font_size', 'color_scheme', 'colors', 'layout'}:
            raise ValueError('style accepts only font_size, color_scheme, colors and layout.')
        size, scheme = style.get('font_size', 22), style.get('color_scheme', 'reference')
        layout = style.get('layout', 'compact')
        if isinstance(size, bool) or not isinstance(size, int) or not 10 <= size <= 48 or scheme not in PALETTES or layout not in ('compact', 'proposal'):
            raise ValueError('font_size must be an integer 10–48; color_scheme: '+', '.join(PALETTES)+'; layout: compact or proposal.')
        colors = colors_for(scheme, style.get('colors', {}))
        font_dir = Path(os.environ.get('WINDIR', ''))/'Fonts'
        song, times = args.chinese_font or font_dir/'simsun.ttc', args.latin_font or font_dir/'times.ttf'
        if not song.is_file() or not times.is_file():
            raise ValueError('Required fonts are missing. Supply --chinese-font (SimSun) and --latin-font (Times New Roman); no substitute is used.')
        renderer = Roadmap(size, song, times, colors, layout)
        rendered = [(graph['id'], renderer.render(graph)) for graph in data['diagrams']]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, svg in rendered:
            target = args.output_dir/(name+'.svg')
            target.write_text(svg, encoding='utf-8')
            print(target)
        return 0
    except (ValueError, OSError, TypeError, KeyError) as e:
        parser.error(str(e))


if __name__ == '__main__':
    sys.exit(main())
