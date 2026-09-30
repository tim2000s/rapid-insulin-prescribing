"""Sweep the NHS Wales InForm formularies for rapid-acting insulin entries.

For each health board prefix and each search term, this submits the InForm search,
opens every result, and saves the raw HTML plus an extracted text of the drug panel
(from the drug name down to the external-search links). Output goes to raw/inform/.
"""
import os, re, sys, html, json
import requests

sys.path.insert(0, os.path.dirname(__file__))
from inform_fetch import BASE, UA, hidden_fields, postback  # noqa: E402
from h2t import h2t  # noqa: E402

BOARDS = {
    "abbformulary": "Aneurin Bevan",
    "bcuformulary": "Betsi Cadwaladr",
    "cavformulary": "Cardiff and Vale",
    "cttformulary": "Cwm Taf Morgannwg",
    "hddformulary": "Hywel Dda",
    "powformulary": "Powys",
    "abmformulary": "Swansea Bay",
}
TERMS = ["fiasp", "lyumjev", "trurapi", "novorapid", "humalog", "admelog", "insulin aspart", "insulin lispro"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "inform")


def panel_text(page):
    t = h2t_str(page)
    lines = [l.strip() for l in t.splitlines() if l.strip() and not l.strip().startswith("[img: Expand")]
    try:
        a = next(i for i, l in enumerate(lines) if l == "Latest News") + 1
    except StopIteration:
        a = 0
    b = next((i for i, l in enumerate(lines) if l.startswith("Search External Sites") or l.startswith("Comments on the content")), len(lines))
    return "\n".join(lines[a:b])


def h2t_str(page):
    tmp = os.path.join(OUT, "_tmp.html")
    open(tmp, "w").write(page)
    return h2t(tmp)


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for prefix, board in BOARDS.items():
        url = BASE + prefix
        for term in TERMS:
            s = requests.Session()
            home = s.get(url, headers=UA, timeout=60).text
            res = postback(s, url, home, "", "", {"txtSearch": term, "btnSearch": "Search"})
            tag = f"{prefix}_{term.replace(' ', '_')}"
            open(os.path.join(OUT, f"{tag}_search.html"), "w").write(res)
            targets = re.findall(r"WebForm_PostBackOptions\(&quot;(dlDrugList\$ctl\d+\$formularyLinkButton)&quot;", res)
            labels = [re.sub(r"<[^>]+>", "", html.unescape(m)) for m in re.findall(r'formularyLinkButton"[^>]*>(.*?)</a>', res, flags=re.S)]
            if not targets:
                summary.append({"board": board, "term": term, "result": None, "text": panel_text(res)[:400]})
            for k, tgt in enumerate(targets):
                pg = postback(s, url, res, tgt, "")
                fn = os.path.join(OUT, f"{tag}_r{k}.html")
                open(fn, "w").write(pg)
                txt = panel_text(pg)
                open(fn[:-5] + ".txt", "w").write(txt)
                summary.append({"board": board, "term": term, "result": labels[k] if k < len(labels) else tgt, "file": os.path.basename(fn), "text": txt})
            print(board, term, len(targets), flush=True)
    json.dump(summary, open(os.path.join(OUT, "sweep_summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
