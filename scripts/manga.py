# -*- coding: utf-8 -*-
"""Render the public allowlist of author-approved manga episodes only."""
import html
import re
e=html.escape

def validate_manga(data,asset_root):
    assert data['visibility']=='public' and data['scope']=='approved-manga-only'
    episodes=data['episodes'];ids=[x['id'] for x in episodes]
    assert len(set(ids))==len(ids)
    for ep in episodes:
        assert re.fullmatch(r'\d+-\d+',ep['id']) and ep['status']=='published' and ep['approvedAt']
        assert ep['contentPages']>=10
        assert len(ep['pages'])==ep['contentPages']+1
        assert [p['number'] for p in ep['pages']]==list(range(len(ep['pages'])))
        assert ep['pages'][0]['kind']=='cover' and ep['cover']==ep['pages'][0]['src']
        for p in ep['pages']:
            assert p['kind']==('cover' if p['number']==0 else 'content')
            assert p['src'].startswith(f'assets/manga/episodes/{ep["id"]}/') and '..' not in p['src']
            assert p['width']>0 and p['height']>0 and (asset_root/p['src']).is_file()

def catalog(data,base):
    episodes=data['episodes']
    rows=''.join(f'<li><span class="manga-episode-number">{e(x["number"])}</span><div><h3><a href="{base}manga/{x["id"]}/">{e(x["title"])}</a></h3><p>{x["contentPages"]} หน้า · พร้อมหน้าปก</p></div><a class="manga-read-link" href="{base}manga/{x["id"]}/">อ่านตอนนี้ ↗</a></li>' for x in episodes)
    latest=episodes[-1] if episodes else None
    feature=f'<section class="manga-feature" aria-labelledby="manga-latest"><a class="manga-cover" href="{base}manga/{latest["id"]}/"><img src="{base}{latest["cover"]}" width="1024" height="1536" alt="ปกมังงะตอน {e(latest["number"])} {e(latest["title"])}" fetchpriority="high"></a><div><p class="eyebrow">ตอนล่าสุด · {e(latest["chapter"])}</p><h2 id="manga-latest"><span>ตอน {e(latest["number"])}</span>{e(latest["title"])}</h2><p>{e(latest["description"])}</p><p class="manga-length">{latest["contentPages"]} หน้าเนื้อหา + หน้าปก</p><a class="primary-button" href="{base}manga/{latest["id"]}/">อ่านตอนนี้ →</a></div></section>' if latest else '<p>กำลังเตรียมตอนแรก</p>'
    return f'<div class="listing-page manga-catalog"><header class="listing-header"><p class="eyebrow">เรื่องเล่าผ่านภาพขาวดำ</p><h1>มังงะ</h1><p>อ่านเดอะ เนเวอร์แลนด์สฉบับมังงะ แยกตามตอนและลำดับการเดินทาง</p><span class="listing-count">เผยแพร่แล้ว {len(episodes)} ตอน</span></header>{feature}<section class="manga-toc" aria-labelledby="manga-episodes"><h2 id="manga-episodes">ตอนทั้งหมด</h2><ol>{rows}</ol><p class="reader-note-copy">ตอนถัดไปอยู่ระหว่างจัดทำ</p></section></div>'

def episode_page(ep,data,base):
    episodes=data['episodes'];index=episodes.index(ep)
    prev=episodes[index-1] if index else None
    nxt=episodes[index+1] if index+1<len(episodes) else None
    previous=f'<a href="{base}manga/{prev["id"]}/">← ตอน {e(prev["number"])}</a>' if prev else '<span class="manga-nav-muted">ตอนแรก</span>'
    following=f'<a href="{base}manga/{nxt["id"]}/">ตอน {e(nxt["number"])} →</a>' if nxt else '<span class="manga-nav-muted">ตอนถัดไปกำลังจัดทำ</span>'
    nav=f'<nav class="manga-episode-nav" aria-label="เปลี่ยนตอน">{previous}<a href="{base}manga/">สารบัญตอน</a>{following}</nav>'
    jumps=''.join(f'<a href="#page-{p["number"]}">{e(p["label"])}</a>' for p in ep['pages'])
    images=''.join(f'<figure class="manga-reader-page" id="page-{p["number"]}"><a href="{base}{p["src"]}" target="_blank" rel="noopener" aria-label="เปิดภาพเต็ม ตอน {e(ep["number"])} {e(p["label"])}"><img src="{base}{p["src"]}" width="{p["width"]}" height="{p["height"]}" alt="ตอน {e(ep["number"])} {e(ep["title"])} · {e(p["label"])}" loading="{"eager" if p["number"]==0 else "lazy"}" decoding="async"></a><figcaption><span>{e(p["label"])}</span><a href="{base}{p["src"]}" target="_blank" rel="noopener">ดูภาพเต็ม ↗</a></figcaption></figure>' for p in ep['pages'])
    return f'<article class="manga-episode"><header class="manga-episode-header"><a class="text-link" href="{base}manga/">← มังงะทั้งหมด</a><p class="eyebrow">{e(ep["chapter"])} · ตอน {e(ep["number"])}</p><h1>{e(ep["title"])}</h1><p>{ep["contentPages"]} หน้าเนื้อหา + หน้าปก · เลื่อนลงเพื่ออ่านต่อ</p></header>{nav}<nav class="manga-page-jumps" aria-label="เลือกหน้า">{jumps}</nav><div class="manga-pages">{images}</div>{nav}<p class="manga-end">จบตอน {e(ep["number"])}</p><a class="manga-back-top" href="#main">กลับขึ้นด้านบน ↑</a></article>'
