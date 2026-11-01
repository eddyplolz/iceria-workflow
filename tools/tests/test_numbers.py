from checks import numbers


def _summary(found):
    return [(f.line, f.level, f.message.split(":")[0]) for f in found]


def test_unit_glued_to_its_number_is_an_error():
    text = "The bay is 120km wide and 1,200km² in area.\nIt is 18°C in summer.\n"
    assert _summary(numbers.run(text, {})) == [
        (1, "error", "no space between number and unit"),
        (2, "error", "no space between number and unit"),
    ]


def test_spaced_units_and_ordinary_words_pass():
    text = "The bay is 120 km wide, 1,200 km² in area and 18 °C in summer, in the 1990s.\n"
    assert numbers.run(text, {}) == []


def test_numeral_opening_a_sentence_is_a_warning():
    text = "1534 was the year of the Compact. The town fell. 12 ships sailed.\n"
    assert _summary(numbers.run(text, {})) == [
        (1, "warning", "numeral opens a sentence"),
    ]


def test_abbreviation_before_a_year_is_not_a_sentence_start():
    text = "The Republic was founded c. 480 BC, and St. 12 is a church. It had 3.5 km of walls.\n"
    assert numbers.run(text, {}) == []


def test_percent_written_as_a_word_is_a_warning():
    text = "About 25 percent of trade, and 3 per cent of fish.\n"
    assert _summary(numbers.run(text, {})) == [(1, "warning", "percent as a word")]


def test_infobox_refs_and_list_items_are_not_read():
    text = "{{Infobox Settlement\n| area = 12km\n}}\n* 1534 the Compact\nA city.<ref>12km</ref>\n"
    assert numbers.run(text, {}) == []


def test_the_finding_quotes_the_whole_number():
    found = numbers.run("The bay is 120km wide and 1,200km² in area.\n", {})
    assert "120km, 1,200km²" in found[0].message
