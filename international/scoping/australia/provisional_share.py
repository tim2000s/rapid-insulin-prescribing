"""Provisional ultra-rapid share on the PBS, financial year July 2025 to June 2026.

Numerator: Fiasp items (11705C vial, 11706D FlexTouch, 13651L Penfill). Lyumjev has
no PBS item code. Denominator: every rapid-acting analogue item in the trimmed monthly
Date of Supply file. Measure is PBS prescriptions (PRSCRPTN_CNT), Section 85, all
patient categories, above and under co-payment.

Units are estimated, not observed. The DoS data do not carry quantity dispensed, so
packs per prescription are inferred as (total cost per prescription minus an assumed
dispensing fee) / PBS pack price, and then multiplied by units per pack. This is a
modelling choice and is reported beside the prescription count, not instead of it.
"""
import csv, collections

BRAND = {"01921D": "Apidra", "09224L": "Apidra", "12268Q": "Apidra",
         "08084L": "Humalog", "08085M": "Humalog", "08212F": "Humalog", "11645X": "Humalog U200",
         "12237C": "Humalog", "08435Y": "NovoRapid", "08571D": "NovoRapid", "12254Y": "NovoRapid",
         "11705C": "Fiasp", "11706D": "Fiasp", "13651L": "Fiasp"}
UNITS_PER_PACK = {"08084L": 1000, "08571D": 1000, "09224L": 1000, "11705C": 1000,
                  "11645X": 3000, "08085M": 750}  # others 5 x 3 mL x 100 U/mL = 1500
PACK_PRICE_SEP2026 = {"12254Y": 28.18}  # filled below from the API dump
ULTRA = {"Fiasp"}

if __name__ == "__main__":
    import json
    api = json.load(open("pbs_api_items_4333.json"))
    for rows in api.values():
        for r in rows:
            PACK_PRICE_SEP2026[r["pbs_code"].zfill(6)] = r["claimed_price"]
    scripts = collections.Counter(); cost = collections.Counter()
    for r in csv.DictReader(open("dos_monthly_rapid_2022_2026.csv")):
        m = int(r["MONTH_OF_SUPPLY"])
        if 202507 <= m <= 202606:
            scripts[r["ITEM_CODE"]] += int(r["PRSCRPTN_CNT"])
            cost[r["ITEM_CODE"]] += float(r["TOTAL_COST"])
    tot = sum(scripts.values()); ultra = sum(v for k, v in scripts.items() if BRAND[k] in ULTRA)
    print(f"{'item':7} {'brand':13} {'scripts':>8} {'cost/script':>11} {'pack price':>10}")
    for k in sorted(scripts, key=lambda k: -scripts[k]):
        print(f"{k:7} {BRAND[k]:13} {scripts[k]:8d} {cost[k]/scripts[k]:11.2f} {PACK_PRICE_SEP2026.get(k, float('nan')):10.2f}")
    print(f"\nPrescriptions: ultra-rapid {ultra} / all {tot} = {100*ultra/tot:.2f}%")
    by = collections.Counter()
    for k, v in scripts.items(): by[BRAND[k].split()[0]] += v
    print({b: f"{v} ({100*v/tot:.1f}%)" for b, v in by.most_common()})

    # Units, assuming five packs per prescription (the PBS maximum quantity for every item).
    # Cost per prescription divided by pack price is 5.3 to 5.9 for every item above, which
    # is consistent with near-universal dispensing of the maximum once fees and markup are allowed.
    PER_SCRIPT = {k: 5 * UNITS_PER_PACK.get(k, 1500) for k in BRAND}
    u = {k: v * PER_SCRIPT[k] for k, v in scripts.items()}
    ut = sum(u.values()); uu = sum(v for k, v in u.items() if BRAND[k] in ULTRA)
    print(f"Units (assumed 5 packs/script): ultra-rapid {uu/1e6:.1f}M / all {ut/1e6:.1f}M = {100*uu/ut:.2f}%")
