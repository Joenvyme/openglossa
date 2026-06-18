# OpenGlossa v0.1.0

Première version d'**OpenGlossa** — termbase et mémoire de traduction **open source** pour la traduction juridique suisse (DE/FR/IT), ancrés dans des sources officielles **citables**. Les phases P0 à P8 de la fiche projet sont complètes.

> ⚠️ Les sorties d'OpenGlossa ne constituent **pas** le texte légal officiel faisant foi. Toujours vérifier contre la source officielle (n° RS + article Fedlex, ou référence ATF/BGE).

## Points forts

- **Pipeline d'ingestion** d'actes fédéraux (Fedlex) via SPARQL + Akoma Ntoso, avec **alignement structurel par `eId`** au niveau article/alinéa, et ingestion des **regestes trilingues** du Tribunal fédéral (SLDS).
- **Backbone terminologique TERMDAT** en live (LINDAS, schema.org), avec garde-fou de redistribution (dérivés uniquement, règle #6).
- **Term mining** depuis le parallèle (co-occurrence / Dice) avec preuve de source et file de revue *human-in-the-loop* ; filtre « absent de TERMDAT ».
- **Exports** TBX / TMX / CSV / JSONL / Parquet, **validés** (DTD TMX 1.4 + profil TBX) et **round-trip** testés.
- **Serveur MCP** (Streamable HTTP) avec 5 outils **cités** : `lookup_term`, `search_parallel`, `verify_translation`, `get_official_text` (texte Fedlex en live), `suggest_glossary`.
- **Recherche sémantique** : index vectoriel **sqlite-vec** + **LaBSE** (repli lexical déterministe).
- **Évaluation reproductible** (term hit-rate@k) avec baseline committée.
- **Site statique** avec démo de recherche citée et téléchargements.

## Évaluation (baseline term hit-rate@3, n=15)

| Condition | hit-rate |
|---|:--:|
| sans ancrage | 0.00 |
| lexical | 0.60 |
| vectoriel (hashing) | 0.73 |
| **vectoriel (LaBSE)** | **0.93** |

L'ancrage OpenGlossa + la recherche sémantique font passer la précision terminologique de 0 % à 93 %.

## Phases livrées

- **P0** Setup (repo, licences, schémas pydantic v2, connecteurs)
- **P1** Ingest Fedlex (SPARQL + Akoma Ntoso, alignement eId)
- **P2** Ingest SLDS (regestes trilingues groupés par décision)
- **P3** Backbone TERMDAT (live LINDAS)
- **P4** Term mining + verify (human-in-the-loop)
- **P5** Packaging / exports + validation DTD + round-trip
- **P6** Serveur MCP (+ index vectoriel LaBSE)
- **P7** Évaluation reproductible (baseline committée)
- **P8** Site statique (démo citée, téléchargements, schéma, licences)

## Démarrage rapide

```bash
pip install -e ".[all]"
openglossa ingest-fedlex --articles --rs 220 --max-articles 200
openglossa build-index --encoder labse        # recherche sémantique
openglossa build-exports                       # TBX / TMX / CSV / JSONL / Parquet
python -m openglossa.mcp.server                # serveur MCP (Streamable HTTP)
```

## Licences

Code sous **Apache-2.0**, données sous **CC-BY-4.0**. Voir `LICENSING.md` et `ATTRIBUTIONS.md`. Statut des sources : Fedlex ✅, SLDS ✅ (CC-BY-4.0), TERMDAT 🟠 (redistribution à confirmer — live / dérivés uniquement).

## Backlog (non bloquant)

JURIVOC (connecteur), LaBSE/eflomal pour le mining, XSD TBX complet, A/B COMET/BLEU, packaging des DTD dans le wheel, connecteur MCP dans Claude Desktop.

**Changelog** : `cb68fab..582db3a`
