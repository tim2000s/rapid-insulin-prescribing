#!/usr/bin/env python3
"""Check the author's time in range for the article's statement: sensor glucose entries from the
author's Nightscout, 1 April to 31 August 2026 (UK time), in 7-day chunks with retries. Reports time
in range 3.9 to 10.0 mmol/L as the share of readings, with readings deduplicated by timestamp. The
Nightscout address and token are read from environment variables so they are not committed."""
import os, time
import pandas as pd, requests
NS, TOKEN = os.environ["NS_URL"], os.environ["NS_TOKEN"]
start, end = pd.Timestamp("2026-04-01", tz="Europe/London"), pd.Timestamp("2026-09-01", tz="Europe/London")
rows = []
t = start
while t < end:
    u = min(t + pd.Timedelta(days=7), end)
    for attempt in range(5):
        try:
            r = requests.get(f"{NS}/api/v1/entries/sgv.json", timeout=120, params={
                "token": TOKEN, "count": 50000,
                "find[date][$gte]": int(t.timestamp() * 1000), "find[date][$lt]": int(u.timestamp() * 1000)})
            r.raise_for_status(); rows += r.json(); break
        except Exception:
            time.sleep(15 * (attempt + 1))
    t = u
d = pd.DataFrame(rows).drop_duplicates("date")
d = d[d.sgv.between(39, 450)]
mmol = d.sgv / 18.0
print(f"readings {len(d):,}; days with data {pd.to_datetime(d.date, unit='ms').dt.date.nunique()}")
print(f"TIR 3.9-10.0: {(mmol.between(3.9, 10.0)).mean() * 100:.1f}%  below 3.9: {(mmol < 3.9).mean() * 100:.1f}%  above 10: {(mmol > 10).mean() * 100:.1f}%")
print(f"mean glucose {mmol.mean():.1f} mmol/L")
