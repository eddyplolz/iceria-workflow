from checks import names

CTX = {
    "names": ["Serenian Ocean", "the Aeterna", "Lake Gemina", "Septentria", "the Dorsal Range"],
    "families": ["Hesperic"],
}
BAD = """'''Vell''' lies on the Serenean Ocean, north of Septentira.
Its rivers drain into the Vell Sea.
Its people are Hesperik.
"""


def test_near_misses_and_unknown_fixed_features_are_warnings():
    found = names.run(BAD, CTX)
    assert {f.level for f in found} == {"warning"}
    assert [(f.line, f.message) for f in found] == [
        (1, "unofficial feature name: 'Serenean Ocean' is not on the world map (MoS 7.3)"),
        (1, "near an official name: 'Serenean' looks like 'Serenian' (MoS 7.3)"),
        (1, "near an official name: 'Septentira' looks like 'Septentria' (MoS 7.3)"),
        (2, "unofficial feature name: 'Vell Sea' is not on the world map (MoS 7.3)"),
        (3, "near an official name: 'Hesperik' looks like 'Hesperic' (MoS 7.3)"),
    ]


def test_official_names_pass():
    clean = "'''Vell''' lies on the Serenian Ocean by the Dorsal Range and Lake Gemina.\n"
    assert names.run(clean, CTX) == []


def test_without_canon_files_the_check_is_silent():
    assert names.run(BAD, {}) == []
