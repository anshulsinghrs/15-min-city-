import json
import math
import struct
import re
from pathlib import Path
from collections import defaultdict, Counter

CATS = [
    "Groceries & Essentials",        # 0
    "Healthcare",                    # 1
    "Education",                     # 2
    "Parks & Recreation",            # 3
    "Dining & Cafés",                # 4
    "Rest Benches",                  # 5
    "Metro Stations",                # 6
    "Civic & Financial",             # 7
    "Culture & Worship",             # 8
    "Sanitation & Water",            # 9
    "Local Bus, Tram & Ferry Stops", # 10
    "Suburban Railway Stations",     # 11
    "Bus Terminals & Stations"       # 12 (DEDICATED BUS STATIONS!)
]

GROCERY_SHOPS = {
    "supermarket", "convenience", "greengrocer", "bakery", "butcher", "general",
    "department_store", "dairy", "kiosk", "confectionery", "pastry", "seafood",
    "deli", "variety_store", "market", "grocery", "spices", "tea", "coffee", "mall"
}
HEALTH_AMENITIES = {"pharmacy", "doctors", "clinic", "hospital", "dentist", "veterinary", "nursing_home", "health_post"}
HEALTH_SHOPS = {"chemist", "optician", "medical_supply"}
EDU_AMENITIES = {"school", "kindergarten", "library", "college", "university", "music_school", "language_school", "tuition", "research_institute", "training"}
PARKS_LEISURE = {"park", "playground", "garden", "pitch", "sports_centre", "fitness_centre", "swimming_pool", "stadium", "nature_reserve", "track", "recreation_ground"}
EATING_AMENITIES = {"cafe", "restaurant", "pub", "bar", "fast_food", "food_court", "ice_cream", "street_vendor"}
CIVIC_AMENITIES = {"bank", "atm", "post_office", "police", "fire_station", "townhall", "courthouse", "social_facility", "community_centre", "bureau_de_change"}
CULTURE_AMENITIES = {"place_of_worship", "theatre", "cinema", "arts_centre"}
CULTURE_TOURISMS = {"museum", "gallery", "attraction", "viewpoint"}
CULTURE_HISTORIC = {"monument", "memorial", "heritage", "archaeological_site"}
SANITATION_AMENITIES = {"drinking_water", "toilets", "water_point"}

WHEELCHAIR_MAP = {"yes": 1, "limited": 2, "no": 3}

KNOWN_METRO_NAMES = {
    'dakshineswar', 'baranagar', 'noapara', 'dum dum', 'dum dum cantt.', 'dum dum cantonment',
    'belgachia', 'shyambazar', 'shobhabazar sutee', 'shobhabazar sutanuti', 'girish park',
    'mahatma gandhi road', 'central', 'chandni chowk', 'esplanade', 'park street', 'maidan',
    'netaji bhavan', 'jatin das park', 'kalighat', 'rabindra sarobar', 'mahanayak uttam kumar',
    'netaji', 'masterda surya sen', 'gitanjali', 'kavi nazrul', 'shahid khudiram', 'kavi subhash',
    'howrah maidan', 'howrah metro', 'sealdah metro', 'phoolbagan', 'salt lake stadium',
    'bengal chemical', 'city centre', 'central park', 'karunamoyee', 'salt lake sector v',
    'joka', 'thakurpukur', 'sakherbazar', 'sokher bazar', 'behala chourasta', 'behala bazar',
    'taratala', 'majerhat metro', 'mominpur', 'khidirpur metro', 'victoria',
    'kavi sukanta', 'kavi sukanta (kalikapur)', 'hemanta mukhopadhyay', 'hemanta mukherjee (ruby)',
    'vip bazar', 'ritwik ghatak', 'barun sengupta', 'beliaghata', 'gurudakshina', 'chinar park'
}

def clean_station_name(raw_name):
    if not raw_name:
        return "Metro Station"
    name = re.sub(r'\s*Metro Station\s*', '', raw_name, flags=re.I)
    name = re.sub(r'\s*Metro\s*', '', name, flags=re.I).strip()
    return name if name else raw_name.strip()

