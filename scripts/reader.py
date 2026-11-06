# -*- coding: utf-8 -*-
"""Reader-only portraits, relationships, heraldry and safe chapter labels.
Never imports author files or local writer data.
"""
import html
import json
from pronunciation import annotate

e = html.escape


def portrait(person, base, eager=False, full=False):
    image_class='manga-portrait' if person.get('artFormat')=='manga-sheet' and not full else 'manga-sheet-image'
    return f'<img class="{image_class}" src="{base}{person["portrait"]}" alt="{e(person["portraitAlt"])}" width="{person.get("portraitWidth",1086)}" height="{person.get("portraitHeight",1448)}" loading="{"eager" if eager else "lazy"}" decoding="async">'


def relation_links(person, data, base):
    people={p['id']:p for p in data['characters']}
    links=[]
    for r in data['relations']:
        if person['id'] not in (r['source'],r['target']): continue
        other=people[r['target'] if r['source']==person['id'] else r['source']]
        kind='ความสัมพันธ์ที่เปิดเผย' if r['kind']=='known' else 'ความเกี่ยวข้องตามบทบาท'
        links.append(f'''<a class="relation-link" href="{base}wiki/{other['id']}/"><span class="relation-type {r['kind']}">{kind}</span><strong>{e(other['name'])}</strong><span>{e(r['label'])}</span><small>{e(r['description'])}</small><span aria-hidden="true">↗</span></a>''')
    if not links:
        return '<p class="reader-note-copy">ยังไม่มีความเชื่อมโยงในขอบเขตข้อมูลที่เปิดเผย</p>'
    return '<div class="relation-links">'+''.join(links)+'</div>'


def profile_block(slug, data, base):
    person=next((p for p in data['characters'] if p['id']==slug),None)
    if not person: return ''
    region=f'<a href="{base}wiki/{person["kingdom"]}/">{e(person["affiliation"])} ↗</a>' if person['kingdom'] else e(person['affiliation'])
    status='บทบาทเสนอ · ยังพัฒนา' if person['status']=='proposed' else 'ข้อมูลช่วงต้นเรื่อง'
    design=f'''<section class="character-design" id="character-design" aria-labelledby="character-design-heading"><p class="eyebrow">แบบตัวละครมังงะขาวดำ</p><h2 id="character-design-heading">เต็มตัวสามมุมและสองสีหน้า</h2><p class="reader-note-copy">จุดจำของแบบนี้: {e(person['appearance'])}</p><figure><a href="{base}{person['portrait']}" target="_blank" rel="noopener" aria-label="เปิดแบบเต็มของ {e(person['name'])}">{portrait(person,base,full=True)}</a><figcaption>แบบระหว่างพัฒนา · รายละเอียดกายภาพและสัดส่วนที่เห็นยังปรับได้</figcaption></figure><a class="text-link" href="{base}{person['portrait']}" target="_blank" rel="noopener">เปิดภาพขนาดเต็ม ↗</a></section>''' if person.get('artFormat')=='manga-sheet' else ''
    return f'''<section class="person-profile" aria-label="ภาพและบทบาทตัวละคร"><figure><div class="person-portrait">{portrait(person,base,True)}</div><figcaption>แบบมังงะขาวดำ · รูปลักษณ์ยังปรับได้</figcaption></figure><div class="person-summary"><p class="eyebrow">{status}</p><h2>{e(person['role'])}</h2><p>{e(person['bio'])}</p><dl><div><dt>สังกัดหรือบริบท</dt><dd>{region}</dd></div><div><dt>ขอบเขตภาพ</dt><dd>หน้าตา เสื้อผ้า และอายุที่เห็นเป็นข้อเสนอด้านภาพ ยังไม่ยืนยันเป็นข้อมูลถาวร</dd></div></dl><a class="text-link" href="{base}categories/characters/?character={person['id']}#connections">ดูความเชื่อมโยงของตัวละคร →</a></div></section>{design}
    <section class="reader-connections" aria-labelledby="character-connections-heading"><p class="eyebrow">อ่านต่อผ่านผู้คน</p><h2 id="character-connections-heading">ความเชื่อมโยงที่เปิดเผยได้</h2><p class="reader-note-copy">ความเกี่ยวข้องตามบทบาทใช้เชื่อมบริบท ไม่ยืนยันความเป็นญาติ การร่วมมือ หรือความภักดีในอนาคต</p>{relation_links(person,data,base)}</section>'''


