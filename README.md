# Rapid-acting insulin prescribing in England

Monthly insulin units dispensed in English primary care over the last five years, for each Lyumjev
device and for Humalog, NovoRapid and Fiasp. It tests the argument that low and uneven uptake of the
ultra-rapid insulins (Lyumjev, Fiasp) made withdrawal of some presentations commercially easier, so
that prescriber habit rather than patient need ends up limiting access. The analysis is built to
show where the data supports that and where it does not.

This sits apart from the meal investigations in the rest of the repository and shares nothing with
them. It reads no local database.

## Status

No live data has been pulled yet. The session that wrote this ran in an environment whose network
policy blocks `openprescribing.net` and `opendata.nhsbsa.net`, so `output/` does not exist and
there is no `FINDINGS.md`. The pipeline is tested end to end against a synthetic API
(`test_pipeline.py`) whose answers are known; that proves the arithmetic, not the numbers.

To finish the work:

1. Run `python3 rapid_insulin_units.py` somewhere with access to openprescribing.net.
2. Confirm the quantity basis of each presentation (below) and fill in `CONFIRMED_BASIS`.
3. Rerun; responses are cached in `api_cache/`, so the rerun makes no API calls.
4. Check the sample month in `output/SUMMARY.md` against the OpenPrescribing web UI.
5. Write `FINDINGS.md` from `output/SUMMARY.md`.

## Running

    pip install requests pandas numpy matplotlib
    python3 rapid_insulin_units.py                  # full pull, writes output/
    python3 rapid_insulin_units.py --skip-practice  # without the practice pull
    python3 test_pipeline.py                        # synthetic end-to-end test, no network

A full pull makes roughly 23 national calls, 23 ICB calls, 5 context calls and, for the practice
concentration, 12 calls per Lyumjev presentation plus 48 for the denominator (or one per
presentation-month if the API refuses brand-level codes). Allow about ten minutes.

## Method

Presentations are discovered from the `bnf_code` endpoint for each brand prefix and merged with a
fallback list from dm+d (May 2023). Any code discovery finds that the fallback lacks is named in
the summary, which is how a new device such as a Fiasp PumpCart would show up.

National monthly items, quantity and cost come from `/spending/` for each presentation. Units are
quantity times units per quantity, where units per quantity is the concentration if quantity is in
ml and concentration times fill volume if it is a count of devices.

Missing and zero months are listed in `gaps.csv` and are not filled. A brand with no rows in a month
has an empty total for that month rather than a zero, and shares are only computed for months where
all four brands are present.

ICB figures come from `/spending_by_org/?org_type=icb` per presentation. Practice figures need a
date, so they loop over the last 12 months. The script first tries a brand-level code for the
denominator (practices prescribing any of the four brands) and records whether the API accepted it.
Lyumjev units at practice level are always pulled per presentation, because a brand-level quantity
would add U100 and U200 millilitres together.

The vial and pump segment is vials plus PumpCart cartridges. It is a rough proxy for pump use: some
pump users fill from 3 ml cartridges, and some vials are drawn up by syringe.

## Quantity basis

The `quantity` field in the English Prescribing Dataset is in the dm+d unit of measure, which for
insulin may be ml or a count of pens, cartridges or vials. Getting it wrong puts every unit figure
out by a factor of 1.5 to 10.

Not yet confirmed. The script infers it from cost: under each hypothesis it computes what 100 units
cost and picks the one nearer the list price of about 1.90 pounds per 100 units. The two hypotheses
differ by the fill volume, so this is decisive for 3 ml and 10 ml devices and weak for 1.5 ml and
1.6 ml cartridges, which are flagged as low confidence. The handover's rule of median quantity per
item (12 or more means ml) is kept in `presentations.csv` for comparison but not used, because a
single 10 ml vial reads 10 in ml and would be classed as a count.

To confirm, look up each presentation's VMPP on the OpenPrescribing dm+d pages or the NHSBSA dm+d
browser, note the unit of measure, and add it to `CONFIRMED_BASIS` with the source. Until every
presentation is confirmed, every chart carries "Quantity basis inferred, not yet verified" and the
summary lists the unverified codes.

## Outputs (`output/`)

| file | content |
|---|---|
| `presentations.csv` | code, name, brand, device, concentration, fill volume, basis and its source, cost-based diagnostics |
| `monthly_by_presentation.csv` | date by presentation: items, quantity, units, cost |
| `monthly_units_by_brand.csv`, `monthly_share_by_brand.csv` | analysis 1 |
| `lyumjev_monthly_by_device.csv`, `lyumjev_device_status.csv` | analysis 2, with the last month each device had units |
| `ultra_rapid_share_monthly.csv` | analysis 3, monthly and 12-month rolling |
| `icb_ultrarapid_share_last12m.csv`, `icb_variation_stats.csv`, `icb_monthly_by_presentation.csv` | analysis 4 |
| `practice_lyumjev_concentration.csv`, `practice_concentration_stats.csv` | analysis 5 |
| `vial_share_by_brand.csv`, `ultra_rapid_share_by_segment_monthly.csv` | analysis 6 |
| `context_products_last12m.csv` | generic lispro and aspart, Admelog, Sanofi lispro, Trurapi, for scale |
| `gaps.csv` | missing and zero months |
| `SUMMARY.md` | every headline number, generated |
| `*.png` | charts, 160 dpi, each with the source line |

Analysis 7, launch trajectories from the NHSBSA English Prescribing Dataset back to 2014, is not
built. The API covers five years, which starts after both launches.

## Caveats

- Primary care dispensing only. Hospital initiations and hospital supply are missing, and new
  starts on ultra-rapid insulin often begin in specialist clinics.
- Units dispensed are not units used. Stockpiling around shortages distorts the months near supply
  problems, which is exactly when the Lyumjev device series matter.
- Variation between ICBs is not proof of inertia. Local formularies, the reach of specialist
  centres, the mix of pump users and local shortages can each explain some of it.
- England only. Public Health Scotland publishes comparable monthly practice-level data by drug.
- The latest month is usually two to three months behind the pull date. The summary states it.

## Source

OpenPrescribing.net, Bennett Institute for Applied Data Science, University of Oxford, built on the
NHSBSA English Prescribing Dataset.
