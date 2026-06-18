from __future__ import annotations

from openglossa.align.eli_structural import align_segments, shared_eids
from openglossa.sources.akn import parse_segments, ref_from_eid

_AKN_FR = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
 <act><body>
  <article eId="art_1"><num><b>Art. 1</b></num>
   <paragraph eId="art_1/para_1"><num>1</num><content><p> Le contrat est parfait.</p></content></paragraph>
   <paragraph eId="art_1/para_2"><num>2</num><content><p> Elle peut etre tacite.</p></content></paragraph>
  </article>
  <article eId="art_6_a"><num><b>Art. 6a</b></num>
   <paragraph eId="art_6_a/para_1"><num>1</num><content><p> Disposition speciale.</p></content></paragraph>
  </article>
 </body></act>
</akomaNtoso>"""

_AKN_DE = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
 <act><body>
  <article eId="art_1"><num><b>Art. 1</b></num>
   <paragraph eId="art_1/para_1"><num>1</num><content><p> Der Vertrag ist vollkommen.</p></content></paragraph>
   <paragraph eId="art_1/para_2"><num>2</num><content><p> Sie kann stillschweigend sein.</p></content></paragraph>
  </article>
  <article eId="art_6_a"><num><b>Art. 6a</b></num>
   <paragraph eId="art_6_a/para_1"><num>1</num><content><p> Besondere Bestimmung.</p></content></paragraph>
  </article>
 </body></act>
</akomaNtoso>"""


def test_parse_segments():
    segs = parse_segments(_AKN_FR)
    assert segs["art_1/para_1"] == "Le contrat est parfait."
    assert segs["art_1/para_2"] == "Elle peut etre tacite."
    assert segs["art_6_a/para_1"] == "Disposition speciale."
    assert len(segs) == 3


def test_ref_from_eid():
    assert ref_from_eid("220", "art_1/para_1") == "SR 220 Art. 1 al. 1"
    assert ref_from_eid("220", "art_6_a/para_2") == "SR 220 Art. 6a al. 2"
    assert ref_from_eid("220", "art_10") == "SR 220 Art. 10"


def test_shared_eids_intersection():
    fr = parse_segments(_AKN_FR)
    de = parse_segments(_AKN_DE)
    de.pop("art_6_a/para_1")  # missing in DE -> excluded
    common = shared_eids({"fr": fr, "de": de}, ["fr", "de"])
    assert common == ["art_1/para_1", "art_1/para_2"]


def test_align_segments_builds_cited_tus():
    segs = {"de": parse_segments(_AKN_DE), "fr": parse_segments(_AKN_FR)}
    tus = align_segments(
        "220",
        segs,
        langs=["de", "fr"],
        citable_uri_by_lang={
            "de": "https://fedlex.data.admin.ch/eli/cc/27/317_321_377/20260101/de",
            "fr": "https://fedlex.data.admin.ch/eli/cc/27/317_321_377/20260101/fr",
        },
    )
    assert len(tus) == 3  # 3 shared eIds, 1 language pair
    tu = tus[0]
    assert tu.src_lang == "de"
    assert tu.tgt_lang == "fr"
    assert tu.src == "Der Vertrag ist vollkommen."
    assert tu.tgt == "Le contrat est parfait."
    assert tu.source.ref == "SR 220 Art. 1 al. 1"
    assert tu.alignment.method == "eli-structural"
    assert str(tu.source.uri).endswith("/de")


def test_align_limit():
    segs = {"de": parse_segments(_AKN_DE), "fr": parse_segments(_AKN_FR)}
    tus = align_segments("220", segs, langs=["de", "fr"], limit=1)
    assert len(tus) == 1
