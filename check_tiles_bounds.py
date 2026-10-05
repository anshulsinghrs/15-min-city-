import json

meta = json.load(open('data/kolkata/meta.json', encoding='utf-8'))
tiles_info = meta['tiles']
lon0 = tiles_info['lon0']
lat0 = tiles_info['lat0']
dlon = tiles_info['dlon']
dlat = tiles_info['dlat']
valid_tiles = set(tiles_info['list'])

stations = json.load(open('cleaned_train_stations.json', encoding='utf-8'))

exclude = {
    'howrah metro', 'salt lake stadium', 'vip bazar', 'ritwik ghatak', 
    'barun sengupta', 'beliaghata', 'sokher bazar', 'howrah goods'
}

filtered = []
for s in stations:
    if s['name'].lower() in exclude:
        continue
    
    # Calculate tile coordinates
    tx = int((s['lon'] - lon0) / dlon)
    ty = int((s['lat'] - lat0) / dlat)
    tkey = f"{tx}_{ty}"
    
    if tkey in valid_tiles:
        filtered.append((s, tkey))
    else:
        print(f"Out of tile bounds: {s['name']} at ({s['lat']}, {s['lon']}) -> {tkey}")

print(f"\nTotal valid train stations inside Kolkata tiles: {len(filtered)}")
for s, tkey in sorted(filtered, key=lambda x: x[0]['name']):
    print(f"  [{tkey:5}] {s['name']:35} ({s['lat']:.5f}, {s['lon']:.5f}) wc={s['wc']}")
