#!/usr/bin/env python3
"""
Where should biosimilar switching be aimed, if the aim is to free money for the faster mealtime
insulins? England and North West London, August 2025 to July 2026.

Prices are list prices: net ingredient cost (NIC) per unit for each BNF presentation, national, over
the twelve months (the BNF's NHS indicative price; see international/market_value.py). Every switch is
priced device for device (vial, cartridge, pen), because a person on cartridges cannot move to a
product sold only as pens: Semglee is a pen only, and Trurapi has no pump cartridge.

Scenarios, each at 80% of eligible units (the share used in the Norfolk and Waveney and Cheshire and
Merseyside estimates) and at 100%:
  A  long-acting: Lantus and Abasaglar moved to Semglee, pens only
  B  rapid-acting: NovoRapid moved to Trurapi, device for device (PumpCart excluded)
  C  the cost of the faster insulins against the cheapest same-speed product with the same device:
     Fiasp against Trurapi, Lyumjev against the cheapest lispro still marketed
  D  what A would buy: the number of rapid-acting units that could move from Trurapi to Fiasp with
     A's saving, as percentage points of the area's rapid-acting analogue units
  E  raising the area's ultra-rapid share to Wales's (international/output/UK_SUMMARY.md): the Trurapi
     saving forgone if every added unit is aspart going to Fiasp in place of Trurapi. Lispro moved to
     Lyumjev costs nothing at list price, so this is an upper bound
North West London is sub-ICB location W2U3Z (NHS North West London ICB until the 2026 merger, then
part of NHS West and North London ICB); its 12-month pull is cached in epd_cache/biosim_nwl.

Modelling choices, stated here and in the output: units moved keep their device; the price of each
product is its national mean list price per unit for that device; prices are list, so confidential
discounts are not reflected; Admelog, discontinued in 2026, is excluded as a lispro comparator.

Writes output/biosimilar/SUMMARY.md and scenarios.csv.
"""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

import epd_source as E
import history as H

HERE = Path(__file__).parent
OUT = HERE / "output" / "biosimilar"
NAT = HERE / "epd_cache" / "basal_nic"
NWL = HERE / "epd_cache" / "biosim_nwl"
MONTHS = [f"EPD_SNOMED_{y}{m:02d}" for y, m in [(2025, m) for m in range(8, 13)] + [(2026, m) for m in range(1, 8)]]
LONG = ("0601012V0", "0601012Z0", "0601012X0")


def pull_nwl(res):
    f = NWL / f"{res}.json"
    if f.exists():
        return json.loads(f.read_text())
    like = " OR ".join(f"BNF_PRESENTATION_CODE LIKE '{p}%'" for p in LONG + ("0601011",))
    q = (f"SELECT BNF_PRESENTATION_CODE AS code, BNF_PRESENTATION_NAME AS name, "
         f"SUM(CAST(TOTAL_QUANTITY AS FLOAT64)) AS quantity, SUM(CAST(NIC AS FLOAT64)) AS nic "
         f"FROM `{res}` WHERE PCO_CODE = 'W2U3Z' AND ({like}) GROUP BY 1, 2")
    rows = E.sql(q, res)
    NWL.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows))
    return rows


def device(name):
    n = name.lower()
    if "pumpcart" in n or "1.6ml" in n:
        return "pump cartridge"
    if "vial" in n or " vl" in n:
        return "vial"
    if "penfill" in n or "cartridge" in n or "cart" in n:
        return "cartridge"
    return "pen"


def brand(name):
    first = name.split()[0]
    return "generic" if first == "Insulin" else first


def frame(rows):
    d = pd.DataFrame(rows)
    d[["quantity", "nic"]] = d[["quantity", "nic"]].apply(pd.to_numeric)
    d = d[~d.code.map(lambda c: c.startswith("0601011") and H.klass(c) == "human soluble")]
    d["units"] = d.quantity * d.name.map(H.units_per_device)
    d["brand"] = d.name.map(brand)
    d["device"] = d.name.map(device)
    d["rapid"] = d.code.str.startswith("0601011")
    return d


def wales_share():
    summ = (HERE / "international" / "output" / "UK_SUMMARY.md").read_text()
    return float(next(l for l in summ.splitlines() if l.startswith("| Wales | ")).split("|")[2])


