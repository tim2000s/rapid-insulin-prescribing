"""Long-acting analogue insulin volumes and shares, France, from Open Medic (2017-2025).

Same basis as the rapid-acting series in ../compute_share.py: national community-pharmacy boxes
reimbursed by Assurance Maladie (all schemes), by CIP13, from ../raw/NB_<year>_cip13.CSV.gz, times
units per box. Units per box are in basal_codes.csv, read from the presentation wording in the ANSM
Base de donnees publique des medicaments (../bdpm/CIS_CIP_bdpm.txt), e.g. Toujeo SoloStar is
3 pens x 1.5 ml x 300 U/ml = 1350 U. The CIP13 list was built by scanning every Open Medic year for
insulin labels, so every long-acting analogue box reimbursed in 2017-2025 is either in the list or
is NPH, a premix or a fixed combination (Xultophy), which are excluded by design.

Writes:
  basal_share_by_year.csv      shares of long-acting analogue units (the requested table)
  basal_by_product_year.csv    boxes, units and Open Medic base de remboursement per brand-year
  basal_first_year.csv         first Open Medic year each brand appears, with the BDPM
                               commercialisation date of its earliest listed presentation
Open Medic starts in 2017, so a product already marketed then has first year '2017 (series start)'.
"""
import csv
import gzip
import io
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE.parent / "raw"
YEARS = range(2017, 2026)


def num(s):
    return float(s.replace(".", "").replace(",", "."))


def one_year(job):
    year, codes = job
    text = gzip.open(RAW / f"NB_{year}_cip13.CSV.gz").read().decode("latin-1")
    rdr = csv.reader(io.StringIO(text), delimiter=";")
    next(rdr)
    out = defaultdict(lambda: [0, 0, 0.0])  # boxes, units, BSE euro
    for r in rdr:
        c = codes.get(r[0])
        if c:
            boxes = int(r[5].replace(".", ""))
            k = (c["brand"], c["class"])
            out[k][0] += boxes
            out[k][1] += boxes * int(c["units_per_box"])
            out[k][2] += num(r[4])
    return year, dict(out)


def bdpm_dates():
    d = {}
    for line in open(HERE.parent / "bdpm" / "CIS_CIP_bdpm.txt", encoding="latin-1"):
        f = line.rstrip("\n").split("\t")
        if len(f) > 6:
            d[f[6]] = f[5]
    return d


def main():
    codes = {r["cip13"]: r for r in csv.DictReader(open(HERE / "basal_codes.csv"))}
    with ProcessPoolExecutor(7) as ex:
        res = dict(ex.map(one_year, [(y, codes) for y in YEARS]))

    rows, prod = [], []
    for y in YEARS:
        d = res[y]
        cls = defaultdict(int)
        for (b, c), v in d.items():
            cls[c] += v[1]
            prod.append([y, b, c, v[0], v[1], round(v[2], 2), round(v[2] / v[0], 2) if v[0] else ""])
        t = sum(cls.values())
        g100 = ", ".join(f"{b} {100 * v[1] / t:.1f}%" for (b, c), v in sorted(d.items()) if c == "glargine100")
        rows.append(["France", y] + [round(100 * cls[k] / t, 2) for k in ("degludec", "glargine300", "glargine100", "detemir")]
                    + [round(t / 1e6, 1), "insulin units (reimbursed boxes x units per box), Open Medic CIP13",
                       f"community pharmacy, Assurance Maladie all schemes; glargine 100 = {g100}; "
                       "NPH, premixes and Xultophy excluded; no Suliqua rows in Open Medic"])
    with open(HERE / "basal_share_by_year.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["country", "year", "degludec_pct", "glargine300_pct", "glargine100_pct", "detemir_pct",
                    "total_units_m", "basis", "note"])
        w.writerows(rows)
    with open(HERE / "basal_by_product_year.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "brand", "class", "boxes", "units", "bse_eur", "bse_per_box_eur"])
        w.writerows(sorted(prod))

    dates = bdpm_dates()
    first = {}
    for y in YEARS:
        for (b, c) in res[y]:
            first.setdefault(b, y)
    with open(HERE / "basal_first_year.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["brand", "first_open_medic_year", "earliest_bdpm_commercialisation_date"])
        for b in sorted({c["brand"] for c in codes.values()}):
            ds = [dates.get(k, "") for k, c in codes.items() if c["brand"] == b and dates.get(k)]
            ds = sorted(ds, key=lambda s: s[6:] + s[3:5] + s[:2])
            fy = first.get(b)
            w.writerow([b, "not dispensed 2017-2025" if fy is None else (f"{fy} (series start)" if fy == 2017 else fy),
                        ds[0] if ds else ""])
    for r in rows:
        print(r[1:7])


if __name__ == "__main__":
    main()
