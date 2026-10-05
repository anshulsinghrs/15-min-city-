import json
import urllib.request
import urllib.parse

bbox = "22.44,88.23,22.66,88.48"

q = f"""
[out:json][timeout:30];
(
  node["railway"="platform"]["train"="yes"]({bbox});
  node["public_transport"="platform"]["train"="yes"]({bbox});
  node["railway"="station_entrance"]({bbox});
  node["entrance"="yes"]["railway"]({bbox});
);
out center tags;
"""

print("Querying Overpass for railway platforms and entrances...")
url = "https://overpass-api.de/api/interpreter"
data = urllib.parse.urlencode({"data": q}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"User-Agent": "15MinCityKolkata/2.0"})

try:
    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        elements = res.get("elements", [])
        print(f"Fetched {len(elements)} railway platform/entrance elements")
        with open("kolkata_railway_extra_elements.json", "w", encoding="utf-8") as f:
            json.dump(elements, f, indent=2)
except Exception as e:
    print("Error querying overpass:", e)
