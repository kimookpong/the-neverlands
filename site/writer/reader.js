import {decryptVault} from './crypto.mjs';

const $ = id => document.getElementById(id);
const make = (tag, cls, text) => {const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;};
let book=null, selected='', chapter='1', documentPath='', activeView='read', attempt=0;
const chapters = () => book.acts.flatMap(a=>a.chapters.map(c=>({act:a,chapter:c})));
const current = () => {for(const row of chapters()){const episode=row.chapter.episodes.find(e=>e.id===selected);if(episode)return {...row,episode};}return null;};
const stages = { 'compact-first-draft':'ร่างแรกแบบกระชับ · สำหรับขยายและขัดเกลา', 'expanded-second-draft':'ร่างขยายรอบสอง · ยังขัดเกลาได้' };
function stage(ep){return stages[ep.draftStage]||'ร่างแรก · ยังขัดเกลาได้';}
function button(label, action, cls='quiet'){const e=make('button',cls,label);e.type='button';e.onclick=action;return e;}
function setView(view){
  if(!book)return;
  activeView=['outline','read','library'].includes(view)?view:'read';
  for(const b of document.querySelectorAll('[data-view]'))b.setAttribute('aria-pressed',String(b.dataset.view===activeView));
  for(const key of ['outline','read','library'])$('view-'+key).hidden=key!==activeView;
  if(activeView==='read')renderReading();else if(activeView==='outline'){renderTree();renderEpisode();}else renderDocuments();
}
function renderTree(){
  const q=$('outline-query').value.trim().toLocaleLowerCase(), root=$('outline-tree');root.replaceChildren();
  for(const act of book.acts){
    const matches=act.chapters.filter(c=>!q||JSON.stringify([act.title,c.title,c.purpose,c.episodes]).toLocaleLowerCase().includes(q));
    if(!matches.length)continue;
    const group=make('details','act-group');group.open=Boolean(q)||matches.some(c=>c.episodes.some(e=>e.id===selected));group.append(make('summary','',act.title));
    for(const c of matches){const chosen=c.episodes.some(e=>e.id===selected),b=button(`บท ${c.number} · ${c.title}`,()=>{selected=c.episodes[0].id;renderTree();renderEpisode();$('episode-detail').scrollIntoView({block:'start'});},'chapter-option'+(chosen?' active':''));if(chosen)b.setAttribute('aria-current','true');group.append(b);}
    root.append(group);
  }
  if(!root.childElementCount)root.append(make('p','empty','ไม่พบข้อมูลที่ค้นหา'));
}
function fact(label,value){const dl=make('div','fact');dl.append(make('dt','',label),make('dd','',value||'ยังไม่ระบุ'));return dl;}
function renderEpisode(){
  const row=current(),root=$('episode-detail');root.replaceChildren();if(!row)return;
  const {act,chapter:c,episode:ep}=row;
  root.append(make('p','eyebrow',act.title),make('h3','',`บท ${c.number} — ${c.title}`),make('p','chapter-purpose',c.purpose));
  const choices=make('nav','episode-selector');choices.setAttribute('aria-label','เลือกตอน');
  c.episodes.forEach((e,i)=>{const b=button(`ตอน ${c.number}.${i+1}`,()=>{selected=e.id;renderEpisode();},'');b.setAttribute('aria-pressed',String(e.id===selected));choices.append(b);});root.append(choices);
  const number=c.episodes.indexOf(ep)+1;
  root.append(make('h4','',`${c.number}.${number} · ${ep.title}`),make('p','draft-stage',stage(ep)));
  const facts=make('dl','facts');facts.append(fact('มุมมอง',ep.pov),fact('สถานที่',ep.location),fact('เวลาและลำดับ',ep.timeNote),fact('ผู้เกี่ยวข้อง',ep.characters.join(' · ')));root.append(facts);
  if(ep.continuity){const reference=make('section','reference');reference.append(make('strong','','เวลาและความรู้ในฉาก'),make('p','',ep.continuity.knowledgeChange),make('p','muted',ep.continuity.guard));root.append(reference);}
  const beats=make('dl','beats');
  for(const [key,label] of [['summary','เรื่องย่อ'],['goal','เป้าหมาย'],['conflict','ความขัดแย้ง'],['decision','การตัดสินใจ'],['outcome','ผลที่ตามมา'],['setup','สิ่งที่ปูไว้'],['questions','จุดที่ยังต้องตรวจ']]){if(!ep[key])continue;const item=make('div','beat');item.append(make('dt','',label),make('dd','',ep[key]));beats.append(item);}root.append(beats);
  root.append(button('อ่านต้นฉบับของบทนี้ ↗',()=>{chapter=String(c.number);setView('read');$('view-read').scrollIntoView({block:'start'});}));
}
function renderReading(){
  const rows=chapters(),select=$('chapter-select');select.replaceChildren();
  for(const [value,label] of [['all','ทุกบท'],['opening','บทเปิด 3–5']]){const option=make('option','',label);option.value=value;select.append(option);}
  for(const {chapter:c} of rows){const option=make('option','',`บท ${c.number} · ${c.title}`);option.value=String(c.number);select.append(option);}
  if(!['all','opening',...rows.map(r=>String(r.chapter.number))].includes(chapter))chapter=String(rows[0].chapter.number);
  select.value=chapter;
  const shown=rows.filter(r=>chapter==='all'||chapter==='opening'&&[3,4,5].includes(r.chapter.number)||String(r.chapter.number)===chapter);
  const count=shown.reduce((n,r)=>n+r.chapter.episodes.filter(e=>e.draft.trim()).length,0);
  $('reading-count').textContent=`${shown.length} บท · ${count} ตอน · อ่านจากข้อมูลฉบับเผยแพร่`;
  const root=$('manuscript'),toc=$('reading-toc');root.replaceChildren();toc.replaceChildren();
  for(const {act,chapter:c} of shown){
    const section=make('section','reading-chapter');section.id='read-'+c.id;section.append(make('p','eyebrow',act.title),make('h3','',`บท ${c.number} — ${c.title}`));
    const link=make('a','',`บท ${c.number} · ${c.title}`);link.href='#'+section.id;toc.append(link);
    c.episodes.forEach((ep,i)=>{if(!ep.draft.trim())return;const scene=make('section','reading-scene');scene.append(make('h4','',`${c.number}.${i+1} · ${ep.title}`),make('p','draft-stage',stage(ep)));
      const prose=make('div','prose');for(const p of ep.draft.trim().split(/\n\s*\n/))prose.append(make('p','',p));scene.append(prose);
      const links=make('div','scene-links');links.append(button('อ่านแผนตอนนี้ ↗',()=>{selected=ep.id;$('outline-query').value='';setView('outline');$('episode-detail').scrollIntoView({block:'start'});}));scene.append(links);section.append(scene);
    });root.append(section);
  }
}
function openDocument(path){documentPath=path;$('document-query').value='';setView('library');$('document-title').scrollIntoView({block:'start'});}
function inline(root,text){
  const pattern=/\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`/g;let offset=0;
  for(const m of text.matchAll(pattern)){
    root.append(document.createTextNode(text.slice(offset,m.index)));
    if(m[1]){const path=m[2].split(/[?#]/)[0].split('/').pop(),doc=book.documents.find(d=>d.path.split('/').pop()===path),c=path.match(/^chapter-(\d+)\.md$/);
      if(doc)root.append(button(m[1],()=>openDocument(doc.path),'inline-link'));
      else if(c||['full-manuscript.md','opening-03-05.md'].includes(path))root.append(button(m[1],()=>{chapter=c?String(Number(c[1])):path==='opening-03-05.md'?'opening':'all';setView('read');$('view-read').scrollIntoView({block:'start'});},'inline-link'));
      else root.append(document.createTextNode(m[1]));
    }else root.append(make(m[3]?'strong':'code','',m[3]||m[4]));
    offset=m.index+m[0].length;
  }root.append(document.createTextNode(text.slice(offset)));
}
function markdown(root,text){
  root.replaceChildren();const lines=text.replace(/\r/g,'').split('\n');let i=0;
  const cells=line=>line.trim().replace(/^\||\|$/g,'').split('|').map(s=>s.trim());
  while(i<lines.length){const line=lines[i].trim();if(!line||i===0&&line.startsWith('# ')){i++;continue;}
    const heading=line.match(/^(#{1,6})\s+(.+)/);if(heading){const h=make('h'+Math.min(heading[1].length+2,6));inline(h,heading[2]);root.append(h);i++;continue;}
    if(line.startsWith('|')&&i+1<lines.length&&/^\s*\|?[\s:|\-]+\|?\s*$/.test(lines[i+1])){
      const wrap=make('div','table-wrap'),table=make('table'),thead=make('thead'),tr=make('tr'),tbody=make('tbody');
      for(const value of cells(line)){const th=make('th');th.scope='col';inline(th,value);tr.append(th);}thead.append(tr);i+=2;
      while(i<lines.length&&lines[i].trim().startsWith('|')){const r=make('tr');for(const value of cells(lines[i])){const td=make('td');inline(td,value);r.append(td);}tbody.append(r);i++;}
      table.append(thead,tbody);wrap.append(table);root.append(wrap);continue;
    }
    const list=line.match(/^(-|\d+\.)\s+(.+)/);if(list){const ordered=list[1]!=='-',ul=make(ordered?'ol':'ul');while(i<lines.length){const m=lines[i].trim().match(ordered?/^\d+\.\s+(.+)/:/^-\s+(.+)/);if(!m)break;const li=make('li');inline(li,m[1]);ul.append(li);i++;}root.append(ul);continue;}
    const p=make('p');inline(p,line);root.append(p);i++;
  }
}
function renderDocuments(){
  const q=$('document-query').value.trim().toLocaleLowerCase(),matches=book.documents.filter(d=>(d.title+' '+d.text).toLocaleLowerCase().includes(q));
  if(!matches.some(d=>d.path===documentPath))documentPath=matches[0]?.path||'';
  $('document-count').textContent=`${matches.length} / ${book.documents.length} เอกสาร`;
  const list=$('document-list');list.replaceChildren();
  for(const doc of matches){const b=button('',()=>{documentPath=doc.path;renderDocuments();},'document-option'+(doc.path===documentPath?' active':''));b.append(make('strong','',doc.title),make('span','',doc.state));b.setAttribute('aria-pressed',String(doc.path===documentPath));list.append(b);}
  const doc=matches.find(d=>d.path===documentPath);$('document-title').textContent=doc?.title||'ไม่พบเอกสาร';$('document-state').textContent=doc?.state||'';
  if(doc)markdown($('document-content'),doc.text);else $('document-content').replaceChildren(make('p','empty','ลองเปลี่ยนคำค้นหา'));
}
function lock(){
  attempt++;book=null;selected='';documentPath='';chapter='1';
  for(const id of ['outline-tree','episode-detail','chapter-select','reading-toc','manuscript','document-list','document-content'])$(id).replaceChildren();
  for(const id of ['snapshot','reading-count','document-count','document-title','document-state'])$(id).textContent='';
  for(const id of ['password','outline-query','document-query'])$(id).value='';
  $('message').hidden=true;$('desk').hidden=true;$('lock').hidden=true;$('gate').hidden=false;
  $('unlock').disabled=false;$('unlock').textContent='เปิดห้องนักเขียน →';
}
$('unlock-form').onsubmit=async e=>{
  e.preventDefault();const id=++attempt;$('unlock').disabled=true;$('unlock').textContent='กำลังเปิดข้อมูล…';$('message').hidden=true;
  let password=$('password').value;$('password').value='';
  try{
    if(!crypto.subtle)throw new Error('unsupported');
    const response=await fetch(new URL('vault.json',location.href),{cache:'no-store',credentials:'omit'});
    if(!response.ok)throw new Error('network');
    const opened=await decryptVault(await response.json(),password);if(id!==attempt)return;book=opened;
    const rows=chapters(),episodes=rows.flatMap(r=>r.chapter.episodes);selected=episodes[0].id;chapter=String(rows[0].chapter.number);
    const expanded=episodes.filter(e=>e.draftStage==='expanded-second-draft').length;
    $('snapshot').textContent=`${rows.length} บท · ${episodes.length} ตอน · ร่างขยาย ${expanded} ตอน · ${book.documents.length} เอกสาร · ข้อมูลรุ่น ${book.revision}`;
    $('gate').hidden=true;$('desk').hidden=false;$('lock').hidden=false;setView('read');$('desk').scrollIntoView({block:'start'});
  }catch(error){if(id!==attempt)return;book=null;$('message').textContent=error.message==='unsupported'?'เบราว์เซอร์นี้ยังเปิดข้อมูลที่เข้ารหัสไม่ได้ กรุณาใช้เบราว์เซอร์รุ่นปัจจุบันผ่านที่อยู่เว็บที่ปลอดภัย':error.message==='network'||error instanceof TypeError?'โหลดไฟล์ข้อมูลไม่ได้ กรุณาตรวจการเชื่อมต่อแล้วลองใหม่':'รหัสผ่านไม่ถูกต้อง หรือไฟล์ข้อมูลไม่สมบูรณ์';$('message').hidden=false;}
  finally{password='';if(id===attempt){$('unlock').disabled=false;$('unlock').textContent='เปิดห้องนักเขียน →';}}
};
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>setView(b.dataset.view);
$('chapter-select').onchange=()=>{chapter=$('chapter-select').value;renderReading();};
$('outline-query').oninput=()=>{if(book)renderTree();};$('document-query').oninput=()=>{if(book)renderDocuments();};
$('lock').onclick=()=>{lock();$('password').focus();};
window.addEventListener('pagehide',lock);
