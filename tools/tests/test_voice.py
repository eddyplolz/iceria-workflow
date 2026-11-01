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
