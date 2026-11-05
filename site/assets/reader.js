(() => {
  'use strict';
  const payload=document.getElementById('reader-data');if(!payload)return;
  const data=JSON.parse(payload.textContent),people=new Map(data.characters.map(p=>[p.id,p]));
  const personPicker=document.getElementById('relation-person'),kindPicker=document.getElementById('relation-kind');
  const focus=document.getElementById('relation-focus'),results=document.getElementById('relation-results');
  const query=document.getElementById('cast-query'),affiliation=document.getElementById('cast-affiliation');
  const cards=[...document.querySelectorAll('.cast-card')];
  function node(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
  function photo(p){const img=node('img');img.src=p.portrait;img.alt='ภาพแนวคิดของ '+p.name;img.width=80;img.height=104;img.loading='lazy';return img;}
  function draw(){
    const p=people.get(personPicker.value);if(!p)return;
    focus.replaceChildren();results.replaceChildren();
    const a=node('a','focus-person');a.href=p.url;const copy=node('div');copy.append(node('small','','ตัวละครที่เลือก'),node('h3','',p.name),node('p','',p.role));a.append(photo(p),copy,node('span','','↗'));focus.append(a);
    const visible=data.relations.filter(r=>(r.source===p.id||r.target===p.id)&&(kindPicker.value==='all'||r.kind===kindPicker.value));
    for(const r of visible){const other=people.get(r.source===p.id?r.target:r.source);const link=node('a','connection-card '+r.kind);link.href=other.url;const text=node('div');text.append(node('span','relation-type '+r.kind,r.kind==='known'?'ความสัมพันธ์ที่เปิดเผย':'ความเกี่ยวข้องตามบทบาท'),node('h4','',other.name),node('strong','',r.label),node('p','',r.description));link.append(photo(other),text);results.append(link);}
    if(!visible.length)results.append(node('p','relation-empty','ยังไม่มีความเชื่อมโยงประเภทนี้ในขอบเขตข้อมูลที่เปิดเผย'));
    document.getElementById('relation-status').textContent=`${p.name} · ${visible.length} ความเชื่อมโยงในขอบเขตที่เลือก`;
    const u=new URL(location.href);u.searchParams.set('character',p.id);history.replaceState(null,'',u.pathname+u.search+u.hash);
  }
  function filter(){const q=query.value.trim().toLocaleLowerCase(),selected=affiliation.value;let n=0;for(const card of cards){const matches=(!q||card.textContent.toLocaleLowerCase().includes(q))&&(!selected||card.dataset.affiliation===selected);card.hidden=!matches;if(matches)n++;}document.getElementById('cast-status').textContent=n?`${n} ตัวละคร`:'ไม่พบตัวละครที่ตรงกับคำค้นหา';}
  personPicker.addEventListener('change',draw);kindPicker.addEventListener('change',draw);query.addEventListener('input',filter);affiliation.addEventListener('change',filter);
  for(const a of document.querySelectorAll('[data-focus-person]'))a.addEventListener('click',event=>{event.preventDefault();personPicker.value=a.dataset.focusPerson;draw();history.replaceState(null,'',location.pathname+location.search+'#connections');document.getElementById('connections').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});personPicker.focus({preventScroll:true});});
  const initial=new URLSearchParams(location.search).get('character');if(people.has(initial))personPicker.value=initial;draw();
})();
