(() => {
  'use strict';
  const themeButton = document.querySelector('#theme-toggle');
  function themeLabel() {
    const label = document.documentElement.dataset.theme === 'dark' ? 'เปลี่ยนเป็นโหมดสว่าง' : 'เปลี่ยนเป็นโหมดมืด';
    themeButton.setAttribute('aria-label', label);
    themeButton.title = label;
  }
  themeLabel();
  themeButton.addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]').content = theme === 'dark' ? '#121715' : '#f5f2ea';
    try { localStorage.setItem('neverlands-theme', theme); } catch (_) { /* Optional preference. */ }
    themeLabel();
  });

  const menu = document.querySelector('#menu-toggle');
  const overlay = document.querySelector('#nav-overlay');
  const sidebar = document.querySelector('#sidebar');
  function setMenu(open) {
    const mobile = matchMedia('(max-width: 900px)').matches;
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? 'ปิดสารบัญ' : 'เปิดสารบัญ');
    document.body.classList.toggle('menu-open', open);
    overlay.hidden = !open;
    sidebar.inert = mobile && !open;
    if (open) sidebar.querySelector('a').focus();
  }
  menu.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
  overlay.addEventListener('click', () => { setMenu(false); menu.focus(); });
  const mobileQuery = matchMedia('(max-width: 900px)');
  mobileQuery.addEventListener('change', () => setMenu(false));
  setMenu(false);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') {
      setMenu(false); menu.focus();
    }
    if (event.key === 'Tab' && document.body.classList.contains('menu-open')) {
      const links = [...sidebar.querySelectorAll('a,button')];
      const first = links[0], last = links[links.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    const editing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName) || document.activeElement.isContentEditable;
    if (event.key === '/' && !editing && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault(); document.querySelector('#header-search').focus();
    }
  });

  const query = document.querySelector('#wiki-query');
  if (!query) return;
  const select = document.querySelector('#search-category');
  const results = document.querySelector('#search-results');
  const status = document.querySelector('#search-status');
  const params = new URLSearchParams(location.search);
  query.value = params.get('q') || '';
  select.value = params.get('category') || '';
  let index = [];
  const normalize = value => value.normalize('NFC').toLocaleLowerCase('th').trim();

  function element(tag, className, text) {
    const el = document.createElement(tag);
    el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function render() {
    const terms = normalize(query.value).split(/\s+/).filter(Boolean);
    const matches = index.map(article => {
      const title = normalize(article.title + ' ' + article.subtitle);
      const haystack = normalize(title + ' ' + article.description + ' ' + article.text);
      return {article, matched: terms.every(term => haystack.includes(term)),
        score: terms.reduce((n,term) => n + (title.includes(term) ? 10 : 1),0)};
    }).filter(({article, matched}) => matched && (!select.value || article.category === select.value))
      .sort((a,b) => b.score - a.score);
    results.replaceChildren();
    status.textContent = `${terms.length ? 'พบ' : 'ทั้งหมด'} ${matches.length} บทความ`;
    for (const {article} of matches) {
      const link = element('a','article-card');
      link.href = article.url;
      const top = element('div','card-top');
      top.append(element('span','eyebrow',article.categoryTitle));
      const bottom = element('div','card-bottom');
      const badge = element('span',`status status--${article.status}`);
      badge.append(element('i',''),document.createTextNode(article.statusLabel));
      const arrow = element('span','card-arrow','↗');
      arrow.setAttribute('aria-hidden','true');
      bottom.append(badge,arrow);
      link.append(top,element('h3','',article.title),element('p','',article.description),bottom);
      results.append(link);
    }
    if (!matches.length) {
      const empty = element('div','search-empty');
      empty.append(element('h2','','ยังไม่พบบันทึกที่ตรงกัน'),element('p','','ลองเปลี่ยนคำค้น หรือล้างตัวกรองหมวดหมู่'));
      results.append(empty);
    }
    const next = new URLSearchParams();
    if (query.value.trim()) next.set('q',query.value.trim());
    if (select.value) next.set('category',select.value);
    history.replaceState(null,'',location.pathname + (next.size ? '?' + next : ''));
  }
  let debounce;
  query.addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(render,100); });
  select.addEventListener('change',render);
  query.form.addEventListener('submit',event => { event.preventDefault(); render(); });
  status.textContent = 'กำลังเปิดคลังบทความ…';
  fetch(document.body.dataset.base + 'search-index.json')
    .then(response => { if (!response.ok) throw new Error('Search unavailable'); return response.json(); })
    .then(data => { index = data; render(); })
    .catch(() => {
      status.textContent = 'โหลดการค้นหาไม่สำเร็จ ลองโหลดหน้าใหม่ หรือเลือกอ่านจากสารบัญ';
      const retry = element('button','primary-button','ลองอีกครั้ง');
      retry.addEventListener('click', () => location.reload());
      results.append(retry);
    });
})();
