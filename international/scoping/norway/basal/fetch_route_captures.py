"""Re-download the sources behind route.csv and prices.csv into captures/.

Each web page or PDF is saved raw, with a plain-text copy beside it (.txt). PDFs are converted with
pdftotext when it is on PATH, otherwise with pypdf. Three sources are not single files and are
rebuilt rather than copied:

- FEST 2.5.1 (the Norwegian prescribing and reimbursement register, about 14 MB zipped) is
  downloaded to a temporary directory and only the A10A reimbursement groups, the vilkår they cite
  and the relevant insulin packs are written out, since the full XML is 118 MB.
- Nye Metoder and Sykehusinnkjøp have no server-side search page. Their sites query an Optimizely
  Graph endpoint with a public key published in the page source, and the same queries are run here.
- The Sykehusinnkjøp basis-drug agreement list is an .xlsx; its text copy holds the A10A rows only.

The DMP completed-assessments page carries its table as embedded JSON arrays; the text copy is
that table, one row per line.

Pages change: the captures in the repository were taken on 2026-10-02 and a re-run will reflect
the sites on the day it is run. Run with: python3 fetch_route_captures.py
"""
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(HERE, "captures")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
FK = "https://www.felleskatalogen.no/medisin/"
SLV = "https://legemiddelverket.no/Documents/Offentlig-finansiering-og-pris/Metodevurderinger/"
HD = ("https://www.helsedirektoratet.no/retningslinjer/diabetes/"
      "behandling-med-blodsukkersenkende-legemidler-ved-diabetes/")
GRAPH = "https://cg.optimizely.com/content/v2?auth=FOssxJD0F5jW1TW3VRuqxRkuLlAulQIpUCXRESLCOaCvrZEt"
FEST_URL = ("https://www.dmp.no/globalassets/documents/om-oss/distribusjon-av-legemiddeldata/"
            "fest/festfiler/fest251.zip")
SI_XLSX = ("https://www.sykehusinnkjop.no/492829/siteassets/avtaledokumenter/avtaler-legemidler/"
           "basislegemidler/alle-basis.xlsx")
DMP_LIST = ("https://www.dmp.no/offentlig-finansiering/metodevurdering-av-medisinske-produkter/"
            "metodevurdering-av-legemidler/fullforte-metodevurderinger-for-legemidler")

PAGES = [
    (FK + "tresiba-flextouch-tresiba-penfill-novo-nordisk-589607", "fk_tresiba.html"),
    (FK + "toujeo-sanofi-aventis-596100", "fk_toujeo.html"),
    (FK + "lantus-sanofi-aventis-560832", "fk_lantus.html"),
    (FK + "levemir-flexpen-levemir-penfill-novo-nordisk-560927", "fk_levemir.html"),
    (FK + "fiasp-fiasp-flextouch-fiasp-penfill-fiasp-pumpcart-novo-nordisk-640799", "fk_fiasp.html"),
    (FK + "novorapid-novorapid-flexpen-novorapid-penfill-novorapid-pumpcart-novo-nordisk-562204",
     "fk_novorapid.html"),
    (FK + "humalog-lilly-559829", "fk_humalog.html"),
    (FK + "lyumjev-lilly-686975", "fk_lyumjev.html"),
    (FK + "substansregister/insulin-glargin", "fk_substans_insulin_glargin.html"),
    (FK + "sok?sokord=abasaglar", "fk_search_abasaglar.html"),
    (FK + "sok?sokord=semglee", "fk_search_semglee.html"),
    (FK + "utgatte-preparater/2025", "fk_utgatte_preparater_2025.html"),
    (FK + "endret-navn/2024", "fk_endret_navn_2024.html"),
    ("https://www.nyemetoder.no/innforing-av-nye-metoder/beslutning/", "nyemetoder_beslutning.html"),
    ("https://www.nyemetoder.no/metoder/kontinuerlig-glukosemaling-og-flash-glukosemaling-indikasjon-ii/",
     "nyemetoder_ID2023_075.html"),
    (HD + "insulinbehandling-og-behandlingsmal-ved-diabetes-type-1",
     "hdir_diabetes_insulinbehandling_type1.html"),
    (HD + "blodsukkersenkende-behandling-og-behandlingsmal-ved-diabetes-type-2",
     "hdir_diabetes_blodsukkersenkende_type2.html"),
]

