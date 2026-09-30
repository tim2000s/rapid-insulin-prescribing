"""Write ultra_share_by_year.csv for Australia (PBS), financial years July to June.

Input: dos_pharmacytype_rapid_2020_2026.csv (trim_dos.py, from the PBS Date of Supply
supplementary files by pharmacy type). Basis is PBS prescriptions, all patient categories,
above and under co-payment. Units are not observed in these files (see provisional_share.py
for an estimate under an assumed five packs per prescription).
Fiasp items: 11705C vial, 11706D FlexTouch (both last supplied Sep 2023), 13651L Penfill (from Oct 2023).
Lyumjev is not PBS-listed, so lyumjev_pct is 0 by construction and private scripts are not seen.
"""
import csv, collections
FIASP = {"11705C", "11706D", "13651L"}
s = collections.Counter(); f = collections.Counter()
for r in csv.DictReader(open("dos_pharmacytype_rapid_2020_2026.csv")):
    m = int(r["MONTH_OF_SUPPLY"]); fy = m // 100 + (1 if m % 100 >= 7 else 0)
    n = int(r["PRESCRIPTIONS"]); s[fy] += n
    if r["ITEM_CODE"] in FIASP: f[fy] += n
w = csv.writer(open("ultra_share_by_year.csv", "w", newline=""))
w.writerow(["year", "ultra_pct", "fiasp_pct", "lyumjev_pct", "basis", "denominator_note"])
for fy in sorted(s):
    p = round(100 * f[fy] / s[fy], 2)
    row = [f"FY{fy-1}-{fy%100:02d}", p, p, 0.0, "PBS prescriptions (Section 85, date of supply)",
           f"all PBS rapid-acting analogue items (NovoRapid, Humalog incl. U200, Apidra, Fiasp); n={s[fy]}; Lyumjev not PBS-listed"]
    w.writerow(row); print(row[:4], s[fy])
