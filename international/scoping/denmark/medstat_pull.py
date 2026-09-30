"""Pull medstat.dk package-level (varenummer) annual sales for rapid-acting analogues.

Source: Sundhedsdatastyrelsen, medstat.dk bulk download (https://medstat.dk/en/download).
Files are addressed by base64 of the filename. Each YYYY_product_name_data.txt is filtered
to ATC A10AB04/05/06 and written to rapid_packages_by_year.csv; product_name_text.txt is
filtered to the same ATC codes (Danish-language rows) for the package lookup.
"""
import base64, csv, io, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/126"}
ATC = ("A10AB04", "A10AB05", "A10AB06")
YEARS = range(2015, 2026)
COLS = ["atc", "year", "sector", "pkg", "a1_packages_k", "a1_volume_k", "a1_turnover_kdkk",
        "a2_packages_k", "a2_packages_reimb_k", "a2_volume_k", "a2_turnover_kdkk",
        "a2_reimb_kdkk", "a3_packages_k", "a3_volume_k"]


def get(name):
    url = "https://medstat.dk/en/download/file/" + base64.b64encode(name.encode()).decode()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read().decode("utf-8", errors="replace")


def main():
    txt = get("product_name_text.txt")
    lookup = [l.split(";") for l in txt.splitlines() if l.startswith(ATC)]
    lookup = [r for r in lookup if len(r) > 14 and r[14] == "0"]  # Danish rows
    with open(os.path.join(HERE, "rapid_package_lookup.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["atc", "pkg", "product", "holder", "form", "strength", "pack_size",
                    "status_end_2025", "dispensing", "change", "volume_unit", "note",
                    "reimbursement", "subst_group"])
        for r in lookup:
            w.writerow(r[:14])
    rows = []
    for y in YEARS:
        for l in get(f"{y}_product_name_data.txt").splitlines():
            if l.startswith(ATC):
                rows.append(l.rstrip(";").split(";")[:14])
        print(y, len(rows), file=sys.stderr)
    with open(os.path.join(HERE, "rapid_packages_by_year.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow(r + [""] * (14 - len(r)))


if __name__ == "__main__":
    main()
