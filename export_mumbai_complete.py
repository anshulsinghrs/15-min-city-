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

MIN_LAT, MAX_LAT = 18.890, 19.160
MIN_LON, MAX_LON = 72.790, 72.950

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

# Comprehensive verified Mumbai Metro Stations
MUMBAI_METRO = [
    # Line 1 (Versova - Ghatkopar)
    ("Versova", 19.1317, 72.8166),
    ("D.N. Nagar", 19.1311, 72.8258),
    ("Azad Nagar", 19.1293, 72.8362),
    ("Andheri", 19.1207, 72.8465),
    ("Western Express Highway", 19.1158, 72.8566),
    ("Chakala (J.B. Nagar)", 19.1114, 72.8660),
    ("Airport Road", 19.1102, 72.8744),
    ("Marol Naka", 19.1095, 72.8824),
    ("Saki Naka", 19.1042, 72.8878),
    ("Asalpha", 19.0963, 72.8942),
    ("Jagruti Nagar", 19.0927, 72.9038),
    ("Ghatkopar", 19.0863, 72.9080),

    # Line 3 (Aqua Line - Colaba to SEEPZ)
    ("Cuffe Parade", 18.9145, 72.8215),
    ("Vidhan Bhavan", 18.9275, 72.8258),
    ("Churchgate", 18.9322, 72.8264),
    ("Hutatma Chowk", 18.9320, 72.8315),
    ("Chhatrapati Shivaji Maharaj Terminus (CSMT)", 18.9402, 72.8354),
    ("Kalbadevi", 18.9485, 72.8285),
    ("Girgaon", 18.9560, 72.8210),
    ("Grant Road", 18.9630, 72.8185),
    ("Mumbai Central", 18.9700, 72.8195),
    ("Mahalaxmi", 18.9830, 72.8240),
    ("Science Centre", 18.9910, 72.8190),
    ("Acharya Atre Chowk", 18.9985, 72.8175),
    ("Worli", 19.0110, 72.8190),
    ("Siddhivinayak", 19.0175, 72.8310),
    ("Dadar", 19.0205, 72.8430),
    ("Shitaladevi Temple", 19.0355, 72.8425),
    ("Dharavi", 19.0470, 72.8525),
    ("BKC (Bandra Kurla Complex)", 19.0620, 72.8670),
    ("Vidyanagari", 19.0725, 72.8625),
    ("Santacruz", 19.0820, 72.8570),
    ("CSMIA Domestic T1", 19.0905, 72.8530),
    ("Sahar Road", 19.1025, 72.8660),
    ("CSMIA International T2", 19.0980, 72.8745),
    ("MIDC Andheri", 19.1180, 72.8720),
    ("SEEPZ", 19.1285, 72.8710),
    ("Aarey JVLR", 19.1350, 72.8750),

    # Line 2A & 7
    ("Gundavali", 19.1170, 72.8530),
    ("Mogra", 19.1270, 72.8535),
    ("Jogeshwari East", 19.1360, 72.8550),
    ("Goregaon East", 19.1550, 72.8560),
    ("Andheri West", 19.1310, 72.8260),
    ("Lower Oshiwara", 19.1430, 72.8310),
    ("Oshiwara", 19.1540, 72.8340)
]

# Mumbai Suburban Railway Stations
MUMBAI_RAILWAYS = [
    # Western Line
    ("Churchgate Railway Station", 18.9322, 72.8264),
    ("Marine Lines Railway Station", 18.9438, 72.8242),
    ("Charni Road Railway Station", 18.9525, 72.8188),
    ("Grant Road Railway Station", 18.9632, 72.8158),
    ("Mumbai Central Railway Station", 18.9698, 72.8193),
    ("Mahalaxmi Railway Station", 18.9827, 72.8236),
    ("Lower Parel Railway Station", 18.9950, 72.8300),
    ("Prabhadevi Railway Station", 19.0085, 72.8345),
    ("Dadar Western Station", 19.0178, 72.8433),
    ("Matunga Road Railway Station", 19.0270, 72.8420),
    ("Mahim Junction Railway Station", 19.0400, 72.8405),
    ("Bandra Railway Station", 19.0550, 72.8405),
    ("Khar Road Railway Station", 19.0690, 72.8385),
    ("Santacruz Railway Station", 19.0815, 72.8400),
    ("Vile Parle Railway Station", 19.0990, 72.8435),
    ("Andheri Railway Station", 19.1197, 72.8464),
    ("Jogeshwari Railway Station", 19.1360, 72.8490),

    # Central Line
    ("Chhatrapati Shivaji Maharaj Terminus (CSMT)", 18.9400, 72.8354),
    ("Masjid Railway Station", 18.9525, 72.8380),
    ("Sandhurst Road Railway Station", 18.9605, 72.8395),
    ("Byculla Railway Station", 18.9750, 72.8335),
    ("Chinchpokli Railway Station", 18.9855, 72.8315),
    ("Currey Road Railway Station", 18.9940, 72.8330),
    ("Parel Railway Station", 19.0060, 72.8370),
    ("Dadar Central Station", 19.0185, 72.8440),
    ("Matunga Railway Station", 19.0275, 72.8565),
    ("Sion Railway Station", 19.0410, 72.8620),
    ("Kurla Railway Station", 19.0655, 72.8790),
    ("Vidyavihar Railway Station", 19.0795, 72.8970),
    ("Ghatkopar Railway Station", 19.0860, 72.9080),
    ("Vikhroli Railway Station", 19.1110, 72.9280),
    ("Kanjurmarg Railway Station", 19.1275, 72.9320),

    # Harbour Line
    ("Dockyard Road Railway Station", 18.9660, 72.8435),
    ("Reay Road Railway Station", 18.9755, 72.8445),
    ("Cotton Green Railway Station", 18.9860, 72.8465),
    ("Sewri Railway Station", 18.9980, 72.8520),
    ("Vadala Road Railway Station", 19.0170, 72.8580),
    ("Kings Circle Railway Station", 19.0345, 72.8565),
    ("GTB Nagar Railway Station", 19.0370, 72.8670),
    ("Chunabhatti Railway Station", 19.0520, 72.8760)
]

