#!/usr/bin/env python3
"""
Hospital supply of rapid-acting insulin in England, from two NHSBSA datasets.

Hospital prescribing dispensed in the community (HPDC), December 2016 onwards. Prescriptions written
by hospital trust prescribers (FP10(HP) and equivalents) and dispensed by community pharmacies. It
is coded by BNF presentation, so brands and devices are distinguishable and the same units-per-
device arithmetic as the primary care pipeline applies. One CSV per month, about 25 MB each and not
loaded into the portal's SQL store, so each file is downloaded, filtered to BNF 0601011 (short-
acting insulins) and discarded.

Secondary Care Medicines Data (SCMD, finalised), April 2019 to March 2026. Hospital pharmacy stock
issues to wards, clinics and outpatients, by trust. It is coded by dm+d VMP, and dm+d has one VMP
per molecule, strength and device: Lyumjev and Humalog share "Insulin lispro 100units/ml solution
for injection 3ml pre-filled disposable devices", Fiasp and NovoRapid share the aspart equivalent.
SCMD therefore gives hospital volume by molecule and cannot give an ultra-rapid share. Its quantity
is in the VMP unit of measure, which is ml for every insulin here, so units are quantity times
concentration.

    python3 hospital_source.py        # fill hospital_cache/, resumable
"""
import argparse
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

PORTAL = "https://opendata.nhsbsa.net/api/3/action"
CACHE = Path(__file__).parent / "hospital_cache"
HPDC_PACKAGE = "hospital-prescribing-dispensed-in-the-community"
SCMD_PACKAGE = "finalised-secondary-care-medicines-data-scmd-with-indicative-price"
SCMD_MOLECULES = ("Insulin lispro", "Insulin aspart", "Insulin glulisine")


def resources(package):
    r = requests.get(f"{PORTAL}/package_show", params={"id": package}, timeout=120).json()
    return sorted((x["name"], x["url"]) for x in r["result"]["resources"])


def retry(fn, *a, tries=5):
    for attempt in range(tries):
        try:
            return fn(*a)
        except Exception as e:  # network or portal errors; a malformed query fails every attempt
            last = e
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"{a}: {last}")


def hpdc_month(name, url, cache):
    out = cache / "hpdc" / f"{name}.csv"
    if out.exists():
        return name, None

    def fetch():
        r = requests.get(url, timeout=600)
        r.raise_for_status()
        return r.content

    raw = retry(fetch)
    df = pd.read_csv(io.BytesIO(raw), dtype=str)
    # November 2024 to April 2025 use spaces in the column names instead of underscores.
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df = df[df.BNF_CODE.str.startswith("0601011", na=False)]
    df.to_csv(out, index=False)
    return name, len(df)


def scmd_sql(res, sql):
    j = requests.get(f"{PORTAL}/datastore_search_sql", params={"resource_id": res, "sql": sql}, timeout=600).json()
    if not j.get("success"):
        raise RuntimeError(j.get("error"))
    r = j["result"]
    return r["result"]["records"] if "result" in r else r["records"]


def scmd_month(name, cache):
    out = cache / "scmd" / f"{name}.json"
    if out.exists():
        return name, None
    where = " OR ".join(f"VMP_PRODUCT_NAME LIKE '{m}%'" for m in SCMD_MOLECULES)
    sql = (f"SELECT YEAR_MONTH, ODS_CODE, VMP_SNOMED_CODE, VMP_PRODUCT_NAME, UNIT_OF_MEASURE_NAME, "
           f"SUM(CAST(TOTAL_QUANITY_IN_VMP_UNIT AS FLOAT64)) AS quantity, "
           f"SUM(CAST(INDICATIVE_COST AS FLOAT64)) AS indicative_cost "
           f"FROM `{name}` WHERE {where} "
           f"GROUP BY YEAR_MONTH, ODS_CODE, VMP_SNOMED_CODE, VMP_PRODUCT_NAME, UNIT_OF_MEASURE_NAME")
    rows = retry(scmd_sql, name, sql)
    out.write_text(json.dumps(rows))
    return name, len(rows)


def fill_cache(cache=CACHE, workers=7):
    for sub in ("hpdc", "scmd"):
        (cache / sub).mkdir(parents=True, exist_ok=True)
    hp = resources(HPDC_PACKAGE)
    sc = [n for n, _ in resources(SCMD_PACKAGE) if n.startswith("SCMD_FINAL_")]
    print(f"HPDC {len(hp)} months ({hp[0][0]} to {hp[-1][0]}); SCMD {len(sc)} months ({sc[0]} to {sc[-1]})")
    with ThreadPoolExecutor(workers) as ex:
        jobs = [ex.submit(hpdc_month, n, u, cache) for n, u in hp] + [ex.submit(scmd_month, n, cache) for n in sc]
        for j in jobs:
            name, n = j.result()
            if n is not None:
                print(f"  {name:32s} {n:6d} rows", flush=True)

    hpdc = pd.concat([pd.read_csv(f, dtype=str) for f in sorted((cache / "hpdc").glob("*.csv"))], ignore_index=True)
    hpdc.to_csv(cache / "hpdc_insulin.csv", index=False)
    scmd = pd.concat([pd.DataFrame(json.loads(f.read_text())) for f in sorted((cache / "scmd").glob("*.json"))],
                     ignore_index=True)
    scmd.to_csv(cache / "scmd_insulin.csv", index=False)
    print(f"hpdc_insulin.csv {len(hpdc):,} rows; scmd_insulin.csv {len(scmd):,} rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fill the hospital insulin cache from the NHSBSA open data portal.")
    ap.add_argument("--cache", type=Path, default=CACHE)
    ap.add_argument("--workers", type=int, default=7)
    a = ap.parse_args()
    fill_cache(a.cache, a.workers)
