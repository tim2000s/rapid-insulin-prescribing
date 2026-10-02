"""Long-acting analogue insulin on the PBS by product and financial year (July to June).

Inputs are the raw PBS Date of Supply downloads already saved one directory up, the same
files the rapid-acting series (../build_ultra_share.py) was built from:
  raw_dos-jul-YYYY-to-jun-YYYY-phrmcy-type.csv  quarterly supplementary, FY2020-21 to FY2025-26
  raw_dos-jul-2022-to-jul-2026.xlsx             monthly report, Jul 2022 to Jul 2026
  raw_dop-ytd-jan-2018.zip                      date of processing, Jul 2017 to Jan 2018
  raw_pbs-item-drug-map.csv                     item code to drug and ATC

Basis matches the rapid series: PBS prescriptions, every row of the pharmacy-type files
(all patient categories, above and under co-payment, no filter on drug type), financial
year by month of supply. Prescriptions are not units. A prescription is for up to five
packs, and pack contents differ (Toujeo 11302W is 5 x 1.5 mL at 300 units/mL = 2,250 units;
11308E is 3 x 1.5 mL at 300 units/mL = 1,350 units; the 100 units/mL items are 5 x 3 mL =
1,500 units), so a prescription share is not a share of insulin dispensed.

Denominator: long-acting analogues only, ATC A10AE04 glargine, A10AE05 detemir and A10AE06
degludec. NPH (A10AC) and every premix (A10AD, which includes Ryzodeg, degludec with aspart,
A10AD06) are excluded. This mirrors the rapid denominator, which was ATC A10AB04/05/06 only
and left the analogue premixes out. Xultophy (A10AE56) and Suliqua (A10AE54) do not occur in
the PBS files, so excluding them changes nothing. Ryzodeg counts are written to a separate
column of the item table because Ryzodeg was the only PBS route to degludec before July 2026.

The DoS files are by PBS item code, not by brand. Glargine 100 units/mL brands (Lantus,
Optisulin, Semglee, any others) that share an item code cannot be separated; the brands
listed under each item are taken from the PBS API dump written by fetch_basal_prices.py.
"""
import collections, csv, glob, io, os, zipfile
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.join(HERE, "..")
ATC_KEEP = ("A10AE04", "A10AE05", "A10AE06", "A10AD06")
PRODUCT = {  # item code -> product group used in the share
    "09039R": "glargine100", "11815W": "glargine100",
    "11302W": "glargine300", "11308E": "glargine300",
    "09040T": "detemir", "12236B": "detemir",
    "15393E": "degludec",
    "11417X": "ryzodeg", "11426J": "ryzodeg",
}
SHARE = ["degludec", "glargine300", "glargine100", "detemir"]


def item_atc():
    m = {}
    for r in csv.DictReader(open(os.path.join(UP, "raw_pbs-item-drug-map.csv"), encoding="latin-1")):
        m[r["ITEM_CODE"]] = (r["ATC5_Code"], r["DRUG_NAME"])
    return m


def scan_csv(job):
    """Return rows (month, item, prescriptions) for insulin items from one pharmacy-type file."""
    path, items = job
    out = []
    with open(path, newline="") as g:
        for r in csv.DictReader(g):
            if r["ITEM_CODE"] in items:
                out.append((int(r["MONTH_OF_SUPPLY"]), r["ITEM_CODE"], int(r["PRESCRIPTIONS"])))
    return os.path.basename(path), out


def scan_xlsx(job):
    path, _ = job
    import openpyxl
    out = []
    wb = openpyxl.load_workbook(path, read_only=True)
    for ws in wb.worksheets:
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i and r[2] in ATC_KEEP:
                out.append((int(r[0]), r[1], int(r[7] or 0)))
    return os.path.basename(path), out


def scan_dop(job):
    path, items = job
    out = []
    with zipfile.ZipFile(path) as z:
        with z.open("dop-ytd-jan-2018.csv") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1")):
                if r["ITEM_CODE"] in items:
                    out.append((int(r["MONTH_OF_PROCESS"]), r["ITEM_CODE"], int(r["PRESCRIPTIONS"])))
    return os.path.basename(path), out


def run(job):
    kind, path, items = job
    return kind, {"csv": scan_csv, "xlsx": scan_xlsx, "dop": scan_dop}[kind]((path, items))


def fy(m):
    return m // 100 + (1 if m % 100 >= 7 else 0)


