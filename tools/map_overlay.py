"""Draw your nation's places and routes over the canon map, inside your own land.

    python tools/map_overlay.py notes/vell-map.json

The plan file names your nation and lists what to draw, each point as [latitude, longitude]:

    {"nation": "Vell",
     "places": [{"name": "Orra", "at": [20.5, -61.2]}],
     "routes": [{"name": "Coast road", "via": [[20.5, -61.2], [24.0, -58.9]]},
                {"name": "Ferry", "kind": "sea", "via": [[24.0, -58.9], [22.1, -55.0]]}],
     "labels": [{"text": "Dorsal foothills", "at": [23.0, -60.0]}]}

Every place, label and land route stays inside your nation's land on canon/claims.json. A sea route
starts and ends there and may cross open water between, never another nation's land. Anything else
is refused, naming the point, and nothing is written: a map that moves a border is not canon. The
SVG lands beside the plan, cropped to your land, and opens in any browser. It reads no wiki.
"""

import argparse
import bisect
import json
import sys
from html import escape
from pathlib import Path

import kit_python  # noqa: F401  stops on Python < 3.10

KIT_ROOT = Path(__file__).resolve().parent.parent
BASE = Path("maps") / "iceria-base.png"


class Refused(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


class Claims:
    """Who holds each cell of the world grid: canon/claims.json as rows of [y, x0, x1] runs."""

    def __init__(self, grid: list[int], runs: dict[str, list[list[int]]]):
        self.w, self.h = grid
        self.runs = runs
        self._rows: dict[int, list[tuple[int, int, str]]] = {}
        for nation, spans in runs.items():
            for y, x0, x1 in spans:
                self._rows.setdefault(y, []).append((x0, x1, nation))
        for row in self._rows.values():
            row.sort()

    @classmethod
    def load(cls, kit: Path) -> "Claims":
        data = json.loads((kit / "canon" / "claims.json").read_text(encoding="utf-8"))
        return cls(data["grid"], data["runs"])

    def cell(self, lat: float, lon: float) -> tuple[float, float]:
        """Grid position of a point on the map's equirectangular projection."""
        return (lon + 180) / 360 * self.w, (90 - lat) / 180 * self.h

    def owner(self, lat: float, lon: float) -> str | None:
        x, y = self.cell(lat, lon)
        cx, cy = min(int(x), self.w - 1), min(int(y), self.h - 1)
        row = self._rows.get(cy, [])
        i = bisect.bisect_right(row, (cx, self.w, "")) - 1
        return row[i][2] if i >= 0 and row[i][0] <= cx <= row[i][1] else None

    def box(self, nation: str) -> tuple[int, int, int, int]:
        """(x0, y0, x1, y1) of the nation's land, ends exclusive."""
        spans = self.runs[nation]
        return (
            min(s[1] for s in spans),
            min(s[0] for s in spans),
            max(s[2] for s in spans) + 1,
            max(s[0] for s in spans) + 1,
        )


def _point(at, what: str) -> tuple[float, float]:
    try:
        lat, lon = (float(v) for v in at)
    except (TypeError, ValueError):
        lat = lon = None
    if lat is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise Refused([f"{what} {at!r} is not a latitude and longitude"])
    return lat, lon


def _where(owner: str | None, nation: str) -> str:
    return f"is in {owner}'s land, not {nation}'s" if owner else f"is outside {nation}'s land"


def _show(lat: float, lon: float) -> str:
    return f"({lat:g}, {lon:g})"


def _check_route(route: dict, nation: str, claims: Claims) -> list[str]:
    name, sea = route["name"], route.get("kind") == "sea"
    via = [_point(p, f"{name} point") for p in route["via"]]
    problems = []
    for i, (lat, lon) in enumerate(via):
        owner = claims.owner(lat, lon)
        end = i in (0, len(via) - 1)
        if owner != nation and (owner or not sea or end):
            problems.append(f"{name} {_show(lat, lon)} {_where(owner, nation)}")
    # Between points, sample the line about twice per grid cell so it cannot jump a neighbor.
    for (a, b), (c, d) in zip(via, via[1:], strict=False):
        (x0, y0), (x1, y1) = claims.cell(a, b), claims.cell(c, d)
        steps = max(2, int(2 * max(abs(x1 - x0), abs(y1 - y0))))
        for k in range(1, steps):
            lat, lon = a + (c - a) * k / steps, b + (d - b) * k / steps
            owner = claims.owner(lat, lon)
            if owner != nation and (owner or not sea):
                problems.append(
                    f"{name} between {_show(a, b)} and {_show(c, d)} {_where(owner, nation)}"
                )
                break
    return problems


def check(plan: dict, claims: Claims) -> list[str]:
    """Every reason the plan cannot be drawn, in plan order; empty when it can."""
    nation = plan["nation"]
    if nation not in claims.runs:
        return [f"{nation} has no land in canon/claims.json; use your nation's name as it is there"]
    problems = []
    for kind, key in (("places", "name"), ("labels", "text")):
        for item in plan.get(kind, []):
            lat, lon = _point(item["at"], item[key])
            owner = claims.owner(lat, lon)
            if owner != nation:
                problems.append(f"{item[key]} {_show(lat, lon)} {_where(owner, nation)}")
    for route in plan.get("routes", []):
        problems += _check_route(route, nation, claims)
    return problems


def draw(plan: dict, claims: Claims, base_href: str) -> str:
    """The SVG text, or Refused naming every point that falls outside the nation's land."""
    problems = check(plan, claims)
    if problems:
        raise Refused(problems)
    x0, y0, x1, y1 = claims.box(plan["nation"])
    pad = max(x1 - x0, y1 - y0) / 4
    vx, vy, vw, vh = x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    r, font, stroke = vw / 200, vw / 60, vw / 400

    def xy(at) -> tuple[float, float]:
        return claims.cell(*_point(at, "point"))

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:g} {vy:g} {vw:g} {vh:g}">',
        f"<title>{escape(plan['nation'])}</title>",
        f'<image href="{escape(base_href)}" x="0" y="0" width="{claims.w}" height="{claims.h}" '
        'preserveAspectRatio="none"/>',
    ]
    for route in plan.get("routes", []):
        dash = f' stroke-dasharray="{stroke * 4:g}"' if route.get("kind") == "sea" else ""
        points = " ".join("{:.3f},{:.3f}".format(*xy(p)) for p in route["via"])
        out.append(
            f'<polyline points="{points}" fill="none" stroke="#7a1f1f" '
            f'stroke-width="{stroke:g}"{dash}><title>{escape(route["name"])}</title></polyline>'
        )
    text = f'font-family="Georgia, serif" font-size="{font:g}"'
    for place in plan.get("places", []):
        x, y = xy(place["at"])
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r:g}" fill="#111"/>')
        out.append(
            f'<text x="{x + 1.5 * r:.3f}" y="{y + r:.3f}" {text}>{escape(place["name"])}</text>'
        )
    for label in plan.get("labels", []):
        x, y = xy(label["at"])
        out.append(
            f'<text x="{x:.3f}" y="{y:.3f}" {text} font-style="italic" text-anchor="middle">'
            f"{escape(label['text'])}</text>"
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("plan", type=Path)
    ap.add_argument("--root", type=Path, default=KIT_ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    try:
        svg = draw(plan, Claims.load(args.root), (args.root / BASE).resolve().as_uri())
    except Refused as e:
        for p in e.problems:
            print(f"refused: {p}", file=sys.stderr)
        print(
            "Nothing was written. Move those points inside your land, then run this again.",
            file=sys.stderr,
        )
        return 1
    out = args.plan.with_suffix(".svg")
    out.write_text(svg, encoding="utf-8", newline="\n")
    print(f"wrote {out.name}; open it in a browser")
    return 0


if __name__ == "__main__":
    sys.exit(main())
