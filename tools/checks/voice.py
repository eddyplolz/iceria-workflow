"""Encyclopedic, in-world voice: MoS 1.1, 1.2, 1.5 (words to watch) and 7.2.

Words that can only come from outside the world (Discord, a chatbot's name, "this wiki") are
errors, and they are read inside comments and nowiki too, where the other checks look away. Words
with a fair in-world use ("the steward of the harbor", "a claim to the throne") and real-world
names are warnings, so the writer decides. Ref bodies are not read.
"""

import re

from checks import ERROR, HIDDEN, WARNING, Finding, prose_lines, strip_refs

# MoS 1.5, by its own groups: praise, inflated verbs, stock phrases, editorializing, weasel
# words, loaded words for "said", doubt.
WATCH = """legendary|renowned|iconic|world-class|breathtaking|vibrant|picturesque|prestigious|
thriving|beloved|rich history|rich heritage|boasts|boast|features|serves as|stands as|plays a key role|
plays a vital role|plays a pivotal role|lies at the heart of|nestled|steeped in history|
a land of contrasts|a melting pot|the crossroads of|a testament to|a tapestry of|the jewel of|
notably|interestingly|importantly|remarkably|of course|clearly|undoubtedly|it should be noted that|
it is worth mentioning|some say|many believe|it is widely regarded as|critics argue|is considered|
claimed|admitted|insisted|revealed|conceded|so-called|supposed|alleged"""
# Words with an in-world sense that mostly speak from outside it: about the game, the wiki or the
# drafting (MoS 1.1). "Member" is left out: councils and parliaments have members in-world too.
FOURTH_WALL = """player|players|steward|stewards|proposal|proposals|
not yet written|will be added|to be written|to be added|artist's interpretation|in-character|
claim|claims|official map|the member who|who writes|who wrote"""
# Words no sentence inside the world can hold (MoS 1.1): always an error, in any case.
OUT_OF_WORLD = """Discord|forum|roleplay|role-play|role play|out of character|
this wiki|the wiki|Wikipedia|Britannica|nation owner|fictional|real world|real-world|
artificial intelligence|language model|ChatGPT|OpenAI|Anthropic|Copilot|as Claude|as an AI|
written with|written for|joined Iceria|joined the wiki|this article|fan fiction|fanfiction|
geofiction|conworld|Micras|editor's note|lorem ipsum"""
# The same, but only in capitals: "ai" and "rp" are inside ordinary words and names.
OUT_OF_WORLD_CAPS = "AI|RP|OOC|LLM|GPT|WIP|TODO|TBD"
# Second person and time-relative phrases, and the wiki's founder, by handle.
ADDRESS = """you|your|yours|we|our|ours|at the time of writing|as of this writing|nowadays|
currently|recently|Eddy"""
# Real-world countries and continents (MoS 7.2: Iceria's world has its own), then the islands,
# microstates and cities a writer compares a place to, languages, wars and brand names.
REAL = """France|England|Britain|United Kingdom|Germany|Spain|Portugal|Italy|Russia|China|Japan|
Korea|India|Mexico|Brazil|Canada|Australia|United States|America|Europe|Africa|Asia|Netherlands|
Belgium|Poland|Greece|Turkey|Egypt|Persia|Iran|Iraq|Arabia|Scotland|Ireland|Wales|Sweden|Norway|
Denmark|Finland|Austria|Switzerland|Hungary|Argentina|Chile|Peru|Colombia|Indonesia|Vietnam|
Thailand|Philippines|Earth|Malta|Monaco|Singapore|Luxembourg|Liechtenstein|Andorra|San Marino|
Vatican|Iceland|Cyprus|Gibraltar|Hong Kong|Macau|Venice|Rome|Paris|London|Berlin|Madrid|
Athens|Vienna|Prague|Moscow|Istanbul|Cairo|Tokyo|Beijing|Shanghai|New York|Los Angeles|
Chicago|Sydney|Dubai|Hawaii|Bermuda|Bahamas|Cuba|Jamaica|Sicily|Sardinia|Corsica|Crete|
Greenland|Antarctica|Pakistan|Bangladesh|Israel|Saudi Arabia|Syria|Lebanon|Jordan|Nigeria|
Kenya|Ethiopia|Morocco|South Africa|Ukraine|Romania|Bulgaria|Serbia|Croatia|Czechia|Slovakia|
Slovenia|Estonia|Latvia|Lithuania|Belarus|Venezuela|Ecuador|Bolivia|Uruguay|Paraguay|
Cambodia|Malaysia|Taiwan|Mongolia|Nepal|Afghanistan|New Zealand|North America|South America|
English|Spanish|French|German|Italian|Russian|Chinese|Japanese|Arabic|Latin|Greek|
World War|AK-47|Glock|Kalashnikov|iPhone|Google|Facebook|Twitter|YouTube|Coca-Cola"""
UNFINISHED = r"\[citation needed\]"
QUOTED = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”")


