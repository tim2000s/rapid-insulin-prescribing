"""Pull national (state = XX) Medicaid State Drug Utilization Data rows for
rapid-acting and related insulin products, 2017 to 2026, from the
data.medicaid.gov DKAN datastore API. One dataset per year; the identifiers
come from the metastore catalogue (medicaid_catalog.json).

Output: medicaid_sdud_insulin_XX.csv (one row per NDC x quarter x
utilisation type; FFSU = fee for service, MCOU = managed care)."""
import json, urllib.parse, urllib.request, csv, time
from concurrent.futures import ThreadPoolExecutor

YEARS = {
    2017: "776a3880-a62d-5990-8b40-4406e6861dbb",
    2018: "a1f3598e-fc71-51aa-8560-78e7e1a61b09",
    2019: "daba7980-e219-5996-9bec-90358fd156f1",
    2020: "cc318bfb-a9b2-55f3-a924-d47376b32ea3",
    2021: "eec7fbe6-c4c4-5915-b3d0-be5828ef4e9d",
    2022: "200c2cba-e58d-4a95-aa60-14b99736808d",
    2023: "d890d3a9-6b00-43fd-8b31-fcba4c8e2909",
    2024: "61729e5a-7aa8-448c-8903-ba3e0cd0ea3c",
    2025: "158a1baa-5506-400a-8ec3-97756f0b0536",
    2026: "2957a7f9-9a15-453e-9afd-3bbdcbac8fd3",
}
# product_name is truncated to about ten characters in SDUD
PATTERNS = ["FIASP%", "LYUMJEV%", "NOVOLOG%", "HUMALOG%", "ADMELOG%", "APIDRA%",
            "INSULIN%", "KIRSTY%", "MERILOG%", "RELION%"]
BASE = "https://data.medicaid.gov/api/1/datastore/query/{}/0"


def fetch(job):
    year, dsid, pat = job
    rows, offset = [], 0
    while True:
        q = {"limit": 500, "offset": offset,
             "conditions[0][property]": "product_name", "conditions[0][value]": pat,
             "conditions[0][operator]": "like",
             "conditions[1][property]": "state", "conditions[1][value]": "XX"}
        url = BASE.format(dsid) + "?" + urllib.parse.urlencode(q)
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    d = json.load(r)
                break
            except Exception as e:
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"failed {year} {pat}")
        res = d["results"]
        rows += res
        offset += len(res)
        if not res or offset >= d["count"]:
            break
    return rows


if __name__ == "__main__":
    jobs = [(y, i, p) for y, i in YEARS.items() for p in PATTERNS]
    out = []
    with ThreadPoolExecutor(7) as ex:
        for rows in ex.map(fetch, jobs):
            out += rows
    keys = sorted({k for r in out for k in r})
    with open("medicaid_sdud_insulin_XX.csv", "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(out)
    print(len(out), "rows")
