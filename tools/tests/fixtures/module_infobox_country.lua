-- Trimmed from the live Module:Infobox country: only the lines that read a field.
	local function v(k)
	local name = v("common_name") or v("conventional_long_name") or mw.title.getCurrentTitle().text
	if v("common_name") and v("conventional_long_name") then
		top:tag("div"):addClass("ib-long"):wikitext(v("conventional_long_name"))
	if v("native_name") then
		top:tag("div"):addClass("ib-native"):wikitext(v("native_name"))
	if v("image_flag") or v("image_coat") then
		if v("image_flag") then
			imgs:tag("td"):wikitext("[[File:" .. v("image_flag") .. "|125px|border|" .. (v("alt_flag") or "Flag") .. "]]")
		if v("image_coat") then
			imgs:tag("td"):wikitext("[[File:" .. v("image_coat") .. "|85px|" .. (v("symbol_type") or "Coat of arms") .. "]]")
			caps:tag("td"):addClass("ib-caption"):wikitext(v("symbol_type") or "Coat of arms")
	if v("national_motto") then
		center("'''Motto:''' ''" .. v("national_motto") .. "''")
	if v("national_anthem") then
		center("'''Anthem:''' ''" .. v("national_anthem") .. "''")
	if v("image_map") then
		center("[[File:" .. v("image_map") .. "|250px|" .. (v("map_caption") or "Map") .. "]]"
			.. (v("map_caption") and ('<div class="ib-caption">' .. v("map_caption") .. "</div>") or ""))
	local capital, largest = v("capital"), v("largest_city")
	row("Official languages", v("official_languages"), true)
	row(v("languages_type") or "Other languages", v("languages"), not v("official_languages"))
	local eth = v("ethnic_groups")
	row("Ethnic groups" .. (v("ethnic_groups_year") and (" (" .. v("ethnic_groups_year") .. ")") or ""), eth, true)
	row("Religion" .. (v("religion_year") and (" (" .. v("religion_year") .. ")") or ""), v("religion"), not eth)
	row("Demonym", v("demonym"), not (eth or v("religion")))
	if v("government_type") or v("leader_name1") then
		row("Government", v("government_type") or "", true)
			if v("leader_name" .. i) then
				row(v("leader_title" .. i) or "Leader", v("leader_name" .. i), false, true)
	if v("legislature") then
		row("Legislature", v("legislature"), true)
		row("Upper house", v("upper_house"), false, true)
		row("Lower house", v("lower_house"), false, true)
	if v("established_event1") then
		heading(v("sovereignty_type") or "Formation", true)
			if v("established_event" .. i) then
				row(v("established_event" .. i), v("established_date" .. i) or "", false, true)
	local area = p.number(v("area_km2"))
		row("Total", fmt(area) .. " km²" .. (v("area_footnote") or ""), false, true)
		row("Water (%)", v("percent_water"), false, true)
	local pe, pc = p.number(v("population_estimate")), p.number(v("population_census"))
			row((v("population_estimate_year") or "") .. " estimate", fmt(pe), false, true)
			row((v("population_census_year") or "") .. " census", fmt(pc), false, true)
	local gdp = p.number(v("GDP_nominal"))
		heading("GDP (nominal)" .. (v("GDP_nominal_year") and (" (" .. v("GDP_nominal_year") .. ")") or ""), true)
	row("Gini" .. (v("Gini_year") and (" (" .. v("Gini_year") .. ")") or ""), v("Gini"), true)
	row("HDI" .. (v("HDI_year") and (" (" .. v("HDI_year") .. ")") or ""), v("HDI"), not v("Gini"))
	row("Currency", v("currency") and (v("currency") .. (v("currency_code") and (" (" .. v("currency_code") .. ")") or "")), true)
	local zone = v("utc_offset")
		zone = "Zone " .. zone .. (v("time_zone") and (" (" .. v("time_zone") .. ")") or "")
	row("Drives on", v("drives_on"), not zone)
	row("Calling code", v("calling_code"), false)
	if v("culture_zone") or v("tier") or v("status") or v("continent") then
		row("Continent", v("continent"), false, true)
		row("Culture zone", v("culture_zone") and (v("culture_zone") .. (v("culture_twist") and ("<br /><small>" .. v("culture_twist") .. "</small>") or "")), false, true)
		row("People", v("people"), false, true)
		row("Tier", v("tier"), false, true)
		row("Status", v("status"), false, true)
