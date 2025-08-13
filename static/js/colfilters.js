// Automatiniai filtrai pagal <th data-type="..."> visoms kolonoms.
(function () {
  const tableEl = document.getElementById('main-table');
  if (!tableEl) return;

  const headRow   = tableEl.querySelector('thead tr.head');
  const filterRow = tableEl.querySelector('thead tr.filters');
  filterRow.innerHTML = '';

  // 1) Sugeneruojam filtrų eilę
  [...headRow.children].forEach((th) => {
    const cell = document.createElement('th');
    const type = th.dataset.type || 'text';
    if (type === 'none') { filterRow.appendChild(cell); return; }

    if (type === 'select') {
      const sel = document.createElement('select');
      sel.innerHTML = `<option value="">Visi</option>`;
      const choicesAttr = th.getAttribute('data-choices');
      if (choicesAttr) { try { JSON.parse(choicesAttr).forEach(v => sel.innerHTML += `<option>${v}</option>`); } catch(e){} }
      cell.appendChild(sel);
    } else if (type === 'date') {
      cell.innerHTML = `<div class="rng"><input type="date" data-op="gte"><span>–</span><input type="date" data-op="lte"></div>`;
    } else if (type === 'number') {
      cell.innerHTML = `<div class="rng"><input type="number" step="any" data-op="gte" placeholder="nuo"><span>–</span><input type="number" step="any" data-op="lte" placeholder="iki"></div>`;
    } else {
      cell.innerHTML = `<input type="text" placeholder="Filtruoti…">`;
    }
    filterRow.appendChild(cell);
  });

  // 2) Paprastas (be DataTables) filtravimas
  function rowVisible(tr){
    return [...filterRow.children].every((th, i) => {
      const type = headRow.children[i].dataset.type || 'text';
      const cell = tr.children[i];
      const text = (cell ? cell.textContent : '').trim();
      if (type === 'none') return true;
      if (type === 'select') {
        const v = th.querySelector('select').value;
        return !v || text === v;
      }
      if (type === 'number' || type === 'date') {
        const min = th.querySelector('input[data-op="gte"]').value;
        const max = th.querySelector('input[data-op="lte"]').value;
        if (min && text < min) return false;
        if (max && text > max) return false;
        return true;
      }
      const v = th.querySelector('input').value.toLowerCase();
      return !v || text.toLowerCase().includes(v);
    });
  }
  function applyFilter(){ tableEl.querySelectorAll('tbody tr').forEach(tr => tr.style.display = rowVisible(tr) ? '' : 'none'); }
  filterRow.addEventListener('input', applyFilter);

  // 3) Jei naudoji DataTables ir jis jau inicializuotas – perimame filtrus kolonoms
  const hasDT = !!window.jQuery && !!jQuery.fn.dataTable && jQuery.fn.dataTable.isDataTable(tableEl);
  if (hasDT) {
    const dt = jQuery(tableEl).DataTable();
    dt.columns().every(function (i) {
      const thHead = headRow.children[i];
      if ((thHead.dataset.type||'') !== 'select' || thHead.getAttribute('data-choices')) return;
      const sel = filterRow.children[i].querySelector('select');
      sel.innerHTML = `<option value="">Visi</option>`;
      this.data().unique().sort().each(function (d) {
        const t = String(jQuery(d).text ? jQuery(d).text() : d).trim();
        if (t) sel.innerHTML += `<option>${t}</option>`;
      });
    });
    dt.columns().every(function (i) {
      const thHead = headRow.children[i];
      const th = filterRow.children[i];
      const type = thHead.dataset.type || 'text';
      if (type === 'text') {
        const inp = th.querySelector('input');
        inp.addEventListener('keyup', e=>{ if(e.key==='Enter') jQuery(inp).trigger('change'); });
        inp.addEventListener('change', function(){ dt.column(i).search(this.value).draw(); });
      } else if (type === 'select') {
        th.querySelector('select').addEventListener('change', function(){ dt.column(i).search(this.value).draw(); });
      } else if (type === 'number' || type === 'date') {
        const from = th.querySelector('input[data-op="gte"]');
        const to   = th.querySelector('input[data-op="lte"]');
        const fire = ()=> dt.column(i).search((from.value||'') + '…' + (to.value||'')).draw();
        from.addEventListener('change', fire); to.addEventListener('change', fire);
      }
    });
  }
})();
