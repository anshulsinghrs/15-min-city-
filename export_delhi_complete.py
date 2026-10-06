import gzip
import xml.etree.ElementTree as ET
import time
import json
import math
from pathlib import Path
import networkx as nx
import numpy as np
import osmnx as ox

from export_city import (
    categorize, step_kind, build_graph_arrays, write_tiles, haversine_m
)

MIN_LAT, MAX_LAT = 28.480, 28.750
MIN_LON, MAX_LON = 77.000, 77.340

WALK_EXCLUDE = {
    "abandoned", "bus_guideway", "construction", "corridor", "elevator",
    "escalator", "motorway", "motorway_link", "planned", "platform",
    "proposed", "raceway"
}

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
    "Bus Terminals & Stations"       # 12
]

# Major Indian Railways Terminals & Stations in Delhi
DELHI_RAILWAYS = [
    ("New Delhi Railway Station (NDLS)", 28.6430, 77.2195),
    ("Old Delhi Railway Station (DLI)", 28.6619, 77.2280),
    ("Hazrat Nizamuddin Railway Station (NZM)", 28.5887, 77.2536),
    ("Anand Vihar Railway Terminal (ANVT)", 28.6508, 77.3152),
    ("Delhi Sarai Rohilla (DEE)", 28.6625, 77.1855),
    ("Delhi Cantt Railway Station (DEC)", 28.5955, 77.1265),
    ("Tilak Bridge Railway Station", 28.6275, 77.2415),
    ("Shivaji Bridge Railway Station", 28.6315, 77.2295),
    ("Subzi Mandi Railway Station", 28.6675, 77.2025),
    ("Kishanganj Railway Station", 28.6610, 77.1950),
    ("Sewa Nagar Railway Station", 28.5780, 77.2250),
    ("Lodhi Colony Railway Station", 28.5835, 77.2200),
    ("Okhla Railway Station", 28.5550, 77.2750),
    ("Shakurbasti Railway Station", 28.6825, 77.1350),
    ("Mangolpuri Railway Station", 28.6850, 77.0950),
    ("Shahdara Railway Junction", 28.6730, 77.2880)
]

