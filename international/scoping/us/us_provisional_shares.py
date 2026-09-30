"""Provisional ultra-rapid share of rapid-acting analogue insulin in two US
public sources. Mixes, basal insulins and human insulin are excluded; the
denominator is every rapid-acting analogue (aspart, lispro, glulisine, in
any brand, unbranded or biosimilar form, plus Fiasp and Lyumjev).

1. Medicaid SDUD, national rows (state XX), by NDC and quarter.
   units_reimbursed is in millilitres for insulin (NCPDP billing unit),
   so insulin units = ml x concentration (100 or 200 U/ml).
2. Medicare Part D Spending by Drug (2020-2024), by brand name.
   Tot_Dsg_Unts is also in millilitres for insulin.
"""
import pandas as pd

# class: 'ultra' or 'standard'; conc in U/ml
NDC = {
    # Fiasp (Novo Nordisk, labeler 00169)
    "00169320111": ("Fiasp", "ultra", 100), "00169320415": ("Fiasp", "ultra", 100),
    "00169320511": ("Fiasp", "ultra", 100), "00169320515": ("Fiasp", "ultra", 100),
    "00169320611": ("Fiasp", "ultra", 100), "00169320615": ("Fiasp", "ultra", 100),
    # Lyumjev (Eli Lilly, labeler 00002)
    "00002772801": ("Lyumjev", "ultra", 100), "00002820701": ("Lyumjev", "ultra", 100),
    "00002820705": ("Lyumjev", "ultra", 100), "00002822801": ("Lyumjev", "ultra", 200),
    "00002822827": ("Lyumjev", "ultra", 200), "00002823505": ("Lyumjev", "ultra", 100),
    # Novolog
    "00169750111": ("Novolog", "standard", 100), "00169210011": ("Novolog", "standard", 100),
    "00169633910": ("Novolog", "standard", 100), "00169210112": ("Novolog", "standard", 100),
    "00169210125": ("Novolog", "standard", 100), "00169330312": ("Novolog", "standard", 100),
    # Insulin aspart, unbranded Novolog (Novo Nordisk Pharma, labeler 73070)
    "73070010011": ("Insulin aspart (unbranded)", "standard", 100),
    "73070010210": ("Insulin aspart (unbranded)", "standard", 100),
    "73070010215": ("Insulin aspart (unbranded)", "standard", 100),
    "73070010310": ("Insulin aspart (unbranded)", "standard", 100),
    "73070010315": ("Insulin aspart (unbranded)", "standard", 100),
    # Biosimilar aspart
    "00024592700": ("Merilog", "standard", 100), "00024592805": ("Merilog", "standard", 100),
    "83257000711": ("Kirsty", "standard", 100), "83257000832": ("Kirsty", "standard", 100),
    # Humalog
    "00002751001": ("Humalog", "standard", 100), "00002751017": ("Humalog", "standard", 100),
    "00002751601": ("Humalog", "standard", 100), "00002751659": ("Humalog", "standard", 100),
    "00002753301": ("Humalog", "standard", 100), "00002771201": ("Humalog", "standard", 200),
    "00002771227": ("Humalog", "standard", 200), "00002771401": ("Humalog", "standard", 100),
    "00002771459": ("Humalog", "standard", 100), "00002879901": ("Humalog", "standard", 100),
    "00002879959": ("Humalog", "standard", 100), "00002821305": ("Humalog", "standard", 100),
    "00002872501": ("Humalog", "standard", 100),
    # Insulin lispro, unbranded Humalog (Lilly labelers 00002 and 66733)
    "00002773701": ("Insulin lispro (unbranded)", "standard", 100),
    "00002775201": ("Insulin lispro (unbranded)", "standard", 100),
    "00002775205": ("Insulin lispro (unbranded)", "standard", 100),
    "00002822201": ("Insulin lispro (unbranded)", "standard", 100),
    "00002822259": ("Insulin lispro (unbranded)", "standard", 100),
    "66733077301": ("Insulin lispro (unbranded)", "standard", 100),
    "66733082201": ("Insulin lispro (unbranded)", "standard", 100),
    "66733082259": ("Insulin lispro (unbranded)", "standard", 100),
    # Admelog (Sanofi lispro)
    "00024592410": ("Admelog", "standard", 100), "00024592501": ("Admelog", "standard", 100),
    "00024592505": ("Admelog", "standard", 100), "00024592605": ("Admelog", "standard", 100),
    # Apidra
    "00088250033": ("Apidra", "standard", 100), "00088250052": ("Apidra", "standard", 100),
    "00088250200": ("Apidra", "standard", 100), "00088250205": ("Apidra", "standard", 100),
}

