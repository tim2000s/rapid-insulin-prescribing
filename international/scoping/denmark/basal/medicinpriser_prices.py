"""Pull current Danish pharmacy prices and reimbursement icons for selected insulins.

medicinpriser.dk is an ASP.NET WebForms site: the search is a POST carrying the page's
__VIEWSTATE, and the product page is a GET on Default.aspx?id=15&vnr=<varenummer>. The
reimbursement status of a package is shown only as an icon (alt text "Generelt tilskud" or
"Klausuleret tilskud til receptpligtig medicin") in the search-result grid, so it is read
from there, while the purchase price (AIP, "Apotekets indkøbspris") and the consumer price
(AUP, "Pris pr. pakning", incl. VAT and dispensing fee) are read from the product page.

Only packages sold by the marketing-authorisation holder are written to the CSV; parallel
imports (firm names such as Orifarm, 2care4, Abacus) are recorded in the raw captures but
excluded, because their prices are not the list price set by the manufacturer.

Captures go to captures/medicinpriser_*. Prices change every 14 days, so the fetch date is
written on every row.
"""
import csv
import datetime as dt
import html
import re
import time
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://www.medicinpriser.dk/default.aspx"
HERE = Path(__file__).resolve().parent
CAP = HERE / "captures"

# (label, search term, product-name prefix, required pack text, manufacturer firm)
TARGETS = [
    ("Tresiba 100 FlexTouch", "tresiba", "Tresiba 100 Flextouch", "5 x 3 ml", "Novo"),
    ("Toujeo SoloStar", "toujeo", "Toujeo SoloStar", "", "Sanofi"),
    ("Toujeo DoubleStar", "toujeo", "Toujeo DoubleStar", "", "Sanofi"),
    ("Lantus SoloStar", "lantus", "Lantus SoloStar", "5 x 3 ml", "Sanofi"),
    ("Semglee", "semglee", "Semglee", "5 x 3 ml", "Biocon"),
    # The Lilly-sold Abasaglar package is listed as withdrawn ("Udgået"); only parallel
    # imports carry a price, so every Abasaglar row is kept and the firm is shown.
    ("Abasaglar KwikPen", "abasaglar", "Abasaglar KwikPen", "", ""),
    # Novo sells Levemir FlexPen in Denmark only as a single 3 ml pen; 5 x 3 ml packs
    # are parallel imports.
    ("Levemir FlexPen", "levemir", "Levemir FlexPen", "", "Novo"),
    ("Fiasp FlexTouch", "fiasp", "Fiasp FlexTouch", "5 x 3 ml", "Novo"),
    ("NovoRapid FlexPen", "novorapid", "Novorapid FlexPen", "5 x 3 ml", "Novo"),
    ("Humalog KwikPen", "humalog", "Humalog KwikPen", "5 x 3 ml", "Eli Lilly"),
    ("Lyumjev", "lyumjev", "Lyumjev", "", ""),
]


