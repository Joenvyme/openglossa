"""Statistical term mining from parallel translation units (P4).

Approach (deterministic, dependency-free):

1. **Monolingual candidates** — extract noun-phrase-like n-grams (1..3 tokens)
   per language, filtered by stopwords and corpus frequency.
2. **Cross-lingual pairing** — "translation spotting" by co-occurrence: a source
   term ``s`` and target term ``t`` are paired when they co-occur across the same
   official segments more than chance, scored by the Dice coefficient
   ``2·a / (df_s + df_t)`` where ``a`` is the co-occurrence count.
3. **verify** — re-collect the official segments backing a pair (the evidence).
   Never fabricates: a pair with zero support is unsupported.

Heavy aligners (eflomal/fast_align) and embedding aligners (LaBSE/simalign)
remain optional future backends; this module gives a defensible, testable
baseline that runs offline on already-ingested parallel data.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence

from ..schemas import Evidence, Lang, TermCandidate, TranslationUnit

__all__ = [
    "candidate_terms",
    "mine_pairs",
    "verify",
    "STOPWORDS",
]

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

# Minimal closed-class stopword lists (articles, prepositions, conjunctions,
# pronouns, auxiliaries) for the three core languages. Kept small on purpose.
STOPWORDS: dict[str, frozenset[str]] = {
    "de": frozenset(
        """der die das den dem des ein eine einen einem einer eines und oder aber
        nicht kein keine als auch wenn weil dass ob wie wo bei mit von zu zum zur
        im in an auf aus für gegen ohne um über unter vor nach durch ist sind war
        waren wird werden worden sein hat haben hatte haben kann können muss müssen
        soll sollen darf dürfen man sie er es wir ihr ich du diese dieser dieses
        jede jeder jedes alle aller allen so nur noch schon sowie sowohl beziehungsweise""".split()
    ),
    "fr": frozenset(
        """le la les un une des du de au aux et ou mais ne pas que qui quoi dont où
        si comme car donc or ni à dans en sur sous pour par avec sans vers chez
        entre est sont était étaient sera seront été être a ont avait avaient avoir
        ce cet cette ces son sa ses leur leurs notre nos votre vos mon ma mes ton
        ta tes il elle ils elles on nous vous je tu se sy y en aussi ainsi selon""".split()
    ),
    "it": frozenset(
        """il lo la i gli le un uno una dei degli delle del della di a da in con su
        per tra fra e o ma se che chi cui dove come perché quando è sono era erano
        sarà saranno stato essere ha hanno aveva avevano avere questo questa questi
        queste suo sua suoi sue loro nostro vostro mio tuo egli ella esso essa noi
        voi io tu si non anche così secondo nonché ovvero""".split()
    ),
}


def _tokens(text: str) -> list[str]:
    return [m.group(0) for m in _WORD.finditer(text)]


def _ngrams(text: str, lang: str, n_max: int = 3) -> set[str]:
    """Return the set of candidate n-grams (1..n_max) present in ``text``.

    A candidate is rejected when its first/last token is a stopword, when every
    token is a stopword, or when any token is a single character. Matching keys
    are casefolded so surface variants collapse.
    """

    stop = STOPWORDS.get(lang, frozenset())
    toks = [t.casefold() for t in _tokens(text)]
    out: set[str] = set()
    for n in range(1, n_max + 1):
        for i in range(len(toks) - n + 1):
            gram = toks[i : i + n]
            if any(len(t) < 2 for t in gram):
                continue
            if gram[0] in stop or gram[-1] in stop:
                continue
            if all(t in stop for t in gram):
                continue
            out.add(" ".join(gram))
    return out


def _orient(
    tus: Iterable[TranslationUnit], src_lang: Lang, tgt_lang: Lang
) -> list[tuple[str, str, TranslationUnit]]:
    """Orient TUs to ``(src_lang -> tgt_lang)``, swapping reversed pairs."""

    src, tgt = str(src_lang), str(tgt_lang)
    pairs: list[tuple[str, str, TranslationUnit]] = []
    for tu in tus:
        sl, tl = str(tu.src_lang), str(tu.tgt_lang)
        if sl == src and tl == tgt:
            pairs.append((tu.src, tu.tgt, tu))
        elif sl == tgt and tl == src:
            pairs.append((tu.tgt, tu.src, tu))
    return pairs


def candidate_terms(
    texts: Iterable[str], lang: Lang | str, *, n_max: int = 3, min_count: int = 2
) -> Counter[str]:
    """Document-frequency of candidate n-grams over ``texts`` (one count per text)."""

    lang = str(lang)
    df: Counter[str] = Counter()
    for text in texts:
        df.update(_ngrams(text, lang, n_max))
    return Counter({g: c for g, c in df.items() if c >= min_count})


def mine_pairs(
    tus: Sequence[TranslationUnit],
    src_lang: Lang,
    tgt_lang: Lang,
    *,
    n_max: int = 3,
    min_count: int = 3,
    min_support: int = 3,
    min_score: float = 0.34,
    max_evidence: int = 3,
    one_best: bool = True,
) -> list[TermCandidate]:
    """Mine source→target term pairs by co-occurrence (Dice) over official TUs."""

    oriented = _orient(tus, src_lang, tgt_lang)
    if not oriented:
        return []

    src_l, tgt_l = str(src_lang), str(tgt_lang)
    df_s: Counter[str] = Counter()
    df_t: Counter[str] = Counter()
    cooc: dict[tuple[str, str], int] = defaultdict(int)
    support_tus: dict[tuple[str, str], list[TranslationUnit]] = defaultdict(list)

    for src_text, tgt_text, tu in oriented:
        s_grams = _ngrams(src_text, src_l, n_max)
        t_grams = _ngrams(tgt_text, tgt_l, n_max)
        df_s.update(s_grams)
        df_t.update(t_grams)
        for s in s_grams:
            for t in t_grams:
                key = (s, t)
                cooc[key] += 1
                if len(support_tus[key]) < max_evidence:
                    support_tus[key].append(tu)

    # Score every co-occurring pair where both sides clear the frequency floor.
    scored: list[tuple[str, str, float, int]] = []
    for (s, t), a in cooc.items():
        if a < min_support or df_s[s] < min_count or df_t[t] < min_count:
            continue
        dice = (2.0 * a) / (df_s[s] + df_t[t])
        if dice >= min_score:
            scored.append((s, t, dice, a))

    if one_best:
        best: dict[str, tuple[str, str, float, int]] = {}
        for row in scored:
            s, _t, dice, _a = row
            cur = best.get(s)
            if cur is None or dice > cur[2]:
                best[s] = row
        scored = list(best.values())

    # Deterministic order: score desc, then support desc, then lexical.
    scored.sort(key=lambda r: (-r[2], -r[3], r[0], r[1]))

    candidates: list[TermCandidate] = []
    for s, t, dice, a in scored:
        evidence = [
            Evidence(source=tu.source.name, uri=tu.source.uri, ref=tu.source.ref)
            for tu in support_tus[(s, t)]
        ]
        candidates.append(
            TermCandidate(
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                src=s,
                tgt=t,
                score=round(dice, 4),
                support=a,
                evidence=evidence,
            )
        )
    return candidates


def verify(
    candidate: TermCandidate,
    tus: Sequence[TranslationUnit],
    *,
    max_evidence: int = 3,
) -> tuple[bool, list[Evidence]]:
    """Re-collect official segments where both terms co-occur (hard rule #4).

    Returns ``(supported, evidence)``. ``supported`` is False when no official
    source backs the pair — candidates are never asserted without proof.
    """

    s = candidate.src.casefold()
    t = candidate.tgt.casefold()
    oriented = _orient(tus, candidate.src_lang, candidate.tgt_lang)
    evidence: list[Evidence] = []
    for src_text, tgt_text, tu in oriented:
        if s in _ngrams(src_text, str(candidate.src_lang)) and t in _ngrams(
            tgt_text, str(candidate.tgt_lang)
        ):
            evidence.append(
                Evidence(source=tu.source.name, uri=tu.source.uri, ref=tu.source.ref)
            )
            if len(evidence) >= max_evidence:
                break
    return (len(evidence) > 0, evidence)
