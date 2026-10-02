"""Pull national (state = XX) Medicaid State Drug Utilization Data rows for the branded
long-acting analogue insulins, 2015 to 2026, by the same method as ../pull_medicaid_sdud.py
(data.medicaid.gov DKAN datastore, one dataset per year, product_name LIKE pattern).

The cached rapid-acting extract (../medicaid_sdud_insulin_XX.csv) was pulled with the pattern
INSULIN%, so it already holds the unbranded long-acting products (insulin glargine, glargine-yfgn,
degludec) but none of the branded ones. This script fetches the branded names and also re-pulls
INSULIN% so that the basal extract is self-contained.

Output: medicaid_sdud_basal_XX.csv (one row per NDC x quarter x utilisation type).
Run from this folder: python3 pull_medicaid_sdud_basal.py
"""
import csv
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pull_medicaid_sdud import YEARS as YEARS_2017_ON, fetch  # noqa: E402

# 2015 and 2016 are added (identifiers from ../medicaid_catalog.json) so that the series
# reaches back to the US launches of Toujeo (2015) and Tresiba (January 2016).
YEARS = {2015: "2fed5758-5fd6-5dbb-8f92-34b3a0c3c8dd", 2016: "53cf9f05-97e3-5bd6-a237-bc971e3642d9",
         **YEARS_2017_ON}

# product_name is truncated to about ten characters in SDUD; LIKE matching is case-insensitive
PATTERNS = ["TRESIBA%", "TOUJEO%", "LANTUS%", "BASAGLAR%", "SEMGLEE%", "REZVOGLAR%",
            "LEVEMIR%", "INSULIN%"]


def main():
    jobs = [(y, i, p) for y, i in YEARS.items() for p in PATTERNS]
    out = []
    with ThreadPoolExecutor(7) as ex:
        for rows in ex.map(fetch, jobs):
            out += rows
    keys = sorted({k for r in out for k in r})
    with open("medicaid_sdud_basal_XX.csv", "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(out)
    print(len(out), "rows")


if __name__ == "__main__":
    main()
