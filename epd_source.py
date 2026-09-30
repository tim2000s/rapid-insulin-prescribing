#!/usr/bin/env python3
"""
NHSBSA English Prescribing Dataset as a stand-in for the OpenPrescribing API.

OpenPrescribing sits behind a Cloudflare JavaScript challenge that refuses scripted clients (HTTP 403
with a "Just a moment" page, whatever the user agent), so the pipeline cannot call it directly. The
data underneath it is the NHSBSA English Prescribing Dataset, which the NHSBSA open data portal
serves through a CKAN SQL endpoint. This module pulls that dataset once into a local cache and then
answers the same four queries `rapid_insulin_units.py` makes of OpenPrescribing, in the same shape,
so the analysis code does not change with the source.

The package used is "English Prescribing Dataset (EPD) with SNOMED code", one table per month from
November 2020. The older package without SNOMED codes stops at June 2025.

    python3 epd_source.py                 # fill epd_cache/ (about 80 SQL calls, a few minutes)
    python3 rapid_insulin_units.py --source epd

Two tables are cached, both already aggregated on the server:
    icb_monthly.csv       month x presentation x ICB, every 0601011 code (short-acting insulins)
    practice_monthly.csv  month x presentation x practice, the analysed brands, last 12 months only
National figures are the sum of the ICB table, including the rows with no ICB, so they match the
national total rather than the sum of named ICBs.

ICB figures come from the practice table instead. Twelve ICBs merged into six in April 2026, and
three of the old ones were split between new ones (Frimley went to three), so no code-to-code map
exists. Each practice is assigned to the ICB it belonged to in the latest month and its rows are
summed on that basis, which puts the whole 12-month window on current boundaries. ICB figures are
therefore available only for the months in the practice cache. Practices with no rows after the
merger keep a code that no longer exists; they are left out of the ICB figures (64 of 6,906
practices and 0.03% of quantity in the August 2025 to July 2026 window).
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

PORTAL = "https://opendata.nhsbsa.net/api/3/action"
PACKAGE = "english-prescribing-dataset-epd-with-snomed-code"
CACHE = Path(__file__).parent / "epd_cache"
PAGE = 25000
# Practice rows are only needed for the brands the concentration analysis uses.
PRACTICE_PREFIXES = ("0601011L0BD", "0601011L0BB", "0601011A0BB", "0601011A0BC", "0601011A0BD", "0601011P0BB")


def sql(query, resource_id, tries=5):
    for attempt in range(tries):
        try:
            r = requests.get(f"{PORTAL}/datastore_search_sql", params={"resource_id": resource_id, "sql": query},
                             timeout=600)
            j = r.json()
            if j.get("success"):
                # The portal wraps the CKAN result one level deeper than CKAN does.
                res = j["result"]
                return res["result"]["records"] if "result" in res else res["records"]
            err = j.get("error")
            if isinstance(err, dict) and err.get("__type") == "Search Query Error":
                break  # a malformed query does not improve on retry
        except (requests.RequestException, ValueError) as e:
            err = e
        time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"{resource_id}: {err}")


def paged(query, resource_id):
    rows, offset = [], 0
    while True:
        page = sql(f"{query} LIMIT {PAGE} OFFSET {offset}", resource_id)
        rows += page
        if len(page) < PAGE:
            return rows
        offset += PAGE


def months():
    r = requests.get(f"{PORTAL}/package_show", params={"id": PACKAGE}, timeout=120).json()
    return sorted(x["name"] for x in r["result"]["resources"] if x["name"].startswith("EPD_SNOMED_"))


def columns(res):
    """The monthly tables use three schemas. Before May 2022 the area is an STP rather than an
    ICB, and from March 2025 the BNF code and name columns were renamed. Returns the column
    names to select for (code, name, area code, area name)."""
    r = requests.get(f"{PORTAL}/datastore_search", params={"resource_id": res, "limit": 0}, timeout=120).json()
    f = {x["id"] for x in r["result"]["fields"]}
    code, name = ("BNF_PRESENTATION_CODE", "BNF_PRESENTATION_NAME") if "BNF_PRESENTATION_CODE" in f \
        else ("BNF_CODE", "BNF_DESCRIPTION")
    area = "ICB" if "ICB_CODE" in f else "STP"
    return code, name, f"{area}_CODE", f"{area}_NAME"


def pull_icb(res):
    code, name, ac, an = columns(res)
    q = (f"SELECT YEAR_MONTH, {code} AS BNF_PRESENTATION_CODE, {name} AS BNF_PRESENTATION_NAME, "
         f"{ac} AS ICB_CODE, {an} AS ICB_NAME, "
         f"SUM(CAST(ITEMS AS FLOAT64)) AS items, SUM(CAST(TOTAL_QUANTITY AS FLOAT64)) AS quantity, "
         f"SUM(CAST(ACTUAL_COST AS FLOAT64)) AS actual_cost "
         f"FROM `{res}` WHERE {code} LIKE '0601011%' "
         f"GROUP BY YEAR_MONTH, {code}, {name}, {ac}, {an} ORDER BY {code}, {ac}")
    return paged(q, res)


def pull_practice(res):
    code, _, ac, an = columns(res)
    like = " OR ".join(f"{code} LIKE '{p}%'" for p in PRACTICE_PREFIXES)
    q = (f"SELECT YEAR_MONTH, {code} AS BNF_PRESENTATION_CODE, PRACTICE_CODE, PRACTICE_NAME, "
         f"{ac} AS ICB_CODE, {an} AS ICB_NAME, "
         f"SUM(CAST(ITEMS AS FLOAT64)) AS items, SUM(CAST(TOTAL_QUANTITY AS FLOAT64)) AS quantity, "
         f"SUM(CAST(ACTUAL_COST AS FLOAT64)) AS actual_cost "
         f"FROM `{res}` WHERE ({like}) "
         f"GROUP BY YEAR_MONTH, {code}, PRACTICE_CODE, PRACTICE_NAME, {ac}, {an} ORDER BY {code}, PRACTICE_CODE")
    return paged(q, res)


def fill_cache(cache=CACHE, workers=7, practice_months=12):
    """One file per month per table, so an interrupted pull resumes where it stopped."""
    for sub in ("icb", "practice"):
        (cache / sub).mkdir(parents=True, exist_ok=True)
    ms = months()
    jobs = [("icb", m) for m in ms] + [("practice", m) for m in ms[-practice_months:]]
    jobs = [(t, m) for t, m in jobs if not (cache / t / f"{m}.json").exists()]
    print(f"{len(ms)} months ({ms[0]} to {ms[-1]}); {len(jobs)} month-tables to pull")

    def one(job):
        t, m = job
        rows = (pull_icb if t == "icb" else pull_practice)(m)
        (cache / t / f"{m}.json").write_text(json.dumps(rows))
        return t, m, len(rows)

    with ThreadPoolExecutor(workers) as ex:
        for t, m, n in ex.map(one, jobs):
            print(f"  {t:8s} {m}  {n:6d} rows", flush=True)
    for t in ("icb", "practice"):
        frames = [pd.DataFrame(json.loads(f.read_text())) for f in sorted((cache / t).glob("*.json"))]
        df = pd.concat([f for f in frames if len(f)], ignore_index=True)
        df.to_csv(cache / f"{t}_monthly.csv", index=False)
        print(f"{t}_monthly.csv: {len(df):,} rows")


def _clean_icb(name):
    # EPD truncates ICB names at 40 characters ("... INTEGRA"); restore the suffix the charts strip.
    if not isinstance(name, str):
        return name
    n = name.title().replace("Nhs ", "NHS ")
    for stub in (" Integrated Care Boar", " Integrated Care Boa", " Integrated Care Bo", " Integrated Care B",
                 " Integrated Care", " Integrated Car", " Integrated Ca", " Integrated C", " Integrated",
                 " Integrate", " Integrat", " Integra", " Integr", " Integ", " Inte", " Int"):
        if n.endswith(stub):
            return n[: -len(stub)] + " Integrated Care Board"
    return n


def _month(ym):
    # YEAR_MONTH is 202011 in the older tables and 2026-07 in the newer ones.
    return pd.to_datetime(ym.str.replace("-", "", regex=False), format="%Y%m").dt.strftime("%Y-%m-%d")


class EPDClient:
    """Answers the OpenPrescribing endpoints `rapid_insulin_units.py` uses, from the cache."""

    def __init__(self, cache=CACHE):
        self.calls = 0
        icb = pd.read_csv(cache / "icb_monthly.csv", dtype={"YEAR_MONTH": str, "ICB_CODE": str})
        icb["date"] = _month(icb.YEAR_MONTH)
        icb["ICB_NAME"] = icb.ICB_NAME.map(_clean_icb)
        self.icb = icb.rename(columns={"BNF_PRESENTATION_CODE": "code", "BNF_PRESENTATION_NAME": "name"})
        pr = pd.read_csv(cache / "practice_monthly.csv", dtype={"YEAR_MONTH": str})
        pr["date"] = _month(pr.YEAR_MONTH)
        pr = pr.rename(columns={"BNF_PRESENTATION_CODE": "code"})
        latest = pr.sort_values("date").groupby("PRACTICE_CODE")[["ICB_CODE", "ICB_NAME"]].last()
        pr = pr.drop(columns=["ICB_CODE", "ICB_NAME"]).join(latest, on="PRACTICE_CODE")
        pr["ICB_NAME"] = pr.ICB_NAME.map(_clean_icb)
        self.current_icbs = set(pr.loc[pr.date == pr.date.max(), "ICB_CODE"]) - {"-"}
        self.practice = pr
        self.practice_dates = set(pr.date)

    @staticmethod
    def _rows(df, keys):
        g = df.groupby(keys, dropna=False)[["items", "quantity", "actual_cost"]].sum().reset_index()
        return g.to_dict("records")

    def get(self, path, **params):
        self.calls += 1
        code = params.get("code", params.get("q"))
        if path == "bnf_code":
            names = self.icb[self.icb.code.str.startswith(code)].groupby("code").name.last()
            return [dict(id=c, name=n) for c, n in names.items()]
        if path == "spending":
            return self._rows(self.icb[self.icb.code.str.startswith(code)], ["date"])
        if path == "spending_by_org" and params["org_type"] == "icb":
            d = self.practice[(self.practice.code == code) & self.practice.ICB_CODE.isin(self.current_icbs)]
            rows = self._rows(d, ["date", "ICB_CODE", "ICB_NAME"])
            return [dict(r, row_id=r.pop("ICB_CODE"), row_name=r.pop("ICB_NAME")) for r in rows]
        if path == "spending_by_org" and params["org_type"] == "practice":
            if params["date"] not in self.practice_dates:
                raise KeyError(f"practice data for {params['date']} is not in the cache")
            d = self.practice[(self.practice.date == params["date"]) & self.practice.code.str.startswith(code)]
            rows = self._rows(d, ["date", "PRACTICE_CODE", "PRACTICE_NAME"])
            return [dict(r, row_id=r.pop("PRACTICE_CODE"), row_name=r.pop("PRACTICE_NAME")) for r in rows]
        raise ValueError(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fill the local EPD cache from the NHSBSA open data portal.")
    ap.add_argument("--cache", type=Path, default=CACHE)
    ap.add_argument("--workers", type=int, default=7)
    a = ap.parse_args()
    fill_cache(a.cache, a.workers)
    sys.exit(0)
