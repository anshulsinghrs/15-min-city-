import urllib.request
import time
import os

url = "https://download.bbbike.org/osm/bbbike/NewDelhi/NewDelhi.osm.gz"
dest = "NewDelhi.osm.gz"

print(f"Downloading {url} to {dest}...")
t0 = time.time()

req = urllib.request.Request(url, headers={'User-Agent': '15MinCityUrbanResearch/2.0'})
with urllib.request.urlopen(req) as resp, open(dest, 'wb') as out:
    total = int(resp.headers.get('Content-Length', 0))
    downloaded = 0
    chunk_size = 1024 * 512
    last_print = t0
    while True:
        chunk = resp.read(chunk_size)
        if not chunk:
            break
        out.write(chunk)
        downloaded += len(chunk)
        now = time.time()
        if now - last_print > 3:
            pct = (downloaded / total * 100) if total else 0
            mb = downloaded / (1024 * 1024)
            speed = mb / (now - t0)
            print(f"  {mb:.1f} MB / {total/(1024*1024):.1f} MB ({pct:.1f}%) at {speed:.2f} MB/s...")
            last_print = now

elapsed = time.time() - t0
sz_mb = os.path.getsize(dest) / (1024 * 1024)
print(f"DONE! Downloaded {sz_mb:.1f} MB in {elapsed:.1f}s ({sz_mb/elapsed:.2f} MB/s).")
