"""Write ultra_share_by_year.csv for Germany from the GAmSi Bundesberichte (GKV-Spitzenverband).

Source: Tabelle 8 of the consolidated December reports (Jan-Dec of each year) and the March 2026
report (Q1 2026), converted to text with pdftotext -layout into pdf/*.txt. Tabelle 8 splits
insulin aspart (A10AB05) into Biosimilar (Insulin Aspart Sanofi, Kirsty), Referenz-AM (NovoRapid)
and Sonstige (Fiasp), and insulin lispro (A10AB04) into Biosimilar (Insulin Lispro Sanofi),
Referenz-AM (Humalog) and Sonstige (Liprolog and Lyumjev together). Volume is DDD in thousands;
insulin DDD = 40 U, so DDD shares are unit shares.

Limits: the aspart split appears only from the 2020 report (no aspart biosimilar before);
Lyumjev cannot be separated from Liprolog, so the ultra-rapid share is bounded:
lower = Fiasp only, upper = Fiasp + all of 'Liprolog, Lyumjev'. Insulin glulisine (Apidra)
is not in Tabelle 8, so the denominator is aspart + lispro only.
Lilly ceased marketing Liprolog in Germany at the end of 2025 (AMK-Nachricht 18/26), so from the
Q2 2026 report onward the Sonstige lispro line should be close to Lyumjev alone.
"""
import csv, re
from pathlib import Path

HERE = Path(__file__).parent
num = lambda s: float(s.replace(".", "").replace(",", "."))


def block(lines, head):
    for i, l in enumerate(lines):
        if l.strip() == head:
            out = {"total": num(lines[i + 1].split()[-3 - 1])}
            for l2 in lines[i + 2:i + 6]:
                m = re.match(r"\s+(Biosimilar|Referenz-AM|Sonstige)\s+(.+?)\s{2,}([\d.]+)\s+([\d.]+)\s+", l2)
                if m:
                    out[m.group(1)] = (m.group(2).strip(), num(m.group(4)))
            return out
    return None


import subprocess
for pdf in (HERE / "pdf").glob("*.pdf"):  # regenerate text layer where missing
    if not pdf.with_suffix(".txt").exists():
        subprocess.run(["pdftotext", "-layout", str(pdf), str(pdf.with_suffix(".txt"))], check=True)

rows = []
for f in sorted((HERE / "pdf").glob("Bundesbericht_GAmSi_*_konsolidiert.txt")):
    ym = re.search(r"_(\d{6})_", f.name).group(1)
    if ym[4:] not in ("12", "03") or (ym[4:] == "03" and ym[:4] != "2026"):
        continue
    L = f.read_text(errors="replace").splitlines()
    asp, lis = block(L, "Insulin aspart"), block(L, "Insulin lispro")
    if not asp or not lis:
        print(f.name, "no aspart/lispro split; skipped")
        continue
    # DDD totals: second numeric column of the header line
    tot_asp = sum(v[1] for k, v in asp.items() if k != "total")
    tot_lis = sum(v[1] for k, v in lis.items() if k != "total")
    assert "Fiasp" in asp["Sonstige"][0], asp
    assert "Lyumjev" in lis["Sonstige"][0] or ym < "2020", lis
    fiasp = asp["Sonstige"][1]; lip_lyu = lis["Sonstige"][1]
    den = tot_asp + tot_lis
    label = ym[:4] if ym[4:] == "12" else "2026 Q1"
    lo = 100 * fiasp / den; hi = 100 * (fiasp + lip_lyu) / den
    rows.append([label, round(lo, 2), round(lo, 2), "",
                 "DDD (40 U) = units, GKV outpatient prescriptions, GAmSi Tabelle 8",
                 f"aspart+lispro only (glulisine not reported), {den/1000:.1f} M DDD = {den*0.04/1000:.2f} bn U; "
                 f"ultra_pct is Fiasp only (lower bound); upper bound incl. all Liprolog+Lyumjev {hi:.2f}%; "
                 f"Fiasp share of aspart {100*fiasp/tot_asp:.2f}%"
                 + ("; PROVISIONAL, Q1 only; Liprolog marketing ceased end 2025 (AMK-Nachricht 18/26), so the upper bound is Lyumjev plus Liprolog run-out stock" if label == "2026 Q1" else "")])
with open(HERE / "ultra_share_by_year.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["year", "ultra_pct", "fiasp_pct", "lyumjev_pct", "basis", "denominator_note"])
    w.writerows(rows)
for r in rows:
    print(r[0], r[1], r[5])
