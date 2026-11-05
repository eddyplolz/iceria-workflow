# Changelog

Every release of the kit gets an entry here, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the version numbers follow
[Semantic Versioning](https://semver.org/).

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
