"""Write ultra_share_by_year.csv for France.

Calendar years 2017-2025 come from share_by_year.csv (compute_share.py, Open Medic CIP13
tables). The final row is the twelve months July 2025 to June 2026 from the Medic'AM monthly
CIP13 extract (medicam_monthly.py writes medicam/medicam_rapid_insulin_rows.csv), labelled
as a period rather than a year. Units = reimbursed boxes x units per box (product_codes.csv).
Run compute_share.py and medicam_monthly.py first.
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent
NOTE = ("community pharmacy, reimbursed by Assurance Maladie (all schemes); denominator NovoRapid, "
        "Humalog incl. U200, Apidra, Insuline asparte Sanofi (biosimilar), Fiasp, Lyumjev; mixes excluded")
rows = []
for r in csv.DictReader(open(HERE / "share_by_year.csv")):
    t = int(r["total_units"])
    f, l = int(r["Fiasp_units"]), int(r["Lyumjev_units"])
    rows.append([r["year"], round(100 * (f + l) / t, 2), round(100 * f / t, 2), round(100 * l / t, 2),
                 "insulin units (reimbursed boxes x units per box), Open Medic", NOTE])

codes = {r["cip13"]: r for r in csv.DictReader(open(HERE / "product_codes.csv"))}
u = {"Fiasp": 0, "Lyumjev": 0, "all": 0}
for r in csv.DictReader(open(HERE / "medicam" / "medicam_rapid_insulin_rows.csv")):
    c = codes[r["cip13"]]
    n = int(r["boxes"]) * int(c["units_per_box"])
    u["all"] += n
    if c["brand"] in u:
        u[c["brand"]] += n
t = u["all"]
rows.append(["2025-07 to 2026-06", round(100 * (u["Fiasp"] + u["Lyumjev"]) / t, 2),
             round(100 * u["Fiasp"] / t, 2), round(100 * u["Lyumjev"] / t, 2),
             "insulin units (reimbursed boxes x units per box), Medic'AM monthly", NOTE])

with open(HERE / "ultra_share_by_year.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["year", "ultra_pct", "fiasp_pct", "lyumjev_pct", "basis", "denominator_note"])
    w.writerows(rows)
for r in rows:
    print(r[:4])
