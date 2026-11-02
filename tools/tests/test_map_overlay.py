"""map_overlay.py: the member's places and routes drawn over the canon map, inside their own land."""

import json

import map_overlay
import pytest

# An 8 x 4 world: Vell holds the two cells west of the meridian in the row north of the equator
# (lat 0 to 45, lon -90 to 0), and Brenn the cell just east of them.
CLAIMS = {"grid": [8, 4], "runs": {"Vell": [[1, 2, 3]], "Brenn": [[1, 4, 4]]}}


def _kit(tmp_path):
    (tmp_path / "canon").mkdir(parents=True)
    (tmp_path / "canon" / "claims.json").write_text(json.dumps(CLAIMS), encoding="utf-8")
    (tmp_path / "maps").mkdir()
    (tmp_path / "maps" / "iceria-base.png").write_bytes(b"\x89PNG fake")
    return tmp_path


def _plan(**kw):
    return {"nation": "Vell", "places": [], "routes": [], **kw}


def test_a_point_is_owned_by_the_nation_whose_cell_it_falls_in(tmp_path):
    claims = map_overlay.Claims.load(_kit(tmp_path))
    assert claims.owner(20, -60) == "Vell"
    assert claims.owner(20, -30) == "Vell"
    assert claims.owner(20, 10) == "Brenn"
    assert claims.owner(-20, -60) is None


def test_places_and_routes_inside_the_nation_draw_and_crop_to_its_land(tmp_path):
    plan = _plan(
        places=[{"name": "Orra", "at": [20, -60]}, {"name": "Tel & Co", "at": [30, -20]}],
        routes=[{"name": "Coast road", "via": [[20, -60], [30, -20]]}],
    )
    svg = map_overlay.draw(plan, map_overlay.Claims.load(_kit(tmp_path)), "iceria-base.png")
    assert svg.count("<circle") == 2 and svg.count("<polyline") == 1
    assert "Tel &amp; Co" in svg  # names are escaped, so a name can never break the file
    assert 'href="iceria-base.png"' in svg
    # Vell spans x 2..4 and y 1..2 of the 8 x 4 grid; the view is that box with a margin.
    assert 'viewBox="1.5 0.5 3 2"' in svg


def test_a_place_outside_the_nations_land_is_refused_with_whose_land_it_is(tmp_path):
    plan = _plan(places=[{"name": "Far", "at": [20, 10]}, {"name": "Wet", "at": [-20, -60]}])
    with pytest.raises(map_overlay.Refused) as e:
        map_overlay.draw(plan, map_overlay.Claims.load(_kit(tmp_path)), "base.png")
    assert e.value.problems == [
        "Far (20, 10) is in Brenn's land, not Vell's",
        "Wet (-20, -60) is outside Vell's land",
    ]


def test_a_sea_route_may_cross_open_water_but_never_anothers_land(tmp_path):
    claims = map_overlay.Claims.load(_kit(tmp_path))
    sea = {"name": "Ferry", "kind": "sea", "via": [[20, -60], [-20, -60], [20, -20]]}
    assert "<polyline" in map_overlay.draw(_plan(routes=[sea]), claims, "b.png")
    sea["via"][1] = [20, 10]
    with pytest.raises(map_overlay.Refused, match="Brenn's land"):
        map_overlay.draw(_plan(routes=[sea]), claims, "b.png")
    sea["via"] = [[-20, -60], [20, -20]]
    with pytest.raises(map_overlay.Refused, match="outside Vell's land"):
        map_overlay.draw(_plan(routes=[sea]), claims, "b.png")


def test_a_coordinate_off_the_globe_or_an_unknown_nation_is_refused(tmp_path):
    claims = map_overlay.Claims.load(_kit(tmp_path))
    with pytest.raises(map_overlay.Refused, match="not a latitude and longitude"):
        map_overlay.draw(_plan(places=[{"name": "X", "at": [95, 0]}]), claims, "b.png")
    with pytest.raises(map_overlay.Refused, match="Valmora has no land"):
        map_overlay.draw(_plan(nation="Valmora"), claims, "b.png")


def test_main_writes_the_svg_beside_the_plan_and_copies_nothing(tmp_path, capsys):
    kit = _kit(tmp_path / "kit")
    plan = tmp_path / "vell-map.json"
    plan.write_text(json.dumps(_plan(places=[{"name": "Orra", "at": [20, -60]}])), encoding="utf-8")
    assert map_overlay.main([str(plan), "--root", str(kit)]) == 0
    svg = (tmp_path / "vell-map.svg").read_text(encoding="utf-8")
    assert "Orra" in svg and (kit / "maps" / "iceria-base.png").as_uri() in svg
    assert "vell-map.svg" in capsys.readouterr().out


def test_main_refuses_and_writes_nothing(tmp_path, capsys):
    kit = _kit(tmp_path / "kit")
    plan = tmp_path / "vell-map.json"
    plan.write_text(json.dumps(_plan(places=[{"name": "Far", "at": [20, 10]}])), encoding="utf-8")
    assert map_overlay.main([str(plan), "--root", str(kit)]) == 1
    assert not (tmp_path / "vell-map.svg").exists()
    assert "Brenn's land" in capsys.readouterr().err


def test_a_route_whose_ends_are_home_may_not_cross_anothers_land_between_them():
    # Vell also holds an exclave at x 6; the straight line from x 2 to it passes Brenn at x 4.
    claims = map_overlay.Claims([8, 4], {"Vell": [[1, 2, 3], [1, 6, 6]], "Brenn": [[1, 4, 4]]})
    road = {"name": "Long road", "via": [[20, -60], [20, 100]]}
    with pytest.raises(map_overlay.Refused) as e:
        map_overlay.draw(_plan(routes=[road]), claims, "b.png")
    assert e.value.problems == [
        "Long road between (20, -60) and (20, 100) is in Brenn's land, not Vell's"
    ]


def test_a_plan_that_is_not_there_or_is_not_json_is_named_with_how_to_fix_it(tmp_path, capsys):
    kit = _kit(tmp_path / "kit")
    plan = tmp_path / "vell-map.json"
    assert map_overlay.main([str(plan), "--root", str(kit)]) == 2
    assert "no file at" in capsys.readouterr().err
    plan.write_text('{"nation": "Vell",\n "places": [}', encoding="utf-8")
    assert map_overlay.main([str(plan), "--root", str(kit)]) == 2
    assert "not valid JSON at line 2" in capsys.readouterr().err
    assert not (tmp_path / "vell-map.svg").exists()
