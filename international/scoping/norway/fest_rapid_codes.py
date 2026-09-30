"""Extract Norwegian varenummer for rapid-acting analogues (ATC A10AB04/05/06) from FEST 2.5.1.

FEST is the Norwegian Medical Products Agency product register (https://www.dmp.no, file
fest251.zip, refreshed twice monthly). Run with the path to fest251.zip; writes
fest_rapid_varenummer.csv. The file lists packages currently in FEST, so products removed
before the extract date may be missing.
"""
import csv, os, re, sys, zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))


def local(tag):
    return tag.rsplit("}", 1)[-1]


def main(zpath):
    z = zipfile.ZipFile(zpath)
    rows = []
    with z.open(z.namelist()[0]) as f:
        for ev, el in ET.iterparse(f, events=("end",)):
            if local(el.tag) != "Legemiddelpakning":
                continue
            d = {}
            for c in el.iter():
                n = local(c.tag)
                if n == "Atc" and "atc" not in d:
                    d["atc"] = c.get("V")
                elif n == "NavnFormStyrke":
                    d.setdefault("name", (c.text or "").strip())
                elif n == "Varenr":
                    d.setdefault("varenr", (c.text or "").strip())
                elif n == "Pakningsstr":
                    d.setdefault("pack_size", c.text)
                elif n == "EnhetPakning":
                    d.setdefault("pack_unit", c.get("V"))
                elif n == "Pakningstype":
                    d.setdefault("pack_type", c.get("DN"))
                elif n == "Mengde":
                    d.setdefault("amount", c.text)
                elif n == "DDD":
                    d.setdefault("ddd", f"{c.get('V')} {c.get('U')}")
                elif n == "Statistikkfaktor":
                    d.setdefault("stat_factor", c.text)
                elif n == "Markedsforingsdato":
                    d.setdefault("mf_date", c.text)
            if (d.get("atc") or "").startswith(("A10AB04", "A10AB05", "A10AB06")):
                rows.append(d)
            el.clear()
    keys = ["atc", "varenr", "name", "pack_type", "pack_size", "pack_unit", "amount", "ddd", "stat_factor", "mf_date"]
    with open(os.path.join(HERE, "fest_rapid_varenummer.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, keys, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r.get("atc", ""), r.get("name", ""))):
            w.writerow(r)
    print(len(rows))


if __name__ == "__main__":
    main(sys.argv[1])
