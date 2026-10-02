"""PBS prices per 100 units for long-acting and rapid-acting analogue items.

Two bases, both published prices before any confidential rebate:
  claimed_price  per pack, PBS API v3 schedule 4333 (September 2026); basal items from
                 pbs_api_basal_items_4333.json, rapid items from ../pbs_api_items_4333.json.
  DPMQ           dispensed price for maximum quantity (5 packs for every item here), parsed
                 from the pbs.gov.au item pages saved in captures/item_pages on 2 October 2026,
                 i.e. the October 2026 schedule. DPMQ includes pharmacy mark-up and fees.
Tresiba is listed with a special pricing arrangement (PBAC July 2025 PSD, section 8), so its
published price overstates what the Commonwealth pays by an undisclosed rebate.
Lantus, Semglee and Basaglar have no item in the September 2026 schedule; Optisulin is the
only glargine 100 units/mL brand returned by the API.
"""
import csv, glob, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = {"11302W": 2250, "11308E": 1350}  # Toujeo 5 x 1.5 mL, 3 x 1.5 mL at 300 units/mL
PRODUCT = {"15393E": "degludec (Tresiba)", "11302W": "glargine 300 (Toujeo)", "11308E": "glargine 300 (Toujeo)",
           "9039R": "glargine 100 (Optisulin)", "11815W": "glargine 100 (Optisulin)",
           "9040T": "detemir (Levemir)", "12236B": "detemir (Levemir)", "11426J": "degludec+aspart (Ryzodeg)",
           "13651L": "faster aspart (Fiasp)", "12254Y": "aspart (NovoRapid)", "8435Y": "aspart (NovoRapid)",
           "12237C": "lispro (Humalog)", "8212F": "lispro (Humalog)"}

if __name__ == "__main__":
    api = {}
    for f in [os.path.join(HERE, "pbs_api_basal_items_4333.json"), os.path.join(HERE, "..", "pbs_api_items_4333.json")]:
        for rows in json.load(open(f)).values():
            for r in rows:
                api[r["pbs_code"]] = r
    dpmq = {}
    for f in glob.glob(os.path.join(HERE, "captures", "item_pages", "*.html")):
        t = open(f, errors="ignore").read()
        s = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>", "", t, flags=re.S))))
        m = re.search(r"Max qty packs: (\d+) .*?DPMQ: \$([\d.,]+)", s)
        if m: dpmq[os.path.basename(f)[:-5]] = (int(m.group(1)), float(m.group(2).replace(",", "")))
    with open(os.path.join(HERE, "prices_per_100_units.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pbs_code", "product", "brand", "pack", "units_per_pack", "claimed_price_aud_sep2026",
                    "claimed_aud_per_100u", "dpmq_aud_oct2026", "max_packs", "dpmq_aud_per_100u", "benefit_type", "first_listed_date"])
        for code, prod in PRODUCT.items():
            r = api[code]; u = UNITS.get(code, 1500); mp, dp = dpmq[code]
            w.writerow([code, prod, r["brand_name"], r["schedule_form"], u, r["claimed_price"],
                        round(100 * r["claimed_price"] / u, 2), dp, mp, round(100 * dp / (mp * u), 2),
                        {"U": "unrestricted", "R": "restricted benefit"}[r["benefit_type_code"]], r["first_listed_date"]])
            print(f"{code:7} {prod:28} claimed/100u {100*r['claimed_price']/u:5.2f}  DPMQ/100u {100*dp/(mp*u):5.2f}")
