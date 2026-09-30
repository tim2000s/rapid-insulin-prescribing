#!/usr/bin/env python3
"""
Comparisons the generated summary does not make: practice-level concentration for every brand,
not only Lyumjev, and the last month with units for every presentation of every brand. Reads the
EPD cache and output/ written by rapid_insulin_units.py; writes output/brand_concentration.csv and
output/presentation_status.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import rapid_insulin_units as R
from epd_source import EPDClient

OUT = Path(__file__).parent / "output"


def main():
    c = EPDClient()
    meta = pd.read_csv(OUT / "presentations.csv").set_index("code")
    pr = c.practice[c.practice.code.isin(meta.index[meta.basis.notna()])].copy()
    pr["brand"] = pr.code.map(meta.brand)
    pr["units"] = pr.quantity * pr.code.map(meta.apply(R.units_per_quantity, axis=1))
    n_any = pr[pr["items"] > 0].PRACTICE_CODE.nunique()
    rows = []
    for b in R.BRANDS:
        per = pr[pr.brand == b].groupby("PRACTICE_CODE").units.sum()
        per = per[per > 0].sort_values(ascending=False)
        top = max(1, int(np.ceil(0.1 * len(per))))
        rows.append(dict(brand=b, practices=len(per), pct_of_practices=len(per) / n_any * 100,
                         units_m=per.sum() / 1e6, top10pct_share=per.iloc[:top].sum() / per.sum() * 100,
                         gini=R.gini(per.values)))
    t = pd.DataFrame(rows).round(2)
    t.to_csv(OUT / "brand_concentration.csv", index=False)
    print(t.to_string(index=False))

    allp = pd.read_csv(OUT / "monthly_by_presentation.csv", parse_dates=["date"])
    latest = allp.date.max()
    st = allp[allp.units > 0].groupby(["brand", "code", "name"]).agg(
        first=("date", "min"), last=("date", "max"), items_total=("items", "sum"),
        peak_items_month=("items", "max")).reset_index()
    last12 = allp[allp.date > latest - pd.DateOffset(months=12)].groupby("code")["items"].sum()
    st["items_last12m"] = st.code.map(last12).fillna(0)
    st["stopped"] = st["last"] < latest - pd.DateOffset(months=2)
    st.to_csv(OUT / "presentation_status.csv", index=False)
    print(st[st.stopped | (st.items_last12m < 500)].to_string(index=False))


if __name__ == "__main__":
    main()
