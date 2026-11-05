#!/usr/bin/env python3
"""Build the reader wiki from explicitly public content/ data and site/ assets."""
import argparse
import html
import json
import os
from pathlib import Path
import re
import shutil
from atlas import atlas_block, render_svg
from pronunciation import annotate_data, annotate_html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
DATA = json.loads((ROOT / 'content/wiki.json').read_text())
ATLAS = json.loads((ROOT / 'content/atlas.json').read_text())
ARTICLES = {a['slug']: a for a in DATA['articles']}
CATEGORIES = {c['id']: c for c in DATA['categories']}
STATUS = {'established': 'ข้อมูลพื้นฐาน', 'working': 'ชื่อชั่วคราว',
          'developing': 'อยู่ระหว่างออกแบบ', 'in-world': 'เรื่องเล่าทางการ',
          'proposed': 'ข้อเสนอ · ยังไม่ล็อก Canon'}
ICONS = {
 'world': '◎', 'history': '⌛', 'kingdoms': '♜', 'characters': '♙',
 'peoples': '❋', 'magic': '✧', 'technology': '⚒', 'timeline': '◷', 'atlas': '⌖',
}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-path', default=os.environ.get('BASE_PATH', '/the-neverlands/'))
args = parser.parse_args()
BASE = '/' + args.base_path.strip('/') + '/' if args.base_path.strip('/') else '/'
ORIGIN = 'https://kimookpong.github.io'
e = html.escape


def url(path=''):
    return BASE + path.lstrip('/')


def article_url(slug):
    return url(f'wiki/{slug}/')


def badge(article):
    return f'<span class="status status--{e(article["status"])}"><i></i>{STATUS[article["status"]]}</span>'


def card(article, index=None):
    category = CATEGORIES[article['category']]
    num = f'<span class="card-number">{index:02d}</span>' if index else ''
    return f'''<a class="article-card" href="{article_url(article['slug'])}">
      <div class="card-top"><span class="eyebrow">{e(category['english'])}</span>{num}</div>
      <h3>{e(article['title'])}</h3><p>{e(article['description'])}</p>
      <div class="card-bottom">{badge(article)}<span class="card-arrow" aria-hidden="true">↗</span></div>
    </a>'''