def clean_train_station_name(raw_name):
    if not raw_name or raw_name.strip().lower() in ("railway station", "station", "train station"):
        return None
    name = raw_name.strip()
    low = name.lower()
    if low == "sealdah":
        return "Sealdah Railway Station"
    if low in ("howrah junction", "howrah"):
        return "Howrah Junction (HWH)"
    if low in ("kolkata", "kolkata railway station"):
        return "Kolkata Chitpur Terminal"
    if low == "santragachi junction":
        return "Santragachi Junction (SRC)"
    if low in ("dum dum junction", "dum dum"):
        return "Dum Dum Junction (DDJ)"
    if low in ("tollygunge rail station", "tollygunge"):
        return "Tollygunge Suburban Station"
    if low in ("shalimar", "shalimar station"):
        return "Shalimar Railway Station"
    if low in ("ballygunge junction", "ballygunge"):
        return "Ballygunge Junction"
    if low in ("bidhannagar road", "bidhan nagar road"):
        return "Bidhannagar Road"
    if low in ("majherhat", "majherhat station"):
        return "Majherhat Railway Station"
    if low in ("jadavpur", "jadavpur station"):
        return "Jadavpur Railway Station"
    return name

def clean_bus_station_name(raw_name):
    if not raw_name:
        return None
    name = raw_name.strip()
    name = re.sub(r'[\u200e\u200f\u200b\u200c\u200d]', '', name).strip()
    low = name.lower()
    if low in ('unnamed', 'none', 'bus stop', 'bus stopage', 'bus station', 'subway to ctc bus stand and road crossing', 'gujarat co-operative milk marketing federation'):
        return None
    if low == 'esplanade':
        return 'Esplanade Bus Terminus'
    if low == 'babughat':
        return 'Babughat Bus Stand'
    if low == 'howrah':
        return 'Howrah Bus Station'
    return name

def classify_feature(tags):
    a = tags.get("amenity")
    s = tags.get("shop")
    l = tags.get("leisure")
    r = tags.get("railway")
    h = tags.get("highway")
    t = tags.get("tourism")
    hist = tags.get("historic")
    station = tags.get("station")
    subway = tags.get("subway")
    network = tags.get("network", "")
    operator = tags.get("operator", "")
    pt = tags.get("public_transport")
    name = tags.get("name") or tags.get("name:en") or tags.get("name:bn") or ""

    wc = 0
    if tags.get("wheelchair") in WHEELCHAIR_MAP:
        wc = WHEELCHAIR_MAP[tags.get("wheelchair")]

    # 1. Metro Railway Station or Subway Entrance (Category 6)
    is_metro = (
        station == "subway" or 
        subway == "yes" or 
        r == "subway_entrance" or
        "metro" in name.lower() or
        "metro railway" in network.lower() or 
        "kolkata metro" in network.lower() or
        "metro railway" in operator.lower()
    )
    if is_metro:
        clean_name = clean_station_name(name)
        return 6, wc, clean_name

    # 2. Indian Railways / Suburban Railway Stations (Category 11)
    is_train = (
        (r in ("station", "halt") and station != "subway" and subway != "yes") or
        tags.get("building") == "train_station" or
        (tags.get("train") == "yes" and (r is not None or station is not None))
    )
    norm = name.lower().replace(' railway station', '').replace(' station', '').strip()
    if is_train and norm not in KNOWN_METRO_NAMES and not is_metro:
        if "goods" in name.lower():
            return None
        st_name = clean_train_station_name(name)
        if st_name:
            if any(term in st_name.lower() for term in ['howrah junction', 'sealdah']):
                wc = 1
            return 11, wc, st_name

    # 3. Dedicated Bus Stations, Terminals & Depots (Category 12)
    name_low = name.lower()
    is_bus_station = (
        a == "bus_station" or
        (pt == "station" and tags.get("bus") == "yes") or
        (h == "bus_stop" and tags.get("bus_station") == "yes") or
        any(w in name_low for w in ["bus terminus", "bus terminal", "bus depot", "bus stand", "mini bus terminus", "mini bus stand", "cstc depot", "wbtc bus terminal"])
    )
    if is_bus_station:
        clean_b_name = clean_bus_station_name(name)
        if clean_b_name:
            return 12, wc, clean_b_name

    # 4. Local Transit (Local roadside bus stops, Tram stops, Ferry Ghats) (Category 10)
    if r in ("tram_stop",) or a in ("ferry_terminal",) or h == "bus_stop" or "ghat" in name.lower():
        return 10, wc, name.strip()

    # 5. Rest Benches (Category 5)
    if a == "bench":
        return 5, 0, ""

    # 6. Groceries & Essentials (Category 0)
    if a == "marketplace" or s in GROCERY_SHOPS:
        return 0, wc, name.strip()

    # 7. Healthcare (Category 1)
    if a in HEALTH_AMENITIES or s in HEALTH_SHOPS:
        return 1, wc, name.strip()

    # 8. Education (Category 2)
    if a in EDU_AMENITIES:
        return 2, wc, name.strip()

    # 9. Parks & Sports (Category 3)
    if l in PARKS_LEISURE or a == "gym":
        return 3, wc, name.strip()

    # 10. Dining & Cafes (Category 4)
    if a in EATING_AMENITIES:
        return 4, wc, name.strip()

    # 11. Civic & Financial (Category 7)
    if a in CIVIC_AMENITIES:
        return 7, wc, name.strip()

    # 12. Culture & Worship (Category 8)
    if a in CULTURE_AMENITIES or t in CULTURE_TOURISMS or hist in CULTURE_HISTORIC:
        return 8, wc, name.strip()

    # 13. Sanitation & Water (Category 9)
    if a in SANITATION_AMENITIES:
        return 9, wc, name.strip()

    return None

