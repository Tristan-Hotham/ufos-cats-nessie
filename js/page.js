/* UFOs, big cats and Nessie. Plain MapLibre base map (OpenFreeMap Positron) with three toggleable topics: UFO reports by
 * geocoded town (NUFORC), police force answers about big cat reports (WhatDoTheyKnow batch 666) and a Loch Ness panel with
 * the register's sightings by year. Counts only; no report text. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:600px)').matches;
  const fmt = n => Number(n).toLocaleString('en-GB');
  const UFO = '#5B3E9C', CAT = '#C07A12', NES = '#1F6E78';
  const RATE = ['#F2ECF7', '#D9CCEB', '#B49ED6', '#8A6BBE', '#5B3E9C', '#33205F'];
  let map = null, loch = null, S = null, GC = null, GF = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => { ct.classList.toggle('folded', f); document.getElementById('ctToggle').setAttribute('aria-expanded', !f); };
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));
  const inset = document.getElementById('inset');
  if (small) inset.classList.add('off');

  function pop(ll, h) { new maplibregl.Popup({ maxWidth: '320px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map); }
  function ufoPopup(p, ll) {
    pop(ll, `<b class="t">${esc(p.nm || 'Unnamed place')}</b><table><tr><td>UFO reports</td><td><b>${fmt(p.n)}</b></td></tr><tr><td>years</td><td>${p.y0 === p.y1 ? p.y0 : p.y0 + ' to ' + p.y1}</td></tr><tr><td>shapes</td><td>${esc(p.sh)}</td></tr></table>` +
      (p.nm === 'London' ? '<p class="nt">Most London reports are pinned to one central point.</p>' : '') +
      '<p class="nt">Reports to the National UFO Reporting Center placed at the town the witness named (planetsig/ufo-reports). Report text is not used.</p>');
  }
  function councilPopup(p, ll) {
    pop(ll, `<b class="t">${esc(p.n)}</b><table><tr><td>UFO reports</td><td><b>${fmt(p.c)}</b></td></tr><tr><td>per 100,000</td><td><b>${p.r.toFixed(2)}</b></td></tr><tr><td>people</td><td>${fmt(p.p)}</td></tr><tr><td>to a military airfield</td><td>${p.m.toFixed(0)} km</td></tr><tr><td>to a civil airport</td><td>${p.a.toFixed(0)} km</td></tr><tr><td>sky (mag/arcsec²)</td><td>${p.s.toFixed(2)}</td></tr></table><p class="nt">Distances from the council's central point. Population WorldPop 2023; sky brightness from Darkest skies (Hotham 2026).</p>`);
  }
  function forcePopup(p, ll) {
    let h = `<b class="t">${esc(p.force)}</b><p><b>${esc(p.lab)}</b></p>`;
    if (p.note) h += `<p class="nt" style="margin-top:0">${esc(p.note)}</p>`;
    let ys = p.ys; if (typeof ys === 'string') ys = JSON.parse(ys);
    if (ys) {
      h += '<table><tr>' + [2014, 2015, 2016, 2017, 2018, 2019].map(y => `<td>${y === 2019 ? '2019*' : y}</td>`).join('') + '</tr><tr>' + ys.map(v => `<td><b>${v}</b></td>`).join('') + '</tr></table>';
      if (p.rate !== null && p.rate !== undefined) h += `<p>${Number(p.rate).toFixed(2)} reports a year per 100,000 people, ${/Northern Ireland/.test(p.force) ? '2016' : '2014'} to 2018</p>`;
      h += '<p class="nt">* January to the date of the reply (spring 2019).</p>';
    }
    if (p.url) h += `<p class="nt"><a href="${esc(p.url)}" target="_blank" rel="noopener">The request and reply on WhatDoTheyKnow</a></p>`;
    pop(ll, h);
  }
  function bounds(f) {
    let b = [180, 90, -180, -90];
    (f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates).forEach(p => p[0].forEach(c => { b = [Math.min(b[0], c[0]), Math.min(b[1], c[1]), Math.max(b[2], c[0]), Math.max(b[3], c[1])]; }));
    return [[b[0], b[1]], [b[2], b[3]]];
  }
  function centre(f) { const b = bounds(f); return [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2]; }

  function setup() {
    const lbl = map.getStyle().layers.find(l => l.type === 'symbol');
    const before = lbl && lbl.id;
    // councils (UFO rate), off by default
    map.addSource('c', { type: 'geojson', data: GC });
    map.addLayer({ id: 'councils', type: 'fill', source: 'c', layout: { visibility: 'none' }, paint: { 'fill-color': ['step', ['get', 'r'], RATE[0], 0.5, RATE[1], 1.5, RATE[2], 3, RATE[3], 5, RATE[4], 8, RATE[5]], 'fill-opacity': 0.75 } }, before);
    map.addLayer({ id: 'councils-l', type: 'line', source: 'c', layout: { visibility: 'none' }, paint: { 'line-color': '#FFFFFF', 'line-width': 0.6 } }, before);
    // police forces (big cats), off by default
    GF.features.forEach(f => { const p = f.properties; p.k = p.st === 'released' ? (p.rate >= 0.3 ? 'r3' : p.rate >= 0.15 ? 'r2' : 'r1') : p.st; });
    map.addSource('f', { type: 'geojson', data: GF });
    map.addLayer({ id: 'forces', type: 'fill', source: 'f', layout: { visibility: 'none' }, paint: { 'fill-color': ['match', ['get', 'k'], 'r3', '#8A5208', 'r2', '#C07A12', 'r1', '#E3B262', 'nil', '#F1D9A6', 'refused', '#8C7B5A', 'not_held', '#B9AE96', '#E9E1CE'], 'fill-opacity': 0.72 } }, before);
    map.addLayer({ id: 'forces-l', type: 'line', source: 'f', layout: { visibility: 'none' }, paint: { 'line-color': '#5A4A30', 'line-width': 1.1 } }, before);
    // airfields
    const air = { type: 'FeatureCollection', features: S.air.map(a => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [a[1], a[0]] }, properties: { nm: a[2], k: a[3] } })) };
    map.addSource('a', { type: 'geojson', data: air });
    map.addLayer({ id: 'air', type: 'circle', source: 'a', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 3, 10, 6], 'circle-color': ['match', ['get', 'k'], 'civil', '#FFFFFF', '#C07A12'], 'circle-stroke-color': ['match', ['get', 'k'], 'civil', '#262019', '#FFFFFF'], 'circle-stroke-width': 1.3 } });
    // UFO points
    const uf = { type: 'FeatureCollection', features: S.ufo.map((u, i) => ({ type: 'Feature', id: i, geometry: { type: 'Point', coordinates: [u[1], u[0]] }, properties: { nm: u[2], n: u[3], y0: u[4], y1: u[5], sh: u[6] } })) };
    map.addSource('u', { type: 'geojson', data: uf });
    map.addLayer({ id: 'ufo', type: 'circle', source: 'u', paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, ['max', 3, ['*', 1.6, ['sqrt', ['get', 'n']]]], 10, ['max', 6, ['*', 3.2, ['sqrt', ['get', 'n']]]]],
      'circle-color': UFO, 'circle-opacity': 0.72, 'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 1 } });
    // Loch Ness marker on the main map
    map.addSource('ln', { type: 'geojson', data: { type: 'Feature', geometry: { type: 'Point', coordinates: [-4.45, 57.29] }, properties: {} } });
    map.addLayer({ id: 'loch', type: 'circle', source: 'ln', paint: { 'circle-radius': 8, 'circle-color': NES, 'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 2 } });
    map.on('click', 'loch', () => { inset.classList.remove('off'); document.getElementById('lyN').checked = true; setChip('nes', true); if (loch) loch.resize(); });
    // clicks
    map.on('click', e => {
      const f = map.queryRenderedFeatures(e.point, { layers: ['ufo', 'air', 'loch', 'councils', 'forces'].filter(id => map.getLayoutProperty(id, 'visibility') !== 'none') });
      if (!f.length) return;
      const top = f[0];
      if (top.layer.id === 'ufo') ufoPopup(top.properties, e.lngLat);
      else if (top.layer.id === 'air') pop(e.lngLat, `<b class="t">${esc(top.properties.nm)}</b><p>${top.properties.k === 'civil' ? 'Civil airport' : top.properties.k === 'usaf' ? 'Military airfield used by the US Air Force' : 'Military airfield'}</p><p class="nt">OurAirports (public domain).</p>`);
      else if (top.layer.id === 'councils') councilPopup(top.properties, e.lngLat);
      else if (top.layer.id === 'forces') forcePopup(top.properties, e.lngLat);
    });
    ['ufo', 'air', 'loch', 'councils', 'forces'].forEach(id => { map.on('mouseenter', id, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', id, () => map.getCanvas().style.cursor = ''); });
    // layer toggles
    const vis = (ids, on) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none'));
    const box = id => document.getElementById(id);
    box('lyU').addEventListener('change', e => { vis(['ufo'], e.target.checked); setChip('ufo', e.target.checked || box('lyR').checked); });
    box('lyR').addEventListener('change', e => { vis(['councils', 'councils-l'], e.target.checked); setChip('ufo', e.target.checked || box('lyU').checked); });
    box('lyA').addEventListener('change', e => vis(['air'], e.target.checked));
    box('lyF').addEventListener('change', e => { vis(['forces', 'forces-l'], e.target.checked); setChip('cat', e.target.checked); keyCats(e.target.checked); });
    box('lyN').addEventListener('change', e => { inset.classList.toggle('off', !e.target.checked); vis(['loch'], e.target.checked); setChip('nes', e.target.checked); if (loch) loch.resize(); });
    const symbols = map.getStyle().layers.filter(l => l.type === 'symbol').map(l => l.id);
    box('lyL').addEventListener('change', e => vis(symbols, e.target.checked));
    document.querySelectorAll('.chip[data-t]').forEach(b => b.addEventListener('click', () => {
      const on = b.getAttribute('aria-pressed') !== 'true';
      if (b.dataset.t === 'ufo') { box('lyU').checked = on; box('lyU').dispatchEvent(new Event('change')); if (!on) { box('lyR').checked = false; box('lyR').dispatchEvent(new Event('change')); } }
      if (b.dataset.t === 'cat') { box('lyF').checked = on; box('lyF').dispatchEvent(new Event('change')); }
      if (b.dataset.t === 'nes') { box('lyN').checked = on; box('lyN').dispatchEvent(new Event('change')); }
    }));
    search();
  }
  function setChip(t, on) { const b = document.querySelector(`.chip[data-t="${t}"]`); if (b) b.setAttribute('aria-pressed', on); }
  function keyCats(on) { ['kc1', 'kc2', 'kc3'].forEach(id => document.getElementById(id).style.display = on ? 'flex' : 'none'); }
  document.getElementById('insetX').addEventListener('click', () => { document.getElementById('lyN').checked = false; document.getElementById('lyN').dispatchEvent(new Event('change')); inset.classList.add('off'); setChip('nes', false); });

  function search() {
    const idx = [];
    S.ufo.forEach(u => { if (u[2]) idx.push({ k: norm(u[2]), t: u[2], sub: `${u[3]} UFO report${u[3] > 1 ? 's' : ''}`, ll: [u[1], u[0]], go: () => ufoPopup({ nm: u[2], n: u[3], y0: u[4], y1: u[5], sh: u[6] }, [u[1], u[0]]) }); });
    GC.features.forEach(f => idx.push({ k: norm(f.properties.n), t: f.properties.n, sub: 'council', f, go: () => councilPopup(f.properties, centre(f)) }));
    GF.features.forEach(f => idx.push({ k: norm(f.properties.force), t: f.properties.force, sub: 'police force', f, go: () => { document.getElementById('lyF').checked = true; document.getElementById('lyF').dispatchEvent(new Event('change')); forcePopup(f.properties, centre(f)); } }));
    idx.push({ k: 'loch ness nessie', t: 'Loch Ness', sub: 'Nessie panel', ll: [-4.45, 57.29], go: () => { document.getElementById('lyN').checked = true; document.getElementById('lyN').dispatchEvent(new Event('change')); } });
    const q = document.getElementById('q'), sug = document.getElementById('sug');
    let hits = [], cur = -1;
    function go(h) {
      sug.style.display = 'none'; q.value = h.t;
      if (h.f) map.fitBounds(bounds(h.f), { padding: small ? 30 : 80, maxZoom: 10 }); else map.flyTo({ center: h.ll, zoom: 10 });
      map.once('moveend', h.go);
    }
    q.addEventListener('input', () => {
      const v = norm(q.value.trim()); cur = -1;
      if (v.length < 2) { sug.style.display = 'none'; return; }
      const seen = new Set();
      hits = idx.filter(x => x.k.includes(v)).sort((a, b) => (b.k.startsWith(v) - a.k.startsWith(v)) || a.k.length - b.k.length).filter(x => { const k = x.t + x.sub; if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 8);
      sug.innerHTML = hits.map((h, i) => `<li role="option" data-i="${i}">${esc(h.t)} <span>${esc(h.sub)}</span></li>`).join('') || '<li>No match</li>';
      sug.style.display = 'block';
    });
    sug.addEventListener('click', e => { const li = e.target.closest('li[data-i]'); if (li) go(hits[+li.dataset.i]); });
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); cur = Math.max(0, Math.min(hits.length - 1, cur + (e.key === 'ArrowDown' ? 1 : -1))); sug.querySelectorAll('li').forEach((l, i) => l.setAttribute('aria-selected', i === cur)); }
      if (e.key === 'Enter' && hits.length) go(hits[Math.max(cur, 0)]);
      if (e.key === 'Escape') sug.style.display = 'none';
    });
  }

  function lochPanel() {
    loch = new maplibregl.Map({ container: 'lochmap', style: STYLE, center: [-4.47, 57.285], zoom: small ? 8.0 : 8.3, attributionControl: false, interactive: true });
    window.__loch = loch;
    loch.on('load', () => {
      const fc = { type: 'FeatureCollection', features: S.nessie_places.map(p => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [p[1], p[0]] }, properties: { nm: p[2], n: p[3], y0: p[4], y1: p[5] } })) };
      loch.addSource('p', { type: 'geojson', data: fc });
      loch.addLayer({ id: 'p', type: 'circle', source: 'p', paint: { 'circle-radius': ['max', 4, ['*', 2, ['sqrt', ['get', 'n']]]], 'circle-color': NES, 'circle-opacity': 0.8, 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2 } });
      loch.on('click', 'p', e => { const p = e.features[0].properties; new maplibregl.Popup({ maxWidth: '240px' }).setLngLat(e.lngLat).setHTML(`<b class="t">${esc(p.nm)}</b><p>${p.n} sighting${p.n > 1 ? 's' : ''} named here, ${p.y0} to ${p.y1}</p><p class="nt">Official Loch Ness Monster Sightings Register. Approximate positions.</p>`).addTo(loch); });
      loch.on('mouseenter', 'p', () => loch.getCanvas().style.cursor = 'pointer'); loch.on('mouseleave', 'p', () => loch.getCanvas().style.cursor = '');
    });
    // timeline
    const Y = S.nessie_years, ys = Object.keys(Y).map(Number), mx = Math.max(...Object.values(Y));
    const svg = document.getElementById('spark'), w = 300 / (2026 - 1900 + 1);
    let h = '';
    ys.forEach(y => { const v = Y[y], hh = v / mx * 54; h += `<rect data-y="${y}" x="${((y - 1900) * w).toFixed(2)}" y="${(58 - hh).toFixed(2)}" width="${(w * 0.85).toFixed(2)}" height="${hh.toFixed(2)}" fill="${NES}"></rect>`; });
    h += '<line id="cur" x1="0" x2="0" y1="0" y2="58" stroke="#B4442E" stroke-width="1.4"></line>';
    svg.innerHTML = h;
    const r = document.getElementById('yr'), lab = document.getElementById('yrlab');
    const upd = () => { const y = +r.value, v = Y[y] || 0; lab.textContent = `${y}: ${v} sighting${v === 1 ? '' : 's'}`; const x = (y - 1900 + 0.42) * w; const l = document.getElementById('cur'); l.setAttribute('x1', x); l.setAttribute('x2', x); };
    r.addEventListener('input', upd); upd();
    svg.addEventListener('click', e => { const b = svg.getBoundingClientRect(); r.value = Math.round(1900 + (e.clientX - b.left) / b.width * 127); upd(); });
  }

  const lb = document.getElementById('lyrBtn'), lp = document.getElementById('lp');
  lb.addEventListener('click', () => { const o = !lp.classList.contains('open'); lp.classList.toggle('open', o); lb.setAttribute('aria-expanded', o); });
  Promise.all([fetch('data/site.json').then(r => r.json()), fetch('data/map_councils.geojson').then(r => r.json()), fetch('data/map_forces.geojson').then(r => r.json())]).then(([s, gc, gf]) => {
    S = s; GC = gc; GF = gf;
    map = new maplibregl.Map({ container: 'map', style: STYLE, bounds: [[-8.7, 49.8], [1.9, 59.4]], fitBoundsOptions: { padding: small ? 10 : 30 }, attributionControl: { compact: true }, minZoom: 3.5, maxZoom: 14 });
    window.__map = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.on('load', () => { document.getElementById('nojs').style.display = 'none'; setup(); });
    lochPanel();
  }).catch(() => { document.getElementById('nojs').textContent = 'The map data could not be loaded.'; });
})();
