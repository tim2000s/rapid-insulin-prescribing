"""Pull Swedish ATC-level rapid-acting analogue dispensing from Socialstyrelsen's statistics API.

Endpoint: https://sdb.socialstyrelsen.se/api/v1/sv/lakemedel/resultat/matt/{m}/atc/{atc}/region/0/kon/3/ar/{years}
Measures available: 1 patients, 3 dispensings (expedieringar). No DDD, no product dimension,
so this is a denominator only. Age groups are summed; patients summed over age groups is
valid because each person falls in a single age group within a year.
"""
import csv, json, os, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
B = "https://sdb.socialstyrelsen.se/api/v1/sv/lakemedel/resultat"
YEARS = ",".join(str(y) for y in range(2015, 2026))
out = defaultdict(float)
for m in (1, 3):
    for atc in ("A10AB04", "A10AB05", "A10AB06"):
        url = f"{B}/matt/{m}/atc/{atc}/region/0/kon/3/ar/{YEARS}"
        while url:
            d = json.load(urllib.request.urlopen(url, timeout=120))
            for r in d["data"]:
                out[(r["ar"], atc, m)] += float(r["varde"])
            url = d.get("nasta_sida")
with open(os.path.join(HERE, "socialstyrelsen_rapid_atc.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "atc", "patients", "dispensings"])
    for (y, a) in sorted({(k[0], k[1]) for k in out}):
        w.writerow([y, a, int(out[(y, a, 1)]), int(out[(y, a, 3)])])
