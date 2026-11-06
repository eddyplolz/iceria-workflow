from checks import links


def _summary(found):
    return [(f.line, f.level, f.message.split(":")[0]) for f in found]


def test_self_link_is_an_error_even_in_bold_and_piped():
    text = "'''[[Port-Réal]]''' is a city.\nSee [[port-Réal|the port]] and [[Geneva]].\n"
    assert _summary(links.run(text, {"title": "Port-Réal"})) == [
        (1, "error", "link to the article itself"),
        (2, "error", "link to the article itself"),
    ]


def test_no_title_means_no_self_link_check():
    assert links.run("'''[[Port-Réal]]''' is a city.\n", {}) == []


def test_outside_link_in_the_body_is_an_error_but_not_in_a_ref():
    text = (
        "Visit https://example.com today.\n* [https://x.y Site]\nA fact.<ref>[[Alexandria]]</ref>\n"
    )
    assert _summary(links.run(text, {})) == [
        (1, "error", "link outside the wiki"),
        (2, "error", "link outside the wiki"),
    ]


def test_image_size_in_pixels_and_caption_opener_are_warnings():
    text = "[[File:Port.png|300px|thumb|A picture of the port]]\n[[File:Map.png|thumb|upright=1.4|The regions]]\n"
    assert _summary(links.run(text, {})) == [
        (1, "warning", "image size in pixels"),
        (1, "warning", "caption opens with"),
    ]


def test_a_small_icon_beside_a_line_may_carry_a_pixel_size():
    # MoS 15.4 places pictures as thumbnails; a 25px flag beside a list item is an icon, not one.
    for ok in (
        "* [[File:Flag.png|25px]] Knight of the Order of Vell\n",
        "Vell [[File:Flag.png|x20px]] signed it.\n",
    ):
        assert _summary(links.run(ok, {})) == [], ok
    # A placed picture, or a big one, still takes upright=.
    for line in (
        "* [[File:Flag.png|25px|thumb|The flag]]\n",
        "[[File:Seal.png|40px|right]]\n",
        "[[File:Seal.png|40px|centre]]\n",
        "* [[File:Port.png|80px]] The port\n",
        # A template field is not a table cell, though both lines open with "|".
        "| image = [[File:Port.png|400px]]\n",
        "| image-size = [[File:Port.png|400px]]\n",
    ):
        assert _summary(links.run(line, {})) == [(1, "warning", "image size in pixels")], line


def test_an_image_in_a_table_cell_may_carry_a_pixel_size():
    # MoS 15.4 is about pictures placed in the text; a flag icon in a table cell is sized to its cell.
    text = (
        '{| class="wikitable"\n'
        "| [[File:Flag.png|20px]] Seltana\n"
        "|-\n"
        "! [[File:Seal.png|30px]] || [[File:Arms.png|30px]]\n"
        "|-\n"
        # A cell with attributes (The World of Iceria:Archive/Yuriev): "style=" is not a field.
        '| align=center style="width:50%;" | [[File:Emblem.png|100px|frameless]]\n'
        "|}\n"
        "Text || more [[File:Port.png|300px]]\n"
        "[[File:Port.png|300px|center]]\n"
        "| logo = [[File:Seal.png|200px]]\n"
    )
    # "||" splits cells only on a row line, so line 8 is text and its picture is still read; a
    # template field on line 10 is not a cell.
    assert _summary(links.run(text, {})) == [
        (8, "warning", "image size in pixels"),
        (9, "warning", "image size in pixels"),
        (10, "warning", "image size in pixels"),
    ]


def test_category_faults():
    text = (
        "A city.\n[[Category:Cities and Towns]]\n[[Category:Countries]]\n"
        "[[Category:Meta Iceria]]\n[[Category:Alexandria]]\n[[Category:Rise of the Vell League]]\n"
    )
    assert _summary(links.run(text, {"title": "Port-Réal"})) == [
        (2, "warning", "category may be in title case"),
        (3, "warning", "Countries is filled by the nation infobox"),
        (4, "error", "article in Meta Iceria"),
    ]


def test_project_pages_may_sit_in_meta_iceria():
    assert links.run("[[Category:Meta Iceria]]\n", {"title": "Proposal:Vell"}) == []


def _kinds(text, ctx=None):
    return [(f.level, f.message.split(":")[0]) for f in links.run(text, ctx or {})]


def test_an_artists_interpretation_caption_is_a_warning():
    text = "[[File:Port Alba.png|thumb|upright|Artist's interpretation of Port Alba]]\n"
    assert ("warning", "caption opens with") in _kinds(text)


def test_a_piped_link_to_the_same_name_and_a_linked_year_are_warnings():
    assert ("warning", "piped link to the same name") in _kinds("Near [[Alexandria|Alexandria]].\n")
    assert ("warning", "linked year") in _kinds("It was dredged in [[1700]].\n")
    assert _kinds("Near [[Alexandria|the coast]] in 1700.\n") == []


def test_the_first_mention_of_a_nation_is_linked():
    ctx = {"nations": {"Alexandria": "Port Alba"}}
    assert ("warning", "nation not linked") in _kinds("A port city in Alexandria.\n", ctx)
    assert _kinds("A port city in [[Alexandria]]. Alexandria trades.\n", ctx) == []
    infobox_only = "| subdivision_name = [[Alexandria]]\nA port city in Alexandria.\n"
    assert ("warning", "nation not linked") in _kinds(infobox_only, ctx)
    later = "A port city in Alexandria.\nIt trades with [[Alexandria]].\n"
    assert _kinds(later, ctx) == []


def test_a_category_that_starts_lowercase_is_a_warning():
    found = links.run("[[Category:cities of Vell]]\n[[Category:Ports]]\n", {})
    assert [(f.line, f.level, f.message.split(":")[0]) for f in found] == [
        (1, "warning", "category starts lowercase")
    ]


def test_a_lowercase_category_keyword_is_a_warning():
    found = links.run("[[category:Alexandria]]\n[[Category:Ports]]\n", {})
    assert [(f.line, f.level, f.message.split(":")[0]) for f in found] == [
        (1, "warning", "category keyword starts lowercase")
    ]


def test_a_banner_above_the_lead_is_not_the_lead():
    ctx = {"nations": {"Alexandria": "Port Alba"}}
    banner = '<div style="text-align:center;">[[Vell|Welcome]] · [[Vell: Ports|Ports]]</div>\n'
    found = _kinds(banner + "\nA port city in Alexandria.\n", ctx)
    assert ("warning", "nation not linked") in found
