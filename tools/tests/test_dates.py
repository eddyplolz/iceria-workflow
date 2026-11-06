from checks import dates

BAD = """'''Vell''' was founded on March 14, 1802.
The 14th March treaty followed.
It ruled from 1406-1632.
Its golden age was the 1890's.
It signed on 14/03/1898.
In March, 1898 it fell.
It joined the league in 2003.
It is currently a republic.
"""


def _summary(found):
    return [(f.line, f.level, f.message.split(":")[0]) for f in found]


def test_each_date_fault_is_named_on_its_line():
    assert _summary(dates.run(BAD, {})) == [
        (1, "error", "month-first date"),
        (2, "error", "ordinal date"),
        (3, "error", "hyphen in a year range"),
        (4, "error", "apostrophe in a decade"),
        (5, "error", "numeric date"),
        (6, "error", "comma between month and year"),
        (7, "error", "date after the present"),
        (8, "warning", "relative time word"),
    ]


def test_a_relative_time_word_inside_a_quotation_is_the_speaker_s():
    # The speaker's "today" was their day, so the page cannot give it a year (MoS 1.3 is for the
    # page's own voice).
    text = (
        'She was described as "the most eligible of any in the royal courts today".\n'
        "She was described as “the finest pianist now living”.\n"
        'The court, which "met daily", is today a museum.\n'
    )
    assert _summary(dates.run(text, {})) == [(3, "warning", "relative time word")]


def test_the_present_comes_from_the_in_world_date_when_there_is_one():
    text = "It joined the league in 2003.\n"
    assert dates.run(text, {"in_world_date": "1 May 2004"}) == []
    found = dates.run("It joined in 2005.\n", {"in_world_date": "1 May 2004"})
    assert "2004" in found[0].message


def test_correct_dates_pass():
    clean = (
        "'''Vell''' was founded on 14 March 1802 and ruled from 1406–1632.\n"
        "Its golden age was the 1890s. As of 2000 it had 40,000 people and 2,100 ships.\n"
    )
    assert dates.run(clean, {}) == []


def test_a_scheduled_future_date_is_not_an_event_after_the_present():
    text = "The next election is due by 2002. The lease expires in 2010. It fell in 2003.\n"
    assert [f.message.split(":")[1].split(";")[0].strip() for f in dates.run(text, {})] == ["2003"]


def test_a_count_after_a_preposition_is_not_read_as_a_year():
    # Audit bug 1: "an army of 3000 men" was an error, a date after the present.
    text = "It raised an army of 3000 men and sent 2500 ships to 4000 islands.\n"
    assert _summary(dates.run(text, {})) == [(1, "warning", "number read as a count, not a year")]


def test_a_year_before_a_function_word_or_a_name_is_still_a_date():
    text = "By 2005 the city had grown. In 2006 King Arvo died. It fell in 2007, then rose.\n"
    found = dates.run(text, {})
    assert _summary(found) == [(1, "error", "date after the present")]
    assert "2005, 2006, 2007" in found[0].message


def test_a_count_after_a_quantity_noun_and_of_is_not_a_year():
    # Review: "a population of 4500." and "a garrison of 2500 in the fort" were errors.
    text = "The city has a population of 4500.\nA garrison of 2500 in the fort held.\n"
    assert _summary(dates.run(text, {})) == [
        (1, "warning", "number read as a count, not a year"),
        (2, "warning", "number read as a count, not a year"),
    ]


def test_an_event_of_a_year_is_still_a_date():
    found = dates.run("It was the election of 2005.\n", {})
    assert _summary(found) == [(1, "error", "date after the present")]