PDFS = [
    (SLV + "T/Tresiba_Diabetes1_2015.pdf", "dmp_Tresiba_Diabetes1_2015.pdf"),
    (SLV + "T/Tresiba_T1D_2016.pdf", "dmp_Tresiba_T1D_2016.pdf"),
    (SLV + "T/Tresiba_T2DM_2019.pdf", "dmp_Tresiba_T2DM_2019.pdf"),
    (SLV + "T/Toujeo_T1DM_2015.pdf", "dmp_Toujeo_T1DM_2015.pdf"),
    (SLV + "T/Toujeo_T2D_2017.pdf", "dmp_Toujeo_T2D_2017.pdf"),
    (SLV + "F/Fiasp_diabetes-type-1-og-2_2017.pdf", "dmp_Fiasp_diabetes-type-1-og-2_2017.pdf"),
    (SLV + "L/Lyumjev_DM_2021.pdf", "dmp_Lyumjev_DM_2021.pdf"),
    (SLV + "I/Insulin-Glargin-100-E-ml_Diabetes_Fjerning-av-refusjonsvilkar_2023.pdf",
     "dmp_Insulin-Glargin-100_Fjerning-av-refusjonsvilkar_2023.pdf"),
    ("https://www.dmp.no/globalassets/documents/offentlig-finansiering-og-pris/metodevurderinger/i/"
     "insulin_diabetes_2026_-endring-av-refusjonsvilkar.pdf",
     "dmp_insulin_diabetes_2026_endring-av-refusjonsvilkar.pdf"),
    (SLV + "L/Lantus_diabetes_type_I_2009.pdf", "dmp_Lantus_diabetes_type_I_2009.pdf"),
    (SLV + "L/Lantus_diabtetes2_avslag_2012.pdf", "dmp_Lantus_diabetes2_avslag_2012.pdf"),
    (SLV + "L/Levimir_diabetes_type_I_2008.pdf", "dmp_Levemir_diabetes_type_I_2008.pdf"),
    (SLV + "L/Levemir_diabetes_type_II_2010.pdf", "dmp_Levemir_diabetes_type_II_2010.pdf"),
]

BRANDS = r"Tresiba|Toujeo|Lantus|Abasaglar|Semglee|Levemir|Fiasp|NovoRapid|Humalog|Lyumjev|glargin"


def get(url, data=None, headers=None):
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def html_to_text(raw):
    t = raw.decode("utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("​", "")
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t)


def pdf_to_text(path, out):
    if shutil.which("pdftotext"):
        subprocess.run(["pdftotext", path, out], check=True)
        return
    from pypdf import PdfReader
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join((p.extract_text() or "") for p in PdfReader(path).pages))


def write(name, data, mode="wb"):
    with open(os.path.join(CAP, name), mode) as f:
        f.write(data)


def stem(name):
    return os.path.join(CAP, name.rsplit(".", 1)[0] + ".txt")


def fetch_pages():
    for url, name in PAGES:
        raw = get(url)
        write(name, raw)
        with open(stem(name), "w", encoding="utf-8") as f:
            f.write(html_to_text(raw))
        print("page", name, len(raw))


def fetch_pdfs():
    for url, name in PDFS:
        raw = get(url)
        write(name, raw)
        pdf_to_text(os.path.join(CAP, name), stem(name))
        print("pdf", name, len(raw))


