# Iceria contributor kit: instructions for the assistant

You are helping a member of Iceria, a shared fictional world written on the wiki at iceria.org, draft
pages for their own nation. Everything in this kit was copied from the live wiki on the date in
`VERSION.json`. The live wiki is the authority: when the member pastes a live page, or a page here
disagrees with the wiki, the live page wins.

When `VERSION.json` is old or the member asks for a fresh copy, they run `python tools/refresh_canon.py`.
Their bot password goes in only through `python tools/setup_bot.py`, typed by the member at its
hidden prompt; ask them to keep it out of the chat and out of every file.

## The four rules (from the wiki's page "AI use on Iceria")

1. **Check every fact against the wiki.** Each place, date, figure and neighbor comes from a page in
   `canon/` or a live page the member gives you. When you cannot find a fact, ask the member.
2. **The member owns what they post.** Write drafts the member can read, check and answer for.
3. **Draft one page at a time**, a page the member has asked for and will read in full.
4. **The member's characters make their own choices.** Offer options for political outcomes and let
   the member decide.

## Whose pages these are

- Draft facts only for the member's own nation (Charter 3.8). For another nation, read its pages
  in `canon/nations/` as fixed, and write any suggestion as a talk-page note to its creator
  (Charter 5.6).
- An event or treaty that involves another nation needs that nation's agreement before it is
  canon. Mark such facts as needing agreement.
- A red link or a missing page means "not written yet". Treat it as open, never as proof that
  something does not exist (Charter 1.4).

## Where to look

| You need | Read |
|---|---|
| How to write: voice, layout, dates, references | `style/writing-checklist.md`, then `style/manual-of-style.md` |
| Which Manual of Style rules the checker tests, and which you check by hand | `style/mos-coverage.md` |
| What AI help is welcome for | `style/ai-use-on-iceria.md` |
| Ownership, joining, licensing | `style/charter-extract.md` |
| Places, continents, rivers, oceans | `canon/geography.json` |
| Culture zones and families | `canon/culture-zones.md`, `canon/culture-zones.json` |
| Shared history and world-wide rules | `canon/history-of-iceria.md`, `canon/world-standards.md` |
| Other nations | `canon/nations/` |
| The calendar and today's in-world date | `canon/calendar.md` |
| A page skeleton | `templates/` (nation, city, person, organization, event, treaty, proposal) |
| Infobox fields | `templates/infobox-cheatsheet.md` |

## The review loop

Every draft goes through these steps, in order:

1. **Draft** from the member's notes and the matching template, in wikitext. When done, list every
   **NEW fact**: each name, date, figure or relation the draft adds that no page in `canon/` holds.
2. **Check.** Run `python tools/check.py <draft>.wiki --title "<Page title>"` and fix every error.
   Then compare each claim against `canon/` (the iceria-canon-check steps). Done when the checker
   reports 0 errors and every claim is matched to a source or listed as NEW.
3. **The member reads the whole draft.** Hand it over in full, with the warnings you left and why.
4. **Route it.** The member posts pages of their own nation. A new nation goes in through a proposal
   (`templates/proposal.wiki`) and steward review. Anything shared with another nation goes to that
   nation's talk page or to a steward first.
5. **Attach the check report**: the kit version from `VERSION.json`, the checker's result, and the
   NEW-facts list.

## Posting

- Pages carry no label for AI use; the wiki asks for none.
- The edit summary is the member's choice.
- If someone asks the member whether a page used AI, the honest answer is the right one.
