#!/usr/bin/env python3
"""
Hospital side of the rapid-acting insulin analysis. Reads hospital_cache/ (filled by
hospital_source.py) and the primary care outputs of rapid_insulin_units.py, and writes
output/hospital/.

Two questions. Does hospital prescribing, where many people start on ultra-rapid insulin, use a
higher ultra-rapid share than primary care? And how large is hospital supply against primary care,
which bounds how much the primary care analysis can be missing?

HPDC (hospital prescriptions dispensed in the community) answers the first by brand and device.
SCMD (hospital pharmacy stock issues) answers the second by molecule only, since it is coded by VMP
and the ultra-rapid products share VMPs with their standard counterparts.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

import rapid_insulin_units as R

HERE = Path(__file__).parent
CACHE = HERE / "hospital_cache"
PC = HERE / "output"
OUT = HERE / "output" / "hospital"
MOLECULE = {"Lyumjev": "lispro", "Humalog": "lispro", "NovoRapid": "aspart", "Fiasp": "aspart",
            "Trurapi": "aspart", "Apidra": "glulisine"}
# Trusts below this many units over the last 12 months are left out of the trust spread, because a
# share computed from a handful of prescriptions says nothing about practice. About 330 pens a year.
MIN_TRUST_UNITS = 100_000


def hpdc_table():
    h = pd.read_csv(CACHE / "hpdc_insulin.csv", dtype=str)
    for c in ("TOTAL_QUANTITY", "TOTAL_ITEMS", "TOTAL_ACTUAL_COST"):
        h[c] = pd.to_numeric(h[c])
    h["date"] = pd.to_datetime(h.PERIOD, format="%Y%m")
    h = h[h.BNF_CODE.str.startswith(tuple(R.BRANDS.values()))].copy()
    # HPDC names are abbreviated in the older files ("Ins NovoRapid_Inj 100u/ml 10ml Vl"), so the
    # device is read from the primary care name for the same BNF code where one exists.
    pc_names = pd.read_csv(PC / "presentations.csv").set_index("code")["name"].to_dict()
    names = {c: pc_names.get(c, n) for c, n in h.groupby("BNF_CODE").BNF_NAME.last().items()}
    meta = pd.DataFrame([R.classify(c, n) for c, n in names.items()]).set_index("code")
    # Quantity counts devices, as in primary care; checked below against cost per 100 units.
    meta["units_per_quantity"] = meta.units_per_ml * meta.ml_per_pack_unit
    h = h.join(meta[["brand", "device", "segment", "units_per_quantity"]], on="BNF_CODE")
    h["units"] = h.TOTAL_QUANTITY * h.units_per_quantity
    return h, meta


def scmd_table():
    s = pd.read_csv(CACHE / "scmd_insulin.csv", dtype={"YEAR_MONTH": str, "ODS_CODE": str})
    s = s[~s.VMP_PRODUCT_NAME.str.contains("biphasic", case=False)].copy()  # mixes are not rapid-acting
    assert (s.UNIT_OF_MEASURE_NAME.str.upper() == "ML").all(), s.UNIT_OF_MEASURE_NAME.unique()
    s["date"] = pd.to_datetime(s.YEAR_MONTH.str.replace("-", ""), format="%Y%m")
    s["molecule"] = s.VMP_PRODUCT_NAME.str.extract(r"Insulin (\w+)")[0]
    s["concentration"] = s.VMP_PRODUCT_NAME.str.extract(r"(\d+)units/ml")[0].astype(float)
    s["units"] = s.quantity * s.concentration
    s["device"] = np.select([s.VMP_PRODUCT_NAME.str.contains("vial"), s.VMP_PRODUCT_NAME.str.contains("1.6ml")],
                            ["Vial", "Pump cartridge"], "Pen or 3 ml cartridge")
    return s


def rolling_share(num, den, n=12):
    return num.rolling(n).sum() / den.rolling(n).sum() * 100


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    h, meta = hpdc_table()
    s = scmd_table()
    pc = pd.read_csv(PC / "monthly_units_by_brand.csv", index_col="date", parse_dates=True)
    brands = list(R.BRANDS)
    L = []
    w = L.append

    # ---- HPDC: basis check, brand units, ultra-rapid share.
    cost = h.groupby("brand").apply(lambda g: g.TOTAL_ACTUAL_COST.sum() / g.units.sum() * 100)
    hb = h.pivot_table(index="date", columns="brand", values="units", aggfunc="sum").reindex(columns=brands)
    months = pd.date_range(hb.index.min(), hb.index.max(), freq="MS")
    hb = hb.reindex(months).fillna(0.0)  # every monthly file was read whole: no row means none dispensed
    htot = hb.sum(axis=1)
    hshare = hb.div(htot, axis=0) * 100
    hultra = hb[R.ULTRA_RAPID].sum(axis=1)
    pultra = pc[R.ULTRA_RAPID].sum(axis=1)
    comp = pd.DataFrame({
        "hospital_units": htot, "hospital_ultra_pct": hultra / htot * 100,
        "hospital_ultra_pct_12m": rolling_share(hultra, htot),
        "primary_units": pc["total"], "primary_ultra_pct": pultra / pc["total"] * 100,
        "primary_ultra_pct_12m": rolling_share(pultra, pc["total"]),
    })
    comp["hospital_pct_of_community"] = comp.hospital_units / (comp.hospital_units + comp.primary_units) * 100
    comp.to_csv(OUT / "hpdc_vs_primary_monthly.csv", index_label="date")
    hb.assign(total=htot).to_csv(OUT / "hpdc_units_by_brand.csv", index_label="date")

    latest = min(hb.index.max(), pc.index.max())
    last12 = (comp.index > latest - pd.DateOffset(months=12)) & (comp.index <= latest)
    sum12 = comp[last12].sum()
    h12 = hb[(hb.index > latest - pd.DateOffset(months=12)) & (hb.index <= latest)].sum()
    p12 = pc.loc[(pc.index > latest - pd.DateOffset(months=12)) & (pc.index <= latest), brands].sum()

    w("# Hospital supply of rapid-acting insulin: generated summary\n")
    w(f"Generated by `hospital_analysis.py`; do not edit by hand. HPDC {months[0]:%B %Y} to {months[-1]:%B %Y}; "
      f"SCMD {s.date.min():%B %Y} to {s.date.max():%B %Y}; primary care {pc.index.min():%B %Y} to "
      f"{pc.index.max():%B %Y}. Comparison window for the last 12 months ends {latest:%B %Y}.\n")
    w("## Quantity basis in HPDC\n")
    w("Cost per 100 units with quantity read as a device count (primary care runs 1.6 to 2.0 pounds):\n")
    w("| brand | pounds per 100 units |")
    w("|---|---|")
    for b in brands:
        w(f"| {b} | {R.fmt(cost.get(b, np.nan), 2)} |")
    w("")

    w("## Hospital prescriptions dispensed in the community, last 12 months\n")
    w(f"{R.fmt(sum12.hospital_units / 1e6)} million units, against {R.fmt(sum12.primary_units / 1e6)} million "
      f"prescribed in primary care: hospital prescribers wrote "
      f"{R.fmt(sum12.hospital_units / (sum12.hospital_units + sum12.primary_units) * 100, 2)}% of rapid-acting "
      "analogue units dispensed in the community.\n")
    w("| brand | hospital share % | primary care share % |")
    w("|---|---|---|")
    for b in brands:
        w(f"| {b} | {R.fmt(h12[b] / h12.sum() * 100)} | {R.fmt(p12[b] / p12.sum() * 100)} |")
    hu12 = h12[R.ULTRA_RAPID].sum() / h12.sum() * 100
    pu12 = p12[R.ULTRA_RAPID].sum() / p12.sum() * 100
    w(f"| ultra-rapid (Lyumjev plus Fiasp) | {R.fmt(hu12)} | {R.fmt(pu12)} |")
    w("")

    # Trajectory: annual ultra-rapid share on both sides, years to the latest month.
    w("## Ultra-rapid share by year\n")
    w("| year to | hospital % | primary care % | hospital Lyumjev % | primary care Lyumjev % |")
    w("|---|---|---|---|---|")
    ends = [latest - pd.DateOffset(years=k) for k in range(9, -1, -1)]
    for e in ends:
        m = (hb.index > e - pd.DateOffset(months=12)) & (hb.index <= e)
        if m.sum() < 12:
            continue
        hs = hb[m].sum()
        pm = (pc.index > e - pd.DateOffset(months=12)) & (pc.index <= e)
        ps = pc.loc[pm, brands].sum() if pm.sum() == 12 else None
        w(f"| {e:%b %Y} | {R.fmt(hs[R.ULTRA_RAPID].sum() / hs.sum() * 100)} | "
          f"{R.fmt(ps[R.ULTRA_RAPID].sum() / ps.sum() * 100) if ps is not None else 'n/a'} | "
          f"{R.fmt(hs['Lyumjev'] / hs.sum() * 100)} | "
          f"{R.fmt(ps['Lyumjev'] / ps.sum() * 100) if ps is not None else 'n/a'} |")
    w("")
    first = {b: hb.index[hb[b] > 0].min() for b in brands}
    w("First month with hospital-prescribed units: " +
      "; ".join(f"{b} {first[b]:%b %Y}" if pd.notna(first[b]) else f"{b} none" for b in brands) + ".\n")

    # Lyumjev devices in HPDC.
    ly = h[h.brand == "Lyumjev"].pivot_table(index="date", columns="device", values="units", aggfunc="sum")
    ly = ly.reindex(months).fillna(0.0)
    ly.to_csv(OUT / "hpdc_lyumjev_by_device.csv", index_label="date")
    w("## Lyumjev by device, hospital prescriptions\n")
    w("| device | first month | last month | units last 12 months (thousand) |")
    w("|---|---|---|---|")
    for d in ly.columns:
        nz = ly.index[ly[d] > 0]
        w(f"| {d} | {nz.min():%b %Y} | {nz.max():%b %Y} | "
          f"{R.fmt(ly.loc[ly.index > latest - pd.DateOffset(months=12), d].sum() / 1e3)} |")
    w("")

    # Trust spread.
    t12 = h[(h.date > latest - pd.DateOffset(months=12)) & (h.date <= latest)]
    tt = t12.pivot_table(index=["HOSPITAL_TRUST_CODE"], columns="brand", values="units", aggfunc="sum").fillna(0)
    tt = tt.reindex(columns=brands, fill_value=0.0)
    tt["total"] = tt.sum(axis=1)
    tt["ultra_pct"] = tt[R.ULTRA_RAPID].sum(axis=1) / tt.total * 100
    tt["lyumjev_pct"] = tt.Lyumjev / tt.total * 100
    tnames = t12.groupby("HOSPITAL_TRUST_CODE").HOSPITAL_TRUST.last()
    tt = tt.join(tnames).sort_values("ultra_pct")
    tt.round(3).to_csv(OUT / "hpdc_trust_last12m.csv")
    big = tt[tt.total >= MIN_TRUST_UNITS]
    q = big.ultra_pct.quantile([0.1, 0.5, 0.9])
    w("## Variation between trusts, hospital prescriptions, last 12 months\n")
    w(f"{len(big)} of {len(tt)} trusts prescribed at least {MIN_TRUST_UNITS:,} units (together "
      f"{R.fmt(big.total.sum() / tt.total.sum() * 100)}% of hospital-prescribed units). Their ultra-rapid share "
      f"ranges from {R.fmt(big.ultra_pct.min())}% to {R.fmt(big.ultra_pct.max())}%, median {R.fmt(q[0.5])}%, "
      f"10th percentile {R.fmt(q[0.1])}%, 90th {R.fmt(q[0.9])}%. Trusts with no Lyumjev: "
      f"{(big.Lyumjev == 0).sum()}; with no Fiasp: {(big.Fiasp == 0).sum()}.\n")
    w("| trust | ultra-rapid % | Lyumjev % | thousand units |")
    w("|---|---|---|---|")
    for _, r in pd.concat([big.tail(5).iloc[::-1], big.head(5)]).iterrows():
        w(f"| {r.HOSPITAL_TRUST.title()} | {R.fmt(r.ultra_pct)} | {R.fmt(r.lyumjev_pct)} | {R.fmt(r.total / 1e3)} |")
    w("")

    # ---- SCMD: hospital stock issues by molecule against primary care.
    sm = s.pivot_table(index="date", columns="molecule", values="units", aggfunc="sum")
    sm.to_csv(OUT / "scmd_units_by_molecule.csv", index_label="date")
    pm = pc[brands].T.groupby(MOLECULE).sum().T
    both = sm.index.intersection(pm.index)
    s_end = both.max()
    s12 = sm.loc[both[both > s_end - pd.DateOffset(months=12)]].sum()
    p12m = pm.loc[both[both > s_end - pd.DateOffset(months=12)]].sum()
    w(f"## Hospital pharmacy issues (SCMD), 12 months to {s_end:%B %Y}\n")
    w("Rapid-acting analogues only (biphasic mixes excluded). SCMD cannot separate brands, because "
      "Lyumjev and Humalog share a dm+d VMP, as do Fiasp, NovoRapid and Trurapi.\n")
    w("| molecule | hospital issues (million units) | primary care (million units) | hospital as % of primary care |")
    w("|---|---|---|---|")
    for m in ("lispro", "aspart", "glulisine"):
        w(f"| {m} | {R.fmt(s12.get(m, np.nan) / 1e6)} | {R.fmt(p12m.get(m, np.nan) / 1e6)} | "
          f"{R.fmt(s12.get(m, np.nan) / p12m.get(m, np.nan) * 100)} |")
    w(f"| all | {R.fmt(s12.sum() / 1e6)} | {R.fmt(p12m.sum() / 1e6)} | {R.fmt(s12.sum() / p12m.sum() * 100)} |")
    w("")
    sy = sm.sum(axis=1).resample("YS-APR").sum()
    w("Hospital issues by financial year (million units): " +
      "; ".join(f"{d.year}/{str(d.year + 1)[2:]} {R.fmt(v / 1e6)}" for d, v in sy.items()) + ".\n")
    sd = s[s.date > s_end - pd.DateOffset(months=12)].groupby("device").units.sum()
    w("Device mix of hospital issues, same 12 months: " +
      "; ".join(f"{d} {R.fmt(v / sd.sum() * 100)}%" for d, v in sd.items()) + ".\n")

    (OUT / "SUMMARY.md").write_text("\n".join(L))
    charts(comp, hshare, sm, pm)
    print("\n".join(L))


def charts(comp, hshare, sm, pm):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6,
                         "axes.edgecolor": "#8a8984", "axes.titlesize": 12})
    note = "Source: NHSBSA hospital prescribing dispensed in the community; English Prescribing Dataset; SCMD."

    def finish(fig, ax, name):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        fig.text(0.01, 0.01, note, fontsize=7, color="#52514e")
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        fig.savefig(OUT / name, dpi=160)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(comp.index, comp.hospital_ultra_pct, color="#b8b7b0", lw=1)
    ax.plot(comp.index, comp.hospital_ultra_pct_12m, color="#eb6834", lw=2, label="Hospital prescribers, 12-month")
    ax.plot(comp.index, comp.primary_ultra_pct_12m, color="#2a78d6", lw=2, label="Primary care, 12-month")
    ax.set_ylabel("Lyumjev plus Fiasp, % of rapid-acting analogue units")
    ax.set_ylim(bottom=0)
    ax.set_title("Ultra-rapid share: hospital prescriptions against primary care", loc="left", pad=26)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, ncol=2)
    finish(fig, ax, "ultra_rapid_hospital_vs_primary.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    for b in R.BRANDS:
        ax.plot(hshare.index, hshare[b].rolling(3).mean(), color=R.COLOURS[b], lw=2, label=b)
    ax.set_ylabel("% of hospital-prescribed units (3-month mean)")
    ax.set_ylim(0, 100)
    ax.set_title("Brand share of hospital prescriptions dispensed in the community", loc="left", pad=26)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, ncol=6)
    finish(fig, ax, "hpdc_share_by_brand.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    cols = {"lispro": "#1baf7a", "aspart": "#eda100", "glulisine": "#4a3aa7"}
    for m, c in cols.items():
        if m in sm:
            ratio = sm[m].rolling(12).sum() / pm[m].rolling(12).sum().reindex(sm.index) * 100
            ax.plot(sm.index, ratio, color=c, lw=2, label=m)
    ax.set_ylabel("Hospital issues as % of primary care units, 12-month")
    ax.set_ylim(bottom=0)
    ax.set_title("Hospital pharmacy issues relative to primary care, by molecule", loc="left", pad=26)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, ncol=3)
    finish(fig, ax, "scmd_vs_primary.png")


if __name__ == "__main__":
    main()
