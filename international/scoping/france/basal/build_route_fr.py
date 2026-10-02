"""Write route.csv for France: HAS Commission de la Transparence SMR and ASMR ratings.

Quotes are the decision wording as published by HAS and reproduced in the BDPM files
captures/CIS_HAS_SMR_bdpm.txt and captures/CIS_HAS_ASMR_bdpm.txt (downloaded 2026-10-02 from
base-donnees-publique.medicaments.gouv.fr). The opinion PDF for each CT number is saved by
fetch_has.py as captures/has_<product>_<ct>_avis.pdf with a pdftotext version beside it; run that
first. Market-entry dates come from the BDPM presentation file (../bdpm/CIS_CIP_bdpm.txt).
"""
import csv
import re
from pathlib import Path

HERE = Path(__file__).parent
CAP = HERE / "captures"
# CT number -> (product label, capture stem)
CT = {"CT-12822": ("Tresiba (degludec)", "has_tresiba_ct-12822"),
      "CT-16576": ("Tresiba 200 (degludec)", "has_tresiba_ct-16576"),
      "CT-16983": ("Tresiba (degludec), children", "has_tresiba_ct-16983"),
      "CT-17265": ("Tresiba (degludec)", "has_tresiba_ct-17265"),
      "CT-14452": ("Toujeo (glargine 300)", "has_toujeo_ct-14452"),
      "CT-16883": ("Toujeo (glargine 300) and Lantus", "has_lantus_toujeo_ct-16883"),
      "CT-18415": ("Toujeo (glargine 300), children", "has_toujeo_ct-18415"),
      "CT-14408": ("Abasaglar (glargine 100 biosimilar)", "has_abasaglar_ct-14408"),
      "CT-12976": ("Lantus (glargine 100)", "has_lantus_ct-12976"),
      "CT-16059": ("Fiasp (faster aspart)", "has_fiasp_ct-16059"),
      "CT-18375": ("Fiasp (faster aspart), children", "has_fiasp_ct-18375"),
      "CT-18474": ("Lyumjev (ultra-rapid lispro)", "has_lyumjev_ct-18474")}


def read(name):
    out = {}
    for raw in open(CAP / name, "rb"):
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError:
            s = raw.decode("cp1252", errors="replace")
        p = s.rstrip("\r\n").split("\t")
        if len(p) > 5 and p[1] in CT and p[1] not in out:
            out[p[1]] = (p[2], p[3], p[4], p[5].replace("<br>", " ").replace("  ", " ").strip(" ;"))
    return out


def main():
    smr, asmr = read("CIS_HAS_SMR_bdpm.txt"), read("CIS_HAS_ASMR_bdpm.txt")
    links = dict(l.split("\t") for l in open(CAP / "HAS_LiensPageCT_bdpm.txt").read().splitlines() if "\t" in l)
    rows = []
    for ct, (prod, stem) in CT.items():
        s, a = smr.get(ct), asmr.get(ct)
        if s is None:  # SMR not in the BDPM file for this CT; take the sentence from the opinion PDF
            t = re.sub(r"\s+", " ", open(CAP / f"{stem}_avis.txt").read())
            m = re.search(r"[^.]{0,200}service médical rendu par [^.]{0,300}est (important|modéré|faible|insuffisant)[^.]*\.", t)
            if m:
                s = ("", "", m.group(1).capitalize(), m.group(0).strip() + " [from opinion PDF]")
        d = (a or s)[1]
        date = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        dec = f"{(a or s)[0]}, {ct}: SMR {s[2] if s else 'not restated'}; ASMR {a[2] if a else 'not restated'}"
        quote = " | ".join(x for x in [s[3] if s else "", a[3] if a else ""] if x)
        cap = f"captures/{stem}_avis.pdf; captures/{stem}_avis.txt"
        rows.append([prod, "HAS Commission de la Transparence", dec, date, quote, links[ct], cap])
    # market entry, from the ANSM BDPM presentation file
    for cip, prod in [("3400926853389", "Tresiba (degludec)"), ("3400930016671", "Toujeo (glargine 300)"),
                      ("3400930083161", "Fiasp (faster aspart)"), ("3400930204023", "Lyumjev (ultra-rapid lispro)"),
                      ("3400930270356", "Semglee (glargine 100 biosimilar)")]:
        for line in open(HERE.parent / "bdpm" / "CIS_CIP_bdpm.txt", encoding="latin-1"):
            f = line.rstrip("\n").split("\t")
            if len(f) > 9 and f[6] == cip:
                d = f[5]
                rows.append([prod, "ANSM BDPM (presentation register)",
                             f"marketed and reimbursed at {f[8].strip()}, price {f[9]} euro per box",
                             f"{d[6:]}-{d[3:5]}-{d[:2]}", "\t".join(f[2:10]),
                             "https://base-donnees-publique.medicaments.gouv.fr/telechargement",
                             "../bdpm/CIS_CIP_bdpm.txt"])
    rows.sort(key=lambda r: (r[0].split(" ")[0], r[3]))
    with open(HERE / "route.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["product", "body", "decision", "date", "quote", "url", "capture"])
        w.writerows(rows)
    for r in rows:
        print(r[3], r[0], "|", r[2])


if __name__ == "__main__":
    main()
