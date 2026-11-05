# -*- coding: utf-8 -*-
"""Render the proposed public atlas from structured, spoiler-free map data."""
import html
import json
import math
import random
from pronunciation import annotate, annotate_data, reading

e = html.escape
KINDS = {'seat': 'เมืองศูนย์กลางที่เสนอ', 'city': 'เมือง / สถาบัน',
         'port': 'ท่าเรือ', 'fort': 'ป้อม / ด่าน',
         'resource': 'แหล่งทรัพยากร', 'natural': 'ภูมิประเทศสำคัญ'}


def svg_label(term,x,y,cls,attrs=''):
    return f'<text class="{cls}" x="{x}" y="{y}" {attrs}>{e(term)}<tspan class="map-reading" x="{x}" dy="17">({e(reading(term))})</tspan></text>'


def polygon(points):
    return 'M' + ' L'.join(f'{x:g},{y:g}' for x,y in points) + ' Z'


def line(points):
    return 'M' + ' L'.join(f'{x:g},{y:g}' for x,y in points)


def inside(point, poly):
    x,y = point
    odd = False
    for a,b in zip(poly, poly[1:] + poly[:1]):
        if ((a[1] > y) != (b[1] > y)) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            odd = not odd
    return odd


def coast_detail(points, seed):
    # Preserve every control point, so ports, mouths and the scale remain stable.
    rng = random.Random(seed)
    detailed = []
    for a,b in zip(points, points[1:] + points[:1]):
        detailed.append(a)
        dx,dy = b[0]-a[0],b[1]-a[1]
        length = math.hypot(dx,dy)
        n = max(1,int(length/11))
        for j in range(1,n):
            t = j/n
            # Offshore texture is decorative; keep every land marker on land.
            jitter = rng.uniform(-2.2,2.2) * math.sin(t*math.pi)
            detailed.append((round(a[0]+dx*t-dy/length*jitter,2),
                             round(a[1]+dy*t+dx/length*jitter,2)))
    return detailed


