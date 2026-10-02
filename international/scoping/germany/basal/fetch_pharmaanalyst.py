"""Fetch annual GKV prescription volumes for long-acting insulins from WIdO PharMaAnalyst.

PharMaAnalyst (https://arzneimittel.wido.de/PharMaAnalyst/) is the public front end of the
GKV-Arzneimittelindex of the Wissenschaftliches Institut der AOK. It reports, per report year
2012-2024, prescriptions, DDD and net cost for the whole statutory insurance outpatient market,
by ATC group or substance ("Wirkstoff") and by product name ("Medikament"). It is an Apache Wicket
application with no documented API, so this script drives the same Ajax calls the page makes:
select the year, switch on the columns, submit. The raw Ajax responses are kept in pharmaanalyst/
so that the parsed numbers can be checked against what the server returned.

Queries: ATC group A10AE (all long-acting insulins, one row per substance) and the products
Tresiba, Levemir, Lantus, Toujeo, Abasaglar, Semglee.

The jobs run one at a time. A first run with seven parallel sessions returned rows for years other
than the one each session had selected, so the report year appears to be held server-side across
sessions; every response therefore carries its year in the result row and build_basal_share.py
checks it against the file name. A job whose year does not match is retried here.
"""
import html, re, json, time
from pathlib import Path
import requests

B = "https://arzneimittel.wido.de/PharMaAnalyst/"
OUT = Path(__file__).with_name("pharmaanalyst")
YEARS = {2012 + i: str(i) for i in range(13)}  # option value i = year 2012+i (checked on the page)
PRODUCTS = ["Tresiba", "Levemir", "Lantus", "Toujeo", "Abasaglar", "Semglee"]


def run(job):
    year, kind, term = job
    s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0"
    r = s.get(B, timeout=60)
    u = lambda k: B + re.search(r'"u":"\./([^"]*' + k + ')"', r.text).group(1)
    base = re.search(r'Wicket.Ajax.baseUrl="([^"]*)"', r.text).group(1)
    H = {"Wicket-Ajax": "true", "Wicket-Ajax-BaseURL": base, "X-Requested-With": "XMLHttpRequest"}
    # the year is confirmed by an Ajax POST of the year form (a plain form POST is ignored)
    s.post(u("berichtJahrForm-btnBerichtJahr"), headers=H, timeout=60,
           data={"id4a_hf_0": "", "selBerichtJahr": YEARS[year], "btnBerichtJahr": "1"})
    if kind == "atc":
        s.get(u("menWirk"), headers=H, timeout=60)
        for b in ("btnWirk10", "btnWirk13", "btnWirk12"):  # Verordnungen, DDD, Nettokosten
            s.get(u("wirkstForm-" + b), headers=H, timeout=60)
        x = s.post(u("wirkstForm-btnWirkAuswert"), headers=H, timeout=120,
                   data={"idf_hf_0": "", "tfWirkst": "", "tfAtcCode": term, "btnWirkAuswert": "1"})
    else:
        s.get(u("menPraep"), headers=H, timeout=60)
        for b in ("btnPro10", "btnPro13", "btnPro12"):
            s.get(u("praepForm-" + b), headers=H, timeout=60)
        x = s.post(u("praepForm-btnPraepAuswert"), headers=H, timeout=120,
                   data={"id7_hf_0": "", "tfPraep": term, "btnPraepAuswert": "1"})
    return x.text


def row_year(text):
    """Report year printed in the result rows, or None for an empty result."""
    yrs = set(re.findall(r">(20\d\d)<", text))
    return yrs.pop() if len(yrs) == 1 else ("mixed" if yrs else None)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    jobs = [(y, "atc", "A10AE Insuline und Analoga zur Injektion, lang wirkend") for y in YEARS]
    jobs += [(y, "praep", p) for y in YEARS for p in PRODUCTS]
    for job in jobs:
        name = f"{job[0]}_{job[1]}_{job[2].split()[0]}.xml"
        if (OUT / name).exists():
            continue
        for attempt in range(12):
            text = run(job)
            ry = row_year(text)
            if ry == str(job[0]):
                (OUT / name).write_text(text); print("ok", name, attempt); break
            if ry is None and "gültiges Präparat" in text:
                # empty result: accepted only if it repeats, since a stale year can also be empty
                if (OUT / (name + ".empty")).exists():
                    (OUT / name).write_text(text); print("empty", name, attempt); break
                (OUT / (name + ".empty")).write_text(text)
            time.sleep(2)
        else:
            print("FAILED", name)