def fetch_dmp_list():
    raw = get(DMP_LIST)
    write("dmp_fullforte_metodevurderinger_legemidler.html", raw)
    t = html.unescape(raw.decode("utf-8", errors="replace"))
    cols = []
    for m in re.finditer(r'\[("(?:[^"\\]|\\.)*"(?:,"(?:[^"\\]|\\.)*")+)\]', t):
        try:
            a = json.loads("[" + m.group(1) + "]")
        except ValueError:
            continue
        if len(a) > 500:
            cols.append(a)
    lines = [f"Table data embedded in {DMP_LIST}.",
             "Columns as embedded (unlabelled in source): preparat | virkestoff | indikasjon | (flag) | "
             "rapport-URL | år | finansiering | Nye metoder ID | (blank)"]
    lines += [" | ".join(x.split(";linkObject;")[0] for x in r) for r in zip(*cols)]
    with open(stem("dmp_fullforte_metodevurderinger_legemidler.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("dmp list rows", len(lines) - 2)


def fetch_fest():
    with tempfile.TemporaryDirectory() as td:
        zp = os.path.join(td, "fest251.zip")
        with open(zp, "wb") as f:
            f.write(get(FEST_URL))
        z = zipfile.ZipFile(zp)
        x = z.read(z.namelist()[0]).decode("utf-8-sig")
    stamp = re.search(r"<HentetDato>([^<]+)<", x).group(1)
    kr = x[x.find("<KatRefusjon>"):x.find("</KatRefusjon>")]
    ref = [m.group(0) for m in re.finditer(r"<OppfRefusjon>.*?</OppfRefusjon>", kr, re.S)
           if re.search(r'Atc V="A10A', m.group(0))]
    ids = set(re.findall(r"<RefVilkar>(ID_[^<]+)</RefVilkar>", "".join(ref)))
    kv = x[x.find("<KatVilkar>"):x.find("</KatVilkar>")]
    vil = [m.group(0) for m in re.finditer(r"<OppfVilkar>.*?</OppfVilkar>", kv, re.S)
           if any(i in m.group(0) for i in ids)]
    kp = x[x.find("<KatLegemiddelpakning>"):x.find("</KatLegemiddelpakning>")]
    pak = []
    for m in re.finditer(r"<OppfLegemiddelpakning>.*?</OppfLegemiddelpakning>", kp, re.S):
        b = m.group(0)
        name = re.search(r"<NavnFormStyrke>(.*?)<", b)
        if re.search(r'Atc V="A10A[BCE]', b) and name and re.search(BRANDS, name.group(1), re.I):
            pak.append(b)
    head = ('<?xml version="1.0" encoding="utf-8"?>\n'
            f"<!-- Extract from fest251.xml (HentetDato {stamp}) downloaded from {FEST_URL} -->\n")
    for name, blocks in [("fest251_a10a_refusjon_blocks", ref), ("fest251_a10a_vilkar", vil),
                         ("fest251_a10a_pakninger", pak)]:
        body = head + "<Extract>\n" + "\n".join(blocks) + "\n</Extract>\n"
        for ext in (".xml", ".txt"):
            write(name + ext, body, "w")
        print("fest", name, len(blocks))


def graph(query):
    body = json.dumps({"query": query}).encode()
    return json.loads(get(GRAPH, data=body, headers={"Content-Type": "application/json"}))


def fetch_graph_searches(day):
    nm = {"_note": "Optimizely Graph fulltext search of nyemetoder.no MethodPage; public key from the "
                   "nyemetoder.no page source"}
    for w in ["insulin", "degludek", "glargin", "aspart", "lispro", "detemir", "Tresiba", "Toujeo",
              "Fiasp", "Lyumjev", "Levemir", "Lantus", "NovoRapid", "Humalog", "semaglutid",
              "tirzepatid", "diabetes", "pembrolizumab"]:
        q = '{ MethodPage(where:{_fulltext:{match:"%s"}}, limit:100){ total items{ Name RelativePath } } }' % w
        nm[w] = graph(q)["data"]["MethodPage"]
    nm["_all_methods_total"] = graph("{ MethodPage(limit:0){ total } }")["data"]["MethodPage"]["total"]
    write(f"nyemetoder_graph_search_{day}.json", json.dumps(nm, ensure_ascii=False, indent=1), "w")
    lines = []
    for k, v in nm.items():
        if isinstance(v, dict):
            lines.append(f"{k}: total={v['total']} " + "; ".join(i["Name"] + " " + i["RelativePath"]
                                                              for i in v["items"]))
        else:
            lines.append(f"{k}: {v}")
    with open(stem(f"nyemetoder_graph_search_{day}.json"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    si = {"_note": "Optimizely Graph fulltext search restricted to Url startsWith "
                   "https://www.sykehusinnkjop.no; public key from the page source"}
    for w in ["insulin", "insulin anbefaling", "LIS-anbefaling insulin", "degludek", "glargin",
              "Fiasp", "Lyumjev", "Tresiba", "Toujeo"]:
        q = ('{ Content(where:{_fulltext:{match:"%s"}, Url:{startsWith:"https://www.sykehusinnkjop.no"}}, '
             'limit:100){ total items{ Name Url } } }' % w)
        si[w] = graph(q)["data"]["Content"]
    write(f"sykehusinnkjop_graph_search_{day}.json", json.dumps(si, ensure_ascii=False, indent=1), "w")
    lines = []
    for k, v in si.items():
        if isinstance(v, dict):
            lines.append(f"{k}: total={v['total']}")
            lines += ["  " + i["Url"] + " | " + i["Name"] for i in v["items"]]
        else:
            lines.append(f"{k}: {v}")
    with open(stem(f"sykehusinnkjop_graph_search_{day}.json"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("graph searches written")


def fetch_si_xlsx():
    import openpyxl
    name = "sykehusinnkjop_avtaleoversikt_basislegemidler.xlsx"
    write(name, get(SI_XLSX))
    wb = openpyxl.load_workbook(os.path.join(CAP, name), read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    out = [f"Source: {SI_XLSX} (Avtaleoversikt basislegemidler).",
           f"Sheet '{ws.title}', {len(rows)} rows. Header row and all rows with ATC A10A shown.",
           " | ".join(str(v) for v in rows[0])]
    out += [" | ".join("" if v is None else str(v) for v in r)
            for r in rows if r[8] and str(r[8]).startswith("A10A")]
    with open(stem(name), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("xlsx A10A rows", len(out) - 3)


def main():
    import datetime
    os.makedirs(CAP, exist_ok=True)
    day = datetime.date.today().isoformat()
    fetch_pages()
    fetch_pdfs()
    fetch_dmp_list()
    fetch_fest()
    fetch_graph_searches(day)
    fetch_si_xlsx()


if __name__ == "__main__":
    main()
