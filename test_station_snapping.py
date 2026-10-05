import json
import struct
import math

meta = json.load(open('data/kolkata/meta.json', encoding='utf-8'))
tiles_info = meta['tiles']
lon0 = tiles_info['lon0']
lat0 = tiles_info['lat0']
dlon = tiles_info['dlon']
dlat = tiles_info['dlat']

stations = json.load(open('cleaned_train_stations.json', encoding='utf-8'))
exclude = {'howrah metro', 'salt lake stadium', 'vip bazar', 'ritwik ghatak', 'barun sengupta', 'beliaghata', 'sokher bazar', 'howrah goods'}
stations = [s for s in stations if s['name'].lower() not in exclude]

# Distance formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

results = []
for s in stations:
    tx = int((s['lon'] - lon0) / dlon)
    ty = int((s['lat'] - lat0) / dlat)
    tkey = f"{tx}_{ty}"
    try:
        with open(f"data/kolkata/t/{tkey}.bin", "rb") as f:
            buf = f.read()
            graph_len = struct.unpack_from("<I", buf, 0)[0]
            # parse graph to find nearest node
            # The tile binary layout:
            # uint32 graph_len
            # nN (uint32), nE (uint32)
            # lat (float64 * nN), lon (float64 * nN)
            nN, nE = struct.unpack_from("<II", buf, 4)
            offset = 12
            lats = struct.unpack_from(f"<{nN}d", buf, offset)
            offset += nN * 8
            lons = struct.unpack_from(f"<{nN}d", buf, offset)
            
            min_dist = float('inf')
            nearest_idx = -1
            for i in range(nN):
                d = haversine(s['lat'], s['lon'], lats[i], lons[i])
                if d < min_dist:
                    min_dist = d
                    nearest_idx = i
            results.append((s['name'], tkey, min_dist, nearest_idx))
    except Exception as e:
        results.append((s['name'], tkey, 99999, -1))

print(f"Tested {len(results)} stations for network snap distance:")
for name, tkey, dist, idx in sorted(results, key=lambda x: -x[2]):
    print(f"  {name:30} in {tkey}: dist={dist:.1f}m (idx={idx})")