def shell(title, description, body, path='', category='', page_type='website', crumbs='หน้าหลัก'):
    nav = ''.join(f'''<a class="nav-link {'active' if category == c['id'] else ''}"
        href="{url('categories/'+c['id']+'/')}" {'aria-current="page"' if category == c['id'] else ''}>
        <span class="nav-icon" aria-hidden="true">{ICONS[c['id']]}</span><span>{e(c['title'])}</span>
        <span class="nav-count">{sum(a['category'] == c['id'] for a in ARTICLES.values()):02d}</span></a>'''
        for c in CATEGORIES.values())
    full_title = 'The Neverlands — Wiki' if not path else f'{title} | The Neverlands Wiki'
    canonical = ORIGIN + url(path)
    return f'''<!doctype html>
<html lang="th" data-theme="dark">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="{url('assets/theme.js')}"></script>
  <title>{e(full_title)}</title><meta name="description" content="{e(description)}">
  <meta name="theme-color" content="#121715">
  <meta property="og:title" content="{e(full_title)}"><meta property="og:description" content="{e(description)}">
  <meta property="og:type" content="{page_type}"><meta property="og:locale" content="th_TH">
  <meta property="og:url" content="{canonical}"><meta property="og:site_name" content="The Neverlands Wiki">
  <meta property="og:image" content="{ORIGIN + url('assets/social-card.png')}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{canonical}"><link rel="icon" type="image/svg+xml" href="{url('assets/favicon.svg')}">
  <link rel="stylesheet" href="{url('assets/styles.css')}">
  <link rel="stylesheet" href="{url('assets/atlas.css')}">
  <script defer src="{url('assets/app.js')}"></script>
</head>
<body data-base="{BASE}">
<a class="skip-link" href="#main">ข้ามไปยังเนื้อหา</a>
<div class="mobile-bar"><a class="mobile-brand" href="{url()}">THE NEVERLANDS</a>
  <button class="icon-button" id="menu-toggle" aria-expanded="false" aria-controls="sidebar" aria-label="เปิดสารบัญ">☰</button></div>
<button class="nav-overlay" id="nav-overlay" aria-label="ปิดสารบัญ" hidden></button>
<aside class="sidebar" id="sidebar" aria-label="สารบัญ Wiki">
  <a class="brand" href="{url()}"><span class="brand-seal" aria-hidden="true">N</span>
    <span class="brand-title">THE NEVERLANDS<span class="brand-caption">บันทึกโลกและเรื่องเล่า</span></span></a>
  <div class="sidebar-rule"><span>สารานุกรมสำหรับผู้อ่าน</span><span>ฉบับ 01</span></div>
  <nav aria-label="หมวดบทความ">
    <a class="nav-link {'active' if not path else ''}" href="{url()}" {'aria-current="page"' if not path else ''}><span class="nav-icon" aria-hidden="true">⌂</span><span>หน้าหลัก</span></a>
    <p class="nav-label">สำรวจจักรวาล</p>{nav}
  </nav>
  <div class="sidebar-bottom"><a class="about-link" href="{article_url('about')}">เกี่ยวกับ Wiki <span aria-hidden="true">↗</span></a>
    <div class="work-status"><span class="status-dot"></span>โลกนี้กำลังเติบโต<span>บันทึกโลก · รุ่น {e(DATA['version'])}</span></div></div>
</aside>
<div class="workspace">
  <header class="topbar"><div class="breadcrumb"><span>คลังบันทึก</span><span aria-hidden="true">/</span><span>{e(crumbs)}</span></div>
    <div class="topbar-actions"><form class="search-shortcut" action="{url('search/')}" role="search"><label for="header-search" class="sr-only">ค้นหาใน Wiki</label><span aria-hidden="true">⌕</span><input id="header-search" name="q" placeholder="ค้นหาในจักรวาลนี้…" autocomplete="off"><kbd>/</kbd></form>
    <button id="theme-toggle" class="icon-button theme-toggle" aria-label="เปลี่ยนเป็นโหมดสว่าง" title="เปลี่ยนธีม">◐</button></div>
  </header>
  <main id="main" tabindex="-1">{body}</main>
  <footer class="footer"><a href="{url()}">THE NEVERLANDS</a><span>จักรวาลที่กำลังถูกเขียนขึ้น · สารานุกรมผู้อ่าน รุ่น {e(DATA['version'])}</span><a href="{article_url('about')}">ขอบเขตข้อมูล <span aria-hidden="true">↗</span></a></footer>
</div>
</body></html>'''


