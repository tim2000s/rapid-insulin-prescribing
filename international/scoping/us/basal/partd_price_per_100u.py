"""Average Medicare Part D spending per 100 insulin units, 2024 (and 2023 for comparison), for each long-acting and
rapid-acting analogue product, from Part D Spending by Drug DY24.

Avg_Spnd_Per_Dsg_Unt_Wghtd is spending per millilitre for insulin, so the cost of 100 units is
that figure x 100 / concentration (U/ml). Product rows are spending-weighted across brand names
(total spending / total units), which is what Avg_Spnd_Per_Dsg_Unt_Wghtd does within a name.

These are gross drug costs, before manufacturer rebates and other price concessions. CMS states
in the dataset description that it is "prohibited from publicly disclosing" rebates, so the
figures overstate net cost, by different amounts for different products. Insulin rebates were
large in this period and differed by manufacturer, so the gross ranking need not hold net.

"Insulin Glargine Solostar" mixes 100 and 300 U/ml in 2024 (see build_basal_share.py); that year
it is reported on its own line per ml only and left out of the product average.

2023 is included because the gross figures for several insulins fell sharply between 2023 and
2024 (Lantus $30.14 to $6.14 per 100 units, Novolog $36.56 to $8.41, Levemir $32.59 to $10.12),
which is consistent with the manufacturers' announced list-price reductions; those announcements
were not captured or dated here.

Output: partd_price_per_100u.csv. Run from this folder: python3 partd_price_per_100u.py
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from us_provisional_shares import PARTD as RAPID  # noqa: E402
from build_basal_share import PARTD as BASAL  # noqa: E402

YEARS = (2023, 2024)
MIXED = "Insulin Glargine Solostar"


def one_year(YEAR):
    d = pd.read_csv("../partd_spending_by_drug_DY24.csv")
    d = d[d.Mftr_Name == "Overall"]
    rows = []
    for name, (product, cls, conc) in {**BASAL, **{k: (v[0], "rapid " + v[1], v[2]) for k, v in RAPID.items()}}.items():
        r = d[d.Brnd_Name == name]
        if r.empty or pd.isna(r[f"Tot_Dsg_Unts_{YEAR}"].iloc[0]):
            continue
        r = r.iloc[0]
        ml, spend, per_ml = r[f"Tot_Dsg_Unts_{YEAR}"], r[f"Tot_Spndng_{YEAR}"], r[f"Avg_Spnd_Per_Dsg_Unt_Wghtd_{YEAR}"]
        rows.append(dict(level="brand name", product=product, partd_brand_name=name, cls=cls,
                         conc_u_per_ml=conc, spending_usd=spend, ml=ml, claims=r[f"Tot_Clms_{YEAR}"],
                         spend_per_ml=round(per_ml, 2),
                         spend_per_100u=None if (name == MIXED and YEAR == 2024) else round(per_ml * 100 / conc, 2)))
    t = pd.DataFrame(rows)
    ok = t[t.spend_per_100u.notna()].copy()
    ok["units"] = ok.ml * ok.conc_u_per_ml
    g = ok.groupby(["product", "cls"]).agg(spending_usd=("spending_usd", "sum"), units=("units", "sum"),
                                           ml=("ml", "sum"), claims=("claims", "sum")).reset_index()
    g["spend_per_100u"] = (g.spending_usd / g.units * 100).round(2)
    g["level"] = "product"
    out = pd.concat([g.drop(columns="units"), t], ignore_index=True)
    out["year"] = YEAR
    out["note"] = "gross Part D drug cost before manufacturer rebates (CMS may not disclose rebates)"
    return out.sort_values(["level", "cls", "spend_per_100u"], ascending=[False, True, False])


def main():
    out = pd.concat([one_year(y) for y in YEARS], ignore_index=True)
    out.to_csv("partd_price_per_100u.csv", index=False)
    pd.set_option("display.width", 250)
    p = out[out.level == "product"].pivot_table(index=["cls", "product"], columns="year", values="spend_per_100u")
    print(p.to_string())


if __name__ == "__main__":
    main()
