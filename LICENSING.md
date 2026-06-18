# LICENSING — registre des sources OpenGlossa

> Ce fichier matérialise la **règle dure n°3** (provenance par enregistrement) et
> la **règle dure n°6** (sources à licence de redistribution non confirmée). Il
> est la source de vérité du statut licence de chaque source amont. **Aucune
> ingestion sans licence/condition confirmée et provenance complète.**

## Légende des statuts

| Statut | Signification | Conséquence pipeline |
|--------|---------------|----------------------|
| ✅ VERT | Réutilisation (incl. redistribution) confirmée | Peut être **bundlé** dans les dumps téléchargeables |
| 🟠 ORANGE | Accès gratuit mais **redistribution à confirmer** | **Live-only** via MCP, ou n'exporter que des **dérivés** (pas le texte amont brut) |
| 🔴 ROUGE | Propriétaire / interdit | **Jamais** ingéré |

## Registre (miroir de la §4 de la fiche projet)

| # | Source | Contenu | Langues | Accès / endpoint | Licence / condition | Statut | Rôle |
|---|--------|---------|---------|------------------|---------------------|--------|------|
| 1 | **Fedlex** (Recueil systématique) | Statuts fédéraux parallèles | DE/FR/IT | SPARQL `https://fedlex.data.admin.ch/sparqlendpoint` ; filestore HTML/DOCX/PDF ; RDF (JOLux, ELI) | Réutilisation autorisée incl. commerciale ; citer la source ; ne pas présenter comme officiel. Base : art. 5 LDA | ✅ VERT | Termes + TM alignée par article |
| 2 | **SLDS** (`ipst/slds`, HF) | Regeste trilingues, ~20K arrêts TF, ~60K paires | DE/FR/IT | `datasets.load_dataset("ipst/slds")` | **CC-BY-4.0** | ✅ VERT | TM concept-alignée + exemples |
| 3 | **swiss_leading_decision_summarization** (`rcds/...`, HF) | Décisions TF + résumés | DE/FR/IT | `datasets` | **CC-BY-4.0** | ✅ VERT | TM/texte complémentaire (optionnel) |
| 4 | **TERMDAT** (Chancellerie fédérale) | Termbase officiel ~400K entrées | DE/FR/IT/RM/EN | `termdat.bk.admin.ch` ; LINDAS RDF `register.ld.admin.ch` / SPARQL | Accès gratuit ; **tag de redistribution à confirmer** | 🟠 ORANGE | Backbone terminologique — **live d'abord** |
| 5 | **JURIVOC** (thésaurus TF) | Vocabulaire de matières | DE/FR/IT | À localiser (souvent SKOS/RDF) | **À vérifier** | 🟠 ORANGE | Synonymes / matières |
| 6 | **OpenCaseLaw** | 950k+ décisions, dump Parquet HF, MCP | DE/FR/IT | API / HF Parquet | **À vérifier** | 🟠 ORANGE | TM étendue (optionnel) |
| 7 | **MultiLegalPile** (`joelniklaus/Multi_Legal_Pile`) | Corpus multilingue 689GB | multi | HF | **Licences mixtes** — sous-ensembles permissifs seulement | 🟠 RÉFÉRENCE | Probablement inutile en v1 |

## Questions ouvertes (à trancher — humain)

- [ ] **TERMDAT** : confirmer le tag de redistribution (fiche LINDAS / opendata.swiss,
      contact Chancellerie fédérale — Section terminologie). Tant que non confirmé :
      **live-only**, ne bundler que `concept_id` + URI + dérivés.
- [ ] **JURIVOC** : localiser l'export SKOS/RDF + vérifier la licence.
- [ ] **OpenCaseLaw** : vérifier la licence du dump Parquet HF avant tout export.
- [ ] **MultiLegalPile** : si utilisé, documenter sous-ensemble par sous-ensemble.

## Licence des livrables OpenGlossa

- **Dataset agrégé** : CC-BY-4.0 (`LICENSE-DATA`).
- **Code** (pipeline + MCP + site) : Apache-2.0 (`LICENSE`).
- Attributions amont : `ATTRIBUTIONS.md` + `NOTICE`.

> Mainteneur : à chaque ajout/modification de source, mettre à jour ce tableau,
> `ATTRIBUTIONS.md`, et le test `tests/test_licensing.py` (cohérence registre ↔ code).
