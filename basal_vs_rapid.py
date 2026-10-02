#!/usr/bin/env python3
"""
Do the places that use Lyumjev also use the newer long-acting insulins? Across UK areas, the share of
long-acting analogue units that is degludec (Tresiba) or glargine 300 units/ml (Toujeo), set against
the Lyumjev and ultra-rapid shares of rapid-acting analogue units.

Areas: English sub-ICB locations (stable through the 2026 ICB mergers) and ICBs, each sub-ICB location
assigned to its ICB in July 2026; Scottish and Welsh health boards; Northern Ireland as one area, as
its files carry no board. Windows: England August 2025 to July 2026; Scotland, Wales and Northern
Ireland July 2025 to June 2026, the latest twelve months common to all three. Rapid and long-acting
insulin come from the same pull, so they share the area definitions.

Long-acting classes by BNF code: degludec 0601012Z0; glargine 0601012V0, split by strength into
300 units/ml (Toujeo and generic) and 100 units/ml (Lantus, Abasaglar, Semglee, generic); detemir
0601012X0. The denominator is those four. NPH and premixed insulins are left out: they are not
alternatives in the same choice. Units are quantity x units per device, as in history.py.

Two things this cannot separate. Long-acting insulin in primary care is used mostly by people with
type 2 diabetes, rapid-acting mostly by people with type 1, so an area's case mix shapes the two
shares differently. And Tresiba costs more per unit than glargine 100, so a cost-led formulary can
lower both shares for reasons that have nothing to do with speed or clinical openness. The
association is ecological and unadjusted.

Writes output/basal/{areas.csv, SUMMARY.md}; caches under epd_cache/basal and international/cache/basal.
"""
import io
import json
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "international"))
import epd_source as E  # noqa: E402
import history as H  # noqa: E402

OUT = HERE / "output" / "basal"
EC = HERE / "epd_cache" / "basal"
IC = HERE / "international" / "cache" / "basal"
ENG_MONTHS = [f"EPD_SNOMED_{y}{m:02d}" for y, m in [(2025, m) for m in range(8, 13)] + [(2026, m) for m in range(1, 8)]]
DEV_MONTHS = [f"{y}{m:02d}" for y, m in [(2025, m) for m in range(7, 13)] + [(2026, m) for m in range(1, 7)]]
RNG = np.random.default_rng(20261002)
BOARDS = {"S08000015": "Ayrshire and Arran", "S08000016": "Borders", "S08000017": "Dumfries and Galloway",
          "S08000019": "Forth Valley", "S08000020": "Grampian", "S08000022": "Highland", "S08000024": "Lothian",
          "S08000025": "Orkney", "S08000026": "Shetland", "S08000028": "Western Isles", "S08000029": "Fife",
          "S08000030": "Tayside", "S08000031": "Greater Glasgow and Clyde", "S08000032": "Lanarkshire",
          "7A1": "Betsi Cadwaladr", "7A2": "Hywel Dda", "7A3": "Swansea Bay", "7A4": "Cardiff and Vale",
          "7A5": "Cwm Taf Morgannwg", "7A6": "Aneurin Bevan", "7A7": "Powys"}


def klass(code, name):
    if code.startswith("0601011"):
        k = H.klass(code)
        if k == "human soluble":
            return None
        if code.startswith("0601011L0BD"):
            return "Lyumjev"
        if code.startswith("0601011A0BC"):
            return "Fiasp"
        return "rapid other"
    if code.startswith("0601012Z0"):
        return "degludec"
    if code.startswith("0601012V0"):
        return "glargine 300" if "300" in name else "glargine 100"
    if code.startswith("0601012X0"):
        return "detemir"
    return None


