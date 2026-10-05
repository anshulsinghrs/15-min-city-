import json

elements = json.load(open('kolkata_train_elements.json', encoding='utf-8'))

# List of known Kolkata Metro stations to exclude
metro_names = {
    'dakshineswar', 'baranagar', 'noapara', 'dum dum', 'dum dum cantt.', 'dum dum cantonment',
    'belgachia', 'shyambazar', 'shobhabazar sutee', 'shobhabazar sutanuti', 'girish park',
    'mahatma gandhi road', 'central', 'chandni chowk', 'esplanade', 'park street', 'maidan',
    'netaji bhavan', 'jatin das park', 'kalighat', 'rabindra sarobar', 'mahanayak uttam kumar',
    'netaji', 'masterda surya sen', 'gitanjali', 'kavi nazrul', 'shahid khudiram', 'kavi subhash',
    'howrah maidan', 'howrah metro', 'sealdah metro', 'phoolbagan', 'salt lake stadium',
    'bengal chemical', 'city centre', 'central park', 'karunamoyee', 'salt lake sector v',
    'joka', 'thakurpukur', 'sakherbazar', 'sokher bazar', 'behala chourasta', 'behala bazar',
    'taratala', 'majerhat metro', 'mominpur', 'khidirpur metro', 'victoria',
    'kavi sukanta', 'kavi sukanta (kalikapur)', 'hemanta mukhopadhyay', 'hemanta mukherjee (ruby)',
    'vip bazar', 'ritwik ghatak', 'barun sengupta', 'beliaghata', 'gurudakshina', 'chinar park'
}

stations = []

for el in elements:
    tags = el.get('tags', {})
    name = tags.get('name') or tags.get('name:en') or tags.get('name:bn') or ''
    if not name or name.strip().lower() == 'unnamed station':
        continue
    
    clean_name = name.strip()
    norm = clean_name.lower().replace(' metro station', '').replace(' metro', '').strip()
    
    # Exclude metro
    stn = tags.get('station', '')
    sub = tags.get('subway', '')
    if stn == 'subway' or sub == 'yes' or tags.get('network') == 'Kolkata Metro' or tags.get('operator') == 'Metro Railway, Kolkata':
        continue
    if norm in metro_names and ('metro' in clean_name.lower() or 'sector' in norm or 'karunamoyee' in norm or 'ruby' in norm or 'taratala' in norm or 'thakurpukur' in norm or 'chourasta' in norm or 'bengal chemical' in norm or 'central park' in norm or 'city centre' in norm or 'phoolbagan' in norm or 'kavi sukanta' in norm):
        continue

    # Get lat, lon
    lat = el.get('lat') or (el.get('center', {}).get('lat') if 'center' in el else None)
    lon = el.get('lon') or (el.get('center', {}).get('lon') if 'center' in el else None)
    if lat is None or lon is None:
        continue

    # Wheelchair
    wc_tag = tags.get('wheelchair', 'untagged').lower()
    wc_code = 0
    if wc_tag in ['yes', 'designated']:
        wc_code = 1
    elif wc_tag in ['limited']:
        wc_code = 2
    elif wc_tag in ['no']:
        wc_code = 3

    # Important terminal stations usually have ramps/accessibility facilities
    if any(term in clean_name.lower() for term in ['howrah junction', 'sealdah']):
        wc_code = 1

    network = tags.get('network', tags.get('operator', 'Indian Railways'))

    stations.append({
        'id': f"{el['type']}/{el['id']}",
        'name': clean_name,
        'lat': lat,
        'lon': lon,
        'wc': wc_code,
        'network': network,
        'tags': tags
    })

# Deduplicate points that are within 50m of each other with same or very similar name
deduped = []
for s in stations:
    is_dup = False
    for existing in deduped:
        dlat = abs(s['lat'] - existing['lat'])
        dlon = abs(s['lon'] - existing['lon'])
        if dlat < 0.002 and dlon < 0.002 and (s['name'].lower() in existing['name'].lower() or existing['name'].lower() in s['name'].lower()):
            is_dup = True
            # keep the one with better wc if available
            if s['wc'] > 0 and existing['wc'] == 0:
                existing['wc'] = s['wc']
            break
    if not is_dup:
        deduped.append(s)

print(f"Total deduplicated train stations: {len(deduped)}")
for s in sorted(deduped, key=lambda x: x['name']):
    print(f"  • {s['name']:30} ({s['lat']:.5f}, {s['lon']:.5f}) wc={s['wc']} net={s['network']}")

with open('cleaned_train_stations.json', 'w', encoding='utf-8') as f:
    json.dump(deduped, f, indent=2)
