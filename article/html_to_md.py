"""WordPress block HTML (the live post body) back to the article's markdown, so edits made in WordPress
can be taken into the master. Inverse of md_to_wordpress.convert for the block types it emits.

    python3 html_to_md.py published/live_<date>_body.html > body.md
"""
import html
import json
import re
import sys
import textwrap
from pathlib import Path

MEDIA = {v: k for k, v in json.loads((Path(__file__).parent / "wordpress_media.json").read_text()).items()}


def inline(t):
    t = re.sub(r'<a href="([^"]+)">([^<]+)</a>', lambda m: m.group(1) if m.group(1) == m.group(2) else
               f"[{m.group(2)}]({m.group(1)})", t)
    t = re.sub(r"<em>(.*?)</em>", r"*\1*", t)
    return html.unescape(t).strip()


def wrap(t):
    return "\n".join(textwrap.wrap(t, 100, break_long_words=False, break_on_hyphens=False))


def convert(src):
    out = []
    for m in re.finditer(r"<!-- wp:(\w+)[^>]*-->(.*?)<!-- /wp:\1 -->", src, flags=re.S):
        kind, body = m.group(1), m.group(2).strip()
        if kind == "paragraph":
            out.append(wrap(inline(re.sub(r"^<p>|</p>$", "", body))))
        elif kind == "heading":
            h = re.match(r"<h(\d)[^>]*>(.*)</h\d>", body, flags=re.S)
            out.append("#" * int(h.group(1)) + " " + inline(h.group(2)))
        elif kind == "separator":
            out.append("---")
        elif kind == "image":
            src_ = re.search(r'src="([^"]+)"', body).group(1)
            cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", body, flags=re.S).group(1)
            out.append(f"![{inline(cap)}]({MEDIA.get(src_, src_)})")
        else:
            raise ValueError(kind)
    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(convert(Path(sys.argv[1]).read_text()))
