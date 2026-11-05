(() => {
  'use strict';
  const payload = document.getElementById('atlas-data');
  if (!payload) return;
  const data = JSON.parse(payload.textContent);
  const map = document.getElementById('atlas-map');
  const picker = document.getElementById('atlas-region');
  const title = document.getElementById('atlas-region-title');
  const description = document.getElementById('atlas-region-text');
  const facts = document.getElementById('atlas-region-facts');
  const detail = document.getElementById('atlas-place-detail');
  const buttons = document.getElementById('atlas-place-buttons');
  const status = document.getElementById('atlas-selection-status');
  const zoomIn = document.getElementById('atlas-zoom-in');
  const zoomOut = document.getElementById('atlas-zoom-out');
  const regions = new Map(data.kingdoms.map(k => [k.id,k]));
  const places = new Map(data.places.map(p => [p.id,p]));
  const mappedCount = data.kingdoms.filter(k => k.mapped).length;
  const catalogSummary = `${data.kingdoms.length} อาณาจักร · ${mappedCount} แห่งมีผังข้อเสนอ`;
  const unmappedAlert = document.getElementById('atlas-unmapped-alert');
  const initial = new URLSearchParams(location.search);
  let selectedRegion = '', selectedPlace = '', zoom = 1, center = [720,520];

  function node(tag,className,text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function setView(x,y,nextZoom) {
    zoom = Math.max(1,Math.min(3.5,nextZoom));
    const width = 1440/zoom, height = 1040/zoom;
    const left = Math.max(0,Math.min(1440-width,x-width/2));
    const top = Math.max(0,Math.min(1040-height,y-height/2));
    center = [left+width/2,top+height/2];
    map.setAttribute('viewBox',`${left} ${top} ${width} ${height}`);
    zoomIn.disabled = zoom >= 3.5;
    zoomOut.disabled = zoom <= 1;
  }
  function fit(region) {
    if (!region || !region.mapped) { setView(720,520,1); return; }
    const [x,y,w,h] = region.view;
    setView(x+w/2,y+h/2,Math.min(1440/w,1040/h));
  }
  function updateURL() {
    const next = new URL(location.href);
    if (selectedRegion) next.searchParams.set('region',selectedRegion);
    else next.searchParams.delete('region');
    if (selectedPlace) next.searchParams.set('place',selectedPlace);
    else next.searchParams.delete('place');
    history.replaceState(null,'',next.pathname+next.search+next.hash);
  }
  function select(regionId,placeId='',fitMap=true) {
    const region = regions.get(regionId);
    const place = places.get(placeId);
    const regionPlaces = data.places.filter(p => p.kingdom === regionId);
    selectedRegion = region ? region.id : '';
    selectedPlace = place && place.kingdom === selectedRegion ? place.id : '';
    picker.value = selectedRegion;
    const schematic = region && region.mapConfidence === 'schematic';
    document.getElementById('atlas-inspector-kicker').textContent = region ? schematic ? 'เกาะปิด · ตำแหน่งและรูปร่างเสนอ' : `ภูมิภาคข้อเสนอ · ${regionPlaces.length} สถานที่` : catalogSummary;
    title.textContent = region ? region.title : 'โลกที่ต้องพึ่งพากัน';
    description.textContent = region ? region.summary || region.terrain : 'เลือกพื้นที่หรือชื่ออาณาจักรเพื่ออ่านรายละเอียด ทั้งเก้าแห่งมีตำแหน่งที่เสนอแล้ว ส่วนภายในเกาะปิดยังไม่เปิดเผย';
    unmappedAlert.hidden = !schematic;
    unmappedAlert.textContent = schematic ? `${region.title} แสดงตำแหน่งและชายฝั่งอย่างหยาบตามข้อเสนอ ภายในเกาะและตำแหน่งต้นไม้ในตำนานยังไม่เปิดเผย` : '';
    facts.replaceChildren(); buttons.replaceChildren(); detail.replaceChildren();
    detail.hidden = !selectedPlace;
    if (region) {
      for (const [label,key] of [['ตำแหน่ง','position'],['ภูมิอากาศ','climate'],['ฐานเศรษฐกิจ','resources'],['อำนาจต่อรอง','leverage'],['ข้อจำกัด','vulnerability']]) {
        const row = node('div'); row.append(node('dt','',label),node('dd','',region[key])); facts.append(row);
      }
      if (schematic) {
        const terrain = node('div'); terrain.append(node('dt','','ภูมิประเทศ'),node('dd','',region.terrain)); facts.append(terrain);
      }
      if (region.legend) {
        const legend = node('div'); legend.append(node('dt','','ตำนาน · ยังไม่ยืนยันความจริง'),node('dd','',region.legend)); facts.append(legend);
      }
      buttons.append(node('h4','','สถานที่สำคัญ'));
      if (schematic) buttons.append(node('p','atlas-no-location','ยังไม่เปิดเผยเมือง ท่าเรือ หรือสถานที่ภายในเกาะ ไม่มีหมุดยืนยันต้นไม้ในตำนาน'));
      for (const p of regionPlaces) {
        const button = node('button','atlas-place-button');
        button.type = 'button';
        button.append(node('span','',p.thai),node('small','',p.name));
        button.setAttribute('aria-pressed',String(p.id===selectedPlace));
        button.addEventListener('click',()=>select(region.id,p.id,false));
        buttons.append(button);
      }
      const link=node('a','text-link',`อ่านเรื่อง ${region.title} →`);
      link.href=document.body.dataset.base+`wiki/${region.id}/`;buttons.append(link);
    }
    if (selectedPlace) {
      detail.append(node('h4','',`${place.thai} · ${place.name}`),node('p','',place.role),node('p','',place.strategic),node('p','atlas-place-caveat',place.dependency));
    }
    for (const shape of map.querySelectorAll('.map-region')) {
      const active=shape.dataset.region===selectedRegion;
      shape.classList.toggle('is-active',active);
      shape.classList.toggle('is-muted',!!region && region.mapped && !active);
      shape.setAttribute('aria-pressed',String(active));
    }
    for (const marker of map.querySelectorAll('.map-place')) {
      const active=marker.dataset.region===selectedRegion;
      const current=marker.dataset.place===selectedPlace;
      marker.classList.toggle('is-active',active);
      marker.classList.toggle('is-muted',!!region && region.mapped && !active);
      marker.classList.toggle('is-selected',current);
      marker.setAttribute('aria-pressed',String(current));
    }
    if (fitMap) fit(region);
    status.textContent=selectedPlace ? `เลือก ${place.thai} ใน ${region.title}` : region ? schematic ? `เลือก ${region.title} · ภายในไม่เปิดเผย` : `เลือก ${region.title} · ${regionPlaces.length} สถานที่สำคัญ` : catalogSummary;
    updateURL();
  }
  function activate(target) {
    const marker=target.closest('[data-place]');
    if (marker) { const p=places.get(marker.dataset.place);select(p.kingdom,p.id);return; }
    const region=target.closest('.map-region');
    if (region) select(region.dataset.region);
  }
  map.addEventListener('click',event=>activate(event.target));
  map.addEventListener('keydown',event=>{
    if ((event.key==='Enter'||event.key===' ')&&event.target.closest('[role="button"]')) {event.preventDefault();activate(event.target);}
  });
  picker.addEventListener('change',()=>select(picker.value));
  zoomIn.addEventListener('click',()=>setView(...center,zoom*1.25));
  zoomOut.addEventListener('click',()=>setView(...center,zoom/1.25));
  document.getElementById('atlas-reset').addEventListener('click',()=>select(''));
  for (const [id,className,inverse] of [['atlas-terrain','hide-terrain',true],['atlas-trade','hide-trade',true],['atlas-migration','show-migration',false]]) {
    const input=document.getElementById(id);
    const apply=()=>map.classList.toggle(className,inverse?!input.checked:input.checked);
    input.addEventListener('change',apply);apply();
  }
  for (const button of document.querySelectorAll('[data-locate]')) {
    button.addEventListener('click',()=>{
      const p=places.get(button.dataset.locate);select(p.kingdom,p.id);
      document.querySelector('.atlas-heading').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
      map.querySelector(`[data-place="${p.id}"]`).focus({preventScroll:true});
    });
  }
  const initialPlace=places.get(initial.get('place'));
  select(initialPlace?initialPlace.kingdom:initial.get('region'),initialPlace?initialPlace.id:'');
})();