# England -----------------------------------------------------------------------------------------
def pull_england(res):
    f = EC / f"{res}.json"
    if f.exists():
        return json.loads(f.read_text())
    q = (f"SELECT PCO_CODE AS pco, PCO_NAME AS pco_name, ICB_CODE AS icb, ICB_NAME AS icb_name, "
         f"BNF_PRESENTATION_CODE AS code, BNF_PRESENTATION_NAME AS name, "
         f"SUM(CAST(TOTAL_QUANTITY AS FLOAT64)) AS quantity "
         f"FROM `{res}` WHERE BNF_PRESENTATION_CODE LIKE '0601011%' OR BNF_PRESENTATION_CODE LIKE '0601012%' "
         f"GROUP BY PCO_CODE, PCO_NAME, ICB_CODE, ICB_NAME, BNF_PRESENTATION_CODE, BNF_PRESENTATION_NAME")
    rows = E.paged(q, res)
    for r in rows:
        r["month"] = res[-6:]
    EC.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows))
    return rows


def england():
    with ThreadPoolExecutor(7) as ex:
        d = pd.DataFrame([r for part in ex.map(pull_england, ENG_MONTHS) for r in part])
    d["quantity"] = pd.to_numeric(d.quantity)
    last = d[d.month == d.month.max()].groupby("pco")[["icb", "icb_name", "pco_name"]].first()
    d = d.drop(columns=["icb", "icb_name", "pco_name"]).join(last, on="pco")
    # Sub-ICB locations only (codes like 26A00); trusts, federations and other prescriber bodies are
    # small and are left out of the area analysis but kept in their ICB.
    d["sub_icb"] = d.pco.str.fullmatch(r"\d\d[A-Z]00|[A-Z0-9]{3}00") & d.pco_name.str.contains(" - ", na=False)
    return d


# Scotland ----------------------------------------------------------------------------------------
def pull_scotland(month, rid):
    import scotland as S
    f = IC / f"scotland_{month}.json"
    if f.exists():
        return json.loads(f.read_text())
    fields = {x["id"] for x in requests.get(f"{S.API}/datastore_search", params={"resource_id": rid, "limit": 0},
                                             timeout=300).json()["result"]["fields"]}
    hb = "HBT" if "HBT" in fields else "HBT2014"
    sql = (f'SELECT "{hb}" AS "HBT", "BNFItemCode" AS code, "BNFItemDescription" AS name, '
           f'SUM("PaidQuantity"::numeric) AS quantity FROM "{rid}" '
           f'WHERE "BNFItemCode" LIKE \'0601011%\' OR "BNFItemCode" LIKE \'0601012%\' GROUP BY 1, 2, 3')
    for attempt in range(5):
        try:
            r = requests.get(f"{S.API}/datastore_search_sql", params={"sql": sql}, timeout=600).json()
            if r.get("success"):
                rows = [dict(x, month=month) for x in r["result"]["records"]]
                f.write_text(json.dumps(rows))
                return rows
            err = r.get("error")
        except Exception as e:
            err = e
    raise RuntimeError(f"scotland {month}: {err}")


def scotland():
    import scotland as S
    res = S.resources()
    with ThreadPoolExecutor(4) as ex:
        rows = [r for part in ex.map(lambda m: pull_scotland(m, res[m]), DEV_MONTHS) for r in part]
    d = pd.DataFrame(rows)
    d["quantity"] = pd.to_numeric(d.quantity)
    d["area"] = d.HBT.map(BOARDS)
    return d.dropna(subset=["area"])


