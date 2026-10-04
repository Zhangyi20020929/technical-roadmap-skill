#!/usr/bin/env python3
"""Check editable roadmap SVG structure; optionally ungroup or compare renders."""
import argparse
import json
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

NS = {'s': 'http://www.w3.org/2000/svg'}
ET.register_namespace('', NS['s'])


def inspect_svg(filename, ungrouped_dir=None):
    tree = ET.parse(filename)
    root = tree.getroot()
    errors = []
    if root.tag != '{' + NS['s'] + '}svg':
        errors.append('Root is not SVG.')
    if not all(k in root.attrib for k in ('width', 'height', 'viewBox')):
        errors.append('Explicit width, height and viewBox are required.')
    ids = [e.attrib['id'] for e in root.iter() if 'id' in e.attrib]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate IDs.')
    for tag in ('image', 'use', 'script', 'foreignObject'):
        if root.findall('.//s:' + tag, NS):
            errors.append('Unsupported editable-roadmap element: ' + tag)
    groups = root.findall('.//s:g', NS)
    if not groups:
        errors.append('No independent object groups.')
    for g in groups:
        if not g.get('id'):
            errors.append('Object group is missing an ID.')
        if any(k in g.attrib for k in ('transform', 'style', 'fill', 'stroke')):
            errors.append('Parent group has inherited styles or transforms: ' + g.get('id', '?'))
    texts = root.findall('.//s:text', NS)
    boxes = [g for g in groups if g.get('data-object-type') == 'text-box']
    if not boxes:
        errors.append('No text-box objects found.')
    if len(texts) != len(boxes):
        errors.append('Each text must belong to exactly one text-box object.')
    sizes = set()
    for g in boxes:
        label = g.get('id', '?')
        if len(g.findall('s:text', NS)) != 1 or len(g.findall('s:rect', NS)) != 1:
            errors.append('Expected one rectangle and one complete text: ' + label)
            continue
        t = g.find('s:text', NS)
        if not t.get('font-size'):
            errors.append('Text missing font size: ' + label)
        else:
            sizes.add(t.get('font-size'))
        if not t.get('font-family') or not t.get('fill'):
            errors.append('Text missing explicit font or fill: ' + label)
        spans = t.findall('.//s:tspan', NS)
        if not spans:
            errors.append('Text should use positioned tspans: ' + label)
        for span in spans:
            s = span.text or ''
            family = span.get('font-family', '')
            if not family or not all(k in span.attrib for k in ('x', 'y')):
                errors.append('Tspan lacks explicit font/position: ' + label)
            expected = 'Times New Roman' if s and all(32 <= ord(c) <= 126 for c in s) else 'SimSun'
            if family != expected:
                errors.append('Unexpected font for run in ' + label + ': ' + family)
            m = re.search(r'font-size\s*:\s*([\d.]+)px', span.get('style', ''))
            if not m or m.group(1) != t.get('font-size'):
                errors.append('Tspan font size differs from its complete text: ' + label)
    if len(sizes) > 1:
        errors.append('Text sizes are not uniform: ' + ', '.join(sorted(sizes)))
    if errors:
        return {'file': filename.name, 'passed': False, 'errors': errors}
    if ungrouped_dir:
        ungrouped_dir.mkdir(parents=True, exist_ok=True)
        # All groups have only IDs/labels; lifting children preserves coordinates,
        # style and painter order. No transform or inheritance is lost.
        def lift(parent):
            for element in list(parent):
                lift(element)
                if element.tag == '{' + NS['s'] + '}g':
                    idx = list(parent).index(element)
                    children = list(element)
                    parent.remove(element)
                    for i, child in enumerate(children):
                        parent.insert(idx + i, child)
        lift(root)
        tree.write(ungrouped_dir / filename.name, encoding='utf-8', xml_declaration=True)
    return {'file': filename.name, 'passed': True, 'text_boxes': len(boxes),
            'objects': len(groups), 'font_sizes': sorted(sizes), 'raster_images': 0,
            'visual_comparison': 'not performed by structural inspection'}


def compare_images(a, b):
    from PIL import Image, ImageChops
    with Image.open(a) as ia, Image.open(b) as ib:
        ia, ib = ia.convert('RGBA'), ib.convert('RGBA')
        if ia.size != ib.size:
            return {'passed': False, 'reason': 'Image dimensions differ.'}
        difference = ImageChops.difference(ia, ib)
        changed = sum(any(channel != 0 for channel in px) for px in difference.getdata())
        return {'passed': changed == 0, 'changed_pixels': changed,
                'width': ia.width, 'height': ia.height}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path, help='SVG file or delivery directory')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--ungrouped-dir', type=Path)
    parser.add_argument('--compare', nargs=2, type=Path, metavar=('BEFORE', 'AFTER'))
    args = parser.parse_args()
    if args.compare:
        try:
            report = compare_images(*args.compare)
        except ImportError:
            parser.error('Pixel comparison requires Pillow in the current Python environment.')
        result = [report]
    else:
        if not args.source:
            parser.error('Provide an SVG file/directory or --compare.')
        files = sorted(args.source.glob('*.svg')) if args.source.is_dir() else [args.source]
        if not files or not all(f.is_file() for f in files):
            parser.error('No SVG files found.')
        result = []
        for f in files:
            try:
                result.append(inspect_svg(f, args.ungrouped_dir))
            except (ET.ParseError, ValueError, OSError) as e:
                result.append({'file': f.name, 'passed': False, 'errors': [str(e)]})
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + '\n', encoding='utf-8')
    return 0 if all(r['passed'] for r in result) else 1


if __name__ == '__main__':
    sys.exit(main())
