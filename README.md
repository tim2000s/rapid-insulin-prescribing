# Rapid-acting insulin prescribing in England

Monthly insulin units dispensed in English primary care from November 2020 to July 2026, for each
Lyumjev device and for Humalog, NovoRapid, Fiasp, Trurapi and Apidra. It tests the argument that low
and uneven uptake of the ultra-rapid insulins (Lyumjev, Fiasp) made withdrawal of some
presentations commercially easier, so that prescriber habit rather than patient need ends up
limiting access. The analysis is built to show where the data supports that and where it does not.

## Status

Data pulled and analysed on 30 September 2026; results are in `FINDINGS.md`. The pipeline was
first written against the OpenPrescribing API, which refuses scripted clients (a Cloudflare
challenge, HTTP 403). It now reads the same dataset from the NHSBSA open data portal through
`epd_source.py`, which answers the pipeline's API calls from a local cache. The OpenPrescribing
client is kept behind `--source openprescribing`.

## Running

    pip install requests pandas numpy matplotlib
    python3 epd_source.py           # fill epd_cache/ from NHSBSA (about 90 SQL calls, a few minutes)
    python3 rapid_insulin_units.py  # analyse, writes output/
    python3 compare_brands.py       # concentration and presentation status for every brand
    python3 test_pipeline.py        # synthetic end-to-end test, no network

`epd_source.py` pulls two aggregates from the "English Prescribing Dataset (EPD) with SNOMED code"
package: presentation by ICB for every month (all 0601011 codes), and presentation by practice for
the last 12 months (the six brands). The monthly tables use three schemas (STP columns before May
2022, renamed BNF columns from March 2025) and some store numbers as text; the queries handle both.
The cache is resumable, one JSON file per month per table.

## Method

The denominator is six branded rapid-acting analogues. Trurapi and Apidra were added to the
original four because Trurapi alone was 7.5% of units in July 2026, nearly twice Lyumjev.

Presentations are discovered from the `bnf_code` endpoint for each brand prefix and merged with a
fallback list from dm+d (May 2023). Any code discovery finds that the fallback lacks is named in
the summary, which is how a new device such as a Fiasp PumpCart would show up.

National monthly items, quantity and cost come from `/spending/` for each presentation. Units are
quantity times units per quantity, where units per quantity is the concentration if quantity is in
ml and concentration times fill volume if it is a count of devices.

Missing and zero months are listed in `gaps.csv`. Months before a brand first appears are zero.
With the EPD source, which is complete for every month because each table is pulled whole, a brand
with no rows in a later month is also zero. With the API source it stays empty, because a missing
month there may be a failed call, and shares are only computed for months where every brand is
present.

ICB figures come from `/spending_by_org/?org_type=icb` per presentation. With the EPD source they
are built from practice rows, each practice assigned to its ICB in the latest month, because twelve
ICBs merged into six in April 2026 and three were split between successors. Practice figures need a
date, so they loop over the last 12 months. The script first tries a brand-level code for the
denominator (practices prescribing any of the six brands) and records whether the API accepted it.
Lyumjev units at practice level are always pulled per presentation, because a brand-level quantity
would add U100 and U200 millilitres together.

The vial and pump segment is vials plus PumpCart cartridges. It is a rough proxy for pump use: some
pump users fill from 3 ml cartridges, and some vials are drawn up by syringe.

## Quantity basis

The `quantity` field in the English Prescribing Dataset counts devices (pens, cartridges, vials)
for these insulins, not millilitres. Getting it wrong puts every unit figure out by a factor of 1.5
to 10.

Confirmed on 30 September 2026 against the NHSBSA Secondary Care Medicines Data, which reports the
same products in the dm+d VMP unit of measure. That unit is ML for every lispro, aspart and
glulisine product, and hospital cost per ml multiplied by fill volume reproduces EPD cost per unit
of quantity to within 2% for every device type (3 ml aspart cartridge: 1.87 pounds per ml times 3
is 5.61, against 5.63 in EPD). `CONFIRMED_BASIS` records this for every presentation. The
cost-based inference in the script reached the same answer independently and is still reported in
`presentations.csv`.

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
| `context_products_last12m.csv` | generic lispro, aspart and glulisine, Admelog, Sanofi lispro, for scale |
| `brand_concentration.csv`, `presentation_status.csv` | from `compare_brands.py`: practice concentration and withdrawals for every brand |
| `gaps.csv` | missing and zero months |
| `SUMMARY.md` | every headline number, generated |
| `*.png` | charts, 160 dpi, each with the source line |

Analysis 7, launch trajectories back to 2014, is not built. The SNOMED-coded dataset starts in
November 2020, after both launches; the older EPD package without SNOMED codes runs from January
2014 to June 2025 and would support it.

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

NHSBSA English Prescribing Dataset with SNOMED code and Secondary Care Medicines Data, NHSBSA open
data portal (opendata.nhsbsa.net), Open Government Licence. OpenPrescribing.net, Bennett Institute
for Applied Data Science, University of Oxford, serves the same prescribing data.
