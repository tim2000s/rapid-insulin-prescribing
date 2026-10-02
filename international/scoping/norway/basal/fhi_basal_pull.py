"""Long-acting analogue insulin volumes and shares, Norway, from the FHI open statistics API.

Same sources as ../fhi_atc_pull.py uses for rapid-acting insulin, at ATC 7th level only:
  lmr table 825: Legemiddelregisteret, prescriptions dispensed by pharmacies, DDD, 2004-2025
  gs  table 847: grossist-based (wholesale, all sectors), DDD, 1999-2025 (pulled 2004-2025)
ATC A10AE04 glargine, A10AE05 detemir, A10AE06 degludec. Insulin DDD = 40 U for all three, so
shares of DDD are shares of units. Neither table has a product or strength dimension, so glargine
300 (Toujeo) cannot be separated from glargine 100 (Lantus, Abasaglar, Semglee); glargine300_pct is
left empty and glargine100_pct holds all glargine. The prescription register (lmr) is the primary
basis, matching community dispensing in the other countries; wholesale shares are in the note.

Writes lmr_825_basal_atc.csv, gs_847_basal_atc.csv (raw API responses), basal_share_by_year.csv
and basal_first_year.csv.
"""
import csv
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
B = "https://statistikk-data.fhi.no/api/open/v1"
ATC = ["A10AE04", "A10AE05", "A10AE06"]
YEARS = [str(y) for y in range(2004, 2026)]
CLS = {"A10AE04": "glargine", "A10AE05": "detemir", "A10AE06": "degludec"}


def item(code, vals):
    return {"code": code, "filter": "item", "values": vals}


def post(job):
    src, tid, dims, fname = job
    body = {"dimensions": dims, "response": {"format": "csv2", "maxRowCount": 50000}}
    req = urllib.request.Request(f"{B}/{src}/Table/{tid}/data", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    (HERE / fname).write_bytes(raw)
    return fname


def read(fname, ddd_col, year_col):
    out = {}
    for r in csv.DictReader(io.StringIO((HERE / fname).read_text(encoding="utf-8-sig")), delimiter=";"):
        atc = r[list(r)[0]].split(" ")[0]
        v = r[ddd_col]
        if atc in CLS and v not in ("", None) and v.replace(".", "").isdigit():
            out[(r[year_col], CLS[atc])] = float(v)
    return out


def main():
    jobs = [("lmr", 825, [item("Atc_Verdi", ATC), item("Kjonn_Verdi", ["TOTALT"]),
                          item("Aldersgruppe_Verdi", ["TOTALT"]), item("Utlevering_Ar", YEARS),
                          item("MEASURE_TYPE", ["AntallBrukere", "DDD"])], "lmr_825_basal_atc.csv"),
            ("gs", 847, [item("ATC_Verdi", ATC), item("Salg_Ar", YEARS), item("MEASURE_TYPE", ["DDD"])],
             "gs_847_basal_atc.csv")]
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(post, jobs))
    lmr = read("lmr_825_basal_atc.csv", "Definerte døgndoser (DDD)", "År")
    gs = read("gs_847_basal_atc.csv", "Definerte døgndoser (DDD)", "År")
    rows, first = [], {}
    for y in YEARS:
        d = {c: lmr.get((y, c), 0.0) for c in CLS.values()}
        g = {c: gs.get((y, c), 0.0) for c in CLS.values()}
        for c in CLS.values():
            if d[c] > 0:
                first.setdefault(c, y)
        t, T = sum(d.values()), sum(g.values())
        if t == 0:
            continue
        rows.append(["Norway", y, round(100 * d["degludec"] / t, 2), "", round(100 * d["glargine"] / t, 2),
                     round(100 * d["detemir"] / t, 2), round(t * 40 / 1e6, 1),
                     "DDD (40 U) = units, FHI Legemiddelregisteret table 825 (dispensed prescriptions), ATC level",
                     "glargine 300 not separable from glargine 100 at ATC level; glargine100_pct = all glargine "
                     "(Lantus, Toujeo, Abasaglar, Semglee). Wholesale (gs 847) shares: "
                     + (f"degludec {100 * g['degludec'] / T:.1f}%, glargine {100 * g['glargine'] / T:.1f}%, "
                        f"detemir {100 * g['detemir'] / T:.1f}%" if T else "n/a")
                     + "; Xultophy (A10AE56), Suliqua (A10AE54), NPH and premixes excluded"])
    with open(HERE / "basal_share_by_year.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["country", "year", "degludec_pct", "glargine300_pct", "glargine100_pct", "detemir_pct",
                    "total_units_m", "basis", "note"])
        w.writerows(rows)
    with open(HERE / "basal_first_year.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["molecule", "first_lmr_year"])
        for c, y in first.items():
            w.writerow([c, f"{y} (series start)" if y == YEARS[0] else y])
    for r in rows:
        print(r[1:7])
    print(first)


if __name__ == "__main__":
    main()
