/* ═══════════════════════════════════════════════════════════════
   ANATEL MONITOR — app.js
   Dark mode · Filtros · Busca AJAX · Collapse · Modal · Charts
═══════════════════════════════════════════════════════════════ */

'use strict';

// ──────────────────────────────────────────────────────────────
// Utilitários
// ──────────────────────────────────────────────────────────────
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

function fmtData(iso) {
  if (!iso) return '—';
  const [y, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}/${y}`;
}

// ──────────────────────────────────────────────────────────────
// TEMA CLARO / ESCURO
// ──────────────────────────────────────────────────────────────
(function initTheme() {
  const saved = localStorage.getItem('anatel-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
})();

function updateThemeIcon(theme) {
  const el = $('#themeIcon');
  if (el) el.textContent = theme === 'dark' ? '☀️' : '🌙';
}

$('#themeToggle')?.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  const next    = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('anatel-theme', next);
  updateThemeIcon(next);
  updateChartColors();
});

// ──────────────────────────────────────────────────────────────
// ESTADO DOS FILTROS
// ──────────────────────────────────────────────────────────────
const state = { q: '', tipo: '', status: '', ano: '' };
let searchActive = false;

// ──────────────────────────────────────────────────────────────
// BUSCA
// ──────────────────────────────────────────────────────────────
const searchInput  = $('#searchInput');
const clearBtn     = $('#clearSearch');
const staticContent= $('#staticContent');
const searchResults= $('#searchResults');
const searchGrid   = $('#searchGrid');
const searchCount  = $('#searchCount');
const searchEmpty  = $('#searchEmpty');
const exportBtn    = $('#exportBtn');

const doSearch = debounce(async () => {
  const params = new URLSearchParams();
  if (state.q)      params.set('q',      state.q);
  if (state.tipo)   params.set('tipo',   state.tipo);
  if (state.status) params.set('status', state.status);
  if (state.ano)    params.set('ano',    state.ano);

  // Atualiza link de exportação CSV com filtros activos
  exportBtn.href = '/exportar.csv?' + params.toString();

  const hasFilter = state.q || state.tipo || state.status || state.ano;

  if (!hasFilter) {
    // Volta para a view estática
    searchResults.hidden = true;
    staticContent.hidden = false;
    searchActive = false;
    return;
  }

  try {
    const resp = await fetch('/api/consultas?' + params.toString());
    const data = await resp.json();

    searchGrid.innerHTML = '';
    searchCount.textContent = data.length;
    searchResults.hidden = false;
    staticContent.hidden = true;
    searchActive = true;

    if (data.length === 0) {
      searchEmpty.hidden = false;
    } else {
      searchEmpty.hidden = true;
      data.forEach(c => {
        searchGrid.insertAdjacentHTML('beforeend', buildCardHTML(c));
      });
    }
  } catch (err) {
    console.error('Erro na busca:', err);
  }
}, 350);

searchInput?.addEventListener('input', () => {
  state.q = searchInput.value.trim();
  clearBtn.hidden = !state.q;
  doSearch();
});

clearBtn?.addEventListener('click', () => {
  searchInput.value = '';
  state.q = '';
  clearBtn.hidden = true;
  doSearch();
});

// ──────────────────────────────────────────────────────────────
// FILTROS (chips)
// ──────────────────────────────────────────────────────────────
$$('[data-filter]').forEach(chip => {
  chip.addEventListener('click', () => {
    const filterKey = chip.dataset.filter;    // tipo | ano | status
    const value     = chip.dataset.value;

    // Ativa chip visualmente
    $$(`[data-filter="${filterKey}"]`).forEach(c => c.classList.remove('chip-active'));
    chip.classList.add('chip-active');

    state[filterKey] = value;
    doSearch();
  });
});

// ──────────────────────────────────────────────────────────────
// CARD HTML (para resultados AJAX)
// ──────────────────────────────────────────────────────────────
function buildCardHTML(c) {
  const aberta    = c.status === 'Aberta';
  const tipoCurto = c.tipo.includes('Pública') ? 'CP' : 'TS';
  const prazo     = c.prazo_resposta || c.data_encerramento;
  const prazoFmt  = fmtData(prazo);
  const dias      = c.dias_restantes;
  const urgente   = c.urgente;

  let cardClass = 'card ';
  if (urgente)       cardClass += 'card-urgent';
  else if (aberta)   cardClass += 'card-open';
  else               cardClass += 'card-closed';

  let diasHTML = '';
  if (aberta && dias !== null && dias !== undefined) {
    if      (dias < 0)  diasHTML = `<span class="meta-item tag-overdue">Vencida</span>`;
    else if (dias === 0)diasHTML = `<span class="meta-item tag-today">Hoje!</span>`;
    else if (dias <= 7) diasHTML = `<span class="meta-item tag-critical">${dias}d</span>`;
    else if (dias <= 15)diasHTML = `<span class="meta-item tag-warning">${dias} dias</span>`;
    else                diasHTML = `<span class="meta-item tag-ok">${dias} dias</span>`;
  }

  const objeto = c.objeto && c.objeto !== c.titulo
    ? `<p class="card-objeto">${c.objeto.slice(0,120)}${c.objeto.length > 120 ? '…' : ''}</p>`
    : '';

  const prazoMeta = prazo
    ? `<span class="meta-item">📅 <strong>${prazoFmt}</strong></span>${diasHTML}`
    : `<span class="meta-item meta-muted">📅 Prazo não informado</span>`;

  const contribs = c.numero_contribuicoes > 0
    ? `<span class="meta-item">💬 ${c.numero_contribuicoes}</span>`
    : '';

  const linkBtn = c.link
    ? `<a href="${c.link}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Participar →</a>`
    : '';

  const adiada = c.adiada
    ? `<span class="badge-tag badge-postponed">🔄 Adiada</span>` : '';
  const urg = urgente
    ? `<span class="badge-tag badge-urgent-sm">🔥 Urgente</span>` : '';

  const statusDot = aberta
    ? `<span class="status-dot status-open">● Aberta</span>`
    : `<span class="status-dot status-closed">● Encerrada</span>`;

  // Serializa dados no card para abrir modal
  const dataAttrs = Object.entries({
    codigo: c.codigo, tipo: c.tipo, status: c.status,
    titulo: c.titulo, objeto: c.objeto, descricao: c.descricao,
    questionamentos: c.questionamentos, prazo: prazo || '',
    link: c.link, abertura: c.data_abertura || '',
    contribuicoes: c.numero_contribuicoes, adiada: c.adiada,
  }).map(([k,v]) => `data-${k}="${String(v).replace(/"/g,'&quot;')}"`).join(' ');

  return `
  <article class="${cardClass}" ${dataAttrs}>
    <div class="card-header">
      <div class="card-badges">
        <span class="badge-tipo badge-tipo-${tipoCurto.toLowerCase()}" title="${c.tipo}">${tipoCurto}</span>
        ${adiada}${urg}
      </div>
      ${statusDot}
    </div>
    <div class="card-body">
      <h3 class="card-title">${c.titulo}</h3>
      ${objeto}
    </div>
    <div class="card-footer">
      <div class="card-meta">${prazoMeta}${contribs}</div>
      <div class="card-actions">
        <button class="btn btn-ghost btn-sm" onclick="abrirDetalhe(this.closest('.card'))">Ver mais</button>
        ${linkBtn}
      </div>
    </div>
  </article>`;
}

