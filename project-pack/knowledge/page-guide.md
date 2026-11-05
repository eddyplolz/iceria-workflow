# The page templates, section by section

Each `.wiki` file here is a bare skeleton: copy it into `notes/drafts/`, replace "Name" and
"Nation", and fill each section in prose. The templates carry no `<!-- -->` comments, because
pages on Iceria carry none and `check.py` fails a draft that has one; what each part asks is
here instead. For every template:

- Leave out any infobox line you have no fact for: an empty line is dropped, and a "none" or
  "N/A" is an error (MoS 14.3). Infobox fields: `templates/infobox-cheatsheet.md`.
- The short description (`{{SHORTDESC:...}}`) is under 60 characters, with no full stop
  (MoS 3.4).

The proposal form for a new nation has its own guide: `templates/proposal-guide.md`.

## Nation article (`nation-article.wiki`)

Nation article skeleton (MoS 8). Order of sections: MoS 8.3.

- **Short description:** name the continent or region.
- **Infobox fields:**
  - `image_map`: the locator map is part of a finished article (MoS 8.4).
  - `largest_city`: "capital" if it is the capital.
  - `sovereignty_type`: "Independence" or "Formation".
  - `area_km2`: the Claims Desk's figure.
  - `GDP_nominal`: in IRU, like 412 billion.
  - `utc_offset`: like +2.
  - `people`: Septentria, Meridia and Selenara: native, settler or mixed.
  - `tier`: set by the stewards.
  - `status`: set by the stewards: provisional or admitted.
- **Lead:** four paragraphs (MoS 8.1):
  1. what and where it is: continent, neighbors, capital, population in 2000;
  2. the shape of its history, in a few sentences;
  3. government and economy;
  4. culture and what the country is known for.

  Every figure carries a reference (MoS 13.2).
- **Etymology:** where the name comes from, in the nation's own language (MoS 7.1, 7.4).
- **History:** one subsection per era, oldest first; history ends in 1999 (MoS 5.1).
- **Geography:** relief, rivers, coasts; then === Climate ===, === Natural resources ===,
  === Environment ===.
- **Government and politics:** the constitution and the head of state; then === Legislature ===,
  === Law and courts ===, === Regions ===, === Foreign relations ===, === Military ===.
- **Economy:** GDP in IRU for 2000 (MoS 5.4); then === Agriculture ===, === Industry ===,
  === Transport ===, === Energy ===.
- **Demographics:** population in 2000; then === Cities ===, === Languages ===, === Religion ===,
  === Education ===.
- **Culture:** === Cuisine ===, === Festivals ===, === Arts and architecture ===,
  === Literature ===, === Media ===, === Sport ===.
- **Participants:** one line per member who takes part in the nation: put your own user name in
  place of YourName. Only the nation's current holder is its creator; everyone else is a
  participant. A short note may follow, as in: `* [[User:Name]] (participant), writes the navy`
  (MoS 8.5).

## City or town (`city.wiki`)

City or town skeleton (MoS 10). A building takes History, Architecture and Use instead, with
{{Infobox building}} (MoS 10.3).

- **Lead:** what kind of place, which nation and region, where it sits, and its population in
  2000 (MoS 10). Example from the manual: "Port-Réal is a port city in Alexandria, at the mouth
  of the Lère in the region of Baudrix. It had about 4.6 million people in 2000."

## Event (`event.wiki`)

Event skeleton (MoS 11): a war, crisis, disaster or election.

- Titles put the year first: "1997 Alexandrian general election" (MoS 2.4).
- An election uses Background, Campaign, Results and Aftermath, with {{Infobox election}}; a war
  uses {{Infobox military conflict}}.
- An event that involves another nation needs that nation's agreement (Charter 3.8).
- **Lead:** what happened, where, when, and with what result. Example from the manual: "The 1991
  Alexandrian coup attempt was an attempt by ... on 3 April 1991." (MoS 11)

## Organization (`organization.wiki`)

Organization skeleton: a company, party, order, armed force or institution.

- Pick the infobox from the table in MoS 14.1 (Infobox political party, Infobox legislature,
  Infobox order, Infobox national military); ask on the Water cooler before making a new one.
- **Lead:** what the body is, where it works, when it was founded, and what it does. Membership
  and seats are given as of 2000 (MoS 1.3, 5.1).

## Person (`person.wiki`)

Biography skeleton (MoS 9).

- **Short description:** what the person is known for.
- A monarch takes Reign for Career, and may add a succession box ({{S-start}}, {{S-bef}},
  {{S-ttl}}, {{S-aft}}, {{S-end}}) above the categories.
- **Lead:** who the person is, when they lived, and why they matter (MoS 9). Give dates as
  14 March 1941 (MoS 5.2). A living person is described as of 2000 (MoS 5.1).
- **Death and legacy:** leave this section out for a person still alive in 2000.

## Treaty (`treaty.wiki`)

Treaty skeleton. Replace "Other nation" too.

- A treaty needs every party's agreement before it is canon (Charter 3.8), and it is filed in
  Category:Treaties as well as each party's category (MoS 17.5).
- Ask on the Water cooler which infobox to use (MoS 14.1).
- **Lead:** who signed it, when and where, and what it settles. Every term that binds the other
  party comes from that party's own pages (MoS 13.1).