def main():
    print("="*60)
    print("Exporting COMPLETE Greater Mumbai Walk Network & POIs")
    print(f"Bounding Box: Lat [{MIN_LAT} .. {MAX_LAT}], Lon [{MIN_LON} .. {MAX_LON}]")
    print("="*60)

    t0 = time.time()
    node_coords = {}
    raw_pois = []

    print("\n[Step 1/5] Parsing OSM nodes from Bombay.osm.gz...")
    with gzip.open("Bombay.osm.gz", "rb") as f:
        for event, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "node":
                nid = int(elem.attrib["id"])
                lat = float(elem.attrib["lat"])
                lon = float(elem.attrib["lon"])
                if MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON:
                    node_coords[nid] = (lon, lat)
                    tags = {c.attrib["k"]: c.attrib["v"] for c in elem if c.tag == "tag"}
                    if tags:
                        cat_res = categorize(tags)
                        if cat_res is not None:
                            name = tags.get("name:en") or tags.get("name") or ""
                            c_id, wc = cat_res
                            # Handle transit subcategories
                            if c_id == 6:
                                r_tag = tags.get("railway")
                                a_tag = tags.get("amenity")
                                h_tag = tags.get("highway")
                                if r_tag in ("station", "halt") and tags.get("station") != "subway":
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

    print("\n[Step 2/5] Parsing OSM ways (streets + polygons)...")
    G = nx.MultiDiGraph()
    way_poi_count = 0

    with gzip.open("Bombay.osm.gz", "rb") as f:
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
    # Inject verified Metro stations
    metro_injected = 0
    final_pois = []
    
    # Add all verified metro stations
    for sname, slat, slon in MUMBAI_METRO:
        if MIN_LAT <= slat <= MAX_LAT and MIN_LON <= slon <= MAX_LON:
            final_pois.append([round(slon, 5), round(slat, 5), 6, 1, sname])
            metro_injected += 1

    # Add all verified railway stations
    rail_injected = 0
    for sname, slat, slon in MUMBAI_RAILWAYS:
        if MIN_LAT <= slat <= MAX_LAT and MIN_LON <= slon <= MAX_LON:
            final_pois.append([round(slon, 5), round(slat, 5), 11, 1, sname])
            rail_injected += 1

    # Add other OSM POIs (deduplicating near metro/rail)
    for lon, lat, c_id, wc, name in raw_pois:
        if c_id == 6:
            # Check if near any verified metro
            near = False
            for _, ms_lat, ms_lon in MUMBAI_METRO:
                if haversine_m(lon, lat, ms_lon, ms_lat) < 200:
                    near = True
                    break
            if not near:
                # If it's a bus stop incorrectly categorized as transit
                final_pois.append([round(lon, 5), round(lat, 5), 10, wc, name or "Bus Stop"])
        else:
            final_pois.append([round(lon, 5), round(lat, 5), c_id, wc, name])

    print(f"  Total POIs: {len(final_pois):,} (including {metro_injected} Metro & {rail_injected} Suburban Rail stations)")

    out_dir = Path("data/mumbai")
    tiles_meta = write_tiles(arrays, final_pois, out_dir, tile_km=2.5)
    print(f"  Generated {len(tiles_meta['list'])} tiles in data/mumbai/t/")

    # Update meta.json
    lonlat = arrays["lonlat"]
    bbox = [
        float(lonlat[:, 0].min() / 1e5),
        float(lonlat[:, 1].min() / 1e5),
        float(lonlat[:, 0].max() / 1e5),
        float(lonlat[:, 1].max() / 1e5)
    ]
    meta = {
        "name": "Mumbai, Maharashtra, India",
        "bbox": bbox,
        "start": [18.9400, 72.8354], # CSMT / South Mumbai
        "nodes": len(lonlat),
        "edges": len(arrays["eu"]),
        "pois": len(final_pois),
        "tiles": tiles_meta,
        "cats": CATS
    }
    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)

    print(f"\nSUCCESS! Updated data/mumbai/meta.json in {time.time()-t0:.1f}s total.")
    print(f"Bbox: {bbox}")
    print(f"Nodes: {len(lonlat):,}, Edges: {len(arrays['eu']):,}, Tiles: {len(tiles_meta['list'])}")

if __name__ == "__main__":
    main()
