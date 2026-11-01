"""Names a nation may not take (World Standards 6.2 and 6.5).

Reads the draft's infobox. A real country's name in a nation's name is an error (6.2), and so is
another nation's name or capital used as this nation's name or capital (6.5); ctx["nations"] holds
{nation: capital} from canon/nations/. A town that shares another nation's capital name is a
warning: it may stand, titled with its nation in brackets. Names in prose are not checked, since a
page may well mention France's real-world namesake or a neighbor's capital.
"""

import re

from checks import ERROR, WARNING, Finding, lines

FIELD = re.compile(r"^\s*\|\s*(conventional_long_name|common_name|capital|name)\s*=\s*(.*?)\s*$")
REAL_COUNTRIES = (
    "Afghanistan|Albania|Algeria|Andorra|Angola|Argentina|Armenia|Australia|Austria|Azerbaijan"
    "|Bahamas|Bahrain|Bangladesh|Barbados|Belarus|Belgium|Belize|Benin|Bhutan|Bolivia|Bosnia"
    "|Botswana|Brazil|Brunei|Bulgaria|Burkina Faso|Burundi|Cambodia|Cameroon|Canada|Cape Verde"
    "|Chad|Chile|China|Colombia|Comoros|Congo|Costa Rica|Croatia|Cuba|Cyprus|Czechia|Denmark"
    "|Djibouti|Dominica|Ecuador|Egypt|El Salvador|Eritrea|Estonia|Eswatini|Ethiopia|Fiji|Finland"
    "|France|Gabon|Gambia|Georgia|Germany|Ghana|Greece|Grenada|Guatemala|Guinea|Guyana|Haiti"
    "|Honduras|Hungary|Iceland|India|Indonesia|Iran|Iraq|Ireland|Israel|Italy|Jamaica|Japan"
    "|Jordan|Kazakhstan|Kenya|Kiribati|Korea|Kosovo|Kuwait|Kyrgyzstan|Laos|Latvia|Lebanon"
    "|Lesotho|Liberia|Libya|Liechtenstein|Lithuania|Luxembourg|Madagascar|Malawi|Malaysia"
    "|Maldives|Mali|Malta|Mauritania|Mauritius|Mexico|Micronesia|Moldova|Monaco|Mongolia"
    "|Montenegro|Morocco|Mozambique|Myanmar|Namibia|Nauru|Nepal|Netherlands|New Zealand"
    "|Nicaragua|Niger|Nigeria|Norway|Oman|Pakistan|Palau|Palestine|Panama|Paraguay|Peru"
    "|Philippines|Poland|Portugal|Qatar|Romania|Russia|Rwanda|Samoa|San Marino|Saudi Arabia"
    "|Senegal|Serbia|Seychelles|Sierra Leone|Singapore|Slovakia|Slovenia|Somalia|South Africa"
    "|Spain|Sri Lanka|Sudan|Suriname|Sweden|Switzerland|Syria|Taiwan|Tajikistan|Tanzania"
    "|Thailand|Togo|Tonga|Trinidad|Tunisia|Turkey|Turkmenistan|Tuvalu|Uganda|Ukraine"
    "|United Kingdom|United States|Uruguay|Uzbekistan|Vanuatu|Vatican|Venezuela|Vietnam|Yemen"
    "|Zambia|Zimbabwe"
)
REAL = re.compile(rf"\b(?:{REAL_COUNTRIES})\b")
NATION_FIELDS = ("conventional_long_name", "common_name")


def plain(value: str) -> str:
    """The name a field shows: links resolved to their label, italics and brackets dropped."""
    value = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", value)
    value = re.sub(r"\([^)]*\)|''+|<[^>]*>", "", value)
    return value.strip()


def run(text: str, ctx: dict) -> list[Finding]:
    title = ctx.get("title")
    # A redraft of the member's own nation page is not a clash with itself, whether the page is
    # titled with the nation's common name or its long name (ctx["nation_pages"]).
    own = ctx.get("nation_pages", {}).get(title, title)
    others = {n: c for n, c in ctx.get("nations", {}).items() if n != own}
    capital_of = {c: n for n, c in others.items() if c}
    found = []
    for n, line in enumerate(lines(text), 1):
        m = FIELD.match(line)
        if not m:
            continue
        field, value = m.group(1), plain(m.group(2))
        if field in NATION_FIELDS and (real := REAL.search(value)):
            level = ERROR
            msg = f"{real.group(0)} is a real country's name; a nation takes none (WS 6.2)"
        elif field != "name" and (value in others or value in capital_of):
            level = ERROR
            msg = f"{value} is already another nation's name or capital (WS 6.5)"
        elif field == "name" and value in capital_of:
            level = WARNING
            msg = (
                f"{value} is {capital_of[value]}'s capital: title the page {value} (your nation), "
                "and it may not be your capital (WS 6.5)"
            )
        else:
            continue
        found.append(Finding(n, "clashes", level, msg))
    return found
