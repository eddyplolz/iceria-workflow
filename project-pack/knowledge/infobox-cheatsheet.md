# Template:Infobox Country/doc

Copied from the Iceria wiki page "Template:Infobox Country/doc" (revision 1131) on 2026-10-31. The live page outranks this copy.

'''Template:Infobox Country''' is the fact box on the right of a nation's page ([[World Standards]] 7.1). It follows Wikipedia's Infobox country: the same field names and layout, so a box copied from a Wikipedia-style draft works as it is. <code><nowiki>{{Infobox country}}</nowiki></code>, with a small c, works too. [[Alexandria]] shows one filled in.

== Quick start ==
Every field is optional, and only the fields filled in are shown. A short box looks like this:
<pre>{{Infobox country
| conventional_long_name = The full official name
| common_name            = The short name
| image_flag             = Flag of your nation.svg
| capital                = Your capital
| official_languages     = Your languages
| government_type        = Parliamentary republic
| leader_title1          = President
| leader_name1           = A name
| area_km2               = 412,000
| population_estimate    = 18 million
| population_estimate_year = 2000
| currency               = Your currency
}}</pre>

== Parameters ==
The full list, ready to copy. Leave out any line you don't need.
<pre>{{Infobox country
| conventional_long_name =
| common_name            =
| native_name            =
| image_flag             =
| image_coat             =
| symbol_type            =
| national_motto         =
| national_anthem        =
| image_map              =
| map_caption            =
| capital                =
| largest_city           = <!-- "capital" if it is the capital -->
| official_languages     =
| languages_type         =
| languages              =
| ethnic_groups          =
| ethnic_groups_year     =
| religion               =
| religion_year          =
| demonym                =
| government_type        =
| leader_title1          =
| leader_name1           =
| leader_title2          =
| leader_name2           =
| legislature            =
| upper_house            =
| lower_house            =
| sovereignty_type       = <!-- "Independence" or "Formation" -->
| established_event1     =
| established_date1      =
| area_km2               = <!-- the Claims Desk's figure -->
| percent_water          =
| population_estimate    =
| population_estimate_year =
| population_census      =
| population_census_year =
| GDP_nominal            = <!-- in IRU, like 412 billion -->
| GDP_nominal_year       =
| Gini                   =
| Gini_year              =
| HDI                    =
| HDI_year               =
| currency               =
| currency_code          =
| utc_offset             = <!-- like +2 -->
| time_zone              =
| drives_on              =
| calling_code           =
| continent              =
| culture_zone           =
| culture_twist          =
| people                 = <!-- Septentria, Meridia and Selenara: native, settler or mixed -->
| tier                   = <!-- set by the stewards -->
| status                 = <!-- set by the stewards: provisional or admitted -->
}}</pre>
Leaders run to six (<code>leader_title1</code> to <code>leader_title6</code>, with their names) and founding events to eight (<code>established_event1</code> to <code>established_event8</code>, with their dates).

== What the World Standards ask ==
{| class="wikitable"
! Field !! What to give
|-
| <code>area_km2</code> || The figure the Claims Desk reports, in km² ([[World Standards]] 5.4)
|-
| <code>GDP_nominal</code> || Money in International Reference Units (IRU); the nation's own currency goes in <code>currency</code> ([[World Standards]] 8.1)
|-
| <code>utc_offset</code> || Counted from Iceria's prime meridian: <code>+2</code> shows "Zone +2" ([[World Standards]] 5.2)
|-
| <code>image_flag</code> || A 2:3 or 1:2 flag, uploaded as SVG or as a PNG at least 600 pixels wide ([[World Standards]] 7.3)
|-
| <code>religion</code> || Iceria's faiths, such as Soterian or Diathecan ([[World Standards]] 13.3)
|-
| <code>culture_zone</code>, <code>culture_twist</code> || The nation's zone on the [[Culture zones of Iceria|culture-zone map]], and its twist if it differs ([[World Standards]] 10.2)
|-
| <code>tier</code>, <code>status</code> || Set by the stewards: great, regional or local power, and provisional or admitted ([[Charter]] 3.2 and 3.7)
|}

== Notes for experienced editors ==
* [[Module:Infobox country]] builds the box. It works out population density and GDP per person from the population, the area and the GDP.
* When either figure falls outside the plausible ranges, the page goes in the hidden [[:Category:Countries outside the plausibility ranges]] for the stewards; a nation may be outside them if its page explains why ([[World Standards]] 8.2).
* The box files a nation's page in [[:Category:Countries]], but only an ordinary article page, so this documentation shows code and no live box.

