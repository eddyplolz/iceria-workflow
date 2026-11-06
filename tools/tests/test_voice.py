from checks import voice

BAD = """'''Vell''' is a vibrant port that boasts a rich history.
The steward of Vell has not yet written its laws.
Notably, it is considered a melting pot.
Its people came from France.
"""


def test_each_voice_problem_is_a_warning_naming_the_words():
    found = voice.run(BAD, {})
    assert {f.level for f in found} == {"warning"}
    assert [(f.line, f.message.split(":")[0]) for f in found] == [
        (1, "words to watch"),
        (2, "out-of-world voice"),
        (3, "words to watch"),
        (4, "real-world name"),
    ]
    assert "vibrant" in found[0].message and "boasts" in found[0].message
    assert "rich history" in found[0].message
    assert "steward" in found[1].message and "not yet written" in found[1].message
    assert "France" in found[3].message


def test_plain_in_world_prose_passes():
    clean = "'''Vell''' is a port on the Saran coast. Its trade grew after 1802.\n"
    assert voice.run(clean, {}) == []


def test_members_of_an_in_world_body_are_not_out_of_world():
    assert voice.run("The Council elects one of its members High Warden.\n", {}) == []


def _levels(text, ctx=None):
    return {(f.line, f.level) for f in voice.run(text, ctx or {})}


def test_a_forum_in_the_world_is_not_the_website():
    # A town's forum and a forum of nations are in-world; the website is "on the forum".
    for ok in (
        "The tablets were set up in the forum of Leria.\n",
        "The Concord is a forum where nations meet.\n",
    ):
        assert voice.run(ok, {}) == [], ok
    for meta in ("It was posted on a forum.", "See the forum thread.", "A forum post said so."):
        assert _levels(meta) == {(1, "error")}, meta


def test_unambiguous_out_of_world_words_are_errors():
    for word in (
        "Details were agreed on Discord.",
        "As announced on the forum.",
        "Port Alba is a popular RP location.",
        "This wiki has no page on its mayor.",
        "The nation owner added a harbor.",
        "Port Alba is a fictional city.",
        "It is like the real world.",
        "This text was written with an AI assistant.",
        "Made by artificial intelligence.",
        "ChatGPT suggested the name.",
        "Port Alba joined Iceria in October.",
        "This is fan fiction.",
        "A geofiction city on a conworld.",
        "It trades with the Micras nations.",
        "WIP section, more to come.",
        "The quay is old.[citation needed]",
        "Editor's note: a placeholder.",
        "As Claude, I cannot confirm it.",
        "(Written for the nation Alexandria by its owner.)",
    ):
        assert _levels(word) == {(1, "error")}, word


def test_words_with_an_in_world_sense_stay_warnings():
    for word in (
        "The member who writes Alexandria is away.",
        "The city sits inside the land the claim covers on the official map.",
        "The steward of the harbor keeps the keys.",
        "If you visit, you will see the quay.",
        "At the time of writing the quay is closed.",
    ):
        assert _levels(word) == {(1, "warning")}, word


def test_a_claim_to_or_that_is_an_in_world_claim_not_the_claim_map():
    for line in (
        "Vell lays claim to the coast.",
        "The jarls press their claims to the islands.",
        "Its claim that the river was its own held for a century.",
    ):
        assert voice.run(line + "\n", {}) == [], line
    assert _levels("The claim covers the north shore.") == {(1, "warning")}


def test_players_in_a_market_are_not_the_game_players():
    # "Leading global players" are firms; the game's players are still read.
    for ok in (
        "Its media firms are leading global players.\n",
        "The two banks are major players in the bond market.\n",
    ):
        assert voice.run(ok, {}) == [], ok
    for meta in ("The players of Vell agreed.", "Each player claims land."):
        assert _levels(meta) == {(1, "warning")}, meta


def test_our_lady_is_a_name_not_the_writer_speaking():
    for ok in (
        "The city holds the Basilica of Our Lady of the Seven Sorrows.\n",
        "Our Lady of the Harbor is its patron.\n",
        "The Church of Our Savior stands on the hill.\n",
    ):
        assert voice.run(ok, {}) == [], ok
    for meta in ("Our shipwrights built it.", "It is our port.", "Join Our Government today."):
        assert _levels(meta) == {(1, "warning")}, meta


def test_the_letters_ai_in_a_word_are_not_the_chatbot():
    assert voice.run("The Aileron road runs past the Said quarter.\n", {}) == []


def test_the_full_real_places_list_warns():
    for word in (
        "The harbor is like Malta's.",
        "The city is often compared with Monaco.",
        "Residents speak English, Spanish and French.",
        "The harbor was rebuilt after World War II.",
        "Its guard carries AK-47 rifles.",
        "It lies near Singapore.",
    ):
        assert _levels(word) == {(1, "warning")}, word


def test_a_real_name_that_is_an_iceria_name_is_exempt():
    text = "The road leads to Mantua and on to Malta.\n"
    found = voice.run(text, {"nations": {"Mantua": "Mantua City"}})
    assert [f.message for f in found if "Mantua" in f.message] == []
    assert any("Malta" in f.message for f in found)


def test_out_of_world_words_hide_nowhere():
    # A comment is an error of its own (checks/comments.py), so voice does not report it twice.
    assert _levels("Text.\n<!-- agreed on Discord -->\n") == set()
    assert (1, "error") in _levels("<nowiki>This article is a draft.</nowiki>\n")
    assert (1, "error") in _levels("<nowiki>agreed on Discord</nowiki>\n")
    assert (3, "error") in _levels("a\nb\n<pre>\nforum post\n</pre>\n")
