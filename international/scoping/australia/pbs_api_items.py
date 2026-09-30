"""Query the PBS public data API (v3) for every item in the rapid-acting analogue
ATC classes and record brand, pack and listing dates.

The public subscription key is the one the PBS developer portal publishes for
unregistered users; it is rate limited to roughly one call per 20 seconds.
"""
import json, time, urllib.request, sys
KEY = "2384af7c667342ceb5a736fe29f1dc6b"
BASE = "https://data-api.health.gov.au/pbs/api/v3"

def get(path):
    for attempt in range(6):
        req = urllib.request.Request(BASE + path, headers={"subscription-key": KEY})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print("retry", path, e, file=sys.stderr); time.sleep(25)
    raise RuntimeError(path)

if __name__ == "__main__":
    sched = sys.argv[1] if len(sys.argv) > 1 else "4333"  # September 2026
    out = {}
    for drug in ["insulin aspart", "insulin lispro", "insulin glulisine"]:
        d = get(f"/items?schedule_code={sched}&drug_name={urllib.parse.quote(drug.upper())}&limit=100")
        out[drug] = d.get("data", [])
        time.sleep(21)
    json.dump(out, open(f"pbs_api_items_{sched}.json", "w"), indent=1)
    for drug, rows in out.items():
        for r in rows:
            print(r.get("pbs_code"), r.get("brand_name"), r.get("li_form") or r.get("schedule_form"),
                  r.get("pack_size"), r.get("first_listed_date"), r.get("program_code"))
