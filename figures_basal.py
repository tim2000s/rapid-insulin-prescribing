#!/usr/bin/env python3
"""
Figures for the Tresiba comparison and the biosimilar section, in the style of figures.py.

    fig5_tresiba_vs_lyumjev_formulary.png  formulary position of each, 38 UK areas
                                            (output/formulary/tresiba_vs_lyumjev.csv)
    fig6_degludec_vs_ultra_countries.png    degludec share of long-acting against ultra-rapid share of
                                            rapid-acting, latest common year in each series
                                            (international/output/basal_intl.csv, intl_annual.csv)
    fig7_biosimilar_savings.png             long-acting biosimilar saving against the cost of reaching
                                            Wales's ultra-rapid share, England and North West London
                                            (output/biosimilar/scenarios.csv)

Restriction classes are ordered, so they take one hue from light (open) to dark (not listed). The
country chart puts each pair on one row so the gap is read directly; Germany's ultra-rapid share is
drawn as a range because its tables pool Lyumjev with Liprolog.
"""
from pathlib import Path

import pandas as pd

import figures as F
import rapid_insulin_units as R

HERE = Path(__file__).parent
OUT = HERE / "output" / "figures"
DEGLUDEC = "#4a3aa7"


def fig5(plt):
    d = pd.read_csv(HERE / "output" / "formulary" / "tresiba_vs_lyumjev.csv")
    order = [("open", "Open to any prescriber"), ("specialist_or_criteria", "Specialist or set criteria"),
             ("behind_another_insulin", "Behind another insulin"), ("not_listed", "Not on the formulary")]
    ramp = ["#cfe0f5", "#86b2e8", "#2a78d6", "#14396b"]
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    for row, (col, label) in enumerate((("tresiba_class", "Tresiba"), ("lyumjev_class", "Lyumjev"))):
        left = 0
        for (k, name), c in zip(order, ramp):
            n = int((d[col] == k).sum())
            ax.barh(row, n, left=left, color=c, height=0.6, edgecolor="white", linewidth=1.2)
            if n:
                ax.text(left + n / 2, row, str(n), ha="center", va="center", fontsize=9,
                        color="white" if c in ramp[2:] else F.INK)
            left += n
    ax.set_yticks([0, 1], ["Tresiba", "Lyumjev"])
    ax.set_xlim(0, len(d))
    ax.set_xlabel(f"Number of UK formulary areas (of {len(d)})")
    ax.grid(axis="y", visible=False)
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=c) for c in ramp], [n for _, n in order], loc="lower left",
              bbox_to_anchor=(0, 1.02), ncol=4, frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_tresiba_vs_lyumjev_formulary.png", dpi=220)
    plt.close(fig)


def fig6(plt):
    b = pd.read_csv(HERE / "international" / "output" / "basal_intl.csv")
    rows = [("England", 2025, "England, 2025"), ("France", 2025, "France, 2025"), ("Denmark", 2025, "Denmark, 2025"),
            ("Germany", 2024, "Germany, 2024"), ("US Medicare Part D", 2024, "US Medicare Part D, 2024"),
            ("US Medicaid", 2025, "US Medicaid, 2025"), ("Australia", 2026, "Australia, 2025-26*")]
    ger_hi = 27.72  # Fiasp plus the pooled Liprolog and Lyumjev line, 2024 (international/output/INTL_SUMMARY.md)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for i, (c, y, label) in enumerate(rows):
        r = b[(b.country == c) & (b.year == y)].iloc[0]
        yy = len(rows) - 1 - i
        ax.plot([r.ultra_pct, r.degludec_pct], [yy, yy], color=F.GRID, lw=3, zorder=1)
        if c == "Germany":
            ax.plot([r.ultra_pct, ger_hi], [yy, yy], color=R.COLOURS["Fiasp"], lw=2, alpha=0.5, zorder=2)
        ax.scatter(r.ultra_pct, yy, s=60, color=R.COLOURS["Fiasp"], zorder=3, edgecolor="white", linewidth=1.5)
        ax.scatter(r.degludec_pct, yy, s=60, color=DEGLUDEC, zorder=3, edgecolor="white", linewidth=1.5)
    ax.set_yticks(range(len(rows)), [r[2] for r in rows][::-1])
    ax.set_xlabel("% of class volume (long-acting analogue for degludec; rapid-acting analogue for ultra-rapid)")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 45)
    ax.legend([plt.Line2D([], [], marker="o", ls="", color=DEGLUDEC, markersize=7),
               plt.Line2D([], [], marker="o", ls="", color=R.COLOURS["Fiasp"], markersize=7)],
              ["Degludec (Tresiba) share of long-acting", "Ultra-rapid share of rapid-acting"],
              loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2, frameon=False, fontsize=8)
    ax.text(0, -0.30, "Germany: ultra-rapid drawn as a range, from Fiasp alone to Fiasp plus the pooled Lyumjev and "
            "Liprolog line.\n*Australia: PBS prescriptions; degludec was not subsidised until July 2026.",
            transform=ax.transAxes, fontsize=7, color=F.MUTED, va="top")
    fig.tight_layout()
    fig.savefig(OUT / "fig6_degludec_vs_ultra_countries.png", dpi=220)
    plt.close(fig)


def fig7(plt):
    s = pd.read_csv(HERE / "output" / "biosimilar" / "scenarios.csv").set_index("area")
    bars = [("A_long_saving_80_gbp_m", "Long-acting saving:\n80% of Lantus and\nAbasaglar pens to Semglee", DEGLUDEC),
            ("B_rapid_saving_80_gbp_m", "Rapid-acting saving:\n80% of NovoRapid\nto Trurapi", R.COLOURS["Trurapi"]),
            ("E_forgone_to_wales_gbp_m", "Most it would cost to\nreach Wales's\nultra-rapid share", R.COLOURS["Fiasp"])]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6))
    for ax, (area, unit, scale) in zip(axes, (("England", "£ million", 1), ("North West London", "£ thousand", 1000))):
        vals = [s.loc[area, k] * scale for k, _, _ in bars]
        ax.bar(range(3), vals, color=[c for _, _, c in bars], width=0.65, edgecolor="white", linewidth=0.8)
        for x, v in enumerate(vals):
            ax.text(x, v, f"{v:,.1f}" if scale == 1 else f"{v:,.0f}", ha="center", va="bottom", fontsize=8, color=F.INK)
        ax.set_xticks(range(3), [l for _, l, _ in bars], fontsize=7)
        ax.set_ylabel(f"{unit} a year, list price")
        ax.set_title(area, fontsize=10, color=F.INK)
        ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig7_biosimilar_savings.png", dpi=220)
    plt.close(fig)


def main():
    plt = F.style()
    for f in (fig5, fig6, fig7):
        f(plt)
    print("written", [p.name for p in sorted(OUT.glob("fig[567]_*.png"))])


if __name__ == "__main__":
    main()