# Part D brand names (Overall rows); InPen devices and mixes excluded
PARTD = {
    "Fiasp": ("Fiasp", "ultra", 100), "Fiasp Flextouch": ("Fiasp", "ultra", 100),
    "Fiasp Penfill": ("Fiasp", "ultra", 100), "Fiasp Pumpcart": ("Fiasp", "ultra", 100),
    "Lyumjev": ("Lyumjev", "ultra", 100), "Lyumjev Kwikpen U-100": ("Lyumjev", "ultra", 100),
    "Lyumjev Kwikpen U-200": ("Lyumjev", "ultra", 200), "Lyumjev Tempo Pen U-100": ("Lyumjev", "ultra", 100),
    "Novolog": ("Novolog", "standard", 100), "Novolog Flexpen": ("Novolog", "standard", 100),
    "Novolog Penfill": ("Novolog", "standard", 100),
    "Insulin Aspart": ("Insulin aspart (unbranded)", "standard", 100),
    "Insulin Aspart Flexpen": ("Insulin aspart (unbranded)", "standard", 100),
    "Insulin Aspart Penfill": ("Insulin aspart (unbranded)", "standard", 100),
    "Humalog": ("Humalog", "standard", 100), "Humalog Junior Kwikpen": ("Humalog", "standard", 100),
    "Humalog Kwikpen U-100": ("Humalog", "standard", 100), "Humalog Kwikpen U-200": ("Humalog", "standard", 200),
    "Humalog Tempo Pen U-100": ("Humalog", "standard", 100),
    "Insulin Lispro": ("Insulin lispro (unbranded)", "standard", 100),
    "Insulin Lispro Junior Kwikpen": ("Insulin lispro (unbranded)", "standard", 100),
    "Insulin Lispro Kwikpen U-100": ("Insulin lispro (unbranded)", "standard", 100),
    "Admelog": ("Admelog", "standard", 100), "Admelog Solostar": ("Admelog", "standard", 100),
    "Apidra": ("Apidra", "standard", 100), "Apidra Solostar": ("Apidra", "standard", 100),
    "Kirsty": ("Kirsty", "standard", 100), "Kirsty Pen": ("Kirsty", "standard", 100),
    "Merilog": ("Merilog", "standard", 100), "Merilog Solostar": ("Merilog", "standard", 100),
}


def medicaid():
    d = pd.read_csv("medicaid_sdud_insulin_XX.csv", dtype={"ndc": str})
    d = d[d.ndc.isin(NDC)].copy()
    d["brand"] = d.ndc.map(lambda n: NDC[n][0])
    d["cls"] = d.ndc.map(lambda n: NDC[n][1])
    d["units"] = d.units_reimbursed * d.ndc.map(lambda n: NDC[n][2])
    supp = d.groupby("year").suppression_used.mean()
    y = d.groupby(["year", "cls"])[["units", "number_of_prescriptions"]].sum().unstack().fillna(0)
    out = pd.DataFrame({
        "ultra_MU": y[("units", "ultra")] / 1e6,
        "all_MU": (y[("units", "ultra")] + y[("units", "standard")]) / 1e6,
        "ultra_rx": y[("number_of_prescriptions", "ultra")],
        "all_rx": y[("number_of_prescriptions", "ultra")] + y[("number_of_prescriptions", "standard")],
        "suppressed_row_frac": supp,
    })
    out["ultra_share_units_pct"] = 100 * out.ultra_MU / out.all_MU
    out["ultra_share_rx_pct"] = 100 * out.ultra_rx / out.all_rx
    b = d.groupby(["year", "brand"]).units.sum().unstack().fillna(0) / 1e6
    return out, b


def partd():
    p = pd.read_csv("partd_spending_by_drug_DY24.csv")
    p = p[(p.Mftr_Name == "Overall") & p.Brnd_Name.isin(PARTD)].copy()
    rows = []
    for yr in range(2020, 2025):
        for _, r in p.iterrows():
            b, c, conc = PARTD[r.Brnd_Name]
            rows.append(dict(year=yr, brand=b, cls=c,
                             units=(r[f"Tot_Dsg_Unts_{yr}"] if pd.notna(r[f"Tot_Dsg_Unts_{yr}"]) else 0) * conc,
                             claims=r[f"Tot_Clms_{yr}"] if pd.notna(r[f"Tot_Clms_{yr}"]) else 0))
    t = pd.DataFrame(rows)
    y = t.groupby(["year", "cls"])[["units", "claims"]].sum().unstack()
    out = pd.DataFrame({
        "ultra_MU": y[("units", "ultra")] / 1e6,
        "all_MU": y["units"].sum(axis=1) / 1e6,
        "ultra_claims": y[("claims", "ultra")],
        "all_claims": y["claims"].sum(axis=1),
    })
    out["ultra_share_units_pct"] = 100 * out.ultra_MU / out.all_MU
    out["ultra_share_claims_pct"] = 100 * out.ultra_claims / out.all_claims
    b = t.groupby(["year", "brand"]).units.sum().unstack() / 1e6
    return out, b


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    m, mb = medicaid()
    print("Medicaid SDUD, national, million insulin units\n", m.round(3))
    print(mb.round(2))
    m.to_csv("medicaid_ultra_share_by_year.csv")
    mb.to_csv("medicaid_units_by_brand_year.csv")
    p, pb = partd()
    print("\nMedicare Part D, million insulin units\n", p.round(3))
    print(pb.round(2))
    p.to_csv("partd_ultra_share_by_year.csv")
    pb.to_csv("partd_units_by_brand_year.csv")


def partd_quarterly():
    """Quarterly Part D Spending by Drug: year-to-date claims only (no dosage
    units), so the share here is of claims."""
    q = pd.read_csv("partd_quarterly_2026Q1.csv")
    q = q[(q.Mftr_Name == "Overall") & q.Brnd_Name.isin(PARTD)].copy()
    q["cls"] = q.Brnd_Name.map(lambda b: PARTD[b][1])
    y = q.groupby(["Year", "cls"]).Tot_Clms.sum().unstack()
    y["ultra_share_claims_pct"] = 100 * y.ultra / (y.ultra + y.standard)
    return y


if __name__ == "__main__":
    print("\nPart D quarterly file, claims\n", partd_quarterly().round(3))
    partd_quarterly().to_csv("partd_quarterly_ultra_share_claims.csv")
