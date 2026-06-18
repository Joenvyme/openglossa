# Évaluation (P7)

Mini-benchmark **reproductible** de précision terminologique juridique : est-ce que
l'ancrage OpenGlossa fait apparaître le **terme officiel** attendu ?

## Métrique — term hit-rate@k

Pour chaque requête source tenue à l'écart (`gold.jsonl`), on récupère les `k`
meilleurs segments parallèles via `search_parallel` et on vérifie si le **terme
cible officiel attendu** apparaît côté cible. `term_hit_rate@k` = fraction de
réussites.

## Conditions comparées (avec vs sans ancrage)

| Condition        | Description |
|------------------|-------------|
| `no-grounding`   | Plancher : aucune ressource (le terme cible est-il déjà dans la requête source ? ≈ 0 entre langues). |
| `lexical`        | RAG lexical OpenGlossa sur la TM officielle. |
| `vector:hashing` | RAG sémantique, encodeur de hachage déterministe (offline/CI). |
| `vector:labse`   | RAG sémantique, encodeur de production **LaBSE** (extra `ml`). |

## Données

- `data/corpus.jsonl` — 200 segments parallèles **officiels** DE/FR du CO
  (SR 220, Fedlex, cités). Sert de base de connaissances pour la récupération.
- `data/gold.jsonl` — 15 requêtes DE **paraphrasées** (pas de copie verbatim) +
  le terme FR officiel attendu + la référence (SR/article).

## Lancer

```bash
python eval/run_eval.py --k 3 \
  --encoders no-grounding lexical vector:hashing vector:labse
# -> tableau + eval/results/baseline.json
```

`vector:labse` nécessite `pip install 'openglossa[ml]'` (télécharge LaBSE).
Les autres conditions sont reproductibles hors-ligne.

## Chiffres de base (committés — `results/baseline.json`)

term hit-rate@3, n = 15 requêtes, corpus = 200 segments :

| Condition        | hit-rate@3 |
|------------------|:----------:|
| no-grounding     | **0.000**  |
| lexical          | **0.600**  |
| vector:hashing   | **0.733**  |
| vector:labse     | **0.933**  |

Lecture : sans ancrage on n'obtient jamais le terme officiel ; l'ancrage lexical
en récupère 60 %, et la recherche **sémantique LaBSE 93 %** (1 seul échec :
`prescri`). Cela quantifie l'apport d'OpenGlossa **et** de l'index vectoriel.

## Extension optionnelle

A/B de traduction complète (COMET/BLEU via `sacrebleu` + `unbabel-comet`) sur les
segments : nécessite un modèle de traduction externe, hors périmètre de ce
harnais déterministe.
