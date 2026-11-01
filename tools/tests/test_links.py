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
