"""Signs that a draft came out of a chat window: AI use on Iceria and MoS 1.5.

Chatbot artifacts, unfilled placeholders and invisible characters are errors: none of them belongs
on a page. AI vocabulary and stock sentence patterns are warnings, since a person writes them too.
If humanizer-audit is installed, `check.py --humanizer` adds its score; this module stays stdlib.
"""

import re

from checks import ERROR, WARNING, Finding, lines, strip_refs

ARTIFACT = re.compile(
    r"citeturn\d|contentReference|oaicite|oai_citation|utm_source=(?:chatgpt|claude|openai|copilot|perplexity)"
    r"|\bas an AI\b|\bas a language model\b|I hope this helps|let me know if you",
    re.I,
)
PLACEHOLDER = re.compile(
    r"(?<!\[)\[(?:Your|Insert|Add|Name of)\b[^\]]*\](?!\])|\bINSERT_|\bPASTE_|\bTODO\b|\bTBD\b|\b\d{2}XX\b|XX-XX|lorem ipsum",
    re.I,
)
INVISIBLE = re.compile("[​‌‍⁠﻿­]")
VOCAB = re.compile(
    r"\b(delve[sd]?|delving|intricate|intricacies|showcas(?:e|es|ed|ing)|underscor(?:e|es|ed|ing)"
    r"|seamless(?:ly)?|realm|tapestry|multifaceted|pivotal|testament|bustling|meticulous(?:ly)?"
    r"|navigat(?:e|es|ing) the|ever-evolving|in the heart of|embark(?:s|ed)?|foster(?:s|ed|ing)?"
    r"|garner(?:s|ed)?|enduring legacy|captivating)\b",
    re.I,
)
PATTERN = re.compile(
    r"\bnot only\b.*\bbut also\b|^\s*(?:In conclusion|In summary)\b|^\s*(?:Overall|Ultimately),"
    r"|\bit is not just\b.*\bit is\b|\bmore than just\b",
    re.I,
)


def run(text: str, ctx: dict) -> list[Finding]:
    found = []
    # Raw lines: artifacts and placeholders hide in comments and refs too.
    for n, line in enumerate(text.splitlines(), 1):
        if ARTIFACT.search(line):
            found.append(
                Finding(
                    n,
                    "ai_tells",
                    ERROR,
                    "chatbot artifact: delete the pasted tool output (AI use on Iceria)",
                )
            )
        if PLACEHOLDER.search(line):
            found.append(Finding(n, "ai_tells", ERROR, "placeholder: fill it in or cut it"))
        if INVISIBLE.search(line):
            found.append(
                Finding(
                    n,
                    "ai_tells",
                    ERROR,
                    "invisible character: zero-width or soft hyphen, delete it",
                )
            )
    for n, line in enumerate(lines(text), 1):
        prose = strip_refs(line)
        words = list(dict.fromkeys(m.group(0).lower() for m in VOCAB.finditer(prose)))
        if words:
            found.append(
                Finding(
                    n,
                    "ai_tells",
                    WARNING,
                    f"AI vocabulary: {', '.join(words)}; say it plainly (MoS 1.5)",
                )
            )
        if PATTERN.search(prose):
            found.append(
                Finding(
                    n,
                    "ai_tells",
                    WARNING,
                    "AI sentence pattern: state the point directly (MoS 1.5)",
                )
            )
    return sorted(found, key=lambda f: f.line)