# Wales and Northern Ireland ----------------------------------------------------------------------
def pull_file(nation, month, url):
    import ni_wales as W
    f = IC / f"{nation}_{month}.csv"
    if f.exists():
        return pd.read_csv(f, dtype={"code": str, "area": str})
    raw = W.get(url)
    if nation == "wales":
        z = zipfile.ZipFile(io.BytesIO(raw))
        df = pd.read_csv(z.open(next(n for n in z.namelist() if n.lower().startswith("gpdata"))), dtype=str,
                         encoding="latin-1")
        area = df[W.col(df, r"HB")].astype(str)
    else:
        df = pd.read_csv(io.BytesIO(raw), dtype=str, encoding="latin-1")
        area = pd.Series("NI", index=df.index)
    code = W.col(df, r"BNF ?Code")
    keep = df[code].astype(str).str.startswith(("0601011", "0601012"))
    out = pd.DataFrame({"area": area[keep], "code": df.loc[keep, code].astype(str),
                        "name": df.loc[keep, W.col(df, r"AMP_NM", r"BNF ?Name", r"BNF ?Description")].astype(str),
                        "quantity": pd.to_numeric(df.loc[keep, W.col(df, r"Total ?Quantity", r"Quantity")],
                                                  errors="coerce")})
    out = out.groupby(["area", "code", "name"], as_index=False).quantity.sum().assign(month=month)
    out.to_csv(f, index=False)
    return out


def wales_ni():
    import ni_wales as W
    files = {"wales": W.wales_files(), "ni": W.ni_files()}
    jobs = [(n, m, files[n][m]) for n in files for m in DEV_MONTHS]
    missing = [(n, m) for n, m, _ in jobs if m not in files[n]]
    assert not missing, missing
    with ThreadPoolExecutor(7) as ex:
        parts = list(ex.map(lambda j: pull_file(*j), jobs))
    d = pd.concat(parts, ignore_index=True)
    d["area"] = d.area.map(lambda a: "Northern Ireland" if a == "NI" else BOARDS.get(a))
    return d.dropna(subset=["area"])


# Shares and association --------------------------------------------------------------------------
def shares(d, keys, names=None):
    d = d.copy()
    if names is not None:
        d["name"] = d.code.map(names).fillna(d.name)
    d["k"] = [klass(c, n) for c, n in zip(d.code, d.name)]
    d = d.dropna(subset=["k"])
    d["units"] = d.quantity * d.name.map(H.units_per_device)
    p = d.pivot_table(index=keys, columns="k", values="units", aggfunc="sum").fillna(0)
    rapid = p[["Lyumjev", "Fiasp", "rapid other"]].sum(axis=1)
    basal = p[["degludec", "glargine 300", "glargine 100", "detemir"]].sum(axis=1)
    return pd.DataFrame({"lyumjev_pct": p.Lyumjev / rapid * 100, "ultra_pct": (p.Lyumjev + p.Fiasp) / rapid * 100,
                         "degludec_pct": p.degludec / basal * 100, "glargine300_pct": p["glargine 300"] / basal * 100,
                         "newer_basal_pct": (p.degludec + p["glargine 300"]) / basal * 100,
                         "rapid_units_m": rapid / 1e6, "basal_units_m": basal / 1e6})


