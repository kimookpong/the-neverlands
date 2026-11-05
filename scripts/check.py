#!/usr/bin/env python3
"""Check the exported site's links, metadata, and publication boundary."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from atlas import inside
from pronunciation import PATTERN, reading
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
        self.text_stack = []
        self.unread_english = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.text_stack.append(tag)
        if tag not in ('option','title'):
            assert not ('option' in self.text_stack and tag=='span'), 'HTML markup inside a select option'
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

    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if self.text_stack and self.text_stack[-1]==tag:
            self.text_stack.pop()

    def handle_endtag(self,tag):
        if tag in self.text_stack:
            self.text_stack=self.text_stack[:len(self.text_stack)-1-self.text_stack[::-1].index(tag)]

    def handle_data(self,text):
        if not any(tag in ('script','style','pre','code') for tag in self.text_stack):
            if re.search(r'[A-Za-z]{2,}',PATTERN.sub('',text)):
                self.unread_english.append(text.strip())


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
        assert not p.unread_english, f'Visible English needs a Thai pronunciation entry: {f.relative_to(OUT)}: {p.unread_english}'
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
    reader=json.loads((ROOT/'content/reader-guide.json').read_text())
    assert reader['visibility']=='public' and reader['scope']=='opening-only'
    cast={p['id']:p for p in reader['characters']}
    assert len(cast)==len(reader['characters'])==19
    artwork=json.loads((ROOT/'content/artwork.json').read_text())
    assert {a['character'] for a in artwork['portraits']}==set(cast)
    for person in cast.values():
        assert (OUT/person['portrait']).exists() and reading(person['name'])
        assert person['status'] in {'working','proposed'}
        assert next(a for a in content['articles'] if a['slug']==person['id'])['category']=='characters'
    known_pairs={frozenset((r['source'],r['target'])) for r in reader['relations'] if r['kind']=='known'}
    assert known_pairs=={frozenset(('caelan','maeron')),frozenset(('roderic','luceran')),frozenset(('halvaren','roderic'))}, 'Published family/guardian ties require explicit review'
    for relation in reader['relations']:
        assert relation['source'] in cast and relation['target'] in cast
        assert relation['kind'] in {'known','role'}
    public_chapters=[c for a in reader['acts'] for c in a['chapters']]
    assert [c['number'] for c in public_chapters]==list(range(1,42))
    assert len(reader['acts'])==6
    assert all(set(c)=={'number','title'} for c in public_chapters), 'Author-only chapter metadata must never be serialized'
    assert len(reader['heraldry'])==9
    for realm in reader['heraldry']:
        assert realm['status']=='proposed' and (OUT/realm['crest']).exists()
        if realm['familyCrest']: assert (OUT/realm['familyCrest']).exists()
        if realm['id'] in {'closed-kingdom','kingless-kingdom'}:assert realm['familyCrest'] is None
    assert next(r for r in reader['heraldry'] if r['id']=='closed-kingdom')['kind']=='reference'
    events=json.loads((ROOT/'content/events.json').read_text())
    assert events['visibility']=='public' and events['scope']=='background-only'
    public_articles={a['slug']:a for a in content['articles']}
    event_slugs={x['slug'] for x in events['events']}
    assert len(event_slugs)==len(events['events'])==8
    places=json.loads((ROOT/'content/atlas.json').read_text())['places']
    for event in events['events']:
        assert set(event)=={'slug','title','kind','period','regions','people','topics','place','summary','knowledge','pressure'}, 'Unexpected event metadata requires public review'
        a=public_articles[event['slug']]
        assert a['category']=='events' and a['status']=='proposed'
        assert a['title']==event['title'] and a['description']==event['summary']
        assert event['regions'] and event['topics'] and event['people']
        assert all(public_articles[s]['category']=='kingdoms' for s in event['regions'])
        assert all(s in cast for s in event['people'])
        assert all(s in public_articles for s in event['topics'])
        place=next(p for p in places if p['id']==event['place'])
        assert place['kingdom'] in event['regions'] and place['kingdom']!='closed-kingdom'
        for slug in event['regions']+event['people']+event['topics']:
            assert event['slug'] in public_articles[slug]['related'], 'Missing return link to event'
        assert (OUT/f'wiki/{event["slug"]}/index.html').exists()
    for path in ['wiki/fantasy-events/index.html','categories/events/index.html']:
        assert (OUT/path).read_text().count('class="event-card"')==8
    atlas=json.loads((ROOT/'content/atlas.json').read_text())
    assert atlas['visibility']=='public' and atlas['status']=='proposed'
    kingdoms={k['id']:k for k in atlas['kingdoms']}
    assert len(kingdoms)==9
    mapped={k:v for k,v in kingdoms.items() if v['mapped']}
    unmapped={k:v for k,v in kingdoms.items() if not v['mapped']}
    assert len(mapped)==9 and not unmapped
    assert kingdoms['closed-kingdom']['title']=='Nhalyra' and kingdoms['kingless-kingdom']['title']=='Orranth'
    assert kingdoms['closed-kingdom']['mapConfidence']=='schematic', 'Closed-island outline must remain explicitly provisional'
    assert len([a for a in content['articles'] if a['category']=='kingdoms'])==9
    assert kingdoms['closed-kingdom']['landform']=='island'
    closed_outline=kingdoms['closed-kingdom']['polygon']
    assert closed_outline in atlas['islands']
    assert all(not inside(p,atlas['mainland']) for p in closed_outline), 'Closed kingdom must remain a separate island'
    legend=next(a for a in content['articles'] if a['slug']=='tree-of-life')
    assert legend['status']=='legend', 'The tree origin story must stay explicitly unverified lore'
    place_ids={p['id'] for p in atlas['places']}
    assert len(place_ids)==len(atlas['places'])==40, 'Expected 40 unique places'
    assert 'tree-of-life' not in place_ids, 'A legendary tree must not acquire a factual map pin'
    for p in atlas['places']:
        assert p['visibility']=='public' and p['status']=='proposed'
        assert p['kingdom'] in kingdoms and inside(p['point'],kingdoms[p['kingdom']]['polygon']), f'Place outside its region: {p["id"]}'
        assert any(inside(p['point'],poly) for poly in [atlas['mainland']]+atlas['islands']), f'Landmark in water: {p["id"]}'
        assert reading(p['name']), f'Missing place pronunciation: {p["id"]}'
    for k in mapped.values():
        assert reading(k['title']), f'Missing region pronunciation: {k["id"]}'
    # Every map label has an adjacent reading in the exported vector, not only
    # in the inspector. Native select options and the JS data must remain valid.
    from xml.etree import ElementTree
    svg=ElementTree.parse(OUT/'assets/neverlands-atlas.svg')
    ns={'s':'http://www.w3.org/2000/svg'}
    map_regions=svg.findall('.//s:path[@class="map-region"]',ns)
    assert {r.attrib['data-region'] for r in map_regions}==set(mapped), 'Only located kingdoms may have map polygons'
    for label in svg.findall('.//s:text',ns):
        if re.search('[A-Za-z]{2,}',label.text or ''):
            assert label.find('s:tspan',ns) is not None, 'Map label lacks a visible Thai reading'
    class Payload(HTMLParser):
        def __init__(self):super().__init__();self.capture=False;self.parts=[]
        def handle_starttag(self,t,attrs):
            if t=='script' and dict(attrs).get('id')=='atlas-data':self.capture=True
        def handle_endtag(self,t):
            if t=='script':self.capture=False
        def handle_data(self,s):
            if self.capture:self.parts.append(s)
    payload=Payload();payload.feed((OUT/'wiki/atlas/index.html').read_text())
    rendered_atlas=json.loads(''.join(payload.parts))
    assert [p['id'] for p in rendered_atlas['places']]==[p['id'] for p in atlas['places']]
    assert all('('+reading(original['name'])+')' in rendered['name'] for original,rendered in zip(atlas['places'],rendered_atlas['places']))
    assert all('('+reading(a['title'])+')' in next(r for r in articles if r['slug']==a['id'])['title'] for a in mapped.values())
    assert {k['id'] for k in rendered_atlas['kingdoms']}==set(kingdoms)
    for k in kingdoms:
        assert sum(p['kingdom']==k for p in atlas['places'])==(0 if k=='closed-kingdom' else 5)
    for x in range(60,1360,13):
        for y in range(60,930,13):
            if any(inside((x,y),poly) for poly in [atlas['mainland']]+atlas['islands']):
                assert sum(inside((x,y),k['polygon']) for k in mapped.values())==1, 'Gap or overlap between proposed regions'
    # A plotted land route must not cross the gulf just to connect two endpoints.
    for route in atlas['routes']:
        for a,b in zip(route['points'],route['points'][1:]):
            for t in (i/30 for i in range(31)):
                point=(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
                assert not inside(point,closed_outline), 'No established route may enter the closed island'
        if route['kind']!='land': continue
        for a,b in zip(route['points'],route['points'][1:]):
            for t in (i/30 for i in range(31)):
                point=(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
                assert inside(point,atlas['mainland']), f'Land route crosses water: {route["id"]}'
    print(f'PASS: {len(pages)} pages, {count} internal links, metadata, fragments, and public-content boundary')
    print('PASS: 9 proposed regions, 40 landmarks, a schematic closed island, no gaps or overlaps, and land routes')
    print('PASS: visible English coverage, bilingual SVG labels, search readings, and unchanged map identifiers')
    print('PASS: 19 portraits, reviewed opening-only relationships, 9 provisional realm symbols and 41 safe chapter labels')
    print('PASS: 8 proposed background events, public-only metadata, reciprocal connections and existing map locations')


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, KeyError, ValueError) as error:
        print(f'FAIL: {error}',file=sys.stderr)
        sys.exit(1)
