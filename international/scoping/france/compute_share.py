"""Provisional ultra-rapid share of rapid-acting analogue insulin units, France, Open Medic.

Input: raw/NB_<year>_cip13.CSV.gz (national, community-dispensed reimbursed boxes by CIP13),
fetched by fetch_open_medic.py. Units per box come from product_codes.csv, whose pack sizes were
read from the ANSM Base de donnees publique des medicaments (bdpm/CIS_CIP_bdpm.txt).
Premixed Humalog Mix25/Mix50 are excluded (ATC A10AD). Output: share_by_year.csv, printed table.
"""
import csv, gzip, io
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
codes = {r["cip13"]: r for r in csv.DictReader(open(HERE / "product_codes.csv"))}

rows_out, insulin_rows = [], []
for year in range(2017, 2026):
    f = HERE / "raw" / f"NB_{year}_cip13.CSV.gz"
    text = gzip.open(f).read().decode("latin-1")
    rdr = csv.reader(io.StringIO(text), delimiter=";")
    header = next(rdr)
    by_brand = defaultdict(lambda: [0, 0])  # boxes, units
    seen = set()
    for r in rdr:
        if r[0] in codes:
            boxes = int(r[5].replace(".", ""))
            c = codes[r[0]]
            by_brand[c["brand"]][0] += boxes
            by_brand[c["brand"]][1] += boxes * int(c["units_per_box"])
            seen.add(r[0])
            insulin_rows.append([year] + r)
    ultra = sum(v[1] for b, v in by_brand.items() if b in ("Fiasp", "Lyumjev"))
    total = sum(v[1] for v in by_brand.values())
    row = {"year": year, "total_units": total, "ultra_units": ultra,
           "ultra_share_pct": round(100 * ultra / total, 2)}
    for b in ["NovoRapid", "Humalog", "Apidra", "Insuline asparte Sanofi", "Fiasp", "Lyumjev"]:
        row[f"{b}_units"] = by_brand[b][1]
        row[f"{b}_boxes"] = by_brand[b][0]
    rows_out.append(row)

with open(HERE / "share_by_year.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_out[0]))
    w.writeheader(); w.writerows(rows_out)
with open(HERE / "open_medic_rapid_insulin_rows.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["year", "CIP13", "label", "nbc", "REM", "BSE", "BOITES"])
    w.writerows(insulin_rows)

print("year  total_MU  NovoRapid Humalog Apidra AspSanofi  Fiasp Lyumjev  ultra_MU  share%")
for r in rows_out:
    m = lambda k: r[k] / 1e6
    print(f"{r['year']}  {m('total_units'):8.1f}  {m('NovoRapid_units'):8.1f} {m('Humalog_units'):7.1f} "
          f"{m('Apidra_units'):6.1f} {m('Insuline asparte Sanofi_units'):8.1f}  {m('Fiasp_units'):6.1f} "
          f"{m('Lyumjev_units'):6.1f}  {m('ultra_units'):7.1f}  {r['ultra_share_pct']:6.2f}")