def render_svg(data, interactive=True):
    coast = polygon(coast_detail(data['mainland'], 27))
    land = coast + ' ' + ' '.join(polygon(island) for island in data['islands'])
    regions = []
    for k in data['kingdoms']:
        attrs = f'role="button" tabindex="0" aria-label="สำรวจ {e(annotate(k["title"]))}" aria-pressed="false"' if interactive else ''
        regions.append(f'<path class="map-region" data-region="{k["id"]}" d="{polygon(k["polygon"])}" fill="{k["color"]}" {attrs}><title>{e(annotate(k["title"]))} — {e(k["position"])}</title></path>')
    mountains = []
    rng = random.Random(90)
    # Two separate upland systems; symbols do not imply a surveyed elevation model.
    for x,y in [(662,145),(700,155),(735,160),(773,175),(809,157),(845,145),(881,166),(930,175),
                (680,209),(740,225),(780,255),(835,260),(886,280),(944,307),
                (1010,601),(1050,620),(1090,650),(1125,680),(1160,696)]:
        w = rng.randint(14,21)
        h = rng.randint(19,29)
        mountains.append(f'<g transform="translate({x} {y})"><path d="M{-w},9 L0,{-h} L{w},9 M0,{-h} L4,0 L{w},9"/><path d="M{-w*.28:g},{-h*.46:g} L0,{-h} L{w*.31:g},{-h*.44:g}" class="snow-line"/></g>')
    trees = []
    for row in range(10):
        for col in range(7):
            x=1025+col*27+rng.randint(-7,7)
            y=229+row*29+rng.randint(-6,6)
            if inside((x,y), data['mainland']) and inside((x,y),next(k['polygon'] for k in data['kingdoms'] if k['id']=='sylvara')):
                trees.append(f'<g transform="translate({x} {y})"><path d="M0,3V13"/><circle cx="0" cy="0" r="7"/></g>')
    rivers = ''.join(f'<path d="{line(r["points"])}" stroke-width="{r["width"]}"><title>{e(annotate(r["name"]))}</title></path>' for r in data['rivers'])
    routes = ''.join(f'<path class="map-route route-{r["kind"]}" d="{line(r["points"])}"><title>{e(annotate(r["name"]))}</title></path>' for r in data['routes'])
    labels = ''.join(svg_label(k['title'].upper(),k['label'][0],k['label'][1],'region-label') for k in data['kingdoms'])
    markers=[]
    for p in data['places']:
        x,y=p['point']
        if p['kind']=='seat':
            shape='<path class="place-shape" d="M0,-9 L2.6,-2.7 L9,-2.7 L4,1.5 L5.8,8 L0,4 L-5.8,8 L-4,1.5 L-9,-2.7 L-2.6,-2.7 Z"/>'
        elif p['kind']=='fort':
            shape='<rect class="place-shape" x="-4.5" y="-4.5" width="9" height="9"/>'
        elif p['kind'] in ('resource','natural'):
            shape='<path class="place-shape" d="M0,-6 L5,0 L0,6 L-5,0 Z"/>'
        else:
            shape='<circle class="place-shape" r="4.5"/>'
        # Natural features and close markers have purposefully offset labels.
        offsets={'north-strait':(-15,-12,'end'),'south-strait':(15,18,'start'),
                 'lantern-isles':(-15,18,'end'),'aurel-fields':(13,21,'start'),
                 'veyr-gate':(12,17,'start'),'orath':(12,-13,'start'),
                 'veylora':(14,2,'start'),'myravel':(14,2,'start')}
        dx,dy,anchor=offsets.get(p['id'],(12,-22,'start'))
        attrs=f'role="button" tabindex="0" aria-label="{e(p["thai"])} · {e(annotate(p["name"]))}" aria-pressed="false"' if interactive else ''
        markers.append(f'''<g class="map-place place-{p['kind']}" data-place="{p['id']}" data-region="{p['kingdom']}" transform="translate({x} {y})" {attrs}>
          <title>{e(annotate(p['name']))} · {e(p['thai'])}</title><circle class="place-hit" r="13"/>{shape}
          {svg_label(p['name'],dx,dy,'place-label',f'text-anchor="{anchor}"')}</g>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" id="atlas-map" viewBox="0 0 1440 1040" role="group" aria-labelledby="atlas-svg-title atlas-svg-desc">
      <title id="atlas-svg-title">{e(annotate('The Neverlands'))} — แผนที่ทวีปข้อเสนอ 0.1</title>
      <desc id="atlas-svg-desc">{e(annotate('เจ็ดภูมิภาครอบอ่าวที่เปิดทางตะวันตก Karveth อยู่เหนือ Eldraven อยู่กลาง Aurevan อยู่ตะวันตกเฉียงเหนือ Varessia อยู่ฝั่งเหนือปากอ่าว Myrthen อยู่ฝั่งใต้ Sylvara อยู่ตะวันออก และ Drakoria อยู่ตะวันออกเฉียงใต้ จุดทั้งหมดมีรายละเอียดในรายชื่อสถานที่ด้านล่าง'))}</desc>
      <defs><clipPath id="atlas-land-clip"><path d="{land}"/></clipPath>
      <pattern id="atlas-grid" width="125" height="125" patternUnits="userSpaceOnUse"><path d="M125,0 H0 V125" fill="none" stroke="#738b85" stroke-width=".6" opacity=".22"/></pattern>
      <pattern id="atlas-grain" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".45" fill="#6b6249" opacity=".1"/></pattern>
      <style>
        #atlas-map{{background:#cbd9d3;font-family:Georgia,'Times New Roman',serif;color:#384738;touch-action:pan-y}}
        #atlas-map .map-region{{fill-opacity:.32;stroke:#706951;stroke-width:1.25;stroke-dasharray:5 5;transition:fill-opacity .18s;cursor:{'pointer' if interactive else 'default'}}}
        #atlas-map .map-region:hover,#atlas-map .map-region:focus,#atlas-map .map-region.is-active{{fill-opacity:.66;stroke:#463e28;stroke-width:2.5;outline:none}}
        #atlas-map .map-region.is-muted{{fill-opacity:.13}}
        #atlas-map .coastline{{fill:none;stroke:#536452;stroke-width:2;pointer-events:none}}
        #atlas-map .terrain-mountains{{stroke:#7b7056;stroke-width:1.05;fill:#d0c6aa;opacity:.8;pointer-events:none}}
        #atlas-map .snow-line{{fill:#eee9d9;stroke-width:.7}}
        #atlas-map .terrain-trees{{stroke:#637a5a;stroke-width:.7;fill:#99aa7c;opacity:.48;pointer-events:none}}
        #atlas-map .map-rivers{{stroke:#598991;fill:none;stroke-linejoin:round;stroke-linecap:round;pointer-events:none}}
        #atlas-map .map-route{{fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}}
        #atlas-map .route-land{{stroke:#8f6047;stroke-dasharray:5 5}}
        #atlas-map .route-sea{{stroke:#497b83;stroke-dasharray:9 5}}
        #atlas-map .route-migration{{stroke:#7e6d9d;stroke-dasharray:2 7;display:none}}
        #atlas-map.show-migration .route-migration{{display:block}}
        #atlas-map.hide-trade .route-land,#atlas-map.hide-trade .route-sea{{display:none}}
        #atlas-map.hide-terrain .map-terrain{{display:none}}
        #atlas-map .region-label{{font-size:20px;letter-spacing:3px;text-anchor:middle;fill:#46503b;paint-order:stroke;stroke:#e4dec5;stroke-width:3;stroke-linejoin:round;pointer-events:none}}
        #atlas-map .map-reading{{font-family:Thonburi,'Noto Sans Thai',Tahoma,sans-serif;font-size:12px;letter-spacing:0;font-weight:400;font-style:normal}}
        #atlas-map .water-label{{fill:#577a7a;font-size:18px;letter-spacing:3px;text-anchor:middle;font-style:italic;pointer-events:none}}
        #atlas-map .feature-label{{font-size:12px;font-style:italic;fill:#796c51;letter-spacing:1px;paint-order:stroke;stroke:#e7e0cb;stroke-width:3;pointer-events:none}}
        #atlas-map .map-place{{cursor:{'pointer' if interactive else 'default'};outline:none}}
        #atlas-map .place-hit{{fill:transparent;stroke:none}}
        #atlas-map .place-shape{{fill:#eee9d5;stroke:#51482f;stroke-width:1.5}}
        #atlas-map .place-seat .place-shape{{fill:#51482f;stroke:#eee9d5;stroke-width:1.3}}
        #atlas-map .place-label{{fill:#3d422f;stroke:#ece6d0;stroke-width:4;stroke-linejoin:round;paint-order:stroke;font-size:13px;display:none;pointer-events:none}}
        #atlas-map .place-seat .place-label,#atlas-map .map-place:hover .place-label,#atlas-map .map-place:focus .place-label,#atlas-map .map-place.is-active .place-label{{display:block}}
        #atlas-map .map-place.is-muted{{opacity:.24}}
        #atlas-map .map-place.is-selected .place-shape,#atlas-map .map-place:focus .place-shape{{fill:#d6a951;stroke:#3d321e;stroke-width:2.5}}
        #atlas-map .map-place.is-selected .place-label{{font-weight:bold}}
      </style></defs>
      <rect width="1440" height="1040" fill="#cbd9d3"/>
      <rect x="22" y="22" width="1396" height="996" fill="url(#atlas-grid)" stroke="#879482" stroke-width="1"/>
      <path d="{land}" fill="#e5dec6" stroke="#8b9579" stroke-width="9" stroke-opacity=".3"/>
      <g clip-path="url(#atlas-land-clip)">{''.join(regions)}<rect x="250" y="50" width="1040" height="900" fill="url(#atlas-grain)" pointer-events="none"/></g>
      <g class="map-terrain" clip-path="url(#atlas-land-clip)"><g class="terrain-trees">{''.join(trees)}</g><g class="terrain-mountains">{''.join(mountains)}</g></g>
      <path class="coastline" d="{land}"/>
      <g class="map-rivers">{rivers}<ellipse cx="908" cy="205" rx="19" ry="10" transform="rotate(15 908 205)" fill="#a6c2c0" stroke="#598991" stroke-width="1.3"/></g>
      <g class="map-routes">{routes}</g>
      <g class="region-labels">{labels}</g>
      {svg_label('LONGWAKE OCEAN',175,555,'water-label','transform="rotate(-90 175 555)"')}
      {svg_label('VEYR GULF',629,578,'water-label','transform="rotate(-15 629 578)" style="font-size:13px;letter-spacing:2px"')}
      {svg_label('RAIN SEA',1350,464,'water-label','transform="rotate(90 1350 464)"')}
      {svg_label('SOUTHERN WATERS',950,978,'water-label','style="font-size:15px"')}
      {svg_label('KARVETH SPINE',776,295,'feature-label','transform="rotate(20 776 295)"')}
      {svg_label('Veyr',875,454,'feature-label')}
      {svg_label('Lethi',568,476,'feature-label')}
      <g class="map-places">{''.join(markers)}</g>
      <g transform="translate(58 65)" fill="#374937"><text font-size="30" letter-spacing="1">THE NEVERLANDS<tspan class="map-reading" x="0" dy="23">(เดอะ เนเวอร์แลนด์ส)</tspan></text><text y="44" font-size="12" font-family="Thonburi,Tahoma,sans-serif">แผนที่ทวีปข้อเสนอ · รุ่น 0.1</text></g>
      <g transform="translate(62 165)"><rect width="193" height="177" rx="2" fill="#e5e4d2" stroke="#91a08c"/><text x="14" y="24" fill="#5b6751" font-size="10" letter-spacing="1">OLD MAINLAND<tspan class="map-reading" x="14" dy="17">(โอลด์ เมนแลนด์) · นอกกรอบ</tspan></text><path d="M22,64 L43,48 L63,55 L75,85 L61,98 L68,114 L49,126 L29,116 L18,93Z" fill="#b2b795" stroke="#7a8567"/><path d="M76,86 Q135,84 165,126" stroke="#7e6d9d" stroke-width="1.5" stroke-dasharray="3 5" fill="none"/><path d="M155,121 L166,127 L164,116" stroke="#7e6d9d" fill="none"/><text x="14" y="150" font-size="11" font-family="Thonburi,Tahoma,sans-serif" fill="#68745d">3,000–4,500 กม. · ข้อเสนอ</text><text x="14" y="168" font-size="10" font-family="Thonburi,Tahoma,sans-serif" fill="#68745d">ภาพย่อใช้คนละมาตราส่วนกับทวีป</text></g>
      <g transform="translate(1345 125)" stroke="#56644a" fill="#56644a"><path d="M0,5V95 M-30,52H30" stroke-width="1"/><path d="M0,5 L-9,53 L0,43 L9,53Z"/><path d="M0,95 L-5,52 L0,61 L5,52Z" fill="none"/><circle cy="52" r="19" fill="none" stroke-opacity=".5"/><text y="-7" text-anchor="middle" stroke="none" font-size="13" font-family="Thonburi,Tahoma,sans-serif">เหนือ</text></g>
      <g transform="translate(60 924)" fill="#46543e" font-family="Thonburi,Tahoma,sans-serif"><text font-size="12">มาตราส่วนแนวคิด · ไม่ใช่ผลสำรวจ</text><path d="M0,20H250 M0,15V25 M125,15V25 M250,15V25" stroke="#46543e" stroke-width="2"/><text y="42" font-size="11">0</text><text x="114" y="42" font-size="11">250</text><text x="230" y="42" font-size="11">500 กม.</text><text y="66" font-size="11">แนวภูมิภาคเป็นข้อเสนอ ไม่ใช่แนวควบคุมทางทหาร</text></g>
    </svg>'''


def atlas_block(data, base):
    options=''.join(f'<option value="{k["id"]}">{e(k["title"])}</option>' for k in data['kingdoms'])
    static=[]
    for k in data['kingdoms']:
        places=''.join(f'''<li id="place-{p['id']}"><div><span class="atlas-place-type">{KINDS[p['kind']]}</span><h4>{e(p['thai'])} <span>{e(p['name'])}</span></h4></div><p>{e(p['role'])}</p><p><strong>ความสำคัญ:</strong> {e(p['strategic'])}</p><p class="atlas-place-caveat">{e(p['dependency'])}</p><button type="button" class="atlas-locate" data-locate="{p['id']}">ดูตำแหน่งบนแผนที่ ↗</button></li>''' for p in data['places'] if p['kingdom']==k['id'])
        static.append(f'''<details class="atlas-region-detail" id="region-{k['id']}"><summary><span class="atlas-swatch" style="background:{k['color']}"></span><span class="atlas-region-name">{e(k['title'])}</span><span>5 สถานที่สำคัญ</span></summary><div class="atlas-region-copy"><p>{e(k['terrain'])}</p><dl><div><dt>ภูมิอากาศที่เสนอ</dt><dd>{e(k['climate'])}</dd></div><div><dt>ทรัพยากรและเศรษฐกิจ</dt><dd>{e(k['resources'])}</dd></div><div><dt>อำนาจต่อรอง</dt><dd>{e(k['leverage'])}</dd></div><div><dt>ข้อจำกัด</dt><dd>{e(k['vulnerability'])}</dd></div></dl></div><ol class="atlas-place-list">{places}</ol><a class="text-link" href="{base}wiki/{k['id']}/">อ่านเรื่อง {e(k['title'])} →</a></details>''')
    routes=''.join(f'<li><strong>{e(r["name"])}</strong><p>{e(r["description"])}</p></li>' for r in data['routes'])
    assumptions=''.join(f'<li>{e(t)}</li>' for t in data['assumptions'])
    payload=json.dumps(annotate_data(data),ensure_ascii=False).replace('<','\\u003c')
    return f'''<section class="atlas-experience" aria-labelledby="atlas-heading">
      <div class="atlas-heading"><div><p class="eyebrow">ภูมิประเทศก่อนพรมแดน</p><h2 id="atlas-heading">แผนที่ทวีปและสถานที่สำคัญ</h2></div><span class="atlas-proposal">แผนที่ข้อเสนอ · 0.1</span></div>
      <p class="atlas-disclaimer">ชื่อ ภูมิประเทศ เมือง และขอบเขตทั้งหมดในแผนที่เป็นข้อเสนอ ยังไม่ล็อก Canon สีแสดงภูมิภาคอ้างอิง ไม่ใช่แนวควบคุมทางทหารในทุกช่วงเรื่อง</p>
      <div class="atlas-toolbar"><label for="atlas-region">เลือกดินแดน <select id="atlas-region"><option value="">ภาพรวมทั้งทวีป</option>{options}</select></label><fieldset><legend class="sr-only">ชั้นข้อมูลแผนที่</legend><label><input id="atlas-terrain" type="checkbox" checked> ภูมิประเทศ</label><label><input id="atlas-trade" type="checkbox" checked> การค้า</label><label><input id="atlas-migration" type="checkbox"> เส้นทางอพยพที่เสนอ</label></fieldset></div>
      <div class="atlas-layout"><div class="atlas-map-wrap"><div class="atlas-map-viewport">{render_svg(data)}</div><div class="atlas-zoom"><button type="button" id="atlas-zoom-in" aria-label="ขยายแผนที่">+</button><button type="button" id="atlas-zoom-out" aria-label="ย่อแผนที่">−</button><button type="button" id="atlas-reset">ทั้งทวีป</button></div><div class="atlas-legend"><span>★ เมืองศูนย์กลาง</span><span>○ เมือง / ท่าเรือ</span><span>□ ป้อม / ด่าน</span><span>◇ ทรัพยากร / ธรรมชาติ</span><span><i class="legend-land"></i> ทางบก</span><span><i class="legend-sea"></i> ทางเรือ</span></div></div>
      <aside class="atlas-inspector" aria-label="รายละเอียดดินแดนที่เลือก"><p class="eyebrow" id="atlas-inspector-kicker">7 ภูมิภาค · 35 สถานที่</p><h3 id="atlas-region-title">โลกที่ต้องพึ่งพากัน</h3><p id="atlas-region-text">เลือกพื้นที่หรือจุดบนแผนที่เพื่ออ่านรายละเอียด อ่าวเวย์ร์เชื่อมลุ่มน้ำกลางกับทะเลเปิด โดยมี Varessia และ Myrthen อยู่คนละฝั่งของปากอ่าว</p><dl id="atlas-region-facts"></dl><div id="atlas-place-detail" hidden></div><div id="atlas-place-buttons"></div><p id="atlas-selection-status" role="status" aria-live="polite"></p></aside></div>
      <div class="atlas-reading-links"><a href="{base}assets/neverlands-atlas.svg" download="the-neverlands-proposed-atlas.svg">ดาวน์โหลดแผนที่ SVG ↗</a><span>เหนืออยู่ด้านบน · ระยะทางเป็นมาตราส่วนแนวคิด</span></div>
      <section class="atlas-explanation"><h3>เหตุผลที่วางภูมิประเทศแบบนี้</h3><p>แนวเขาทางเหนือให้แร่ ต้นน้ำ และข้อจำกัดการขนส่ง ลุ่มน้ำกลางรองรับอาหาร เมือง และตลาด อ่าวลึกทำให้การค้าในแผ่นดินต้องเจรจากับอำนาจทางทะเล ส่วนชายฝั่งตะวันออกและท่าเรือใต้ช่วยให้ไม่มีฝ่ายใดผูกขาดทางออกของทั้งทวีป</p><p>ป่า Sylvara รับฝนตามฤดูจากทะเลตะวันออก จึงไม่ต้องอธิบายว่าป่าชื้นเกิดจากเวทมนตร์ ขณะที่แนวเขารองและหลายลุ่มน้ำทำให้ Drakoria มีศูนย์อำนาจกระจายตัวได้</p></section>
      <section class="atlas-locations" aria-labelledby="atlas-locations-heading"><div class="section-heading"><div><p class="eyebrow">สถานที่ที่กำหนดการเมือง</p><h3 id="atlas-locations-heading">สถานที่สำคัญของแต่ละอาณาจักร</h3></div><span class="section-note">ทั้งหมดเป็นข้อเสนอและชื่อชั่วคราว</span></div>{''.join(static)}</section>
      <details class="atlas-method"><summary>เส้นทางการค้าและการอพยพที่เสนอ</summary><ul>{routes}</ul></details><details class="atlas-method"><summary>มาตราส่วน สมมติฐาน และขอบเขตข้อมูล</summary><ul>{assumptions}</ul></details>
      <noscript><p>แผนที่ภาพรวมและรายชื่อสถานที่อ่านได้โดยไม่ใช้ JavaScript การเลือกพื้นที่และการขยายแผนที่ต้องเปิด JavaScript</p></noscript>
      <script type="application/json" id="atlas-data">{payload}</script><script defer src="{base}assets/atlas.js"></script>
    </section>'''
