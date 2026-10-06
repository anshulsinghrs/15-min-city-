#!/usr/bin/env python3
import subprocess
import sys
import time

cities = [
    {
        "slug": "bengaluru",
        "name": "Bengaluru",
        "place": "Bengaluru, Karnataka, India",
        "center": "12.9716,77.5946",
        "radius": 6000,
        "tile_km": 2.5
    },
    {
        "slug": "chennai",
        "name": "Chennai",
        "place": "Chennai, Tamil Nadu, India",
        "center": "13.0827,80.2707",
        "radius": 6000,
        "tile_km": 2.5
    },
    {
        "slug": "delhi",
        "name": "New Delhi",
        "place": "New Delhi, Delhi, India",
        "center": "28.6139,77.2090",
        "radius": 6000,
        "tile_km": 2.5
    },
    {
        "slug": "mumbai",
        "name": "Mumbai",
        "place": "Mumbai, Maharashtra, India",
        "center": "18.9388,72.8354",
        "radius": 6000,
        "tile_km": 2.5
    },
    {
        "slug": "hyderabad",
        "name": "Hyderabad",
        "place": "Hyderabad, Telangana, India",
        "center": "17.3850,78.4867",
        "radius": 6000,
        "tile_km": 2.5
    },
    {
        "slug": "pune",
        "name": "Pune",
        "place": "Pune, Maharashtra, India",
        "center": "18.5204,73.8567",
        "radius": 6000,
        "tile_km": 2.5
    },
    {
        "slug": "gurgaon",
        "name": "Gurgaon",
        "place": "Gurgaon, Haryana, India",
        "center": "28.4595,77.0266",
        "radius": 6000,
        "tile_km": 2.5
    }
]

print(f"Starting batch export for {len(cities)} cities...")

for idx, c in enumerate(cities, 1):
    import os
    if os.path.exists(f"data/{c['slug']}/meta.json"):
        print(f"[{idx}/{len(cities)}] {c['name']} ({c['slug']}) already exported, skipping.")
        continue

    print(f"\n=======================================================")
    print(f"[{idx}/{len(cities)}] Exporting {c['name']} ({c['slug']})...")
    print(f"=======================================================")
    
    cmd = [
        sys.executable,
        "export_city.py",
        c["place"],
        c["slug"],
        "--name", c["name"],
        "--center", c["center"],
        "--radius", str(c["radius"]),
        "--tile-km", str(c["tile_km"])
    ]
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        print(f"Attempt {attempt}/{max_retries} for {c['name']}...")
        result = subprocess.run(cmd)
        if result.returncode == 0:
            print(f"Successfully exported {c['name']}!")
            break
        else:
            print(f"Export for {c['name']} failed with code {result.returncode}.")
            if attempt < max_retries:
                print("Waiting 30 seconds before retrying...")
                time.sleep(30)
            else:
                print(f"Giving up on {c['name']} after {max_retries} attempts.")
    
    # Polite pause between cities to avoid aggressive rate limiting from Overpass
    print("Pausing 10 seconds before next city...")
    time.sleep(10)

print("\nAll batch exports completed!")
