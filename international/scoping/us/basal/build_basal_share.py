"""Long-acting analogue insulin shares by year for Medicare Part D and Medicaid, and a
years-since-launch comparison of degludec with the ultra-rapid insulins (Fiasp plus Lyumjev).

Denominator: every long-acting analogue, i.e. degludec, glargine 300 U/ml, glargine 100 U/ml in
any form (Lantus, unbranded Lantus, Basaglar, Semglee in both its original and its glargine-yfgn
form, unbranded glargine-yfgn, Rezvoglar), and detemir. NPH, premixes and the fixed-ratio GLP-1
combinations (Xultophy, Soliqua) are excluded.

Units: both sources report insulin in millilitres (Part D Tot_Dsg_Unts; SDUD units_reimbursed),
so insulin units = ml x concentration (100, 200 or 300 U/ml). Shares are of insulin units, which
weights a 300 U/ml pen by its insulin content; this is a modelling choice and the alternative,
share of claims, would count a Toujeo pen fill the same as a Lantus one.

Part D (2015-2024): Spending by Drug, every annual release (extract_partd_spending.py); each
brand-year is taken from the latest release that contains it, because a release drops brand
names absent from its final year (the original Semglee is missing from DY24, for example).
One Part D brand name mixes concentrations. "Insulin Glargine Solostar" was Sanofi's unbranded
Lantus SoloStar (100 U/ml) until 2023, priced at $11.80/ml in 2023; in 2024 it also took in
unbranded Toujeo SoloStar (300 U/ml, NDC 00955-3900, launched April 2023 per the FDA NDC
directory) and its average rose to $19.76/ml. The 300 U/ml fraction of its 2024 millilitres is
estimated from price as (19.76 - p100) / (p300 - p100), with p100 its own 2023 price and p300
the 2024 price of "Insulin Glargine Max Solostar" (300 U/ml only). The quantity involved is
353,108 ml in 2024, about 0.1 % of long-acting units either way.

Medicaid (2015-2025): SDUD national rows (state XX), fee-for-service plus managed care, by NDC
(pull_medicaid_sdud_basal.py), classified from RxNorm names (lookup_ndc_basal.py). Cells with
fewer than 11 prescriptions are suppressed by CMS and contribute nothing.

Outputs: basal_share_by_year.csv, basal_units_by_product_year.csv, years_since_launch.csv.
Run from this folder: python3 build_basal_share.py
"""
import pandas as pd

CLASSES = ["degludec", "glargine300", "glargine100", "detemir"]

# Part D brand name -> (product label, class, U/ml)
PARTD = {
    "Tresiba": ("Tresiba", "degludec", 100),
    "Tresiba Flextouch U-100": ("Tresiba", "degludec", 100),
    "Tresiba Flextouch U-200": ("Tresiba", "degludec", 200),
    "Insulin Degludec": ("Insulin degludec (unbranded)", "degludec", 100),
    "Insulin Degludec Pen (U-100)": ("Insulin degludec (unbranded)", "degludec", 100),
    "Insulin Degludec Pen (U-200)": ("Insulin degludec (unbranded)", "degludec", 200),
    "Toujeo Solostar": ("Toujeo", "glargine300", 300),
    "Toujeo Max Solostar": ("Toujeo", "glargine300", 300),
    "Insulin Glargine Max Solostar": ("Insulin glargine U-300 (unbranded)", "glargine300", 300),
    "Insulin Glargine Solostar": ("Insulin glargine (unbranded Lantus)", "glargine100", 100),  # split in 2024
    "Insulin Glargine": ("Insulin glargine (unbranded Lantus)", "glargine100", 100),
    "Lantus": ("Lantus", "glargine100", 100),
    "Lantus Solostar": ("Lantus", "glargine100", 100),
    "Basaglar Kwikpen U-100": ("Basaglar", "glargine100", 100),
    "Basaglar Tempo Pen U-100": ("Basaglar", "glargine100", 100),
    "Semglee": ("Semglee (glargine, pre-yfgn)", "glargine100", 100),
    "Semglee Pen": ("Semglee (glargine, pre-yfgn)", "glargine100", 100),
    "Semglee (Yfgn)": ("Semglee (glargine-yfgn)", "glargine100", 100),
    "Semglee (Yfgn) Pen": ("Semglee (glargine-yfgn)", "glargine100", 100),
    "Insulin Glargine-Yfgn": ("Insulin glargine-yfgn (unbranded)", "glargine100", 100),
    "Rezvoglar Kwikpen": ("Rezvoglar (glargine-aglr)", "glargine100", 100),
    "Levemir": ("Levemir", "detemir", 100),
    "Levemir Flexpen": ("Levemir", "detemir", 100),
    "Levemir Flextouch": ("Levemir", "detemir", 100),
}

# US launch years (first calendar year with sales). Approval dates and sources are in route.csv.
LAUNCH = {"degludec (Tresiba)": 2016, "ultra-rapid (Fiasp)": 2018, "Lyumjev": 2020}


