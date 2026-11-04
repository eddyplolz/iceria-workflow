# Changelog

Every release of the kit gets an entry here, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the version numbers follow
[Semantic Versioning](https://semver.org/).

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
