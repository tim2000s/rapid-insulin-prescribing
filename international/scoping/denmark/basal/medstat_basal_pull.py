"""Pull medstat.dk package-level annual sales for long-acting analogue insulins (A10AE04 glargine,
A10AE05 detemir, A10AE06 degludec), 2010-2025, the same source and layout as ../medstat_pull.py
uses for the rapid-acting series.

Source: Sundhedsdatastyrelsen, medstat.dk bulk download; files addressed by base64 of the name.
The package lookup is read from ../raw/product_name_text.txt.gz (cached by the rapid pull) and
filtered to the same ATC codes, Danish-language rows. One thread per year, at most 7.
Writes basal_packages_by_year.csv and basal_package_lookup.csv.
"""
import base64
import csv
import gzip
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/126"}
ATC = ("A10AE04", "A10AE05", "A10AE06")
YEARS = range(2010, 2026)
COLS = ["atc", "year", "sector", "pkg", "a1_packages_k", "a1_volume_k", "a1_turnover_kdkk",
        "a2_packages_k", "a2_packages_reimb_k", "a2_volume_k", "a2_turnover_kdkk",
        "a2_reimb_kdkk", "a3_packages_k", "a3_volume_k"]


def get(name):
    url = "https://medstat.dk/en/download/file/" + base64.b64encode(name.encode()).decode()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        return r.read().decode("utf-8", errors="replace")


def year_rows(y):
    rows = [l.rstrip(";").split(";")[:14] for l in get(f"{y}_product_name_data.txt").splitlines() if l.startswith(ATC)]
    print(y, len(rows), file=sys.stderr)
    return rows


def main():
    txt = gzip.open(HERE.parent / "raw" / "product_name_text.txt.gz").read().decode("utf-8", errors="replace")
    lookup = [l.split(";") for l in txt.splitlines() if l.startswith(ATC)]
    lookup = [r for r in lookup if len(r) > 14 and r[14] == "0"]
    with open(HERE / "basal_package_lookup.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["atc", "pkg", "product", "holder", "form", "strength", "pack_size", "status_end_2025",
                    "dispensing", "change", "volume_unit", "note", "reimbursement", "subst_group"])
        for r in lookup:
            w.writerow(r[:14])
    with ThreadPoolExecutor(7) as ex:
        allrows = [r for rows in ex.map(year_rows, YEARS) for r in rows]
    with open(HERE / "basal_packages_by_year.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in allrows:
            w.writerow(r + [""] * (14 - len(r)))


if __name__ == "__main__":
    main()
