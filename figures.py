#!/usr/bin/env python3
"""
Figures for the preprint, from output/history/ and output/hospital/. Run after history.py and
hospital_analysis.py. Writes output/figures/.

Colours follow each brand throughout (rapid_insulin_units.COLOURS). The stack order puts the
ultra-rapid products at the base and keeps Fiasp (orange) and NovoRapid (yellow) apart, since that
pair fails the normal-vision separation check when adjacent; the order below passed
validate_palette.js from the dataviz reference (CVD worst adjacent 9.1, normal-vision 22.9).
"""
from pathlib import Path

import numpy as np
import pandas as pd

import rapid_insulin_units as R

HERE = Path(__file__).parent
OUT = HERE / "output" / "figures"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
STACK = [("Lyumjev", "0601011L0BD"), ("Fiasp", "0601011A0BC"), ("Humalog", "0601011L0BB"),
         ("NovoRapid", "0601011A0BB"), ("Apidra", "0601011P0BB")]
OTHER = ("Biosimilar and generic", "#e87ba4")


def style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                         "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                         "axes.edgecolor": "#8a8984", "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.labelcolor": INK})
    return plt


def fig_share_stack(plt):
    p = pd.read_csv(HERE / "output" / "history" / "national_by_presentation.csv", parse_dates=["date"])
    p = p[p["class"] != "human soluble"]
    lab = pd.Series(OTHER[0], index=p.index)
    for name, prefix in STACK:
        lab[p.code.str.startswith(prefix)] = name
    u = p.assign(label=lab).pivot_table(index="date", columns="label", values="units", aggfunc="sum").fillna(0)
    u = u.rolling(3).sum().dropna()
    share = u.div(u.sum(axis=1), axis=0) * 100
    cols = [n for n, _ in STACK] + [OTHER[0]]
    colours = [R.COLOURS[n] for n, _ in STACK] + [OTHER[1]]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.stackplot(share.index, *[share[c] for c in cols], colors=colours, edgecolor="white", linewidth=0.6)
    ax.set_ylim(0, 100)
    ax.set_xlim(share.index[0], share.index[-1])
    ax.set_ylabel("% of rapid-acting analogue units (3-month)")
    ax.grid(axis="x", visible=False)
    # Direct labels at the right edge, centred in each band, for the bands wide enough to hold one.
    last = share[cols].iloc[-1]
    base = 0.0
    for c, v in last.items():
        if v >= 1.5:
            ax.annotate(f"{c} {v:.1f}%", (share.index[-1], base + v / 2), xytext=(5, 0),
                        textcoords="offset points", va="center", fontsize=8, color=INK, annotation_clip=False)
        base += v
    ultra = share[["Lyumjev", "Fiasp"]].sum(axis=1)
    ax.plot(share.index, ultra, color=INK, lw=1.0)
    ax.annotate(f"Ultra-rapid {ultra.iloc[-1]:.1f}%", (share.index[-1], ultra.iloc[-1]), xytext=(-6, 6),
                textcoords="offset points", ha="right", fontsize=8, color=INK)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colours]
    ax.legend(handles, cols, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, frameon=False, fontsize=8)
    fig.tight_layout()
    fig.subplots_adjust(right=0.8)
    fig.savefig(OUT / "fig1_share_by_product.png", dpi=220)
    plt.close(fig)
    return share


def fig_hospital(plt):
    h = pd.read_csv(HERE / "output" / "hospital" / "hpdc_vs_primary_monthly.csv", index_col="date", parse_dates=True)
    y = pd.read_csv(HERE / "output" / "history" / "rolling_12m_shares.csv", index_col="date", parse_dates=True)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(h.index, h.hospital_ultra_pct_12m, color=R.COLOURS["Fiasp"], lw=2)
    ax.plot(y.index, y.ultra_units_pct, color=R.COLOURS["Lyumjev"], lw=2)
    ax.annotate("Hospital prescribers", (h.index[-1], h.hospital_ultra_pct_12m.iloc[-1]), xytext=(5, 0),
                textcoords="offset points", va="center", fontsize=8, color=INK, annotation_clip=False)
    ax.annotate("Primary care", (y.index[-1], y.ultra_units_pct.iloc[-1]), xytext=(5, 0),
                textcoords="offset points", va="center", fontsize=8, color=INK, annotation_clip=False)
    ax.set_ylim(0, 50)
    ax.set_xlim(pd.Timestamp("2016-01-01"), y.index[-1])
    ax.set_ylabel("Ultra-rapid % of analogue units (12-month)")
    fig.tight_layout()
    fig.subplots_adjust(right=0.82)
    fig.savefig(OUT / "fig3_hospital_vs_primary.png", dpi=220)
    plt.close(fig)


def fig_icb(plt):
    t = pd.read_csv(HERE / "output" / "icb_ultrarapid_share_last12m.csv").sort_values("ultra_rapid_share_pct")
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    y = np.arange(len(t))
    ax.barh(y, t.Lyumjev_share_pct, color=R.COLOURS["Lyumjev"], height=0.7, edgecolor="white", linewidth=0.6)
    ax.barh(y, t.Fiasp_share_pct, left=t.Lyumjev_share_pct, color=R.COLOURS["Fiasp"], height=0.7,
            edgecolor="white", linewidth=0.6)
    names = [n.replace("NHS ", "").replace(" Integrated Care Board", "").replace(" And ", " and ")
             .replace(" Of ", " of ").replace("-On-", "-on-") for n in t.icb]
    ax.set_yticks(y, names, fontsize=7)
    ax.set_ylim(-0.7, len(t) - 0.3)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("% of rapid-acting analogue units, August 2025 to July 2026")
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=R.COLOURS[b]) for b in ("Lyumjev", "Fiasp")], ["Lyumjev", "Fiasp"],
              loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_icb.png", dpi=220)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plt = style()
    fig_share_stack(plt)
    fig_icb(plt)
    fig_hospital(plt)


if __name__ == "__main__":
    main()
