#!/usr/bin/env python3
"""
Scotland: Public Health Scotland "Prescriptions in the Community", one table per month on the
NHS Scotland open data portal (CKAN, SQL endpoint), by prescriber location (GP practice and health
board). Items are coded by BNF presentation and quantity is a device count, as in the English
Prescribing Dataset (checked: Fiasp Penfill costs 5.66 pounds per unit of quantity in October 2025,
the price of one cartridge). The same classes and units-per-device arithmetic as history.py apply.

Writes international/cache/scotland/<month>.json and international/output/scotland_by_presentation.csv
(month x health board x BNF code).
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

API = "https://www.opendata.nhs.scot/api/3/action"
HERE = Path(__file__).parent
CACHE = HERE / "cache" / "scotland"
OUT = HERE / "output"


def resources():
    d = requests.get(f"{API}/package_show", params={"id": "prescriptions-in-the-community"}, timeout=120).json()
    out = {}
    for x in d["result"]["resources"]:
        if not x["name"].startswith("Data by Prescrib"):
            continue
        m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
                      x["name"])
        if m:
            out[pd.Timestamp(f"1 {m.group(1)} {m.group(2)}").strftime("%Y%m")] = x["id"]
    return dict(sorted(out.items()))


def pull(month, rid):
    f = CACHE / f"{month}.json"
    if f.exists():
        return month, None
    fields = {x["id"] for x in requests.get(f"{API}/datastore_search", params={"resource_id": rid, "limit": 0},
                                             timeout=300).json()["result"]["fields"]}
    hb = "HBT" if "HBT" in fields else "HBT2014"  # the board column alternates between these names
    sql = (f'SELECT "{hb}" AS "HBT", "BNFItemCode", "BNFItemDescription", SUM("NumberOfPaidItems"::numeric) AS items, '
           f'SUM("PaidQuantity"::numeric) AS quantity, SUM("GrossIngredientCost"::numeric) AS cost '
           f'FROM "{rid}" WHERE "BNFItemCode" LIKE \'0601011%\' GROUP BY 1, 2, 3')
    for attempt in range(5):
        try:
            r = requests.get(f"{API}/datastore_search_sql", params={"sql": sql}, timeout=600).json()
            if r.get("success"):
                rows = r["result"]["records"]
                for x in rows:
                    x["month"] = month
                f.write_text(json.dumps(rows))
                return month, len(rows)
            err = r.get("error")
        except Exception as e:
            err = e
    raise RuntimeError(f"{month}: {err}")


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    res = resources()
    print(f"{len(res)} months, {min(res)} to {max(res)}")
    with ThreadPoolExecutor(7) as ex:
        for m, n in ex.map(lambda kv: pull(*kv), res.items()):
            if n is not None:
                print(f"  {m} {n} rows", flush=True)
    df = pd.concat([pd.DataFrame(json.loads(f.read_text())) for f in sorted(CACHE.glob("*.json"))], ignore_index=True)
    df = df.rename(columns={"BNFItemCode": "code", "BNFItemDescription": "name", "HBT": "area"})
    df.to_csv(OUT / "scotland_by_presentation.csv", index=False)
    print(f"{len(df):,} rows")


if __name__ == "__main__":
    sys.exit(main())
