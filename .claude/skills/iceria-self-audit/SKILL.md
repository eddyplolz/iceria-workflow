---
name: iceria-self-audit
description: Style and AI-tell audit of an Iceria draft before the member reads it. Use after canon-check, when the member asks to polish or review a draft, or when the checker reports warnings.
---

# Audit a draft's style

1. **Run the checker:** `python tools/check.py <draft>.wiki --title "<Page title>" --humanizer`.
   Fix every error, and treat each humanizer finding as a warning. If it says humanizer-audit is
   not installed, tell the member once that setup step 5 in `README.md` adds it, and carry on.
2. **Read each warning** and either fix it or write one line on why it stays.
3. **Treat each tell as a class.** When one AI tell turns up (puffery, a stock phrase, a "not only
   ... but also", a run of three), search the whole draft for it and its relatives, and fix them
   all.
4. **Walk `style/writing-checklist.md`** rule by rule, then the checklist in MoS 19 ("Before you
   call it finished"). Note each rule the draft fails.
5. **Walk the `by hand` rows** of `style/mos-coverage.md` that fit the page type: nothing in the
   kit tests these, so read the MoS section each row names and hold the draft against it. Skip a
   row only when the page type puts it out of reach (a nation article skips 9, 10, 11 and 18).
6. **Write the check report** for the member: the kit version from `VERSION.json`, the checker's
   result line, the warnings kept and why, the MoS sections the draft still fails, and the NEW-facts
   list.

Done when the checker reports 0 errors, every kept warning has its reason, and every checklist rule
and every fitting `by hand` row has been read against the draft.