def main():
    print("="*60)
    print("Exporting COMPLETE Greater Delhi Walking Network & POIs")
    print(f"Bounding Box: Lat [{MIN_LAT} .. {MAX_LAT}], Lon [{MIN_LON} .. {MAX_LON}]")
    print("="*60)

    t0 = time.time()
    node_coords = {}
    raw_pois = []
    metro_from_osm = {} # name -> (lat, lon)

    print("\n[Step 1/5] Parsing OSM nodes from NewDelhi.osm.gz...")
    with gzip.open("NewDelhi.osm.gz", "rb") as f:
        for event, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "node":
                nid = int(elem.attrib["id"])
                lat = float(elem.attrib["lat"])
                lon = float(elem.attrib["lon"])
                if MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON:
                    node_coords[nid] = (lon, lat)
                    tags = {c.attrib["k"]: c.attrib["v"] for c in elem if c.tag == "tag"}
                    if tags:
                        name = tags.get("name:en") or tags.get("name") or ""
                        # Check if metro station
                        station = tags.get("station")
                        r_tag = tags.get("railway")
                        subway = tags.get("subway")
                        if station == "subway" or subway == "yes" or r_tag == "subway_entrance":
                            if name:
                                clean_name = name.split("Gate")[0].replace("Metro Station", "").replace("Metro", "").strip()
                                if clean_name and len(clean_name) > 2:
                                    metro_from_osm[clean_name] = (lat, lon)

                        cat_res = categorize(tags)
                        if cat_res is not None:
                            c_id, wc = cat_res
                            # Handle transit subcategories
                            if c_id == 6:
                                a_tag = tags.get("amenity")
                                h_tag = tags.get("highway")
                                if r_tag in ("station", "halt") and station != "subway" and subway != "yes":
                                    c_id = 11 # Train
                                elif a_tag == "bus_station":
                                    c_id = 12 # Bus terminal
                                elif h_tag == "bus_stop":
                                    c_id = 10 # Bus stop
                            raw_pois.append((lon, lat, c_id, wc, name))
                elem.clear()
            elif elem.tag == "way":
                break

    print(f"  Nodes parsed: {len(node_coords):,}")
    print(f"  Node POIs collected: {len(raw_pois):,}")
    print(f"  Identified {len(metro_from_osm):,} Metro station points from OSM nodes")

    print("\n[Step 2/5] Parsing OSM ways (streets + polygons)...")
    G = nx.MultiDiGraph()
    way_poi_count = 0

    with gzip.open("NewDelhi.osm.gz", "rb") as f:
        for event, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "way":
                tags = {c.attrib["k"]: c.attrib["v"] for c in elem if c.tag == "tag"}
                nds = [int(c.attrib["ref"]) for c in elem if c.tag == "nd"]
                
                # Check for POI way
                cat_res = categorize(tags)
                if cat_res is not None and nds:
                    valid_pts = [node_coords[n] for n in nds if n in node_coords]
                    if valid_pts:
                        avg_lon = sum(p[0] for p in valid_pts) / len(valid_pts)
                        avg_lat = sum(p[1] for p in valid_pts) / len(valid_pts)
                        name = tags.get("name:en") or tags.get("name") or ""
                        c_id, wc = cat_res
                        if c_id == 6:
                            if tags.get("amenity") == "bus_station": c_id = 12
                            elif tags.get("railway") == "station": c_id = 11
                        raw_pois.append((avg_lon, avg_lat, c_id, wc, name))
                        way_poi_count += 1

                # Check for walkable street
                hw = tags.get("highway")
                if hw and hw not in WALK_EXCLUDE and tags.get("foot") != "no" and tags.get("access") != "private":
                    seg = []
                    for n in nds:
                        if n in node_coords:
                            seg.append(n)
                        else:
                            if len(seg) >= 2:
                                for u, v in zip(seg[:-1], seg[1:]):
                                    d = haversine_m(node_coords[u][0], node_coords[u][1], node_coords[v][0], node_coords[v][1])
                                    edata = dict(tags)
                                    edata["length"] = d
                                    if not G.has_node(u): G.add_node(u, x=node_coords[u][0], y=node_coords[u][1])
                                    if not G.has_node(v): G.add_node(v, x=node_coords[v][0], y=node_coords[v][1])
                                    G.add_edge(u, v, **edata)
                                    G.add_edge(v, u, **edata)
                            seg = []
                    if len(seg) >= 2:
                        for u, v in zip(seg[:-1], seg[1:]):
                            d = haversine_m(node_coords[u][0], node_coords[u][1], node_coords[v][0], node_coords[v][1])
                            edata = dict(tags)
                            edata["length"] = d
                            if not G.has_node(u): G.add_node(u, x=node_coords[u][0], y=node_coords[u][1])
                            if not G.has_node(v): G.add_node(v, x=node_coords[v][0], y=node_coords[v][1])
                            G.add_edge(u, v, **edata)
                            G.add_edge(v, u, **edata)
                elem.clear()

    print(f"  Way POIs collected: {way_poi_count:,}")
    print(f"  Raw Street Graph: {len(G.nodes):,} nodes, {len(G.edges):,} edges")

    print("\n[Step 3/5] Simplifying network graph...")
    t_simp = time.time()
    G_simp = ox.simplify_graph(G, edge_attrs_differ=["highway", "ramp:wheelchair"])
    print(f"  Simplified in {time.time()-t_simp:.1f}s: {len(G_simp.nodes):,} nodes, {len(G_simp.edges):,} edges")

    print("\n[Step 4/5] Building graph binary arrays...")
    arrays = build_graph_arrays(G_simp)
    print(f"  Arrays built: {len(arrays['lonlat']):,} nodes, {len(arrays['eu']):,} edges, {len(arrays['shape_arr']):,} shape points")

    print("\n[Step 5/5] Integrating verified Metro & Railway Stations & POIs...")
    
    # Load all registered Delhi Metro stations
    from update_all_cities_metro import CITY_METRO_REGISTRY
    delhi_registry = {}
    for item in CITY_METRO_REGISTRY.get("delhi", []):
        delhi_registry[item[0]] = (item[1], item[2])
    for sname, (slat, slon) in metro_from_osm.items():
        if sname not in delhi_registry:
            delhi_registry[sname] = (slat, slon)

    final_pois = []
    metro_injected = 0
    for sname, coords in delhi_registry.items():
        slat, slon = coords if isinstance(coords, (tuple, list)) else (coords[0], coords[1])
        if MIN_LAT <= slat <= MAX_LAT and MIN_LON <= slon <= MAX_LON:
            final_pois.append([round(slon, 5), round(slat, 5), 6, 1, sname])
            metro_injected += 1

    # Add all railway stations
    rail_injected = 0
    for sname, slat, slon in DELHI_RAILWAYS:
        if MIN_LAT <= slat <= MAX_LAT and MIN_LON <= slon <= MAX_LON:
            final_pois.append([round(slon, 5), round(slat, 5), 11, 1, sname])
            rail_injected += 1

    # Add other OSM POIs
    for lon, lat, c_id, wc, name in raw_pois:
        if c_id == 6:
            # Check if near any verified metro
            near = False
            for sname, coords in delhi_registry.items():
                slat, slon = coords if isinstance(coords, (tuple, list)) else (coords[0], coords[1])
                if haversine_m(lon, lat, slon, slat) < 250:
                    near = True
                    break
            if not near:
                final_pois.append([round(lon, 5), round(lat, 5), 10, wc, name or "Bus Stop"])
        else:
            final_pois.append([round(lon, 5), round(lat, 5), c_id, wc, name])

    print(f"  Total POIs: {len(final_pois):,} (including {metro_injected} Metro & {rail_injected} Suburban Rail stations)")

    out_dir = Path("data/delhi")
    tiles_meta = write_tiles(arrays, final_pois, out_dir, tile_km=2.5)
    print(f"  Generated {len(tiles_meta['list'])} tiles in data/delhi/t/")

    # Update meta.json
    lonlat = arrays["lonlat"]
    bbox = [
        float(lonlat[:, 0].min() / 1e5),
        float(lonlat[:, 1].min() / 1e5),
        float(lonlat[:, 0].max() / 1e5),
        float(lonlat[:, 1].max() / 1e5)
    ]
    meta = {
        "name": "Delhi, NCT, India",
        "bbox": bbox,
        "start": [28.6315, 77.2167], # Connaught Place / Central Delhi
        "nodes": len(lonlat),
        "edges": len(arrays["eu"]),
        "pois": len(final_pois),
        "tiles": tiles_meta,
        "cats": CATS
    }
    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)

    print(f"\nSUCCESS! Updated data/delhi/meta.json in {time.time()-t0:.1f}s total.")
    print(f"Bbox: {bbox}")
    print(f"Nodes: {len(lonlat):,}, Edges: {len(arrays['eu']):,}, Tiles: {len(tiles_meta['list'])}")

if __name__ == "__main__":
    main()
