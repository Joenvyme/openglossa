# OpenGlossa — Fiche projet (v0.1)

> Brief de démarrage destiné à un **agent dev IA**. Prose explicative en français, identifiants techniques / schémas / commandes en anglais. À déposer tel quel dans le contexte de l'agent ou à la racine du repo (`PROJECT.md` / `CLAUDE.md`).

---

## 1. Mission

**OpenGlossa** est une infrastructure **open source** de traduction juridique suisse : un *termbase* + une *translation memory* (TM) dérivés **exclusivement de sources officielles publiques ou sous licence ouverte**, packagés dans des formats standards et exposés via un **serveur MCP**, pour que n'importe quel outil IA juridique puisse **ancrer ses traductions DE/FR/IT (→ RM/EN)** dans des sources officielles **citables**.

OpenGlossa ne remplace pas un moteur de traduction : il le **fiabilise** (terminologie officielle + exemples alignés + vérification de couples de termes contre la source).

Le facteur de confiance pour des juristes = **la citabilité**. Chaque entrée pointe vers sa source (n° RS + article Fedlex, ou référence ATF/BGE).

---

## 2. Règles dures (NON négociables pour l'agent)

1. **Sources autorisées uniquement.** N'ingérer que les sources de la table §4 dont la licence/condition est confirmée. Aucune autre source sans validation humaine.
2. **Aucun contenu commercial / sous licence propriétaire** (Weblaw, Jusletter, Swisslex, éditeurs privés, etc.). Jamais.
3. **Provenance par enregistrement.** Chaque record stocke `source`, `source_uri`, `license`, `retrieved_at`. Pas de provenance ⇒ pas d'ingestion.
4. **Pas de fabrication.** Le MCP et le pipeline ne « devinent » jamais une traduction officielle. Si aucune source ne supporte un couple, le dire explicitement (`supported: false`).
5. **Ne jamais présenter une sortie comme le texte légal officiel faisant foi.** Disclaimer obligatoire sur le site, dans le README et dans les réponses MCP.
6. **Source à licence de redistribution non confirmée** (TERMDAT, JURIVOC, OpenCaseLaw au moment d'écrire) : **ne pas l'inclure dans les dumps téléchargeables**. Soit on l'interroge **en live** via le MCP (accès gratuit), soit on ne publie que des **alignements dérivés** sans le texte amont brut. Tenir `LICENSING.md` à jour.
7. **PII.** Aucune donnée personnelle au-delà de ce que les tribunaux ont déjà anonymisé.

---

## 3. Périmètre

**Inclus**
- Paires linguistiques : **DE / FR / IT** (cœur). **RM** et **EN** où la source le permet (stretch).
- Deux artefacts : **termbase** (concept-centré) + **translation memory** (segments alignés).
- Exports : **TBX**, **TMX**, **CSV**, **JSONL**, **Parquet**, **glossaire DeepL (CSV)**.
- **Serveur MCP** (HTTP) avec outils lookup / search / verify.
- **Harnais d'évaluation** (mini-benchmark de traduction juridique suisse).
- **Site statique** : téléchargements + doc + registre de licences + démo de recherche.

**Exclu (v1)**
- Pas de moteur de TM complet ni de fine-tuning de LLM (OpenGlossa augmente, n'entraîne pas).
- Pas de couche éditoriale propriétaire.
- Pas de législation cantonale en v1 (Fedlex fédéral d'abord ; cantonal = backlog via Lexfind/Fedlex).

---

## 4. Sources & licences (registre — à recopier dans `LICENSING.md`)

| # | Source | Contenu | Langues | Accès / endpoint | Licence / condition | Statut | Rôle dans OpenGlossa |
|---|--------|---------|---------|------------------|---------------------|--------|----------------------|
| 1 | **Fedlex** (Recueil systématique, lois consolidées) | Statuts fédéraux parallèles | DE/FR/IT | SPARQL `https://fedlex.data.admin.ch/sparqlendpoint` ; filestore HTML/DOCX/PDF ; métadonnées RDF (ontologie JOLux, identifiants ELI) | Réutilisation autorisée **incl. commerciale** ; citer la source ; ne pas présenter comme officiel. Base : **art. 5 LDA** (lois & décisions non protégées) | ✅ VERT | Extraction de termes + TM alignée par article |
| 2 | **SLDS** (`ipst/slds`, Hugging Face) | Regeste (headnotes) trilingues, 20K arrêts TF 1954–2024, ~60K paires | DE/FR/IT | `datasets.load_dataset("ipst/slds")` | **CC-BY-4.0** | ✅ VERT | TM concept-alignée + exemples par domaine |
| 3 | **swiss_leading_decision_summarization** (`rcds/...`, HF) | Décisions TF + résumés | DE/FR/IT | `datasets` | **CC-BY-4.0** (conforme conditions TF) | ✅ VERT | TM/texte complémentaire (optionnel) |
| 4 | **TERMDAT** (Chancellerie fédérale) | Termbase officiel ~400K entrées (termes + équivalents + définitions + base légale) | DE/FR/IT/RM/EN | `termdat.bk.admin.ch` (UI/API) ; LINDAS RDF `register.ld.admin.ch` / SPARQL LINDAS | Accès gratuit ; **tag de redistribution à confirmer** (modèle opendata.swiss « libre utilisation, source obligatoire ») | 🟠 ORANGE | Backbone terminologique — **live d'abord** |
| 5 | **JURIVOC** (thésaurus du Tribunal fédéral) | Vocabulaire de matières juridiques | DE/FR/IT | À localiser (souvent SKOS/RDF) | **À vérifier** | 🟠 ORANGE | Synonymes / matières (enrichissement) |
| 6 | **OpenCaseLaw** | 950k+ décisions, dump Parquet HF, MCP | DE/FR/IT | API / HF Parquet | **À vérifier** | 🟠 ORANGE | TM étendue (corps des décisions) — optionnel |
| 7 | **MultiLegalPile** (`joelniklaus/Multi_Legal_Pile`) | Corpus multilingue 689GB, sous-ensembles suisses | multi | HF | **Licences mixtes** — n'utiliser que les sous-ensembles permissifs | 🟠 RÉFÉRENCE | Probablement inutile en v1 |

**Réutilisables côté outillage** (ne pas réinventer) :
- **Fedlex Connector MCP** (`https://mcp.fedlex-connector.ch`, open source) — interroge SPARQL + filestore HTML, renvoie actes/articles DE/FR/IT. À **forker / composer** pour la récupération Fedlex et l'outil `get_official_text`.
- Helpers Fedlex : `droid-f/fedlex`, `bequrios/fedlex` (tutoriels SPARQL).

**Licence des livrables**
- Dataset agrégé OpenGlossa : **CC-BY-4.0** (compatible avec les sources CC-BY et les conditions Fedlex).
- Code (pipeline + serveur MCP + site) : **Apache-2.0** (grant de brevet explicite, sain pour un MCP réutilisé par des tiers).
- Fournir `NOTICE` + `ATTRIBUTIONS.md` listant chaque source amont et sa citation.

---

## 5. Modèle de données

Deux types d'enregistrements. Définir en **pydantic v2** et figer le schéma JSON.

### 5.1 Term record (concept-centré, équivalent d'un `termEntry` TBX)

```json
{
  "concept_id": "og:term:0001",
  "domain": ["civil_law", "obligations"],
  "legal_basis": ["SR 220 Art. 102"],
  "definition": { "de": "...", "fr": "...", "it": "..." },
  "terms": {
    "de": [{ "text": "Verzug", "pos": "noun", "status": "preferred" }],
    "fr": [{ "text": "demeure", "pos": "noun", "status": "preferred" }],
    "it": [{ "text": "mora", "pos": "noun", "status": "preferred" }],
    "rm": [],
    "en": []
  },
  "authority": "statutory",            // statutory | jurisprudential | administrative
  "sources": [
    { "name": "TERMDAT", "uri": "https://www.termdat.bk.admin.ch/entry/...", "license": "OGD-open-use" }
  ],
  "confidence": 0.92,
  "review_status": "verified"          // candidate | verified | rejected
}
```

### 5.2 Translation unit (TU — segment parallèle)

```json
{
  "tu_id": "og:tu:7f3a...",
  "src_lang": "de",
  "tgt_lang": "fr",
  "src": "Der Schuldner kommt in Verzug, ...",
  "tgt": "Le débiteur est en demeure, ...",
  "domain": ["obligations"],
  "source": { "name": "SLDS", "ref": "BGE 146 IV 226", "uri": "...", "license": "CC-BY-4.0" },
  "alignment": { "method": "eli-structural", "score": 0.98 }  // eli-structural | labse | manual
}
```

---

## 6. Pipeline (phases avec critères d'acceptation)

> Chaque phase produit des artefacts versionnés + tests. Sortie intermédiaire en JSONL ; sortie analytique en Parquet/DuckDB.

- **P0 — Setup.** Repo, licences (`LICENSE` Apache-2.0, `LICENSE-DATA` CC-BY-4.0), `LICENSING.md`, `ATTRIBUTIONS.md`, env (`uv`/`pip`), arborescence data, connecteurs sources avec capture de provenance.
  *Acceptation :* `make setup` OK ; `LICENSING.md` reflète la table §4.

- **P1 — Ingest Fedlex.** SPARQL → énumérer les actes en vigueur + URIs ELI ; récupérer les manifestations HTML DE/FR/IT depuis le filestore ; normaliser ; **aligner par structure ELI/eId** (même article/alinéa entre langues) → segments parallèles niveau article.
  *Acceptation :* N actes ingérés, alignés par article, provenance présente ; échantillon de 20 articles vérifié manuellement (alignement correct sur les 3 langues).

- **P2 — Ingest SLDS (+ rcds optionnel).** `datasets` → construire les TU regeste trilingues (DE↔FR, DE↔IT, FR↔IT) par identifiant d'arrêt.
  *Acceptation :* ~60K paires normalisées avec provenance + licence ; dédoublonnage par hash.

- **P3 — Backbone terminologique.** TERMDAT : **interroger en live** (LINDAS SPARQL / API termdat) → records concept avec équivalents / domaine / base légale. Fusionner les matières JURIVOC. (Bundler le dump TERMDAT **seulement** si licence confirmée — sinon, ne stocker que `concept_id` + URI + dérivés.)
  *Acceptation :* records de termes avec ≥ DE/FR/IT pour le cœur ; provenance + statut licence par record.

- **P4 — Term mining depuis le parallèle.** Extraction de termes candidats : statistique (log-likelihood, c-value) + tables de phrases (`fast_align`/`eflomal` sur segments Fedlex alignés) + alignement par embeddings (**LaBSE** via `sentence-transformers`, ou `simalign`). Proposer les couples **absents de TERMDAT**. Normalisation + **vérification LLM contre la source** (étape `verify`). File de revue *human-in-the-loop*.
  *Acceptation :* liste de candidats avec `confidence` + preuve de source ; précision échantillonnée ≥ seuil convenu sur un set annoté.

- **P5 — Packaging / exports.** Générer **TBX** (termbase), **TMX** (TM), **CSV**, **JSONL**, **Parquet**, **glossaire DeepL (CSV : `source,target` par paire de langues)**. Valider TBX/TMX contre DTD/XSD.
  *Acceptation :* tous les formats valident ; test de round-trip (export → ré-import → égalité).

- **P6 — Serveur MCP.** Implémenter les outils §7. Transport **HTTP (Streamable HTTP)** pour ajout comme connecteur custom dans claude.ai / Claude Desktop (même schéma que Fedlex Connector).
  *Acceptation :* outils appelables ; chaque réponse inclut des citations ; conformité au contrat ; `verify_translation` renvoie `false` proprement quand non supporté.

- **P7 — Évaluation.** Mini-benchmark de traduction juridique suisse (slice de SLDS/Fedlex **non** utilisé pour construire le glossaire). Mesurer la **précision terminologique avec vs sans** ancrage OpenGlossa (term hit-rate), + optionnellement COMET/BLEU (`sacrebleu`, `unbabel-comet`) sur les segments.
  *Acceptation :* script d'éval reproductible + chiffres de base (baseline) committés.

- **P8 — Site.** Statique : téléchargements, doc, schéma, registre de licences, **démo de recherche** appelant l'API/MCP (résultats cités).
  *Acceptation :* déploie ; téléchargements OK ; la démo renvoie des résultats sourcés.

---

## 7. Contrats des outils MCP (le différenciateur)

Toutes les réponses **doivent** inclure les citations de sources.

```
lookup_term(query, src_lang, tgt_lang, domain?)
  -> [{ term, translations[], domain, authority, definition?, sources[] }]

search_parallel(text, src_lang, tgt_lang, k=5)
  -> [{ src, tgt, source{name, ref, uri}, score }]      # RAG few-shot

verify_translation(src_term, tgt_term, src_lang, tgt_lang)
  -> { supported: bool, evidence: sources[], note }      # le couple existe-t-il en source officielle ?

get_official_text(eli_or_citation, lang)
  -> { text, uri, lang }                                 # délègue à Fedlex (réutiliser Fedlex Connector)

# stretch
suggest_glossary(text, src_lang, tgt_lang)
  -> [{ term, translation, sources[] }]                  # extrait les termes d'un passage + leurs trads officielles
```

---

## 8. Stack technique (choix recommandés, à figer)

- **Pipeline** : Python 3.11+ — `datasets`, `polars`/`pandas`, `rdflib`+`SPARQLWrapper`, `lxml` (parsing HTML Fedlex), `sentence-transformers` (LaBSE), `eflomal`/`fast_align` ou `simalign`, `sacrebleu` + `unbabel-comet` (éval), `pydantic` v2.
- **Stockage** : **DuckDB + Parquet** pour la TM (fichier, reproductible) ; index vectoriel **`sqlite-vec`** ou **LanceDB** pour `search_parallel` ; DuckDB/SQLite pour les termes.
- **Serveur MCP** : Python MCP SDK (style FastMCP), transport HTTP. Partage le code du pipeline.
- **Exports** : TBX/TMX via templates XML (`lxml`) validés ; CSV/JSONL/Parquet via `polars`.
- **Site** : Astro ou Next.js sur Vercel ; téléchargements depuis release GitHub / HF Hub ; démo → API/MCP.
- **Distribution** : repo GitHub (Apache-2.0) ; dataset sur **Hugging Face Hub** (CC-BY-4.0) + **Zenodo** (DOI citable).
- **CI** : validation de schéma + check du registre de licences + petite éval sur les PR.

---

## 9. Arborescence du repo (cible)

```
openglossa/
├── PROJECT.md                  # cette fiche
├── LICENSE                     # Apache-2.0 (code)
├── LICENSE-DATA                # CC-BY-4.0 (dataset)
├── LICENSING.md                # registre §4, statut par source + questions ouvertes
├── ATTRIBUTIONS.md / NOTICE
├── pyproject.toml
├── src/openglossa/
│   ├── schemas.py              # pydantic: TermRecord, TranslationUnit
│   ├── sources/
│   │   ├── fedlex.py           # SPARQL + filestore + alignement ELI
│   │   ├── slds.py             # loader HF
│   │   ├── termdat.py          # LINDAS/API (live)
│   │   └── jurivoc.py
│   ├── align/                  # eli-structural, labse
│   ├── mining/                 # term extraction + verify
│   ├── export/                 # tbx.py, tmx.py, deepl_csv.py, parquet.py
│   └── mcp/server.py           # outils §7
├── eval/                       # benchmark + scripts
├── data/                       # raw/ (gitignored), processed/, exports/
├── web/                        # site statique
└── tests/
```

---

## 10. Premières tâches (checklist de démarrage pour l'agent)

1. Scaffolder le repo + licences + `LICENSING.md` (recopier la table §4, marquer les 🟠 « à confirmer »).
2. Implémenter `sources/fedlex.py` : requête SPARQL renvoyant, pour un acte donné, les URIs ELI des 3 versions linguistiques + provenance. Test sur le CO (SR 220).
3. Implémenter `sources/slds.py` : charger `ipst/slds`, mapper vers `TranslationUnit` (DE↔FR, DE↔IT, FR↔IT) avec provenance + licence.
4. Définir `schemas.py` (pydantic) pour `TermRecord` et `TranslationUnit` + export JSON Schema.
5. **PoC bout-en-bout** sur un slice : 50 termes (depuis TERMDAT live) + 500 segments (Fedlex + SLDS) → exports **TBX + TMX + glossaire DeepL CSV** + **un** outil MCP (`lookup_term`) servant ce slice. Inclure les citations.
6. Écrire le stub d'éval (term hit-rate avec/sans ancrage) sur 20 phrases tests.
7. Ouvrir une issue « Confirmer la licence de redistribution TERMDAT/JURIVOC/OpenCaseLaw » avec liens LINDAS/opendata.swiss à vérifier.

Itérer ensuite phase par phase (§6).

---

## 11. Questions ouvertes à trancher (humain)

- Confirmer le **tag de redistribution** TERMDAT + JURIVOC + OpenCaseLaw (fiche LINDAS/opendata.swiss / contact Chancellerie fédérale, Section terminologie).
- Inclure le **romanche** dès la v1 ? (différenciateur fort, peu couvert ailleurs — TERMDAT le fournit).
- Projet **personnel / commun de la legaltech CH** vs **brandé** — décision de gouvernance et de discours (impacte README, nom d'org GitHub/HF, et communication).
