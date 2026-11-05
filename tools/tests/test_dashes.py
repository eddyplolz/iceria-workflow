from checks import dashes

BAD = """'''Vell''' is a state—the oldest in the west.
The war -- a long one -- ended.
The north – the poorer half – rebelled.
It is a “free” city.
Trade runs north–south.
The port - the only one - is small.
"""


def test_each_dash_and_quote_fault_is_an_error_on_its_line():
    found = dashes.run(BAD, {})
    assert [(f.line, f.level, f.message.split(":")[0]) for f in found] == [
        (1, "error", "em dash"),
        (2, "error", "double hyphen"),
        (3, "error", "spaced en dash in prose"),
        (4, "error", "curly quote"),
        (5, "error", "en dash outside a range"),
        (6, "error", "spaced hyphen"),
    ]


def test_ranges_compound_modifiers_and_infobox_lines_pass():
    clean = """{{Infobox country
| founded = 1802 — 1840
}}
'''Vell''' ruled from 1802–1840 and from 14 March – 2 April 1898.
It is a well-known port with a "free" market.
"""
    assert dashes.run(clean, {}) == []


def test_month_decade_and_open_ranges_pass():
    # Audit bug 2: these MoS 5.2 ranges were errors, an en dash outside a range.
    clean = (
        "It met each March–April and grew through the 1890s–1900s.\n"
        "The league ran 1990–present, and its seat from 14 March 1990 – present.\n"
    )
    assert dashes.run(clean, {}) == []


def test_a_word_beside_a_month_is_still_an_en_dash_outside_a_range():
    assert [f.line for f in dashes.run("The March–north road is long.\n", {})] == [1]


def test_page_names_and_html_tags_are_not_prose():
    # A linked page's title is that page's own name, and a tag's attributes are not read text.
    clean = (
        "See [[Tleyew-Pas: Living Stories - The Three Lights|the Three Lights]] and "
        "[[Tleyew-Pas: 02 Land - Climate]].\n"
        '<span style="margin:0 -- 0">The port</span> grew.\n'
    )
    assert dashes.run(clean, {}) == []
    assert [f.line for f in dashes.run("[[Vell|the port - the only one]] is small.\n", {})] == [1]


def test_a_dash_beside_an_unpiped_link_is_still_read():
    # The link's name is blanked, but the link still stands as a word beside the dash.
    for bad in ("Vell was founded by [[Aldric]] – a king.\n", "[[Vell]]–[[Brannvik]] road.\n"):
        assert [f.line for f in dashes.run(bad, {})] == [1], bad
