"""Write ultra_share_by_year.csv for the US from the files already pulled.

Two programmes are reported separately, since neither is national in coverage and they
differ in basis:

  Medicare Part D  2017-2019  claims, Part D Prescribers by Geography and Drug (national rows)
                   2020-2024  insulin units, Part D Spending by Drug DY24 (Tot_Dsg_Unts is ml)
                   2025       claims, Quarterly Part D Spending by Drug (no dosage units)
  Medicaid (SDUD)  2017-2025  insulin units, national (state XX) rows, FFS plus managed care
                   2026       Q1 only, provisional

Product lists (NDC and Part D brand names, including unbranded lispro and aspart, Admelog,
Kirsty and Merilog) are in us_provisional_shares.py. Mixes and InPen devices are excluded.
Run from this folder: python3 build_ultra_share.py
"""
import pandas as pd
from us_provisional_shares import NDC, PARTD


def pct_row(year, by_brand, basis, note):
    tot = sum(by_brand.values())
    f = by_brand.get("Fiasp", 0) / tot * 100
    l = by_brand.get("Lyumjev", 0) / tot * 100
    return dict(year=year, ultra_pct=round(f + l, 2), fiasp_pct=round(f, 2),
                lyumjev_pct=round(l, 2), basis=basis, denominator_note=note)


def main():
    rows = []
    # Part D claims 2017-2019 (geography file, national level)
    g = pd.read_csv("partd_geo_rapid_2017_2024.csv")
    g = g[(g.Prscrbr_Geo_Lvl == "National") & g.Brnd_Name.isin(PARTD)].copy()
    g["brand"] = g.Brnd_Name.map(lambda b: PARTD[b][0])
    for y in (2017, 2018, 2019):
        rows.append(pct_row(y, g[g.year == y].groupby("brand").Tot_Clms.sum().to_dict(),
                            "Medicare Part D claims",
                            "all Part D claims for rapid-acting analogue brand names incl. unbranded lispro/aspart, Admelog, Apidra"))
    # Part D units 2020-2024
    p = pd.read_csv("partd_spending_by_drug_DY24.csv")
    p = p[(p.Mftr_Name == "Overall") & p.Brnd_Name.isin(PARTD)]
    for y in range(2020, 2025):
        d = {}
        for _, r in p.iterrows():
            b, _, conc = PARTD[r.Brnd_Name]
            d[b] = d.get(b, 0) + (r[f"Tot_Dsg_Unts_{y}"] if pd.notna(r[f"Tot_Dsg_Unts_{y}"]) else 0) * conc
        rows.append(pct_row(y, d, "Medicare Part D insulin units (ml x U/ml)",
                            "all Part D rapid-acting analogue units incl. unbranded lispro/aspart, Admelog, Apidra, U-200 pens at 200 U/ml"))
    # Part D claims 2025 (quarterly file)
    q = pd.read_csv("partd_quarterly_2026Q1.csv")
    q = q[(q.Mftr_Name == "Overall") & q.Brnd_Name.isin(PARTD) & (q.Year == "2025 (Q1-Q4)")].copy()
    q["brand"] = q.Brnd_Name.map(lambda b: PARTD[b][0])
    rows.append(pct_row(2025, q.groupby("brand").Tot_Clms.sum().to_dict(), "Medicare Part D claims",
                        "quarterly Part D file, full-year 2025; claims only, no dosage units; includes Kirsty and Merilog"))
    # Medicaid units
    m = pd.read_csv("medicaid_sdud_insulin_XX.csv", dtype={"ndc": str})
    m = m[m.ndc.isin(NDC)].copy()
    m["brand"] = m.ndc.map(lambda n: NDC[n][0])
    m["units"] = m.units_reimbursed * m.ndc.map(lambda n: NDC[n][2])
    for y in range(2017, 2027):
        note = "Medicaid FFS + managed care, national rows; cells with <11 prescriptions suppressed"
        if y == 2026:
            note = "PROVISIONAL: Q1 2026 only; " + note
        rows.append(pct_row(y, m[m.year == y].groupby("brand").units.sum().to_dict(),
                            "Medicaid insulin units (ml x U/ml)", note))
    out = pd.DataFrame(rows)
    out.to_csv("ultra_share_by_year.csv", index=False)
    print(out.to_string())


if __name__ == "__main__":
    main()
