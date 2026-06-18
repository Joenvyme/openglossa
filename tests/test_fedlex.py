from __future__ import annotations

from openglossa.sources.fedlex import (
    bindings_to_manifestations,
    build_query,
    manifestations_to_title_units,
)

# Minimal SPARQL JSON bindings mimicking the live Fedlex response for an act.
_BINDINGS = [
    {
        "act": {"value": "https://fedlex.data.admin.ch/eli/cc/27/317_321_377"},
        "lang": {"value": "http://publications.europa.eu/resource/authority/language/DEU"},
        "title": {"value": "Bundesgesetz betreffend die Ergänzung des ZGB (OR)"},
    },
    {
        "act": {"value": "https://fedlex.data.admin.ch/eli/cc/27/317_321_377"},
        "lang": {"value": "http://publications.europa.eu/resource/authority/language/FRA"},
        "title": {"value": "Loi fédérale complétant le code civil suisse (CO)"},
    },
    {
        "act": {"value": "https://fedlex.data.admin.ch/eli/cc/27/317_321_377"},
        "lang": {"value": "http://publications.europa.eu/resource/authority/language/ITA"},
        "title": {"value": "Legge federale di complemento del Codice civile svizzero (CO)"},
    },
    {
        "act": {"value": "https://fedlex.data.admin.ch/eli/cc/27/317_321_377"},
        "lang": {"value": "http://publications.europa.eu/resource/authority/language/ENG"},
        "title": {"value": "Federal Act on the Amendment of the Swiss Civil Code (CO)"},
    },
]


def test_build_query_contains_filters():
    q = build_query("220")
    assert '"220"' in q
    assert "/eli/cc/" in q
    assert "isRealizedBy" in q


def test_bindings_to_manifestations_core_langs():
    manifs = bindings_to_manifestations("220", _BINDINGS)
    langs = {m.lang for m in manifs}
    assert langs == {"de", "fr", "it"}  # EN dropped by default core filter
    de = next(m for m in manifs if m.lang == "de")
    sref = de.to_source_ref()
    assert sref.name == "Fedlex"
    assert sref.ref == "SR 220"
    assert str(sref.uri).endswith("317_321_377")


def test_manifestations_to_title_units():
    manifs = bindings_to_manifestations("220", _BINDINGS)
    tus = manifestations_to_title_units(manifs)
    assert len(tus) == 3  # de-fr, de-it, fr-it
    for tu in tus:
        assert tu.source.name == "Fedlex"
        assert tu.source.ref == "SR 220"
        assert tu.domain == ["statute-title"]
        assert tu.alignment.method == "eli-structural"
