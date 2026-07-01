// Corpus overview chart for the landing page (bundled TM + live backbones).

"use strict";

const CORPUS_STATS_URL = "data/corpus_stats.json";

function t(key) {
  return typeof window.ogT === "function" ? window.ogT(key) : key;
}

function fmt(n) {
  return new Intl.NumberFormat(document.documentElement.lang || "fr").format(n);
}

function pct(part, total) {
  return total ? Math.round((part / total) * 1000) / 10 : 0;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function sourceLabel(id) {
  return t(`s00.src.${id}`);
}

function renderStackedBar(stats) {
  const total = stats.total;
  const rows = stats.bundled.map((row) => ({
    ...row,
    label: sourceLabel(row.id),
    share: pct(row.count, total),
  }));

  const segments = rows
    .map(
      (row, i) => `
    <div class="corpus-seg corpus-seg--${row.id}" style="width:${row.share}%" role="listitem"
         title="${escapeHtml(row.label)} · ${fmt(row.count)} (${row.share}%)">
      <span class="corpus-seg-label">${escapeHtml(row.label)}</span>
      <span class="corpus-seg-val">${fmt(row.count)}</span>
    </div>`
    )
    .join("");

  return `
    <div class="corpus-stack" role="list" aria-label="${escapeHtml(t("s00.chartBundled"))}">
      ${segments}
    </div>
    <div class="corpus-legend">
      ${rows
        .map(
          (row) => `
        <div class="corpus-legend-item">
          <span class="corpus-swatch corpus-swatch--${row.id}"></span>
          <span>${escapeHtml(row.label)}</span>
          <span class="corpus-legend-meta">${row.share}% · ${escapeHtml(t("s00.langs311"))}</span>
        </div>`
        )
        .join("")}
    </div>`;
}

function renderPairs(stats) {
  const max = Math.max(...stats.pairs.map((p) => p.count), 1);
  return `
    <div class="corpus-pairs" aria-label="${escapeHtml(t("s00.chartPairs"))}">
      ${stats.pairs
        .map((p) => {
          const w = Math.round((p.count / max) * 100);
          const label = `${p.src.toUpperCase()} → ${p.tgt.toUpperCase()}`;
          return `
        <div class="corpus-pair">
          <div class="corpus-pair-head">
            <span>${label}</span>
            <span>${fmt(p.count)}</span>
          </div>
          <div class="corpus-pair-bar"><span style="width:${w}%"></span></div>
        </div>`;
        })
        .join("")}
    </div>`;
}

function renderLive(stats) {
  return `
    <div class="corpus-live" aria-label="${escapeHtml(t("s00.chartLive"))}">
      ${stats.live
        .map((row) => {
          const badge =
            row.license === "warn"
              ? `<span class="badge warn">${escapeHtml(t("s05.badge_warn"))}</span>`
              : `<span class="badge ok">${escapeHtml(t("s05.badge_ok"))}</span>`;
          const scale = row.scale ? `<span class="corpus-live-scale">${escapeHtml(row.scale)}</span>` : "";
          return `
        <div class="corpus-live-item">
          <span class="corpus-live-name">${escapeHtml(sourceLabel(row.id))}${scale}</span>
          <span class="corpus-live-tag">${escapeHtml(t("s00.liveTag"))}</span>
          ${badge}
        </div>`;
        })
        .join("")}
    </div>`;
}

function renderChart(stats) {
  const host = document.getElementById("corpus-chart");
  if (!host || !stats) return;

  host.innerHTML = `
    <div class="corpus-headline">
      <div class="corpus-total">${fmt(stats.total)}</div>
      <div class="corpus-total-label">${escapeHtml(t("s00.totalLabel"))}</div>
    </div>
    <div class="corpus-grid">
      <div class="corpus-panel">
        <h3 class="corpus-sub">${escapeHtml(t("s00.panelBundled"))}</h3>
        ${renderStackedBar(stats)}
      </div>
      <div class="corpus-panel">
        <h3 class="corpus-sub">${escapeHtml(t("s00.panelPairs"))}</h3>
        ${renderPairs(stats)}
      </div>
      <div class="corpus-panel corpus-panel--live">
        <h3 class="corpus-sub">${escapeHtml(t("s00.panelLive"))}</h3>
        <p class="corpus-live-note">${escapeHtml(t("s00.liveNote"))}</p>
        ${renderLive(stats)}
      </div>
    </div>`;
}

async function initCorpusChart() {
  const host = document.getElementById("corpus-chart");
  if (!host) return;
  try {
    if (!initCorpusChart.stats) {
      const res = await fetch(CORPUS_STATS_URL);
      if (!res.ok) throw new Error(String(res.status));
      initCorpusChart.stats = await res.json();
    }
    renderChart(initCorpusChart.stats);
  } catch {
    host.innerHTML = `<p class="hint">${escapeHtml(t("s00.loadError"))}</p>`;
  }
}
initCorpusChart.stats = null;

window.addEventListener("og:langchange", () => {
  initCorpusChart();
});

initCorpusChart();
