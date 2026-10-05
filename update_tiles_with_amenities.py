import json
import math
import struct
from pathlib import Path
from collections import defaultdict, Counter

CATS = [
    "Groceries & Essentials",   # 0
    "Healthcare",               # 1
    "Education",                # 2
    "Parks & Recreation",       # 3
    "Dining & Cafés",           # 4
    "Rest Benches",             # 5
    "Transit & Stations",       # 6
    "Civic & Financial",        # 7
    "Culture & Worship",        # 8
    "Sanitation & Water"        # 9
]

GROCERY_SHOPS = {
    "supermarket", "convenience", "greengrocer", "bakery", "butcher", "general",
    "department_store", "dairy", "kiosk", "confectionery", "pastry", "seafood",
    "deli", "variety_store", "market", "grocery", "spices", "tea", "coffee", "mall"
}
HEALTH_AMENITIES = {
    "pharmacy", "doctors", "clinic", "hospital", "dentist", "veterinary", "nursing_home", "health_post"
}
HEALTH_SHOPS = {"chemist", "optician", "medical_supply"}
EDU_AMENITIES = {
    "school", "kindergarten", "library", "college", "university", "music_school",
    "language_school", "tuition", "research_institute", "training"
}
PARKS_LEISURE = {
    "park", "playground", "garden", "pitch", "sports_centre", "fitness_centre",
    "swimming_pool", "stadium", "nature_reserve", "track", "recreation_ground"
}
EATING_AMENITIES = {
    "cafe", "restaurant", "pub", "bar", "fast_food", "food_court", "ice_cream", "street_vendor"
}
CIVIC_AMENITIES = {
    "bank", "atm", "post_office", "police", "fire_station", "townhall", "courthouse",
    "social_facility", "community_centre", "bureau_de_change"
}
CULTURE_AMENITIES = {"place_of_worship", "theatre", "cinema", "arts_centre"}
CULTURE_TOURISMS = {"museum", "gallery", "attraction", "viewpoint"}
CULTURE_HISTORIC = {"monument", "memorial", "heritage", "archaeological_site"}
SANITATION_AMENITIES = {"drinking_water", "toilets", "water_point"}

WHEELCHAIR_MAP = {"yes": 1, "limited": 2, "no": 3}

def classify(tags):
    a = tags.get("amenity")
    s = tags.get("shop")
    l = tags.get("leisure")
    r = tags.get("railway")
    h = tags.get("highway")
    t = tags.get("tourism")
    hist = tags.get("historic")

    wc = 0
    if tags.get("wheelchair") in WHEELCHAIR_MAP:
        wc = WHEELCHAIR_MAP[tags.get("wheelchair")]

    # 6: Transit
    if r in ("station", "tram_stop", "subway_entrance", "halt") or a in ("ferry_terminal", "bus_station") or h == "bus_stop":
        return 6, wc
    # 5: Benches
    if a == "bench":
        return 5, 0
    # 0: Groceries / Food market
    if a == "marketplace" or s in GROCERY_SHOPS:
        return 0, wc
    # 1: Health
    if a in HEALTH_AMENITIES or s in HEALTH_SHOPS:
        return 1, wc
    # 2: Education
    if a in EDU_AMENITIES:
        return 2, wc
    # 3: Parks & Sports
    if l in PARKS_LEISURE or a == "gym":
        return 3, wc
    # 4: Dining & Cafes
    if a in EATING_AMENITIES:
        return 4, wc
    # 7: Civic & Financial
    if a in CIVIC_AMENITIES:
        return 7, wc
    # 8: Culture & Worship
    if a in CULTURE_AMENITIES or t in CULTURE_TOURISMS or hist in CULTURE_HISTORIC:
        return 8, wc
    # 9: Water & Sanitation
    if a in SANITATION_AMENITIES:
        return 9, wc

    return None

def main():
    meta_path = Path("data/kolkata/meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Save backup of meta.json
    with open("data/kolkata/meta.json.bak", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    t_info = meta["tiles"]
    lon0 = t_info["lon0"]
    lat0 = t_info["lat0"]
    dlon = t_info["dlon"]
    dlat = t_info["dlat"]

    with open("raw_kolkata_osm_pois.json", "r", encoding="utf-8") as f:
        raw_elements = json.load(f)

    pts = []
    seen = set()
    cat_counts = Counter()

    for el in raw_elements:
        tags = el.get("tags", {})
        res = classify(tags)
        if res is None:
            continue
        cat_id, wc = res

        # Coordinate extraction
        if "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el and "lat" in el["center"] and "lon" in el["center"]:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue

        lat_r, lon_r = round(lat, 5), round(lon, 5)
        # Deduplicate identical category at identical rounded coordinate
        dedup_key = (lon_r, lat_r, cat_id)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        pts.append([lon_r, lat_r, cat_id, wc])
        cat_counts[cat_id] += 1

    print(f"Total unique POIs prepared: {len(pts)}")
    for i, name in enumerate(CATS):
        print(f"  [{i}] {name}: {cat_counts[i]}")

    # Group POIs by tile key
    poi_by_tile = defaultdict(list)
    for p in pts:
        ix = int(math.floor((p[0] - lon0) / dlon))
        iy = int(math.floor((p[1] - lat0) / dlat))
        key = f"{ix}_{iy}"
        poi_by_tile[key].append(p)

    tiles_dir = Path("data/kolkata/t")
    updated_tiles = 0

    for tile_file in tiles_dir.glob("*.bin"):
        key = tile_file.stem
        with open(tile_file, "rb") as f:
            buf = f.read()
        if len(buf) < 20:
            continue

        h = struct.unpack("<5I", buf[:20])
        version, nN, nE, nS, oldPoiLen = h
        if version != 2:
            continue

        poiOff = 20 + 4 * nN + 8 * nN + 4 * nE + 4 * nE + 4 * nE + 4 * (nE + 1) + 8 * nS
        graph_bytes = buf[:poiOff]

        # New POIs for this tile
        tile_pois = poi_by_tile.get(key, [])
        new_poi_bytes = json.dumps(tile_pois, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        new_poi_len = len(new_poi_bytes)

        # Update header at bytes 16..20 with new_poi_len
        new_header = struct.pack("<5I", version, nN, nE, nS, new_poi_len)
        updated_data = new_header + graph_bytes[20:] + new_poi_bytes

        with open(tile_file, "wb") as f:
            f.write(updated_data)
        updated_tiles += 1

    # Check if there are tiles with POIs that don't have a file yet
    for key, tile_pois in poi_by_tile.items():
        tile_file = tiles_dir / f"{key}.bin"
        if not tile_file.exists():
            new_poi_bytes = json.dumps(tile_pois, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            # Empty graph tile: nN=0, nE=0, nS=0
            header = struct.pack("<5I", 2, 0, 0, 0, len(new_poi_bytes))
            # empty sst has 1 element
            lstart = struct.pack("<I", 0)
            with open(tile_file, "wb") as f:
                f.write(header + lstart + new_poi_bytes)
            if key not in t_info["list"]:
                t_info["list"].append(key)
            updated_tiles += 1

    # Update meta.json
    meta["cats"] = CATS
    meta["pois"] = len(pts)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)

    print(f"Successfully updated {updated_tiles} tiles!")
    print(f"Updated data/kolkata/meta.json with {len(CATS)} categories and {len(pts)} total POIs.")

if __name__ == "__main__":
    main()
