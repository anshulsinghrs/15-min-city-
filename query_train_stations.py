import json
import urllib.request
import urllib.parse
import time

# Kolkata bbox: [minLat, minLon, maxLat, maxLon]
# [22.44, 88.23, 22.66, 88.48]
bbox = "22.44,88.23,22.66,88.48"

overpass_query = f"""
[out:json][timeout:30];
(
  node["railway"="station"]["station"!="subway"]({bbox});
  way["railway"="station"]["station"!="subway"]({bbox});
  relation["railway"="station"]["station"!="subway"]({bbox});
  node["railway"="halt"]({bbox});
  way["railway"="halt"]({bbox});
  node["building"="train_station"]({bbox});
  way["building"="train_station"]({bbox});
  node["public_transport"="station"]["train"="yes"]({bbox});
  way["public_transport"="station"]["train"="yes"]({bbox});
);
out center tags;
"""

print("Querying Overpass for Kolkata railway/train stations...")
url = "https://overpass-api.de/api/interpreter"
data = urllib.parse.urlencode({"data": overpass_query}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"User-Agent": "15MinCityKolkata/2.0"})

try:
    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        elements = res.get("elements", [])
        print(f"Fetched {len(elements)} train station elements")
        with open("kolkata_train_elements.json", "w", encoding="utf-8") as f:
            json.dump(elements, f, indent=2)
except Exception as e:
    print("Error querying overpass:", e)
