#!/usr/bin/env python3
"""Check the exported site's links, metadata, and publication boundary."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from atlas import inside
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
BASE = '/the-neverlands/'


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.lang = None
        self.title = False
        self.main = False
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, f'Duplicate id: {a["id"]}'
            self.ids.add(a['id'])
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'title': self.title = True
        if tag == 'main': self.main = True
        if tag == 'h1': self.h1_count += 1
        if tag == 'img': assert 'alt' in a, 'Image needs alt attribute'
        for key in ('href', 'src', 'action'):
            if a.get(key): self.links.append(a[key])


def main():
    global BASE
    index = OUT / 'index.html'
    assert index.exists(), 'Run scripts/build.py first'
    BASE = re.search(r'<body data-base="([^"]+)"',index.read_text()).group(1)
    pages = {}
    for f in OUT.rglob('*.html'):
        p = Page()
        p.feed(f.read_text())
        assert p.lang == 'th' and p.title and p.main and p.h1_count == 1, f'Invalid page structure: {f}'
        pages[f] = p
    count = 0
    for f,p in pages.items():
        for link in p.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc: continue
            if parsed.path:
                assert parsed.path.startswith(BASE), f'Incorrect project base path in {f}: {link}'
                relative = unquote(parsed.path[len(BASE):])
                target = OUT / relative
                if target.is_dir(): target /= 'index.html'
                assert target.exists(), f'Broken link in {f}: {link}'
            else:
                target = f
            if parsed.fragment and target in pages:
                assert unquote(parsed.fragment) in pages[target].ids, f'Broken fragment in {f}: {link}'
            count += 1
    # Editorial exclusion rules stay local: publishing the rules themselves
    # could expose the very information they are intended to protect.
    policy = ROOT / '.publication-policy.json'
    forbidden = json.loads(policy.read_text())['forbidden'] if policy.exists() else []
    files = list((ROOT/'content').glob('*.json')) + [f for f in OUT.rglob('*') if f.suffix in ('.html','.json','.js','.css','.xml','.txt','.svg')]
    for f in files:
        text = f.read_text()
        for term in forbidden:
            assert not re.search(term,text,re.IGNORECASE), f'Author-only content in public output: {f.name} ({term})'
    assert not list(OUT.rglob('*.md')), 'Author documents must not enter the export'
    content = json.loads((ROOT/'content/wiki.json').read_text())
    assert all(a['visibility'] == 'public' for a in content['articles'])
    assert all(f.relative_to(OUT).parts[0] in {
        'index.html','404.html','wiki','categories','search','assets',
        'search-index.json','sitemap.xml','robots.txt','.nojekyll'
    } for f in OUT.rglob('*')), 'Unexpected file in the website export'
    articles = json.loads((OUT/'search-index.json').read_text())
    assert len(articles) == len(content['articles'])
    atlas=json.loads((ROOT/'content/atlas.json').read_text())
    assert atlas['visibility']=='public' and atlas['status']=='proposed'
    kingdoms={k['id']:k for k in atlas['kingdoms']}
    assert len(kingdoms)==7
    place_ids={p['id'] for p in atlas['places']}
    assert len(place_ids)==len(atlas['places'])==35, 'Expected 35 unique places'
    for p in atlas['places']:
        assert p['visibility']=='public' and p['status']=='proposed'
        assert p['kingdom'] in kingdoms and inside(p['point'],kingdoms[p['kingdom']]['polygon']), f'Place outside its region: {p["id"]}'
        assert any(inside(p['point'],poly) for poly in [atlas['mainland']]+atlas['islands']), f'Landmark in water: {p["id"]}'
    for k in kingdoms:
        assert sum(p['kingdom']==k for p in atlas['places'])==5
    for x in range(307,1260,13):
        for y in range(67,930,13):
            if inside((x,y),atlas['mainland']):
                assert sum(inside((x,y),k['polygon']) for k in kingdoms.values())==1, 'Gap or overlap between proposed regions'
    # A plotted land route must not cross the gulf just to connect two endpoints.
    for route in atlas['routes']:
        if route['kind']!='land': continue
        for a,b in zip(route['points'],route['points'][1:]):
            for t in (i/30 for i in range(31)):
                point=(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
                assert inside(point,atlas['mainland']), f'Land route crosses water: {route["id"]}'
    print(f'PASS: {len(pages)} pages, {count} internal links, metadata, fragments, and public-content boundary')
    print('PASS: 7 proposed regions, 35 placed landmarks, regional coverage, and land routes')


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, KeyError, ValueError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        sys.exit(1)
