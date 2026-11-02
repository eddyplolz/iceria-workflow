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


def _kinds(text):
    return [(f.level, f.message.split(":")[0]) for f in numbers.run(text, {})]


SMALL = ("warning", "small number as a numeral")


def test_numerals_from_zero_to_nine_in_prose_are_spelled_out():
    assert SMALL in _kinds("The harbor has 3 quays and 7 ferries.\n")
    assert SMALL not in _kinds("The harbor has three quays and 13 ferries.\n")


def test_numbers_that_are_not_counts_keep_their_numerals():
    for ok in (
        "It lies 5 km away.\n",
        "It rose 8% in 1700.\n",
        "It was founded on 3 March 1406.\n",
        "On March 3 it opened.\n",
        "The fee was 3 billion écu.\n",
        "Rates of 2.5 and 1,200 apply.\n",
        "Article 3 of the Charter applies.\n",
        'The ship was called "Seven Seas 3".\n',
        "Between 5 and 12 ships sailed.\n",
        "It came 3rd.\n",
    ):
        assert SMALL not in _kinds(ok), ok


def test_a_figure_with_no_reference_in_its_line_is_a_warning():
    uncited = ("warning", "figure without a reference")
    assert uncited in _kinds("About 4,000 sailors work there.\n")
    assert uncited in _kinds("About 3 million people live there.\n")
    assert uncited not in _kinds('About 4,000 sailors work there.<ref name="a" />\n')
    assert uncited not in _kinds("It was founded in 1406.\n")


def test_a_figure_in_an_uncited_sentence_is_a_warning_though_the_line_has_a_ref():
    line = 'It had 120,000 people.<ref name="nation" /> About 4,000 sailors work there.\n'
    found = numbers.run(line, {})
    assert [(f.level, f.message.split(":")[0]) for f in found] == [
        ("warning", "figure without a reference")
    ]
    cited = 'It had 120,000 people.<ref name="nation" /> The ref follows its sentence.\n'
    assert numbers.run(cited, {}) == []
