"""Encyclopedic, in-world voice: MoS 1.1, 1.5 (words to watch) and 7.2.

Every finding is a warning: each word has fair uses ("the steward of the harbor", "a claim to the
throne"), so the writer decides. Ref bodies are not read.
"""

import re

from checks import WARNING, Finding, prose_lines, strip_refs

# MoS 1.5, by its own groups: praise, inflated verbs, stock phrases, editorializing, weasel
# words, loaded words for "said", doubt.
WATCH = """legendary|renowned|iconic|world-class|breathtaking|vibrant|picturesque|prestigious|
thriving|beloved|rich history|rich heritage|boasts|boast|features|serves as|stands as|plays a key role|
plays a vital role|plays a pivotal role|lies at the heart of|nestled|steeped in history|
a land of contrasts|a melting pot|the crossroads of|a testament to|a tapestry of|the jewel of|
notably|interestingly|importantly|remarkably|of course|clearly|undoubtedly|it should be noted that|
it is worth mentioning|some say|many believe|it is widely regarded as|critics argue|is considered|
claimed|admitted|insisted|revealed|conceded|so-called|supposed|alleged"""
# Words that speak from outside the world: about the game, the wiki or the drafting (MoS 1.1).
# "Member" is left out: councils and parliaments have members in-world too.
FOURTH_WALL = """player|players|steward|stewards|proposal|proposals|roleplay|
not yet written|will be added|to be written|to be added|artist's interpretation|in-character|
out of character|OOC|the wiki|this article"""
# Real-world countries and continents (MoS 7.2: Iceria's world has its own).
REAL = """France|England|Britain|United Kingdom|Germany|Spain|Portugal|Italy|Russia|China|Japan|
Korea|India|Mexico|Brazil|Canada|Australia|United States|America|Europe|Africa|Asia|Netherlands|
Belgium|Poland|Greece|Turkey|Egypt|Persia|Iran|Iraq|Arabia|Scotland|Ireland|Wales|Sweden|Norway|
Denmark|Finland|Austria|Switzerland|Hungary|Argentina|Chile|Peru|Colombia|Indonesia|Vietnam|
Thailand|Philippines|Earth"""


def _pattern(words: str, flags=re.I) -> re.Pattern:
    parts = sorted(
        {p.strip() for p in re.split(r"[|\n]", words) if p.strip()}, key=len, reverse=True
    )
    return re.compile(r"\b(" + "|".join(re.escape(p) for p in parts) + r")\b", flags)


GROUPS = [
    (_pattern(WATCH), "words to watch", "say it plainly or attribute it (MoS 1.5)"),
    (_pattern(FOURTH_WALL), "out-of-world voice", "write from inside the world (MoS 1.1)"),
    (_pattern(REAL, 0), "real-world name", "Iceria has its own places (MoS 7.2)"),
]


def run(text: str, ctx: dict) -> list[Finding]:
    found = []
    for n, line in prose_lines(text):
        prose = strip_refs(line)
        for rx, label, advice in GROUPS:
            hits = list(dict.fromkeys(m.group(0) for m in rx.finditer(prose)))
            if hits:
                found.append(Finding(n, "voice", WARNING, f"{label}: {', '.join(hits)}; {advice}"))
    return found
