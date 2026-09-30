"""Extract A10AB04/05/06 rows from the GIPdatabank 'farmacie Zvw meerjaren' open data files.

The files are ATC5-level only (every atclaatst code is 7 characters), so they give a denominator
and cannot separate Fiasp from NovoRapid or Lyumjev from Humalog. 2017-2020 are taken from the
2017-2021 vintage and 2021-2025 from the 2021-2025 vintage, since later vintages revise earlier years.
Insulin units = DDD x 40 (WHO DDD for insulin is 40 U).
"""
import csv
from pathlib import Path
HERE = Path(__file__).parent
out = []
for fn, years in [("gip_farmacie_zvw_meerjaren_2017_2021.csv", range(2017, 2021)),
                  ("gip_farmacie_meerjaren_2021-2025.csv", range(2021, 2026))]:
    for r in csv.reader(open(HERE / fn, encoding="latin-1"), delimiter="#"):
        r = [x.strip() for x in r]
        if r[1] in ("A10AB04", "A10AB05", "A10AB06") and int(r[0]) in years:
            out.append([r[0], r[1], r[2], r[4], r[5], r[6], int(r[6]) * 40])
with open(HERE / "gip_rapid_analogue_atc_2017_2025.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["year", "atc", "name", "users", "dispensings", "DDD", "units_DDDx40"]); w.writerows(out)
for y in range(2017, 2026):
    print(y, sum(r[6] for r in out if r[0] == str(y)) / 1e9, "billion units")
