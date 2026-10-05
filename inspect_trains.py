import json

elms = json.load(open('kolkata_train_elements.json', encoding='utf-8'))
print(f"Total elements: {len(elms)}")

train_stations = []
metro_elements = []

for e in elms:
    tags = e.get('tags', {})
    name = tags.get('name') or tags.get('name:en') or tags.get('name:bn') or 'Unnamed Station'
    rwy = tags.get('railway')
    stn = tags.get('station')
    sub = tags.get('subway')
    trn = tags.get('train')
    
    # Check if it's explicitly metro / subway
    is_metro = (
        stn == 'subway' or 
        sub == 'yes' or 
        'metro' in name.lower() or 
        tags.get('network') == 'Kolkata Metro' or 
        tags.get('operator') == 'Metro Railway, Kolkata'
    )
    
    if is_metro:
        metro_elements.append((name, tags))
    else:
        train_stations.append((e['type'], e['id'], name, tags))

print(f"\nIdentified Train/Rail stations: {len(train_stations)}")
print(f"Filtered out Metro overlap: {len(metro_elements)}")

print("\n--- SAMPLE TRAIN STATIONS ---")
for t, eid, name, tags in train_stations:
    operator = tags.get('operator', tags.get('network', ''))
    wc = tags.get('wheelchair', 'untagged')
    print(f"• {name} [{t}/{eid}] ({operator}) - wheelchair={wc}")
