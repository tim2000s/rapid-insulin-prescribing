"""Trim the PBS Date of Supply files to the rapid-acting analogue items.

Inputs are the raw downloads from https://www.pbs.gov.au/info/statistics/dos-and-dop/dos-and-dop
(monthly report xlsx, Jul 2022 to Jul 2026; quarterly supplementary csv by pharmacy type,
FY2020-21 onward). Output keeps every row whose item code is in the rapid-acting analogue
set (ATC A10AB04, A10AB05, A10AB06), which is what the ultra-rapid share needs.
"""
import csv, glob, openpyxl

ITEMS = {"01921D", "08084L", "08085M", "08212F", "08435Y", "08571D", "09224L",
         "11645X", "11705C", "11706D", "12237C", "12254Y", "12268Q", "13651L"}

if __name__ == "__main__":
    wb = openpyxl.load_workbook("raw_dos-jul-2022-to-jul-2026.xlsx", read_only=True)
    with open("dos_monthly_rapid_2022_2026.csv", "w", newline="") as f:
        w = csv.writer(f); hdr = None
        for ws in wb.worksheets:
            for i, r in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    if hdr is None: hdr = r; w.writerow(r)
                    continue
                if r[1] in ITEMS or r[2] in ("A10AB04", "A10AB05", "A10AB06"):
                    w.writerow(r)
    with open("dos_pharmacytype_rapid_2020_2026.csv", "w", newline="") as f:
        w = csv.writer(f); first = True
        for p in sorted(glob.glob("raw_dos-jul-*-phrmcy-type.csv")):
            with open(p, newline="") as g:
                rd = csv.reader(g); hdr = next(rd)
                if first: w.writerow(hdr); first = False
                for r in rd:
                    if r[1] in ITEMS: w.writerow(r)
