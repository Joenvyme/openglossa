# OpenGlossa

**Infrastructure open source de traduction juridique suisse** : un *termbase* +
une *translation memory* (TM) dérivés **exclusivement de sources officielles
publiques ou sous licence ouverte**, packagés en formats standards (TBX, TMX,
CSV, JSONL, Parquet, glossaire DeepL) et exposés via un **serveur MCP**, pour que
n'importe quel outil IA juridique puisse **ancrer ses traductions DE/FR/IT
(→ RM/EN)** dans des sources officielles **citables**.

OpenGlossa ne remplace pas un moteur de traduction : il le **fiabilise**
(terminologie officielle + exemples alignés + vérification de couples de termes
contre la source).

> ⚠️ **Disclaimer.** Les sorties d'OpenGlossa ne constituent **pas** le texte
> légal officiel faisant foi. Toujours vérifier contre la source officielle
> (n° RS + article Fedlex, ou référence ATF/BGE).

## Licences

- **Code** (pipeline + serveur MCP + site) : [Apache-2.0](LICENSE).
- **Dataset agrégé** : [CC-BY-4.0](LICENSE-DATA).
- Statut licence par source : [LICENSING.md](LICENSING.md) · attributions :
  [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

## Règles dures

1. Sources autorisées uniquement (cf. `LICENSING.md`).
2. Aucun contenu commercial / propriétaire.
3. Provenance par enregistrement (`source`, `source_uri`, `license`, `retrieved_at`).
4. Pas de fabrication (`supported: false` si non sourcé).
5. Jamais présenté comme le texte légal officiel.
6. Source à redistribution non confirmée → **live-only**, pas dans les dumps.
7. Aucune PII au-delà de l'anonymisation déjà faite par les tribunaux.

## Démarrage rapide

> Prérequis : **Python 3.11+**. Recommandé : [`uv`](https://docs.astral.sh/uv/).

```bash
# 1. Installer l'environnement (dev)
make setup            # ou : uv sync --extra dev   /   pip install -e ".[dev]"

# 2. Lancer les tests
make test

# 3. Exporter les JSON Schemas (TermRecord, TranslationUnit)
make schema           # écrit dans schemas/

# 4. Lancer le serveur MCP (HTTP)
make mcp
```

### PoC bout-en-bout (Fedlex → exports → MCP)

```bash
# Ingestion live des actes fédéraux (titres parallèles DE/FR/IT) + exports
openglossa poc                       # ou : python -m openglossa poc

# Étapes séparées
openglossa ingest-fedlex --rs 220 210 101    # titres d'actes (rapide)
openglossa build-exports                      # -> data/exports/ (TMX, JSONL, ...)

# Alignement article/alinéa (Akoma Ntoso eId) — TM fine, citable par article
openglossa ingest-fedlex --articles --rs 220 --max-articles 40

# Regeste trilingues du Tribunal fédéral (SLDS, CC-BY-4.0)
openglossa ingest-slds --limit 200            # -> data/processed/tus_slds.jsonl

# Fusionner les sources (dédup par tu_id) puis exporter
openglossa merge-tus data/processed/tus.jsonl data/processed/tus_slds.jsonl
openglossa build-exports

# Terminologie TERMDAT en live (backbone) — index dérivé uniquement (règle #6)
openglossa ingest-termdat Motion Bundesrat --src de

# Term mining : couples candidats DE→FR depuis le parallèle (co-occurrence Dice)
openglossa mine-terms --in data/processed/tus.jsonl --src de --tgt fr
# ... + ne garder que les couples ABSENTS de TERMDAT (vérif live)
openglossa mine-terms --src de --tgt fr --check-termdat --novel-only

# Index sémantique (sqlite-vec) pour search_parallel — LaBSE (prod) ou hashing
openglossa build-index --encoder labse   # -> data/processed/tm_index.db
```

Le serveur MCP interroge **TERMDAT en live** pour `lookup_term` et
`verify_translation` (équivalents officiels DE/FR/IT/RM/EN + définition + base
légale, cités). Quand l'anglais est impliqué, **IATE** (terminologie UE, API
live) et **EUR-Lex/CELLAR** (législation UE parallèle, SPARQL live) sont aussi
consultés — licences UE (2011/833, CC-BY 4.0) avec attribution. **Anglais et
romanche** : terminologie administrative TERMDAT/IATE et TM UE EUR-Lex — pas de
loi consolidée faisant foi (Fedlex = DE/FR/IT). Le MCP renvoie `en_scope` /
`iate_scope` / `eurlex_scope` ;
`get_official_text(lang="en")` est refusé explicitement. TERMDAT étant en
statut 🟠 (redistribution non confirmée), aucun texte brut n'est écrit sur disque :
seul un index dérivé (`concept_id` + URI + identifiant + langues + base légale).

Le serveur MCP lit `data/processed/*.jsonl` et expose (transport **Streamable
HTTP**, à ajouter comme connecteur custom dans Claude) :

- `lookup_term(query, src, tgt, domain?)` — traductions officielles + définition
  + base légale, **citées** (termbase local + TERMDAT live optionnel) ;
- `search_parallel(text, src, tgt, k)` — exemples parallèles cités (RAG few-shot),
  insensible à l'orientation des TUs ; **sémantique** via index sqlite-vec/LaBSE
  s'il est présent (`build-index`), sinon repli **lexical** déterministe ;
- `verify_translation(src, tgt, …)` — le couple est-il **attesté en source
  officielle** ? (termbase **et** TM Fedlex/SLDS) ; renvoie `false` proprement ;
- `get_official_text(eli_or_citation, lang)` — **texte officiel Fedlex en live**
  (ex. « SR 220 Art. 1 al. 1 ») avec URI ELI citable ;
- `suggest_glossary(text, src, tgt)` *(stretch)* — termes d'un passage + leurs
  traductions officielles citées.

Toutes les réponses incluent les citations et un `disclaimer` (sortie non
officielle).

### Hébergement (Vercel)

Le serveur MCP se déploie en **fonction serverless** sur Vercel (Streamable HTTP
en mode *stateless*). Le dépôt est préconfiguré :

- `api/index.py` — point d'entrée Vercel ; expose l'app ASGI FastMCP (`app`),
  amorcée avec la TM de démo citée (`web/downloads/openglossa_demo.jsonl`) ;
- `requirements.txt` — dépendances légères de la fonction (sans torch/LaBSE :
  la recherche sémantique est désactivée en serverless, repli lexical) ;
- `vercel.json` — sert le site statique (`web/`) et réécrit `/mcp` → `/api/index`.

```bash
npm i -g vercel
vercel            # déploiement de préversion
vercel --prod     # production
```

Endpoint MCP public : `https://openglossa-mcp.onrender.com/mcp` (Render, recherche
sémantique MiniLM sur le corpus complet). Le site `https://openglossa.ch`
(hébergé sur Vercel) présente le projet et les téléchargements. Les outils live
(`get_official_text`, TERMDAT) restent best-effort et dégradent proprement.

`mine-terms` extrait des **couples de termes candidats** du parallèle par
co-occurrence (coefficient de Dice), avec `score`, `support` et **preuve de
source** (segments officiels). C'est une file de revue *human-in-the-loop*
(`review_status: candidate`) — aucun couple n'est présenté comme vérifié sans
relecture. `--check-termdat` signale (ou, avec `--novel-only`, filtre) les
couples déjà connus de TERMDAT.

`build-exports` génère **TMX 1.4**, **TBX-Basic (DCA)**, **glossaire DeepL CSV**
(par paire de langues), **JSONL** et **Parquet** (colonnes plates + colonne
`record` JSON sans perte, interrogeable en DuckDB/polars). Les fichiers TMX/TBX
sont **validés** : structurellement et contre une **DTD** (TMX 1.4 canonique de
LISA OSCAR + profil TBX OpenGlossa, dans `schemas/dtd/`). Round-trip garanti
(export → ré-import → égalité) couvert par les tests.

Sur **Windows PowerShell** (sans `make`) :

```powershell
uv sync --extra dev
uv run pytest
uv run python -m openglossa.schemas      # export JSON Schema
uv run python -m openglossa.mcp.server   # serveur MCP
```

## Arborescence

```
openglossa/
├── src/openglossa/
│   ├── schemas.py        # pydantic v2 : TermRecord, TranslationUnit
│   ├── sources/          # fedlex, slds, termdat, jurivoc (+ provenance)
│   ├── align/            # eli-structural, labse
│   ├── mining/           # term extraction + verify
│   ├── search/           # index vectoriel sqlite-vec (LaBSE/hashing)
│   ├── export/           # tbx, tmx, deepl_csv, jsonl, parquet, validate (DTD)
│   └── mcp/server.py     # outils MCP (lookup/search/verify/get_official_text)
├── eval/                 # mini-benchmark traduction juridique
├── data/                 # raw/ (gitignored), processed/, exports/
├── web/                  # site statique
└── tests/
```

## Roadmap (phases)

| Phase | Objet | Statut |
|-------|-------|--------|
| P0 | Setup (repo, licences, schémas, connecteurs) | ✅ |
| P1 | Ingest Fedlex (SPARQL + Akoma Ntoso, alignement par eId article/alinéa) | ✅ |
| P2 | Ingest SLDS (TU regeste trilingues, groupées par décision) | ✅ |
| P3 | Backbone terminologique TERMDAT (live LINDAS, schema.org) | ✅ (JURIVOC en backlog) |
| P4 | Term mining + verify (human-in-the-loop) | ✅ (baseline co-occurrence ; LaBSE/eflomal en backlog) |
| P5 | Packaging / exports (TBX/TMX/CSV/JSONL/Parquet) + validation DTD + round-trip | ✅ |
| P6 | Serveur MCP (lookup/search/verify/get_official_text + suggest_glossary) | ✅ |
| P7 | Évaluation reproductible (term hit-rate avec/sans ancrage ; baseline committée) | ✅ |
| P8 | Site statique (démo de recherche citée, téléchargements, schéma, licences) | ✅ |

Voir [`PROJECT.md`](PROJECT.md) pour la fiche complète.
