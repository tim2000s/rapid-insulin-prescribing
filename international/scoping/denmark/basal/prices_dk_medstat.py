"""Turnover per 100 units by brand, Denmark, primary sector, from medstat.dk (a2_turnover / a2_volume).

Turnover is medstat's primary-sector sales value in thousand DKK and volume is thousand DDD
(40 U), so DKK per 100 U = turnover_kDKK * 1000 / (volume_kDDD * 1000 * 40) * 100. This is an
average realised sales value across all packs and parallel imports in the year, not a list price;
medicinpriser.dk list prices, where captured, are in medicinpriser_prices.csv.
Inputs: basal_packages_by_year.csv (this folder) and ../rapid_packages_by_year.csv with lookups.
Writes prices_dk_medstat.csv.
"""
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def brand(name):
    n = name.lower()
    for b in ("fiasp", "lyumjev", "novorapid", "humalog", "apidra", "toujeo", "tresiba", "lantus",
              "abasaglar", "semglee", "levemir"):
        if b in n:
            return b.capitalize()
    return "Insulin aspart Sanofi" if "aspart" in n else name


def main():
    acc = defaultdict(lambda: [0.0, 0.0])
    for data, lk in [(HERE / "basal_packages_by_year.csv", HERE / "basal_package_lookup.csv"),
                     (HERE.parent / "rapid_packages_by_year.csv", HERE.parent / "rapid_package_lookup.csv")]:
        look = {r["pkg"]: r["product"] for r in csv.DictReader(open(lk))}
        for r in csv.DictReader(open(data)):
            if r["sector"] == "100" and r["a2_volume_k"] and r["a2_turnover_kdkk"]:
                k = (r["year"], brand(look.get(r["pkg"], r["pkg"])))
                acc[k][0] += float(r["a2_turnover_kdkk"]); acc[k][1] += float(r["a2_volume_k"])
    with open(HERE / "prices_dk_medstat.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "brand", "turnover_kdkk", "units_m", "dkk_per_100u"])
        for (y, b), (t, v) in sorted(acc.items()):
            if v > 0:
                w.writerow([y, b, round(t, 1), round(v * 0.04, 2), round(t * 1000 / (v * 40) * 100 / 1000, 2)])
    for (y, b), (t, v) in sorted(acc.items()):
        if y == "2025" and v > 0:
            print(b, round(t / (v * 40) * 100, 2))


if __name__ == "__main__":
    main()