def home():
    category_cards = ''.join(f'''<a class="category-card" href="{url('categories/'+c['id']+'/')}">
        <span class="category-symbol" aria-hidden="true">{ICONS[c['id']]}</span>
        <div><span class="eyebrow">{e(c['english'])}</span><h3>{e(c['title'])}</h3><p>{e(c['description'])}</p></div>
        <span class="category-next" aria-hidden="true">↗</span></a>''' for c in CATEGORIES.values())
    kingdoms = ''.join(f'''<a class="kingdom-link" href="{article_url(a['slug'])}"><span class="kingdom-order">{n:02d}</span><span><strong>{e(a['title'])}</strong><small>{e(a['subtitle'])}</small></span><span aria-hidden="true">↗</span></a>'''
        for n, a in enumerate((a for a in ARTICLES.values() if a['category'] == 'kingdoms'), 1))
    body = f'''<div class="home-page">
      <section class="hero" aria-labelledby="hero-title">
        <div class="hero-copy"><p class="hero-kicker"><span></span> แฟนตาซีการเมืองในโลกต้นฉบับ</p>
        <h1 id="hero-title" data-reading-ready="true">The<br><em>Neverlands</em><span class="hero-period">.</span><small class="hero-pronunciation">(เดอะ เนเวอร์แลนด์ส)</small></h1>
        <p class="hero-thai">ทุกอาณาจักรมีประวัติศาสตร์<br>ทุกบัลลังก์มีราคา</p>
        <p class="hero-description">สำรวจดินแดน ผู้คน และความเชื่อ<br class="desktop-break">ในโลกที่อำนาจเปลี่ยนชะตาของทุกชีวิต</p>
        <a class="primary-button" href="{article_url('world')}">เริ่มสำรวจโลก <span aria-hidden="true">↗</span></a></div>
        <div class="hero-art" aria-hidden="true"><img src="{url('assets/compass.svg')}" alt="" width="600" height="600"><span class="art-label">ดินแดนที่รอการสำรวจ</span></div>
        <div class="hero-bottom"><span>บันทึกโลกและเรื่องเล่า</span><span>การเมือง · ประวัติศาสตร์ · แฟนตาซี</span><span>บันทึกโลกฉบับ 0.1</span></div>
      </section>
      <div class="intro-strip"><div><span class="small-star" aria-hidden="true">✧</span><p>คู่มือสำหรับผู้อ่าน <span>รู้จักโลก โดยไม่เปิดเผยความลับของเรื่อง</span></p></div><a href="{article_url('about')}">เกี่ยวกับ Wiki <span aria-hidden="true">→</span></a></div>
      <section class="section" aria-labelledby="start-heading"><div class="section-heading"><div><p class="eyebrow">ก้าวแรกสู่จักรวาลนี้</p><h2 id="start-heading">เริ่มต้นที่นี่</h2></div><span class="section-note">สามบทความเพื่อรู้จักจักรวาลนี้</span></div>
      <div class="featured-grid">{''.join(card(ARTICLES[s],i) for i,s in enumerate(['world','seven-kingdoms','caelan'],1))}</div></section>
      <section class="section" aria-labelledby="explore-heading"><div class="section-heading"><div><p class="eyebrow">สำรวจคลังบันทึก</p><h2 id="explore-heading">เปิดบันทึกของโลก</h2></div><span class="section-note">{len(ARTICLES)} บทความ · {len(CATEGORIES)} หมวดหมู่</span></div><div class="category-grid">{category_cards}</div></section>
      <section class="kingdom-section" aria-labelledby="kingdom-heading"><div class="kingdom-intro"><p class="eyebrow">โลกของเก้าอาณาจักร</p><h2 id="kingdom-heading">เก้าอาณาจักร<br><em>หลายรูปแบบของอำนาจ</em></h2><p>จากราชวงศ์เก่าแก่ถึงดินแดนปิด<br>จากเมืองท่าถึงอาณาจักรไร้กษัตริย์<br>แต่ละดินแดนมีบทบาทของตนเอง</p><span class="inline-note">ชื่อทั้งหมดเป็นชื่อชั่วคราว</span><a class="text-link" href="{article_url('seven-kingdoms')}">อ่านภาพรวม <span aria-hidden="true">→</span></a></div><div class="kingdom-list">{kingdoms}</div></section>
      <aside class="editorial-note"><span aria-hidden="true">✦</span><div><h2>โลกนี้ยังอยู่ระหว่างการเขียน</h2><p>ชื่อ ตัวละคร และรายละเอียดบางส่วนอาจเปลี่ยนแปลง แผนที่ข้อเสนอรุ่น 0.1 มีสถานที่สำคัญ 35 แห่งให้สำรวจ โดยยังไม่ล็อกชื่อหรือพรมแดน</p></div><a href="{article_url('atlas')}">สำรวจแผนที่ <span aria-hidden="true">↗</span></a></aside>
    </div>'''
    return shell('The Neverlands', 'Wiki ภาษาไทยสำหรับผู้อ่าน The Neverlands สำรวจโลก เก้าอาณาจักร ตัวละคร และเวทมนตร์ โดยไม่เปิดเผยความลับหรือตอนจบ', body)


