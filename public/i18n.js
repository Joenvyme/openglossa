// Lightweight client-side i18n for the OpenGlossa site (FR / DE / EN).
// Static text is tagged in the HTML with data-i18n / data-i18n-ph / data-i18n-aria
// keys; this file holds the translations and swaps them on language change.
// Dynamic search strings (used by app.js) live under the "js." keys.

"use strict";

const OG_I18N = {
  fr: {
    "meta.title": "OpenGlossa — traduction juridique suisse ancrée dans les sources officielles",
    "meta.description":
      "Termbase et mémoire de traduction open source pour le droit suisse (DE/FR/IT), ancrés dans des sources officielles citables (Fedlex, TERMDAT, Tribunal fédéral).",
    "nav.search": "Recherche",
    "nav.data": "Données",
    "nav.mcp": "MCP",
    "hero.h1": "traduire.",
    "hero.sub": "le droit suisse, sans rien inventer.",
    "hero.meta":
      "Termbase &amp; mémoire de traduction juridique suisse — DE / FR / IT · open source (depuis 2026)",
    "intro.note":
      "OpenGlossa agrège la terminologie et les textes parallèles du droit fédéral suisse — Fedlex, TERMDAT, Tribunal fédéral — en une base citable, exposée via un serveur MCP.",
    "intro.statement":
      "Une base terminologique et une mémoire de traduction qui ancrent chaque résultat dans une source officielle citable, pour traduire le droit suisse sans rien inventer.",
    "index.search": "Recherche<br />citée",
    "index.data": "Données<br />&amp; exports",
    "index.api": "API MCP<br />(5)",
    "disclaimer.mark": "Avis",
    "disclaimer.text":
      "Les sorties d'OpenGlossa ne constituent <b>pas</b> le texte légal officiel faisant foi. Toujours vérifier contre la source officielle (n° RS + article Fedlex, ou référence ATF/BGE).",
    "s01.h2": "Recherche",
    "s01.lead":
      "Recherche sémantique en direct : 113 095 segments suisses (Fedlex + ATF/BGE, DE/FR/IT) et, dès que l'anglais est impliqué, législation parallèle EUR-Lex (UE). Chaque résultat est cité — article RS, référence ATF ou acte CELEX.",
    "s01.ph": "ex. DE→FR « Schuldner Verzug », DE→EN « Schuldner », EN→FR « personal data »…",
    "s01.srcAria": "Langue source",
    "s01.tgtAria": "Langue cible",
    "s01.go": "Rechercher",
    "s02.h2": "Évaluation",
    "s02.lead":
      "Term hit-rate@3 sur 15 requêtes tenues à l'écart, mesuré sur le corpus complet de production (113 095 segments) : le terme officiel attendu apparaît-il dans les 3 premiers segments récupérés ? Benchmark reproductible (<code>python eval/run_eval.py</code>), figé — ce n'est pas une métrique live.",
    "s02.m1": "sans ancrage",
    "s02.m2": "lexical",
    "s02.m3": "vectoriel · MiniLM",
    "s02.m4": "hybride · MiniLM",
    "s03.h2": "Téléchargements",
    "s03.lead": "Extrait de démonstration (CO / SR 220, source officielle Fedlex, citée).",
    "s03.sub_tmx": "Mémoire de traduction, TMX 1.4 (validée DTD).",
    "s03.sub_jsonl": "Segments parallèles avec provenance.",
    "s03.sub_csv": "Glossaire DeepL DE→FR (couples extraits, à relire).",
    "s03.sub_schema": "JSON Schema d'une unité de traduction.",
    "s03.hint": "Formats complets (TBX, Parquet, toutes paires) : <code>openglossa build-exports</code>.",
    "s04.h2": "Schéma",
    "s04.lead":
      "Modèles pydantic v2 à provenance obligatoire — aucun enregistrement sans source citable.",
    "s04.sub_term": "Entrée terminologique centrée concept (≈ termEntry TBX).",
    "s04.meta_term": "concept",
    "s04.sub_tu": "Segment parallèle aligné (≈ tu TMX).",
    "s04.meta_tu": "segment",
    "s04.sub_cand": "Couple de termes extrait, en file de revue.",
    "s04.meta_cand": "candidat",
    "s05.h2": "Licences",
    "s05.fedlex_name": "Fedlex (RS)",
    "s05.fedlex_sub": "Lois fédérales DE/FR/IT — texte + métadonnées RDF",
    "s05.fedlex_right": "Réutilisation, citation requise",
    "s05.slds_name": "Tribunal fédéral (SLDS)",
    "s05.slds_sub": "Regestes trilingues (ATF/BGE)",
    "s05.termdat_name": "TERMDAT (LINDAS)",
    "s05.termdat_sub": "Terminologie officielle multilingue",
    "s05.termdat_right": "OGD — redistribution à confirmer",
    "s05.badge_ok": "réutilisable",
    "s05.badge_warn": "live / dérivés",
    "s05.hint":
      "Détails : <code>LICENSING.md</code>, <code>ATTRIBUTIONS.md</code>. Code Apache-2.0 · données CC-BY-4.0.",
    "s06.h2": "Connexion MCP",
    "s06.lead":
      "Serveur MCP distant (Streamable HTTP) — cinq outils, réponses toujours citées. Branche-le sur Cursor, Claude Desktop ou tout client MCP.",
    "s06.endpoint": "Endpoint",
    "s06.hint_config":
      "Configuration client (Cursor <code>~/.cursor/mcp.json</code> ou Claude Desktop) :",
    "s06.hint_stdio":
      "Client en stdio uniquement ? Faites le pont avec <code>npx mcp-remote https://openglossa-mcp.onrender.com/mcp</code>.",
    "s06.sub_tools": "Outils",
    "s06.sub_pipeline": "Pipeline &amp; serveur local",
    "footer.top_aria": "Haut de page",
    "footer.d_link": "Téléchargements (TMX · JSONL · CSV · schémas)",
    "footer.l_value": "Apache-2.0 (code) · CC-BY-4.0 (données)",
    "footer.copyright":
      "© 2026 OpenGlossa · sortie non officielle — vérifiez toujours la source faisant foi.",
    "js.demoQuery": "Schuldner Verzug",
    "js.demoQueryEn": "Schuldner",
    "js.prompt": "Saisissez un terme ou une phrase pour interroger la mémoire de traduction.",
    "js.sameLang": "Choisissez deux langues différentes.",
    "js.noResult":
      "Aucun résultat. Essayez « Schuldner », « bonne foi », « personal data », « prescrizione »…",
    "js.enScope":
      "Anglais : pas de loi fédérale suisse consolidée en EN sur Fedlex. Les résultats EN proviennent surtout d'EUR-Lex (UE) et, via le MCP, de TERMDAT/IATE.",
    "js.unavailableEn":
      "Service indisponible ou anglais non couvert hors ligne (nécessite le serveur live + EUR-Lex).",
    "js.methodEurlex": "hybride + EUR-Lex",
    "js.searching": "Recherche…",
    "js.unavailable": "Service de recherche momentanément indisponible. Réessayez dans un instant.",
    "js.unavailableIt":
      "Service de recherche momentanément indisponible (l'italien n'est pas couvert par la démo hors-ligne).",
    "js.methodSemantic": "sémantique",
    "js.methodLexical": "lexical",
    "js.summary": "Recherche {method} · {n} résultat(s)",
    "js.targetTerm": "terme cible probable",
    "js.score": "score",
  },

  de: {
    "meta.title": "OpenGlossa — Schweizer juristische Übersetzung, verankert in amtlichen Quellen",
    "meta.description":
      "Open-Source-Termbank und Translation Memory für das Schweizer Recht (DE/FR/IT), verankert in zitierbaren amtlichen Quellen (Fedlex, TERMDAT, Bundesgericht).",
    "nav.search": "Suche",
    "nav.data": "Daten",
    "nav.mcp": "MCP",
    "hero.h1": "übersetzen.",
    "hero.sub": "Schweizer Recht, ohne Erfindungen.",
    "hero.meta":
      "Schweizer juristische Termbank &amp; Translation Memory — DE / FR / IT · Open Source (seit 2026)",
    "intro.note":
      "OpenGlossa bündelt die Terminologie und die Paralleltexte des Schweizer Bundesrechts — Fedlex, TERMDAT, Bundesgericht — in einer zitierbaren Datenbasis, bereitgestellt über einen MCP-Server.",
    "intro.statement":
      "Eine Termbank und ein Translation Memory, die jedes Ergebnis in einer zitierbaren amtlichen Quelle verankern — um Schweizer Recht zu übersetzen, ohne etwas zu erfinden.",
    "index.search": "Zitierte<br />Suche",
    "index.data": "Daten<br />&amp; Exporte",
    "index.api": "MCP-API<br />(5)",
    "disclaimer.mark": "Hinweis",
    "disclaimer.text":
      "Die Ausgaben von OpenGlossa sind <b>nicht</b> der amtliche, massgebende Gesetzestext. Stets gegen die amtliche Quelle prüfen (SR-Nummer + Fedlex-Artikel oder BGE-Fundstelle).",
    "s01.h2": "Suche",
    "s01.lead":
      "Semantische Live-Suche: 113 095 Schweizer Segmente (Fedlex + BGE, DE/FR/IT) und bei Englisch zusätzlich parallele EU-Gesetzgebung über EUR-Lex. Jedes Ergebnis ist zitiert — SR-Artikel, BGE-Fundstelle oder CELEX-Akt.",
    "s01.ph": "z. B. DE→FR « Schuldner Verzug », DE→EN « Schuldner », EN→FR « personal data »…",
    "s01.srcAria": "Ausgangssprache",
    "s01.tgtAria": "Zielsprache",
    "s01.go": "Suchen",
    "s02.h2": "Evaluation",
    "s02.lead":
      "Term-Hit-Rate@3 über 15 zurückgehaltene Anfragen, gemessen auf dem vollständigen Produktionskorpus (113 095 Segmente): Erscheint der erwartete amtliche Begriff in den ersten 3 gefundenen Segmenten? Reproduzierbarer Benchmark (<code>python eval/run_eval.py</code>), fix — keine Live-Metrik.",
    "s02.m1": "ohne Verankerung",
    "s02.m2": "lexikalisch",
    "s02.m3": "vektoriell · MiniLM",
    "s02.m4": "hybrid · MiniLM",
    "s03.h2": "Downloads",
    "s03.lead": "Demo-Auszug (OR / SR 220, amtliche Fedlex-Quelle, zitiert).",
    "s03.sub_tmx": "Translation Memory, TMX 1.4 (DTD-validiert).",
    "s03.sub_jsonl": "Parallele Segmente mit Provenienz.",
    "s03.sub_csv": "DeepL-Glossar DE→FR (extrahierte Paare, zu prüfen).",
    "s03.sub_schema": "JSON-Schema einer Übersetzungseinheit.",
    "s03.hint": "Vollständige Formate (TBX, Parquet, alle Paare): <code>openglossa build-exports</code>.",
    "s04.h2": "Schema",
    "s04.lead":
      "Pydantic-v2-Modelle mit obligatorischer Provenienz — kein Eintrag ohne zitierbare Quelle.",
    "s04.sub_term": "Konzeptzentrierter Terminologieeintrag (≈ termEntry TBX).",
    "s04.meta_term": "Konzept",
    "s04.sub_tu": "Ausgerichtetes paralleles Segment (≈ tu TMX).",
    "s04.meta_tu": "Segment",
    "s04.sub_cand": "Extrahiertes Begriffspaar, in der Prüfwarteschlange.",
    "s04.meta_cand": "Kandidat",
    "s05.h2": "Lizenzen",
    "s05.fedlex_name": "Fedlex (SR)",
    "s05.fedlex_sub": "Bundesgesetze DE/FR/IT — Text + RDF-Metadaten",
    "s05.fedlex_right": "Weiterverwendung, Quellenangabe erforderlich",
    "s05.slds_name": "Bundesgericht (SLDS)",
    "s05.slds_sub": "Dreisprachige Regesten (BGE)",
    "s05.termdat_name": "TERMDAT (LINDAS)",
    "s05.termdat_sub": "Mehrsprachige amtliche Terminologie",
    "s05.termdat_right": "OGD — Weiterverbreitung zu bestätigen",
    "s05.badge_ok": "wiederverwendbar",
    "s05.badge_warn": "live / Derivate",
    "s05.hint":
      "Details: <code>LICENSING.md</code>, <code>ATTRIBUTIONS.md</code>. Code Apache-2.0 · Daten CC-BY-4.0.",
    "s06.h2": "MCP-Anbindung",
    "s06.lead":
      "Remote-MCP-Server (Streamable HTTP) — fünf Tools, Antworten stets zitiert. Verbinde ihn mit Cursor, Claude Desktop oder jedem MCP-Client.",
    "s06.endpoint": "Endpunkt",
    "s06.hint_config":
      "Client-Konfiguration (Cursor <code>~/.cursor/mcp.json</code> oder Claude Desktop):",
    "s06.hint_stdio":
      "Nur stdio-Client? Überbrücke mit <code>npx mcp-remote https://openglossa-mcp.onrender.com/mcp</code>.",
    "s06.sub_tools": "Tools",
    "s06.sub_pipeline": "Pipeline &amp; lokaler Server",
    "footer.top_aria": "Nach oben",
    "footer.d_link": "Downloads (TMX · JSONL · CSV · Schemas)",
    "footer.l_value": "Apache-2.0 (Code) · CC-BY-4.0 (Daten)",
    "footer.copyright":
      "© 2026 OpenGlossa · inoffizielle Ausgabe — prüfen Sie stets die massgebende Quelle.",
    "js.demoQuery": "Schuldner Verzug",
    "js.demoQueryEn": "Schuldner",
    "js.prompt": "Geben Sie einen Begriff oder Satz ein, um das Translation Memory abzufragen.",
    "js.sameLang": "Wählen Sie zwei verschiedene Sprachen.",
    "js.noResult":
      "Keine Ergebnisse. Versuchen Sie « Schuldner », « bonne foi », « personal data », « prescrizione »…",
    "js.enScope":
      "Englisch: kein konsolidiertes Schweizer Bundesrecht auf Fedlex. EN-Ergebnisse stammen vor allem aus EUR-Lex (EU) und, über MCP, TERMDAT/IATE.",
    "js.unavailableEn":
      "Dienst nicht erreichbar oder Englisch offline nicht abgedeckt (Live-Server + EUR-Lex nötig).",
    "js.methodEurlex": "Hybrid + EUR-Lex",
    "js.searching": "Suche…",
    "js.unavailable": "Suchdienst vorübergehend nicht verfügbar. Bitte versuchen Sie es gleich erneut.",
    "js.unavailableIt":
      "Suchdienst vorübergehend nicht verfügbar (Italienisch wird von der Offline-Demo nicht abgedeckt).",
    "js.methodSemantic": "semantisch",
    "js.methodLexical": "lexikalisch",
    "js.summary": "{method} Suche · {n} Ergebnis(se)",
    "js.targetTerm": "wahrscheinlicher Zielbegriff",
    "js.score": "Score",
  },

  en: {
    "meta.title": "OpenGlossa — Swiss legal translation grounded in official sources",
    "meta.description":
      "Open-source termbase and translation memory for Swiss law (DE/FR/IT), grounded in citable official sources (Fedlex, TERMDAT, Federal Supreme Court).",
    "nav.search": "Search",
    "nav.data": "Data",
    "nav.mcp": "MCP",
    "hero.h1": "translate.",
    "hero.sub": "Swiss law, without making anything up.",
    "hero.meta":
      "Swiss legal termbase &amp; translation memory — DE / FR / IT · open source (since 2026)",
    "intro.note":
      "OpenGlossa aggregates the terminology and parallel texts of Swiss federal law — Fedlex, TERMDAT, Federal Supreme Court — into a citable database, exposed through an MCP server.",
    "intro.statement":
      "A termbase and translation memory that ground every result in a citable official source, to translate Swiss law without making anything up.",
    "index.search": "Cited<br />search",
    "index.data": "Data<br />&amp; exports",
    "index.api": "MCP API<br />(5)",
    "disclaimer.mark": "Notice",
    "disclaimer.text":
      "OpenGlossa's output is <b>not</b> the authoritative official legal text. Always verify against the official source (SR no. + Fedlex article, or ATF/BGE reference).",
    "s01.h2": "Search",
    "s01.lead":
      "Live semantic search: 113,095 Swiss segments (Fedlex + ATF/BGE, DE/FR/IT) and, whenever English is involved, parallel EU legislation via EUR-Lex. Every result is cited — SR article, ATF/BGE reference, or CELEX act.",
    "s01.ph": "e.g. DE→FR « Schuldner Verzug », DE→EN « Schuldner », EN→FR « personal data »…",
    "s01.srcAria": "Source language",
    "s01.tgtAria": "Target language",
    "s01.go": "Search",
    "s02.h2": "Evaluation",
    "s02.lead":
      "Term hit-rate@3 over 15 held-out queries, measured on the full production corpus (113,095 segments): does the expected official term appear in the top 3 retrieved segments? Reproducible benchmark (<code>python eval/run_eval.py</code>), fixed — not a live metric.",
    "s02.m1": "no grounding",
    "s02.m2": "lexical",
    "s02.m3": "vector · MiniLM",
    "s02.m4": "hybrid · MiniLM",
    "s03.h2": "Downloads",
    "s03.lead": "Demo extract (CO / SR 220, official Fedlex source, cited).",
    "s03.sub_tmx": "Translation memory, TMX 1.4 (DTD-validated).",
    "s03.sub_jsonl": "Parallel segments with provenance.",
    "s03.sub_csv": "DeepL glossary DE→FR (extracted pairs, to review).",
    "s03.sub_schema": "JSON Schema of a translation unit.",
    "s03.hint": "Full formats (TBX, Parquet, all pairs): <code>openglossa build-exports</code>.",
    "s04.h2": "Schema",
    "s04.lead":
      "Pydantic v2 models with mandatory provenance — no record without a citable source.",
    "s04.sub_term": "Concept-centric terminology entry (≈ termEntry TBX).",
    "s04.meta_term": "concept",
    "s04.sub_tu": "Aligned parallel segment (≈ tu TMX).",
    "s04.meta_tu": "segment",
    "s04.sub_cand": "Extracted term pair, in the review queue.",
    "s04.meta_cand": "candidate",
    "s05.h2": "Licences",
    "s05.fedlex_name": "Fedlex (SR)",
    "s05.fedlex_sub": "Federal acts DE/FR/IT — text + RDF metadata",
    "s05.fedlex_right": "Reuse, citation required",
    "s05.slds_name": "Federal Supreme Court (SLDS)",
    "s05.slds_sub": "Trilingual regestes (ATF/BGE)",
    "s05.termdat_name": "TERMDAT (LINDAS)",
    "s05.termdat_sub": "Multilingual official terminology",
    "s05.termdat_right": "OGD — redistribution to be confirmed",
    "s05.badge_ok": "reusable",
    "s05.badge_warn": "live / derivatives",
    "s05.hint":
      "Details: <code>LICENSING.md</code>, <code>ATTRIBUTIONS.md</code>. Code Apache-2.0 · data CC-BY-4.0.",
    "s06.h2": "MCP connection",
    "s06.lead":
      "Remote MCP server (Streamable HTTP) — five tools, always-cited responses. Connect it to Cursor, Claude Desktop or any MCP client.",
    "s06.endpoint": "Endpoint",
    "s06.hint_config":
      "Client configuration (Cursor <code>~/.cursor/mcp.json</code> or Claude Desktop):",
    "s06.hint_stdio":
      "stdio-only client? Bridge it with <code>npx mcp-remote https://openglossa-mcp.onrender.com/mcp</code>.",
    "s06.sub_tools": "Tools",
    "s06.sub_pipeline": "Pipeline &amp; local server",
    "footer.top_aria": "Back to top",
    "footer.d_link": "Downloads (TMX · JSONL · CSV · schemas)",
    "footer.l_value": "Apache-2.0 (code) · CC-BY-4.0 (data)",
    "footer.copyright":
      "© 2026 OpenGlossa · unofficial output — always verify the authoritative source.",
    "js.demoQuery": "Schuldner Verzug",
    "js.demoQueryEn": "Schuldner",
    "js.prompt": "Enter a term or phrase to query the translation memory.",
    "js.sameLang": "Choose two different languages.",
    "js.noResult":
      "No results. Try « Schuldner », « bonne foi », « personal data », « prescrizione »…",
    "js.enScope":
      "English: no consolidated Swiss federal law in EN on Fedlex. EN results come mainly from EUR-Lex (EU) and, via MCP, TERMDAT/IATE.",
    "js.unavailableEn":
      "Service unavailable or English not covered offline (requires live server + EUR-Lex).",
    "js.methodEurlex": "hybrid + EUR-Lex",
    "js.searching": "Searching…",
    "js.unavailable": "Search service temporarily unavailable. Please try again shortly.",
    "js.unavailableIt":
      "Search service temporarily unavailable (Italian isn't covered by the offline demo).",
    "js.methodSemantic": "semantic",
    "js.methodLexical": "lexical",
    "js.summary": "{method} search · {n} result(s)",
    "js.targetTerm": "likely target term",
    "js.score": "score",
  },
};

