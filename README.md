# 15 minutes. For whom? — Kolkata

> **Made by VR Lab**  
> *Indian Institute of Technology Kharagpur (IIT KGP)*  
> GitHub: [@anshulsinghrs](https://github.com/anshulsinghrs)

An interactive map of Kolkata that shows how far you can walk in a given time, and how that changes with walking speed and with avoiding stairs. The same 15 minutes reach very different places for different people.

This is a Kolkata adaptation of [martincantcode/15-minutes](https://github.com/martincantcode/15-minutes) by Martin Bangratz (MIT licence).

Click the map to set a starting point, then adjust:

- **Time budget** (5 to 30 minutes)
- **Walking speed** (0.8 to 1.8 m/s)
- **Avoid stairs** (step-free)

Streets you can reach are coloured by walking time. Streets that would be reachable at 1.4 m/s with stairs allowed, but not with your settings, are grey. The panel counts groceries, health, education, parks and playgrounds, cafés and restaurants, benches and stations within reach.

## Coverage

A 24 × 24 km square centred on 22.55° N, 88.36° E: Kolkata Municipal Corporation, most of Howrah, Salt Lake / Bidhannagar and the edge of New Town. Change `--center` and `--radius` in `.github/workflows/export-kolkata.yml` to cover a different area.

## Getting the data

The street and amenity data in `data/kolkata/` is produced by `export_city.py` from OpenStreetMap. The **Export Kolkata data** GitHub Action runs it and commits the result:

- it runs automatically when `export_city.py` or the workflow file changes, or
- run it from the **Actions** tab → *Export Kolkata data* → *Run workflow* (you can set the radius and tile size there).

To run it on your own computer instead:

```
pip install osmnx
python export_city.py "Kolkata, West Bengal, India" kolkata --name Kolkata --center 22.55,88.36 --radius 12000 --tile-km 2.5
```

If the free Overpass servers answer 504, try a smaller `--radius` or add `--overpass https://overpass.private.coffee/api`.

## Run it

```
python3 -m http.server 8000
```

Then open <http://localhost:8000>. (Opening `index.html` directly does not work, because the page has to load the data files.)

To publish it, enable GitHub Pages for the repository (Settings → Pages → deploy from branch, root folder).

## Limits

- Public transport travel, slope, lighting, waterlogging and footpath encroachment are not included.
- OpenStreetMap data for Kolkata is incomplete in places, especially for footpaths, steps and wheelchair tags. Stations count as step-free only if OpenStreetMap tags them `wheelchair=yes`.
- Amenities are matched to the nearest street intersection, so counts near the edge of the reach are approximate.

## Data and licences

Street, amenity and station data: © OpenStreetMap contributors, under the Open Database Licence (<https://www.openstreetmap.org/copyright>). Basemap: © OpenFreeMap, © OpenMapTiles, data from OpenStreetMap.

The code is under the MIT licence (see `LICENSE`). `vendor/` holds unmodified copies of MapLibre GL JS (BSD-3-Clause) and the leaflet-maplibre-gl bridge (ISC), with their licence files. Leaflet is loaded from cdnjs.
