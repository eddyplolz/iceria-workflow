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
