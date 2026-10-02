"""HTML to text for the basal sweep.

Wraps ../formulary_devolved/h2t.py and first rewrites single-quoted alt and title attributes
to double quotes. netFormulary writes its traffic-light images as <img ... alt='Green' />,
which the original converter's pattern (double quotes only) dropped, losing the status.
"""
import os, re, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "formulary_devolved"))
from h2t import h2t as _h2t  # noqa: E402


def h2t(path):
    t = open(path, errors="replace").read()
    t = re.sub(r"(\b(?:alt|title))='([^']*)'", lambda m: f'{m.group(1)}="{m.group(2)}"', t)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(t)
    out = _h2t(f.name)
    os.unlink(f.name)
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        out = re.sub(r"\.html?$", "", p) + ".txt"
        open(out, "w").write(h2t(p))