def spearman(x, y):
    r = x.corr(y, method="spearman")
    n = len(x)
    boots = []
    for _ in range(5000):
        i = RNG.integers(0, n, n)
        boots.append(pd.Series(x.values[i]).corr(pd.Series(y.values[i]), method="spearman"))
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    return r, lo, hi, n


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    IC.mkdir(parents=True, exist_ok=True)
    e = england()
    names = e.groupby("code").name.last()
    icb = shares(e, ["icb", "icb_name"]).reset_index()
    icb["area"] = icb.icb_name.map(E._clean_icb).str.replace("NHS ", "").str.replace(" Integrated Care Board", "")
    icb["nation"], icb["level"] = "England", "ICB"
    sub = shares(e[e.sub_icb], ["pco", "pco_name"]).reset_index()
    sub = sub[sub.rapid_units_m >= 1]
    sub["area"], sub["nation"], sub["level"] = sub.pco_name, "England", "sub-ICB location"
    s = shares(scotland(), ["area"], names).reset_index().assign(nation="Scotland", level="board")
    s = s[s.rapid_units_m >= 1]
    wn = wales_ni()
    w = shares(wn[wn.area != "Northern Ireland"], ["area"], names).reset_index().assign(nation="Wales", level="board")
    ni = shares(wn[wn.area == "Northern Ireland"], ["area"], names).reset_index().assign(nation="Northern Ireland",
                                                                                         level="nation")
    cols = ["nation", "level", "area", "lyumjev_pct", "ultra_pct", "degludec_pct", "glargine300_pct",
            "newer_basal_pct", "rapid_units_m", "basal_units_m"]
    a = pd.concat([icb[cols], sub[cols], s[cols], w[cols], ni[cols]], ignore_index=True)
    a.round(2).to_csv(OUT / "areas.csv", index=False)

    uk = a[a.level != "sub-ICB location"]
    sets = [("England ICBs", a[a.level == "ICB"]), ("England sub-ICB locations", a[a.level == "sub-ICB location"]),
            ("Scottish boards", a[a.nation == "Scotland"]), ("Welsh boards", a[a.nation == "Wales"]),
            ("UK: ICBs, boards and Northern Ireland", uk)]
    L = ["# Newer long-acting insulins against Lyumjev and ultra-rapid use: generated summary\n",
         "Generated by `basal_vs_rapid.py`; definitions, windows and caveats in its docstring. Newer basal is "
         "degludec plus glargine 300 units/ml as a share of long-acting analogue units.\n",
         "## Spearman correlation across areas (bootstrap 95% interval)\n",
         "| areas | n | newer basal vs Lyumjev | newer basal vs ultra-rapid | degludec vs Lyumjev | "
         "glargine 300 vs Lyumjev |", "|---|---|---|---|---|---|"]
    fmt = lambda t: f"{t[0]:.2f} ({t[1]:.2f} to {t[2]:.2f})"
    for label, g in sets:
        L.append(f"| {label} | {len(g)} | {fmt(spearman(g.newer_basal_pct, g.lyumjev_pct))} | "
                 f"{fmt(spearman(g.newer_basal_pct, g.ultra_pct))} | {fmt(spearman(g.degludec_pct, g.lyumjev_pct))} | "
                 f"{fmt(spearman(g.glargine300_pct, g.lyumjev_pct))} |")
    L += ["", "## Nations\n", "| nation | Lyumjev % | ultra-rapid % | degludec % | glargine 300 % | newer basal % |",
          "|---|---|---|---|---|---|"]
    nat = []
    for n, d in (("England", e), ("Scotland", scotland()), ("Wales", wn[wn.area != "Northern Ireland"]),
                 ("Northern Ireland", wn[wn.area == "Northern Ireland"])):
        r = shares(d.assign(nation=n), ["nation"], names).iloc[0]
        nat.append(r)
        L.append(f"| {n} | {r.lyumjev_pct:.1f} | {r.ultra_pct:.1f} | {r.degludec_pct:.1f} | {r.glargine300_pct:.1f} | "
                 f"{r.newer_basal_pct:.1f} |")
    L += ["", "## UK areas by Lyumjev share: lowest and highest ten\n",
          "| area | nation | Lyumjev % | ultra-rapid % | degludec % | glargine 300 % | newer basal % |",
          "|---|---|---|---|---|---|---|"]
    srt = uk.sort_values("lyumjev_pct")
    for _, r in pd.concat([srt.head(10), srt.tail(10)]).iterrows():
        L.append(f"| {r.area} | {r.nation} | {r.lyumjev_pct:.1f} | {r.ultra_pct:.1f} | {r.degludec_pct:.1f} | "
                 f"{r.glargine300_pct:.1f} | {r.newer_basal_pct:.1f} |")
    q = pd.qcut(uk.lyumjev_pct, 4, labels=["lowest quarter", "second", "third", "highest quarter"])
    L += ["", "## UK areas grouped by Lyumjev share\n", "| Lyumjev quarter | areas | median Lyumjev % | "
          "median newer basal % | median degludec % |", "|---|---|---|---|---|"]
    for k, g in uk.groupby(q, observed=True):
        L.append(f"| {k} | {len(g)} | {g.lyumjev_pct.median():.1f} | {g.newer_basal_pct.median():.1f} | "
                 f"{g.degludec_pct.median():.1f} |")
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
