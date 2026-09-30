#!/usr/bin/env python3
"""
End-to-end test of rapid_insulin_units.py against a synthetic OpenPrescribing API whose answers
are known. Nothing here is real data. It checks that the quantity basis is recovered from cost,
that units reconcile exactly with the synthetic truth, that a discontinued device is flagged, and
that the ICB and practice statistics come out where they were planted.

    python3 test_pipeline.py            # writes to a temporary directory and asserts
    python3 test_pipeline.py --keep D   # keep the synthetic outputs in D to look at the charts
"""
import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import rapid_insulin_units as R

RNG = np.random.default_rng(7)
MONTHS = pd.date_range("2021-07-01", "2026-06-01", freq="MS")
LATEST = MONTHS[-1]

# Truth planted in the synthetic API: which presentations report quantity as a device count.
COUNT_BASIS = {"0601011L0BBABAB", "0601011A0BBAAAA", "0601011L0BDAAAG"}
STOPPED = {"0601011L0BDACAC": pd.Timestamp("2025-10-01")}   # Lyumjev cartridge stops
ABSENT = {"0601011L0BBAAAA", "0601011A0BBACAC"}             # no data at all
NEW_CODE = ("0601011A0BCADAD", "Fiasp PumpCart 100units/ml inj 1.6ml cartridges")

MONTHLY_UNITS = {  # rough national units per month at the start, and growth per year
    "Lyumjev": (25e6, 0.30), "Fiasp": (35e6, 0.10), "Humalog": (120e6, -0.05), "NovoRapid": (250e6, -0.03),
}
DEVICE_MIX = {"Vial": 0.08, "PumpCart": 0.05, "Cartridge": 0.30}
N_ICB, N_PRACTICE = 42, 6300


def presentation_truth():
    names = {**R.FALLBACK, NEW_CODE[0]: NEW_CODE[1]}
    rows = []
    for code, name in names.items():
        p = R.classify(code, name)
        if code in ABSENT:
            continue
        w = DEVICE_MIX.get(p["device"], None)
        rows.append({**p, "weight": w})
    t = pd.DataFrame(rows)
    for b, g in t.groupby("brand"):
        fixed = g.weight.fillna(0).sum()
        free = g.weight.isna().sum()
        t.loc[g.index, "weight"] = g.weight.fillna((1 - fixed) / free)
        t.loc[g.index, "weight"] /= t.loc[g.index, "weight"].sum()
    t["basis"] = np.where(t.code.isin(COUNT_BASIS), "count", "ml")
    return t.set_index("code")


TRUTH = presentation_truth()


def national_units(code, date):
    p = TRUTH.loc[code]
    base, g = MONTHLY_UNITS[p.brand]
    if code in STOPPED and date > STOPPED[code]:
        return 0.0
    years = (date - MONTHS[0]).days / 365.25
    return base * (1 + g) ** years * p.weight


def to_row(code, date, units, share=1.0):
    p = TRUTH.loc[code]
    k = p.units_per_ml if p.basis == "ml" else p.units_per_ml * p.ml_per_pack_unit
    qty = units * share / k
    per_item = 15 if p.basis == "ml" else 5
    return dict(date=date.strftime("%Y-%m-%d"), items=round(qty / per_item),
                quantity=qty, actual_cost=units * share * 0.0195 * RNG.uniform(0.9, 1.1))


ICB_ULTRA_TILT = np.linspace(0.3, 2.2, N_ICB)   # planted variation in ultra-rapid use
ICB_SIZE = RNG.uniform(0.5, 1.5, N_ICB)


def icb_weights(brand):
    w = ICB_SIZE * (ICB_ULTRA_TILT if brand in R.ULTRA_RAPID else 1.0)
    return w / w.sum()


PRACTICE_LYU = np.where(RNG.uniform(size=N_PRACTICE) < 0.35, RNG.pareto(1.2, N_PRACTICE) + 0.01, 0)