def character_catalog(data, base):
    cards=[]
    for p in data['characters']:
        role_label='บทบาทที่เสนอ' if p['status']=='proposed' else 'ข้อมูลช่วงต้น'
        appearance=f'<p class="cast-appearance"><strong>จุดจำ</strong> {e(p["appearance"])}</p>' if p.get('appearance') else ''
        design_link=f'<a class="cast-design-link" href="{base}wiki/{p["id"]}/#character-design">ดูแบบเต็ม · สามมุมและสองสีหน้า ↗</a>' if p.get('artFormat')=='manga-sheet' else ''
        cards.append(f'''<article class="cast-card" data-person="{p['id']}" data-affiliation="{e(p['affiliation'])}"><a class="cast-image" href="{base}wiki/{p['id']}/" aria-label="อ่านเรื่อง {e(p['name'])}">{portrait(p,base)}<span>{role_label}</span></a><div class="cast-copy"><p class="eyebrow">{e(p['affiliation'])}</p><h2><a href="{base}wiki/{p['id']}/">{e(p['name'])}</a></h2><p>{e(p['role'])}</p>{appearance}{design_link}<div class="cast-actions"><a href="{base}wiki/{p['id']}/">อ่านข้อมูล ↗</a><a href="?character={p['id']}#connections" data-focus-person="{p['id']}">ความเชื่อมโยง →</a></div></div></article>''')
    affiliations=list(dict.fromkeys(p['affiliation'] for p in data['characters']))
    options=''.join(f'<option value="{e(a)}">{e(a)}</option>' for a in affiliations)
    person_options=''.join(f'<option value="{p["id"]}">{e(annotate(p["name"]))}</option>' for p in data['characters'])
    # Payload contains a purpose-built public allowlist; no author metadata is serialized.
    payload=json.dumps(dict(characters=[dict(id=p['id'],name=annotate(p['name']),role=p['role'],portrait=base+p['portrait'],artFormat=p.get('artFormat','portrait'),url=base+'wiki/'+p['id']+'/') for p in data['characters']],relations=data['relations']),ensure_ascii=False).replace('<','\\u003c')
    fallback=''.join(f'<li><a href="{base}wiki/{r["source"]}/">{e(next(p["name"] for p in data["characters"] if p["id"]==r["source"]))}</a> · {e(r["label"])} · <a href="{base}wiki/{r["target"]}/">{e(next(p["name"] for p in data["characters"] if p["id"]==r["target"]))}</a></li>' for r in data['relations'])
    return f'''<div class="listing-page reader-cast-page"><header class="listing-header"><p class="eyebrow">ผู้คนที่ทำให้โลกเคลื่อนไหว</p><h1>ตัวละครสำคัญ</h1><p>รู้จักผู้คนผ่านภาพมังงะขาวดำ จุดจำ และความสัมพันธ์จากช่วงต้นเรื่อง</p><span class="listing-count">{len(data['characters'])} ตัวละคร · แบบมังงะขาวดำระหว่างพัฒนา</span><p class="reader-note-copy">เปิดแบบเต็มเพื่อดูตัวละครสามมุมและสองสีหน้า จุดจำอธิบายภาพร่างและยังปรับได้</p></header>
      <div class="reader-filter"><label for="cast-query">ค้นหาตัวละคร<input id="cast-query" type="search" placeholder="ชื่อ คำอ่าน หรือบทบาท…"></label><label for="cast-affiliation">สังกัดและบริบท<select id="cast-affiliation"><option value="">ทั้งหมด</option>{options}</select></label><p id="cast-status" role="status" aria-live="polite">{len(cards)} ตัวละคร</p></div><div class="cast-grid" id="cast-grid">{''.join(cards)}</div>
      <section class="relationship-hub" id="connections" aria-labelledby="connections-heading"><header><p class="eyebrow">มองผู้คนผ่านความเชื่อมโยง</p><h2 id="connections-heading">ใครเกี่ยวข้องกับใคร</h2><p>เลือกตัวละครเพื่อดูความสัมพันธ์ที่เปิดเผยแล้ว หรือบริบทที่เชื่อมกันผ่านงานและดินแดน</p></header><div class="reader-filter"><label for="relation-person">ตัวละคร<select id="relation-person">{person_options}</select></label><label for="relation-kind">ประเภทความเชื่อมโยง<select id="relation-kind"><option value="all">ทั้งหมด</option><option value="known">ความสัมพันธ์ที่เปิดเผย</option><option value="role">ความเกี่ยวข้องตามบทบาท</option></select></label></div><div id="relation-focus" class="relation-focus"></div><div class="relation-branch" aria-hidden="true"></div><div id="relation-results" class="relation-results"></div><p id="relation-status" role="status" aria-live="polite"></p><noscript><ul class="relation-fallback">{fallback}</ul></noscript></section><p class="reader-bottom-note">ข้อมูลแสดงเฉพาะขอบเขตที่เปิดเผยได้ ภาพไม่ได้ยืนยันรายละเอียดรูปลักษณ์หรือเหตุการณ์อนาคต</p><script type="application/json" id="reader-data">{payload}</script><script src="{base}assets/reader.js?v=manga1" defer></script></div>'''