def article_page(a):
    c = CATEGORIES[a['category']]
    sections = ''.join(f'''<section class="prose-section" id="section-{i}"><h2>{e(s['heading'])}</h2>{''.join('<p>'+e(p)+'</p>' for p in s['paragraphs'])}</section>'''
        for i,s in enumerate(a['sections'],1))
    toc = ''.join(f'<a href="#section-{i}">{e(s["heading"])}</a>' for i,s in enumerate(a['sections'],1))
    facts = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in a['facts'])
    related = ''.join(card(ARTICLES[s]) for s in a['related'])
    atlas = atlas_block(ATLAS,BASE) if a['slug'] == 'atlas' else ''
    has_map = next((k['mapped'] for k in ATLAS['kingdoms'] if k['id']==a['slug']),False)
    map_label = 'ดูตำแหน่งและสถานที่สำคัญบนแผนที่ข้อเสนอ' if has_map else 'ดูสถานะข้อมูลในคลังแผนที่'
    map_link = f'<a class="kingdom-map-link" href="{article_url("atlas")}?region={a["slug"]}">{map_label} ↗</a>' if a['category'] == 'kingdoms' else ''
    body = f'''<article class="article-page {'atlas-article' if atlas else ''}"><div class="article-breadcrumb"><a href="{url()}">Wiki</a><span>/</span><a href="{url('categories/'+c['id']+'/')}">{e(c['title'])}</a></div>
      <header class="article-header"><p class="eyebrow">{e(a['subtitle'])}</p><h1>{e(a['title'])}</h1><p class="article-lead">{e(a['description'])}</p><div class="article-meta">{badge(a)}<span>ข้อมูลสำหรับผู้อ่าน</span><span>Wiki รุ่น {e(DATA['version'])}</span></div>{map_link}</header>
      {atlas}
      <div class="article-layout"><div class="prose">{sections}</div><aside class="article-aside"><div class="toc"><p class="eyebrow">ในหน้านี้</p><h2>ในบทความนี้</h2>{toc}</div>{'<dl class="fact-box">'+facts+'</dl>' if facts else ''}<div class="reader-note"><span aria-hidden="true">✧</span><p>แสดงเฉพาะข้อมูลที่เปิดเผยได้<br>ไม่รวมความลับและตอนจบ</p></div></aside></div>
      <section class="related-section"><div class="section-heading"><div><p class="eyebrow">สำรวจต่อ</p><h2>บันทึกที่เกี่ยวข้อง</h2></div></div><div class="related-grid">{related}</div></section>
    </article>'''
    return shell(a['title'],a['description'],body,f'wiki/{a["slug"]}/',a['category'],'article',c['title'])


def category_page(c):
    articles = [a for a in ARTICLES.values() if a['category'] == c['id']]
    body = f'''<div class="listing-page"><header class="listing-header"><p class="eyebrow">{e(c['english'])}</p><h1>{e(c['title'])}</h1><p>{e(c['description'])}</p><span class="listing-count">{len(articles):02d} บทความในหมวดนี้</span></header><div class="listing-grid">{''.join(card(a) for a in articles)}</div></div>'''
    return shell(c['title'],c['description'],body,f'categories/{c["id"]}/',c['id'],crumbs=c['title'])


