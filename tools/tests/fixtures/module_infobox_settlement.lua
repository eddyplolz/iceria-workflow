-- Trimmed from the live Module:Infobox settlement: only the lines that read a field.
	local function v(...)
	local name = v("name") or mw.title.getCurrentTitle().text
	if v("official_name") and v("official_name") ~= name then
		top:tag("div"):addClass("ib-long"):wikitext(v("official_name"))
	if v("native_name") then
		top:tag("div"):addClass("ib-native"):wikitext("''" .. v("native_name") .. "''"
			.. (v("native_name_lang") and (" (" .. v("native_name_lang") .. ")") or ""))
	if v("other_name") then
		top:tag("div"):addClass("ib-native"):wikitext(v("other_name"))
	if v("settlement_type", "type") then
		top:tag("div"):addClass("ib-long"):wikitext(v("settlement_type", "type"))
	local skyline = v("image_skyline", "image")
		center("[[File:" .. skyline .. "|250px|" .. (v("image_alt") or v("image_caption") or name) .. "]]"
			.. caption(v("image_caption")))
	local seal = v("image_seal", "image_shield")
	if v("image_flag") or seal then
		if v("image_flag") then
			imgs:tag("td"):wikitext("[[File:" .. v("image_flag") .. "|100px|border|Flag]]")
			local kind = v("seal_type") or (v("image_seal") and "Seal" or "Coat of arms")
	if v("nickname") then
		center("'''Nickname:''' ''" .. v("nickname") .. "''")
	if v("motto") then
		center("'''Motto:''' ''" .. v("motto") .. "''")
	if v("image_map") then
		center("[[File:" .. v("image_map") .. "|250px|" .. (v("map_caption") or "Map") .. "]]"
			.. caption(v("map_caption")))
	row(v("subdivision_type") or "Country", v("subdivision_name", "country"), true)
	row(v("subdivision_type1") or "Region", v("subdivision_name1", "region"))
	row(v("subdivision_type2") or "Province", v("subdivision_name2", "province"))
	row(v("subdivision_type3") or "Subdivision", v("subdivision_name3"))
	if v("established_date1") then
		heading(v("established_title") or "History")
			row(v("established_title" .. i) or "Event", v("established_date" .. i), false, true)
		row(v("established_title") or "Founded", v("established_date", "founded"), true)
	row("Founded by", v("founder"), true)
	row("Named for", v("named_for"), not v("founder"))
	local leader1 = v("leader_name", "leader_name1", "mayor")
	if v("government_type") or leader1 then
		row("Type", v("government_type"), false, true)
		row(v("leader_title", "leader_title1") or "Mayor", leader1, false, true)
			row(v("leader_title" .. i) or "Leader", v("leader_name" .. i), false, true)
	local area_n = number(v("area_total_km2"))
	local area = area_n and (fmt(area_n, area_n < 10 and 1 or 0) .. " km²") or v("area")
	if area or v("area_land_km2") then
		local land = number(v("area_land_km2"))
	local elev_n = number(v("elevation_m"))
	row("Elevation", elev_n and (fmt(elev_n) .. " m") or v("elevation"), true)
	local pop_text = v("population_total", "population")
	if pop_text or v("population_metro") then
		local year = v("population_as_of", "population_year")
		local density = number(v("population_density_km2"))
		local metro = number(v("population_metro"))
		row("Metro", metro and fmt(metro) or v("population_metro"), false, true)
	row("Demonym", v("population_demonym", "demonym"), true)
	local zone = v("utc_offset", "timezone")
		zone = "Zone " .. zone .. ((v("utc_offset") and v("timezone")) and (" (" .. v("timezone") .. ")") or "")
	row("Postal code", v("postal_code"), not zone)
	row("Area code", v("area_code"), not (zone or v("postal_code")))
	row("Website", v("website"), true)
