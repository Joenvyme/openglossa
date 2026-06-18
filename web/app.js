// Client-side demo of search_parallel over an official, cited TM slice.
// No backend required: lexical retrieval runs entirely in the browser.

"use strict";

const state = { data: [], ready: false };

const tokenize = (s) =>
  (s.toLowerCase().match(/[\p{L}]+/gu) || []).filter((t) => t.length > 1);

async function load() {
  const res = await fetch("data/tm_demo.json");
  state.data = await res.json();
  state.ready = true;
}

function score(queryTokens, text) {
  const docTokens = new Set(tokenize(text));
  if (queryTokens.size === 0 || docTokens.size === 0) return 0;
  let inter = 0;
  for (const t of queryTokens) if (docTokens.has(t)) inter += 1;
  return inter / queryTokens.size;
}

function search(query, dir, k = 8) {
  const qTokens = new Set(tokenize(query));
  const srcKey = dir; // "de" or "fr"
  const tgtKey = dir === "de" ? "fr" : "de";
  const scored = [];
  for (const row of state.data) {
    const s = score(qTokens, row[srcKey]);
    if (s > 0) scored.push({ s, src: row[srcKey], tgt: row[tgtKey], ref: row.ref, uri: row.uri });
  }
  scored.sort((a, b) => b.s - a.s || a.src.localeCompare(b.src));
  return scored.slice(0, k);
}

function escapeHtml(s) {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function highlight(text, qTokens) {
  return escapeHtml(text).replace(/[\p{L}]+/gu, (w) =>
    qTokens.has(w.toLowerCase()) ? `<mark>${w}</mark>` : w
  );
}

function render(hits, query, dir) {
  const box = document.getElementById("results");
  if (!query.trim()) {
    box.innerHTML = `<p class="hint">Saisissez un terme ou une phrase pour interroger la mémoire de traduction.</p>`;
    return;
  }
  if (hits.length === 0) {
    box.innerHTML = `<p class="hint">Aucun résultat dans l'extrait de démonstration. Essayez « contrat », « erreur », « délai », « Schuldner »…</p>`;
    return;
  }
  const qTokens = new Set(tokenize(query));
  const srcLang = dir.toUpperCase();
  const tgtLang = (dir === "de" ? "fr" : "de").toUpperCase();
  box.innerHTML = hits
    .map(
      (h) => `
      <div class="result">
        <div class="pair">
          <div><div class="lang">${srcLang}</div>${highlight(h.src, qTokens)}</div>
          <div><div class="lang">${tgtLang}</div>${escapeHtml(h.tgt)}</div>
        </div>
        <div class="cite">
          <a href="${escapeHtml(h.uri)}" target="_blank" rel="noopener">${escapeHtml(h.ref)} ↗</a>
          <span class="score">score ${h.s.toFixed(2)}</span>
        </div>
      </div>`
    )
    .join("");
}

async function run() {
  const input = document.getElementById("q");
  const dirSel = document.getElementById("dir");
  const box = document.getElementById("results");
  if (!state.ready) {
    box.innerHTML = `<p class="hint">Chargement de la mémoire de traduction…</p>`;
    try {
      await load();
    } catch {
      box.innerHTML = `<p class="hint">Impossible de charger les données de démo (servez le site via HTTP).</p>`;
      return;
    }
  }
  const q = input.value;
  render(search(q, dirSel.value), q, dirSel.value);
}

document.getElementById("go").addEventListener("click", run);
document.getElementById("q").addEventListener("keydown", (e) => {
  if (e.key === "Enter") run();
});
document.getElementById("dir").addEventListener("change", run);

// Preload data and show an example so the demo is alive on first paint.
load().then(() => {
  document.getElementById("q").value = "Schuldner Verzug";
  run();
});
