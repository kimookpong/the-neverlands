"""Render the curated public event register, without author planning data."""
from html import escape as e


def event_links(slug, data, articles, base):
    matches = [x for x in data['events'] if slug in x['regions'] + x['people'] + x['topics']]
    if not matches:
        return ''
    links = ''.join(f'<a href="{base}wiki/{x["slug"]}/"><span>{e(x["kind"])}</span><strong>{e(x["title"])}</strong><small>{e(x["summary"])}</small><b aria-hidden="true">↗</b></a>' for x in matches)
    return f'<section class="event-connections" aria-labelledby="event-connections-heading"><p class="eyebrow">ร่องรอยที่เชื่อมเรื่องเล่า</p><h2 id="event-connections-heading">เหตุการณ์ที่เกี่ยวข้อง</h2><p class="reader-note-copy">เหตุการณ์เสนอในช่วงภูมิหลังก่อนเรื่องหลัก ความเกี่ยวข้องตามหน้าที่ไม่ยืนยันว่าตัวละครอยู่ในเหตุการณ์หรือเป็นผู้ก่อเหตุ</p><div class="event-related">{links}</div></section>'


def event_context(slug, data, articles, atlas, base):
    event = next((x for x in data['events'] if x['slug'] == slug), None)
    if not event:
        return ''
    links = lambda ids: ''.join(f'<a href="{base}wiki/{s}/">{e(articles[s]["title"])} ↗</a>' for s in ids)
    place = next(p for p in atlas['places'] if p['id'] == event['place'])
    return f'''<section class="event-context" aria-label="บริบทของเหตุการณ์"><div><p class="eyebrow">{e(event['kind'])} · ข้อเสนอ</p><h2>ขอบเขตที่ผู้อ่านรู้</h2><p>{e(event['knowledge'])}</p><dl><div><dt>ช่วงเวลา</dt><dd>{e(event['period'])}</dd></div><div><dt>สถานที่อ้างอิง</dt><dd><a href="{base}wiki/atlas/?place={place['id']}">{e(place['name'])} ↗</a></dd></div></dl></div><div class="event-context-links"><h3>ดินแดนและหัวข้อ</h3>{links(event['regions'] + event['topics'])}<h3>ผู้เกี่ยวข้องตามบทบาท</h3><p>ใช้เชื่อมงานและบริบท ไม่ยืนยันการมีส่วนร่วมในคดี</p>{links(event['people'])}</div></section>'''


def event_catalog(data, articles, base):
    groups = list(dict.fromkeys(x['kind'] for x in data['events']))
    jumps = ''.join(f'<a href="#event-group-{i}">{e(kind)}</a>' for i, kind in enumerate(groups, 1))
    sections = []
    for i, kind in enumerate(groups, 1):
        cards = []
        for x in data['events']:
            if x['kind'] != kind:
                continue
            tags = ''.join(f'<a href="{base}wiki/{s}/">{e(articles[s]["title"])}</a>' for s in x['regions'] + x['topics'])
            cards.append(f'''<article class="event-card"><p class="eyebrow">ภูมิหลังก่อนเรื่องหลัก · ข้อเสนอ</p><h3><a href="{base}wiki/{x['slug']}/">{e(x['title'])} ↗</a></h3><p>{e(x['summary'])}</p><div class="event-pressure"><span>แรงกดดันต่อโลก</span><p>{e(x['pressure'])}</p></div><div class="event-tags">{tags}</div><a class="text-link" href="{base}wiki/{x['slug']}/">อ่านเหตุการณ์และขอบเขตข้อมูล →</a></article>''')
        sections.append(f'<section class="event-group" id="event-group-{i}"><header><p class="eyebrow">บันทึกเหตุการณ์</p><h2>{e(kind)}</h2></header><div class="event-grid">{"".join(cards)}</div></section>')
    return f'''<section class="event-register" aria-label="ทะเบียนเหตุการณ์แฟนตาซี"><div class="event-register-intro"><strong>{len(data['events'])} เหตุการณ์</strong><p>{e(data['timingNote'])}</p><p>สถานะการออกแบบเป็นข้อเสนอ ส่วนความน่าเชื่อถือของคำกล่าวในโลกเรื่องระบุแยกในแต่ละหน้า ไม่มีลำดับเฉลยหรือผลลัพธ์อนาคตในทะเบียนนี้</p></div><nav class="act-jumps" aria-label="เลือกประเภทเหตุการณ์">{jumps}</nav>{''.join(sections)}</section>'''
