"""Write the cost of sale onto won enquiries that have none yet.

    bash tools/import-sales.sh --costs   (reads Desktop/LITPROFIT importas 2026/costs.json)

costs.json is made by 5_costs_read.py + 5_costs_pick.py and reviewed in
Savikaina.xlsx. Two sources, in this order:
  - the supplier's own invoice / order confirmation for that order, read by
    position (the total on the same line as its label), kept only when it is
    a plausible share of the sale price (margin 2-45 %);
  - the markup the offer was made with, from the folder name
    "Komercinis pasiulymas + N proc": cost = price / (1 + N %);
  - otherwise an estimate from the median margin of that supplier's
    documented sales this year, marked "įvertinta" in the note.
A cost already typed into the calculator is never overwritten. The source is
appended to the note, so nobody mistakes an estimate for an invoice."""
import json, os, sys
sys.argv = sys.argv[:1] + ["/dev/null"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "4_load.py")).read().split("M = json.load")[0])
C = json.load(open(os.environ["COSTS_JSON"]))
rows = []
while True:
    part = call("GET", "enquiries?select=id,number,cost_ex_vat,price_ex_vat,note&order=id&limit=1000&offset=%d" % len(rows)) or []
    rows += part
    if len(part) < 1000: break
by = {}
for r in rows: by.setdefault((r["number"] or "").strip(), []).append(r)   # a number can carry two lines
done = skipped = 0
for num, v in C.items():
    if not v.get("cost"): continue
    for r in by.get(num, []):
        if r.get("cost_ex_vat") is not None: skipped += 1; continue
        note = " · ".join(x for x in [(r.get("note") or "").strip(), "Savikaina: " + v["source"]] if x)
        body = {"cost_ex_vat": v["cost"], "note": note[:2000]}
        # rows created from a folder had no price: it comes from Litprofit's own invoices
        if v.get("price_set") and not float(r.get("price_ex_vat") or 0):
            body["price_ex_vat"] = v["price_set"]
            body["note"] = (body["note"] + " · Kaina: iš Litprofit sąskaitų")[:2000]
        call("PATCH", "enquiries?id=eq." + r["id"], body, prefer="return=minimal")
        done += 1
print("Costs written: %d · already had a cost, left alone: %d" % (done, skipped))