== TemplateData ==
These are the fields the visual editor shows when you add or edit this template. Editing the source, you can skip this section.
<templatedata>
{
	"description": "The fact box on a nation's page, with Wikipedia's Infobox country field names. Every field is optional.",
	"params": {
		"conventional_long_name": {
			"label": "Full name",
			"description": "The full official name.",
			"type": "line",
			"suggested": true
		},
		"common_name": {
			"label": "Short name",
			"description": "The short name.",
			"type": "line",
			"suggested": true
		},
		"native_name": {
			"label": "Native name",
			"description": "The name in the nation's own language.",
			"type": "line"
		},
		"image_flag": {
			"label": "Flag",
			"description": "The flag's file name: 2:3 or 1:2, SVG or a PNG at least 600 pixels wide (World Standards 7.3).",
			"type": "wiki-file-name",
			"suggested": true
		},
		"image_coat": {
			"label": "Coat of arms",
			"description": "The coat of arms or emblem's file name.",
			"type": "wiki-file-name"
		},
		"symbol_type": {
			"label": "Symbol type",
			"description": "What the second image is, such as Coat of arms or Emblem.",
			"type": "line"
		},
		"national_motto": {
			"label": "Motto",
			"description": "The national motto.",
			"type": "line"
		},
		"national_anthem": {
			"label": "Anthem",
			"description": "The national anthem.",
			"type": "line"
		},
		"image_map": {
			"label": "Map",
			"description": "The map's file name.",
			"type": "wiki-file-name",
			"suggested": true
		},
		"map_caption": {
			"label": "Map caption",
			"description": "The map's caption.",
			"type": "line"
		},
		"capital": {
			"label": "Capital",
			"description": "The capital.",
			"type": "wiki-page-name",
			"suggested": true
		},
		"largest_city": {
			"label": "Largest city",
			"description": "The largest city, or capital if it is the capital.",
			"type": "line"
		},
		"official_languages": {
			"label": "Official languages",
			"description": "The official languages.",
			"type": "line"
		},
		"languages_type": {
			"label": "Other languages heading",
			"description": "A heading for the other languages, such as Regional languages.",
			"type": "line"
		},
		"languages": {
			"label": "Other languages",
			"description": "The other languages.",
			"type": "line"
		},
		"ethnic_groups": {
			"label": "Ethnic groups",
			"description": "The ethnic groups.",
			"type": "line"
		},
		"ethnic_groups_year": {
			"label": "Ethnic groups year",
			"description": "The year of the ethnic groups figures.",
			"type": "line"
		},
		"religion": {
			"label": "Religion",
			"description": "Iceria's faiths, such as Soterian or Diathecan (World Standards 13.3).",
			"type": "line"
		},
		"religion_year": {
			"label": "Religion year",
			"description": "The year of the religion figures.",
			"type": "line"
		},
		"demonym": {
			"label": "Demonym",
			"description": "What its people are called.",
			"type": "line"
		},
		"government_type": {
			"label": "Government",
			"description": "The form of government.",
			"type": "line",
			"suggested": true
		},
		"leader_title1": {
			"label": "Leader 1 title",
			"description": "The first leader's title; leaders run to 6.",
			"type": "line",
			"example": "President"
		},
		"leader_name1": {
			"label": "Leader 1 name",
			"description": "The first leader's name.",
			"type": "line"
		},
		"leader_title2": {
			"label": "Leader 2 title",
			"description": "The second leader's title.",
			"type": "line",
			"example": "Prime Minister"
		},
		"leader_name2": {
			"label": "Leader 2 name",
			"description": "The second leader's name.",
			"type": "line"
		},
		"legislature": {
			"label": "Legislature",
			"description": "The legislature's name.",
			"type": "line"
		},
		"upper_house": {
			"label": "Upper house",
			"description": "The upper house's name.",
			"type": "line"
		},
		"lower_house": {
			"label": "Lower house",
			"description": "The lower house's name.",
			"type": "line"
		},
		"sovereignty_type": {
			"label": "Founding heading",
			"description": "Independence or Formation.",
			"type": "line",
			"suggestedvalues": [
				"Independence",
				"Formation"
			]
		},
		"established_event1": {
			"label": "Founding event 1",
			"description": "The first founding event; events run to 8.",
			"type": "line"
		},
		"established_date1": {
			"label": "Founding date 1",
			"description": "The first founding event's date.",
			"type": "line"
		},
		"area_km2": {
			"label": "Area (km²)",
			"description": "The figure the Claims Desk reports (World Standards 5.4).",
			"type": "line",
			"suggested": true,
			"example": "412,000"
		},
		"percent_water": {
			"label": "Water (%)",
			"description": "The share of the area that is water.",
			"type": "line"
		},
		"population_estimate": {
			"label": "Population",
			"description": "The population estimate.",
			"type": "line",
			"suggested": true,
			"example": "18 million"
		},
		"population_estimate_year": {
			"label": "Population year",
			"description": "The year of the estimate.",
			"type": "line",
			"example": "2000"
		},
		"population_census": {
			"label": "Census population",
			"description": "The last census population.",
			"type": "line"
		},
		"population_census_year": {
			"label": "Census year",
			"description": "The year of the last census.",
			"type": "line"
		},
		"GDP_nominal": {
			"label": "GDP",
			"description": "In International Reference Units (IRU), such as 412 billion (World Standards 8.1).",
			"type": "line",
			"example": "412 billion"
		},
		"GDP_nominal_year": {
			"label": "GDP year",
			"description": "The year of the GDP figure.",
			"type": "line"
		},
		"Gini": {
			"label": "Gini",
			"description": "The Gini coefficient.",
			"type": "number"
		},
		"Gini_year": {
			"label": "Gini year",
			"description": "The year of the Gini figure.",
			"type": "line"
		},
		"HDI": {
			"label": "HDI",
			"description": "The Human Development Index.",
			"type": "number"
		},
		"HDI_year": {
			"label": "HDI year",
			"description": "The year of the HDI figure.",
			"type": "line"
		},
		"currency": {
			"label": "Currency",
			"description": "The nation's own currency.",
			"type": "line"
		},
		"currency_code": {
			"label": "Currency code",
			"description": "Its three-letter code.",
			"type": "line"
		},
		"utc_offset": {
			"label": "Time zone offset",
			"description": "Counted from Iceria's prime meridian, such as +2 (World Standards 5.2).",
			"type": "line",
			"example": "+2"
		},
		"time_zone": {
			"label": "Time zone name",
			"description": "The time zone's name.",
			"type": "line"
		},
		"drives_on": {
			"label": "Drives on",
			"description": "left or right.",
			"type": "line",
			"suggestedvalues": [
				"left",
				"right"
			]
		},
		"calling_code": {
			"label": "Calling code",
			"description": "The telephone calling code.",
			"type": "line"
		},
		"continent": {
			"label": "Continent",
			"description": "The continent.",
			"type": "line"
		},
		"culture_zone": {
			"label": "Culture zone",
			"description": "The nation's zone on the culture-zone map (World Standards 10.2).",
			"type": "line"
		},
		"culture_twist": {
			"label": "Culture twist",
			"description": "For a nation whose culture differs from its zone.",
			"type": "line"
		},
		"people": {
			"label": "People",
			"description": "On Septentria, Meridia and Selenara: native, settler or mixed.",
			"type": "line"
		},
		"tier": {
			"label": "Tier",
			"description": "Set by the stewards: great, regional or local power (Charter 3.7).",
			"type": "line"
		},
		"status": {
			"label": "Status",
			"description": "Set by the stewards: provisional or admitted (Charter 3.2).",
			"type": "line",
			"suggestedvalues": [
				"provisional",
				"admitted"
			]
		}
	},
	"paramOrder": [
		"conventional_long_name",
		"common_name",
		"native_name",
		"image_flag",
		"image_coat",
		"symbol_type",
		"national_motto",
		"national_anthem",
		"image_map",
		"map_caption",
		"capital",
		"largest_city",
		"official_languages",
		"languages_type",
		"languages",
		"ethnic_groups",
		"ethnic_groups_year",
		"religion",
		"religion_year",
		"demonym",
		"government_type",
		"leader_title1",
		"leader_name1",
		"leader_title2",
		"leader_name2",
		"legislature",
		"upper_house",
		"lower_house",
		"sovereignty_type",
		"established_event1",
		"established_date1",
		"area_km2",
		"percent_water",
		"population_estimate",
		"population_estimate_year",
		"population_census",
		"population_census_year",
		"GDP_nominal",
		"GDP_nominal_year",
		"Gini",
		"Gini_year",
		"HDI",
		"HDI_year",
		"currency",
		"currency_code",
		"utc_offset",
		"time_zone",
		"drives_on",
		"calling_code",
		"continent",
		"culture_zone",
		"culture_twist",
		"people",
		"tier",
		"status"
	],
	"format": "block"
}
</templatedata>

== See also ==
* [[Module:Infobox country]]
* {{tl|Proposal}}, whose infobox uses the same field names<includeonly>[[Category:Infobox templates]]</includeonly>
