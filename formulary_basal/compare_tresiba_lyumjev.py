#!/usr/bin/env python3
"""
Tresiba against Lyumjev, formulary by formulary, on the four-class scheme of formulary_lyumjev_listing.csv:
    open                    available to any prescriber, no criteria
    specialist_or_criteria  specialist initiation or recommendation, or clinical criteria
    behind_another_insulin  a lower choice rank, or prior failure or unsuitability of another insulin required
    not_listed              not on the formulary
The areas and the documents are the ones used for Lyumjev (38 areas; Lanarkshire's formulary could not
be read and is left out, as it was there). Scottish boards are taken from the formularies in force
before the West of Scotland Formulary, as for Lyumjev.

Tresiba positions come from basal_positions_uk_part1.csv (England and Wales, read 2 October 2026) and
basal_positions_devolved_scotland_ni.csv (Scotland and Northern Ireland, from the pages captured for the
rapid-acting work). Part 1 used three classes; its second_line_or_excluded maps to behind_another_insulin
because Tresiba is listed in every one of those formularies. Two parity rules, so the two insulins are
read the same way: a choice rank below first counts as behind another insulin, as it did for Lyumjev
in the East Region; and a formulary that names neither product (archived Forth Valley, one class entry
for all insulins) counts as not listed for both. The coding was done after the uptake figures were seen.

Writes output/formulary/tresiba_vs_lyumjev.csv and TRESIBA_VS_LYUMJEV.md.
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = ROOT / "output" / "formulary"
ORDER = ["open", "specialist_or_criteria", "behind_another_insulin", "not_listed"]
MAP3 = {"open": "open", "specialist": "specialist_or_criteria", "second_line_or_excluded": "behind_another_insulin"}
# England and Wales: Lyumjev listing area -> fragment of the part 1 area name.
PART1 = {"Leicester Leicestershire and Rutland": "Leicester", "North East and North Cumbria": "North East and North Cumbria",
         "Greater Manchester": "Greater Manchester", "Lancashire and South Cumbria": "Lancashire",
         "Hampshire and Isle of Wight": "Hampshire", "Devon": "Devon",
         "Bath and North East Somerset, Swindon and Wiltshire": "Bath", "Kent and Medway": "Kent",
         "Cheshire and Merseyside": "Cheshire", "Humber and North Yorkshire": "Humber",
         "Nottingham and Nottinghamshire": "Nottingham", "Herefordshire and Worcestershire": "Herefordshire",
         "South East London": "South East London", "Norfolk and Suffolk (Norfolk and Waveney part)": "Norfolk",
         "South West London": "South West London", "Birmingham and Solihull": "Birmingham",
         "West and North London": "West and North London", "Aneurin Bevan": "Aneurin Bevan",
         "Cwm Taf Morgannwg": "Cwm Taf", "Hywel Dda": "Hywel Dda", "Swansea Bay": "Swansea",
         "Betsi Cadwaladr": "Betsi", "Powys": "Powys", "Cardiff and Vale": "Cardiff"}
# Scotland and Northern Ireland: four-class Tresiba code, with the row of the devolved file it rests on.
DEVOLVED = {
    "Highland": ("open", "Highland Formulary"), "Western Isles": ("open", "Highland Formulary"),
    "Lothian": ("behind_another_insulin", "East Region"), "Fife": ("behind_another_insulin", "East Region"),
    "Borders": ("behind_another_insulin", "East Region"),
    "Greater Glasgow and Clyde": ("specialist_or_criteria", "Greater Glasgow and Clyde (GGC Adult"),
    "Ayrshire and Arran": ("specialist_or_criteria", "Ayrshire and Arran (Abbreviated"),
    "Forth Valley": ("not_listed", "Forth Valley (Forth Valley Formulary"),
    "Dumfries and Galloway": ("specialist_or_criteria", "Dumfries and Galloway (Joint Formulary"),
    "Tayside": ("behind_another_insulin", "Tayside"), "Grampian": ("specialist_or_criteria", "Grampian"),
    "Orkney": ("specialist_or_criteria", "Grampian"), "Shetland": ("specialist_or_criteria", "Grampian"),
    "Northern Ireland Formulary": ("open", "Northern Ireland"),
}


def main():
    lyu = pd.read_csv(ROOT / "formulary_lyumjev_listing.csv")
    p1 = pd.read_csv(HERE / "basal_positions_uk_part1.csv")
    dev = pd.read_csv(HERE / "basal_positions_devolved_scotland_ni.csv")
    rows = []
    for _, r in lyu.iterrows():
        if r.area in PART1:
            m = p1[p1.area.str.contains(PART1[r.area], regex=False)]
            assert len(m) == 1, (r.area, len(m))
            t, basis = MAP3[m.tresiba_class.iloc[0]], m.tresiba_position.iloc[0]
        else:
            t, frag = DEVOLVED[r.area]
            m = dev[dev.area.str.contains(frag, regex=False)]
            assert len(m) == 1, (r.area, len(m))
            basis = m.tresiba_position.iloc[0]
        rows.append(dict(nation=r.nation, area=r.area, lyumjev_class=r.lyumjev_class, tresiba_class=t,
                         tresiba_basis=basis))
    d = pd.DataFrame(rows)
    rank = {k: i for i, k in enumerate(ORDER)}
    d["comparison"] = [("Tresiba less restricted" if rank[t] < rank[l] else "same" if t == l else
                        "Lyumjev less restricted") for t, l in zip(d.tresiba_class, d.lyumjev_class)]
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "tresiba_vs_lyumjev.csv", index=False)
    L = ["# Tresiba against Lyumjev on UK formularies: generated summary\n",
         "Generated by `formulary_basal/compare_tresiba_lyumjev.py`; scheme and parity rules in its docstring.\n",
         "| class | Lyumjev | Tresiba |", "|---|---|---|"]
    for k in ORDER:
        L.append(f"| {k} | {(d.lyumjev_class == k).sum()} | {(d.tresiba_class == k).sum()} |")
    L += ["", "| comparison | areas |", "|---|---|"]
    for k, n in d.comparison.value_counts().items():
        L.append(f"| {k} | {n} |")
    L += ["", "| nation | area | Lyumjev | Tresiba |", "|---|---|---|---|"]
    for _, r in d.iterrows():
        L.append(f"| {r.nation} | {r.area} | {r.lyumjev_class} | {r.tresiba_class} |")
    (OUT / "TRESIBA_VS_LYUMJEV.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