def text_of(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def search(session, term):
    r = session.get(BASE, timeout=60)
    form = {k: html.unescape(v) for k, v in
            re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', r.text)
            if k.startswith("__")}
    form["ctl00$ctl07$simpleForm$LaegemiddelBox"] = term
    form["ctl00$ctl07$simpleForm$SearchButton"] = "Søg"
    return session.post(BASE, data=form, timeout=60).text


def grid_rows(page):
    """Join the two halves of the result grid (mgr_0_i: name/pack, mgr_1_i: firm/prices/icons)."""
    rows = {}
    for m in re.finditer(r'<tr[^>]*id="mgr_([01])_(\d+)"(.*?)</tr>', page, re.S):
        half, idx, body = m.group(1), int(m.group(2)), m.group(3)
        d = rows.setdefault(idx, {})
        if half == "0":
            v = re.search(r"mvnr(\d{6})", body)
            d["vnr"] = v.group(1) if v else ""
            cells = re.findall(r"<td>(.*?)</td>", body, re.S)
            d["cells0"] = [text_of(c) for c in cells]
        else:
            d["icons"] = [a for a in re.findall(r"alt='([^']*)'", body) if "tilskud" in a.lower()]
            d["cells1"] = [text_of(c) for c in re.findall(r"<td>(.*?)</td>", body, re.S)]
    return [rows[i] for i in sorted(rows)]


def detail(session, vnr):
    url = f"https://www.medicinpriser.dk/Default.aspx?id=15&vnr={vnr}"
    page = session.get(url, timeout=60).text
    lines = [l.strip() for l in text_of_lines(page)]
    def after(label):
        for i, l in enumerate(lines):
            if l == label and i + 1 < len(lines):
                return lines[i + 1]
        return ""
    return url, page, {k: after(lab) for k, lab in [
        ("name", "Lægemiddel"), ("strength", "Styrke"), ("pack", "Pakning"),
        ("firm", "Firma"), ("aup", "Pris pr. pakning"), ("aip", "Apotekets indkøbspris"),
        ("ddd_price", "Pris pr. defineret døgndosis")]}


def text_of_lines(page):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", page)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d|td|th|span)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in t.split("\n") if l.strip()]


def units(strength, pack):
    s = re.search(r"(\d+)\s*(?:E|enheder|IE)/ml", strength)
    p = re.search(r"(?:(\d+)\s*x\s*)?([\d,]+)\s*ml", pack)
    if not (s and p):
        return ""
    n = int(p.group(1)) if p.group(1) else 1
    return round(int(s.group(1)) * n * float(p.group(2).replace(",", ".")))


def num(x):
    m = re.search(r"([\d\.]+,\d+)", x)
    return m.group(1).replace(".", "").replace(",", ".") if m else ""


def main():
    today = dt.date.today().isoformat()
    s = requests.Session()
    s.headers["User-Agent"] = UA
    CAP.mkdir(exist_ok=True)
    out = []
    pages = {}
    for label, term, prefix, pack_req, firm in TARGETS:
        if term not in pages:
            pages[term] = search(s, term)
            (CAP / f"medicinpriser_search_{term}.html").write_text(pages[term])
            (CAP / f"medicinpriser_search_{term}.txt").write_text("\n".join(text_of_lines(pages[term])))
            time.sleep(1)
        rows = [r for r in grid_rows(pages[term])
                if r.get("cells0") and r["cells0"][0].startswith(prefix)]
        if not rows:
            out.append(dict(product=label, pack="no package found in medicinpriser.dk search",
                            units_per_pack="", aip_dkk="", aup_dkk="", tilskud_icon="",
                            tilskud_beregnes_af_dkk="",
                            varenummer="", fetched=today,
                            url=f"{BASE} (POST search '{term}')"))
            continue
        for r in rows:
            firm_cell = r["cells1"][1] if len(r.get("cells1", [])) > 1 else ""
            if firm and not firm_cell.startswith(firm):
                continue
            if "Udgået" in r.get("cells1", []):  # withdrawn package, no current price
                continue
            if pack_req and pack_req not in r["cells0"][2]:
                continue
            url, page, d = detail(s, r["vnr"])
            (CAP / f"medicinpriser_vnr{r['vnr']}_{label.replace(' ', '_')}.html").write_text(page)
            (CAP / f"medicinpriser_vnr{r['vnr']}_{label.replace(' ', '_')}.txt").write_text(
                "\n".join(text_of_lines(page)))
            out.append(dict(product=label, pack=d["pack"] + f" ({d['firm']})",
                            units_per_pack=units(d["strength"], d["pack"]),
                            aip_dkk=num(d["aip"]), aup_dkk=num(d["aup"]),
                            tilskud_beregnes_af_dkk=num(r["cells1"][2]) if len(r.get("cells1", [])) > 2 else "",
                            tilskud_icon="; ".join(r.get("icons", [])) or "none shown",
                            varenummer=r["vnr"], fetched=today, url=url))
            time.sleep(0.5)
    cols = ["product", "pack", "units_per_pack", "aip_dkk", "aup_dkk", "fetched", "url",
            "varenummer", "tilskud_icon", "tilskud_beregnes_af_dkk"]
    with open(HERE / "medicinpriser_prices.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
