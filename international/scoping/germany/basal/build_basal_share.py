"""Write basal_share_by_year.csv: shares of long-acting insulin analogue DDD in German statutory
health insurance (GKV) outpatient prescribing, 2012-2024, with GAmSi glargine rows for 2025 and
Q1 2026.

Sources
- WIdO PharMaAnalyst (GKV-Arzneimittelindex), annual, fetched by fetch_pharmaanalyst.py into
  pharmaanalyst/. ATC group A10AE gives DDD per substance (glargin A10AE04, detemir A10AE05,
  degludec A10AE06, icodec A10AE07); the product query "Toujeo" gives glargine 300 U/ml.
  WIdO states the tool covers "rund 95 Prozent aller Arzneimittel" prescribed to GKV members, so a
  product below its volume cut-off returns nothing. This matters only for degludec in 2016 to 2018.
- GAmSi Bundesberichte (GKV-Spitzenverband), Tabelle 8, ../pdf/*.txt. Glargine only, split into
  Biosimilar (Abasaglar, Semglee), Referenz-AM (Lantus) and Sonstige (Toujeo). Degludec and detemir
  are not in Tabelle 8 (it lists substances with biosimilar competition), so GAmSi cannot give
  their shares and the 2025 and 2026 Q1 rows carry the glargine split only.

Definitions
- Denominator: glargine + detemir + degludec + icodec DDD (single-substance long-acting analogues).
  Fixed combinations with GLP-1 receptor agonists (A10AE54 glargine/lixisenatide, Suliqua; A10AE56
  degludec/liraglutide, Xultophy) are excluded, a modelling choice; their DDD are given in the note.
  Human NPH insulin (A10AC01) is not a long-acting analogue and is excluded.
- One DDD = 40 units for every insulin in the German ATC/DDD index (WIdO ATC GKV-AI 2025,
  captures/wido_atc_gkv-ai_2025_insulin_ddd.txt), so DDD shares are unit shares.
- glargine300 = Toujeo product DDD; glargine100 = all other glargine (Lantus, Abasaglar, Semglee,
  imports and any other brand) = glargine total minus Toujeo.
"""
import csv, html, re
from pathlib import Path

HERE = Path(__file__).parent
PA = HERE / "pharmaanalyst"
num = lambda s: float(s.replace(".", "").replace(",", "."))


def rows_of(path):
    """Parse a PharMaAnalyst Ajax response into {label: (year, ddd_thousand)}."""
    t = path.read_text()
    out = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        if len(cells) < 6 or not re.fullmatch(r"20\d\d", cells[1]):
            continue
        out[cells[0]] = cells
    return out


def ddd(cells, kind):
    # ATC rows: name, year, ATC, Vo, d%, Netto, d%, DDD, d%, ...
    # product rows: name, year, Wirkstoff, ATC, Vo, d%, rank, Netto, d%, rank, DDD, d%, rank, ...
    return num(cells[7] if kind == "atc" else cells[10])


rows = []
for y in range(2012, 2025):
    atc = rows_of(PA / f"{y}_atc_A10AE.xml")
    assert atc and all(c[1] == str(y) for c in atc.values()), (y, "year mismatch in ATC response")
    g = ddd(atc["Insulin glargin"], "atc")
    det = ddd(atc["Insulin detemir"], "atc")
    deg = ddd(atc["Insulin degludec"], "atc") if "Insulin degludec" in atc else 0.0
    ico = ddd(atc["Insulin icodec"], "atc") if "Insulin icodec" in atc else 0.0
    combos = {k: ddd(v, "atc") for k, v in atc.items() if " und " in k}
    tj = rows_of(PA / f"{y}_praep_Toujeo.xml")
    tou = ddd(tj["Toujeo"], "praep") if tj else 0.0
    trs = rows_of(PA / f"{y}_praep_Tresiba.xml")
    if trs:
        assert abs(ddd(trs["Tresiba"], "praep") - deg) < 0.2, (y, "Tresiba product DDD differs from degludec substance DDD")
    den = g + det + deg + ico
    cost = lambda name: num(atc[name][-1]) if name in atc else None  # net cost per DDD, EUR
    note = [f"glargine {g/1000:.1f} M DDD, of which Toujeo {100*tou/g:.1f}%",
            f"net cost per DDD: glargine {cost('Insulin glargin'):.2f} EUR, detemir {cost('Insulin detemir'):.2f} EUR"
            + (f", degludec {cost('Insulin degludec'):.2f} EUR" if deg else "")]
    if ico:
        note.append(f"icodec {ico/1000:.2f} M DDD in denominator")
    if combos:
        note.append("excluded combinations: " + "; ".join(f"{k} {v/1000:.2f} M DDD" for k, v in combos.items()))
    if not deg and y >= 2014:
        note.append("no degludec row returned (below PharMaAnalyst coverage or not marketed; Tresiba off the German market 15 Jan 2016 to 1 Dec 2018)")
    rows.append(["Germany", str(y), round(100 * deg / den, 2), round(100 * tou / den, 2),
                 round(100 * (g - tou) / den, 2), round(100 * det / den, 2), round(den * 1000 * 40 / 1e6),
                 "DDD (40 U), GKV outpatient prescriptions, WIdO PharMaAnalyst (GKV-Arzneimittelindex); denominator glargine+detemir+degludec+icodec",
                 "; ".join(note)])

# GAmSi Tabelle 8: glargine split only
for f in sorted((HERE.parent / "pdf").glob("Bundesbericht_GAmSi_*_konsolidiert.txt")):
    ym = re.search(r"_(\d{6})_", f.name).group(1)
    label = ym[:4] if ym[4:] == "12" else ("2026 Q1" if ym == "202603" else None)
    if label not in ("2024", "2025", "2026 Q1"):
        continue
    L = f.read_text(errors="replace").splitlines()
    i = next(k for k, l in enumerate(L) if l.strip() == "Insulin glargin")
    part = {}
    for l in L[i + 2:i + 6]:
        m = re.match(r"\s+(Biosimilar|Referenz-AM|Sonstige)\s+(.+?)\s{2,}([\d.]+)\s+([\d.]+)\s+", l)
        if m:
            part[m.group(1)] = (m.group(2).strip(), num(m.group(4)))
    assert part["Sonstige"][0] == "Toujeo", part
    tot = sum(v[1] for v in part.values())
    note = (f"GAmSi Tabelle 8 glargine only: {tot/1000:.1f} M DDD, Toujeo {100*part['Sonstige'][1]/tot:.1f}%, "
            f"Lantus {100*part['Referenz-AM'][1]/tot:.1f}%, biosimilars ({part['Biosimilar'][0]}) {100*part['Biosimilar'][1]/tot:.1f}%; "
            "degludec and detemir are not reported in GAmSi, so no long-acting denominator")
    if label == "2024":
        pa = next(r for r in rows if r[1] == "2024")
        pa[8] += "; cross-check, " + note.replace("GAmSi Tabelle 8 glargine only", "GAmSi 2024 glargine") + \
            " (GAmSi is pre-audit billing data at a fixed cut-off, PharMaAnalyst is extrapolated to the full GKV)"
        continue
    rows.append(["Germany", label, "", "", "", "", "",
                 "DDD (40 U), GKV outpatient prescriptions, GAmSi Tabelle 8", note
                 + ("; PROVISIONAL, Q1 only" if label == "2026 Q1" else "")])

with open(HERE / "basal_share_by_year.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["country", "year", "degludec_pct", "glargine300_pct", "glargine100_pct", "detemir_pct",
                "total_units_m", "basis", "note"])
    w.writerows(rows)
for r in rows:
    print(r[1:7])
