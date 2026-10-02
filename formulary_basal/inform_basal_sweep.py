"""Sweep the seven NHS Wales InForm formularies for long-acting insulin entries.

Reuses the postback helpers in ../formulary_devolved (inform_fetch.py, h2t.py), which were
written for the rapid-acting sweep. For each board and term it submits the InForm search,
opens every result and saves the raw HTML and the extracted drug panel to raw/inform/.
A summary of every search, including searches with no result, goes to sweep_summary.json.
"""
import os, re, sys, html, json
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "formulary_devolved"))
from inform_fetch import BASE, UA, postback  # noqa: E402
from inform_sweep import BOARDS, panel_text  # noqa: E402
import inform_sweep  # noqa: E402

TERMS = ["degludec", "tresiba", "toujeo", "glargine", "lantus", "abasaglar", "semglee", "detemir", "levemir"]
OUT = os.path.join(HERE, "raw", "inform")
inform_sweep.OUT = OUT  # panel_text writes its temporary file here


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for prefix, board in BOARDS.items():
        url = BASE + prefix
        for term in TERMS:
            s = requests.Session()
            home = s.get(url, headers=UA, timeout=60).text
            res = postback(s, url, home, "", "", {"txtSearch": term, "btnSearch": "Search"})
            tag = f"{prefix}_{term}"
            open(os.path.join(OUT, f"{tag}_search.html"), "w").write(res)
            targets = re.findall(r"WebForm_PostBackOptions\(&quot;(dlDrugList\$ctl\d+\$formularyLinkButton)&quot;", res)
            labels = [re.sub(r"<[^>]+>", "", html.unescape(m)).strip() for m in re.findall(r'formularyLinkButton"[^>]*>(.*?)</a>', res, flags=re.S)]
            if not targets:
                summary.append({"board": board, "prefix": prefix, "term": term, "result": None,
                                "file": f"{tag}_search.html", "text": panel_text(res)[:600]})
            for k, tgt in enumerate(targets):
                pg = postback(s, url, res, tgt, "")
                fn = os.path.join(OUT, f"{tag}_r{k}.html")
                open(fn, "w").write(pg)
                txt = panel_text(pg)
                open(fn[:-5] + ".txt", "w").write(txt)
                summary.append({"board": board, "prefix": prefix, "term": term,
                                "result": labels[k] if k < len(labels) else tgt,
                                "file": os.path.basename(fn), "text": txt})
            print(board, term, len(targets), flush=True)
    json.dump(summary, open(os.path.join(OUT, "sweep_summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
