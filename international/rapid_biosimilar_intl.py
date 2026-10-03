#!/usr/bin/env python3
"""
Uptake of biosimilar rapid-acting insulin against the ultra-rapid insulins, by country and year, on
each country's existing rapid-acting basis (units, except where stated).

Biosimilar means a product approved by abbreviated comparison with an originator from another
company: Trurapi (Insulin aspart Sanofi), Kirsty (Biocon), Admelog and Insulin lispro Sanofi, and in
the US Merilog. The unbranded US insulin aspart and insulin lispro are the originators' own
lower-priced versions (Novo Nordisk and Lilly), so they are reported in their own column and not as
biosimilars.

    UK nations   output/uk_nations_monthly.csv, calendar years with 12 months (biosimilar class of
                 history.py: Trurapi, Admelog, Insulin lispro Sanofi)
    France       scoping/france/share_by_year.csv (Open Medic units); biosimilar = Insuline asparte
                 Sanofi; no biosimilar lispro appears in Open Medic
    Denmark      scoping/denmark rapid packages, primary sector, DDD x 40; biosimilar = Insulin aspart
                 "Sanofi" (from 2020); no biosimilar lispro is marketed
    Germany      GAmSi Tabelle 8, December reports (scoping/germany/pdf), DDD x 40; Biosimilar lines for
                 insulin aspart and insulin lispro; denominator aspart plus lispro (glulisine not
                 reported); ultra-rapid = Fiasp only, a lower bound
    US           scoping/us Part D (units, 2020 to 2024) and Medicaid (units, 2017 to 2025) by brand
    Australia    no rapid-acting biosimilar is listed on the PBS schedule (API, September 2026: the
                 aspart items carry NovoRapid and Fiasp only), so the share is not computed

Writes output/rapid_biosimilar_intl.csv and RAPID_BIOSIMILAR_INTL.md.
"""
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
SC = HERE / "scoping"
OUT = HERE / "output"


def uk():
    m = pd.read_csv(OUT / "uk_nations_monthly.csv", parse_dates=["date"])
    m["year"] = m.date.dt.year
    rows = []
    for (n, y), g in m.groupby(["nation", "year"]):
        if g.date.nunique() < 12:
            continue
        w = g.analogue_units
        rows.append(dict(country=n, year=y, biosimilar_pct=(g.biosimilar_units_pct * w).sum() / w.sum(),
                         ultra_pct=(g.ultra_units_pct * w).sum() / w.sum(), basis="units"))
    return rows


def france():
    d = pd.read_csv(SC / "france" / "share_by_year.csv")
    return [dict(country="France", year=int(r.year), biosimilar_pct=r["Insuline asparte Sanofi_units"] / r.total_units * 100,
                 ultra_pct=r.ultra_share_pct, basis="units") for _, r in d.iterrows()
            if str(r.year).replace(".0", "").isdigit()]


def denmark():
    d = pd.read_csv(SC / "denmark" / "rapid_packages_by_year.csv", dtype={"pkg": str, "sector": str})
    lk = pd.read_csv(SC / "denmark" / "rapid_package_lookup.csv", dtype={"pkg": str}).drop_duplicates("pkg")
    d = d[d.sector == "100"].merge(lk[["pkg", "product"]], on="pkg")
    d["v"] = pd.to_numeric(d.a2_volume_k, errors="coerce")
    d["b"] = d["product"].str.split().str[0].str.lower()
    rows = []
    for y, g in d.groupby("year"):
        t = g.v.sum()
        rows.append(dict(country="Denmark", year=int(y), biosimilar_pct=g[g["product"].str.contains("Sanofi")].v.sum() / t * 100,
                         ultra_pct=g[g.b == "fiasp"].v.sum() / t * 100, basis="units (DDD x 40)"))
    return rows


def germany():
    num = lambda s: float(s.replace(".", "").replace(",", "."))
    rows = []
    for f in sorted((SC / "germany" / "pdf").glob("Bundesbericht_GAmSi_*12_konsolidiert.txt")):
        y = int(re.search(r"_(\d{4})12_", f.name).group(1))
        L = f.read_text(errors="replace").splitlines()

        def block(head):
            for i, l in enumerate(L):
                if l.strip() == head:
                    out = {}
                    for l2 in L[i + 2:i + 6]:
                        m = re.match(r"\s+(Biosimilar|Referenz-AM|Sonstige)\s+(.+?)\s{2,}([\d.]+)\s+([\d.]+)\s+", l2)
                        if m:
                            out[m.group(1)] = num(m.group(4))
                    return out
        asp, lis = block("Insulin aspart"), block("Insulin lispro")
        if not asp or not lis or "Sonstige" not in asp:
            continue
        t = sum(asp.values()) + sum(lis.values())
        rows.append(dict(country="Germany", year=y, biosimilar_pct=(asp.get("Biosimilar", 0) + lis.get("Biosimilar", 0)) / t * 100,
                         ultra_pct=asp["Sonstige"] / t * 100, basis="units (DDD x 40); ultra-rapid is Fiasp only"))
    return rows


