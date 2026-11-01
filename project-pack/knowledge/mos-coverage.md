# Manual of Style coverage

Every numbered section of the [Manual of Style](manual-of-style.md) (MoS), and what in this kit
holds it. Read it as the map of where a draft can still go wrong:

- `check: x` means `tools/check.py` tests for it (module `tools/checks/x.py`). Fix every error.
- `checklist N` means rule N of [writing-checklist.md](writing-checklist.md) carries it.
- `template` means the skeletons in `templates/` already follow it.
- `steward` means a steward does it, never the writer.
- `by hand` means nothing here tests it. The self-audit walks each of these rows by hand.

The kit's build compares this table with the live manual and refuses to ship when a section has
no row, so a new rule on the wiki cannot slip past the kit unnoticed.

| MoS | Rule | Held by |
|---|---|---|
| 1.1 | Write as an encyclopedia inside the world; describe only what is settled | check: voice; checklist 1 |
| 1.2 | Neutral point of view; attribute opinions | check: voice; checklist 2 |
| 1.3 | Past for history, present for what exists, a year on what changes | check: dates; checklist 3 |
| 1.4 | Plain, specific prose | check: ai_tells; checklist 4 |
| 1.5 | Words to watch | check: voice; check: ai_tells; checklist 4 |
| 1.6 | Wikipedia-grade: every section a good article would carry | checklist 12; by hand |
| 2.1 | Titles use the common name, in sentence case | check: headings; checklist 7 |
| 2.2 | A nation's title is its short name | by hand |
| 2.3 | Telling same-named pages apart | check: clashes; by hand |
| 2.4 | Titles of people and events | by hand |
| 3.1 | The first sentence: subject in bold, what and where it is | check: bold; checklist 8 |
| 3.2 | The lead summarizes the body | by hand |
| 3.3 | Lead length | by hand |
| 3.4 | The short description | check: markup; checklist 12 |
| 4.1 | Sections and headings in sentence case | check: headings; checklist 7 |
| 4.2 | Closing sections: See also, Notes, References; no External links | check: headings; template; checklist 11 |
| 4.3 | Prose over lists; wikitext, never Markdown | check: markup |
| 4.4 | Main articles and summary sections | by hand |
| 5.1 | The calendar: nothing after the present | check: dates; checklist 5 |
| 5.2 | Writing dates | check: dates |
| 5.3 | Numbers: spell out zero to nine, no numeral opens a sentence | check: numbers; by hand |
| 5.4 | Currencies, with the IRU figure first for a whole economy | by hand |
| 5.5 | Units: metric, a space between number and symbol | check: numbers; by hand |
| 6.1 | One variety of English per article | check: spelling; checklist 16 |
| 6.2 | Capital letters | by hand |
| 6.3 | Bold in the lead only; italics for works, ships and foreign words | check: bold; checklist 8; checklist 9 |
| 6.4 | Punctuation: no dashes in prose, en dash for ranges | check: dashes; checklist 10 |
| 6.5 | Abbreviations without full stops | check: markup; by hand |
| 7.1 | Place names fit the nation | by hand |
| 7.2 | No real-world names | check: voice; check: clashes; checklist 5 |
| 7.3 | The fixed names, and naming a new feature | check: names; checklist 19 |
| 7.4 | Native names and words in other languages | checklist 9; by hand |
| 8.1 | A nation's lead | by hand |
| 8.2 | A nation's infobox | template |
| 8.3 | A nation's section order | template; checklist 11 |
| 8.4 | A finished nation article | by hand |
| 9.1 | Biography titles | by hand |
| 9.2 | A biography's lead | by hand |
| 9.3 | Names in the text | by hand |
| 9.4 | The living, the dead, and other members' characters | checklist 6 |
| 9.5 | Biography infoboxes and succession boxes | template |
| 9.6 | Biography section order | template; checklist 11 |
| 10.1 | A place's lead | by hand |
| 10.2 | Place infoboxes | template |
| 10.3 | Place section order | template; checklist 11 |
| 11.1 | Event titles | by hand |
| 11.2 | An event's lead | by hand |
| 11.3 | Event infoboxes | template |
| 11.4 | Event section order | template; checklist 11 |
| 12.1 | What to link | by hand |
| 12.2 | What not to link: no self-links, no links in headings | check: links; check: headings |
| 12.3 | Red links mean "not written yet" | checklist 18; checklist 19 |
| 12.4 | Piped links and links to sections | check: refs; by hand |
| 13.1 | A reference cites a page on this wiki | check: refs; checklist 13; checklist 14 |
| 13.2 | What needs a reference | check: markup; checklist 15; by hand |
| 13.3 | How to write a reference | check: refs |
| 13.4 | Notes take their own group | by hand |
| 14.1 | Which infobox | template; checklist 18 |
| 14.2 | The infobox repeats the article | by hand |
| 14.3 | Leave out fields that do not apply | check: markup; checklist 18 |
| 15.1 | Upload images here, with a description page and a category | checklist 17 |
| 15.2 | Maps follow the official maps | by hand |
| 15.3 | Captions | check: links; checklist 17; by hand |
| 15.4 | Image placement and size | check: links; by hand |
| 16.1 | Short and long quotations | by hand |
| 16.2 | Attribute every quotation inside the world | by hand |
| 16.3 | Quotations never argue or praise | by hand |
| 17.1 | The two category trees; every page has a category | check: markup; check: links; by hand |
| 17.2 | One category per nation, made by a steward | check: links; steward; checklist 18 |
| 17.3 | Splitting a crowded nation category | by hand |
| 17.4 | The most specific category only | by hand |
| 17.5 | Pages that belong to no single nation | by hand |
| 17.6 | Category names, and making a new one | check: links; checklist 18 |
| 17.7 | Maintenance categories come from templates | steward |
| 17.8 | Stewards tidy categories | steward |
| 18.1 | What goes in the Library | checklist 6; by hand |
| 18.2 | A written work's page | by hand |
| 18.3 | The writer's voice in a written work | by hand |
| 18.4 | Long works and series | by hand |
| 18.5 | Who edits a work | by hand |
| 18.6 | Articles about a work | by hand |
| 19 | The finishing checklist | checklist 21; by hand |
| 20 | Where the manual is silent, follow Wikipedia's | checklist 21 |
