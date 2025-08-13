(function(){
  const $ = (s,p=document)=>p.querySelector(s);
  const $$ = (s,p=document)=>Array.from(p.querySelectorAll(s));
  const cards = $$('.uzklausa-card');
  if (!cards.length) return;

  // formos kontrolės
  const F = {
    klientas: $('#f-klientas'),
    projektas: $('#f-projektas'),
    detale: $('#f-detale'),
    brezinys: $('#f-brezinys'),
    danga: $('#f-danga'),
    standartas: $('#f-standartas'),
    kabTipas: $('#f-kabinimo-tipas'),
    kabXYZ: $('#f-kabinimas-xyz'),
    metMin: $('#f-metinis-min'),  metMax: $('#f-metinis-max'),
    menMin: $('#f-menesis-min'),  menMax: $('#f-menesis-max'),
    parMin: $('#f-partija-min'),  parMax: $('#f-partija-max'),
    ploMin: $('#f-plotas-min'),   ploMax: $('#f-plotas-max'),
    svoMin: $('#f-svoris-min'),   svoMax: $('#f-svoris-max'),
    remMin: $('#f-reme-min'),     remMax: $('#f-reme-max'),
    fakMin: $('#f-faktinis-min'), fakMax: $('#f-faktinis-max'),
    uzkFrom: $('#f-uzklausa-from'), uzkTo: $('#f-uzklausa-to'),
    pasFrom: $('#f-pasiulymas-from'), pasTo: $('#f-pasiulymas-to'),
    pastabos: $('#f-pastabos'),
    clear: $('#f-clear'),
    count: $('#f-count'),
  };

  const sval = el => (el?.value||'').trim().toLowerCase();
  const nval = el => (el && el.value!=='') ? parseFloat(el.value) : null;
  const dval = el => (el && el.value) ? el.value : null;

  const hasText = (card, key, el) => { const v = sval(el); if(!v) return true; return (card.dataset[key]||'').toLowerCase().includes(v); };
  const inNum = (card, key, minEl, maxEl) => {
    const t = parseFloat(card.dataset[key]||''); const mn = nval(minEl), mx = nval(maxEl);
    if (mn!=null && !(t>=mn)) return false; if (mx!=null && !(t<=mx)) return false; return true;
  };
  const inDate = (card, key, fromEl, toEl) => {
    const d = (card.dataset[key]||''); const f = dval(fromEl), t = dval(toEl);
    if (f && d < f) return false; if (t && d > t) return false; return true;
  };

  function apply(){
    let shown = 0;
    cards.forEach(card=>{
      const ok =
        hasText(card,'klientas', F.klientas) &&
        hasText(card,'projektas',F.projektas) &&
        hasText(card,'detale',  F.detale) &&
        hasText(card,'brezinys',F.brezinys) &&
        hasText(card,'danga',   F.danga) &&
        hasText(card,'standartas',F.standartas) &&
        hasText(card,'kabinimotipas', F.kabTipas) &&
        hasText(card,'kabinimasxyz',  F.kabXYZ) &&

        inNum(card,'metinis', F.metMin, F.metMax) &&
        inNum(card,'menesis', F.menMin, F.menMax) &&
        inNum(card,'partija', F.parMin, F.parMax) &&
        inNum(card,'plotas',  F.ploMin, F.ploMax) &&
        inNum(card,'svoris',  F.svoMin, F.svoMax) &&
        inNum(card,'kiekisreme', F.remMin, F.remMax) &&
        inNum(card,'faktinisreme',F.fakMin, F.fakMax) &&

        inDate(card,'uzklausosdata', F.uzkFrom, F.uzkTo) &&
        inDate(card,'pasiulymodata', F.pasFrom, F.pasTo) &&

        hasText(card,'pastabos', F.pastabos);

      card.style.display = ok ? '' : 'none';
      if (ok) shown++;
    });
    if (F.count) F.count.textContent = `Rodoma: ${shown}`;
  }

  // įvykiai
  Object.values(F).forEach(el=>{
    if (!el || el === F.clear || el === F.count) return;
    el.addEventListener('input', apply);
    el.addEventListener('change', apply);
  });
  F.clear?.addEventListener('click', ()=>{
    Object.values(F).forEach(el=>{
      if (!el || el === F.clear || el === F.count) return;
      el.value = '';
    });
    apply();
  });

  apply();
})();
