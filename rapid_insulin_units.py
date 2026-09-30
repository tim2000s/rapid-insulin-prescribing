#!/usr/bin/env python3
"""
Monthly insulin units dispensed in English primary care from November 2020, for Lyumjev (by
device) against the other branded rapid-acting analogues: Humalog, NovoRapid, Fiasp, Trurapi and
Apidra. Tests whether
ultra-rapid uptake is low, flat and variable by area, which is the "clinical inertia costs access"
argument, and reports where the data does not support it.

Usage:
    pip install requests pandas matplotlib
    python3 epd_source.py                                    # fill epd_cache/ from NHSBSA
    python3 rapid_insulin_units.py                           # analyse from epd_cache/
    python3 rapid_insulin_units.py --source openprescribing  # call OpenPrescribing instead
    python3 rapid_insulin_units.py --skip-practice           # skip the practice concentration

Everything is written to --out-dir (default ./output). See README.md for method and caveats.

Source: NHSBSA English Prescribing Dataset with SNOMED code, via the NHSBSA open data portal
(epd_source.py), or the same dataset through OpenPrescribing.net. Primary care prescribing only.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

API = "https://openprescribing.net/api/1.0"
HEADERS = {"User-Agent": "diabettech-analysis/1.0 (research; python-requests)"}
SOURCE_LINE = "Source: NHSBSA English Prescribing Dataset, primary care only."

BRANDS = {
    "Lyumjev": "0601011L0BD",
    "Humalog": "0601011L0BB",
    "NovoRapid": "0601011A0BB",
    "Fiasp": "0601011A0BC",
    # Trurapi (biosimilar aspart, from June 2021) and Apidra (glulisine) are rapid-acting analogues
    # prescribed at volumes comparable to Lyumjev, so leaving them out would overstate every share.
    "Trurapi": "0601011A0BD",
    "Apidra": "0601011P0BB",
}
ULTRA_RAPID = ["Lyumjev", "Fiasp"]

# Reported for scale only, not converted to units or counted in shares.
CONTEXT_PRODUCTS = {
    "Insulin lispro (generic)": "0601011L0AA",
    "Admelog": "0601011L0BE",
    "Insulin lispro Sanofi": "0601011L0BC",
    "Insulin aspart (generic)": "0601011A0AA",
    "Insulin glulisine (generic)": "0601011P0AA",
}

# Fallback presentation list, from dm+d (May 2023). Discovery adds anything newer.
FALLBACK = {
    "0601011L0BDABAB": "Lyumjev 100units/ml solution for injection 10ml vials",
    "0601011L0BDACAC": "Lyumjev 100units/ml solution for injection 3ml cartridges",
    "0601011L0BDADAF": "Lyumjev KwikPen 100units/ml inj 3ml pre-filled pens",
    "0601011L0BDAEAF": "Lyumjev Junior KwikPen 100units/ml inj 3ml pre-filled pens",
    "0601011L0BDAAAG": "Lyumjev KwikPen 200units/ml inj 3ml pre-filled pens",
    "0601011L0BDAFAF": "Lyumjev Tempo Pen 100units/ml inj 3ml pre-filled pens",
    "0601011L0BBAAAA": "Humalog 100units/ml solution for injection 1.5ml cartridges",
    "0601011L0BBABAB": "Humalog 100units/ml solution for injection 10ml vials",
    "0601011L0BBACAC": "Humalog 100units/ml solution for injection 3ml cartridges",
    "0601011L0BBAIAF": "Humalog Junior KwikPen 100units/ml inj 3ml pre-filled pens",
    "0601011L0BBAGAF": "Humalog KwikPen 100units/ml inj 3ml pre-filled pens",
    "0601011L0BBAHAG": "Humalog KwikPen 200units/ml inj 3ml pre-filled pens",
    "0601011L0BBAFAF": "Humalog Pen 100units/ml inj 3ml pre-filled pens",
    "0601011L0BBAJAF": "Humalog Tempo Pen 100units/ml inj 3ml pre-filled pens",
    "0601011A0BBAAAA": "NovoRapid 100units/ml solution for injection 10ml vials",
    "0601011A0BBADAC": "NovoRapid FlexPen 100units/ml inj 3ml pre-filled pens",
    "0601011A0BBAEAC": "NovoRapid FlexTouch 100units/ml inj 3ml pre-filled pens",
    "0601011A0BBACAC": "NovoRapid Novolet 100units/ml solution for injection 3ml pre-filled pens",
    "0601011A0BBABAB": "NovoRapid Penfill 100units/ml inj 3ml cartridges",
    "0601011A0BBAFAD": "NovoRapid PumpCart 100units/ml inj 1.6ml cartridges",
    "0601011A0BCACAA": "Fiasp 100units/ml solution for injection 10ml vials",
    "0601011A0BCAAAC": "Fiasp FlexTouch 100units/ml inj 3ml pre-filled pens",
    "0601011A0BCABAB": "Fiasp Penfill 100units/ml inj 3ml cartridges",
    "0601011A0BDAAAB": "Trurapi 100units/ml solution for injection 3ml cartridges",
    "0601011A0BDABAC": "Trurapi 100units/ml inj 3ml pre-filled Solostar pens",
    "0601011A0BDACAA": "Trurapi 100units/ml solution for injection 10ml vial",
    "0601011P0BBAAAA": "Apidra 100units/ml solution for injection 10ml vials",
    "0601011P0BBABAB": "Apidra 100units/ml solution for injection 3ml cartridges",
    "0601011P0BBAEAC": "Apidra 100units/ml inj 3ml pre-filled SoloStar pens",
}

# Quantity basis confirmed against an independent source: code -> ("ml" | "count", source).
# A wrong basis puts unit figures out by a factor of 1.5 to 10.
#
# Checked on 30 September 2026 against the NHSBSA Secondary Care Medicines Data (SCMD_FINAL_202603),
# which reports quantity in the dm+d VMP unit of measure. That unit is ML for every lispro, aspart
# and glulisine VMP, with indicative costs of 1.87 to 1.96 pounds per ml for 3 ml devices, 1.89 for
# 1.6 ml cartridges, 1.40 to 1.66 for 10 ml vials and 3.93 for lispro U200. Multiplying by the fill
# volume reproduces the EPD actual cost per unit of quantity for July 2026 to within 1 to 2%
# (5.63 to 6.10 pounds for 3 ml devices, 3.00 for PumpCart, 14.0 to 16.5 for vials, 11.74 for
# U200), and treating EPD quantity as ml would put it 1.6 to 10 times above. So EPD quantity for
# these insulins counts devices (the dm+d unit dose), not ml. The script's cost-based inference
# reached the same answer for every presentation.
_BASIS_SOURCE = "count: EPD cost per quantity = SCMD dm+d cost per ml x fill volume (checked 2026-09-30)"
CONFIRMED_BASIS = {code: ("count", _BASIS_SOURCE) for code in FALLBACK}

# NHS list prices of these insulins sit near 1.6 to 2.1 pounds per 100 units (U100 and U200
# alike, since U200 is priced per unit). Used only to choose between the two basis hypotheses.
REF_COST_PER_100_UNITS = 1.9

# Colours: fixed categorical order from the dataviz reference palette, by brand.
COLOURS = {"Lyumjev": "#2a78d6", "Fiasp": "#eb6834", "Humalog": "#1baf7a", "NovoRapid": "#eda100",
           "Trurapi": "#e87ba4", "Apidra": "#4a3aa7"}
DEVICE_COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7"]


# ---------------------------------------------------------------------------------------- API

class Client:
    """Thin API client. Every response can be cached to disk so a run is reproducible and a
    rerun does not hit the API again."""

    def __init__(self, cache=None, pause=0.5):
        self.cache = Path(cache) if cache else None
        if self.cache:
            self.cache.mkdir(parents=True, exist_ok=True)
        self.pause = pause
        self.calls = 0

    def get(self, path, **params):
        params["format"] = "json"
        key = hashlib.sha1(json.dumps([path, sorted(params.items())]).encode()).hexdigest()[:16]
        if self.cache and (f := self.cache / f"{path}_{key}.json").exists():
            return json.loads(f.read_text())
        last = None
        for attempt in range(4):
            r = requests.get(f"{API}/{path}/", params=params, headers=HEADERS, timeout=120)
            self.calls += 1
            if r.status_code == 200:
                data = r.json()
                if self.cache:
                    f.write_text(json.dumps(data))
                time.sleep(self.pause)
                return data
            last = r
            time.sleep(2 ** attempt)
        last.raise_for_status()
        raise RuntimeError(f"{path} {params}: status {last.status_code}")


# ------------------------------------------------------------------------------ presentations

def discover(client):
    """Presentations per brand from the bnf_code endpoint, plus the fallback list. Returns the
    table and the codes discovery found that the fallback did not know about."""
    found = {}
    for brand, prefix in BRANDS.items():
        try:
            for hit in client.get("bnf_code", q=prefix) or []:
                code = hit.get("id", "")
                if len(code) == 15 and code.startswith(prefix):
                    found[code] = hit.get("name", code)
        except Exception as e:  # discovery is a convenience; the fallback covers it
            print(f"  discovery failed for {brand}: {e}", file=sys.stderr)
    new = sorted(set(found) - set(FALLBACK))
    rows = {**FALLBACK, **found}
    return rows, new


def classify(code, name):
    brand = next(b for b, p in BRANDS.items() if code.startswith(p))
    n = name.lower()
    conc = int(m.group(1)) if (m := re.search(r"(\d+)\s*units?/ml", n)) else 100
    m = re.search(r"(\d+(?:\.\d+)?)\s*ml\b", n)
    ml = float(m.group(1)) if m else None
    if "vial" in n:
        device, ml = "Vial", ml or 10.0
    elif "pumpcart" in n:
        device, ml = "PumpCart", ml or 1.6
    elif "cartridge" in n or "penfill" in n:
        device, ml = "Cartridge", ml or 3.0
    elif "junior" in n:
        device, ml = "Junior KwikPen", ml or 3.0
    elif "tempo" in n:
        device, ml = "Tempo Pen", ml or 3.0
    elif any(k in n for k in ("kwikpen", "flexpen", "flextouch", "novolet", "pen")):
        base = next((d for d in ["KwikPen", "FlexTouch", "FlexPen", "NovoLet"] if d.lower() in n), "Pen")
        device, ml = f"{base} U{conc}", ml or 3.0
    else:
        device, ml = "Other", ml or 3.0
    # Vials and pump cartridges are the rough pump-use proxy; everything else is pen-type use.
    segment = "Vial/pump" if device in ("Vial", "PumpCart") else "Pen/cartridge"
    return dict(code=code, name=name, brand=brand, device=device, units_per_ml=conc,
                ml_per_pack_unit=ml, segment=segment)


def infer_basis(df, conc, ml):
    """Two independent signals for whether `quantity` is ml or a count of devices.

    cost: under each hypothesis, what does 100 units cost? The one nearer the list price wins.
          The hypotheses differ by a factor of ml_per_pack_unit, so this is decisive for 3 ml and
          10 ml devices and weak for the 1.5 and 1.6 ml cartridges.
    qty/item: the median quantity on one prescription item. Kept for the diagnostics only; a
          single 10 ml vial is 10 in ml and 1 as a count, so a fixed threshold misreads vials.
    """
    ok = (df["quantity"] > 0) & (df["items"] > 0)
    d = df[ok]
    qty_per_item = float((d["quantity"] / d["items"]).median()) if len(d) else np.nan
    cost_per_qty = float(d["actual_cost"].sum() / d["quantity"].sum()) if len(d) else np.nan
    cost_ml = cost_per_qty / conc * 100          # pounds per 100 units if quantity is ml
    cost_count = cost_per_qty / (conc * ml) * 100  # pounds per 100 units if quantity is a count
    err_ml = abs(np.log(cost_ml / REF_COST_PER_100_UNITS))
    err_count = abs(np.log(cost_count / REF_COST_PER_100_UNITS))
    basis = "ml" if err_ml <= err_count else "count"
    confidence = "low" if ml < 2 or min(err_ml, err_count) > np.log(1.6) else "ok"
    return dict(median_qty_per_item=round(qty_per_item, 2),
                cost_per_100u_if_ml=round(cost_ml, 3), cost_per_100u_if_count=round(cost_count, 3),
                inferred_basis=basis, inference_confidence=confidence)


def units_per_quantity(p):
    return p["units_per_ml"] if p["basis"] == "ml" else p["units_per_ml"] * p["ml_per_pack_unit"]


# ---------------------------------------------------------------------------------- national

def month_index(start, end):
    return pd.date_range(start, end, freq="MS")


def national(client, pres_names):
    meta, frames = [], []
    for code, name in sorted(pres_names.items()):
        p = classify(code, name)
        data = client.get("spending", code=code)
        if not data:
            p.update(n_months=0, first_month=None, last_month=None, basis=None, basis_source="no data")
            meta.append(p)
            continue
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        for c in ("items", "quantity", "actual_cost"):
            df[c] = pd.to_numeric(df[c])
        p.update(infer_basis(df, p["units_per_ml"], p["ml_per_pack_unit"]))
        if code in CONFIRMED_BASIS:
            p["basis"], p["basis_source"] = CONFIRMED_BASIS[code]
        else:
            p["basis"], p["basis_source"] = p["inferred_basis"], "inferred from cost, UNVERIFIED"
        p.update(n_months=len(df), first_month=df.date.min().date(), last_month=df.date.max().date())
        df["units"] = df["quantity"] * units_per_quantity(p)
        frames.append(df.assign(code=code, name=name, brand=p["brand"], device=p["device"],
                                segment=p["segment"]))
        meta.append(p)
    return pd.DataFrame(meta), pd.concat(frames, ignore_index=True)


def gaps(allp, months):
    """Missing and zero months for each presentation between its first and last month, and
    for each brand across the whole window. Reported, never filled."""
    rows = []
    for code, g in allp.groupby("code"):
        span = months[(months >= g.date.min()) & (months <= g.date.max())]
        missing = sorted(set(span) - set(g.date))
        zero = sorted(g.loc[g.quantity <= 0, "date"])
        for d in missing:
            rows.append(dict(level="presentation", key=code, name=g.name.iat[0], date=d.date(), issue="missing"))
        for d in zero:
            rows.append(dict(level="presentation", key=code, name=g.name.iat[0], date=d.date(), issue="zero"))
    for brand, g in allp.groupby("brand"):
        for d in sorted(set(months) - set(g.date)):
            rows.append(dict(level="brand", key=brand, name=brand, date=d.date(), issue="missing"))
    return pd.DataFrame(rows, columns=["level", "key", "name", "date", "issue"])


def trend(series):
    """OLS slope of a monthly series in units per year, and the fitted change over the window."""
    s = series.dropna()
    if len(s) < 3:
        return np.nan
    x = (s.index - s.index[0]).days / 365.25
    return float(np.polyfit(x, s.values, 1)[0])


def device_stops(lyu, latest):
    rows = []
    for dev in lyu.columns:
        s = lyu[dev]
        nz = s[s > 0]
        last = nz.index.max() if len(nz) else None
        zero_months = s.index[(s.fillna(0) <= 0) & (s.index > (nz.index.min() if len(nz) else s.index.min()))]
        rows.append(dict(device=dev,
                         first_nonzero=nz.index.min().date() if len(nz) else None,
                         last_nonzero=last.date() if last is not None else None,
                         stopped=bool(last is not None and last < latest),
                         zero_or_missing_months_after_start=len(zero_months),
                         units_last_12m=float(s[s.index > latest - pd.DateOffset(months=12)].sum())))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------- ICB

def icb_pull(client, meta):
    rows = []
    for _, p in meta[meta.basis.notna()].iterrows():
        k = units_per_quantity(p)
        for r in client.get("spending_by_org", org_type="icb", code=p.code) or []:
            rows.append(dict(icb_code=r["row_id"], icb=r["row_name"], date=r["date"], code=p.code,
                             brand=p.brand, segment=p.segment, items=r["items"],
                             quantity=r["quantity"], units=float(r["quantity"]) * k))
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def icb_summary(icb, latest):
    last12 = icb[icb.date > latest - pd.DateOffset(months=12)]
    t = last12.pivot_table(index=["icb_code", "icb"], columns="brand", values="units", aggfunc="sum").fillna(0)
    for b in BRANDS:
        t[b] = t.get(b, 0.0)
    t["total_units"] = t[list(BRANDS)].sum(axis=1)
    for b in BRANDS:
        t[f"{b}_share_pct"] = t[b] / t["total_units"] * 100
    t["ultra_rapid_share_pct"] = t[ULTRA_RAPID].sum(axis=1) / t["total_units"] * 100
    t = t.sort_values("ultra_rapid_share_pct").reset_index()
    months_used = sorted(last12.date.unique())
    s = t["ultra_rapid_share_pct"]
    ly = t["Lyumjev_share_pct"]
    stats = dict(n_icbs=len(t), window_start=pd.Timestamp(months_used[0]).date(),
                 window_end=pd.Timestamp(months_used[-1]).date(), n_months=len(months_used),
                 ultra_min=s.min(), ultra_p10=s.quantile(0.1), ultra_median=s.median(),
                 ultra_p90=s.quantile(0.9), ultra_max=s.max(),
                 ultra_p90_p10_ratio=s.quantile(0.9) / s.quantile(0.1) if s.quantile(0.1) > 0 else np.inf,
                 lyumjev_p10=ly.quantile(0.1), lyumjev_median=ly.median(), lyumjev_p90=ly.quantile(0.9),
                 fiasp_lyumjev_corr=t["Fiasp_share_pct"].rank().corr(t["Lyumjev_share_pct"].rank()))
    return t, stats


# ------------------------------------------------------------------------ practice concentration

def practice_pull(client, meta, latest):
    """Practice-level Lyumjev units, and the denominator of practices prescribing any of the six
    brands, over the last 12 months. The API needs a date for practice queries, so this loops by
    month. Brand-level codes are tried first for the denominator (one call per brand-month); Lyumjev
    units are always pulled per presentation because U100 and U200 quantities cannot be summed."""
    months = month_index(latest - pd.DateOffset(months=11), latest)
    ds = [d.strftime("%Y-%m-%d") for d in months]
    probe = client.get("spending_by_org", org_type="practice", code=BRANDS["Lyumjev"], date=ds[-1]) or []
    brand_level_ok = len(probe) > 0
    any_rows = []
    for brand, prefix in BRANDS.items():
        if brand_level_ok:
            for d in ds:
                for r in client.get("spending_by_org", org_type="practice", code=prefix, date=d) or []:
                    any_rows.append(dict(practice=r["row_id"], brand=brand, items=r["items"]))
        else:
            for code in meta.loc[(meta.brand == brand) & meta.basis.notna(), "code"]:
                for d in ds:
                    for r in client.get("spending_by_org", org_type="practice", code=code, date=d) or []:
                        any_rows.append(dict(practice=r["row_id"], brand=brand, items=r["items"]))
    lyu_rows = []
    for _, p in meta[(meta.brand == "Lyumjev") & meta.basis.notna()].iterrows():
        k = units_per_quantity(p)
        for d in ds:
            for r in client.get("spending_by_org", org_type="practice", code=p.code, date=d) or []:
                lyu_rows.append(dict(practice=r["row_id"], practice_name=r.get("row_name"),
                                     date=d, device=p.device, units=float(r["quantity"]) * k))
    return pd.DataFrame(any_rows), pd.DataFrame(lyu_rows), brand_level_ok, ds


def concentration(any_rows, lyu_rows):
    presc = any_rows[any_rows["items"] > 0]
    by_brand = presc.groupby("brand").practice.nunique()
    n_any = presc.practice.nunique()
    per = lyu_rows.groupby("practice").units.sum().sort_values(ascending=False)
    per = per[per > 0]
    n_lyu = len(per)
    top = max(1, int(np.ceil(0.1 * n_lyu)))
    # Top 10% of all practices prescribing any rapid analogue, not only of Lyumjev prescribers.
    top_all = max(1, int(np.ceil(0.1 * n_any)))
    stats = dict(practices_any_rapid_analogue=n_any,
                 practices_any_lyumjev=n_lyu,
                 pct_practices_with_lyumjev=n_lyu / n_any * 100 if n_any else np.nan,
                 **{f"practices_prescribing_{b.lower()}": int(by_brand.get(b, 0)) for b in BRANDS},
                 lyumjev_units_share_top10pct_of_lyumjev_prescribers=per.iloc[:top].sum() / per.sum() * 100,
                 lyumjev_units_share_top10pct_of_all_practices=per.iloc[:top_all].sum() / per.sum() * 100,
                 lyumjev_units_gini=gini(per.values))
    table = per.rename("lyumjev_units_last12m").reset_index()
    table["rank"] = np.arange(1, len(table) + 1)
    table["cum_share_pct"] = table.lyumjev_units_last12m.cumsum() / table.lyumjev_units_last12m.sum() * 100
    return table, stats


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return np.nan
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


# -------------------------------------------------------------------------------------- charts

def charts(out, by_brand, share, ultra, lyu, seg_share, icb_t, latest, verified):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6,
                         "axes.edgecolor": "#8a8984", "axes.titlesize": 12, "axes.titleweight": "normal"})
    note = SOURCE_LINE + ("" if verified else "  Quantity basis inferred, not yet verified.")

    def finish(fig, ax, name):
        ax.axvline(latest, color="#8a8984", lw=0.8, ls=":")
        ax.annotate(f"latest {latest:%b %Y}", (latest, 1), xycoords=("data", "axes fraction"),
                    xytext=(-4, -4), textcoords="offset points", ha="right", va="top",
                    fontsize=8, color="#52514e")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        fig.text(0.01, 0.01, note, fontsize=7, color="#52514e")
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        fig.savefig(out / name, dpi=160)
        plt.close(fig)

    def label_ends(ax, frame, fmt):
        # Direct labels at the right-hand end, nudged apart so they cannot collide.
        last = frame.ffill().iloc[-1].dropna().sort_values()
        lo, hi = ax.get_ylim()
        gap = (hi - lo) * 0.05
        ys, prev = [], -np.inf
        for v in last.values:
            prev = max(v, prev + gap)
            ys.append(prev)
        for (b, v), y in zip(last.items(), ys):
            ax.annotate(f"{b} {fmt(v)}", (frame.index[-1], y), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8.5, color="#0b0b0b")

    fig, ax = plt.subplots(figsize=(10, 5))
    for b in BRANDS:
        if b in by_brand:
            ax.plot(by_brand.index, by_brand[b] / 1e6, color=COLOURS[b], lw=2, label=b)
    ax.set_ylabel("Million units per month")
    ax.set_ylim(bottom=0)
    ax.set_title("Rapid-acting analogue insulin units dispensed per month, England primary care", loc="left", pad=26)
    label_ends(ax, by_brand[[b for b in BRANDS if b in by_brand]] / 1e6, lambda v: f"{v:.0f}m")
    ax.set_xlim(right=by_brand.index[-1] + pd.DateOffset(months=9))
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, ncol=6)
    finish(fig, ax, "units_by_brand.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    for b in BRANDS:
        if b in share:
            ax.plot(share.index, share[b], color=COLOURS[b], lw=2, label=b)
    ax.set_ylabel("% of units across the six brands")
    ax.set_ylim(0, 100)
    ax.set_title("Brand share of rapid-acting analogue units", loc="left", pad=26)
    label_ends(ax, share[[b for b in BRANDS if b in share]], lambda v: f"{v:.1f}%")
    ax.set_xlim(right=share.index[-1] + pd.DateOffset(months=9))
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, ncol=6)
    finish(fig, ax, "share_by_brand.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(ultra.index, ultra["ultra_rapid_share_pct"], color="#b8b7b0", lw=1.2, label="Monthly")
    ax.plot(ultra.index, ultra["ultra_rapid_share_pct_12m_rolling"], color=COLOURS["Lyumjev"], lw=2,
            label="12-month rolling")
    ax.set_ylabel("% of rapid-acting analogue units")
    ax.set_ylim(bottom=0, top=max(5, ultra["ultra_rapid_share_pct"].max() * 1.25))
    ax.set_title("Ultra-rapid share (Lyumjev plus Fiasp) of rapid-acting analogue units", loc="left", pad=26)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, ncol=2)
    finish(fig, ax, "ultra_rapid_share.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    cols = list(lyu.columns)
    ax.stackplot(lyu.index, *[lyu[c].fillna(0) / 1e6 for c in cols], labels=cols,
                 colors=DEVICE_COLOURS[:len(cols)], edgecolor="white", linewidth=0.5)
    ax.set_ylabel("Million units per month")
    ax.set_title("Lyumjev units dispensed by device", loc="left")
    ax.legend(loc="upper left", frameon=False, ncol=3, fontsize=8)
    finish(fig, ax, "lyumjev_by_device.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    for seg, colour in (("Vial/pump", COLOURS["Fiasp"]), ("Pen/cartridge", COLOURS["Lyumjev"])):
        if seg in seg_share:
            ax.plot(seg_share.index, seg_share[seg], color=colour, lw=2, label=seg)
    ax.set_ylabel("Ultra-rapid % of units in segment")
    ax.set_ylim(bottom=0, top=seg_share.max().max() * 1.2)
    ax.set_title("Ultra-rapid share within vials and pump cartridges, and within pens and cartridges", loc="left", pad=26)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, ncol=2)
    finish(fig, ax, "ultra_rapid_share_by_segment.png")

    if icb_t is not None:
        t = icb_t.sort_values("ultra_rapid_share_pct")
        fig, ax = plt.subplots(figsize=(9, max(6, 0.2 * len(t) + 1.5)))
        y = np.arange(len(t))
        ax.barh(y, t["Lyumjev_share_pct"], color=COLOURS["Lyumjev"], height=0.72, label="Lyumjev",
                edgecolor="white", linewidth=0.8)
        ax.barh(y, t["Fiasp_share_pct"], left=t["Lyumjev_share_pct"], color=COLOURS["Fiasp"], height=0.72,
                label="Fiasp", edgecolor="white", linewidth=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([re.sub(r"^NHS |\s*Integrated Care Board$", "", n)[:48] for n in t["icb"]], fontsize=7)
        ax.set_xlabel("% of rapid-acting analogue units, last 12 months")
        ax.set_title("Ultra-rapid share by Integrated Care Board", loc="left")
        ax.grid(axis="y", visible=False)
        ax.legend(loc="lower right", frameon=False)
        ax.set_ylim(-0.7, len(t) - 0.3)
        fig.text(0.01, 0.005, note, fontsize=7, color="#52514e")
        fig.tight_layout(rect=(0, 0.02, 1, 1))
        fig.savefig(out / "icb_ultrarapid_share.png", dpi=160)
        plt.close(fig)


# ------------------------------------------------------------------------------------- summary

def fmt(x, nd=1):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:,.{nd}f}"


def write_summary(out, ctx):
    L = []
    w = L.append
    w("# Rapid-acting insulin in English primary care: generated summary\n")
    w(f"Pulled {ctx['pulled']}. Latest month in the data: {ctx['latest']:%B %Y}. "
      f"Window: {ctx['first']:%B %Y} to {ctx['latest']:%B %Y}. Generated by `rapid_insulin_units.py`; "
      "do not edit by hand.\n")
    w(SOURCE_LINE + "\n")
    if not ctx["verified"]:
        w("The quantity basis of some presentations is inferred from cost, not confirmed against dm+d. "
          f"Unverified: {', '.join(ctx['unverified'])}. Unit figures for those presentations are not "
          "publishable until `CONFIRMED_BASIS` is filled in.\n")
    if ctx["new_codes"]:
        w(f"Discovery found presentations not in the fallback list: {', '.join(ctx['new_codes'])}.\n")

    w("## Plausibility\n")
    w("| year to | " + " | ".join(BRANDS) + " | total (billion units) |")
    w("|---|" + "---|" * (len(BRANDS) + 1))
    for d, r in ctx["annual"].iterrows():
        w(f"| {d:%b %Y} | " + " | ".join(fmt(r.get(b, np.nan) / 1e9, 2) for b in BRANDS)
          + f" | {fmt(r['total'] / 1e9, 2)} |")
    w("")
    w(ctx["plausible_note"] + "\n")

    w("## 1. Units and share by brand, latest month\n")
    w("| brand | million units | share % |")
    w("|---|---|---|")
    for b in BRANDS:
        w(f"| {b} | {fmt(ctx['latest_units'].get(b, np.nan) / 1e6)} | {fmt(ctx['latest_share'].get(b, np.nan))} |")
    w("")

    w("## 2. Lyumjev by device\n")
    w("| device | first month | last month with units | stopped | units last 12 months (million) |")
    w("|---|---|---|---|---|")
    for _, r in ctx["stops"].iterrows():
        w(f"| {r.device} | {r.first_nonzero} | {r.last_nonzero} | {'yes' if r.stopped else 'no'} | "
          f"{fmt(r.units_last_12m / 1e6, 2)} |")
    w("")

    u = ctx["ultra"]
    w("## 3. Ultra-rapid share over time\n")
    w(f"Lyumjev plus Fiasp was {fmt(u['first12'])}% of units in the first 12 months of the window and "
      f"{fmt(u['last12'])}% in the last 12. The fitted trend over the whole window is "
      f"{fmt(u['slope_all'], 2)} percentage points a year, and {fmt(u['slope_24'], 2)} over the last 24 months. "
      f"Lyumjev alone: {fmt(u['lyu_first12'])}% to {fmt(u['lyu_last12'])}%.\n")

    if ctx.get("icb_stats"):
        s = ctx["icb_stats"]
        w("## 4. Variation between ICBs, last 12 months\n")
        w(f"{s['n_icbs']} ICBs, {s['window_start']:%b %Y} to {s['window_end']:%b %Y} ({s['n_months']} months). "
          f"Ultra-rapid share ranges from {fmt(s['ultra_min'])}% to {fmt(s['ultra_max'])}%, median "
          f"{fmt(s['ultra_median'])}%. The 10th percentile is {fmt(s['ultra_p10'])}% and the 90th "
          f"{fmt(s['ultra_p90'])}%, a ratio of {fmt(s['ultra_p90_p10_ratio'], 2)}. Lyumjev alone runs "
          f"{fmt(s['lyumjev_p10'])}% to {fmt(s['lyumjev_p90'])}% across the same percentiles. The rank "
          f"correlation between an ICB's Fiasp share and its Lyumjev share is {fmt(s['fiasp_lyumjev_corr'], 2)}.\n")
        t = ctx["icb_table"]
        for label, part in (("Highest five", t.tail(5).iloc[::-1]), ("Lowest five", t.head(5))):
            w(f"{label}:\n")
            w("| ICB | ultra-rapid % | Lyumjev % | Fiasp % | million units |")
            w("|---|---|---|---|---|")
            for _, r in part.iterrows():
                w(f"| {r.icb} | {fmt(r.ultra_rapid_share_pct)} | {fmt(r.Lyumjev_share_pct)} | "
                  f"{fmt(r.Fiasp_share_pct)} | {fmt(r.total_units / 1e6)} |")
            w("")

    if ctx.get("conc"):
        c = ctx["conc"]
        w("## 5. Concentration among practices, last 12 months\n")
        w(f"Brand-level codes accepted by `spending_by_org` for practices: "
          f"{'yes' if ctx['brand_level_ok'] else 'no, looped by presentation'}. "
          f"{c['practices_any_lyumjev']:,} of {c['practices_any_rapid_analogue']:,} practices prescribing any of "
          f"the six brands prescribed Lyumjev ({fmt(c['pct_practices_with_lyumjev'])}%). The top 10% of Lyumjev "
          f"prescribers account for {fmt(c['lyumjev_units_share_top10pct_of_lyumjev_prescribers'])}% of Lyumjev "
          f"units; the top 10% of all practices by Lyumjev volume account for "
          f"{fmt(c['lyumjev_units_share_top10pct_of_all_practices'])}%. Gini across Lyumjev prescribers "
          f"{fmt(c['lyumjev_units_gini'], 2)}.\n")
        w("| brand | practices prescribing |")
        w("|---|---|")
        for b in BRANDS:
            w(f"| {b} | {c[f'practices_prescribing_{b.lower()}']:,} |")
        w("")

    w("## 6. Vials and pump cartridges\n")
    w("| brand | vial/pump % of brand units, last 12 months |")
    w("|---|---|")
    for b, v in ctx["vial_share"].items():
        w(f"| {b} | {fmt(v)} |")
    w("")
    w(f"Ultra-rapid share within vials and pump cartridges: {fmt(ctx['seg_last12'].get('Vial/pump', np.nan))}%. "
      f"Within pens and cartridges: {fmt(ctx['seg_last12'].get('Pen/cartridge', np.nan))}%.\n")

    w("## Context: products outside the six brands, last 12 months\n")
    w("Not converted to units or counted in any share.\n")
    w("| product | prefix | items | quantity | cost (pounds) |")
    w("|---|---|---|---|---|")
    for _, r in ctx["context"].iterrows():
        w(f"| {r['product']} | {r['prefix']} | {fmt(r['items'], 0)} | {fmt(r['quantity'], 0)} | {fmt(r['actual_cost'], 0)} |")
    w("")

    w("## Gaps\n")
    g = ctx["gaps"]
    if len(g):
        w(f"{len(g)} presentation or brand months are missing or zero; see `gaps.csv`. They are not filled.\n")
    else:
        w("No missing or zero months inside any presentation's span.\n")

    w("## Sample for checking against the web UI\n")
    sm = ctx["sample"]
    w(f"{sm['name']} ({sm['code']}), {sm['date']:%B %Y}: {sm['items']:,.0f} items, quantity {sm['quantity']:,.0f}, "
      f"actual cost {sm['actual_cost']:,.2f} pounds. Compare with the national total for this code "
      "on the OpenPrescribing analyse page (https://openprescribing.net/analyse/).\n")
    (out / "SUMMARY.md").write_text("\n".join(L))


# ---------------------------------------------------------------------------------------- main

def run(client, out, skip_icb=False, skip_practice=False, pulled=None, absent_is_zero=False):
    """absent_is_zero: the source is known to be complete for every month in the window, so a
    brand with no rows in a month dispensed nothing that month. True for the EPD cache, where each
    monthly table is pulled whole and only rows with items appear; False for API responses, where
    a missing month may be a failed or truncated call."""
    out.mkdir(parents=True, exist_ok=True)
    print("Discovering presentations...")
    names, new_codes = discover(client)

    print("Pulling national monthly data...")
    meta, allp = national(client, names)
    for _, p in meta.iterrows():
        print(f"  {p['name'][:62]:62s} basis={str(p.basis):5s} ({p.basis_source})")
    latest, first = allp.date.max(), allp.date.min()
    months = month_index(first, latest)

    meta.to_csv(out / "presentations.csv", index=False)
    allp[["date", "code", "name", "brand", "device", "segment", "items", "quantity", "units", "actual_cost"]] \
        .sort_values(["date", "code"]).to_csv(out / "monthly_by_presentation.csv", index=False)
    gap = gaps(allp, months)
    gap.to_csv(out / "gaps.csv", index=False)

    # 1. Brand units and share. A brand-month with no rows stays empty rather than zero.
    by_brand = allp.pivot_table(index="date", columns="brand", values="units", aggfunc="sum").reindex(months)
    by_brand = by_brand[[b for b in BRANDS if b in by_brand]]
    # Months before a brand first appears are zero (not yet launched), not missing. Gaps after
    # its first month stay empty and keep the all-brand total empty for that month.
    for b in by_brand:
        by_brand.loc[by_brand.index < by_brand[b].first_valid_index(), b] = 0.0
    if absent_is_zero:
        by_brand = by_brand.fillna(0.0)
    total = by_brand.sum(axis=1, min_count=len(by_brand.columns))
    share = by_brand.div(total, axis=0) * 100
    by_brand.assign(total=total).to_csv(out / "monthly_units_by_brand.csv", index_label="date")
    share.round(3).to_csv(out / "monthly_share_by_brand.csv", index_label="date")

    # Plausibility: rolling 12-month totals at each year end counting back from the latest month.
    annual = by_brand.assign(total=total).rolling(12).sum().iloc[::-1].iloc[::12].dropna(how="all").iloc[::-1]
    ok = annual["total"].dropna().between(1e9, 2e10).all()
    plausible_note = ("Annual totals fall in the billions of units expected for England."
                      if ok else "WARNING: annual totals fall outside 1 to 20 billion units. The quantity "
                      "basis is probably wrong for at least one presentation. Do not publish.")
    print(plausible_note)

    # 2. Lyumjev by device.
    lyu = allp[allp.brand == "Lyumjev"].pivot_table(index="date", columns="device", values="units",
                                                    aggfunc="sum").reindex(months)
    lyu.to_csv(out / "lyumjev_monthly_by_device.csv", index_label="date")
    stops = device_stops(lyu, latest)
    stops.to_csv(out / "lyumjev_device_status.csv", index=False)

    # 3. Ultra-rapid trajectory.
    ultra = pd.DataFrame({"ultra_rapid_units": by_brand[[b for b in ULTRA_RAPID if b in by_brand]].sum(axis=1, min_count=1),
                          "all_brand_units": total})
    ultra["ultra_rapid_share_pct"] = ultra.ultra_rapid_units / ultra.all_brand_units * 100
    ultra["ultra_rapid_share_pct_12m_rolling"] = (ultra.ultra_rapid_units.rolling(12).sum()
                                                  / ultra.all_brand_units.rolling(12).sum() * 100)
    ultra["lyumjev_share_pct"] = share.get("Lyumjev")
    ultra["fiasp_share_pct"] = share.get("Fiasp")
    ultra.to_csv(out / "ultra_rapid_share_monthly.csv", index_label="date")
    last12 = ultra.index > latest - pd.DateOffset(months=12)
    first12 = ultra.index < first + pd.DateOffset(months=12)
    u = dict(first12=ultra[first12].ultra_rapid_units.sum() / ultra[first12].all_brand_units.sum() * 100,
             last12=ultra[last12].ultra_rapid_units.sum() / ultra[last12].all_brand_units.sum() * 100,
             lyu_first12=by_brand.loc[first12, "Lyumjev"].sum() / total[first12].sum() * 100,
             lyu_last12=by_brand.loc[last12, "Lyumjev"].sum() / total[last12].sum() * 100,
             slope_all=trend(ultra.ultra_rapid_share_pct),
             slope_24=trend(ultra.ultra_rapid_share_pct[ultra.index > latest - pd.DateOffset(months=24)]))

    # 6. Vial and pump segment.
    seg = allp.pivot_table(index=["date", "segment"], columns="brand", values="units", aggfunc="sum").fillna(0)
    seg_ultra = seg[[b for b in ULTRA_RAPID if b in seg]].sum(axis=1) / seg.sum(axis=1) * 100
    seg_share = seg_ultra.unstack("segment").reindex(months)
    seg_share.to_csv(out / "ultra_rapid_share_by_segment_monthly.csv", index_label="date")
    a12 = allp[allp.date > latest - pd.DateOffset(months=12)]
    b_seg = a12.pivot_table(index="brand", columns="segment", values="units", aggfunc="sum").fillna(0)
    vial_share = (b_seg.get("Vial/pump", 0) / b_seg.sum(axis=1) * 100).reindex(list(BRANDS))
    s_tot = a12.pivot_table(index="segment", columns="brand", values="units", aggfunc="sum").fillna(0)
    seg_last12 = (s_tot[[b for b in ULTRA_RAPID if b in s_tot]].sum(axis=1) / s_tot.sum(axis=1) * 100).to_dict()
    pd.DataFrame({"vial_pump_pct_of_brand_units_last12m": vial_share}).to_csv(out / "vial_share_by_brand.csv",
                                                                            index_label="brand")

    # Context products.
    ctx_rows = []
    for product, prefix in CONTEXT_PRODUCTS.items():
        try:
            d = pd.DataFrame(client.get("spending", code=prefix) or [])
        except Exception as e:
            print(f"  context pull failed for {product}: {e}", file=sys.stderr)
            d = pd.DataFrame()
        if len(d):
            d["date"] = pd.to_datetime(d["date"])
            d = d[d.date > latest - pd.DateOffset(months=12)]
        ctx_rows.append(dict(product=product, prefix=prefix,
                             items=pd.to_numeric(d.get("items", pd.Series(dtype=float))).sum(),
                             quantity=pd.to_numeric(d.get("quantity", pd.Series(dtype=float))).sum(),
                             actual_cost=pd.to_numeric(d.get("actual_cost", pd.Series(dtype=float))).sum()))
    context = pd.DataFrame(ctx_rows)
    context.to_csv(out / "context_products_last12m.csv", index=False)

    # 4. ICB variation.
    icb_t = icb_stats = None
    if not skip_icb:
        print("Pulling ICB-level data...")
        icb = icb_pull(client, meta)
        icb.to_csv(out / "icb_monthly_by_presentation.csv", index=False)
        icb_t, icb_stats = icb_summary(icb, latest)
        icb_t.round(3).to_csv(out / "icb_ultrarapid_share_last12m.csv", index=False)
        pd.Series(icb_stats).to_csv(out / "icb_variation_stats.csv", header=["value"], index_label="statistic")

    # 5. Practice concentration.
    conc = brand_level_ok = None
    if not skip_practice:
        print("Pulling practice-level data (12 months)...")
        any_rows, lyu_rows, brand_level_ok, _ = practice_pull(client, meta, latest)
        table, conc = concentration(any_rows, lyu_rows)
        table.to_csv(out / "practice_lyumjev_concentration.csv", index=False)
        pd.Series({**conc, "brand_level_codes_accepted": brand_level_ok}).to_csv(
            out / "practice_concentration_stats.csv", header=["value"], index_label="statistic")

    # A presentation with no rows has no basis and contributes no units, so it cannot be unverified.
    unverified = sorted(set(meta.loc[meta.basis.notna(), "code"]) - set(CONFIRMED_BASIS))
    verified = not unverified
    charts(out, by_brand, share, ultra, lyu, seg_share, icb_t, latest, verified)

    s_row = allp[(allp.code == "0601011L0BDADAF") & (allp.date == latest)]
    s_row = (s_row if len(s_row) else allp[allp.date == latest]).iloc[0]
    write_summary(out, dict(
        pulled=pulled or dt.date.today().isoformat(), latest=latest, first=first, verified=verified,
        unverified=unverified, new_codes=new_codes, annual=annual, plausible_note=plausible_note,
        latest_units=by_brand.iloc[-1].to_dict(), latest_share=share.iloc[-1].to_dict(), stops=stops,
        ultra=u, icb_stats=icb_stats, icb_table=icb_t, conc=conc, brand_level_ok=brand_level_ok,
        vial_share=vial_share.to_dict(), seg_last12=seg_last12, context=context, gaps=gap,
        sample=s_row.to_dict()))
    print(f"\nDone in {client.calls} API calls. Latest month: {latest:%B %Y}. Files in {out.resolve()}")
    if not verified:
        print("Quantity basis is inferred for some presentations; see presentations.csv. "
              "Fill in CONFIRMED_BASIS before publishing any unit figure.")
    return dict(meta=meta, allp=allp, by_brand=by_brand, share=share, ultra=ultra, icb=icb_t,
                icb_stats=icb_stats, conc=conc, stops=stops)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", choices=["epd", "openprescribing"], default="epd",
                    help="epd reads the cache filled by epd_source.py; openprescribing calls its API, "
                         "which refused scripted clients when this was written")
    ap.add_argument("--out-dir", default=Path(__file__).parent / "output", type=Path)
    ap.add_argument("--cache", default=Path(__file__).parent / "api_cache", type=Path,
                    help="directory for raw API responses (reused on rerun)")
    ap.add_argument("--skip-icb", action="store_true")
    ap.add_argument("--skip-practice", action="store_true")
    args = ap.parse_args()
    if args.source == "epd":
        from epd_source import EPDClient
        client = EPDClient()
    else:
        client = Client(cache=args.cache)
    run(client, args.out_dir, args.skip_icb, args.skip_practice, absent_is_zero=args.source == "epd")


if __name__ == "__main__":
    main()
