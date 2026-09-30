#!/usr/bin/env python3
"""
Ultra-rapid share of rapid-acting analogue insulin in the four UK nations, on one definition.

England comes from output/history/national_by_presentation.csv (history.py); Scotland, Northern
Ireland and Wales from the files written by scotland.py and ni_wales.py. All four code products by
BNF presentation and count quantity in devices, so the classes and units-per-device arithmetic of
history.py apply unchanged. Wales publishes only from November 2024.

Writes international/output/uk_nations_monthly.csv, uk_nations_annual.csv, uk_scotland_boards.csv
and international/output/UK_SUMMARY.md.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import history as H  # noqa: E402

OUT = HERE / "output"
ANALOGUE = ["ultra-rapid", "originator", "biosimilar", "generic analogue"]
# Scottish health board codes (2019 boundaries) to names.
BOARDS = {"S08000015": "Ayrshire and Arran", "S08000016": "Borders", "S08000017": "Dumfries and Galloway",
          "S08000019": "Forth Valley", "S08000020": "Grampian", "S08000022": "Highland",
          "S08000024": "Lothian", "S08000025": "Orkney", "S08000026": "Shetland", "S08000028": "Western Isles",
          "S08000029": "Fife", "S08000030": "Tayside", "S08000031": "Greater Glasgow and Clyde",
          "S08000032": "Lanarkshire", "S08000021": "Greater Glasgow and Clyde (pre-2019)",
          "S08000023": "Lanarkshire (pre-2019)", "S08000018": "Fife (pre-2018)", "S08000027": "Tayside (pre-2018)",
          # Welsh health board codes.
          "7A1": "Betsi Cadwaladr", "7A2": "Hywel Dda", "7A3": "Swansea Bay", "7A4": "Cardiff and Vale",
          "7A5": "Cwm Taf Morgannwg", "7A6": "Aneurin Bevan", "7A7": "Powys"}


def load():
    e = pd.read_csv(HERE.parent / "output" / "history" / "national_by_presentation.csv", parse_dates=["date"])
    e = e.assign(nation="England", area="England")[["nation", "area", "date", "code", "name", "items", "quantity"]]
    parts = [e]
    s = pd.read_csv(OUT / "scotland_by_presentation.csv", dtype={"month": str})
    parts.append(s.assign(nation="Scotland", date=pd.to_datetime(s.month, format="%Y%m")))
    for n, label in (("ni", "Northern Ireland"), ("wales", "Wales")):
        d = pd.read_csv(OUT / f"{n}_by_presentation.csv", dtype={"month": str, "area": str})
        parts.append(d.assign(nation=label, date=pd.to_datetime(d.month, format="%Y%m")))
    d = pd.concat([p[["nation", "area", "date", "code", "name", "items", "quantity"]] for p in parts], ignore_index=True)
    d["code"] = d.code.astype(str)
    # England's names are the reference for the device parse; the other nations abbreviate them
    # ("Ins Fiasp_Penfill 100u/ml 3ml Cart"), so each code takes its English name where one exists.
    names = e.sort_values("date").groupby("code").name.last()
    d["name"] = d.code.map(names).fillna(d.name)
    d["class"] = d.code.map(H.klass)
    d["units"] = d.quantity * d.name.map(H.units_per_device)
    return d


def main():
    d = load()
    a = d[d["class"].isin(ANALOGUE)]
    m = a.pivot_table(index=["nation", "date"], columns="class", values="units", aggfunc="sum").fillna(0)
    mi = a.pivot_table(index=["nation", "date"], columns="class", values="items", aggfunc="sum").fillna(0)
    mon = pd.DataFrame({"ultra_units_pct": m["ultra-rapid"] / m.sum(axis=1) * 100,
                        "ultra_items_pct": mi["ultra-rapid"] / mi.sum(axis=1) * 100,
                        "biosimilar_units_pct": m["biosimilar"] / m.sum(axis=1) * 100,
                        "analogue_units": m.sum(axis=1)})
    lyu = a[a.code.str.startswith("0601011L0BD")].groupby(["nation", "date"]).units.sum()
    mon["lyumjev_units_pct"] = (lyu / m.sum(axis=1) * 100).reindex(mon.index).fillna(0)
    mon.to_csv(OUT / "uk_nations_monthly.csv")

    # Twelve months to the latest month every nation has, and the same window a year earlier.
    latest = min(g.index.get_level_values("date").max() for _, g in m.groupby(level="nation"))
    rows = []
    for nation, g in a.groupby("nation"):
        for k in range(0, 10):
            end = latest - pd.DateOffset(years=k)
            w = g[(g.date > end - pd.DateOffset(months=12)) & (g.date <= end)]
            if w.date.nunique() < 12:
                continue
            u = w.groupby("class").units.sum()
            it = w.groupby("class")["items"].sum()
            rows.append(dict(nation=nation, year_to=end.date(), ultra_units_pct=u.get("ultra-rapid", 0) / u.sum() * 100,
                             ultra_items_pct=it.get("ultra-rapid", 0) / it.sum() * 100,
                             lyumjev_units_pct=w[w.code.str.startswith("0601011L0BD")].units.sum() / u.sum() * 100,
                             fiasp_units_pct=w[w.code.str.startswith("0601011A0BC")].units.sum() / u.sum() * 100,
                             biosimilar_units_pct=u.get("biosimilar", 0) / u.sum() * 100,
                             analogue_units_m=u.sum() / 1e6))
    ann = pd.DataFrame(rows).sort_values(["nation", "year_to"])
    ann.round(2).to_csv(OUT / "uk_nations_annual.csv", index=False)

    # Scottish and Welsh health boards, last 12 months. Boards with under 1 million units are dropped
    # (a residual Scottish code, SB0806, carries almost none).
    s = a[a.nation.isin(["Scotland", "Wales"]) & (a.date > latest - pd.DateOffset(months=12)) & (a.date <= latest)]
    b = s.pivot_table(index=["nation", "area"], columns="class", values="units", aggfunc="sum").fillna(0)
    b = b[b.sum(axis=1) >= 1e6]
    b = pd.DataFrame({"nation": b.index.get_level_values(0),
                      "board": b.index.get_level_values(1).map(lambda x: BOARDS.get(x, x)),
                      "ultra_units_pct": b["ultra-rapid"] / b.sum(axis=1) * 100,
                      "analogue_units_m": b.sum(axis=1) / 1e6}).sort_values("ultra_units_pct")
    b.round(2).to_csv(OUT / "uk_boards.csv", index=False)

    L = ["# Four UK nations: generated summary\n", f"Generated by `uk_compare.py`. Latest month common to all "
         f"four nations: {latest:%B %Y}.\n", "## Twelve months to the common latest month\n",
         "| nation | ultra-rapid % of units | % of items | Fiasp % | Lyumjev % | biosimilar % | analogue units (million) |",
         "|---|---|---|---|---|---|---|"]
    for _, r in ann[ann.year_to == latest.date()].iterrows():
        L.append(f"| {r.nation} | {r.ultra_units_pct:.1f} | {r.ultra_items_pct:.1f} | {r.fiasp_units_pct:.1f} | "
                 f"{r.lyumjev_units_pct:.1f} | {r.biosimilar_units_pct:.1f} | {r.analogue_units_m:,.0f} |")
    L += ["", f"## Ultra-rapid % of units by year to {latest:%B}\n"]
    piv = ann.pivot(index="year_to", columns="nation", values="ultra_units_pct").round(1)
    L.append("| year to | " + " | ".join(piv.columns) + " |")
    L.append("|---|" + "---|" * len(piv.columns))
    for y, r in piv.iterrows():
        L.append(f"| {y:%b %Y} | " + " | ".join("" if np.isnan(v) else f"{v:.1f}" for v in r) + " |")
    L += ["", "## Scottish and Welsh health boards, same 12 months\n",
          "| nation | board | ultra-rapid % | analogue units (million) |", "|---|---|---|---|"]
    for _, r in b.iterrows():
        L.append(f"| {r.nation} | {r.board} | {r.ultra_units_pct:.1f} | {r.analogue_units_m:.1f} |")
    (OUT / "UK_SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
