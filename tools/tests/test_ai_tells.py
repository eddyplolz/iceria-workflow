from checks import ai_tells

BAD = (
    "'''Vell''' is a state.citeturn0search0\n"
    "It was founded by [Your Name] in 18XX.\n"
    "Its harbor​ is deep.\n"
    "Its history is intricate, showcasing a seamless blend.\n"
    "It is not only a port but also a fortress.\n"
    "In conclusion, Vell matters.\n"
    "See [https://x.y/?utm_source=chatgpt.com the source].\n"
)


def test_artifacts_and_placeholders_are_errors_and_style_tells_warnings():
    found = ai_tells.run(BAD, {})
    assert [(f.line, f.level, f.message.split(":")[0]) for f in found] == [
        (1, "error", "chatbot artifact"),
        (2, "error", "placeholder"),
        (3, "error", "invisible character"),
        (4, "warning", "AI vocabulary"),
        (5, "warning", "AI sentence pattern"),
        (6, "warning", "AI sentence pattern"),
        (7, "error", "chatbot artifact"),
    ]
    assert "intricate, showcasing, seamless" in found[3].message


def test_plain_prose_passes():
    clean = "'''Vell''' is a state founded in 1802. Its harbor is deep and its trade is old.\n"
    assert ai_tells.run(clean, {}) == []


def test_a_wikilink_that_starts_with_your_is_no_placeholder():
    # Audit: [[Your Majesty]] matched the [Your ...] placeholder inside its brackets.
    text = "'''Vell''' is ruled by a queen styled [[Your Majesty]] at court.\n"
    assert ai_tells.run(text, {}) == []


def test_a_closing_formula_without_its_comma_is_still_a_pattern():
    # Review: "In conclusion the port..." slipped past because the pattern demanded a comma.
    found = ai_tells.run("In conclusion the port matters.\nIn summary trade grew.\n", {})
    assert [(f.line, f.message.split(":")[0]) for f in found] == [
        (1, "AI sentence pattern"),
        (2, "AI sentence pattern"),
    ]


def test_overall_with_no_comma_is_an_adjective_not_a_pattern():
    assert ai_tells.run("Overall command passed to the admiral.\n", {}) == []
