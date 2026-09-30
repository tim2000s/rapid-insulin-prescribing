"""Download the national Open Medic CIP13 tables (NB_<year>_cip13.CSV.gz) for 2017-2025.

The ameli open data site serves an index page per year whose links carry a session token;
the token is scraped from that page and the file fetched with it. Files go to raw/.
"""
import re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://open-data-assurance-maladie.ameli.fr/medicaments/"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
OUT = Path(__file__).parent / "raw"
OUT.mkdir(exist_ok=True)

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()

def fetch(year, suffix=""):
    name = f"NB_{year}_cip13{suffix}.CSV.gz"
    dest = OUT / name
    if dest.exists() and dest.stat().st_size > 1000:
        return name, dest.stat().st_size
    html = get(f"{BASE}download2.php?Dir_Rep={year}_CIP13").decode("latin-1")
    m = re.search(r'href="\./(download_file\.php\?token=[0-9a-f]+&file=[^"]*/' + re.escape(name) + ')"', html, re.I)
    if not m:
        return name, "not listed"
    dest.write_bytes(get(BASE + m.group(1)))
    return name, dest.stat().st_size

if __name__ == "__main__":
    years = range(2017, 2026)
    with ThreadPoolExecutor(7) as ex:
        for name, size in ex.map(fetch, years):
            print(name, size)
