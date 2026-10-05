import urllib.request
import json

bbox = "22.44208,88.24315,22.65792,88.47685"
q = f"""
[out:json][timeout:30];
(
  node["station"="subway"]({bbox});
  way["station"="subway"]({bbox});
  node["railway"="station"]["subway"="yes"]({bbox});
  way["railway"="station"]["subway"="yes"]({bbox});
  node["railway"="subway_entrance"]({bbox});
  node["network"~"Metro|Kolkata Metro"]({bbox});
  way["network"~"Metro|Kolkata Metro"]({bbox});
);
out center tags;
"""

for server in ["https://lz4.overpass-api.de/api/interpreter", "https://overpass-api.de/api/interpreter"]:
    try:
        print("Querying", server)
        req = urllib.request.Request(
            server,
            data=q.encode("utf-8"),
            headers={"User-Agent": "15MinCityKolkata/2.0"}
        )
        res = urllib.request.urlopen(req, timeout=30)
        data = json.loads(res.read().decode("utf-8"))
        elements = data.get("elements", [])
        print(f"Retrieved {len(elements)} subway elements.")
        stations = {}
        for el in elements:
            tags = el.get("tags", {})
            n = tags.get("name") or tags.get("name:en")
            if n:
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                stations[n] = (round(lat, 5), round(lon, 5), tags.get("wheelchair"))
        print(f"Total distinct metro names/gates: {len(stations)}")
        print("Sample:", list(stations.keys())[:25])
        with open("kolkata_metro_elements.json", "w", encoding="utf-8") as f:
            json.dump(elements, f)
        break
    except Exception as e:
        print("Error:", e)
