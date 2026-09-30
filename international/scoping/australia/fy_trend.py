"""Fiasp share of PBS rapid-acting analogue prescriptions by financial year, from the
quarterly supplementary (pharmacy type) Date of Supply files, FY2020-21 to FY2025-26."""
import csv, collections
FIASP = {"11705C", "11706D", "13651L"}
if __name__ == "__main__":
    s = collections.Counter(); f = collections.Counter()
    for r in csv.DictReader(open("dos_pharmacytype_rapid_2020_2026.csv")):
        m = int(r["MONTH_OF_SUPPLY"]); fy = m // 100 + (1 if m % 100 >= 7 else 0)
        n = int(r["PRESCRIPTIONS"]); s[fy] += n
        if r["ITEM_CODE"] in FIASP: f[fy] += n
    for fy in sorted(s): print(f"FY{fy-1}-{fy%100:02d}: Fiasp {f[fy]} / {s[fy]} = {100*f[fy]/s[fy]:.2f}%")