def _pattern(words: str, flags=re.I) -> re.Pattern:
    parts = sorted(
        {p.strip() for p in re.split(r"[|\n]", words) if p.strip()}, key=len, reverse=True
    )
    return re.compile(r"\b(" + "|".join(re.escape(p) for p in parts) + r")\b", flags)


OUT_OF_WORLD_RX = _pattern(OUT_OF_WORLD)
OUT_OF_WORLD_CAPS_RX = _pattern(OUT_OF_WORLD_CAPS, 0)
UNFINISHED_RX = re.compile(UNFINISHED, re.I)
REAL_RX = _pattern(REAL, 0)
ADDRESS_RX = _pattern(ADDRESS)
GROUPS = [
    (_pattern(WATCH), "words to watch", "say it plainly or attribute it (MoS 1.5)"),
    (_pattern(FOURTH_WALL), "out-of-world voice", "write from inside the world (MoS 1.1)"),
]


def _exempt(ctx: dict) -> set[str]:
    """Real-world names that are also Iceria names: places, families, nations and capitals."""
    nations = ctx.get("nations", {})
    names = {
        *ctx.get("names", []),
        *ctx.get("families", []),
        *nations,
        *filter(None, nations.values()),
    }
    return {n.lower().removeprefix("the ") for n in names}


def _out_of_world(text: str) -> list[str]:
    hits = [m.group(0) for rx in (OUT_OF_WORLD_RX, OUT_OF_WORLD_CAPS_RX) for m in rx.finditer(text)]
    hits += [m.group(0) for m in UNFINISHED_RX.finditer(text)]
    return list(dict.fromkeys(hits))


def run(text: str, ctx: dict) -> list[Finding]:
    found = []
    exempt = _exempt(ctx)
    for n, line in prose_lines(text):
        prose = strip_refs(line)
        if hits := _out_of_world(prose):
            found.append(
                Finding(
                    n,
                    "voice",
                    ERROR,
                    f"out-of-world voice: {', '.join(hits)}; write from inside the world (MoS 1.1)",
                )
            )
        for rx, label, advice in GROUPS:
            hits = list(dict.fromkeys(m.group(0) for m in rx.finditer(prose)))
            if hits:
                found.append(Finding(n, "voice", WARNING, f"{label}: {', '.join(hits)}; {advice}"))
        # "you" inside a quotation is a character speaking.
        hits = list(dict.fromkeys(m.group(0) for m in ADDRESS_RX.finditer(QUOTED.sub("", prose))))
        if hits:
            found.append(
                Finding(
                    n,
                    "voice",
                    WARNING,
                    f"second person or dated: {', '.join(hits)}; write in the third person "
                    "and give a year (MoS 1.2)",
                )
            )
        hits = [
            w
            for w in dict.fromkeys(m.group(0) for m in REAL_RX.finditer(prose))
            if w.lower() not in exempt
        ]
        if hits:
            found.append(
                Finding(
                    n,
                    "voice",
                    WARNING,
                    f"real-world name: {', '.join(hits)}; Iceria has its own places (MoS 7.2)",
                )
            )
    # Comments, nowiki and pre are blanked for the other checks, so out-of-world text hides there.
    if ctx.get("form"):
        # A proposal may speak about Iceria as a project (Manual of Style intro), so its typed
        # values are not read for out-of-world voice.
        return sorted(found, key=lambda f: f.line)
    for m in HIDDEN.finditer(text):
        if not m.group(0).startswith("__") and (hits := _out_of_world(m.group(0))):
            found.append(
                Finding(
                    text.count("\n", 0, m.start()) + 1,
                    "voice",
                    ERROR,
                    f"out-of-world voice inside a comment or nowiki: {', '.join(hits)}; "
                    "delete it (MoS 1.1)",
                )
            )
    return sorted(found, key=lambda f: f.line)
