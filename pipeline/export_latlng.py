"""Export project coordinates from the Magicbricks crawl as a flat CSV. No OSM, OCR or build step needed.

usage: python mb_crawl.py list <city> && python mb_crawl.py projects <city>
       python export_latlng.py <city>   -> out/<city>/<city>-latlng.csv

Every crawled project gets one row. `coord_status` says whether the pin can be trusted at face value:
  ok              a coordinate inside the city's sanity box (`bounds` in data/cities.json, else `bbox`)
  missing         the portal gave no coordinate
  outside_bounds  a coordinate, but outside the city's sanity box (a stray or wrong pin)
`shared_pin` is how many OTHER "ok" projects sit on exactly the same coordinate. A shared pin can be one
project's phases listed separately, or a default pin for the locality: check these before relying on them.
Coordinates are what the portal lists, not surveyed positions.
"""
import csv
import json
import pathlib
import sys
import urllib.parse
from collections import Counter

ROOT = pathlib.Path(__file__).parent
FIELDS = ["mb_id", "name", "developer", "locality", "pincode", "status", "possession", "rera_id",
          "lat", "lng", "coord_status", "shared_pin", "magicbricks_url", "google_maps_url"]


def status_of(p, box):
    lat, lng = p.get("lat"), p.get("lng")
    if not lat or not lng:
        return "missing"
    south, west, north, east = box
    return "ok" if south < lat < north and west < lng < east else "outside_bounds"


def rows_for(projects, box):
    """One dict per project, in crawl order."""
    status = [status_of(p, box) for p in projects]
    pins = Counter((p["lat"], p["lng"]) for p, st in zip(projects, status) if st == "ok")
    rows = []
    for p, st in zip(projects, status):
        has_pin = st != "missing"
        rows.append({
            "mb_id": p.get("mb_id"), "name": p.get("name"), "developer": p.get("developer"),
            "locality": p.get("locality"), "pincode": p.get("pincode"), "status": p.get("status"),
            "possession": p.get("possession"), "rera_id": p.get("rera_id"),
            "lat": p["lat"] if has_pin else "", "lng": p["lng"] if has_pin else "",
            "coord_status": st,
            "shared_pin": pins[(p["lat"], p["lng"])] - 1 if st == "ok" else "",
            "magicbricks_url": p.get("url"),
            "google_maps_url": ("https://www.google.com/maps/search/?api=1&query="
                                + urllib.parse.quote(f"{p['lat']},{p['lng']}", safe=",")) if has_pin else "",
        })
    return rows


def main(city):
    cfg = json.loads((ROOT.parent / "data" / "cities.json").read_text())[city]
    box = cfg.get("bounds") or cfg["bbox"]
    src = ROOT / "out" / city / "mb_projects.json"
    projects = json.loads(src.read_text())
    rows = rows_for(projects, box)
    dst = ROOT / "out" / city / f"{city}-latlng.csv"
    with dst.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    by = Counter(r["coord_status"] for r in rows)
    shared = sum(1 for r in rows if r["shared_pin"] not in ("", 0))
    print(f"{city}: {len(rows)} projects -> {dst}")
    print("  coord_status:", dict(by))
    print(f"  on a pin shared with another project: {shared}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
