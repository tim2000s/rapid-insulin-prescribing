"""Write ultra_share_by_year.csv for Denmark from provisional_share.csv (run provisional_share.py
first, which reads the medstat.dk package-level file pulled by medstat_pull.py).

Primary-sector rows (sector 100, community pharmacy sales to individuals) are used, as the closest
match to English primary-care dispensing; total (primary + hospital) is given in the note.
Volume is DDD; insulin DDD = 40 U, so the share of DDD equals the share of units.
Lyumjev has no Danish package in medstat.dk (not marketed), so lyumjev_pct is 0 by construction.
"""
import csv
rows = {(r["sector"], r["year"]): r for r in csv.DictReader(open("provisional_share.csv"))}
out = []
for (sec, y), r in sorted(rows.items()):
    if sec != "primary" or int(y) < 2017:
        continue
    a = float(r["all_kDDD"]); f = float(r["fiasp_kDDD"]); l = float(r["lyumjev_kDDD"])
    tot = rows[("total", y)]
    out.append([y, round(100 * (f + l) / a, 2), round(100 * f / a, 2), round(100 * l / a, 2),
                "DDD (40 U) = units, primary sector sales, medstat.dk",
                f"NovoRapid, Insulin aspart Sanofi (biosimilar), Humalog, Apidra, Fiasp; all {a:.0f}k DDD = {a*0.04:.0f} MU; "
                f"primary+hospital share {tot['ultra_share_pct']}%"])
w = csv.writer(open("ultra_share_by_year.csv", "w", newline=""))
w.writerow(["year", "ultra_pct", "fiasp_pct", "lyumjev_pct", "basis", "denominator_note"])
w.writerows(out)
for r in out: print(r[:4])
