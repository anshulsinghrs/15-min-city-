import json
import urllib.request
import urllib.parse
import sys
import time

# Kolkata bbox from meta.json
MIN_LAT = 22.44208
MIN_LON = 88.24315
MAX_LAT = 22.65792
MAX_LON = 88.47685

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

def test_query():
    bbox_str = f"{MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON}"
    print(f"Testing Overpass query for bbox {bbox_str}...")
    
    # Query count of key amenities
    q = f"""
[out:json][timeout:30];
(
  node["amenity"~"hospital|clinic|pharmacy|school|college|university|bank|atm|place_of_worship|cafe|restaurant|ferry_terminal"]({bbox_str});
);
out count;
"""
    for server in OVERPASS_SERVERS:
        try:
            print(f"Trying server: {server}")
            req = urllib.request.Request(
                server,
                data=q.encode("utf-8"),
                headers={"User-Agent": "15MinCityKolkata/1.0"}
            )
            res = urllib.request.urlopen(req, timeout=30)
            res_data = json.loads(res.read().decode("utf-8"))
            print("Response:", res_data)
            return True
        except Exception as e:
            print(f"Failed on {server}: {e}")
            time.sleep(1)
    return False

if __name__ == "__main__":
    test_query()
