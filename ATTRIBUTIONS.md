# ATTRIBUTIONS

OpenGlossa agrège des données dérivées de sources officielles suisses et de jeux
de données ouverts. Toute redistribution du dataset agrégé (CC-BY-4.0) doit
conserver les attributions ci-dessous. Voir `LICENSING.md` pour le statut licence
détaillé de chaque source.

## Sources amont

### Fedlex — Recueil systématique du droit fédéral
- Éditeur : Chancellerie fédérale suisse.
- Accès : https://fedlex.data.admin.ch/ (SPARFL + filestore + RDF/ELI).
- Condition : réutilisation autorisée (incl. commerciale) ; citer la source ;
  ne pas présenter comme texte officiel faisant foi. Base : art. 5 LDA.

### SLDS — Swiss Leading Decision Summarization (`ipst/slds`)
- Regeste (headnotes) trilingues du Tribunal fédéral, 1954–2024.
- Accès : Hugging Face Hub — https://huggingface.co/datasets/ipst/slds
- Licence : CC-BY-4.0.

### swiss_leading_decision_summarization (`rcds/...`)
- Décisions du Tribunal fédéral + résumés.
- Accès : Hugging Face Hub.
- Licence : CC-BY-4.0 (conforme conditions TF).

### TERMDAT — Banque de données terminologiques (Chancellerie fédérale)
- Termbase officiel multilingue (~400K entrées).
- Accès : https://www.termdat.bk.admin.ch/ ; LINDAS RDF.
- Statut : redistribution **à confirmer** — voir `LICENSING.md`.

### IATE — InterActive Terminology for Europe (Commission européenne)
- Termbase institutionnelle multilingue de l'UE (dont anglais).
- Accès : https://iate.europa.eu/ ; API `https://iate.europa.eu/em-api/`.
- Licence : Décision 2011/833/UE — réutilisation libre avec attribution
  « © European Union — IATE (https://iate.europa.eu) ».

### EUR-Lex / CELLAR — Législation de l'Union européenne
- Textes législatifs et résumés multilingues officiels (dont anglais).
- Accès : https://eur-lex.europa.eu/ ; SPARQL CELLAR
  `https://publications.europa.eu/webapi/rdf/sparql`.
- Licence : CC-BY 4.0 (contenu éditorial) ; actes selon Décision 2011/833/UE —
  attribution « © European Union — EUR-Lex (https://eur-lex.europa.eu) ».

### JURIVOC — Thésaurus du Tribunal fédéral
- Statut : licence **à vérifier** — voir `LICENSING.md`.

## Outillage réutilisé

- **Fedlex Connector MCP** (open source) — https://mcp.fedlex-connector.ch
  À composer/forker pour `get_official_text` et la récupération Fedlex.
- Helpers Fedlex : `droid-f/fedlex`, `bequrios/fedlex`.

## Citation suggérée du dataset OpenGlossa

> OpenGlossa contributors (2026). *OpenGlossa: an open termbase & translation
> memory for Swiss legal translation, grounded in official sources.* CC-BY-4.0.
