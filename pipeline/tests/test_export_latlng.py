import json
import pathlib

import export_latlng as ex

BOX = (18.30, 73.60, 18.75, 74.15)
CITIES = json.loads((pathlib.Path(__file__).parents[2] / "data" / "cities.json").read_text())


def P(i, lat, lng, **kw):
    return {"mb_id": str(i), "name": f"P{i}", "lat": lat, "lng": lng, "url": f"https://x/{i}", **kw}


def test_status_and_shared_pins():
    rows = ex.rows_for([
        P(1, 18.52, 73.85), P(2, 18.52, 73.85), P(3, 18.60, 73.80),   # 1 and 2 share a pin
        P(4, None, None), P(5, 28.4, 77.0),                            # no pin / pin in another city
    ], BOX)
    assert [r["coord_status"] for r in rows] == ["ok", "ok", "ok", "missing", "outside_bounds"]
    assert [r["shared_pin"] for r in rows] == [1, 1, 0, "", ""]
    assert rows[3]["lat"] == "" and rows[3]["google_maps_url"] == ""
    assert rows[0]["google_maps_url"].endswith("query=18.52,73.85")


def test_outside_pin_keeps_its_coordinates_for_inspection():
    row = ex.rows_for([P(1, 28.4, 77.0)], BOX)[0]
    assert (row["lat"], row["lng"]) == (28.4, 77.0)


def test_gurgaon_sanity_box_is_unchanged():
    # build_city used to hard-code this box; it now comes from cities.json, so it must stay identical
    assert CITIES["gurgaon"]["bounds"] == [28.2, 76.7, 28.7, 77.3]


def test_every_city_has_a_usable_box():
    for cfg in CITIES.values():
        s, w, n, e = cfg.get("bounds") or cfg["bbox"]
        assert s < n and w < e
