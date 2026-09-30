"""Convert a saved HTML page to plain text (script and style removed) for reading and archiving."""
import re, html, sys
def h2t(path):
    t = open(path, errors="replace").read()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S | re.I)
    # Keep status markers that some formulary platforms carry only in tooltip attributes.
    t = re.sub(r'<[^>]*data-tooltip="([^"]*)"[^>]*>', lambda m: " [" + m.group(1) + "] ", t)
    t = re.sub(r'<img[^>]*(?:alt|title)="([^"]+)"[^>]*>', lambda m: " [img: " + m.group(1) + "] ", t)
    t = re.sub(r"<br\s*/?>|</p>|</li>|</tr>|</h\d>|</div>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t
if __name__ == "__main__":
    for p in sys.argv[1:]:
        out = re.sub(r"\.html?$", "", p) + ".txt"
        open(out, "w").write(h2t(p))
        print(out)
