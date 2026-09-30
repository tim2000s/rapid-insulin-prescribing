#!/usr/bin/env python3
"""
National monthly rapid-acting insulin dispensing in English primary care from January 2014, by
product class. Answers the headline question: with ultra-rapid analogues available since 2017, what
share of rapid-acting prescribing is still for the older, slower products?

January 2014 to October 2020 comes from the older EPD package (no SNOMED codes); November 2020
onwards from the SNOMED package already cached by epd_source.py. A few overlap months are pulled
from both packages and compared, so the join is checked rather than assumed.

Classes, by BNF presentation code:
    ultra-rapid        Lyumjev, Fiasp
    originator         Humalog, NovoRapid, Apidra (standard-speed branded analogues)
    biosimilar         Trurapi, Admelog, Insulin lispro Sanofi (standard-speed)
    generic analogue   lispro, aspart, glulisine prescribed generically
    human soluble      Actrapid, Humulin S, Hypurin Neutral and other soluble human insulin
The headline denominator is every rapid-acting analogue (the first four classes). Human soluble
insulin is reported alongside, since it is older and slower still.

    python3 history.py      # pulls about 85 monthly aggregates, writes output/history/
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

import epd_source as E

HERE = Path(__file__).parent
CACHE = HERE / "epd_cache" / "old_national"
OUT = HERE / "output" / "history"
ULTRA = ("0601011L0BD", "0601011A0BC")
ORIGINATOR = ("0601011L0BB", "0601011A0BB", "0601011P0BB")
BIOSIMILAR = ("0601011A0BD", "0601011L0BE", "0601011L0BC")
GENERIC = ("0601011L0AA", "0601011A0AA", "0601011P0AA")
ANALOGUE = ("0601011L0", "0601011A0", "0601011P0")
OVERLAP = ["EPD_202101", "EPD_202306", "EPD_202506"]


def klass(code):
    for name, prefixes in (("ultra-rapid", ULTRA), ("originator", ORIGINATOR), ("biosimilar", BIOSIMILAR),
                           ("generic analogue", GENERIC)):
        if code.startswith(prefixes):
            return name
    return "other analogue" if code.startswith(ANALOGUE) else "human soluble"


def units_per_device(name):
    """Quantity counts devices (checked for analogues against SCMD; see rapid_insulin_units.py).
    Units per device from the name: concentration times fill volume, with vials 10 ml and
    unlabelled cartridges and pens 3 ml."""
    n = name.lower()
    conc = float(m.group(1)) if (m := re.search(r"(\d+)\s*(?:units?|u)/ml", n)) else 100.0
    ml = float(m.group(1)) if (m := re.search(r"(\d+(?:\.\d+)?)\s*ml\b", n)) else (10.0 if "vial" in n else 3.0)
    return conc * ml


def pull_old(res):
    f = CACHE / f"{res}.json"
    if f.exists():
        return json.loads(f.read_text())
    q = (f"SELECT BNF_CODE AS code, BNF_DESCRIPTION AS name, SUM(CAST(ITEMS AS FLOAT64)) AS items, "
         f"SUM(CAST(TOTAL_QUANTITY AS FLOAT64)) AS quantity, SUM(CAST(ACTUAL_COST AS FLOAT64)) AS actual_cost "
         f"FROM `{res}` WHERE BNF_CODE LIKE '0601011%' GROUP BY BNF_CODE, BNF_DESCRIPTION")
    rows = E.sql(q, res)
    for r in rows:
        r["month"] = res[-6:]
    f.write_text(json.dumps(rows))
    return rows


def old_months():
    import requests
    r = requests.get(f"{E.PORTAL}/package_show", params={"id": "english-prescribing-data-epd"}, timeout=120).json()
    return sorted(x["name"] for x in r["result"]["resources"] if x["name"].startswith("EPD_2"))


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    want = [m for m in old_months() if m <= "EPD_202010"] + OVERLAP
    with ThreadPoolExecutor(7) as ex:
        old = pd.DataFrame([r for rows in ex.map(pull_old, want) for r in rows])
    old["date"] = pd.to_datetime(old.month, format="%Y%m")

    new = pd.read_csv(HERE / "epd_cache" / "icb_monthly.csv", dtype={"YEAR_MONTH": str})
    new["date"] = pd.to_datetime(new.YEAR_MONTH.str.replace("-", ""), format="%Y%m")
    new = new.groupby(["date", "BNF_PRESENTATION_CODE"]).agg(
        name=("BNF_PRESENTATION_NAME", "last"), items=("items", "sum"), quantity=("quantity", "sum"),
        actual_cost=("actual_cost", "sum")).reset_index().rename(columns={"BNF_PRESENTATION_CODE": "code"})

    # Join check: the two packages over the same months.
    ov = old[old.month.isin([m[-6:] for m in OVERLAP])].groupby("date")[["items", "quantity"]].sum()
    nv = new[new.date.isin(ov.index)].groupby("date")[["items", "quantity"]].sum()
    check = (nv / ov).round(5)
    print("SNOMED package / old package, all 0601011 codes:\n" + check.to_string())

    both = pd.concat([old[old.date < new.date.min()], new], ignore_index=True)
    # Names differ between packages for one code; take the newest for the device parse.
    names = both.sort_values("date").groupby("code").name.last()
    both["name"] = both.code.map(names)
    both["class"] = both.code.map(klass)
    both["units"] = both.quantity * both.name.map(units_per_device)
    both.to_csv(OUT / "national_by_presentation.csv", index=False)

    u = both.pivot_table(index="date", columns="class", values="units", aggfunc="sum").fillna(0)
    it = both.pivot_table(index="date", columns="class", values="items", aggfunc="sum").fillna(0)
    analogue = ["ultra-rapid", "originator", "biosimilar", "generic analogue"]
    other = [c for c in u.columns if c not in analogue + ["human soluble"]]
    assert not other or u[other].sum().sum() / u[analogue].sum().sum() < 1e-3, other
    yr = pd.DataFrame({
        "ultra_units_pct": u["ultra-rapid"].rolling(12).sum() / u[analogue].sum(axis=1).rolling(12).sum() * 100,
        "ultra_items_pct": it["ultra-rapid"].rolling(12).sum() / it[analogue].sum(axis=1).rolling(12).sum() * 100,
        "biosimilar_units_pct": u["biosimilar"].rolling(12).sum() / u[analogue].sum(axis=1).rolling(12).sum() * 100,
        "human_soluble_units_pct_of_all": u["human soluble"].rolling(12).sum()
        / u[analogue + ["human soluble"]].sum(axis=1).rolling(12).sum() * 100,
        "analogue_units_12m_bn": u[analogue].sum(axis=1).rolling(12).sum() / 1e9,
        "analogue_items_12m_m": it[analogue].sum(axis=1).rolling(12).sum() / 1e6,
    })
    yr.to_csv(OUT / "rolling_12m_shares.csv", index_label="date")

    # Cost per 100 units by brand, calendar years.
    brand = {"0601011L0BD": "Lyumjev", "0601011A0BC": "Fiasp", "0601011L0BB": "Humalog",
             "0601011A0BB": "NovoRapid", "0601011P0BB": "Apidra", "0601011A0BD": "Trurapi",
             "0601011L0BE": "Admelog"}
    both["brand"] = both.code.str[:11].map(brand)
    b = both.dropna(subset=["brand"])
    cost = b.groupby([b.date.dt.year, "brand"]).apply(lambda g: g.actual_cost.sum() / g.units.sum() * 100)
    cost = cost.unstack("brand")[list(brand.values())].round(2)
    cost.to_csv(OUT / "cost_per_100_units_by_year.csv", index_label="year")

    L = ["# Rapid-acting insulin in English primary care since 2014: generated summary\n",
         f"Generated by `history.py`; do not edit by hand. {u.index.min():%B %Y} to {u.index.max():%B %Y}.\n",
         "Join check, SNOMED package over old package for the same months (items, quantity): "
         + "; ".join(f"{d:%b %Y} {r['items']:.4f}, {r['quantity']:.4f}" for d, r in check.iterrows()) + ".\n",
         "## Share of rapid-acting analogue prescribing, 12 months to July each year\n",
         "| year to | ultra-rapid % of units | ultra-rapid % of items | standard-speed % of units | biosimilar % of units | human soluble % of all rapid and soluble units | analogue units (billion) | analogue items (million) |",
         "|---|---|---|---|---|---|---|---|"]
    for d in [pd.Timestamp(f"{y}-07-01") for y in range(2015, 2027)]:
        if d in yr.index and not np.isnan(yr.loc[d, "ultra_units_pct"]):
            r = yr.loc[d]
            L.append(f"| Jul {d.year} | {r.ultra_units_pct:.1f} | {r.ultra_items_pct:.1f} | {100 - r.ultra_units_pct:.1f} | "
                     f"{r.biosimilar_units_pct:.1f} | {r.human_soluble_units_pct_of_all:.1f} | "
                     f"{r.analogue_units_12m_bn:.2f} | {r.analogue_items_12m_m:.2f} |")
    L.append("")
    first = {n: both.loc[(both.brand == n) & (both["items"] > 0), "date"].min() for n in brand.values()}
    L.append("First month dispensed: " + "; ".join(f"{n} {d:%b %Y}" for n, d in first.items()) + ".\n")
    L.append("## Cost per 100 units dispensed (actual cost, pounds), by calendar year\n")
    L.append("| year | " + " | ".join(cost.columns) + " |")
    L.append("|---|" + "---|" * len(cost.columns))
    for y, r in cost.iterrows():
        L.append(f"| {y} | " + " | ".join("" if np.isnan(v) else f"{v:.2f}" for v in r) + " |")
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
