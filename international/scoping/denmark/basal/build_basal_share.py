"""Long-acting analogue insulin shares, Denmark, from medstat.dk package-level sales.

Primary-sector rows (sector 100, community pharmacy) are used, as for the rapid-acting series in
../build_ultra_share.py, with primary + hospital (sector 300) given in the note. Volume is thousand
DDD; insulin DDD = 40 U, so units = kDDD x 40,000 and shares of DDD are shares of units.
basal_ddd_check.csv confirms that DDD per package equals the pack's units / 40 for each brand,
including Toujeo (300 U/ml) and Tresiba 200, so the 40 U equivalence holds across strengths.

Glargine 300 is separated from glargine 100 at package level by product name (Toujeo) and strength
(300 enheder/ml). Glargine 100 brands are Lantus, Abasaglar and Semglee. Run medstat_basal_pull.py
first. Writes basal_share_by_year.csv, basal_by_brand_year.csv (with turnover per 100 units),
basal_ddd_check.csv and basal_first_year.csv.
"""
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
look = {r["pkg"]: r for r in csv.DictReader(open(HERE / "basal_package_lookup.csv"))}


def brand_class(pkg, atc):
    r = look.get(pkg, {})
    n, s = r.get("product", "").lower(), r.get("strength", "")
    if atc == "A10AE06":
        return "Tresiba", "degludec"
    if atc == "A10AE05":
        return "Levemir", "detemir"
    if "toujeo" in n or s.startswith("300"):
        return "Toujeo", "glargine300"
    for b in ("lantus", "abasaglar", "semglee"):
        if b in n:
            return b.capitalize(), "glargine100"
    return (n or f"unlisted {pkg}"), "glargine100"


def f(x):
    return float(x) if x else 0.0


def main():
    vol = defaultdict(lambda: defaultdict(float))     # (sector, year) -> class -> kDDD
    br = defaultdict(lambda: [0.0, 0.0, 0.0])          # (year, brand, class) -> kpacks, kDDD, kDKK (primary)
    chk = defaultdict(lambda: [0.0, 0.0])
    for r in csv.DictReader(open(HERE / "basal_packages_by_year.csv")):
        b, c = brand_class(r["pkg"], r["atc"])
        if r["sector"] == "100":
            vol[("primary", r["year"])][c] += f(r["a2_volume_k"])
            k = br[(r["year"], b, c)]
            k[0] += f(r["a2_packages_k"]); k[1] += f(r["a2_volume_k"]); k[2] += f(r["a2_turnover_kdkk"])
            chk[r["pkg"]][0] += f(r["a2_packages_k"]); chk[r["pkg"]][1] += f(r["a2_volume_k"])
        elif r["sector"] == "300":
            vol[("total", r["year"])][c] += f(r["a3_volume_k"])

    with open(HERE / "basal_ddd_check.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg", "product", "strength", "pack_size", "kpacks_primary_2015_2025", "ddd_per_pack", "units_per_pack"])
        for p, (n, v) in sorted(chk.items(), key=lambda kv: -kv[1][0]):
            if n > 1:
                L = look.get(p, {})
                w.writerow([p, L.get("product"), L.get("strength"), L.get("pack_size"), round(n, 1),
                            round(v / n, 2), round(40 * v / n)])

    out = []
    for (sec, y), d in sorted(vol.items()):
        if sec != "primary" or int(y) < 2012:
            continue
        t = sum(d.values()); tt = vol[("total", y)]; T = sum(tt.values())
        g100 = {b: v[1] for (yy, b, c), v in br.items() if yy == y and c == "glargine100" and v[1] > 0}
        out.append(["Denmark", y] + [round(100 * d[k] / t, 2) for k in ("degludec", "glargine300", "glargine100", "detemir")]
                   + [round(t * 0.04, 1), "DDD (40 U) = units, primary sector sales (sector 100), medstat.dk package level",
                      "glargine 100 = " + ", ".join(f"{b} {100 * v / t:.1f}%" for b, v in sorted(g100.items()))
                      + f"; primary+hospital degludec {100 * tt['degludec'] / T:.1f}%, glargine 300 {100 * tt['glargine300'] / T:.1f}%"
                      + "; NPH, premixes, Xultophy (A10AE56) and Suliqua (A10AE54) excluded"])
    with open(HERE / "basal_share_by_year.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["country", "year", "degludec_pct", "glargine300_pct", "glargine100_pct", "detemir_pct",
                    "total_units_m", "basis", "note"])
        w.writerows(out)

    with open(HERE / "basal_by_brand_year.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "brand", "class", "kpacks", "units_m", "turnover_kdkk", "turnover_dkk_per_100u"])
        for (y, b, c), (n, v, m) in sorted(br.items()):
            if v > 0:
                w.writerow([y, b, c, round(n, 1), round(v * 0.04, 2), round(m, 1), round(m / (v * 40) * 100 * 1000 / 1000, 2)])
    first = {}
    for (y, b, c), v in sorted(br.items()):
        if v[1] > 0:
            first.setdefault(b, y)
    with open(HERE / "basal_first_year.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["brand", "first_medstat_primary_year"])
        for b, y in sorted(first.items()):
            w.writerow([b, f"{y} (series start)" if y == "2010" else y])
    for r in out:
        print(r[1:7])
    print(first)


if __name__ == "__main__":
    main()