def partd_units():
    d = pd.read_csv("partd_spending_insulin_releases.csv")
    d = d[d.brand.isin(PARTD) & d.dsg_units_ml.notna() & (d.year >= 2015)]
    d = d.sort_values("release").groupby(["brand", "year"]).tail(1).copy()
    d["product"] = d.brand.map(lambda b: PARTD[b][0])
    d["cls"] = d.brand.map(lambda b: PARTD[b][1])
    d["conc"] = d.brand.map(lambda b: PARTD[b][2])
    # split "Insulin Glargine Solostar" 2024 between 100 and 300 U/ml by price
    sel = (d.brand == "Insulin Glargine Solostar") & (d.year == 2024)
    if sel.any():
        p = d.loc[sel, "avg_spend_per_unit"].iloc[0]
        p100 = d.loc[(d.brand == "Insulin Glargine Solostar") & (d.year == 2023), "avg_spend_per_unit"].iloc[0]
        p300 = d.loc[(d.brand == "Insulin Glargine Max Solostar") & (d.year == 2024), "avg_spend_per_unit"].iloc[0]
        f300 = (p - p100) / (p300 - p100)
        print(f"Insulin Glargine Solostar 2024: p={p:.2f} p100={p100:.2f} p300={p300:.2f} "
              f"-> 300 U/ml fraction of ml {f300:.3f}")
        r = d.loc[sel].iloc[0].copy()
        d.loc[sel, "dsg_units_ml"] = r.dsg_units_ml * (1 - f300)
        r300 = r.copy()
        r300["dsg_units_ml"] = r.dsg_units_ml * f300
        r300["product"], r300["cls"], r300["conc"] = "Insulin glargine U-300 (unbranded)", "glargine300", 300
        d = pd.concat([d, r300.to_frame().T], ignore_index=True)
    d["units"] = d.dsg_units_ml.astype(float) * d.conc.astype(float)
    return d[["year", "product", "cls", "units"]]


def medicaid_units():
    m = pd.read_csv("medicaid_sdud_basal_XX.csv", dtype={"ndc": str})
    lk = pd.read_csv("ndc_lookup_basal.csv", dtype={"ndc": str}).set_index("ndc")
    bad = sorted(set(m.ndc) - set(lk.index)) + list(lk.index[lk.cls == "unresolved"])
    if bad:
        print("WARNING unresolved NDCs:", bad)
    m = m[m.ndc.map(lk.cls).isin(CLASSES) & (m.year <= 2025)].copy()
    m["cls"] = m.ndc.map(lk.cls)
    m["conc"] = m.ndc.map(lk.conc_u_per_ml).astype(float)

    def label(n):
        r = lk.loc[n]
        if isinstance(r.brand, str):
            if r.brand == "Semglee":
                return "Semglee (glargine-yfgn)" if "yfgn" in r.rxnav_name else "Semglee (glargine, pre-yfgn)"
            if r.brand == "Rezvoglar":
                return "Rezvoglar (glargine-aglr)"
            return r.brand
        if r.molecule == "degludec":
            return "Insulin degludec (unbranded)"
        if "yfgn" in r.rxnav_name:
            return "Insulin glargine-yfgn (unbranded)"
        return "Insulin glargine U-300 (unbranded)" if r.conc_u_per_ml == 300 else "Insulin glargine (unbranded Lantus)"

    m["product"] = m.ndc.map(label)
    m["units"] = m.units_reimbursed.astype(float) * m.conc
    return m[["year", "product", "cls", "units"]]


def shares(u, country, basis, note):
    rows = []
    for y, g in u.groupby("year"):
        c = g.groupby("cls").units.sum()
        tot = c.sum()
        g100 = g[g.cls == "glargine100"].groupby("product").units.sum().sort_values(ascending=False)
        named = "; ".join(f"{p} {v / tot * 100:.1f}%" for p, v in g100.items() if v > 0)
        rows.append(dict(country=country, year=int(y),
                         **{f"{k}_pct": round(c.get(k, 0) / tot * 100, 2) for k in CLASSES},
                         total_units_m=round(tot / 1e6, 1), basis=basis,
                         note=f"{note}; glargine 100 U/ml comprises: {named}"))
    return rows


def main():
    pu, mu = partd_units(), medicaid_units()
    rows = shares(pu, "US Medicare Part D", "Part D Spending by Drug, insulin units (ml x U/ml)",
                  "gross Part D claims all plans; each brand-year from latest release containing it")
    rows += shares(mu, "US Medicaid", "Medicaid SDUD national rows, insulin units (ml x U/ml)",
                   "FFS + managed care; cells with <11 prescriptions suppressed")
    out = pd.DataFrame(rows)
    out.to_csv("basal_share_by_year.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.drop(columns="note").to_string())

    prod = pd.concat([pu.assign(country="US Medicare Part D"), mu.assign(country="US Medicaid")])
    pt = (prod.groupby(["country", "year", "cls", "product"]).units.sum() / 1e6).round(3)
    pt.rename("units_m").reset_index().to_csv("basal_units_by_product_year.csv", index=False)

    # years since launch: degludec share of long-acting vs ultra-rapid share of rapid-acting
    ultra = pd.read_csv("../ultra_share_by_year.csv")
    ultra["country"] = ultra.basis.str.contains("Medicaid").map({True: "US Medicaid", False: "US Medicare Part D"})
    yl = []
    for country in ["US Medicare Part D", "US Medicaid"]:
        b = out[out.country == country].set_index("year")
        u = ultra[ultra.country == country].set_index("year")
        for k in range(0, 10):
            yd, yf = LAUNCH["degludec (Tresiba)"] + k, LAUNCH["ultra-rapid (Fiasp)"] + k
            yl.append(dict(country=country, launch_year_index=k + 1,
                           degludec_year=yd, degludec_pct=b.degludec_pct.get(yd),
                           ultra_year=yf, ultra_pct=u.ultra_pct.get(yf),
                           ultra_basis=u.basis.get(yf)))
    yl = pd.DataFrame(yl)
    yl.to_csv("years_since_launch.csv", index=False)
    print(yl.to_string())


if __name__ == "__main__":
    main()
