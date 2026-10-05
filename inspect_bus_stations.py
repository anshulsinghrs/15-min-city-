import json
import re

elements = []
if open('kolkata_bus_stations.json').readable():
    elements.extend(json.load(open('kolkata_bus_stations.json', encoding='utf-8')))

raw = json.load(open('raw_kolkata_osm_pois.json', encoding='utf-8'))
for r in raw:
    tags = r.get('tags', {})
    a = tags.get('amenity')
    pt = tags.get('public_transport')
    name = tags.get('name', '').lower()
    if a == 'bus_station' or (pt == 'station' and tags.get('bus') == 'yes') or any(w in name for w in ['bus stand', 'bus terminus', 'bus terminal', 'bus depot', 'mini bus terminus', 'mini bus stand']):
        elements.append(r)

print(f"Total raw bus station candidates: {len(elements)}")

bus_stations = []
WHEELCHAIR_MAP = {"yes": 1, "limited": 2, "no": 3}

def clean_bus_station_name(raw_name):
    if not raw_name:
        return None
    name = raw_name.strip()
    if name.lower() in ('unnamed', 'none', 'bus stop', 'bus stopage', 'bus station'):
        return None
    # Fix spacing
    name = re.sub(r'\s+', ' ', name)
    # If just "Esplanade", make it "Esplanade Bus Terminus"
    if name.lower() == 'esplanade':
        return 'Esplanade Bus Terminus'
    if name.lower() == 'babughat':
        return 'Babughat Bus Stand'
    if name.lower() == 'howrah':
        return 'Howrah Bus Station'
    return name

for el in elements:
    tags = el.get('tags', {})
    name = tags.get('name') or tags.get('name:en') or tags.get('name:bn') or ''
    clean = clean_bus_station_name(name)
    if not clean:
        continue

    lat = el.get('lat') or (el.get('center', {}).get('lat') if 'center' in el else None)
    lon = el.get('lon') or (el.get('center', {}).get('lon') if 'center' in el else None)
    if lat is None or lon is None:
        continue

    # Clean unicode control chars
    clean = re.sub(r'[\u200e\u200f\u200b\u200c\u200d]', '', clean).strip()

    wc = WHEELCHAIR_MAP.get(tags.get('wheelchair'), 0)
    bus_stations.append({
        'name': clean,
        'lat': round(lat, 5),
        'lon': round(lon, 5),
        'wc': wc,
        'tags': tags
    })

# Deduplicate points within ~60m with similar name
deduped = []
for s in bus_stations:
    is_dup = False
    for existing in deduped:
        dlat = abs(s['lat'] - existing['lat'])
        dlon = abs(s['lon'] - existing['lon'])
        if dlat < 0.0025 and dlon < 0.0025:
            # check name similarity
            s1 = set(s['name'].lower().split())
            s2 = set(existing['name'].lower().split())
            if len(s1.intersection(s2)) >= 1:
                is_dup = True
                if s['wc'] > 0 and existing['wc'] == 0:
                    existing['wc'] = s['wc']
                break
    if not is_dup:
        deduped.append(s)

with open('cleaned_bus_stations.json', 'w', encoding='utf-8') as f:
    json.dump(deduped, f, indent=2)

print(f"Deduplicated unique bus stations: {len(deduped)}")
for s in sorted(deduped, key=lambda x: x['name']):
    safe_name = s['name'].encode('ascii', 'replace').decode('ascii')
    print(f"  • {safe_name:40} ({s['lat']}, {s['lon']}) wc={s['wc']}")