def main():
    meta_path = Path("data/kolkata/meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    t_info = meta["tiles"]
    lon0 = t_info["lon0"]
    lat0 = t_info["lat0"]
    dlon = t_info["dlon"]
    dlat = t_info["dlat"]

    all_elements = []
    if Path("raw_kolkata_osm_pois.json").exists():
        with open("raw_kolkata_osm_pois.json", "r", encoding="utf-8") as f:
            all_elements.extend(json.load(f))
    if Path("kolkata_metro_elements.json").exists():
        with open("kolkata_metro_elements.json", "r", encoding="utf-8") as f:
            all_elements.extend(json.load(f))
    if Path("kolkata_train_elements.json").exists():
        with open("kolkata_train_elements.json", "r", encoding="utf-8") as f:
            all_elements.extend(json.load(f))
    if Path("kolkata_bus_stations.json").exists():
        with open("kolkata_bus_stations.json", "r", encoding="utf-8") as f:
            all_elements.extend(json.load(f))

    print(f"Total raw features to classify: {len(all_elements)}")

    pts = []
    seen = set()
    cat_counts = Counter()
    metro_stations_set = set()
    train_stations_set = set()
    bus_stations_set = set()

    for el in all_elements:
        tags = el.get("tags", {})
        res = classify_feature(tags)
        if res is None:
            continue
        cat_id, wc, name = res

        # Coordinates
        if "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el and "lat" in el["center"] and "lon" in el["center"]:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue

        lat_r, lon_r = round(lat, 5), round(lon, 5)
        dedup_key = (lon_r, lat_r, cat_id)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Store [lon, lat, cat_id, wc, name]
        pts.append([lon_r, lat_r, cat_id, wc, name])
        cat_counts[cat_id] += 1
        if cat_id == 6 and name:
            metro_stations_set.add(name)
        if cat_id == 11 and name:
            train_stations_set.add(name)
        if cat_id == 12 and name:
            bus_stations_set.add(name)

    print(f"Total unique POIs prepared: {len(pts)}")
    for i, name in enumerate(CATS):
        print(f"  [{i:2d}] {name:32}: {cat_counts[i]}")
    print(f"Total distinct Metro Stations/Entrances: {len(metro_stations_set)}")
    print(f"Total distinct Train Stations: {len(train_stations_set)}")
    print(f"Total distinct Bus Stations/Terminals: {len(bus_stations_set)}")

    # Group by tile key
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

        tile_pois = poi_by_tile.get(key, [])
        new_poi_bytes = json.dumps(tile_pois, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        new_poi_len = len(new_poi_bytes)

        new_header = struct.pack("<5I", version, nN, nE, nS, new_poi_len)
        updated_data = new_header + graph_bytes[20:] + new_poi_bytes

        with open(tile_file, "wb") as f:
            f.write(updated_data)
        updated_tiles += 1

    # Check for empty-graph tiles with POIs
    for key, tile_pois in poi_by_tile.items():
        tile_file = tiles_dir / f"{key}.bin"
        if not tile_file.exists():
            new_poi_bytes = json.dumps(tile_pois, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            header = struct.pack("<5I", 2, 0, 0, 0, len(new_poi_bytes))
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