def crest_svg(r, family=False):
    bg,fg=r['background'],r['foreground']
    shapes={
    'aurevan':'<path d="M-65,56V-15H-35V-39H-15V-15H15V-39H35V-15H65V56Z"/><path d="M-45,-57L-53,-83L-23,-71L0,-98L23,-71L53,-83L45,-57Z"/><path d="M-10,56V28Q0,10 10,28V56"/>',
    'eldraven':'<path d="M-62,58Q-10,32 0,-5Q10,32 62,58M0,-5V-53M-65,-8Q-24,-16 0,-5Q24,-16 65,-8"/><path d="M0,-94L13,-72L0,-50L-13,-72Z"/>',
    'varessia':'<path d="M0,41Q-30,21 -65,32V-48Q-30,-60 0,-41Q30,-60 65,-48V32Q30,21 0,41ZM0,-41V41M-48,-27L-17,-20M17,-20L48,-27M-48,-5L-17,2M17,2L48,-5M0,77V54M-48,74L-26,58M48,74L26,58"/>',
    'myrthen':'<path d="M0,-91V29M-8,-74L-62,12H-8ZM10,-65L59,12H10ZM-71,28H71L43,55H-43ZM-78,78Q-52,60 -26,78Q0,96 26,78Q52,60 78,78"/>',
    'karveth':'<path d="M-77,7L-29,-76L8,-5L38,-50L78,12ZM-29,-76L-21,-37M-58,79L42,32M58,79L-42,32M23,20L51,39M-23,20L-51,39"/>',
    'sylvara':'<path d="M0,-85V16Q-40,39 0,58Q30,73 0,93M0,-35Q-65,-28 -53,-74Q-10,-80 0,-35ZM0,-3Q65,4 53,-43Q10,-48 0,-3ZM0,20Q-63,30 -49,-13Q-13,-20 0,20Z"/>',
    'drakoria':'<path d="M-77,7H77M-62,7V-30H62V7M-62,5V43M62,5V43M-39,7V-13M0,7V-13M39,7V-13M0,89V52M0,52L-60,81M0,52L60,81"/>',
    'closed-kingdom':'<ellipse cx="0" cy="-36" rx="72" ry="43"/><path d="M-83,-49H83M-89,-23H89M-65,6H65M-58,57L-31,31L-9,43L17,17L43,43L62,58ZM-74,81Q-37,66 0,81Q37,96 74,81"/>',
    'kingless-kingdom':'<path d="M-58,34V-37Q0,-106 58,-37V34M-38,34V-28Q0,-72 38,-28V34M0,92V51M0,51L-55,82M0,51L55,82"/>'}
    crown='<path d="M95,49L85,17L122,34L150,6L178,34L215,17L205,49Z" fill="'+fg+'" stroke="'+bg+'" stroke-width="3"/>' if family else ''
    name=annotate(r['name'])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 360" role="img" aria-labelledby="crest-title"><title id="crest-title">{e(name)} · {e(r['caption']) if family else 'ตราดินแดนที่เสนอ'}</title><defs><linearGradient id="shield-shade" x2="1" y2="1"><stop stop-color="{bg}"/><stop offset="1" stop-color="#202822"/></linearGradient></defs>{crown}<path d="M47,62H253V207Q250,277 150,333Q50,277 47,207Z" fill="url(#shield-shade)" stroke="{fg}" stroke-width="5"/><path d="M59,74H241V207Q238,267 150,319Q62,267 59,207Z" fill="none" stroke="{fg}" stroke-width="1" opacity=".65"/><g transform="translate(150 179)" fill="none" stroke="{fg}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round">{shapes[r['id']]}</g><circle cx="150" cy="300" r="3" fill="{fg}"/></svg>'''


