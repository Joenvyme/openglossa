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
openglossa build-exports
```

Le serveur MCP lit `data/processed/*.jsonl` ; `search_parallel` renvoie des
segments officiels **cités** (n° RS + URI ELI Fedlex).

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
│   ├── export/           # tbx, tmx, deepl_csv, parquet
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
| P2 | Ingest SLDS (TU regeste trilingues) | ⬜ |
| P3 | Backbone terminologique (TERMDAT live) | ⬜ |
| P4 | Term mining + verify (human-in-the-loop) | ⬜ |
| P5 | Packaging / exports (TBX/TMX/...) | ⬜ |
| P6 | Serveur MCP | ⬜ |
| P7 | Évaluation (term hit-rate) | ⬜ |
| P8 | Site statique | ⬜ |

Voir [`PROJECT.md`](PROJECT.md) pour la fiche complète.