if __name__ == "__main__":
    amap = item_atc()
    items = {k for k, (a, _) in amap.items() if a in ATC_KEEP}
    unexpected = items - set(PRODUCT)
    assert not unexpected, f"unclassified long-acting items: {unexpected}"
    jobs = [("csv", p, items) for p in sorted(glob.glob(os.path.join(UP, "raw_dos-jul-*-phrmcy-type.csv")))]
    jobs += [("xlsx", os.path.join(UP, "raw_dos-jul-2022-to-jul-2026.xlsx"), items),
             ("dop", os.path.join(UP, "raw_dop-ytd-jan-2018.zip"), items)]
    with ProcessPoolExecutor(max_workers=7) as ex:
        res = list(ex.map(run, jobs))

    # Trimmed copies of the pharmacy-type rows, so the FY table can be checked without the raw files.
    by_fy = collections.defaultdict(collections.Counter)
    by_item_fy = collections.defaultdict(collections.Counter)
    first = {}
    with open(os.path.join(HERE, "dos_pharmacytype_basal_2020_2026.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["MONTH_OF_SUPPLY", "ITEM_CODE", "PRESCRIPTIONS", "source"])
        for kind, (name, rows) in res:
            for m, it, n in rows:
                if n > 0:
                    key = (PRODUCT[it], kind)
                    first[key] = min(first.get(key, 999999), m)
                    first[(it, kind)] = min(first.get((it, kind), 999999), m)
                if kind == "csv":
                    w.writerow([m, it, n, name])
                    by_fy[fy(m)][PRODUCT[it]] += n
                    by_item_fy[fy(m)][it] += n

    with open(os.path.join(HERE, "basal_share_by_year.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["country", "year", "degludec_pct", "glargine300_pct", "glargine100_pct", "detemir_pct",
                    "total_units_m", "total_scripts", "basis", "note"])
        for y in sorted(by_fy):
            c = by_fy[y]; tot = sum(c[p] for p in SHARE)
            pct = [round(100 * c[p] / tot, 2) for p in SHARE]
            note = (f"denominator A10AE04/05/06 only (glargine, detemir, degludec); NPH and premixes excluded, "
                    f"as in the rapid series; Ryzodeg (degludec+aspart, A10AD06) excluded, {c['ryzodeg']} scripts "
                    f"this year; degludec alone (Tresiba, 15393E) first supplied on the PBS Jul 2026; "
                    f"glargine100 = items 09039R and 11815W, whose only brand in the Sep 2026 schedule is Optisulin "
                    f"(Sanofi); Lantus, Basaglar (PBAC Mar 2015) and Semglee (PBAC Jul 2018) were listed or recommended "
                    f"under the same items and cannot be separated by brand; glargine300 = Toujeo 11302W, 11308E; "
                    f"detemir = Levemir 09040T, 12236B")
            w.writerow(["Australia", f"FY{y-1}-{y%100:02d}", *pct, "", tot,
                        "PBS prescriptions (date of supply, pharmacy-type supplementary files); prescriptions are not units",
                        note])
            print(f"FY{y-1}-{y%100:02d}", dict(zip(SHARE, pct)), "n =", tot, "ryzodeg", c["ryzodeg"])

    with open(os.path.join(HERE, "basal_item_scripts_by_year.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["year", "item_code", "product", "drug_name", "atc", "prescriptions"])
        for y in sorted(by_item_fy):
            for it in sorted(by_item_fy[y]):
                w.writerow([f"FY{y-1}-{y%100:02d}", it, PRODUCT[it], amap[it][1], amap[it][0], by_item_fy[y][it]])

    with open(os.path.join(HERE, "basal_first_month.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["key", "source", "first_month_with_scripts", "window"])
        win = {"dop": "Jul 2017 to Jan 2018 (processing month)", "csv": "Jul 2020 to Jun 2026",
               "xlsx": "Jul 2022 to Jul 2026"}
        for (k, src), m in sorted(first.items()):
            w.writerow([k, src, m, win[src]])
    for (k, src), m in sorted(first.items()):
        if k in PRODUCT.values(): print("first", k, src, m)
    # Monthly product counts from the monthly report, the only file reaching Jul 2026, where
    # degludec alone first appears. Same denominator as the yearly table.
    for kind, (name, rows) in res:
        if kind == "xlsx":
            mon = collections.defaultdict(collections.Counter)
            for m, it, n in rows:
                mon[m][PRODUCT[it]] += n
            with open(os.path.join(HERE, "basal_monthly_2022_2026.csv"), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["month", "degludec", "glargine300", "glargine100", "detemir", "ryzodeg",
                            "total_long_acting", "degludec_pct"])
                for m in sorted(mon):
                    c = mon[m]; tot = sum(c[p] for p in SHARE)
                    w.writerow([m, *[c[p] for p in SHARE], c["ryzodeg"], tot, round(100 * c["degludec"] / tot, 2)])
            for m in sorted(mon)[-3:]:
                c = mon[m]; tot = sum(c[p] for p in SHARE)
                print(m, dict(c), "degludec %", round(100 * c["degludec"] / tot, 2))
