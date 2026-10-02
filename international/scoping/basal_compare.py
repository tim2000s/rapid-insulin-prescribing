"""Degludec share of long-acting analogue units against ultra-rapid share of rapid-acting analogue
units, France, Denmark and Norway, by calendar year and by years since each product's first year
in the national series.

Inputs: <country>/basal/basal_share_by_year.csv (written by each country's basal script) and
<country>/ultra_share_by_year.csv (the existing ultra-rapid series; Norway has none, since FHI data
stop at ATC level and Fiasp shares A10AB05 with NovoRapid). Year 1 is the first calendar year with
nonzero volume: degludec France 2018, Denmark 2013, Norway 2014; Fiasp France 2018, Denmark 2017.
Writes basal_compare.csv.
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent


def series(path, col):
    if not path.exists():
        return {}
    return {r["year"]: float(r[col]) for r in csv.DictReader(open(path)) if r["year"].isdigit() and r[col] != ""}


def main():
    rows = []
    for c in ("france", "denmark", "norway"):
        b = HERE / c / "basal" / "basal_share_by_year.csv"
        deg, g300 = series(b, "degludec_pct"), series(b, "glargine300_pct")
        ultra = series(HERE / c / "ultra_share_by_year.csv", "ultra_pct")
        fiasp = series(HERE / c / "ultra_share_by_year.csv", "fiasp_pct")
        d0 = min((int(y) for y, v in deg.items() if v > 0), default=None)
        f0 = min((int(y) for y, v in fiasp.items() if v > 0), default=None)
        for y in sorted(set(deg) | set(ultra), key=int):
            Y = int(y)
            rows.append([c, Y, deg.get(y, ""), g300.get(y, ""), ultra.get(y, ""), fiasp.get(y, ""),
                         Y - d0 + 1 if d0 and Y >= d0 else "", Y - f0 + 1 if f0 and Y >= f0 else ""])
    with open(HERE / "basal_compare.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["country", "year", "degludec_pct", "glargine300_pct", "ultra_pct", "fiasp_pct",
                    "degludec_years_since_first", "fiasp_years_since_first"])
        w.writerows(rows)
    for c in ("france", "denmark", "norway"):
        R = [r for r in rows if r[0] == c]
        print(c)
        print(" by year since first:", "degludec", [(r[6], r[2]) for r in R if r[6] != ""][:10])
        print("                     ", "fiasp   ", [(r[7], r[5]) for r in R if r[7] != ""][:10])


if __name__ == "__main__":
    main()
