"""Convert the article markdown to WordPress block HTML (headings, paragraphs, figures, rule, numbered
lists). An optional third argument names a sources file (SOURCES.md), which is appended under a
"Sources" heading as a numbered list, so the list lives in one file and the article and the preprint
both take it from there.

    python3 md_to_wordpress.py article.md article-wordpress.html SOURCES.md

The output is the post body only: everything up to the first horizontal rule (title and preamble) is
left out, since WordPress holds the title, and the published post carries neither. Image file names
are replaced by their uploaded media URLs from wordpress_media.json beside the script.
"""
import html, json, re, sys
from pathlib import Path

src = Path(sys.argv[1]); out = Path(sys.argv[2])
text = src.read_text()
text = text.split("\n---\n", 1)[1]                      # body starts after the title and preamble
media = json.loads((Path(__file__).parent / "wordpress_media.json").read_text())
if len(sys.argv) > 3:
    srcs = Path(sys.argv[3]).read_text().split("\n", 2)[2]   # drop the file's own heading
    text = text.rstrip() + "\n\n## Sources\n\n" + srcs.strip() + "\n"
blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

def inline(t):
    t = html.escape(" ".join(t.split()), quote=False)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"(?<![\"=>])(https?://[^\s<]+[^\s<.,)])", r'<a href="\1">\1</a>', t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    return t

parts = []
for b in blocks:
    if b.startswith("# "):
        parts.append(f'<!-- wp:heading {{"level":1}} -->\n<h1 class="wp-block-heading">{inline(b[2:])}</h1>\n<!-- /wp:heading -->')
        parts.append('<!-- wp:paragraph -->\n<p><em>Tim Street | Diabettech | October 2026</em></p>\n<!-- /wp:paragraph -->')
    elif b.startswith("### "):
        parts.append(f'<!-- wp:heading {{"level":3}} -->\n<h3 class="wp-block-heading">{inline(b[4:])}</h3>\n<!-- /wp:heading -->')
    elif b.startswith("## "):
        parts.append(f'<!-- wp:heading -->\n<h2 class="wp-block-heading">{inline(b[3:])}</h2>\n<!-- /wp:heading -->')
    elif b == "---":
        parts.append('<!-- wp:separator -->\n<hr class="wp-block-separator has-alpha-channel-opacity"/>\n<!-- /wp:separator -->')
    elif (m := re.fullmatch(r"!\[(.*)\]\((.*)\)", b, flags=re.S)):
        cap, img = inline(m.group(1)), media.get(m.group(2), m.group(2))
        parts.append(f'<!-- wp:image {{"sizeSlug":"large"}} -->\n<figure class="wp-block-image size-large"><img src="{img}" alt="{html.escape(" ".join(m.group(1).split()))}"/><figcaption class="wp-element-caption">{cap}</figcaption></figure>\n<!-- /wp:image -->')
    elif re.match(r"\d+\. ", b):
        items = re.split(r"\n(?=\d+\. )", b)
        lis = "".join(f'<!-- wp:list-item -->\n<li>{inline(re.sub(r"^\d+\. ", "", i))}</li>\n<!-- /wp:list-item -->\n'
                      for i in items)
        parts.append(f'<!-- wp:list {{"ordered":true}} -->\n<ol class="wp-block-list">\n{lis}</ol>\n<!-- /wp:list -->')
    else:
        parts.append(f"<!-- wp:paragraph -->\n<p>{inline(b)}</p>\n<!-- /wp:paragraph -->")
out.write_text("\n\n".join(parts) + "\n")
print(f"{len(parts)} blocks -> {out}")
