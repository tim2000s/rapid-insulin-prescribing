"""Extract insulin rows from every annual release of Medicare Part D Spending by Drug.

Source: the "Excel Reports including Historical Data" bundle on data.cms.gov (RY26), which holds
one workbook per release, DYT2016 to DYT2024. Each release covers five calendar years. It is
downloaded once to raw/ (git-ignored) and only the insulin rows are written out.

Why every release rather than DY24 alone: a release lists only the brand names present in its
latest year, so products that left the market drop out of later files even for the years in
which they sold. The original (pre-yfgn) Semglee of 2020-2021 is absent from DY24, for example.
build_basal_share.py therefore takes each brand-year from the latest release that contains it.

Part D Tot_Dsg_Unts (Total Dosage Units) for insulin is millilitres. Spending is gross drug
cost before manufacturer rebates, which CMS states it is prohibited from disclosing.

Output: partd_spending_insulin_releases.csv
        (release, year, brand, generic, n_mftr, spending, dsg_units_ml, claims, benes,
         avg_spend_per_unit). Run from this folder: python3 extract_partd_spending.py
"""
import io
import os
import re
import urllib.request
import zipfile
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

URL = ("https://data.cms.gov/sites/default/files/2026-06/Medicare%20Part%20D%20Spending%20by%20"
       "Drug-Excel%20Reports%20including%20Historical%20Data%20RY26.zip")
RAW = "raw/partd_spending_historical_RY26.zip"
UA = {"User-Agent": "Mozilla/5.0 (academic research; insulin utilisation analysis)"}
# Insulin products by generic name; devices, syringes, pumps and pen needles are dropped
KEEP = re.compile(r"insulin|degludec|glargine|detemir", re.I)
# ("Insulin Aspart/B3/Pump Cart" is Fiasp PumpCart and is kept; Omnipod generics are dropped)
DROP = re.compile(r"syr|needle|suppl|device|pen,|pmp|insulin pump|pump cart,|bolus insulin", re.I)
FIELDS = {"Total Spending": "spending", "Total Dosage Units": "dsg_units_ml",
          "Total Claims": "claims", "Total Beneficiaries": "benes",
          "Average Spending Per Dosage Unit (Weighted)": "avg_spend_per_unit"}


def download():
    if not os.path.exists(RAW):
        os.makedirs("raw", exist_ok=True)
        req = urllib.request.Request(URL, headers=UA)
        with urllib.request.urlopen(req, timeout=600) as r, open(RAW, "wb") as f:
            f.write(r.read())


def parse(inner):
    """Parse one release workbook (inner zip name) into long rows."""
    with zipfile.ZipFile(RAW) as outer:
        inner_bytes = outer.read(inner)
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as z:
        xl = [n for n in z.namelist() if n.lower().endswith(".xlsx")][0]
        book = z.read(xl)
    release = int(re.search(r"DYT(\d{4})", inner).group(1))
    x = pd.ExcelFile(io.BytesIO(book))
    sheet = [s for s in x.sheet_names if s.startswith("Spending")][0]
    d = x.parse(sheet, header=None)
    hdr = d.index[d[0].astype(str).str.strip() == "Brand Name"][0]
    years = d.iloc[hdr - 1].ffill()
    names = d.iloc[hdr].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    body = d.iloc[hdr + 1:]
    body = body[body[1].astype(str).str.contains(KEEP) & ~body[1].astype(str).str.contains(DROP)]
    rows = []
    for _, r in body.iterrows():
        rec = {}
        for c in d.columns[3:]:
            m = re.search(r"(\d{4})", str(years[c]))
            if not m or names[c] not in FIELDS:
                continue
            rec.setdefault(int(m.group(1)), {})[FIELDS[names[c]]] = r[c]
        for y, v in rec.items():
            rows.append(dict(release=release, year=y, brand=str(r[0]).strip(),
                             generic=str(r[1]).strip(), n_mftr=r[2], **v))
    return rows


def main():
    download()
    with zipfile.ZipFile(RAW) as z:
        inners = sorted(n for n in z.namelist() if n.endswith(".zip"))
    with ProcessPoolExecutor(7) as ex:
        rows = [r for res in ex.map(parse, inners) for r in res]
    out = pd.DataFrame(rows)
    for c in FIELDS.values():
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.sort_values(["brand", "year", "release"])
    out.to_csv("partd_spending_insulin_releases.csv", index=False)
    print(out.groupby("release").agg(rows=("brand", "size"), years=("year", lambda s: f"{s.min()}-{s.max()}")))


if __name__ == "__main__":
    main()
