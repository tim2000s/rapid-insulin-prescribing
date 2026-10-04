# Author's time in range, 1 April to 31 August 2026: result

Produced by `tir_check.py` on 1 October 2026 (recorded in the commit of that date) from the author's
Nightscout sensor glucose entries. The Nightscout address, token and the underlying personal CGM data
are not published.

| measure | value |
|---|---|
| period | 1 April 2026 00:00 to 1 September 2026 00:00, UK time (153 days) |
| readings after deduplication by timestamp and removal of values outside 39 to 450 mg/dL | 43,818 |
| calendar dates with data (UTC, so the BST start adds one) | 154 |
| coverage against one reading every 5 minutes (44,064 expected) | 99.4% |
| time in range, 3.9 to 10.0 mmol/L | 83.4% |
| time below 3.9 mmol/L | 6.1% |
| time above 10.0 mmol/L | 10.5% |
| mean glucose | 6.9 mmol/L |

Time in range is the share of readings, not of time; at 99.4% coverage the two differ little. Meals
were neither announced nor bolused during the period (Boost, the author's open-source algorithm).
