# Changelog

Every release of the kit gets an entry here, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the version numbers follow
[Semantic Versioning](https://semver.org/).

## [0.1.6] - 2026-11-05

### Added

- `check.py` warns when a page has prose under its headings but no opening paragraph above the
  first one (MoS 3.1).

### Changed

- A category page (`--title "Category:..."`) is checked only for hidden comments, like a project
  page: it labels a group of pages and needs no article lead.
- The "figure without a reference" warning now says when to leave it: a page that is the first to
  publish a number needs no reference; a number taken from another page cites that page (MoS 13.2).

### Fixed

- The lead is found under styled banners, navigation bars and `<noinclude>` lines at the top of a
  page, so the bold-title, nation-link and infobox-type checks read the real first sentence. When no
  plain line comes before the first heading, the first block line that ends a sentence is read as
  the lead. Bold in a block below the lead is still reported.
- A heading the page also writes with its capitals in a sentence ("the Imperial Navy") or names in
  a hatnote (`{{Main|Jagoton Compact}}`) is a proper name, not title case. Only the words a reader
  sees count: an infobox value, a table cell, a ref, the target of a piped link or a category does
  not make a heading a proper name.
- A small icon (50px or less, not a thumbnail or framed picture) and a picture in a table cell,
  including a cell with its own attributes (`| align=center | [[File:...]]`), are no longer asked to
  drop their pixel size. A picture in an infobox field (`| image = ...`) or a centered one is still
  read.
- A clause number at the start of a line ("1.", "12)") and a signed offset ("UTC+2") are no longer
  read as numbers to spell out.
- "Today" or "now" inside a quotation is the speaker's word and is no longer reported.
- A page about the whole world ("Iceria", "List of nations of Iceria", "2000 in Iceria") may link
  the shared reference pages. A nation whose name ends "of Iceria" is still a nation, and is still
  warned.
- A bare "forum" (a town square, a forum of nations) is no longer an out-of-world error; "on the
  forum", "forum post" and "forum thread" still are.
- "Leading global players" (firms in a market) and saints' names ("Our Lady", "Our Savior") are no
  longer read as talk about the game or the writer.

## [0.1.5] - 2026-11-05

### Added

- `check.py` now reports an error for a ref whose name is only digits (`<ref name="1978">`):
  MediaWiki's Cite rejects such a name and shows a cite error in place of the citation. A name
  like `constitution1978` passes.

## [0.1.4] - 2026-11-05

### Added

- `templates/page-guide.md`: what each section of each page template asks. The templates
  themselves now carry no `<!-- -->` comments.
- `templates/proposal-guide.md`, built by `refresh_canon.py` from the wiki's proposal form: the
  form's guidance, field by field. The copy in `templates/proposal.wiki` carries no comments.
- `check.py --own-nation "Name"`: checks a page of a nation that is already canon without
  reporting its own name and capital as taken.

### Changed

- A `<!-- -->` comment anywhere in a draft is now an error, not a warning: pages on Iceria carry
  none.
- A page with a `{{Proposal}}` form is read as a form even when text sits above it. Lines outside
  the form are not checked, and a warning says how many.
- A project page (the Iceria Meta Masthead or Category:Meta Iceria) is checked only for hidden
  comments, since the Manual of Style is for articles.

### Fixed

- A proposal answer written on the lines under its `| history =` line is read whole, not as empty.
  It ends at the next `| field =` line, whatever the field's name.
- Page names inside links and HTML tags (`<span style="...">`) are no longer read as prose, so a
  hyphen in them is not a dash error.
- "A claim to the coast" and "its claim that" are no longer flagged as talk about the claim map.
- `templates/infobox-cheatsheet.md` carries no `<!-- -->` comments: each note from the wiki's
  page is plain text, and a note on a field is listed under the box as "`field`: note".

## [0.1.3] - 2026-11-04

### Added

- README: "Use the Claude desktop app", the steps for running the kit from the desktop app's Code
  tab with no Terminal install. "Making your plan last" now gives the desktop app's way to start a
  fresh session and switch models.

### Fixed

- `refresh_canon.py`'s own notes no longer suggest a bot password gets past the wiki's firewall or
  browser check. It does not: when the wiki asks for one, the read is refused either way.

## [0.1.2] - 2026-11-04

### Fixed

- When iceria.org's firewall refuses your computer (HTTP 403), every tool now says so in plain
  words: it is the wiki's firewall, not your setup; drafting and `check.py --offline` still work;
  send the maintainer everything the tool printed. `setup_bot.py` no longer calls a refusal a
  login problem, and `refresh_canon.py` no longer calls it a connection problem.

## [0.1.1] - 2026-11-04

### Added

- README: install steps for Claude Code on Mac and Windows, a "Where your drafts go" section
  (`notes/drafts/`), and "Making your plan last", four habits for a monthly plan.
- `doctor.py`: a note when you have refreshed canon files locally, with the `git restore`
  line to run before `git pull`. It is a note, not a failure.

### Changed

- Drafts now go in `notes/drafts/` in the README, `AGENTS.md`, and the drafting skill.
- Tool messages name the README step that fixes the problem ("'Set up a Mac (once)' step 7" or
  "'Set up Windows (once)' step 5"), not a step that no longer exists.
- README: the Codex and Projects paths are marked untested; nobody has run them yet.

### Fixed

- The infobox check names the placeholder it found instead of a generic error.
- `map_overlay.py` writes the base map's path relative to the SVG, so the SVG no longer holds
  your computer's folder names and still opens when the folder moves.
- `iceria_calendar.py` reads a `--real` time with a UTC offset (such as `+05:00`) as that moment
  in UTC instead of crashing.
- A failed Windows Credential Manager save prints what went wrong and the way around it (set the
  two environment variables) instead of a traceback.

## [0.1.0] - 2026-11-02

First public release.