def main():
    global WALES
    WALES = wales_share()
    OUT.mkdir(parents=True, exist_ok=True)
    nat = frame([r for f in sorted(NAT.glob("*.json")) for r in json.loads(f.read_text())])
    assert len(list(NAT.glob("*.json"))) == 12
    with ThreadPoolExecutor(7) as ex:
        nwl = frame([r for part in ex.map(pull_nwl, MONTHS) for r in part])
    price = nat.groupby(["brand", "device"]).apply(lambda g: g.nic.sum() / g.units.sum()).rename("p").to_dict()

    def area(d, label):
        u = d.groupby(["brand", "device"]).units.sum()
        rapid_units = d[d.rapid].units.sum()
        out = dict(area=label, rapid_units_m=rapid_units / 1e6, long_units_m=d[~d.rapid].units.sum() / 1e6,
                   rapid_nic_m=d[d.rapid].nic.sum() / 1e6, long_nic_m=d[~d.rapid].nic.sum() / 1e6)
        sg = price[("Semglee", "pen")]
        a = sum(u.get((b, "pen"), 0) * (price[(b, "pen")] - sg) for b in ("Lantus", "Abasaglar"))
        b_ = sum(u.get(("NovoRapid", dv), 0) * (price[("NovoRapid", dv)] - price[("Trurapi", dv)])
                 for dv in ("vial", "cartridge", "pen") if ("Trurapi", dv) in price)
        # Fiasp premium over Trurapi, weighted by the area's NovoRapid and Trurapi device mix.
        mix = {dv: u.get(("NovoRapid", dv), 0) + u.get(("Trurapi", dv), 0) for dv in ("vial", "cartridge", "pen")}
        prem = sum(mix[dv] * (price[("Fiasp", dv)] - price[("Trurapi", dv)]) for dv in mix) / sum(mix.values())
        for pct in (80, 100):
            out[f"A_long_saving_{pct}_gbp_m"] = a * pct / 100 / 1e6
            out[f"B_rapid_saving_{pct}_gbp_m"] = b_ * pct / 100 / 1e6
            out[f"D_fiasp_pp_from_A_{pct}"] = a * pct / 100 / prem / rapid_units * 100
        out["fiasp_premium_over_trurapi_gbp_per_100u"] = prem * 100
        ultra = d[d.brand.isin(["Fiasp", "Lyumjev"]) & d.rapid].units.sum() / rapid_units * 100
        out["E_forgone_to_wales_gbp_m"] = max(WALES - ultra, 0) / 100 * rapid_units * prem / 1e6
        out["ultra_pct"] = d[d.brand.isin(["Fiasp", "Lyumjev"]) & d.rapid].units.sum() / rapid_units * 100
        out["trurapi_pct_of_aspart"] = (d[d.brand == "Trurapi"].units.sum() /
                                        d[d.code.str.startswith("0601011A0") & ~d.brand.eq("Fiasp")].units.sum() * 100)
        lg = d[~d.rapid & d.code.str.startswith("0601012V0") & ~d.name.str.contains("300")]
        out["semglee_pct_of_glargine100"] = lg[lg.brand == "Semglee"].units.sum() / lg.units.sum() * 100
        out["lantus_abasaglar_pen_units_m"] = (u.get(("Lantus", "pen"), 0) + u.get(("Abasaglar", "pen"), 0)) / 1e6
        out["lantus_abasaglar_cartridge_units_m"] = (u.get(("Lantus", "cartridge"), 0) +
                                                     u.get(("Abasaglar", "cartridge"), 0)) / 1e6
        return out

    s = pd.DataFrame([area(nat, "England"), area(nwl, "North West London")])
    s.round(3).to_csv(OUT / "scenarios.csv", index=False)
    pt = lambda b, dv: f"£{price[(b, dv)] * 100:.2f}" if (b, dv) in price else "none"
    L = ["# Aiming biosimilar switching: generated summary\n",
         "Generated by `biosimilar_reallocation.py`; method and modelling choices in its docstring. "
         "August 2025 to July 2026, list prices (NIC per unit, national, by device).\n",
         "## List price per 100 units by device, England\n", "| product | vial | cartridge | pen |", "|---|---|---|---|"]
    for b in ("Lantus", "Abasaglar", "Semglee", "Toujeo", "Tresiba", "NovoRapid", "Trurapi", "Fiasp", "Humalog",
              "Lyumjev", "Admelog"):
        L.append(f"| {b} | {pt(b, 'vial')} | {pt(b, 'cartridge')} | {pt(b, 'pen')} |")
    L += ["", "## Scenarios\n", "| | England | North West London |", "|---|---|---|"]
    rows = [("rapid-acting analogue units (million)", "rapid_units_m", "{:,.0f}"),
            ("long-acting analogue units (million)", "long_units_m", "{:,.0f}"),
            ("ultra-rapid % of rapid-acting units", "ultra_pct", "{:.1f}"),
            ("Trurapi % of standard aspart units", "trurapi_pct_of_aspart", "{:.1f}"),
            ("Semglee % of glargine 100 units", "semglee_pct_of_glargine100", "{:.1f}"),
            ("Lantus and Abasaglar pen units (million)", "lantus_abasaglar_pen_units_m", "{:,.1f}"),
            ("Lantus and Abasaglar cartridge units, no Semglee equivalent (million)",
             "lantus_abasaglar_cartridge_units_m", "{:,.1f}"),
            ("A: long-acting saving, 80% of pens to Semglee (£ million)", "A_long_saving_80_gbp_m", "{:.2f}"),
            ("A: long-acting saving, all pens to Semglee (£ million)", "A_long_saving_100_gbp_m", "{:.2f}"),
            ("B: rapid saving, 80% NovoRapid to Trurapi (£ million)", "B_rapid_saving_80_gbp_m", "{:.2f}"),
            ("B: rapid saving, all NovoRapid to Trurapi (£ million)", "B_rapid_saving_100_gbp_m", "{:.2f}"),
            ("Fiasp premium over Trurapi, area device mix (£ per 100 units)",
             "fiasp_premium_over_trurapi_gbp_per_100u", "{:.2f}"),
            ("D: Fiasp instead of Trurapi paid for by A at 80% (percentage points of rapid units)",
             "D_fiasp_pp_from_A_80", "{:.1f}"),
            ("D: the same at 100%", "D_fiasp_pp_from_A_100", "{:.1f}"),
            ("E: Trurapi saving forgone in reaching Wales's ultra-rapid share, upper bound (£ million)",
             "E_forgone_to_wales_gbp_m", "{:.2f}")]
    for label, col, f in rows:
        L.append(f"| {label} | " + " | ".join(f.format(v) for v in s[col]) + " |")
    L += ["", f"Wales's ultra-rapid share of rapid-acting analogue units, the target in E: {WALES:.1f}%. At list price "
          "Fiasp costs the same as NovoRapid and Lyumjev the same as Humalog for each device, so moving people "
          "from those products to the faster ones costs nothing; the cost arises only against Trurapi."]
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