// ──────────────────────────────────────────────────────────────
// COLLAPSE — Encerradas
// ──────────────────────────────────────────────────────────────
document.querySelector('.collapsible')?.addEventListener('click', function () {
  const target = $('#' + this.dataset.target);
  const arrow  = $('#encerradasArrow');
  if (!target) return;

  const collapsed = target.style.display === 'none';
  target.style.display = collapsed ? '' : 'none';
  arrow?.classList.toggle('collapsed', !collapsed);
});

// ──────────────────────────────────────────────────────────────
// MODAL DETALHE
// ──────────────────────────────────────────────────────────────
const modalOverlay = $('#modalOverlay');
const modalContent = $('#modalContent');
const modalClose   = $('#modalClose');

window.abrirDetalhe = function (card) {
  if (!card) return;
  const d = card.dataset;
  const aberta = d.status === 'Aberta';
  const tipoCurto = d.tipo?.includes('Pública') ? 'CP' : 'TS';
  const adiada = d.adiada === 'true';

  modalContent.innerHTML = `
    <div class="modal-tipo-badge">
      <span class="badge-tipo badge-tipo-${tipoCurto.toLowerCase()}">${d.tipo}</span>
      ${adiada ? '<span class="badge-tag badge-postponed">🔄 Prazo Adiado</span>' : ''}
      ${aberta
        ? '<span class="status-dot status-open">● Aberta</span>'
        : '<span class="status-dot status-closed">● Encerrada</span>'
      }
    </div>
    <h2 class="modal-title">${d.titulo}</h2>

    <div class="modal-grid">
      <div class="modal-field">
        <label>Código</label>
        <p>${d.codigo || '—'}</p>
      </div>
      <div class="modal-field">
        <label>Tipo</label>
        <p>${d.tipo}</p>
      </div>
      <div class="modal-field">
        <label>Status</label>
        <p>${d.status}</p>
      </div>
      <div class="modal-field">
        <label>Prazo de Resposta</label>
        <p>${fmtData(d.prazo) || '—'}</p>
      </div>
      <div class="modal-field">
        <label>Data de Abertura</label>
        <p>${fmtData(d.abertura) || '—'}</p>
      </div>
      <div class="modal-field">
        <label>Contribuições</label>
        <p>${d.contribuicoes > 0 ? d.contribuicoes : '—'}</p>
      </div>
      <div class="modal-field">
        <label>Prazo Adiado?</label>
        <p>${adiada ? 'Sim' : 'Não'}</p>
      </div>
    </div>

    ${d.objeto && d.objeto !== d.titulo ? `
      <hr class="modal-divider" />
      <p class="modal-section-title">Objeto</p>
      <p class="modal-text">${d.objeto}</p>
    ` : ''}

    ${d.descricao ? `
      <hr class="modal-divider" />
      <p class="modal-section-title">Descrição</p>
      <p class="modal-text">${d.descricao}</p>
    ` : ''}

    ${d.questionamentos ? `
      <hr class="modal-divider" />
      <p class="modal-section-title">Questionamentos</p>
      <p class="modal-text">${d.questionamentos}</p>
    ` : ''}

    <div class="modal-actions">
      ${d.link ? `<a href="${d.link}" target="_blank" rel="noopener" class="btn btn-primary">Participar →</a>` : ''}
      <button class="btn btn-ghost" onclick="document.getElementById('modalOverlay').hidden=true">Fechar</button>
    </div>
  `;

  modalOverlay.hidden = false;
  document.body.style.overflow = 'hidden';
};

