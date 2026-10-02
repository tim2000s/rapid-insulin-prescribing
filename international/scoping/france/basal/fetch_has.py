"""Capture the HAS Commission de la Transparence opinions used in route.csv.

Opinion pages are taken from the BDPM file HAS_LiensPageCT_bdpm.txt (captures/), which maps each
CT number to its has-sante.fr page. For each page the HTML and a plain-text version are saved, and
the linked opinion document ('...-avis-ct<NNNNN>') is downloaded and converted with pdftotext.
The SMR and ASMR wording quoted in route.csv comes from the BDPM files CIS_HAS_SMR_bdpm.txt and
CIS_HAS_ASMR_bdpm.txt (captures/), which reproduce the HAS wording; the PDFs are the primary record.
"""
import html
import re
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CAP = Path(__file__).parent / "captures"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
CT = {"CT-12822": "tresiba", "CT-16576": "tresiba", "CT-16983": "tresiba", "CT-17265": "tresiba",
      "CT-14452": "toujeo", "CT-16883": "lantus_toujeo", "CT-17811": "toujeo", "CT-18415": "toujeo",
      "CT-16059": "fiasp", "CT-18375": "fiasp", "CT-18474": "lyumjev", "CT-14408": "abasaglar",
      "CT-12976": "lantus"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read(), r.headers.get("Content-Type", "")


def text_of(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    return re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", h))).replace("\n \n", "\n")


def one(item):
    ct, name = item
    links = dict(l.split("\t") for l in open(CAP / "HAS_LiensPageCT_bdpm.txt").read().splitlines() if "\t" in l)
    url = links[ct]
    stem = f"has_{name}_{ct.lower()}"
    if (CAP / f"{stem}_avis.txt").exists():
        return ct, url, "cached"
    raw, _ = get(url)
    (CAP / f"{stem}_page.html").write_bytes(raw)
    page = raw.decode("utf-8", errors="replace")
    (CAP / f"{stem}_page.txt").write_text(text_of(page))
    num = ct.split("-")[1]
    m = re.search(r'href="(jcms/[^"]*avis-ct-?0*' + num + r'[^"]*)"', page, re.I)
    if not m:
        return ct, url, "no avis link"
    doc_url = "https://www.has-sante.fr/" + m.group(1)
    body, ctype = get(doc_url)
    if body[:4] == b"%PDF":
        (CAP / f"{stem}_avis.pdf").write_bytes(body)
        subprocess.run(["pdftotext", "-layout", str(CAP / f"{stem}_avis.pdf"), str(CAP / f"{stem}_avis.txt")])
        return ct, url, doc_url
    # the document page may itself link to the PDF
    p = body.decode("utf-8", errors="replace")
    # HAS answers with a tracking page whose meta refresh points at upload/docs/.../*.pdf
    m2 = re.search(r"(upload/docs/[^'\"]+\.pdf)", p, re.I)
    if m2:
        pdf_url = "https://www.has-sante.fr/" + m2.group(1)
        pdf, _ = get(pdf_url)
        (CAP / f"{stem}_avis.pdf").write_bytes(pdf)
        subprocess.run(["pdftotext", "-layout", str(CAP / f"{stem}_avis.pdf"), str(CAP / f"{stem}_avis.txt")])
        return ct, url, pdf_url
    return ct, url, "avis page without pdf: " + doc_url


if __name__ == "__main__":
    with ThreadPoolExecutor(3) as ex:
        for r in ex.map(one, CT.items()):
            print(*r)
