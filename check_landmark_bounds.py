import json
import re
from pathlib import Path

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const CITY_LANDMARKS = \{(.*?)\n\};', text, re.S)
block = m.group(1) if m else ''

city_blocks = re.findall(r'(\w+):\s*\[(.*?)\]', block, re.S)
for cid, lmarks in city_blocks:
    meta_p = Path(f'data/{cid}/meta.json')
    if not meta_p.exists():
        print(f"Missing meta for {cid}")
        continue
    meta = json.load(open(meta_p, encoding='utf-8'))
    bbox = meta['bbox']
    minlon, minlat, maxlon, maxlat = bbox
    
    items = re.findall(r'name:\s*"([^"]+)",\s*lat:\s*([\d.-]+),\s*lon:\s*([\d.-]+)', lmarks)
    for name, lat_s, lon_s in items:
        lat, lon = float(lat_s), float(lon_s)
        in_bbox = (minlon <= lon <= maxlon and minlat <= lat <= maxlat)
        if not in_bbox:
            print(f"OUTSIDE! [{cid:10}] {name:30}: ({lat:.4f}, {lon:.4f}) outside bbox [{minlat:.3f}..{maxlat:.3f}, {minlon:.3f}..{maxlon:.3f}]")
