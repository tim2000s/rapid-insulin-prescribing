#!/usr/bin/env python3
"""
Lyumjev's own formulary position against Lyumjev's own uptake, across UK areas.

formulary_uptake.py and formulary_uptake_uk.py test whether access to an ultra-rapid insulin (the less
restrictive of Fiasp and Lyumjev) goes with ultra-rapid uptake. This tests the narrower proposition
the article's narrative rests on: that areas restricting Lyumjev itself use less Lyumjev.

Exposure: Lyumjev's class in formulary_lyumjev_listing.csv, ranked open 0, specialist_or_criteria 1,
behind_another_insulin 2, not_listed 3 (the same documents and coding as the article's 5/8/12/13
breakdown; coded after the uptake figures were seen, so not blind).
Outcomes, twelve months (England August 2025 to July 2026; Scotland, Wales and Northern Ireland July
2025 to June 2026), units:
  lyumjev_pct           Lyumjev share of rapid-acting analogue units
  lyumjev_of_lispro_pct Lyumjev share of lispro (Lyumjev plus Humalog) units, which removes the
                        effect of an area's aspart/lispro mix on Lyumjev's overall share
A partial Spearman correlation of class with Lyumjev share, adjusting for the lispro share of
rapid-acting units (ranks residualised on the covariate's ranks), gives a second way to account for
mix. Intervals are bootstrap 95% over areas (10,000 resamples); p values by permutation (10,000).
Norfolk and Suffolk is excluded from the England set because only its Norfolk part was coded, as in
formulary_uptake.py; Lanarkshire's formulary could not be read.

Writes output/formulary/lyumjev_vs_lyumjev.csv and LYUMJEV_SUMMARY.md.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "international"))
from uk_compare import BOARDS  # noqa: E402

OUT = HERE / "output" / "formulary"
RANK = {"open": 0, "specialist_or_criteria": 1, "behind_another_insulin": 2, "not_listed": 3}
RNG = np.random.default_rng(20261004)
LYU, HUM = "0601011L0BD", "0601011L0BB"


def norm(s):
    return (s.replace("NHS ", "").replace(" Integrated Care Board", "").replace(",", "").replace(" And ", " and ")
            .lower().strip())


def england():
    u = pd.read_csv(HERE / "output" / "icb_ultrarapid_share_last12m.csv")
    u["key"] = u.icb.map(norm)
    u["lispro_pct"] = u.Lyumjev_share_pct + u.Humalog_share_pct
    u["lyumjev_of_lispro_pct"] = u.Lyumjev_share_pct / u.lispro_pct * 100
    return u.set_index("key")[["Lyumjev_share_pct", "lispro_pct", "lyumjev_of_lispro_pct"]].rename(
        columns={"Lyumjev_share_pct": "lyumjev_pct"})


def devolved():
    import history as H
    rows = {}
    for f, months in (("scotland", ("202507", "202606")), ("wales", ("202507", "202606")), ("ni", ("202507", "202606"))):
        d = pd.read_csv(HERE / "international" / "output" / f"{f}_by_presentation.csv", dtype={"month": str, "code": str, "area": str})
        d = d[(d.month >= months[0]) & (d.month <= months[1])]
        d = d[d.code.map(H.klass).isin(["ultra-rapid", "originator", "biosimilar", "generic analogue"])].copy()
        d["units"] = d.quantity * d.name.map(H.units_per_device)
        d["area"] = "Northern Ireland Formulary" if f == "ni" else d.area.map(lambda a: BOARDS.get(a, a))
        for a, g in d.groupby("area"):
            t = g.units.sum()
            ly = g[g.code.str.startswith(LYU)].units.sum()
            hu = g[g.code.str.startswith(HUM)].units.sum()
            rows[a] = dict(lyumjev_pct=ly / t * 100, lispro_pct=(ly + hu) / t * 100,
                           lyumjev_of_lispro_pct=ly / (ly + hu) * 100 if ly + hu else np.nan)
    return pd.DataFrame(rows).T


def ranks(s):
    return s.rank()


def partial(d, y, z):
    rx, ry, rz = ranks(d["rank"]), ranks(d[y]), ranks(d[z])
    res = lambda a: a - np.polyval(np.polyfit(rz, a, 1), rz)
    return np.corrcoef(res(rx), res(ry))[0, 1]


def stats(d, y, fn=None):
    f = fn or (lambda x: x["rank"].corr(x[y], method="spearman"))
    r = f(d)
    boots = []
    for _ in range(10000):
        s = d.sample(len(d), replace=True, random_state=RNG.integers(1 << 31))
        if s["rank"].nunique() > 1:
            boots.append(f(s))
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    perm = []
    for _ in range(10000):
        p_ = d.copy()
        p_["rank"] = RNG.permutation(p_["rank"].values)
        perm.append(f(p_))
    p = (np.sum(np.abs(perm) >= abs(r)) + 1) / (len(perm) + 1)
    return r, lo, hi, p


def main():
    warnings.filterwarnings("ignore", category=RuntimeWarning)   # constant ranks in some bootstrap draws
    lst = pd.read_csv(HERE / "formulary_lyumjev_listing.csv")
    lst = lst[lst.lyumjev_class.isin(RANK)]
    e, dv = england(), devolved()
    rows = []
    for _, r in lst.iterrows():
        if r.nation == "England":
            key = norm(r.area.replace(" (Norfolk and Waveney part)", ""))
            if r.area.startswith("Norfolk and Suffolk"):
                continue
            v = e.loc[key]
        else:
            v = dv.loc[r.area]
        rows.append(dict(nation=r.nation, area=r.area, lyumjev_class=r.lyumjev_class, rank=RANK[r.lyumjev_class],
                         **v.to_dict()))
    d = pd.DataFrame(rows)
    d.round(2).to_csv(OUT / "lyumjev_vs_lyumjev.csv", index=False)

    L = ["# Lyumjev's formulary position against Lyumjev's uptake: generated summary\n",
         "Generated by `lyumjev_formulary.py`; definitions and caveats in its docstring.\n",
         "## Median uptake by Lyumjev's formulary class\n",
         "| nation | class | areas | Lyumjev % of rapid-acting (median) | Lyumjev % of lispro (median) |",
         "|---|---|---|---|---|"]
    for (n, c), g in d.groupby(["nation", "lyumjev_class"], sort=False):
        L.append(f"| {n} | {c} | {len(g)} | {g.lyumjev_pct.median():.1f} | {g.lyumjev_of_lispro_pct.median():.1f} |")
    L += ["", "## Spearman correlation of restriction rank with uptake (bootstrap 95% interval; permutation p)\n",
          "| set | areas | with Lyumjev % | with Lyumjev % of lispro | with Lyumjev %, adjusted for lispro share |",
          "|---|---|---|---|---|"]
    fmt = lambda t: f"{t[0]:.2f} ({t[1]:.2f} to {t[2]:.2f}; p {'< 0.001' if t[3] < 0.001 else f'= {t[3]:.3f}'})"
    for label, g in (("England ICBs", d[d.nation == "England"]), ("Scottish boards", d[d.nation == "Scotland"]),
                     ("Welsh boards", d[d.nation == "Wales"]), ("UK, all areas", d)):
        g = g.dropna(subset=["lyumjev_of_lispro_pct"])
        L.append(f"| {label} | {len(g)} | {fmt(stats(g, 'lyumjev_pct'))} | {fmt(stats(g, 'lyumjev_of_lispro_pct'))} | "
                 f"{fmt(stats(g, 'lyumjev_pct', lambda x: partial(x, 'lyumjev_pct', 'lispro_pct')))} |")
    L += ["", "## Areas\n", "| nation | area | class | Lyumjev % | Lyumjev % of lispro | lispro % of rapid |",
          "|---|---|---|---|---|---|"]
    for _, r in d.sort_values(["nation", "rank", "lyumjev_pct"], ascending=[True, True, False]).iterrows():
        L.append(f"| {r.nation} | {r.area} | {r.lyumjev_class} | {r.lyumjev_pct:.1f} | {r.lyumjev_of_lispro_pct:.1f} | "
                 f"{r.lispro_pct:.1f} |")
    (OUT / "LYUMJEV_SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
