import json
import re
import math
import struct
from pathlib import Path
from collections import defaultdict

CATS = [
    "Groceries & Essentials",       # 0
    "Healthcare",                   # 1
    "Education",                    # 2
    "Parks & Recreation",           # 3
    "Dining & Cafés",               # 4
    "Rest Benches",                 # 5
    "Metro Stations",               # 6
    "Civic & Financial",            # 7
    "Culture & Worship",            # 8
    "Sanitation & Water",           # 9
    "Local Bus, Tram & Ferry Stops",# 10
    "Suburban Railway Stations",    # 11
    "Bus Terminals & Stations"      # 12
]

def haversine(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2 - lon1)/2)**2
    return 12742000 * math.asin(math.sqrt(a))

# Master Registry of Metro Stations across all cities
CITY_METRO_REGISTRY = {
    "delhi": [
        ("Rajiv Chowk", 28.6328, 77.2195),
        ("Central Secretariat", 28.6159, 77.2123),
        ("Patel Chowk", 28.6230, 77.2140),
        ("Barakhamba Road", 28.6304, 77.2233),
        ("Mandi House", 28.6254, 77.2335),
        ("Janpath", 28.6240, 77.2193),
        ("Shivaji Stadium", 28.6289, 77.2113),
        ("Ramakrishna Ashram Marg", 28.6392, 77.2086),
        ("New Delhi", 28.6435, 77.2227),
        ("Chawri Bazar", 28.6493, 77.2265),
        ("Chandni Chowk", 28.6584, 77.2303),
        ("Kashmere Gate", 28.6674, 77.2282),
        ("Delhi Gate", 28.6392, 77.2408),
        ("ITO", 28.6282, 77.2410),
        ("Jama Masjid", 28.6500, 77.2377),
        ("Lal Quila", 28.6587, 77.2372),
        ("Supreme Court", 28.6235, 77.2425),
        ("Indraprastha", 28.6206, 77.2496),
        ("Khan Market", 28.6020, 77.2292),
        ("Jawaharlal Nehru Stadium", 28.5882, 77.2338),
        ("Jangpura", 28.5830, 77.2393),
        ("Lajpat Nagar", 28.5692, 77.2389),
        ("South Extension", 28.5684, 77.2204),
        ("Dilli Haat - INA", 28.5738, 77.2097),
        ("AIIMS", 28.5684, 77.2078),
        ("Jor Bagh", 28.5865, 77.2125),
        ("Lok Kalyan Marg", 28.5974, 77.2111),
        ("Udyog Bhawan", 28.6113, 77.2122),
        ("Dhaula Kuan", 28.5919, 77.1617),
        ("Durgabai Deshmukh South Campus", 28.5894, 77.1698),
        ("Sir M. Vishweshwaraiah Moti Bagh", 28.5785, 77.1757),
        ("Bhikaji Cama Place", 28.5703, 77.1879),
        ("Sarojini Nagar", 28.5758, 77.1981),
        ("Karol Bagh", 28.6440, 77.1885),
        ("Jhandewalan", 28.6443, 77.1999),
        ("Rajendra Place", 28.6425, 77.1783),
        ("Patel Nagar", 28.6450, 77.1693),
        ("Shadipur", 28.6516, 77.1583),
        ("Kirti Nagar", 28.6557, 77.1507),
        ("Tis Hazari", 28.6672, 77.2166),
        ("Pul Bangash", 28.6664, 77.2074),
        ("Pratap Nagar", 28.6667, 77.1989),
        ("Yamuna Bank", 28.6233, 77.2680),
        ("Moolchand", 28.5644, 77.2343),
        ("Vinobapuri", 28.5659, 77.2493),
        ("Sarai Kale Khan - Nizamuddin", 28.5887, 77.2572),
        ("Ashram", 28.5724, 77.2588)
    ],
    "bengaluru": [
        ("Nadaprabhu Kempegowda Station, Majestic", 12.9757, 77.5728),
        ("Mahatma Gandhi Road", 12.9755, 77.6066),
        ("Cubbon Park", 12.9810, 77.5976),
        ("Dr. B. R. Ambedkar Station, Vidhana Soudha", 12.9787, 77.5925),
        ("Sir M. Visvesvaraya Station, Central College", 12.9745, 77.5835),
        ("Krantivira Sangolli Rayanna Railway Station", 12.9759, 77.5670),
        ("Magadi Road", 12.9756, 77.5550),
        ("Sri Balagangadharanatha Swamiji Station, Hosahalli", 12.9743, 77.5450),
        ("Trinity", 12.9730, 77.6170),
        ("Halasuru", 12.9765, 77.6265),
        ("Indiranagar", 12.9783, 77.6385),
        ("Swami Vivekananda Road", 12.9859, 77.6450),
        ("Chickpete", 12.9669, 77.5750),
        ("Krishna Rajendra Market", 12.9609, 77.5750),
        ("National College", 12.9505, 77.5730),
        ("Lalbagh", 12.9465, 77.5800),
        ("South End Circle", 12.9383, 77.5805),
        ("Jayanagar", 12.9295, 77.5801),
        ("Rashtreeya Vidyalaya Road", 12.9216, 77.5800),
        ("Mantri Square Sampige Road", 12.9905, 77.5710),
        ("Srirampura", 12.9965, 77.5630),
        ("Mahakavi Kuvempu Road", 12.9985, 77.5570),
        ("Rajajinagar", 13.0005, 77.5495),
        ("Mahalakshmi", 13.0080, 77.5488),
        ("Sandal Soap Factory", 13.0147, 77.5526),
        ("Yeshwantpur", 13.0233, 77.5501)
    ],
    "chennai": [
        ("Puratchi Thalaivar Dr. M.G. Ramachandran Central Metro", 13.0817, 80.2739),
        ("Government Estate", 13.0696, 80.2730),
        ("LIC", 13.0644, 80.2658),
        ("Thousand Lights", 13.0585, 80.2588),
        ("AG-DMS", 13.0459, 80.2483),
        ("Teynampet", 13.0368, 80.2464),
        ("Nandanam", 13.0317, 80.2412),
        ("Egmore", 13.0803, 80.2631),
        ("Nehru Park", 13.0788, 80.2505),
        ("Kilpauk", 13.0776, 80.2426),
        ("Pachaiyappa's College", 13.0755, 80.2329),
        ("Shenoy Nagar", 13.0797, 80.2250),
        ("High Court", 13.0873, 80.2850),
        ("Mannadi", 13.0954, 80.2861),
        ("Washermanpet", 13.1078, 80.2809),
        ("Sir Theagaraya College", 13.1158, 80.2847),
        ("Tondiarpet", 13.1245, 80.2889),
        ("New Washermanpet", 13.1345, 80.2930)
    ],
    "mumbai": [
        ("Chhatrapati Shivaji Maharaj Terminus (CSMT Metro)", 18.9402, 72.8354),
        ("Churchgate Metro", 18.9322, 72.8264),
        ("Vidhan Bhavan Metro", 18.9275, 72.8258),
        ("Hutatma Chowk Metro", 18.9320, 72.8315),
        ("Cuffe Parade Metro", 18.9145, 72.8215),
        ("Kalbadevi Metro", 18.9485, 72.8285),
        ("Girgaon Metro", 18.9560, 72.8210),
        ("Grant Road Metro", 18.9630, 72.8185),
        ("Mumbai Central Metro", 18.9700, 72.8195),
        ("Mahalaxmi Metro", 18.9830, 72.8240),
        ("Science Centre Metro", 18.9910, 72.8190)
    ],
    "hyderabad": [
        ("MGBS Interchange", 17.3770, 78.4820),
        ("Sultan Bazar", 17.3855, 78.4840),
        ("Narayanguda", 17.3940, 78.4910),
        ("Chikkadpally", 17.4010, 78.4975),
        ("RTC X Roads", 17.4080, 78.5005),
        ("Musheerabad", 17.4170, 78.5030),
        ("Gandhi Hospital", 17.4245, 78.5035),
        ("Secunderabad West", 17.4340, 78.5015),
        ("Parade Ground", 17.4380, 78.5000),
        ("Secunderabad East", 17.4350, 78.5030),
        ("Osmania Medical College", 17.3810, 78.4810),
        ("Gandhi Bhavan", 17.3880, 78.4735),
        ("Nampally", 17.3915, 78.4680),
        ("Assembly", 17.3980, 78.4675),
        ("Lakdi-ka-pul", 17.4045, 78.4660),
        ("Khairatabad", 17.4125, 78.4600),
        ("Irrum Manzil", 17.4205, 78.4550),
        ("Punjagutta", 17.4260, 78.4520),
        ("Ameerpet Interchange", 17.4360, 78.4485),
        ("Begumpet", 17.4375, 78.4605),
        ("Prakash Nagar", 17.4390, 78.4715),
        ("Malakpet", 17.3735, 78.4930),
        ("New Market", 17.3685, 78.5020),
        ("Musarambagh", 17.3650, 78.5115),
        ("Dilsukhnagar", 17.3680, 78.5250),
        ("Chaitanyapuri", 17.3620, 78.5360)
    ],
    "ahmedabad": [
        ("Old High Court Interchange", 23.0360, 72.5685),
        ("Gandhigram", 23.0270, 72.5710),
        ("Paldi", 23.0145, 72.5665),
        ("Shreyas", 23.0070, 72.5530),
        ("Rajiv Nagar", 22.9980, 72.5440),
        ("Jivraj Park", 22.9915, 72.5350),
        ("APMC", 22.9810, 72.5255),
        ("Stadium", 23.0385, 72.5590),
        ("Commerce Six Road", 23.0395, 72.5510),
        ("Gujarat University", 23.0425, 72.5410),
        ("Gurukul Road", 23.0490, 72.5320),
        ("Doordarshan Kendra", 23.0535, 72.5230),
        ("Thaltej", 23.0515, 72.5140),
        ("Shahpur", 23.0365, 72.5805),
        ("Gheekanta", 23.0290, 72.5865),
        ("Kalupur Railway Station", 23.0285, 72.6005),
        ("Kankaria East", 23.0135, 72.6060),
        ("Apparel Park", 23.0105, 72.6160),
        ("Amraiwadi", 23.0070, 72.6240),
        ("Usmanpura", 23.0470, 72.5720),
        ("Vijay Nagar", 23.0570, 72.5740),
        ("Vadaj", 23.0645, 72.5760),
        ("Ranip", 23.0725, 72.5810)
    ],
    "pune": [
        ("District Court Interchange", 18.5290, 73.8560),
        ("Pune Railway Station", 18.5275, 73.8740),
        ("Mangalwar Peth", 18.5240, 73.8680),
        ("Ruby Hall Clinic", 18.5315, 73.8825),
        ("Bund Garden", 18.5375, 73.8900),
        ("Yerwada", 18.5490, 73.8920),
        ("Kalyani Nagar", 18.5495, 73.9040),
        ("PMC", 18.5245, 73.8510),
        ("Chhatrapati Sambhaji Udyan", 18.5195, 73.8450),
        ("Deccan Gymkhana", 18.5165, 73.8410),
        ("Garware College", 18.5110, 73.8340),
        ("Nal Stop", 18.5065, 73.8290),
        ("Ideal Colony", 18.5020, 73.8210),
        ("Anand Nagar", 18.4985, 73.8120),
        ("Vanaz", 18.4975, 73.8050),
        ("Shivaji Nagar", 18.5320, 73.8520),
        ("Budhwar Peth", 18.5190, 73.8570),
        ("Mandai", 18.5135, 73.8565),
        ("Swargate", 18.5015, 73.8580),
        ("Bopodi", 18.5680, 73.8320),
        ("Dapodi", 18.5750, 73.8260)
    ],
    "gurgaon": [
        ("Millennium City Centre Gurugram", 28.4593, 77.0725),
        ("IFFCO Chowk", 28.4720, 77.0725),
        ("MG Road", 28.4795, 77.0805),
        ("Sikanderpur Interchange", 28.4820, 77.0930),
        ("Guru Dronacharya", 28.4895, 77.1025),
        ("Phase 1", 28.4760, 77.0945),
        ("Sector 42-43", 28.4680, 77.0975),
        ("Sector 53-54", 28.4580, 77.1020),
        ("Sector 54 Chowk", 28.4485, 77.1070),
        ("Sector 55-56", 28.4370, 77.1120),
        ("Phase 2", 28.4880, 77.0890),
        ("Belvedere Towers", 28.4940, 77.0885),
        ("Cyber City", 28.4980, 77.0890),
        ("Moulsari Avenue", 28.5015, 77.0960),
        ("Phase 3", 28.4925, 77.1010)
    ]
}

