"""Check every quote in build_lilly_role.ROWS against the capture it cites.

A capture is captures/<name>.txt, .html, .json, .pdf-derived .txt, or a path relative to this
directory. Text is compared after normalising whitespace, HTML entities, zero-width characters
and typographic quotes, because page converters differ on these and none of them changes the
wording. Exit status is non-zero if any quote is not found.
"""
import html
import pathlib
import re
import sys

from build_lilly_role import ROWS

HERE = pathlib.Path(__file__).parent


def norm(s: str) -> str:
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    s = html.unescape(s)
    s = s.replace("\\u003c", "<").replace("\\u003e", ">")
    s = re.sub(r"[​‌‍﻿­]", "", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("\xa0", " ")
    return re.sub(r"\s+", " ", s)


def sources(cap: str):
    if "/" in cap:
        yield HERE / cap
        return
    for ext in (".txt", ".html", ".json", ".js"):
        p = HERE / "captures" / f"{cap}{ext}"
        if p.exists():
            yield p


def main() -> int:
    ok = bad = skipped = 0
    for topic, jur, _finding, quote, _date, _url, cap in ROWS:
        paths = list(sources(cap))
        if not paths:
            print(f"MISSING CAPTURE  {cap}")
            bad += 1
            continue
        if not quote:
            skipped += 1
            continue
        q = norm(quote)
        found = any(q in norm(p.read_text(errors="ignore")) for p in paths)
        if found:
            ok += 1
        else:
            bad += 1
            print(f"NOT FOUND  [{topic} / {jur}] {cap}: {quote[:90]}")
    print(f"{ok} quotes verified, {bad} failed, {skipped} rows without a quote (absences)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
