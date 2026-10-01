#!/usr/bin/env python3
"""
What each branded rapid-acting analogue is worth in each market with open spending data, to set
Lilly's "commercial reasons" against the money at stake. Figures are what the payer spent at list or
reimbursement prices in the latest complete year, by brand and manufacturer. They are not the
manufacturer's net revenue: US prices are subject to confidential rebates, and European pharmacy and
wholesale margins are included. They show the relative size of each brand within a market.

Sources and bases (latest full period in each):
    England          primary care actual cost, Aug 2025 to Jul 2026 (output/history)
    Scotland         gross ingredient cost, Jul 2025 to Jun 2026
    Wales, N Ireland actual cost, Jul 2025 to Jun 2026
    France           Open Medic amount reimbursed (REM), 2025, euros
    Denmark          medstat.dk primary-sector turnover, 2025, thousand kroner
    US Medicare D    Part D total spending, 2024, dollars
    US Medicaid      State Drug Utilization Data total amount reimbursed, 2025, dollars
Manufacturer: Lilly (Lyumjev, Humalog, Liprolog, unbranded US insulin lispro), Novo Nordisk (Fiasp,
NovoRapid/Novolog, unbranded US insulin aspart), Sanofi (Apidra, Admelog, Trurapi, Insulin aspart
or lispro Sanofi, Merilog), Biocon (Kirsty). Writes output/commercial_value.csv and COMMERCIAL.md.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
SC = HERE / "scoping"
sys.path.insert(0, str(SC / "us"))
from us_provisional_shares import NDC, PARTD  # noqa: E402

PREFIX = {"0601011L0BD": "Lyumjev", "0601011L0BB": "Humalog", "0601011A0BC": "Fiasp", "0601011A0BB": "NovoRapid",
          "0601011P0BB": "Apidra", "0601011A0BD": "Trurapi", "0601011L0BE": "Admelog", "0601011L0BC": "Insulin lispro Sanofi"}
MAKER = {"Lyumjev": "Lilly", "Humalog": "Lilly", "Liprolog": "Lilly", "Insulin lispro (unbranded)": "Lilly",
         "Fiasp": "Novo Nordisk", "NovoRapid": "Novo Nordisk", "Novolog": "Novo Nordisk",
         "Insulin aspart (unbranded)": "Novo Nordisk", "Apidra": "Sanofi", "Admelog": "Sanofi", "Trurapi": "Sanofi",
         "Insulin aspart Sanofi": "Sanofi", "Insulin lispro Sanofi": "Sanofi", "Merilog": "Sanofi", "Kirsty": "Biocon"}


def uk():
    rows = []
    e = pd.read_csv(HERE.parent / "output" / "history" / "national_by_presentation.csv", parse_dates=["date"])
    e = e[(e.date > "2025-07-01") & (e.date <= "2026-07-01")]
    e["brand"] = e.code.str[:11].map(PREFIX)
    rows += [dict(market="England (GBP)", brand=b, spend=v) for b, v in e.groupby("brand").actual_cost.sum().items()]
    for f, label in (("scotland", "Scotland (GBP)"), ("wales", "Wales (GBP)"), ("ni", "Northern Ireland (GBP)")):
        d = pd.read_csv(HERE / "output" / f"{f}_by_presentation.csv", dtype={"month": str, "code": str})
        d = d[(d.month >= "202507") & (d.month <= "202606")]
        d["brand"] = d.code.str[:11].map(PREFIX)
        rows += [dict(market=label, brand=b, spend=v) for b, v in d.groupby("brand").cost.sum().items()]
    return rows


def france():
    r = pd.read_csv(SC / "france" / "open_medic_rapid_insulin_rows.csv", dtype={"CIP13": str})
    pc = pd.read_csv(SC / "france" / "product_codes.csv", dtype={"cip13": str}).set_index("cip13").brand
    r = r[r.year == 2025]
    r["rem"] = pd.to_numeric(r.REM.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    r["brand"] = r.CIP13.map(pc).replace({"Insuline asparte Sanofi": "Insulin aspart Sanofi"})
    return [dict(market="France (EUR)", brand=b, spend=v) for b, v in r.groupby("brand").rem.sum().items()]


def denmark():
    d = pd.read_csv(SC / "denmark" / "rapid_packages_by_year.csv", dtype={"pkg": str, "sector": str})
    lk = pd.read_csv(SC / "denmark" / "rapid_package_lookup.csv", dtype={"pkg": str}).drop_duplicates("pkg")
    d = d[(d.year == 2025) & (d.sector == "100")]
    d = d.merge(lk[["pkg", "product"]], on="pkg", how="left")
    d["brand"] = d["product"].str.split().str[0].str.replace('"', "").str.title()
    d["brand"] = d.brand.replace({"Novorapid": "NovoRapid", "Insulin": "Insulin aspart Sanofi"})
    d["spend"] = pd.to_numeric(d.a2_turnover_kdkk, errors="coerce") * 1000
    return [dict(market="Denmark (DKK)", brand=b, spend=v) for b, v in d.groupby("brand").spend.sum().items()]


def usa():
    p = pd.read_csv(SC / "us" / "partd_spending_by_drug_DY24.csv")
    p = p[(p.Mftr_Name == "Overall") & p.Brnd_Name.isin(PARTD)]
    p["brand"] = p.Brnd_Name.map(lambda b: PARTD[b][0])
    rows = [dict(market="US Medicare Part D (USD)", brand=b, spend=v)
            for b, v in p.groupby("brand").Tot_Spndng_2024.sum().items()]
    m = pd.read_csv(SC / "us" / "medicaid_sdud_insulin_XX.csv", dtype={"ndc": str})
    m = m[(m.year == 2025) & m.ndc.isin(NDC)]
    m["brand"] = m.ndc.map(lambda n: NDC[n][0])
    rows += [dict(market="US Medicaid (USD)", brand=b, spend=v)
             for b, v in m.groupby("brand").total_amount_reimbursed.sum().items()]
    return rows


def main():
    d = pd.DataFrame(uk() + france() + denmark() + usa())
    d = d[d.spend > 0]
    d["maker"] = d.brand.map(MAKER).fillna("other")
    d["pct_of_market"] = d.spend / d.groupby("market").spend.transform("sum") * 100
    d["pct_of_maker_in_market"] = d.spend / d.groupby(["market", "maker"]).spend.transform("sum") * 100
    d.round(1).to_csv(HERE / "output" / "commercial_value.csv", index=False)
    L = ["# Commercial value of rapid-acting analogue brands: generated summary\n",
         "Generated by `commercial_value.py`. Payer spending in the latest full period, by brand; not "
         "manufacturer net revenue. Bases in the script docstring.\n"]
    for mk, g in d.groupby("market", sort=False):
        g = g.sort_values("spend", ascending=False)
        L += [f"## {mk}\n", "| brand | maker | spend (million) | % of market | % of maker's rapid-acting spend |",
              "|---|---|---|---|---|"]
        for _, r in g.iterrows():
            L.append(f"| {r.brand} | {r.maker} | {r.spend / 1e6:,.2f} | {r.pct_of_market:.1f} | {r.pct_of_maker_in_market:.1f} |")
        L.append("")
    (HERE / "output" / "COMMERCIAL.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