def search_page():
    opts = ''.join(f'<option value="{c["id"]}">{e(c["title"])}</option>' for c in CATEGORIES.values())
    body = f'''<div class="search-page"><header class="listing-header"><p class="eyebrow">ค้นหาในคลังบันทึก</p><h1>ค้นหาในจักรวาลนี้</h1><p>ค้นหาชื่อดินแดน ตัวละคร หรือเรื่องที่อยากรู้</p></header>
      <form class="search-form" action="{url('search/')}" role="search"><label class="sr-only" for="wiki-query">คำค้นหา</label><div class="search-input-wrap"><span aria-hidden="true">⌕</span><input id="wiki-query" name="q" type="search" placeholder="ลองค้นหา Myrthen, เวทมนตร์, การค้า…" autocomplete="off"><button class="primary-button" type="submit">ค้นหา</button></div>
      <div class="search-controls"><label for="search-category">หมวดหมู่</label><select id="search-category" name="category"><option value="">ทุกหมวดหมู่</option>{opts}</select><p id="search-status" role="status" aria-live="polite">เปิด JavaScript เพื่อค้นหาบทความ</p></div></form>
      <div class="listing-grid" id="search-results"></div><noscript><p>คุณสามารถอ่านบทความทั้งหมดผ่านสารบัญหมวดหมู่ได้ แม้ไม่เปิด JavaScript</p></noscript></div>'''
    return shell('ค้นหา','ค้นหาบทความใน The Neverlands Wiki',body,'search/',crumbs='ค้นหาบทความ')


def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(annotate_html(content) if path.endswith('.html') else content)


def validate():
    if ATLAS['visibility'] != 'public' or ATLAS['status'] != 'proposed':
        raise ValueError('Atlas must be explicitly public and proposed')
    if len(ARTICLES) != len(DATA['articles']):
        raise ValueError('Duplicate article slugs')
    for a in ARTICLES.values():
        if a['visibility'] != 'public':
            raise ValueError(f'Non-public article in public content: {a["slug"]}')
        if not re.fullmatch(r'[a-z0-9-]+',a['slug']):
            raise ValueError('Invalid slug')
        if a['category'] not in CATEGORIES or a['status'] not in STATUS:
            raise ValueError('Invalid category or status')
        for slug in a['related']:
            if slug not in ARTICLES:
                raise ValueError(f'Broken related article: {slug}')


def main():
    validate()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT/'site/assets',OUT/'assets')
    write('assets/neverlands-atlas.svg',render_svg(ATLAS,interactive=False))
    write('index.html',home())
    for a in ARTICLES.values():
        write(f'wiki/{a["slug"]}/index.html',article_page(a))
    for c in CATEGORIES.values():
        write(f'categories/{c["id"]}/index.html',category_page(c))
    write('search/index.html',search_page())
    write('404.html',shell('ไม่พบบันทึก','ไม่พบบทความที่ต้องการ',f'<div class="not-found"><p class="eyebrow">404 · ยังไม่มีบันทึก</p><h1>ยังไม่มีบันทึกหน้านี้</h1><p>ลิงก์อาจเปลี่ยนไป หรือบทความนี้ยังไม่ได้ถูกเขียน</p><a class="primary-button" href="{url()}">กลับหน้าหลัก <span aria-hidden="true">→</span></a></div>','404.html',crumbs='ไม่พบบทความ'))
    index = [dict(slug=a['slug'],title=a['title'],subtitle=a['subtitle'],description=a['description'],
        category=a['category'],categoryTitle=CATEGORIES[a['category']]['title'],
        statusLabel=STATUS[a['status']],status=a['status'],url=article_url(a['slug']),
        text=' '.join(p for s in a['sections'] for p in s['paragraphs']) +
        (' ' + ' '.join(p['name']+' '+p['thai']+' '+p['role']+' '+p['strategic'] for p in ATLAS['places']) if a['slug']=='atlas' else '')) for a in ARTICLES.values()]
    write('search-index.json',json.dumps(annotate_data(index),ensure_ascii=False))
    paths = ['']+[f'wiki/{a}/' for a in ARTICLES]+[f'categories/{c}/' for c in CATEGORIES]
    write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN}{url(p)}</loc></url>' for p in paths)+'</urlset>')
    write('robots.txt',f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}{url("sitemap.xml")}\n')
    write('.nojekyll','')
    print(f'Built {len(ARTICLES)} public articles, {len(CATEGORIES)} categories → {OUT} (base {BASE})')


if __name__ == '__main__':
    main()
