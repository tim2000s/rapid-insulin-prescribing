"""Classify every NDC in medicaid_sdud_basal_XX.csv from the NLM RxNav NDC status API, as
../lookup_ndc.py does, and derive product, molecule and concentration from the RxNorm concept
name (for example "3 ML insulin glargine 300 UNT/ML Pen Injector [Toujeo]").

Classification rules (modelling choices):
  degludec       insulin degludec, alone
  glargine300    insulin glargine at 300 UNT/ML (Toujeo and unbranded Toujeo)
  glargine100    insulin glargine at 100 UNT/ML in any form: Lantus, unbranded Lantus,
                 Basaglar, Semglee, glargine-yfgn, Rezvoglar (glargine-aglr)
  detemir        insulin detemir
  excluded       everything else, including rapid-acting, NPH, premixes and the fixed-ratio
                 GLP-1 combinations (Xultophy, Soliqua), which the concept name joins with " / "
Codes that RxNav cannot resolve are kept with class "unresolved" and listed by the build
script so they can be checked by hand.

Output: ndc_lookup_basal.csv. Run from this folder: python3 lookup_ndc_basal.py
"""
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

UA = {"User-Agent": "Mozilla/5.0 (academic research; insulin utilisation analysis)"}


def rxnav(ndc):
    url = "https://rxnav.nlm.nih.gov/REST/ndcstatus.json?ndc=" + ndc
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                s = json.load(r).get("ndcStatus", {})
            return s.get("status"), s.get("conceptName"), s.get("rxcui")
        except Exception as e:  # network retries
            err = e
            time.sleep(3 * (attempt + 1))
    return f"error {err}", None, None


def classify(name):
    if not name:
        return "unresolved", None, None, None
    n = name.lower()
    brand = re.search(r"\[(.+?)\]", name)
    brand = brand.group(1) if brand else None
    conc = re.search(r"insulin [a-z\- ]+?(\d+) unt/ml", n)
    conc = int(conc.group(1)) if conc else None
    # combinations are joined by " / " in RxNorm names; "UNT/ML" has no spaces
    if " / " in n or "isophane" in n or "nph" in n:
        return "excluded", brand, None, conc
    if "degludec" in n:
        return "degludec", brand, "degludec", conc
    if "glargine" in n:
        return ("glargine300" if conc == 300 else "glargine100"), brand, "glargine", conc
    if "detemir" in n:
        return "detemir", brand, "detemir", conc
    return "excluded", brand, None, conc


def job(args):
    ndc, sdud_name = args
    status, name, rxcui = rxnav(ndc)
    cls, brand, molecule, conc = classify(name)
    return dict(ndc=ndc, sdud_name=sdud_name, rxnav_status=status, rxnav_name=name,
                rxcui=rxcui, cls=cls, brand=brand, molecule=molecule, conc_u_per_ml=conc)


def main():
    d = pd.read_csv("medicaid_sdud_basal_XX.csv", dtype={"ndc": str})
    first = d.groupby("ndc").product_name.first()
    with ThreadPoolExecutor(7) as ex:
        out = list(ex.map(job, first.items()))
    t = pd.DataFrame(out).sort_values("ndc")
    t.to_csv("ndc_lookup_basal.csv", index=False)
    pd.set_option("display.width", 250)
    print(t[["ndc", "sdud_name", "rxnav_status", "cls", "brand", "conc_u_per_ml", "rxnav_name"]].to_string())


if __name__ == "__main__":
    main()
