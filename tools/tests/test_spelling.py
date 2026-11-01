from checks import spelling


def test_mixed_spelling_warns_once_per_pair_at_the_minority_line():
    text = (
        "The flag's colour is red and its harbour deep.\n"
        "The colours of the harbour guild.\n"
        "Its color is old.\n"
        "The harbor fort and the defence wall.\n"
    )
    found = spelling.run(text, {})
    assert [(f.line, f.level, f.message) for f in found] == [
        (
            3,
            "warning",
            "mixed spelling: 'color' here, 'colour' elsewhere; pick one for the page (MoS 6.1)",
        ),
        (
            4,
            "warning",
            "mixed spelling: 'harbor' here, 'harbour' elsewhere; pick one for the page (MoS 6.1)",
        ),
    ]


def test_one_spelling_throughout_passes_either_way():
    assert spelling.run("Its colour and harbour, the centre of defence.\n", {}) == []
    assert spelling.run("Its color and harbor, the center of defense.\n", {}) == []
