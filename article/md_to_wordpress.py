"""Convert the article markdown to WordPress block HTML (headings, paragraphs, figures, rule)."""
import html, re, sys
from pathlib import Path

src = Path(sys.argv[1]); out = Path(sys.argv[2])
text = src.read_text()
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
        cap, img = inline(m.group(1)), m.group(2)
        parts.append(f'<!-- wp:image {{"sizeSlug":"large"}} -->\n<figure class="wp-block-image size-large"><img src="{img}" alt="{html.escape(" ".join(m.group(1).split()))}"/><figcaption class="wp-element-caption">{cap}</figcaption></figure>\n<!-- /wp:image -->')
    else:
        parts.append(f"<!-- wp:paragraph -->\n<p>{inline(b)}</p>\n<!-- /wp:paragraph -->")
out.write_text("\n\n".join(parts) + "\n")
print(f"{len(parts)} blocks -> {out}")