modalClose?.addEventListener('click', closeModal);
modalOverlay?.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

function closeModal() {
  if (modalOverlay) modalOverlay.hidden = true;
  document.body.style.overflow = '';
}

// ──────────────────────────────────────────────────────────────
// GRÁFICOS (Chart.js)
// ──────────────────────────────────────────────────────────────
let chartTipo, chartAno, chartStatus;

function getChartColors() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  return {
    text:    dark ? '#94a3b8' : '#6b7280',
    grid:    dark ? '#2d3f5e' : '#e5e7eb',
    bg:      dark ? '#162035' : '#ffffff',
    blue:    '#3b82f6',
    green:   '#22c55e',
    pink:    '#ec4899',
    amber:   '#f59e0b',
    red:     '#ef4444',
    gray:    '#9ca3af',
  };
}

async function initCharts() {
  try {
    const resp = await fetch('/api/stats');
    const data = await resp.json();
    const col  = getChartColors();

    // Donut: CP vs TS
    const ctxTipo = $('#chartTipo');
    if (ctxTipo) {
      chartTipo = new Chart(ctxTipo, {
        type: 'doughnut',
        data: {
          labels: ['Consultas Públicas', 'Tomadas de Subsídio'],
          datasets: [{
            data: [data.totais.consultas_publicas, data.totais.tomadas_subsidio],
            backgroundColor: [col.blue, col.pink],
            borderColor: col.bg,
            borderWidth: 3,
            hoverOffset: 6,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '65%',
          plugins: {
            legend: { position: 'bottom', labels: { color: col.text, padding: 16, font: { size: 12 } } },
            tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}` } },
          },
        },
      });
    }

    // Barras: consultas por ano (empilhadas CP + TS)
    const ctxAno = $('#chartAno');
    if (ctxAno) {
      const anos  = Object.keys(data.por_tipo_ano).sort();
      const cpData= anos.map(a => data.por_tipo_ano[a].CP || 0);
      const tsData= anos.map(a => data.por_tipo_ano[a].TS || 0);

      chartAno = new Chart(ctxAno, {
        type: 'bar',
        data: {
          labels: anos,
          datasets: [
            { label: 'Consultas Públicas', data: cpData, backgroundColor: col.blue, borderRadius: 4 },
            { label: 'Tomadas de Subsídio', data: tsData, backgroundColor: col.pink, borderRadius: 4 },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { stacked: true, ticks: { color: col.text }, grid: { color: col.grid } },
            y: { stacked: true, ticks: { color: col.text, stepSize: 1 }, grid: { color: col.grid }, beginAtZero: true },
          },
          plugins: {
            legend: { labels: { color: col.text, font: { size: 12 } } },
          },
        },
      });
    }

    // Donut: Abertas vs Encerradas
    const ctxStatus = $('#chartStatus');
    if (ctxStatus) {
      chartStatus = new Chart(ctxStatus, {
        type: 'doughnut',
        data: {
          labels: ['Abertas', 'Encerradas', 'Adiadas'],
          datasets: [{
            data: [data.totais.abertas, data.totais.encerradas, data.totais.adiadas],
            backgroundColor: [col.green, col.gray, col.amber],
            borderColor: col.bg,
            borderWidth: 3,
            hoverOffset: 6,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '65%',
          plugins: {
            legend: { position: 'bottom', labels: { color: col.text, padding: 16, font: { size: 12 } } },
          },
        },
      });
    }

  } catch (err) {
    console.error('Erro ao carregar gráficos:', err);
  }
}

function updateChartColors() {
  if (!chartTipo) return;
  const col = getChartColors();

  [chartTipo, chartStatus].forEach(chart => {
    if (!chart) return;
    chart.options.plugins.legend.labels.color = col.text;
    chart.data.datasets[0].borderColor = col.bg;
    chart.update();
  });

  if (chartAno) {
    chartAno.options.scales.x.ticks.color = col.text;
    chartAno.options.scales.x.grid.color  = col.grid;
    chartAno.options.scales.y.ticks.color = col.text;
    chartAno.options.scales.y.grid.color  = col.grid;
    chartAno.options.plugins.legend.labels.color = col.text;
    chartAno.update();
  }
}

// ──────────────────────────────────────────────────────────────
// INICIALIZAÇÃO
// ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initCharts();

  // Atualiza timestamp com hora local
  const el = document.getElementById('lastUpdate');
  if (el && el.textContent.includes('N/D')) {
    el.textContent = 'Atualizado: ' + new Date().toLocaleString('pt-BR');
  }
});
