// Live search over the full official translation memory (Fedlex + ATF/BGE),
// served by the OpenGlossa MCP host's public /search endpoint. Falls back to a
// small in-browser lexical demo if the backend is unreachable.

"use strict";

const SEARCH_API = "https://openglossa-mcp.onrender.com/search";
const LANGS = { de: "DE", fr: "FR", it: "IT", en: "EN" };

const state = { demo: [], demoReady: false };

const tokenize = (s) =>
  (s.toLowerCase().match(/[\p{L}]+/gu) || []).filter((t) => t.length > 1);

function usesEnglish(src, tgt) {
  return src === "en" || tgt === "en";
}

async function loadDemo() {
  if (state.demoReady) return;
  const res = await fetch("data/tm_demo.json");
  state.demo = await res.json();
  state.demoReady = true;
}

function demoScore(queryTokens, text) {
  const docTokens = new Set(tokenize(text));
  if (queryTokens.size === 0 || docTokens.size === 0) return 0;
  let inter = 0;
  for (const t of queryTokens) if (docTokens.has(t)) inter += 1;
  return inter / queryTokens.size;
}

// Local fallback only covers DE<->FR (the bundled demo slice).
function demoSearch(query, src, tgt, k = 8) {
  const qTokens = new Set(tokenize(query));
  const scored = [];
  for (const row of state.demo) {
    if (!(src in row) || !(tgt in row)) continue;
    const s = demoScore(qTokens, row[src]);
    if (s > 0)
      scored.push({ src: row[src], tgt: row[tgt], source: { ref: row.ref, uri: row.uri }, score: s });
  }
  scored.sort((a, b) => b.score - a.score || a.src.localeCompare(b.src));
  return scored.slice(0, k);
}

async function backendSearch(query, src, tgt, k = 8) {
  const url = `${SEARCH_API}?q=${encodeURIComponent(query)}&src=${src}&tgt=${tgt}&k=${k}`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return {
    results: data.results || [],
    method: data.method || "vector",
    queryTranslation: data.query_translation || "",
    enScope: Boolean(data.en_scope),
    eurlexScope: Boolean(data.eurlex_scope),
  };
}

// Translated dynamic string, with a French fallback if i18n.js hasn't loaded.
function t(key) {
  return typeof window.ogT === "function" ? window.ogT(key) : key;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function highlight(text, qTokens) {
  return escapeHtml(text).replace(/[\p{L}]+/gu, (w) =>
    qTokens.has(w.toLowerCase()) ? `<mark>${w}</mark>` : w
  );
}

function methodLabel(method) {
  if (!method || method === "none") return "";
  if (method.includes("eurlex")) return t("js.methodEurlex");
  if (method === "lexical") return t("js.methodLexical");
  return t("js.methodSemantic");
}

function render(hits, query, src, tgt, method, queryTranslation = "", meta = {}) {
  const box = document.getElementById("results");
  if (!query.trim()) {
    box.innerHTML = `<p class="hint">${escapeHtml(t("js.prompt"))}</p>`;
    return;
  }
  if (src === tgt) {
    box.innerHTML = `<p class="hint">${escapeHtml(t("js.sameLang"))}</p>`;
    return;
  }
  if (hits.length === 0) {
    box.innerHTML = `<p class="hint">${escapeHtml(t("js.noResult"))}</p>`;
    return;
  }
  const qTokens = new Set(tokenize(query));
  const tTokens = new Set(tokenize(queryTranslation));
  const srcLang = LANGS[src] || src.toUpperCase();
  const tgtLang = LANGS[tgt] || tgt.toUpperCase();
  const mLabel = methodLabel(method);
  const summary = t("js.summary")
    .replace("{method}", escapeHtml(mLabel))
    .replace("{n}", String(hits.length));
  const transNote = queryTranslation
    ? ` · ${escapeHtml(t("js.targetTerm"))} : <strong>${escapeHtml(queryTranslation)}</strong>`
    : "";
  const scopeNote =
    usesEnglish(src, tgt) && (meta.enScope || meta.eurlexScope)
      ? `<p class="hint scope">${escapeHtml(t("js.enScope"))}</p>`
      : "";
  box.innerHTML =
    scopeNote +
    `<p class="hint method">${summary}${transNote}</p>` +
    hits
      .map((h) => {
        const ref = (h.source && h.source.ref) || h.ref || "";
        const uri = (h.source && h.source.uri) || h.uri || "";
        const cite = uri
          ? `<a href="${escapeHtml(uri)}" target="_blank" rel="noopener">${escapeHtml(ref)} ↗</a>`
          : `<span>${escapeHtml(ref)}</span>`;
        const score = typeof h.score === "number" ? `<span class="score">${escapeHtml(t("js.score"))} ${h.score.toFixed(2)}</span>` : "";
        const tgtHtml = tTokens.size ? highlight(h.tgt, tTokens) : escapeHtml(h.tgt);
        return `
      <div class="result">
        <div class="pair">
          <div><div class="lang">${srcLang}</div>${highlight(h.src, qTokens)}</div>
          <div><div class="lang">${tgtLang}</div>${tgtHtml}</div>
        </div>
        <div class="cite">${cite}${score}</div>
      </div>`;
      })
      .join("");
}

async function run() {
  const input = document.getElementById("q");
  const src = document.getElementById("src").value;
  const tgt = document.getElementById("tgt").value;
  const box = document.getElementById("results");
  const q = input.value;
  if (!q.trim()) {
    render([], q, src, tgt, "");
    return;
  }
  if (src === tgt) {
    render([], q, src, tgt, "");
    return;
  }
  box.innerHTML = `<p class="hint">${escapeHtml(t("js.searching"))}</p>`;
  try {
    const { results, method, queryTranslation, enScope, eurlexScope } = await backendSearch(q, src, tgt);
    render(results, q, src, tgt, method, queryTranslation, { enScope, eurlexScope });
  } catch {
    // Backend unreachable: fall back to the bundled DE<->FR demo slice.
    try {
      await loadDemo();
      if (usesEnglish(src, tgt)) {
        box.innerHTML = `<p class="hint">${escapeHtml(t("js.unavailableEn"))}</p>`;
        return;
      }
      const hits = demoSearch(q, src, tgt);
      if (hits.length === 0 && (src === "it" || tgt === "it")) {
        box.innerHTML = `<p class="hint">${escapeHtml(t("js.unavailableIt"))}</p>`;
        return;
      }
      render(hits, q, src, tgt, "lexical");
    } catch {
      box.innerHTML = `<p class="hint">${escapeHtml(t("js.unavailable"))}</p>`;
    }
  }
}

document.getElementById("go").addEventListener("click", run);
document.getElementById("q").addEventListener("keydown", (e) => {
  if (e.key === "Enter") run();
});
document.getElementById("src").addEventListener("change", run);
document.getElementById("tgt").addEventListener("change", run);

// Re-render results in the newly selected UI language.
window.addEventListener("og:langchange", () => run());

function applyDemoExample() {
  const uiLang = window.OG_LANG || "fr";
  if (uiLang === "en") {
    document.getElementById("q").value = t("js.demoQueryEn");
    document.getElementById("src").value = "de";
    document.getElementById("tgt").value = "en";
  } else {
    document.getElementById("q").value = t("js.demoQuery");
    document.getElementById("src").value = "de";
    document.getElementById("tgt").value = "fr";
  }
}

applyDemoExample();
run();
