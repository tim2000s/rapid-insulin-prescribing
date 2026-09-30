"""Monthly ultra-rapid share from Medic'AM (ameli), CIP13 sheet, July 2025 to June 2026.

Downloads the two most recent semi-annual Medic'AM 'par classe ATC' workbooks into medicam/,
extracts the rapid-acting analogue CIP13 rows (codes in product_codes.csv) to
medicam/medicam_rapid_insulin_rows.csv and prints monthly boxes, units and the ultra-rapid share.
"""
import csv, io, re, urllib.request, zipfile
from collections import defaultdict
from pathlib import Path
import openpyxl

HERE = Path(__file__).parent
OUT = HERE / "medicam"; OUT.mkdir(exist_ok=True)
URLS = [
    "https://www.assurance-maladie.ameli.fr/sites/default/files/2025-07-a-12_medic-am-par-classe-atc_serie-mensuelle.zip",
    "https://www.assurance-maladie.ameli.fr/sites/default/files/2026-01-a-06_medic-am-par-classe-atc_serie-mensuelle.zip",
]
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/126"}
codes = {r["cip13"]: r for r in csv.DictReader(open(HERE / "product_codes.csv"))}

boxes = defaultdict(lambda: defaultdict(int))  # month -> brand -> boxes
units = defaultdict(lambda: defaultdict(int))
extract = []
for url in URLS:
    z = OUT / url.rsplit("/", 1)[1]
    if not z.exists():
        z.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read())
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(".xlsx")][0]
        wb = openpyxl.load_workbook(io.BytesIO(zf.read(name)), read_only=True)
    ws = [w for w in wb.worksheets if re.search(r"_cip_total$", w.title)][0]
    header = None
    for row in ws.iter_rows(values_only=True):
        if row and row[0] == "CIP13":
            header = row; continue
        if header and row[0] in codes:
            c = codes[row[0]]
            for i, h in enumerate(header):
                if h and h.startswith("Nombre de boites"):
                    month = h.split()[-1]
                    n = int(row[i] or 0)
                    boxes[month][c["brand"]] += n
                    units[month][c["brand"]] += n * int(c["units_per_box"])
                    extract.append([month, row[0], row[1], row[5], n])

with open(OUT / "medicam_rapid_insulin_rows.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["month", "cip13", "label", "atc5", "boxes"]); w.writerows(extract)

print("month    total_MU  Fiasp_MU Lyumjev_MU  ultra_share%")
T = U = 0
for m in sorted(units):
    t = sum(units[m].values()); u = units[m]["Fiasp"] + units[m]["Lyumjev"]
    T += t; U += u
    print(f"{m}  {t/1e6:8.1f}  {units[m]['Fiasp']/1e6:7.1f}  {units[m]['Lyumjev']/1e6:7.1f}  {100*u/t:6.2f}")
print(f"12 months  total {T/1e6:.1f} MU, ultra {U/1e6:.1f} MU, share {100*U/T:.2f}%")
