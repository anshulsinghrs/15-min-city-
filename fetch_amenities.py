import json
import urllib.request
import urllib.parse
import sys
import time

MIN_LAT = 22.44208
MIN_LON = 88.24315
MAX_LAT = 22.65792
MAX_LON = 88.47685

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

def fetch_kolkata_amenities():
    bbox = f"{MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON}"
    print(f"Querying comprehensive amenities for Kolkata ({bbox})...")
    
    query = f"""
[out:json][timeout:90];
(
  node["amenity"]({bbox});
  way["amenity"]({bbox});
  node["shop"]({bbox});
  way["shop"]({bbox});
  node["leisure"]({bbox});
  way["leisure"]({bbox});
  node["tourism"]({bbox});
  way["tourism"]({bbox});
  node["historic"]({bbox});
  way["historic"]({bbox});
  node["railway"~"station|tram_stop|subway_entrance"]({bbox});
  way["railway"~"station|tram_stop|subway_entrance"]({bbox});
  node["highway"="bus_stop"]({bbox});
);
out center tags;
"""
    for server in OVERPASS_SERVERS:
        try:
            print(f"Connecting to {server}...")
            req = urllib.request.Request(
                server,
                data=query.encode("utf-8"),
                headers={"User-Agent": "15MinCityKolkata/2.0 (urban planning research)"}
            )
            res = urllib.request.urlopen(req, timeout=90)
            data = json.loads(res.read().decode("utf-8"))
            elements = data.get("elements", [])
            print(f"Success! Retrieved {len(elements)} raw elements from Overpass.")
            with open("raw_kolkata_osm_pois.json", "w", encoding="utf-8") as f:
                json.dump(elements, f)
            print("Saved raw features to raw_kolkata_osm_pois.json")
            return elements
        except Exception as e:
            print(f"Error on {server}: {e}")
            time.sleep(2)
    return None

if __name__ == "__main__":
    fetch_kolkata_amenities()
