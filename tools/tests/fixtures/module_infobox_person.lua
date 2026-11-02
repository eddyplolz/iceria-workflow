-- Trimmed from the live Module:Infobox person: only the lines that read a field.
	local function v(...)
	local name = v("name") or mw.title.getCurrentTitle().text
	if v("title") and plain(v("title")) ~= plain(v("office", "office1")) then
		top:tag("div"):addClass("ib-long"):wikitext(v("title"))
	local caption = v("image_caption", "caption")
	if v("image") then
		center("[[File:" .. v("image") .. "|220px|" .. (v("alt") or caption or name) .. "]]"
		local function f(field)
				return v(field, field .. "1")
			return v(field .. n)
		local term = f("term")
		if not term and f("term_start") then
			term = f("term_end") and (f("term_start") .. " to " .. f("term_end")) or ("Since " .. f("term_start"))
		local office = f("office")
		if office and f("order") then
			office = f("order") .. " " .. office
			{ "Monarch", f("monarch") },
			{ "President", f("president") },
			{ "Prime Minister", f("prime_minister") },
			{ "Deputy", f("deputy") },
			{ "Preceded by", f("predecessor") },
			{ "Succeeded by", f("successor") },
	local born = v("birth_date")
	if born or v("birth_place") then
		born = (born or "") .. ((born and v("birth_place")) and "<br />" or "") .. (v("birth_place") or "")
	local died = v("death_date")
	if died or v("death_place") then
		died = (died or "") .. ((died and v("death_place")) and "<br />" or "") .. (v("death_place") or "")
	local parents = (not v("father") and not v("mother")) and v("parents") or nil
		{ "Full name", v("full_name", "birth_name") },
		{ "Resting place", v("resting_place") },
		{ "Nationality", v("nationality", "citizenship") },
		{ "Political party", v("party") },
		{ "Other political affiliations", v("otherparty") },
		{ "House", v("house") },
		{ "Spouse", v("spouse", "spouses") },
		{ "Children", v("children", "issue") },
		{ "Father", v("father") },
		{ "Mother", v("mother") },
		{ "Relatives", v("relatives") },
		{ "Residence", v("residence") },
		{ "Alma mater", v("alma_mater") },
		{ "Occupation", v("occupation") },
		{ "Profession", v("profession") },
		{ "Known for", v("known_for") },
		{ "Religion", v("religion") },
		{ "Signature", v("signature") and ("[[File:" .. v("signature") .. "|128px|Signature of " .. name .. "]]") },
		{ "Allegiance", v("allegiance") },
		{ "Branch", v("branch") },
		{ "Years of service", v("serviceyears", "years_of_service") },
		{ "Rank", v("rank") },
		{ "Unit", v("unit") },
		{ "Commands", v("commands") },
		{ "Battles", v("battles") },
		{ "Awards", v("awards") },
