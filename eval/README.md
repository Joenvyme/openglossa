# Évaluation (P7)

Mini-benchmark de traduction juridique suisse. Objectif : mesurer la **précision
terminologique avec vs sans ancrage OpenGlossa** (term hit-rate), sur un slice de
SLDS/Fedlex **non** utilisé pour construire le glossaire.

- `term_hit_rate.py` — stub du calcul de term hit-rate.
- Jeu de test : 20 phrases (à committer dans `eval/data/`), avec termes attendus.

Optionnel : COMET / BLEU via `sacrebleu` + `unbabel-comet` sur les segments.
