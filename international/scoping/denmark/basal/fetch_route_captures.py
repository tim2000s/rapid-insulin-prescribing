"""Re-download the source captures cited in route.csv.

Each source is saved to captures/ under the file name used in route.csv, with a plain-text
copy alongside it (.txt): PDFs via pdftotext -layout (pypdf as fallback), HTML by stripping
tags. For laegemiddelstyrelsen.dk pages the text starts at the page's main-content anchor,
because the navigation menu otherwise fills the first two hundred lines.

The medicinpriser.dk captures need an ASP.NET form POST and are produced by
medicinpriser_prices.py, which this script calls at the end. Pages change: the DKMA
reimbursement lists are regenerated with a new "Sidste opdateringsdato", medicinpriser.dk
prices change every 14 days, and Medicinrådet's type 2 diabetes page moved documents to
"Tidligere versioner" during 2026, so a re-run can legitimately differ from the committed
captures. The Wayback snapshot is pinned to a timestamp and should not change.
"""
import html
import re
import shutil
import subprocess
import time
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HERE = Path(__file__).resolve().parent
CAP = HERE / "captures"
DK = "https://laegemiddelstyrelsen.dk"
MR = "https://filer.medicinraadet.dk/media/"

SOURCES = {
    # Lægemiddelstyrelsen: reimbursement lists, revurdering status and news
    DK + "/da/tilskud/generelle-tilskud/tilskudsberettigede-laegemidler/": "dkma_tilskudsberettigede_laegemidler.html",
    DK + "/ftp-upload/Recept_lm_klaus_til.pdf": "dkma_Recept_lm_klaus_til.pdf",
    DK + "/ftp-upload/recept_lm_gen_uklaus_til.pdf": "dkma_recept_lm_gen_uklaus_til.pdf",
    DK + "/da/tilskud/generelle-tilskud/revurdering/status/": "dkma_revurdering_status.html",
    DK + "/da/nyheder/2026/insulinanalogerne-toujeo-og-tresiba-faar-igen-generelt-tilskud/": "dkma_news_2026-04-24_toujeo_tresiba_generelt_tilskud.html",
    DK + "/da/nyheder/2022/tilskuddet-til-en-raekke-insuliner-aendres-langt-de-fleste-patienter-vil-fortsat-faa-tilskud/": "dkma_news_2022-03-17_tilskud_insuliner_aendres.html",
    DK + "/da/nyheder/2021/medicintilskudsnaevnet-er-nu-faerdige-med-sine-anbefalinger-til-tilskudsstatus-for-insuliner/": "dkma_news_2021-11-22_mtn_anbefalinger_insuliner.html",
    DK + "/da/nyheder/2021/hoering-over-medicintilskudsnaevnets-nye-forslag-til-tilskudsstatus-til-insuliner/": "dkma_news_2021-09-09_hoering_nye_forslag_insuliner.html",
    DK + "/da/nyheder/2019/hoering-om-medicintilskudsnaevnets-forslag-til-tilskudsstatus-for-insuliner/": "dkma_news_2019-12-12_hoering_forslag_insuliner.html",
    DK + "/da/nyheder/revurdering-af-laegemidlers-tilskud-nyheder-arkiv/medicintilskuddet-til-visse-laegemidler-mod-diabetes-aendres-den-11-november-2013/": "dkma_news_2013-06-11_diabetes_tilskud_aendres.html",
    # Lægemiddelstyrelsen decisions and Medicintilskudsnævnet recommendation (PDF via /media/<id>.ashx)
    DK + "/media/3425E9FAA59E4B2FA93DB1EEE09AB0A3.ashx": "dkma_afgoerelse_2026-04_toujeo.pdf",
    DK + "/media/D45289FC399844B18D55694B5B1AFB7E.ashx": "dkma_afgoerelse_2026-04_tresiba.pdf",
    DK + "/media/CBB8F9ECF6544995A7B5A706F34D07D6.ashx": "dkma_2022_oversigt_tilskudsstatus_insuliner_pr_2022-09-19.pdf",
    DK + "/media/454DEAE9D7E24736A036C7EF91A526AC.ashx": "dkma_2022_alfabetisk_oversigt_tilskudsstatus_insuliner.pdf",
    DK + "/media/06D7D6F56D7D4C6FA711989CF17DDBF8.ashx": "dkma_afgoerelse_2022_ny_tilskudsstatus_insuliner.pdf",
    DK + "/media/DD6905257B5540A397961DEE9B476777.ashx": "mtn_indstilling_2021-11-18_tilskudsstatus_insuliner.pdf",
    # Medicinrådet
    "https://medicinraadet.dk/anbefalinger-og-vejledninger/behandlingsvejledninger-og-laegemiddelrekommandationer/type-2-diabetes": "medicinraadet_type-2-diabetes_page.html",
    MR + "pbrn1wmg/medicinrådets-behandlingsvejledning-vedr-antidiabetika-til-type-2-diabetes-version-1-1.pdf": "medicinraadet_behandlingsvejledning_antidiabetika_T2D_v1-1.pdf",
    MR + "ocrfkabu/medicinradets-laegemiddelrek-vedr-antidiabetika-til-type-2-diabetes-vers-1-3.pdf": "medicinraadet_laegemiddelrek_antidiabetika_T2D_v1-3.pdf",
    MR + "iyznpc3c/opsummering-af-medicinradets-evidensgennemgang-vedr-antidiabetika-til-type-2-diabetes-vers-2-1.pdf": "medicinraadet_opsummering_evidensgennemgang_T2D_v2-1.pdf",
    MR + "ieohpomw/algoritme-farmakologisk-behandling-ved-type-2-diabetes-oktober-2026.pdf": "medicinraadet_algoritme_T2D_2026-10.pdf",
    "https://medicinraadet.dk/vejledning-til-primaersektor/primaersektor/basislisten": "medicinraadet_basislisten_page.html",
    MR + "qzipw2gh/basislisten-2026.pdf": "medicinraadet_basislisten_2026.pdf",
    "https://medicinraadet.dk/sog?q=insulin": "medicinraadet_search_insulin.html",
    # RADS (pre-2017), archived
    "https://web.archive.org/web/20170617114104/http://www.rads.dk:80/behandlingsvejledninger/stofskifte": "rads_wayback_2017_stofskifte.html",
    "https://web.archive.org/web/20170617114129/http://www.rads.dk:80/behandlingsvejledninger/tidligere-behandlingsvejledninger/stofskifte-arkiv": "rads_wayback_2017_stofskifte_arkiv.html",
    # Amgros site search, with a control term that does return results (rendered client-side)
    "https://amgros.dk/soegeresultater/?s=insulin": "amgros_search_insulin.html",
    "https://amgros.dk/soegeresultater/?s=adalimumab": "amgros_search_adalimumab.html",
    # Prescriber reference: Lyumjev, with Fiasp as a positive control
    "https://pro.medicin.dk/Search/Search/Search/lyumjev": "promedicin_search_lyumjev.html",
    "https://pro.medicin.dk/Search/Search/Search/fiasp": "promedicin_search_fiasp.html",
    # Dansk Endokrinologisk Selskab, national treatment guideline for type 1 diabetes
    "https://endocrinology.dk/nbv/diabetes-melitus/type-1-diabetes-mellitus/": "des_nbv_type1_diabetes.html",
}


def html_to_text(raw, main_anchor=True):
    t = raw
    if main_anchor:
        i = t.find('id="main-content"')
        if i > 0:
            t = t[i:]
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", "", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d|td|th|a)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\r\xa0]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def pdf_to_text(pdf, txt):
    if shutil.which("pdftotext"):
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)
    else:
        from pypdf import PdfReader
        txt.write_text("\n".join(p.extract_text() or "" for p in PdfReader(str(pdf)).pages))


def main():
    CAP.mkdir(exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = UA
    for url, name in SOURCES.items():
        dest = CAP / name
        try:
            r = s.get(url, timeout=120)
        except requests.RequestException as e:
            print(f"FAIL {name}: {e}")
            continue
        print(r.status_code, name, len(r.content))
        if r.status_code != 200:
            continue
        dest.write_bytes(r.content)
        txt = dest.with_suffix(".txt")
        if name.endswith(".pdf"):
            pdf_to_text(dest, txt)
        else:
            txt.write_text(html_to_text(r.content.decode("utf-8", "replace"),
                                        main_anchor="laegemiddelstyrelsen" in url))
        time.sleep(1)
    import medicinpriser_prices
    medicinpriser_prices.main()


if __name__ == "__main__":
    main()
