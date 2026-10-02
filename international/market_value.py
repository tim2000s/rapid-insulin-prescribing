#!/usr/bin/env python3
"""
What the rapid-acting insulin market is worth at NHS list prices, in England, the other UK nations,
two English ICBs that have published biosimilar savings estimates, and, as a common yardstick, in
countries whose own prices we do not have.

Price. The English Prescribing Dataset reports net ingredient cost (NIC) for every presentation. NIC
is the basic price before discounts, which for a branded insulin is the list price in the Drug Tariff
and dm+d, the figure the BNF prints as the NHS indicative price. NIC divided by units dispensed, over
the twelve months August 2025 to July 2026, gives a list price per unit for each BNF presentation.
Actual cost (NIC less the average discount, plus container allowance) is reported beside it.

UK nations and ICBs. Scotland, Wales and Northern Ireland use the same BNF presentation codes, so
each nation's units are priced at England's list price for the same presentation, over its own
latest twelve months (July 2025 to June 2026). This removes local price and discount differences and
leaves volume and product mix.

Other countries. Units by brand, latest full year, priced at England's average list price per unit
for that brand. The average blends England's mix of vials, cartridges and pens, which other
countries do not share; that is a modelling choice. Brands not sold in England take the price of the
English product with the same molecule and status: Novolog as NovoRapid; Insulin aspart Sanofi,
Merilog, Kirsty and unbranded US aspart as Trurapi; Admelog and unbranded US lispro as Insulin lispro
Sanofi. The result is what each market would cost at NHS list prices. It is neither local spending
nor manufacturer revenue: US list prices are several times higher and European prices differ by
country. Germany's statutory-insurance tables pool Lyumjev with Liprolog, so that line is valued at
the Lyumjev price and labelled as pooled; glulisine is not reported there. Norway reports the class
total only and is valued at England's average analogue price per unit.

Inputs: epd_cache/nic_national/ (pulled here), international/output/*_by_presentation.csv, international/scoping/{france,denmark,germany,us}.
Writes international/output/market_value_*.csv and MARKET_VALUE.md.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import epd_source as E  # noqa: E402
import history as H  # noqa: E402

OUT = HERE / "output"
SC = HERE / "scoping"
CACHE = ROOT / "epd_cache" / "nic_national"
MONTHS = [f"EPD_SNOMED_{y}{m:02d}" for y, m in [(2025, m) for m in range(8, 13)] + [(2026, m) for m in range(1, 8)]]
BRAND = {"0601011L0BD": "Lyumjev", "0601011L0BB": "Humalog", "0601011A0BC": "Fiasp", "0601011A0BB": "NovoRapid",
         "0601011P0BB": "Apidra", "0601011A0BD": "Trurapi", "0601011L0BE": "Admelog",
         "0601011L0BC": "Insulin lispro Sanofi", "0601011L0AA": "lispro (generic)",
         "0601011A0AA": "aspart (generic)", "0601011P0AA": "glulisine (generic)"}
# Foreign brand -> English brand whose list price stands in for it.
PROXY = {"Novolog": "NovoRapid", "Insulin aspart Sanofi": "Trurapi", "Insuline asparte Sanofi": "Trurapi",
         "Merilog": "Trurapi", "Kirsty": "Trurapi", "Insulin aspart (unbranded)": "Trurapi",
         "Admelog": "Insulin lispro Sanofi", "Insulin lispro (unbranded)": "Insulin lispro Sanofi"}
# Areas with published biosimilar aspart documents. Norfolk and Waveney merged into Norfolk and
# Suffolk ICB during the window; its sub-ICB location 26A keeps the old footprint under both codes.
AREAS = {"Norfolk and Waveney": "PCO_CODE = '26A00'", "Cheshire and Merseyside": "ICB_CODE = 'QYG'",
         "Dorset": "ICB_CODE = 'QVV'"}
PUBLISHED_SAVING = {"Norfolk and Waveney": 340_000, "Cheshire and Merseyside": 1_000_000}


def pull(res):
    f = CACHE / f"{res}.json"
    if f.exists():
        return json.loads(f.read_text())
    q = (f"SELECT BNF_PRESENTATION_CODE AS code, BNF_PRESENTATION_NAME AS name, "
         f"SUM(CAST(ITEMS AS FLOAT64)) AS items, SUM(CAST(TOTAL_QUANTITY AS FLOAT64)) AS quantity, "
         f"SUM(CAST(NIC AS FLOAT64)) AS nic, SUM(CAST(ACTUAL_COST AS FLOAT64)) AS actual_cost "
         f"FROM `{res}` WHERE BNF_PRESENTATION_CODE LIKE '0601011%' "
         f"GROUP BY BNF_PRESENTATION_CODE, BNF_PRESENTATION_NAME")
    rows = E.sql(q, res)
    for r in rows:
        r["month"] = res[-6:]
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows))
    return rows


def pull_areas(res):
    f = CACHE / f"areas_{res}.json"
    if f.exists():
        return json.loads(f.read_text())
    rows = []
    for area, where in AREAS.items():
        q = (f"SELECT BNF_PRESENTATION_CODE AS code, BNF_PRESENTATION_NAME AS name, "
             f"SUM(CAST(TOTAL_QUANTITY AS FLOAT64)) AS quantity, SUM(CAST(NIC AS FLOAT64)) AS nic "
             f"FROM `{res}` WHERE BNF_PRESENTATION_CODE LIKE '0601011%' AND {where} "
             f"GROUP BY BNF_PRESENTATION_CODE, BNF_PRESENTATION_NAME")
        for r in E.sql(q, res):
            rows.append(dict(r, area=area, month=res[-6:]))
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows))
    return rows


def device(name):
    n = name.lower()
    if "vial" in n or " vl" in n:
        return "vial"
    if any(k in n for k in ("pen", "solostar", "kwikpen", "flextouch", "junior")) and "penfill" not in n:
        return "pen"
    return "cartridge"


def england():
    with ThreadPoolExecutor(7) as ex:
        rows = [r for part in ex.map(pull, MONTHS) for r in part]
    d = pd.DataFrame(rows)
    for c in ("items", "quantity", "nic", "actual_cost"):
        d[c] = pd.to_numeric(d[c])
    assert d.month.nunique() == 12, d.month.unique()
    d["class"] = d.code.map(H.klass)
    d["units"] = d.quantity * d.name.map(H.units_per_device)
    d["brand"] = d.code.str[:11].map(BRAND)
    return d


def main():
    d = england()
    analogue = d[d["class"] != "human soluble"]
    pres = analogue.groupby(["code", "brand"], dropna=False)[["units", "nic", "actual_cost"]].sum().reset_index()
    pres["list_per_unit"] = pres.nic / pres.units
    price = pres.set_index("code").list_per_unit
    brand = analogue.groupby("brand")[["units", "nic", "actual_cost"]].sum()
    brand["list_per_100u"] = brand.nic / brand.units * 100
    brand["actual_per_100u"] = brand.actual_cost / brand.units * 100
    avg_per_unit = analogue.nic.sum() / analogue.units.sum()
    brand_price = (brand.nic / brand.units).to_dict()
    pres.to_csv(OUT / "market_value_england_prices.csv", index=False)

    # UK nations: own 12 months, England's list price per presentation.
    nations = [dict(area="England", units=analogue.units.sum(), list_value=analogue.nic.sum(),
                    local_cost=analogue.actual_cost.sum(),
                    lyumjev=analogue[analogue.brand == "Lyumjev"].nic.sum(),
                    fiasp=analogue[analogue.brand == "Fiasp"].nic.sum())]
    names = d.groupby("code").name.last()
    unpriced = {}
    for f, label, costcol in (("scotland", "Scotland", "cost"), ("wales", "Wales", "cost"), ("ni", "Northern Ireland", "cost")):
        x = pd.read_csv(OUT / f"{f}_by_presentation.csv", dtype={"month": str, "code": str})
        x = x[(x.month >= "202507") & (x.month <= "202606")]
        x = x[x.code.map(H.klass) != "human soluble"].copy()
        x["name"] = x.code.map(names).fillna(x.name)
        x["units"] = x.quantity * x.name.map(H.units_per_device)
        x["value"] = x.units * x.code.map(price)
        unpriced[label] = x[x.value.isna()].units.sum() / x.units.sum() * 100
        b = x.code.str[:11].map(BRAND)
        nations.append(dict(area=label, units=x.units.sum(), list_value=x.value.sum(), local_cost=x[costcol].sum(),
                            lyumjev=x[b == "Lyumjev"].value.sum(), fiasp=x[b == "Fiasp"].value.sum()))
    nat = pd.DataFrame(nations)
    nat["pct_of_uk"] = nat.list_value / nat.list_value.sum() * 100
    nat["lyumjev_pct"] = nat.lyumjev / nat.list_value * 100
    nat["fiasp_pct"] = nat.fiasp / nat.list_value * 100
    nat.to_csv(OUT / "market_value_uk.csv", index=False)

    # Areas with published biosimilar documents: August 2025 to July 2026 at England's list prices.
    # The 80% saving matches device types: each NovoRapid unit moved is repriced at England's mean
    # Trurapi list price per unit for the same device (vial, cartridge, pen).
    analogue = analogue.assign(device=analogue.name.map(device))
    tr_dev = analogue[analogue.brand == "Trurapi"].groupby("device").apply(lambda g: g.nic.sum() / g.units.sum())
    with ThreadPoolExecutor(7) as ex:
        a = pd.DataFrame([r for part in ex.map(pull_areas, MONTHS) for r in part])
    for col in ("quantity", "nic"):
        a[col] = pd.to_numeric(a[col])
    a = a[a.code.map(H.klass) != "human soluble"].copy()
    a["units"] = a.quantity * a.name.map(H.units_per_device)
    a["device"] = a.name.map(device)
    icb_rows = []
    for k, g in a.groupby("area"):
        nr = g[g.code.str.startswith("0601011A0BB")]
        tr = g[g.code.str.startswith("0601011A0BD")]
        asp = g[g.code.str.startswith("0601011A0") & ~g.code.str.startswith("0601011A0BC")]
        saving = 0.8 * (nr.nic - nr.units * nr.device.map(tr_dev)).sum()
        icb_rows.append(dict(icb=k, months=g.month.nunique(), analogue_value=g.nic.sum(),
                             novorapid_value=nr.nic.sum(), saving_80pct=saving,
                             published_saving=PUBLISHED_SAVING.get(k, float("nan")),
                             biosimilar_share_of_aspart_pct=tr.units.sum() / asp.units.sum() * 100,
                             fiasp_pct=g[g.code.str.startswith("0601011A0BC")].nic.sum() / g.nic.sum() * 100,
                             lyumjev_pct=g[g.code.str.startswith("0601011L0BD")].nic.sum() / g.nic.sum() * 100))
    icbd = pd.DataFrame(icb_rows)
    icbd["published_pct_of_value"] = icbd.published_saving / icbd.analogue_value * 100
    icbd.to_csv(OUT / "market_value_icbs.csv", index=False)

    # Other countries: units by brand, England's average list price per unit for the brand.
    rows = []
    fr = pd.read_csv(SC / "france" / "share_by_year.csv")
    fr = fr[fr.year == 2025].iloc[0]
    for b in ("NovoRapid", "Humalog", "Apidra", "Insuline asparte Sanofi", "Fiasp", "Lyumjev"):
        rows.append(dict(country="France", year=2025, brand=b, units=fr[f"{b}_units"]))
    dk = pd.read_csv(SC / "denmark" / "rapid_packages_by_year.csv", dtype={"pkg": str, "sector": str})
    lk = pd.read_csv(SC / "denmark" / "rapid_package_lookup.csv", dtype={"pkg": str}).drop_duplicates("pkg")
    dk = dk[(dk.year == 2025) & (dk.sector == "100")].merge(lk[["pkg", "product"]], on="pkg", how="left")
    dk["brand"] = dk["product"].str.split().str[0].str.replace('"', "").str.title()
    dk["brand"] = dk.brand.replace({"Novorapid": "NovoRapid", "Insulin": "Insulin aspart Sanofi"})
    dk["units"] = pd.to_numeric(dk.a2_volume_k, errors="coerce") * 1000 * 40
    for b, u in dk.groupby("brand").units.sum().items():
        rows.append(dict(country="Denmark", year=2025, brand=b, units=u))
    sys.path.insert(0, str(SC / "germany"))
    ger = germany_2025()
    for b, u in ger.items():
        rows.append(dict(country="Germany", year=2025, brand=b, units=u))
    for f, label, yr in (("partd_units_by_brand_year.csv", "US Medicare Part D", 2024),
                         ("medicaid_units_by_brand_year.csv", "US Medicaid", 2025)):
        u = pd.read_csv(SC / "us" / f).set_index("year").loc[yr]
        for b, v in u.items():
            if v > 0:
                rows.append(dict(country=label, year=yr, brand=b, units=v * 1e6))
    no = pd.read_csv(SC / "norway" / "gs_847_rapid_atc.csv", sep=";")
    no = no[no["År"] == 2025] if (no["År"] == 2025).any() else no[no["År"] == no["År"].max()]
    rows.append(dict(country="Norway", year=int(no["År"].iloc[0]), brand="all rapid-acting (class total)",
                     units=float(no["Definerte døgndoser (DDD)"].iloc[0]) * 40))
    c = pd.DataFrame(rows)
    c = c[c.units > 0]
    c["england_brand"] = c.brand.map(lambda b: PROXY.get(b, b)).replace({"Liprolog and Lyumjev (pooled)": "Lyumjev"})
    c["price_per_unit"] = c.england_brand.map(brand_price).fillna(avg_per_unit)
    c["value"] = c.units * c.price_per_unit
    c.to_csv(OUT / "market_value_countries.csv", index=False)
    write_md(brand, avg_per_unit, nat, unpriced, icbd, c, tr_dev)


def germany_2025():
    import re
    num = lambda s: float(s.replace(".", "").replace(",", "."))
    L = (SC / "germany" / "pdf" / "Bundesbericht_GAmSi_202512_konsolidiert.txt").read_text(errors="replace").splitlines()

    def block(head):
        for i, l in enumerate(L):
            if l.strip() == head:
                out = {}
                for l2 in L[i + 2:i + 6]:
                    m = re.match(r"\s+(Biosimilar|Referenz-AM|Sonstige)\s+(.+?)\s{2,}([\d.]+)\s+([\d.]+)\s+", l2)
                    if m:
                        out[m.group(1)] = (m.group(2).strip(), num(m.group(4)))
                return out
    asp, lis = block("Insulin aspart"), block("Insulin lispro")
    to_units = lambda kddd: kddd * 1000 * 40
    return {"Insulin aspart Sanofi": to_units(asp["Biosimilar"][1]), "NovoRapid": to_units(asp["Referenz-AM"][1]),
            "Fiasp": to_units(asp["Sonstige"][1]), "Insulin lispro Sanofi": to_units(lis["Biosimilar"][1]),
            "Humalog": to_units(lis["Referenz-AM"][1]), "Liprolog and Lyumjev (pooled)": to_units(lis["Sonstige"][1])}


def write_md(brand, avg, nat, unpriced, icbd, c, tr_dev):
    L = ["# Rapid-acting insulin market value at NHS list prices: generated summary\n",
         "Generated by `market_value.py`; method and caveats in its docstring. List price is NIC from the "
         "English Prescribing Dataset, August 2025 to July 2026.\n",
         "## England list price by brand\n",
         "| brand | units (million) | list value (£ million) | list £ per 100 units | actual cost £ per 100 units |",
         "|---|---|---|---|---|"]
    for b, r in brand.sort_values("nic", ascending=False).iterrows():
        L.append(f"| {b} | {r.units / 1e6:,.0f} | {r.nic / 1e6:,.2f} | {r.list_per_100u:.2f} | {r.actual_per_100u:.2f} |")
    L += [f"\nAll rapid-acting analogues: £{avg * 100:.2f} per 100 units at list price.\n",
          "## UK nations at England's list prices\n",
          "| nation | analogue units (million) | value at England list price (£ million) | % of UK | "
          "local reported cost (£ million) | Fiasp % of value | Lyumjev % of value |",
          "|---|---|---|---|---|---|---|"]
    for _, r in nat.iterrows():
        L.append(f"| {r.area} | {r.units / 1e6:,.0f} | {r.list_value / 1e6:,.2f} | {r.pct_of_uk:.1f} | "
                 f"{r.local_cost / 1e6:,.2f} | {r.fiasp_pct:.1f} | {r.lyumjev_pct:.1f} |")
    L.append(f"| UK | {nat.units.sum() / 1e6:,.0f} | {nat.list_value.sum() / 1e6:,.2f} | 100.0 | "
             f"{nat.local_cost.sum() / 1e6:,.2f} | {nat.fiasp.sum() / nat.list_value.sum() * 100:.1f} | "
             f"{nat.lyumjev.sum() / nat.list_value.sum() * 100:.1f} |")
    L.append("\nUnits with no English price for the same presentation code (left unvalued): " +
             "; ".join(f"{k} {v:.2f}%" for k, v in unpriced.items()) + ". England's 12 months are August 2025 "
             "to July 2026; the other nations' are July 2025 to June 2026. Local cost is gross ingredient cost "
             "in Scotland and actual cost elsewhere.\n")
    L += ["## Areas with published biosimilar aspart documents, August 2025 to July 2026\n",
          "| area | rapid analogue value at list (£ million) | NovoRapid (£ million) | Fiasp % of value | "
          "Lyumjev % of value | Trurapi % of aspart units | 80% NovoRapid to Trurapi, now (£ million) | "
          "published saving (£ million) | published saving % of rapid analogue value |",
          "|---|---|---|---|---|---|---|---|---|"]
    for _, r in icbd.iterrows():
        pub = "" if pd.isna(r.published_saving) else f"{r.published_saving / 1e6:.2f}"
        pp = "" if pd.isna(r.published_saving) else f"{r.published_pct_of_value:.1f}"
        L.append(f"| {r.icb} | {r.analogue_value / 1e6:.2f} | {r.novorapid_value / 1e6:.2f} | {r.fiasp_pct:.1f} | "
                 f"{r.lyumjev_pct:.1f} | {r.biosimilar_share_of_aspart_pct:.1f} | {r.saving_80pct / 1e6:.2f} | {pub} | {pp} |")
    L.append("\nTrurapi list price per 100 units by device in England: " +
             "; ".join(f"{k} £{v * 100:.2f}" for k, v in tr_dev.items()) + ". The published estimates were made "
             "on earlier volumes (Cheshire and Merseyside, September 2024; Norfolk and Waveney, September 2025) "
             "and before any switching they prompted; the 'now' column prices the NovoRapid still dispensed.")
    L += ["", "## Other markets valued at NHS list prices\n",
          "| market | year | units (million) | value at NHS list price (£ million) | Fiasp % | Lyumjev % | "
          "Lilly % | Novo Nordisk % |", "|---|---|---|---|---|---|---|---|"]
    lilly = {"Lyumjev", "Humalog", "Liprolog and Lyumjev (pooled)", "Insulin lispro (unbranded)"}
    novo = {"Fiasp", "NovoRapid", "Novolog", "Insulin aspart (unbranded)"}
    for (k, y), g in c.groupby(["country", "year"], sort=False):
        v = g.value.sum()
        pct = lambda s: g[g.brand.isin(s)].value.sum() / v * 100
        lyu = "pooled with Liprolog: " + f"{pct({'Liprolog and Lyumjev (pooled)'}):.1f}" if k == "Germany" else f"{pct({'Lyumjev'}):.1f}"
        if k == "Norway":
            L.append(f"| {k} | {y} | {g.units.sum() / 1e6:,.0f} | {v / 1e6:,.2f} | | | | |")
            continue
        L.append(f"| {k} | {y} | {g.units.sum() / 1e6:,.0f} | {v / 1e6:,.2f} | {pct({'Fiasp'}):.1f} | {lyu} | "
                 f"{pct(lilly):.1f} | {pct(novo):.1f} |")
    (OUT / "MARKET_VALUE.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