const OG_LANGS = ["fr", "de", "en"];

function ogDetectLang() {
  try {
    const saved = localStorage.getItem("og_lang");
    if (saved && OG_I18N[saved]) return saved;
  } catch (e) {
    /* localStorage may be unavailable */
  }
  const nav = (navigator.language || "fr").slice(0, 2).toLowerCase();
  return OG_I18N[nav] ? nav : "fr";
}

function ogApplyLang(lang) {
  const dict = OG_I18N[lang] || OG_I18N.fr;
  document.documentElement.lang = lang;

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const k = el.getAttribute("data-i18n");
    if (dict[k] != null) el.innerHTML = dict[k];
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    const k = el.getAttribute("data-i18n-ph");
    if (dict[k] != null) el.setAttribute("placeholder", dict[k]);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
    const k = el.getAttribute("data-i18n-aria");
    if (dict[k] != null) el.setAttribute("aria-label", dict[k]);
  });

  if (dict["meta.title"]) document.title = dict["meta.title"];
  const md = document.querySelector('meta[name="description"]');
  if (md && dict["meta.description"]) md.setAttribute("content", dict["meta.description"]);

  document.querySelectorAll(".langsw button").forEach((b) => {
    b.classList.toggle("active", b.dataset.lang === lang);
    b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
  });

  window.OG_LANG = lang;
  window.dispatchEvent(new CustomEvent("og:langchange", { detail: lang }));
}

function ogSetLang(lang) {
  if (!OG_I18N[lang]) return;
  try {
    localStorage.setItem("og_lang", lang);
  } catch (e) {
    /* ignore */
  }
  ogApplyLang(lang);
}

// Expose for app.js (dynamic search strings).
window.OG_I18N = OG_I18N;
window.OG_LANG = ogDetectLang();
window.ogT = function ogT(key) {
  const lang = window.OG_LANG || "fr";
  const d = OG_I18N[lang] || OG_I18N.fr;
  return d[key] != null ? d[key] : OG_I18N.fr[key] != null ? OG_I18N.fr[key] : key;
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".langsw button").forEach((b) => {
    b.addEventListener("click", () => ogSetLang(b.dataset.lang));
  });
  ogApplyLang(window.OG_LANG || ogDetectLang());
});
