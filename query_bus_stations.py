import json
import urllib.request
import urllib.parse

bbox = "22.44,88.23,22.66,88.48"

q = f"""
[out:json][timeout:25];
(
  node["amenity"="bus_station"]({bbox});
  way["amenity"="bus_station"]({bbox});
  relation["amenity"="bus_station"]({bbox});
  node["public_transport"="station"]["bus"="yes"]({bbox});
  way["public_transport"="station"]["bus"="yes"]({bbox});
  node["highway"="bus_stop"]["bus_station"="yes"]({bbox});
);
out center tags;
"""

print("Querying Overpass for Kolkata Bus Stations and Terminals...")
url = "https://overpass-api.de/api/interpreter"
data = urllib.parse.urlencode({"data": q}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"User-Agent": "15MinCityKolkata/2.0"})

try:
    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        elements = res.get("elements", [])
        print(f"Fetched {len(elements)} bus station/terminal elements")
        with open("kolkata_bus_stations.json", "w", encoding="utf-8") as f:
            json.dump(elements, f, indent=2)
except Exception as e:
    print("Error querying overpass:", e)
