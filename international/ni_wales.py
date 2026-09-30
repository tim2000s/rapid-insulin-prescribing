#!/usr/bin/env python3
"""
Northern Ireland and Wales GP prescribing, filtered to BNF 0601011 (short-acting insulins).

Northern Ireland: Business Services Organisation "GP Prescribing Data", one CSV per month from
2013 on the Open Data NI portal, by practice, with BNF code and AMP name. Wales: NHS Wales Shared
Services Partnership "General Practice Prescribing Data Extract", one zip per month, retained only
for the current and two previous financial years, by health board and practice. Both code items
by BNF presentation and count quantity in devices, as in England (checked: Fiasp Penfill comes to
5.66 pounds per unit of quantity in both, the price of one cartridge).

Each file is about 60 MB and is downloaded, filtered and discarded. Column names differ between
years, so the columns are found by pattern. Writes international/cache/{ni,wales}/<month>.csv and
international/output/{ni,wales}_by_presentation.csv (month x area x BNF code; area is the health
board in Wales and "NI" in Northern Ireland, whose files carry no board).
"""
import io
import re
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (research; rapid-insulin-prescribing)"}
NI_PAGE = "https://www.opendatani.gov.uk/@business-services-organisation/gp-prescribing-data"
WALES_INDEX = ("https://nwssp.nhs.wales/ourservices/primary-care-services/primary-care-services-documents/"
               "general-practice-prescribing-data-extract-docs/")
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})


def month_from(text):
    t = text.lower()
    y = re.search(r"(20\d\d)", t)
    m = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december|"
                  r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)", t)
    return f"{y.group(1)}{MONTHS[m.group(1)]:02d}" if y and m else None


def get(url):
    for attempt in range(5):
        try:
            r = requests.get(url, headers=UA, timeout=900)
            r.raise_for_status()
            return r.content
        except Exception as e:
            last = e
    raise RuntimeError(f"{url}: {last}")


def col(df, *patterns):
    for p in patterns:
        for c in df.columns:
            if re.fullmatch(p, c.strip(), flags=re.I):
                return c
    raise KeyError(f"{patterns} not in {list(df.columns)}")


def tidy(df, month, area):
    code = col(df, r"BNF ?Code")
    df = df[df[code].astype(str).str.startswith("0601011")]
    out = pd.DataFrame({
        "month": month, "area": area if isinstance(area, str) else df[area].astype(str),
        "code": df[code].astype(str),
        "name": df[col(df, r"AMP_NM", r"BNF ?Name", r"BNF ?Description")].astype(str),
        "items": pd.to_numeric(df[col(df, r"Total ?Items", r"Items")], errors="coerce"),
        "quantity": pd.to_numeric(df[col(df, r"Total ?Quantity", r"Quantity")], errors="coerce"),
        "cost": pd.to_numeric(df[col(df, r"Actual ?Cost.*", r"ActCost", r"Gross ?Cost.*")], errors="coerce")})
    return out.groupby(["month", "area", "code", "name"], as_index=False)[["items", "quantity", "cost"]].sum()


def ni_files():
    t = get(NI_PAGE).decode("utf-8", "replace")
    urls = sorted(set(re.findall(r"https?://[^\"\s<>]+?\.csv", t)))
    out = {}
    for u in urls:
        m = month_from(u.rsplit("/", 1)[-1])
        if m:
            out.setdefault(m, u)
    return out


def wales_files():
    t = get(WALES_INDEX).decode("utf-8", "replace")
    urls = sorted(set(re.findall(r'href="(https://nwssp\.nhs\.wales/[^"]*gp-data-extract-[^"/]+/)"', t)))
    # Parse only the final slug: "primary" in the path would otherwise read as March.
    return {month_from(u.rstrip("/").rsplit("/", 1)[-1]): u for u in urls
            if month_from(u.rstrip("/").rsplit("/", 1)[-1])}


def job(nation, month, url):
    f = HERE / "cache" / nation / f"{month}.csv"
    if f.exists():
        return nation, month, None
    raw = get(url)
    if nation == "wales":
        z = zipfile.ZipFile(io.BytesIO(raw))
        name = next(n for n in z.namelist() if n.lower().startswith("gpdata"))
        df = pd.read_csv(z.open(name), dtype=str, encoding="latin-1")
        out = tidy(df, month, col(df, r"HB"))
    else:
        df = pd.read_csv(io.BytesIO(raw), dtype=str, encoding="latin-1")
        out = tidy(df, month, "NI")
    out.to_csv(f, index=False)
    return nation, month, len(out)


def main():
    todo = []
    for nation, files in (("ni", ni_files()), ("wales", wales_files())):
        (HERE / "cache" / nation).mkdir(parents=True, exist_ok=True)
        print(f"{nation}: {len(files)} months, {min(files)} to {max(files)}")
        todo += [(nation, m, u) for m, u in files.items()]
    with ThreadPoolExecutor(7) as ex:
        for nation, m, n in ex.map(lambda a: job(*a), todo):
            if n is not None:
                print(f"  {nation} {m} {n} rows", flush=True)
    for nation in ("ni", "wales"):
        df = pd.concat([pd.read_csv(f, dtype={"month": str, "area": str}) for f in
                        sorted((HERE / "cache" / nation).glob("*.csv"))], ignore_index=True)
        df.to_csv(HERE / "output" / f"{nation}_by_presentation.csv", index=False)
        print(f"{nation}: {len(df):,} rows")


if __name__ == "__main__":
    sys.exit(main())
