"""Pull Norwegian ATC-level rapid-acting analogue data from the FHI open statistics API.

Both FHI sources resolve only to ATC 7th level (A10AB04/05/06); no product or varenummer
dimension exists, so these give the denominator only.
  lmr table 825: Legemiddelregisteret (prescriptions dispensed), users and DDD, annual 2004-2025
  gs  table 847: Grossistbasert legemiddelstatistikk (wholesale), DDD, annual 1999-2025
API docs: https://statistikk-data.fhi.no/swagger/index.html
"""
import json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
B = "https://statistikk-data.fhi.no/api/open/v1"
ATC = ["A10AB", "A10AB04", "A10AB05", "A10AB06"]
YEARS = [str(y) for y in range(2015, 2026)]


def post(src, tid, dims, fname):
    body = {"dimensions": dims, "response": {"format": "csv2", "maxRowCount": 50000}}
    req = urllib.request.Request(f"{B}/{src}/Table/{tid}/data", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        open(os.path.join(HERE, fname), "wb").write(r.read())


def item(code, vals):
    return {"code": code, "filter": "item", "values": vals}


if __name__ == "__main__":
    post("lmr", 825, [item("Atc_Verdi", ATC), item("Kjonn_Verdi", ["TOTALT"]),
                      item("Aldersgruppe_Verdi", ["TOTALT"]), item("Utlevering_Ar", YEARS),
                      item("MEASURE_TYPE", ["AntallBrukere", "DDD"])], "lmr_825_rapid_atc.csv")
    post("gs", 847, [item("ATC_Verdi", ATC), item("Salg_Ar", YEARS),
                     item("MEASURE_TYPE", ["DDD"])], "gs_847_rapid_atc.csv")
