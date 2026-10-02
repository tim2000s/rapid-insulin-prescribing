"""List price per 100 units, France, long-acting and rapid-acting analogue insulins.

Two bases, both public:
  bdpm: 'prix du medicament' per box (euro, excluding the 1.02 euro dispensing fee) from the ANSM
        Base de donnees publique des medicaments, ../bdpm/CIS_CIP_bdpm.txt (downloaded 2026-09-30).
        This is the current regulated public price.
  open_medic_2025: base de remboursement (BSE) per reimbursed box in Open Medic 2025, from
        basal_by_product_year.csv and the rapid rows; it includes dispensing fees, so it sits a little
        above the bdpm figure.
Units per box from basal_codes.csv and ../product_codes.csv. Writes prices_fr.csv.
"""
import csv
import gzip
import io
from pathlib import Path

HERE = Path(__file__).parent


def main():
    codes = {r["cip13"]: r for r in csv.DictReader(open(HERE / "basal_codes.csv"))}
    for r in csv.DictReader(open(HERE.parent / "product_codes.csv")):
        codes[r["cip13"]] = dict(r, **{"class": "rapid " + r["group"]})
    bd = {}
    for line in open(HERE.parent / "bdpm" / "CIS_CIP_bdpm.txt", encoding="latin-1"):
        f = line.rstrip("\n").split("\t")
        if len(f) > 9 and f[6] in codes:
            bd[f[6]] = (f[9].replace(",", "."), f[4])
    om = {}
    text = gzip.open(HERE.parent / "raw" / "NB_2025_cip13.CSV.gz").read().decode("latin-1")
    rdr = csv.reader(io.StringIO(text), delimiter=";")
    next(rdr)
    for r in rdr:
        if r[0] in codes:
            boxes = int(r[5].replace(".", ""))
            bse = float(r[4].replace(".", "").replace(",", "."))
            om[r[0]] = (boxes, bse)
    out = []
    for k, c in codes.items():
        u = int(c["units_per_box"])
        p, state = bd.get(k, ("", ""))
        b = om.get(k)
        out.append([c["brand"], c["class"], c["presentation"], k, u, p,
                    round(100 * float(p) / u, 3) if p else "",
                    b[0] if b else 0,
                    round(100 * b[1] / b[0] / u, 3) if b and b[0] else "", state])
    out.sort(key=lambda r: (r[1], r[0], -r[7]))
    with open(HERE / "prices_fr.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["brand", "class", "presentation", "cip13", "units_per_box", "bdpm_price_eur",
                    "bdpm_eur_per_100u", "boxes_2025", "open_medic_2025_bse_eur_per_100u", "bdpm_status"])
        w.writerows(out)
    for r in out:
        print(r[0], r[2][:28], r[6], r[8], r[7])


if __name__ == "__main__":
    main()