def realm_block(slug, data, base):
    r=next((r for r in data['heraldry'] if r['id']==slug),None)
    if not r:return ''
    family=f'<figure><img src="{base}{r["familyCrest"]}" width="300" height="360" alt="{e(r["caption"])}" loading="lazy"><figcaption>{e(r["caption"])}</figcaption></figure>' if r['familyCrest'] else ''
    return f'''<section class="realm-identity" aria-labelledby="realm-emblem-heading"><div class="realm-crests"><figure><img src="{base}{r['crest']}" width="300" height="360" alt="เครื่องหมายที่เสนอของ {e(r['name'])}" loading="lazy"><figcaption>{'เครื่องหมายอ้างอิงที่เสนอ' if r['kind']=='reference' else 'ตราดินแดนที่เสนอ'}</figcaption></figure>{family}</div><div><p class="eyebrow">ตราและผู้ครองอำนาจ</p><h2 id="realm-emblem-heading">{e(r['symbol'])}</h2><p>{e(r['meaning'])}</p><dl><div><dt>ผู้ครองอำนาจหรือสถานะ</dt><dd>{e(r['ruler'])}</dd></div><div><dt>ตระกูลผู้ปกครอง</dt><dd>{e(r['family'])}</dd></div></dl><p class="reader-note-copy">ตราเป็นข้อเสนอด้านภาพ ยังไม่ยืนยันเป็นเครื่องหมายที่ใช้จริงในเรื่อง</p><a class="text-link" href="{base}wiki/heraldry/#emblem-{r['id']}">อ่านตราและสถานะข้อมูล →</a></div></section>'''


def heraldry_catalog(data, base):
    blocks=[]
    for r in data['heraldry']:
        blocks.append(f'''<section class="heraldry-entry" id="emblem-{r['id']}"><header><p class="eyebrow">{e(r['caption'])}</p><h2><a href="{base}wiki/{r['id']}/">{e(r['name'])} ↗</a></h2></header>{realm_block(r['id'],data,base).replace('id="realm-emblem-heading"',f'id="crest-heading-{r["id"]}"').replace('aria-labelledby="realm-emblem-heading"',f'aria-labelledby="crest-heading-{r["id"]}"')}<a class="crest-download" href="{base}{r['crest']}" download>ดาวน์โหลดตราดินแดน ↗</a></section>''')
    jumps=''.join(f'<a href="#emblem-{r["id"]}">{e(r["name"])}</a>' for r in data['heraldry'])
    return '<nav class="act-jumps" aria-label="เลือกตราดินแดน">'+jumps+'</nav><div class="heraldry-catalog">'+''.join(blocks)+'</div>'


def story_block(data):
    jumps=''.join(f'<a href="#story-{a["id"]}">{e(a["title"])}</a>' for a in data['acts'])
    groups=[]
    for act in data['acts']:
        chapters=''.join(f'<li id="chapter-{c["number"]}"><a class="chapter-index" href="#chapter-{c["number"]}" aria-label="บทที่ {c["number"]}">{c["number"]:02d}</a><h3>{e(c["title"])}</h3><span class="chapter-state">อยู่ระหว่างเขียน</span></li>' for c in act['chapters'])
        groups.append(f'''<section class="reader-act" id="story-{act['id']}"><header><div><p class="eyebrow">{e(act['title'])}</p><h2>{e(act['subtitle'])}</h2><p>{e(act['description'])}</p></div><span>{len(act['chapters'])} บท</span></header><ol class="reader-chapters" start="{act['chapters'][0]['number']}">{chapters}</ol></section>''')
    return f'''<section class="story-reader" aria-label="โครงองค์และบทสำหรับผู้อ่าน"><div class="story-summary"><strong>4 องค์</strong><span>บทนำ + บทส่งท้าย</span><strong>41 บท</strong><span>ชื่อฉบับสำหรับผู้อ่าน</span></div><p class="reader-note-copy">ชื่อในหน้านี้เป็นชื่อสำหรับผู้อ่านระหว่างพัฒนา เพื่อเก็บจุดหักมุมจากชื่อบทฉบับผู้เขียน ไม่มีเรื่องย่อตอนจบหรือข้อมูลความลับอยู่ในหน้านี้</p><nav class="act-jumps" aria-label="เลือกองค์">{jumps}</nav>{''.join(groups)}</section>'''
