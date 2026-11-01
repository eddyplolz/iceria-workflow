# Check a draft against canon

1. **List the claims.** Every place name, date, figure, neighbor, culture zone, religion and
   historical event in the draft, one per line.
2. **Match each claim** to its source, in the order Charter 1.4 sets:
   1. the official geography (`canon/geography.json`) and maps;
   2. the Charter and `canon/world-standards.md`;
   3. shared history (`canon/history-of-iceria.md`) and agreed treaties and events;
   4. each nation's own pages (`canon/nations/`).
   Mark each claim **matches** (with the file and section), **conflicts** (quote both), or **NEW**.
3. **Treat a missing page as unwritten.** A claim no page covers is NEW, never a conflict.
4. **Flag another nation's facts.** Any claim about another nation must agree with that nation's page;
   otherwise it is a conflict or needs that nation's agreement.
5. **Run the checker:** `python tools/check.py <draft>.wiki --title "<Page title>"`. Its `names`
   warnings point at names not in the official geography: decide for each whether it is NEW.

Done when every claim carries one of the three marks, and every conflict is reported to the member
with both sources quoted.
