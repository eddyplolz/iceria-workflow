# Writing checklist

The rules an Iceria article has to meet, in one place. Each line names the clause it comes from:
a bare number is a section of the [Manual of Style](manual-of-style.md) (MoS), and "Charter" is
the [Charter](charter-extract.md). Where a line and the live page disagree, the live page wins.
`(check: x)` marks the rules `tools/check.py` tests for; the rest are yours to hold.

## Voice

1. **Stay inside the world.** Article prose never mentions members, players, proposals, claims,
   maps, the wiki, or pages "to be written". It describes only what is settled (1.1).
   `(check: voice)`
2. **Neutral point of view.** Attribute opinions to whoever holds them. A nation's view of itself
   is a view, and a neighbor's facts come from that neighbor's own pages (1.2). `(check: voice)`
3. **Tense and time.** The past for history, the present for what exists, and a year on anything
   that changes: "had 4.6 million people in 2000", never "currently" (1.3). `(check: dates)`
4. **Describe, never promote.** Plain prose with no praise, puffery or stock phrases. Check every
   word on the words-to-watch list (1.4, 1.5). `(check: voice, ai_tells)`
5. **Nothing after the present.** Until launch, history ends in 1999 and figures are given for
   2000. The future appears only as plans made in-world ("the next election is due by 2002") (5.1).
   Iceria has no real-world countries, so use none of their names (7.2). `(check: dates, voice)`
6. **Your nation only.** Never write facts for a nation that is not yours. Its own pages decide
   them (13.1, Charter 3.8). Its pages belong to its creator: anything beyond typos and links goes
   on the talk page first (Charter 5.6).

## Form

7. **Sentence case** for every title and heading: "Foreign relations", not "Foreign Relations"
   (2.1, 4.1). `(check: headings)`
8. **The lead** opens with the subject in bold and says what and where it is (3.1). Bold appears
   in the lead only: no bolded lead-ins, no bold in headings (6.3). `(check: bold)`
9. **Italics** for the titles of works, ships, and foreign words (6.3).
10. **No dashes in running prose.** Use commas, colons or a new sentence; an en dash belongs only
    in ranges such as 1406–1632 (6.4). `(check: dashes)`
11. **Section order.** Use the sections your kind of article takes, in its order: nations 8.3,
    people 9.6, places 10.3, events 11.4. Close with See also, Notes, References, and never
    External links (4.2). A nation's article puts its Participants first among these: one line
    per member, `* [[User:Name]] (creator)` or `(participant)` (8.5). `(check: participants)` The templates in `templates/` already follow these.
12. **Wikipedia-grade.** Draft every section a good Wikipedia article on the same subject would
    carry, the infobox and short description included, in one pass (1.6, 3.4, 14).
    `(check: markup)`

## Sources

13. **Every reference is a page on this wiki.** Never an outside site, Discord, a talk page or the
    Water cooler. When sources disagree, the order in Charter 1.4 decides: the official maps, then
    the Charter, then agreed treaties and events, then each nation's own pages (13.1).
    `(check: refs)`
14. **Cite the page that holds the fact**, and the section of a long one, never a summary of it.
    Never invent a source (13.1).
15. **What needs a reference:** every figure, every date another page could contradict, every fact
    touching another nation, and every quotation. A figure your article publishes first needs
    none; a nation's area is always the Claims Desk figure (13.2). `(check: markup, refs)`
16. **One variety of English** per article. Keep the one the article already uses (6.1).
    `(check: spelling)`

## Pages and files

17. **Images** are uploaded to this wiki, with a description page and a category. Captions say
    what the image shows and stay inside the world (15.1, 15.3).
18. **Links and categories.** A red link is fine: it means "not written yet" (12.3). Use a
    category that exists before making one; a new one needs a description and a parent (17.6).
    A nation's own category is made by a steward (17.2). Ask on the Water cooler before making a
    new infobox (14.1). Leave out an infobox field that does not apply, never "none" or "N/A"
    (14.3). `(check: markup)`
19. **When unsure, ask the human.** Treat a fact you cannot find as unwritten lore, never as proof
    that something does not exist (12.3, Charter 1.4). `(check: names)` flags names it does not
    know, so you can ask whether each is new canon.

## Finishing

20. **A flagged tell is a class.** When a check or a reader flags one AI tell, look for it and its
    relatives through the whole draft, not just at the flagged line. `(check: ai_tells)`
21. **Where the manual is silent**, follow Wikipedia's Manual of Style; where the two disagree,
    Iceria's manual wins (20). Before you call an article finished, go through the checklist in
    MoS 19.
