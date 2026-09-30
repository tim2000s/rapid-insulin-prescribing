"""Look up each SDUD NDC in the openFDA NDC directory (and the NLM RxNav
NDC status API as fallback for discontinued codes) to get brand name,
generic name and dosage form/strength. Output ndc_lookup.csv."""
import json, urllib.request, urllib.parse, csv
import pandas as pd

d = pd.read_csv("medicaid_sdud_insulin_XX.csv", dtype={"ndc": str})
ndcs = sorted(d.ndc.unique())
out = []
for n in ndcs:
    rec = {"ndc": n, "sdud_name": d.loc[d.ndc == n, "product_name"].iloc[0]}
    try:
        url = "https://rxnav.nlm.nih.gov/REST/ndcstatus.json?ndc=" + n
        j = json.load(urllib.request.urlopen(url, timeout=60))
        s = j.get("ndcStatus", {})
        rec["rxnav_status"] = s.get("status")
        rec["rxnav_name"] = s.get("conceptName")
        rec["rxcui"] = s.get("rxcui")
    except Exception as e:
        rec["rxnav_status"] = f"error {e}"
    out.append(rec)
    print(rec)
pd.DataFrame(out).to_csv("ndc_lookup.csv", index=False)
