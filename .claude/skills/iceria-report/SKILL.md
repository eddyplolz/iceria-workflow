---
name: iceria-report
description: Write a problem report the member sends to the kit's maintainer. Use when a kit tool crashes or gives a wrong answer, when the checker flags something that is right or misses something that is wrong, or when the member says the kit or its instructions got something wrong.
---

# Write a problem report

1. **Gather the facts.** The kit version from `VERSION.json` and `KIT_VERSION`, the output of
   `python tools/doctor.py`, the exact command that was run, and its full output.
2. **Write `notes/report-<YYYY-MM-DD>.md`** with these headings, each filled in plain words:
   - **Kit version**
   - **Tool**: the tool, skill or instruction file involved
   - **What happened**
   - **What was expected**, with the rule or canon page that says so
   - **Command and output**: the command and its output, as they came
   - **Snippet**: the few lines of the draft that trigger it, only if the member agrees
   - **Doctor**: the output of `tools/doctor.py`
3. **Leave out anything private.** No password, no bot login name, and no draft text the member has
   not agreed to share. Ask before including any of the draft.
4. **Hand it over.** Tell the member the file's path and that they send it to the maintainer on the
   Iceria Discord. You never send it yourself.

Do not change the kit's tools, skills, templates or `canon/` to work around the problem; the report
is how the fix reaches every member. Done when the file is written and the member knows where it is.
