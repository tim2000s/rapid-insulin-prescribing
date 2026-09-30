"""Provisional ultra-rapid share for Denmark from medstat.dk package-level annual sales.

Volume unit is thousand DDD (insulin DDD = 40 U), so units = volume_k * 1000 * 40.
Sector 300 = total (primary + hospital), sector 100 = total primary sector.
"""
import csv
from collections import defaultdict

look = {r["pkg"]: r for r in csv.DictReader(open("rapid_package_lookup.csv"))}


def brand(pkg):
    n = look.get(pkg, {}).get("product", "UNKNOWN").lower()
    for b in ("fiasp", "lyumjev", "novorapid", "humalog", "apidra", "admelog", "trurapi"):
        if b in n:
            return b
    if "aspart" in n:
        return "aspart_sanofi"
    if "lispro" in n:
        return "lispro_sanofi"
    return n


tot = defaultdict(lambda: defaultdict(float))
units_seen = set()
for r in csv.DictReader(open("rapid_packages_by_year.csv")):
    units_seen.add(look.get(r["pkg"], {}).get("volume_unit"))
    if r["sector"] == "300":
        tot[("total", r["year"])][brand(r["pkg"])] += float(r["a3_volume_k"] or 0)
    elif r["sector"] == "100":
        tot[("primary", r["year"])][brand(r["pkg"])] += float(r["a2_volume_k"] or 0)
    elif r["sector"] == "200":
        tot[("hospital", r["year"])][brand(r["pkg"])] += float(r["a1_volume_k"] or 0)
print("volume units in lookup:", units_seen)
brands = ["novorapid", "fiasp", "aspart_sanofi", "humalog", "lyumjev", "apidra"]
w = csv.writer(open("provisional_share.csv", "w", newline=""))
w.writerow(["sector", "year"] + [b + "_kDDD" for b in brands] + ["other_kDDD", "all_kDDD", "all_MU", "ultra_share_pct"])
for (sec, y) in sorted(tot, key=lambda k: (k[0], k[1])):
    d = tot[(sec, y)]
    allv = sum(d.values())
    other = allv - sum(d.get(b, 0) for b in brands)
    ultra = d.get("fiasp", 0) + d.get("lyumjev", 0)
    share = 100 * ultra / allv if allv else float("nan")
    w.writerow([sec, y] + [round(d.get(b, 0), 1) for b in brands] + [round(other, 1), round(allv, 1), round(allv * 40 / 1000, 1), round(share, 2)])
    print(sec, y, " ".join(f"{b}={d.get(b,0):.1f}" for b in brands), f"other={other:.1f} all={allv:.1f}kDDD ultra={ultra:.1f} share={share:.2f}%")