def us():
    rows = []
    bios = ["Admelog", "Kirsty", "Merilog", "Insulin aspart Sanofi", "Insulin lispro Sanofi"]
    own = ["Insulin aspart (unbranded)", "Insulin lispro (unbranded)"]
    for f, label in (("partd_units_by_brand_year.csv", "US Medicare Part D"), ("medicaid_units_by_brand_year.csv", "US Medicaid")):
        d = pd.read_csv(SC / "us" / f).set_index("year").fillna(0)
        for y, r in d.iterrows():
            if int(y) >= 2026:
                continue                        # partial year (Medicaid 2026 is the first quarter)
            t = r.sum()
            rows.append(dict(country=label, year=int(y), biosimilar_pct=sum(r.get(b, 0) for b in bios) / t * 100,
                             originator_unbranded_pct=sum(r.get(b, 0) for b in own) / t * 100,
                             ultra_pct=(r.get("Fiasp", 0) + r.get("Lyumjev", 0)) / t * 100, basis="units"))
    return rows


def prices():
    """Biosimilar against originator, per 100 units, latest year: list or reimbursement basis per country."""
    rows = []
    e = pd.read_csv(OUT / "market_value_england_prices.csv").groupby("brand")[["nic", "units"]].sum()
    pe = e.nic / e.units * 100
    rows.append(("England (NHS list, Aug 2025 to Jul 2026)", "Trurapi", pe["Trurapi"], "NovoRapid", pe["NovoRapid"]))
    fr = pd.read_csv(SC / "france" / "open_medic_rapid_insulin_rows.csv", dtype={"CIP13": str})
    pc = pd.read_csv(SC / "france" / "product_codes.csv", dtype={"cip13": str}).set_index("cip13")
    fr = fr[fr.year == 2025].copy()
    fr["bse"] = pd.to_numeric(fr.BSE.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    fr["units"] = fr.BOITES * fr.CIP13.map(pc.units_per_box)
    fr["brand"] = fr.CIP13.map(pc.brand)
    g = fr.groupby("brand")[["bse", "units"]].sum()
    pf = g.bse / g.units * 100
    rows.append(("France (reimbursement base, 2025, euros)", "Insuline asparte Sanofi", pf["Insuline asparte Sanofi"],
                 "NovoRapid", pf["NovoRapid"]))
    d = pd.read_csv(SC / "denmark" / "rapid_packages_by_year.csv", dtype={"pkg": str, "sector": str})
    lk = pd.read_csv(SC / "denmark" / "rapid_package_lookup.csv", dtype={"pkg": str}).drop_duplicates("pkg")
    d = d[(d.year == 2025) & (d.sector == "100")].merge(lk[["pkg", "product"]], on="pkg")
    d["kr"] = pd.to_numeric(d.a2_turnover_kdkk, errors="coerce") * 1000
    d["units"] = pd.to_numeric(d.a2_volume_k, errors="coerce") * 1000 * 40
    d["b"] = d["product"].map(lambda x: "Sanofi" if "Sanofi" in x else x.split()[0].lower())
    g = d.groupby("b")[["kr", "units"]].sum()
    pdk = g.kr / g.units * 100
    rows.append(("Denmark (pharmacy turnover, 2025, kroner)", "Insulin aspart Sanofi", pdk["Sanofi"], "NovoRapid",
                 pdk["novorapid"]))
    u = pd.read_csv(SC / "us" / "basal" / "partd_price_per_100u.csv")
    u = u[(u.year == 2024) & (u.level == "product")].set_index("product").spend_per_100u
    rows.append(("US Part D (gross spending, 2024, dollars)", "Admelog", u["Admelog"], "Humalog", u["Humalog"]))
    return rows


def main():
    d = pd.DataFrame(uk() + france() + denmark() + germany() + us()).sort_values(["country", "year"])
    d.round(2).to_csv(OUT / "rapid_biosimilar_intl.csv", index=False)
    L = ["# Biosimilar rapid-acting insulin against the ultra-rapid insulins: generated summary\n",
         "Generated by `rapid_biosimilar_intl.py`; sources and definitions in its docstring. Shares of rapid-acting "
         "analogue volume. Australia has no rapid-acting biosimilar on the PBS schedule.\n",
         "## Latest full year\n", "| country | year | biosimilar % | ultra-rapid % | originators' own unbranded % |",
         "|---|---|---|---|---|"]
    for c, g in d.groupby("country", sort=False):
        r = g.iloc[-1]
        own = "" if pd.isna(r.get("originator_unbranded_pct")) else f"{r.originator_unbranded_pct:.1f}"
        L.append(f"| {c} | {int(r.year)} | {r.biosimilar_pct:.1f} | {r.ultra_pct:.1f} | {own} |")
    L += ["", "## By year\n"]
    piv = d.pivot_table(index="year", columns="country", values="biosimilar_pct").round(1)
    L.append("Biosimilar % of rapid-acting analogue volume:\n")
    L.append("| year | " + " | ".join(piv.columns) + " |")
    L.append("|---|" + "---|" * len(piv.columns))
    for y, r in piv.iterrows():
        L.append(f"| {y} | " + " | ".join("" if pd.isna(v) else f"{v:.1f}" for v in r) + " |")
    L += ["", "## Price of the biosimilar against its originator, per 100 units\n",
          "| basis | biosimilar | price | originator | price | difference |", "|---|---|---|---|---|---|"]
    for basis, b, pb, o, po in prices():
        L.append(f"| {basis} | {b} | {pb:.2f} | {o} | {po:.2f} | {(pb / po - 1) * 100:+.0f}% |")
    L.append("\nGermany: prices are set by confidential rebate contracts, so no comparable figure is published.")
    (OUT / "RAPID_BIOSIMILAR_INTL.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
