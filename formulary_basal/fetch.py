"""Fetch one URL with a browser User-Agent, save the raw body and a text version, and log the fetch.

Usage: python3 fetch.py <url> <short_area>_<what> [note]
Saves raw/<name>.html (or .pdf) and raw/<name>.txt, and appends url, saved_as, status, note
to fetch_log.tsv, from which access_log_part1.csv is built.
"""
import os, sys, subprocess, requests
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from h2t_basal import h2t  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}


def main():
    url, name = sys.argv[1], sys.argv[2]
    note = sys.argv[3] if len(sys.argv) > 3 else ""
    try:
        r = requests.get(url, headers=UA, timeout=60, allow_redirects=True)
        status = str(r.status_code)
        pdf = r.content[:4] == b"%PDF"
        ext = "pdf" if pdf else "html"
        path = os.path.join(HERE, "raw", f"{name}.{ext}")
        open(path, "wb").write(r.content)
        txt = os.path.join(HERE, "raw", f"{name}.txt")
        if pdf:
            subprocess.run(["pdftotext", "-layout", path, txt], check=False)
        else:
            open(txt, "w").write(h2t(path))
        saved = f"raw/{name}.{ext}; raw/{name}.txt"
        if r.url != url:
            note = (note + f" (redirected to {r.url})").strip()
    except Exception as e:  # network failure is logged, not raised
        status, saved, note = "error", "", (note + f" {type(e).__name__}: {e}").strip()
    with open(os.path.join(HERE, "fetch_log.tsv"), "a") as f:
        f.write("\t".join([url, saved, status, note.replace("\t", " ")]) + "\n")
    print(status, saved, len(open(os.path.join(HERE, "raw", f"{name}.txt")).read()) if saved else "")


if __name__ == "__main__":
    main()
