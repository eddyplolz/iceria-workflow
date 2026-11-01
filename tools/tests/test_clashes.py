from checks import ERROR, WARNING, clashes

CTX = {"nations": {"Alexandria": "Geneva", "Seltana": "Amba Abeba"}}


def found(text, ctx=CTX):
    return [(f.line, f.level) for f in clashes.run(text, ctx)]


def test_a_real_country_name_for_the_nation_is_an_error():
    text = "{{Infobox Country\n| conventional_long_name = Kingdom of [[France]]\n| common_name = Norway\n}}"
    assert found(text) == [(2, ERROR), (3, ERROR)]


def test_another_nations_name_or_capital_is_an_error():
    text = "{{Infobox Country\n| common_name = Seltana\n| capital = [[Geneva|Geneva]]\n}}"
    assert found(text, {**CTX, "title": "Valmora"}) == [(2, ERROR), (3, ERROR)]


def test_redrafting_your_own_nation_page_is_not_a_clash():
    text = "{{Infobox Country\n| common_name = Alexandria\n| capital = Geneva\n}}"
    assert found(text, {**CTX, "title": "Alexandria"}) == []


def test_a_town_sharing_a_capitals_name_is_a_warning():
    text = "{{Infobox Settlement\n| name = Geneva\n}}"
    [f] = clashes.run(text, CTX)
    assert (f.line, f.level) == (2, WARNING)
    assert "Geneva (" in f.message


def test_new_names_and_names_in_prose_pass():
    text = "{{Infobox Country\n| common_name = Valmora\n| capital = Brenn\n}}\nTrade with France."
    assert found(text) == []


def test_without_canon_the_nation_check_is_silent_but_real_names_still_count():
    text = "| common_name = Seltana\n| capital = Geneva\n| common_name = Spain"
    assert found(text, {}) == [(3, ERROR)]


def test_redrafting_your_own_nation_page_under_its_long_title_is_not_a_clash():
    text = "{{Infobox Country\n| common_name = Alexandria\n| capital = Geneva\n}}"
    ctx = {**CTX, "nation_pages": {"Kingdom of Alexandria": "Alexandria"}}
    assert found(text, {**ctx, "title": "Kingdom of Alexandria"}) == []