class FakeClient:
    def __init__(self):
        self.calls = 0

    def get(self, path, **params):
        self.calls += 1
        code = params.get("code", params.get("q"))
        if path == "bnf_code":
            return [dict(id=c, name=TRUTH.loc[c, "name"]) for c in TRUTH.index if c.startswith(code)] + \
                   [dict(id=code, name="product-level row, ignored")]
        if path == "spending":
            if code not in TRUTH.index:
                if len(code) == 11:  # context product prefix
                    return [dict(date=d.strftime("%Y-%m-%d"), items=1000, quantity=15000, actual_cost=2900.0)
                            for d in MONTHS]
                return []
            return [to_row(code, d, national_units(code, d)) for d in MONTHS
                    if national_units(code, d) > 0 or d <= STOPPED.get(code, LATEST)]
        if path == "spending_by_org" and params["org_type"] == "icb":
            if code not in TRUTH.index:
                return []
            w = icb_weights(TRUTH.loc[code, "brand"])
            rows = []
            for d in MONTHS:
                u = national_units(code, d)
                if u <= 0:
                    continue
                for i in range(N_ICB):
                    r = to_row(code, d, u, w[i])
                    rows.append(dict(r, row_id=f"QX{i:02d}", row_name=f"NHS Synthetic {i:02d} Integrated Care Board"))
            return rows
        if path == "spending_by_org" and params["org_type"] == "practice":
            d = pd.Timestamp(params["date"])
            if len(code) == 11:  # brand-level code: accepted by the synthetic API
                brand = next(b for b, p in R.BRANDS.items() if p == code)
                mask = PRACTICE_LYU > 0 if brand == "Lyumjev" else np.ones(N_PRACTICE, bool)
                return [dict(row_id=f"P{i:05d}", row_name=f"Practice {i}", date=params["date"], items=3,
                             quantity=45, actual_cost=90.0) for i in np.flatnonzero(mask)]
            if code not in TRUTH.index or TRUTH.loc[code, "brand"] != "Lyumjev":
                return []
            u = national_units(code, d)
            if u <= 0:
                return []
            w = PRACTICE_LYU / PRACTICE_LYU.sum()
            return [dict(to_row(code, d, u, w[i]), row_id=f"P{i:05d}", row_name=f"Practice {i}")
                    for i in np.flatnonzero(w)]
        raise ValueError(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", type=Path)
    args = ap.parse_args()
    out = args.keep or Path(tempfile.mkdtemp())
    res = R.run(FakeClient(), out, pulled="synthetic")
    meta = res["meta"].set_index("code")

    # Basis recovered from cost for every presentation with data.
    got = meta.loc[TRUTH.index, "basis"]
    wrong = got[got != TRUTH.basis]
    assert wrong.empty, f"basis misread: {wrong.to_dict()}"
    assert meta.loc[list(ABSENT), "basis"].isna().all()
    assert NEW_CODE[0] in meta.index

    # Units reconcile with the planted truth.
    for b in R.BRANDS:
        truth = sum(national_units(c, LATEST) for c in TRUTH.index if TRUTH.loc[c, "brand"] == b)
        got = res["by_brand"].loc[LATEST, b]
        assert abs(got / truth - 1) < 1e-9, (b, got, truth)

    # The stopped cartridge is flagged, and nothing else is.
    st = res["stops"].set_index("device")
    assert st.loc["Cartridge", "stopped"] and str(st.loc["Cartridge", "last_nonzero"]) == "2025-10-01"
    assert st.stopped.sum() == 1

    # ICB spread comes out where it was planted: shares are ordered by the tilt.
    icb = res["icb"].set_index("icb_code")
    order = icb.ultra_rapid_share_pct.sort_values().index
    assert list(order) == [f"QX{i:02d}" for i in range(N_ICB)], "ICB ordering does not follow the planted tilt"
    assert res["icb_stats"]["ultra_p90_p10_ratio"] > 2.5

    # Practice concentration: everyone prescribes a rapid analogue, 35% prescribe Lyumjev.
    c = res["conc"]
    assert c["practices_any_rapid_analogue"] == N_PRACTICE
    assert c["practices_any_lyumjev"] == (PRACTICE_LYU > 0).sum()

    for f in ["presentations.csv", "monthly_by_presentation.csv", "monthly_units_by_brand.csv",
              "monthly_share_by_brand.csv", "lyumjev_monthly_by_device.csv", "icb_ultrarapid_share_last12m.csv",
              "practice_lyumjev_concentration.csv", "SUMMARY.md", "units_by_brand.png", "share_by_brand.png",
              "ultra_rapid_share.png", "lyumjev_by_device.png", "icb_ultrarapid_share.png",
              "ultra_rapid_share_by_segment.png"]:
        assert (out / f).exists(), f
    print(f"\nAll checks passed. Synthetic outputs in {out}")


if __name__ == "__main__":
    main()
