/*
Failas: detaliu_registras/static/js/colfilters.js
Final v1 CBV suderinimas: Grupės, stulpelių meniu, „Tilpti lange“, tankio jungiklis, filtrų debounce, AJAX „Detaliau“.
*/

(function () {
  const LS_KEY = "uzklausos_state_final_v1";

  const S = {
    root: '.uzklausos-page',
    headRow: 'thead tr',
    head: 'thead th[data-col-index]',
    filter: 'thead .filters-row th[data-col-index]',
    cells: 'tbody td[data-col-index]',
    table: '.table',
    scroll: '.table-scroll',
    advanced: '[data-advanced="1"][data-col-index]',

    // Col menu
    colGrid: '.js-colvis-grid',
    colAll: '.js-col-all',
    colNone: '.js-col-none',
    colDefault: '.js-col-default',

    // Grupės
    toolbar: '.table-toolbar',
    groupsBox: '.groups',

    // Valdikliai
    densityBtn: '.js-density',
    advBtn: '.js-toggle-advanced',
    fitBtn: '.js-fit-toggle',
    fitStatus: '.js-fit-status',
  };

  const $  = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
  const on = (el, ev, fn) => el && el.addEventListener(ev, fn);
  const debounce = (fn, ms) => { let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), ms); }; };

  // ---------- Tema ----------
  function parseRGB(str){ const m=String(str).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i); return m?{r:+m[1],g:+m[2],b:+m[3]}:null; }
  function initTheme(){
    const root = $(S.root);
    if (!root || root.dataset.theme !== "auto") return;
    const probe = document.createElement("a"); probe.href="#"; probe.style.visibility="hidden"; document.body.appendChild(probe);
    const linkColor = getComputedStyle(probe).color; document.body.removeChild(probe);
    const body = getComputedStyle(document.body);
    root.style.setProperty('--chip-primary', linkColor);
    root.style.setProperty('--text', body.color);
    root.style.setProperty('--bg', body.backgroundColor || "#fff");
    root.style.setProperty('--font-family', body.fontFamily || "system-ui,-apple-system,Segoe UI,Roboto,Inter,Helvetica,Arial,sans-serif");
    const rgb = parseRGB(linkColor); if (rgb) root.style.setProperty('--chip-primary-soft', `rgba(${rgb.r},${rgb.g},${rgb.b},0.10)`);
  }

  // ---------- Būsena ----------
  function defaultState(){
    return {
      hidden: $$(S.advanced).map(x => +x.dataset.colIndex), // slėpti išplėstinius
      groupsOff: [],     // pvz., ['kainodara']
      autoFit: false,
      density: 'normal', // 'normal' | 'compact'
    };
  }
  function getState(){ try { return JSON.parse(localStorage.getItem(LS_KEY)||"null"); } catch { return null; } }
  function setState(st){ localStorage.setItem(LS_KEY, JSON.stringify(st)); }
  function ensureState(){ const s=getState(); if (s && Array.isArray(s.hidden) && Array.isArray(s.groupsOff) && 'autoFit' in s && s.density) return s; const d=defaultState(); setState(d); return d; }

  // ---------- Auto indeksai ----------
  function ensureColIndexAttributes(){
    const firstHeadRow = document.querySelector(S.headRow);
    if (!firstHeadRow) return;
    const ths = Array.from(firstHeadRow.children).filter(el => el.tagName === 'TH');
    ths.forEach((th,i) => { if (!th.dataset.colIndex) th.dataset.colIndex = String(i); });

    const filterRow = document.querySelector('thead .filters-row');
    if (filterRow) {
      const fths = Array.from(filterRow.children).filter(el => el.tagName === 'TH');
      fths.forEach((th,i) => { if (!th.dataset.colIndex) th.dataset.colIndex = String(i); });
    }
    document.querySelectorAll('tbody tr').forEach(tr => {
      const tds = Array.from(tr.children).filter(el => el.tagName === 'TD');
      tds.forEach((td,i) => { if (!td.dataset.colIndex) td.dataset.colIndex = String(i); });
    });
  }

  // ---------- Grupės ----------
  const GROUP_LABELS = { bendra:'Bendra', specs:'Specifikacija', kainodara:'Kainodara', gamyba:'Gamyba', logistika:'Logistika' };

  function upsertGroupsBox(){
    let box = $(S.groupsBox);
    const toolbar = $(S.toolbar);
    if (!box && toolbar) {
      box = document.createElement('div');
      box.className = 'groups';
      const badge = document.createElement('span'); badge.className='chip chip--badge'; badge.textContent='Grupės:'; box.appendChild(badge);
      toolbar.insertBefore(box, toolbar.firstChild);
    }
    return box;
  }

  function collectGroups(){
    const set = new Set();
    $$(S.head).forEach(th => { const g=(th.dataset.group||'').trim(); if (g) set.add(g); });
    return Array.from(set);
  }

  function buildGroupsUI(){
    const groups = collectGroups();
    const box = upsertGroupsBox(); if (!box) return;

    // paliekam „Grupės:“ žetoną
    const badge = Array.from(box.children).find(el => el.classList?.contains('chip--badge'));
    box.innerHTML = ''; if (badge) box.appendChild(badge);

    const st = ensureState();
    const off = new Set(st.groupsOff);

    if (!groups.length) {
      const note = document.createElement('span');
      note.className = 'chip chip--badge'; note.textContent = 'Nėra data-group';
      box.appendChild(note);
      return;
    }

    groups.forEach(g => {
      const btn = document.createElement('button');
      btn.type='button';
      btn.className='chip chip--ghost js-group-toggle';
      btn.dataset.group = g;
      btn.textContent = GROUP_LABELS[g] || g;
      if (!off.has(g)) btn.classList.add('is-on');
      box.appendChild(btn);
    });

    box.addEventListener('click', (e) => {
      const btn = e.target.closest('.js-group-toggle');
      if (!btn) return;
      const g = btn.dataset.group;
      const st = ensureState();
      const off = new Set(st.groupsOff);
      if (off.has(g)) { off.delete(g); btn.classList.add('is-on'); }
      else            { off.add(g);    btn.classList.remove('is-on'); }
      st.groupsOff = Array.from(off);
      setState(st);
      recomputeAndApply();
    });
  }

  function groupsHiddenIndices(){
    const st = ensureState();
    const off = new Set(st.groupsOff || []);
    if (!off.size) return new Set();

    const hidden = new Set();
    $$(S.head).forEach(th => {
      const idx = +th.dataset.colIndex;
      const grp = (th.dataset.group||'').trim();
      const pinned = th.dataset.pin === "1";
      if (grp && off.has(grp) && !pinned) hidden.add(idx);
    });
    return hidden;
  }

  // ---------- Column menu ----------
  function buildColMenu(){
    const grid = $(S.colGrid); if (!grid) return;
    const headerThs = $$(S.head);
    grid.innerHTML = '';

    if (!headerThs.length) {
      grid.innerHTML = '<div style="color:#6b7280; font-size:.9rem;">Nerasta stulpelių galvutėje. Patikrink THEAD.</div>';
      return;
    }

    headerThs.forEach(th => {
      const i = +th.dataset.colIndex;
      const label = th.textContent.trim() || `#${i+1}`;
      const isAdvanced = th.matches('[data-advanced="1"]');

      const wrap = document.createElement('label');
      wrap.className = 'colvis-item';

      const cb = document.createElement('input');
      cb.type='checkbox'; cb.className='js-col-toggle'; cb.dataset.colIndex=String(i);

      const span = document.createElement('span'); span.textContent = label;

      wrap.appendChild(cb); wrap.appendChild(span);

      if (isAdvanced) {
        const chip = document.createElement('span');
        chip.className='chip chip--badge'; chip.textContent='Išplėst.';
        wrap.appendChild(chip);
      }

      grid.appendChild(wrap);
    });

    $$(".js-col-toggle").forEach(cb => {
      on(cb, 'change', () => {
        const idx = +cb.dataset.colIndex;
        const st = ensureState();
        const hidden = new Set(st.hidden);
        cb.checked ? hidden.delete(idx) : hidden.add(idx);
        st.hidden = Array.from(hidden);
        setState(st);
        recomputeAndApply();
      });
    });
  }

  // ---------- Apply visibility ----------
  function applyVisibility(effectiveHidden){
    const hide = (el, on) => el && el.classList.toggle('hidden-col', !!on);
    $$(S.head).forEach(th   => hide(th,   effectiveHidden.has(+th.dataset.colIndex)));
    $$(S.filter).forEach(th => hide(th,   effectiveHidden.has(+th.dataset.colIndex)));
    $$(S.cells).forEach(td  => hide(td,   effectiveHidden.has(+td.dataset.colIndex)));
    // sync checkbox'ai
    $$(".js-col-toggle").forEach(cb => { const i=+cb.dataset.colIndex; cb.checked = !effectiveHidden.has(i); });
  }

  // ---------- Density ----------
  function applyDensity(density){
    const root = $(S.root);
    root.classList.toggle('density-compact', density === 'compact');
    root.classList.toggle('density-normal', density !== 'compact');
    const btn = $(S.densityBtn);
    if (btn) btn.textContent = 'Tankis: ' + (density === 'compact' ? 'Kompaktiškas' : 'Įprastas');
  }
  function initDensity(){
    const btn = $(S.densityBtn); if (!btn) return;
    on(btn, 'click', () => {
      const st = ensureState();
      st.density = st.density === 'compact' ? 'normal' : 'compact';
      setState(st);
      applyDensity(st.density);
    });
  }

  // ---------- AutoFit ----------
  function computeAutoHidden(manualHidden){
    const scroll = $(S.scroll), table = $(S.table);
    if (!scroll || !table) return new Set();

    const man = new Set(manualHidden);
    const candidates = $$(S.head).map(th => ({
      idx:+th.dataset.colIndex,
      prio:+(th.dataset.priority||3),
      pin: th.dataset.pin === "1"
    })).filter(c => !c.pin && !man.has(c.idx))
      .sort((a,b) => b.prio - a.prio);

    const tempHidden = new Set();
    const renderTemp = () => { const eff = new Set([...man, ...tempHidden]); applyVisibility(eff); };

    renderTemp();
    let guard = 0;
    while (table.scrollWidth > scroll.clientWidth && guard++ < 100) {
      const next = candidates.find(c => !tempHidden.has(c.idx));
      if (!next) break;
      tempHidden.add(next.idx);
      renderTemp();
    }
    return tempHidden;
  }
  function showFitStatus(n){ const b=$(S.fitStatus); if(!b) return; if(n>0){ b.style.display=""; b.textContent="Auto: "+n; } else { b.style.display="none"; b.textContent=""; } }

  // ---------- Recompute ----------
  function recomputeAndApply(){
    const st = ensureState();

    // 1) rankinis
    const manualHidden = new Set(st.hidden);

    // 2) grupės slėpimas
    groupsHiddenIndices().forEach(i => manualHidden.add(i));

    // 3) autoFit
    let autoHidden = new Set();
    if (st.autoFit) autoHidden = computeAutoHidden(manualHidden);

    // efektyvus
    const effective = new Set([...manualHidden, ...autoHidden]);
    applyVisibility(effective);
    showFitStatus(autoHidden.size || 0);
  }

  // ---------- Filtrai ----------
  function initFilters(){
    const form = document.getElementById('filters-form'); if (!form) return;
    const submit = debounce(() => {
      const url = new URL(window.location.href);
      url.searchParams.delete('page');
      const fd = new FormData(form);
      for (const [k, v] of fd.entries()) v ? url.searchParams.set(k, v) : url.searchParams.delete(k);
      window.location.assign(url.toString());
    }, 350);

    $$(".filters-row input").forEach(inp => {
      on(inp, 'input', submit);
      on(inp, 'keydown', e => { if (e.key === 'Enter') { e.preventDefault(); submit(); } });
    });
  }

  // ---------- AJAX „Detaliau“ ----------
  function insertLoadingRow(afterTr){
    const tr = document.createElement('tr'); tr.className='row-details loading';
    const td = document.createElement('td'); td.colSpan=100;
    td.innerHTML = '<div class="rd-loading"><span class="rd-spinner" aria-hidden="true"></span> Kraunama…</div>';
    tr.appendChild(td);
    afterTr.parentNode.insertBefore(tr, afterTr.nextSibling);
    return tr;
  }

  function initRowDetailsAjax(){
    document.addEventListener('click', async (e) => {
      const btn = e.target.closest('.js-row-details'); if (!btn) return;
      const tr = btn.closest('tr.data-row'); if (!tr) return;

      // Jei jau yra detalių eilutė (ir ne "loading") – toggle
      const next = tr.nextElementSibling;
      if (next && next.classList.contains('row-details') && !next.classList.contains('loading')) {
        const nowHidden = next.classList.toggle('hidden');
        btn.setAttribute('aria-expanded', nowHidden ? 'false' : 'true');
        return;
      }

      const url = btn.dataset.detailsUrl;
      if (!url) { console.warn('Nėra data-details-url'); return; }

      let loadingRow = next;
      if (!(loadingRow && loadingRow.classList.contains('row-details') && loadingRow.classList.contains('loading'))) {
        loadingRow = insertLoadingRow(tr);
      }

      try {
        const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const html = await resp.text();
        const tmp = document.createElement('tbody'); tmp.innerHTML = html.trim();
        const detailsTr = tmp.querySelector('tr.row-details') || tmp.firstElementChild;
        if (detailsTr) {
          loadingRow.replaceWith(detailsTr);
          btn.setAttribute('aria-expanded', 'true');
        } else {
          loadingRow.querySelector('td').innerHTML = '<div class="rd-error">Nepavyko atvaizduoti detalių.</div>';
          loadingRow.classList.remove('loading');
        }
      } catch (err) {
        console.error(err);
        loadingRow.querySelector('td').innerHTML = '<div class="rd-error">Klaida kraunant detales.</div>';
        loadingRow.classList.remove('loading');
      }
    });
  }

  // ---------- INIT ----------
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    ensureColIndexAttributes();

    buildGroupsUI();
    buildColMenu();
    initFilters();
    initRowDetailsAjax();
    initDensity();

    // Greitieji mygtukai
    on($(S.colAll), 'click', () => { const st=ensureState(); st.hidden=[]; setState(st); recomputeAndApply(); });
    on($(S.colNone),'click', () => { const st=ensureState(); st.hidden=$$(S.head).map(x=>+x.dataset.colIndex); setState(st); recomputeAndApply(); });
    on($(S.colDefault),'click', () => { const st=ensureState(); st.hidden=$$(S.advanced).map(x=>+x.dataset.colIndex); setState(st); recomputeAndApply(); });

    on($(S.advBtn), 'click', () => {
      const st = ensureState();
      const advIdx = new Set($$(S.advanced).map(x => +x.dataset.colIndex));
      const hidden = new Set(st.hidden);
      const allHidden = [...advIdx].every(i => hidden.has(i));
      allHidden ? advIdx.forEach(i => hidden.delete(i)) : advIdx.forEach(i => hidden.add(i));
      st.hidden = Array.from(hidden); setState(st); recomputeAndApply();
    });

    on($(S.fitBtn), 'click', () => {
      const st = ensureState();
      st.autoFit = !st.autoFit; setState(st);
      $(S.fitBtn)?.classList.toggle('is-active', !!st.autoFit);
      recomputeAndApply();
    });

    // Pradinė būsena
    const st = ensureState();
    applyDensity(st.density || 'normal');
    $(S.fitBtn)?.classList.toggle('is-active', !!st.autoFit);
    recomputeAndApply();
  });
})();
