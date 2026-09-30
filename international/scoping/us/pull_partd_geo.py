"""Medicare Part D Prescribers by Geography and Drug, national and state rows
for rapid-acting analogue brand names, 2017-2024 (data.cms.gov API).
Claims and 30-day fills only; no dosage units in this dataset."""
import json, urllib.request, urllib.parse, pandas as pd
from concurrent.futures import ThreadPoolExecutor
from us_provisional_shares import PARTD

IDS = {2017: "7863e41c-3f6f-4889-93a8-be65e9f3d073", 2018: "b083c9b6-b841-4676-8d0a-fb03ee1431a1",
       2019: "73a6335e-f16f-4c81-a84b-6b5a986e2bf8", 2020: "83891e77-99cf-4865-b60a-97703b916e09",
       2021: "7dda2a9d-034a-446a-b4b3-e1254e0127b2", 2022: "1fc57194-a51d-4864-aee6-de0889488151",
       2023: "3463648b-1971-478d-84ca-80cadc758153", 2024: "c8ea3f8e-3a09-4fea-86f2-8902fb4b0920"}


def get(job):
    yr, brand = job
    q = urllib.parse.urlencode({"filter[Brnd_Name]": brand, "size": 200})
    d = json.load(urllib.request.urlopen(f"https://data.cms.gov/data-api/v1/dataset/{IDS[yr]}/data?{q}", timeout=120))
    for r in d:
        r["year"] = yr
    return d


if __name__ == "__main__":
    jobs = [(y, b) for y in IDS for b in PARTD]
    with ThreadPoolExecutor(7) as ex:
        rows = [r for res in ex.map(get, jobs) for r in res]
    df = pd.DataFrame(rows)
    df.to_csv("partd_geo_rapid_2017_2024.csv", index=False)
    n = df[df.Prscrbr_Geo_Lvl == "National"].copy()
    n["cls"] = n.Brnd_Name.map(lambda b: PARTD[b][1])
    n["Tot_Clms"] = n.Tot_Clms.astype(float)
    t = n.groupby(["year", "cls"]).Tot_Clms.sum().unstack().fillna(0)
    t["ultra_share_claims_pct"] = 100 * t.ultra / (t.ultra + t.standard)
    print(t.round(2))
    t.to_csv("partd_geo_national_ultra_share_claims.csv")
