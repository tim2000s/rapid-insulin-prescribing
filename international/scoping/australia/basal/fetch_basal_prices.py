"""Fetch PBS prices for the long-acting analogue items and save the raw responses.

Two sources, both saved unmodified:
1. PBS public data API v3, /items for schedule 4333 (September 2026, the schedule the
   rapid-acting dump pbs_api_items_4333.json was taken from), one call per drug name.
   claimed_price is the price per pack the API reports; it is used as the per-pack basis.
2. The pbs.gov.au item page per item code, which states DPMQ for the maximum quantity.
   These are fetched on the day the script runs and reflect the schedule then in force.

The API key is the public key the PBS developer portal publishes for unregistered users,
rate limited to about one call per 20 seconds. No personal identifiers are sent.
"""
import json, sys, time, urllib.parse, urllib.request
sys.path.insert(0, "..")
from pbs_api_items import get  # same key and retry logic as the rapid dump

# item pages are addressed without the leading zero; 11417X (Ryzodeg FlexTouch) is no longer listed
ITEMS = ["9039R", "11815W", "11302W", "11308E", "9040T", "12236B", "15393E", "11426J",
         "8435Y", "12254Y", "8212F", "12237C", "13651L"]
UA = {"User-Agent": "Mozilla/5.0 (research script; rapid-insulin-prescribing)"}

if __name__ == "__main__":
    sched = sys.argv[1] if len(sys.argv) > 1 else "4333"
    out = {}
    for drug in ["insulin glargine", "insulin detemir", "insulin degludec", "insulin degludec + insulin aspart"]:
        try:
            d = get(f"/items?schedule_code={sched}&drug_name={urllib.parse.quote(drug.upper())}&limit=100")
            out[drug] = d.get("data", [])
        except RuntimeError as e:  # an empty body is what the API returns for a name with no items
            print("no items", drug, e); out[drug] = []
        time.sleep(21)
    json.dump(out, open(f"pbs_api_basal_items_{sched}.json", "w"), indent=1)
    for code in ITEMS:
        req = urllib.request.Request(f"https://www.pbs.gov.au/medicine/item/{code}", headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                open(f"captures/item_pages/{code}.html", "wb").write(r.read())
        except Exception as e:
            print("item page failed", code, e)
        time.sleep(2)