def update_city(cid):
    if cid == "kolkata":
        print(f"[{cid}] Already 100% configured.")
        return

    meta_path = Path(f"data/{cid}/meta.json")
    if not meta_path.exists():
        return
    meta = json.load(open(meta_path, encoding='utf-8'))
    t_info = meta.get("tiles")
    if not t_info:
        return
    
    lon0, lat0 = t_info["lon0"], t_info["lat0"]
    dlon, dlat = t_info["dlon"], t_info["dlat"]
    tiles_dir = Path(f"data/{cid}/t")
    if not tiles_dir.exists():
        return

    ref_stations = CITY_METRO_REGISTRY.get(cid, [])
    # Also incorporate any cached metro elements for this city
    for p in Path('cache').glob('*.json'):
        try:
            cdata = json.load(open(p, encoding='utf-8'))
            for el in cdata.get('elements', []):
                tags = el.get('tags', {})
                name = tags.get('name:en') or tags.get('name')
                if not name: continue
                station = tags.get('station')
                r_tag = tags.get('railway')
                subway = tags.get('subway')
                if station == 'subway' or subway == 'yes' or r_tag == 'subway_entrance':
                    lat = el.get('lat') or (el.get('center') and el['center'].get('lat'))
                    lon = el.get('lon') or (el.get('center') and el['center'].get('lon'))
                    if lat and lon:
                        clean = re.sub(r'\s*Gate\s*[\w\d#.\s]+', '', name, flags=re.I)
                        clean = re.sub(r'\s*Metro\s*Station', '', clean, flags=re.I)
                        clean = re.sub(r'\s*Metro', '', clean, flags=re.I).strip()
                        if clean and len(clean) > 2:
                            ref_stations.append((clean, lat, lon))
        except Exception:
            pass

    # Read all existing tiles and POIs
    tile_data = {}
    stn_has_poi = {s[0]: False for s in ref_stations}
    total_metro = 0
    total_bus = 0
    stations_seen = set()

    for tile_file in sorted(tiles_dir.glob("*.bin")):
        buf = tile_file.read_bytes()
        if len(buf) < 20: continue
        v, nN, nE, nS, oldPoiLen = struct.unpack("<5I", buf[:20])
        if v != 2: continue

        poiOff = 20 + 4 * nN + 8 * nN + 4 * nE + 4 * nE + 4 * nE + 4 * (nE + 1) + 8 * nS
        graph_bytes = buf[:poiOff]
        pois = json.loads(buf[poiOff:poiOff+oldPoiLen].decode("utf-8"))

        new_pois = []
        for pt in pois:
            lon, lat, c = pt[0], pt[1], pt[2]
            wc = pt[3] if len(pt) > 3 else 0
            existing_name = pt[4] if len(pt) > 4 else ""

            if c == 6:
                best_stn = None
                min_d = 999999
                for sname, slat, slon in ref_stations:
                    d = haversine(lon, lat, slon, slat)
                    if d < min_d:
                        min_d = d
                        best_stn = sname

                if min_d <= 250:
                    new_pois.append([lon, lat, 6, wc, best_stn])
                    total_metro += 1
                    stations_seen.add(best_stn)
                    stn_has_poi[best_stn] = True
                else:
                    new_pois.append([lon, lat, 10, wc, "Bus Stop"])
                    total_bus += 1
            else:
                new_pois.append(pt)

        tile_data[tile_file] = (v, nN, nE, nS, graph_bytes, new_pois)

    # For any reference station that has no nearby POI in the existing tiles, inject a primary station point
    for sname, slat, slon in CITY_METRO_REGISTRY.get(cid, []):
        if not stn_has_poi.get(sname, False):
            ix = int(math.floor((slon - lon0) / dlon))
            iy = int(math.floor((slat - lat0) / dlat))
            target_tile = tiles_dir / f"{ix}_{iy}.bin"
            if target_tile in tile_data:
                v, nN, nE, nS, graph_bytes, pois = tile_data[target_tile]
                pois.append([round(slon, 5), round(slat, 5), 6, 1, sname])
                total_metro += 1
                stations_seen.add(sname)

    # Rewrite tiles
    for tile_file, (v, nN, nE, nS, graph_bytes, new_pois) in tile_data.items():
        new_poi_bytes = json.dumps(new_pois, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        new_header = struct.pack("<5I", v, nN, nE, nS, len(new_poi_bytes))
        updated_data = new_header + graph_bytes[20:] + new_poi_bytes
        tile_file.write_bytes(updated_data)

    # Update meta.json
    meta["cats"] = CATS
    meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print(f"[{cid.upper():10}] Updated {len(tile_data)} tiles: {total_metro} Metro POIs across {len(stations_seen)} stations | {total_bus} Bus stops")

def main():
    cities = json.load(open('data/cities.json', encoding='utf-8'))['cities']
    for c in cities:
        update_city(c['id'])

if __name__ == "__main__":
    main()
