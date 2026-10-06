import json
from pathlib import Path

cities = json.load(open('data/cities.json', encoding='utf-8'))['cities']
print(f"{'City':16} {'Slug':10} {'Coverage (km)':15} {'Nodes':8} {'Edges':8} {'POIs':8} {'Tiles':6} {'Bbox Lat':16} {'Bbox Lon':16}")
print("-" * 105)

for c in cities:
    cid = c['id']
    meta_p = Path(f'data/{cid}/meta.json')
    if not meta_p.exists():
        print(f"{c['name']:16} {cid:10} MISSING")
        continue
    meta = json.load(open(meta_p, encoding='utf-8'))
    bbox = meta['bbox']
    minlon, minlat, maxlon, maxlat = bbox
    dlat_km = (maxlat - minlat) * 111.0
    dlon_km = (maxlon - minlon) * 111.0 * 0.95
    t_info = meta.get('tiles', {})
    tiles_count = len(t_info.get('list', []))
    pois_count = meta.get('pois', 0)
    nodes = meta.get('nodes', 0)
    edges = meta.get('edges', 0)
    cov_str = f"{dlat_km:.1f} x {dlon_km:.1f} km"
    lat_range = f"{minlat:.3f}..{maxlat:.3f}"
    lon_range = f"{minlon:.3f}..{maxlon:.3f}"
    print(f"{c['name']:16} {cid:10} {cov_str:15} {nodes:8,d} {edges:8,d} {pois_count:8,d} {tiles_count:6d} {lat_range:16} {lon_range:16}")
