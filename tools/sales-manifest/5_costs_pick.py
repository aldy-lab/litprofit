import os, re, json, collections, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"costs.py")).read().split("rows=list(csv")[0])
import csv
NOT_SUPPLIER=re.compile(r"(?i)issiunc|uzsakov|buhalter|prasau|siunciu|kolega|pridedu|praso|informuo|patikrin|fyi|litprofit|pakoreguot|replikuo")
SUPPLIER_DOC=re.compile(r"(?i)^\W*\d*\s*(saskaita|proforma|invoice|sales invoice|rechnung|faktura|order confirmation)\b.*\b(nuo|from)\b|^\W*\d*\s*(sales invoice|invoice|rechnung|faktura)\b")
rows=list(csv.DictReader(open("/Users/aldy/Downloads/Litprofit tiekimo užklausos.csv",encoding="utf-8-sig")))
price={" ".join(r["Numeris"].split()):float((r["Kaina be PVM"] or "0").replace("€","").replace(",","").strip() or 0) for r in rows}
status={" ".join(r["Numeris"].split()):r["Užklausos būsena"] for r in rows}
client={" ".join(r["Numeris"].split()):r["Klientas"].strip() for r in rows}
markup={}
for e in M["entries"]:
    m=re.search(r"(?i)Komercinis pasiulymas \+ ?(\d{1,2}) ?proc",e["rel"])
    if m: markup.setdefault(e["enquiry"],int(m.group(1)))
out={}
for enq in sorted({e["enquiry"] for e in M["entries"]}):
    p=price.get(enq) or 0
    if not (status.get(enq)=="Gautas PO" or enq.startswith("SK26")): continue
    found={}
    for e in M["entries"]:
        if e["enquiry"]!=enq: continue
        name=e["rel"].split("/")[-1]
        if any(s.lower().startswith(("senas","sena ")) for s in e["rel"].split("/")): continue
        if NOT_SUPPLIER.search(name) or not SUPPLIER_DOC.search(name) or FREIGHT.search(name): continue
        others=set(re.findall(r"SK26-\d{3}",name))-{enq}
        if others: continue          # one invoice for several orders: not attributable
        for nm,doc in pdfs(e):
            if FREIGHT.search(nm) or NOT_SUPPLIER.search(nm): continue
            v=page_total(doc)
            if v: found[round(v,2)]=name[:80]
    vals=sorted(found)
    # proforma and invoice of the same order are the same money: keep distinct amounts only
    total=round(sum(vals),2) if vals else None
    if total and p and not (0.3*p<=total<=1.02*p):
        # a single document that fits on its own beats a sum that does not
        fit=[v for v in vals if 0.3*p<=v<=1.02*p]
        total=max(fit) if fit else None
    src=None; cost=None
    if total and p: cost, src = total, "tiekėjo sąskaita: " + "; ".join(found[v] for v in vals if v<=total+0.01)[:300]
    elif markup.get(enq) and p: cost, src = round(p/(1+markup[enq]/100),2), "apskaičiuota iš antkainio %d%% (aplankas „Komercinis pasiulymas + %d proc“)"%(markup[enq],markup[enq])
    out[enq]={"client":client.get(enq,""),"price":p,"cost":cost,"source":src,"markup":markup.get(enq)}
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"costs_final.json"),"w"),ensure_ascii=False,indent=1)
c=collections.Counter(("invoice" if v["source"] and v["source"].startswith("tiek") else "markup" if v["source"] else ("no price" if not v["price"] else "none")) for v in out.values())
print(len(out),"won enquiries:",dict(c))
