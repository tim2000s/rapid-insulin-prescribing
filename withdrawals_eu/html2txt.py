"""Convert captured HTML pages to plain text beside them, so quoted wording can be checked by grep."""
import re, html, sys, pathlib
for p in sys.argv[1:]:
    t = pathlib.Path(p).read_text(errors="ignore")
    t = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<(br|p|div|li|h\d|tr)\b[^>]*>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    pathlib.Path(p).with_suffix(".txt").write_text(t)
