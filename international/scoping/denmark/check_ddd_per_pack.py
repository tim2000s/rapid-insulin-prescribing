"""Check that medstat.dk's defined daily doses are a fixed relabelling of insulin units: DDD per
package sold should equal the pack's units divided by 40 (37.5 for 5 x 3 ml, 25 for a 10 ml vial,
20 for 5 x 1.6 ml), so DDD x 40 gives units dispensed and shares of DDD equal shares of units."""
import pandas as pd

d = pd.read_csv("rapid_packages_by_year.csv", dtype={"pkg": str})
lk = pd.read_csv("rapid_package_lookup.csv", dtype={"pkg": str}).drop_duplicates("pkg").set_index("pkg")
d = d[d.sector == 100]
for c in ("a2_packages_k", "a2_volume_k"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
g = d.groupby("pkg")[["a2_packages_k", "a2_volume_k"]].sum()
g = g[g.a2_packages_k > 1]
g["ddd_per_pack"] = g.a2_volume_k / g.a2_packages_k
g = g.join(lk[["product", "pack_size"]]).sort_values("a2_packages_k", ascending=False)
g.round(2).to_csv("ddd_per_pack_check.csv")
print(g.head(15).round(2).to_string())
