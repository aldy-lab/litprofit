import os, re, json, csv, warnings, logging, collections
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
import pymupdf, extract_msg
ROOT="/Users/aldy/Downloads/Pardavimai 2026"
M=json.load(open("/Users/aldy/Desktop/LITPROFIT importas 2026/manifest.json"))
LABEL=re.compile(r"(?i)^(final amount|total sum|invoice total|total amount|grand total|total net|net total|total eur|amount due|gesamtbetrag|endbetrag|rechnungsbetrag|nettobetrag|i[šs] viso|viso|suma be pvm|total)\b")
NUM=re.compile(r"^-?\d{1,3}(?:[ .,]\d{3})*(?:[.,]\d{2})$|^-?\d+[.,]\d{2}$")
FREIGHT=re.compile(r"(?i)delamode|\bfl o\b|dhl|ups|schenker|hres|dsv|kuehne|transport|krovin|shipping|freight")
def tonum(s):
    s=s.replace(" ","")
    if re.match(r"^-?\d{1,3}(\.\d{3})+,\d{2}$",s) or re.match(r"^-?\d+,\d{2}$",s): s=s.replace(".","").replace(",",".")
    else: s=s.replace(",","")
    return float(s)
def page_total(doc):
    best=None
    for page in doc:
        words=page.get_text("words")  # x0,y0,x1,y1,text,block,line,wno
        lines=collections.defaultdict(list)
        for w in words: lines[(w[5],w[6])].append(w)
        rows=[]
        for ws in lines.values():
            ws.sort(key=lambda w:w[0]); rows.append((min(w[1] for w in ws),max(w[3] for w in ws),min(w[0] for w in ws)," ".join(w[4] for w in ws)))
        for y0,y1,x0,txt in rows:
            if not LABEL.match(txt.strip()): continue
            # numbers on the same visual line, to the right of the label
            cands=[]
            for w in words:
                cy=(w[1]+w[3])/2
                if y0-3<=cy<=y1+3 and w[0]>x0 and NUM.match(w[4].strip()):
                    try: cands.append((w[0],tonum(w[4].strip())))
                    except ValueError: pass
            if cands:
                v=max(cands)[1]
                if v>0: best=v   # the last total on the document wins: final amount after discounts
    return best
def pdfs(e):
    p=os.path.join(ROOT,e["rel"]); out=[]
    try:
        if p.lower().endswith(".pdf"): out.append((e["rel"].split("/")[-1],pymupdf.open(p)))
        elif p.lower().endswith(".msg"):
            m=extract_msg.openMsg(p)
            for a in m.attachments:
                d=getattr(a,"data",None); nm=(getattr(a,"longFilename",None) or "")
                if isinstance(d,bytes) and nm.lower().endswith(".pdf"):
                    try: out.append((nm,pymupdf.open(stream=d,filetype="pdf")))
                    except Exception: pass
            m.close()
    except Exception: pass
    return out
rows=list(csv.DictReader(open("/Users/aldy/Downloads/Litprofit tiekimo užklausos.csv",encoding="utf-8-sig")))
price={" ".join(r["Numeris"].split()):float((r["Kaina be PVM"] or "0").replace("€","").replace(",","").strip() or 0) for r in rows}
status={" ".join(r["Numeris"].split()):r["Užklausos būsena"] for r in rows}
pays=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"payments.json")))
markup={}
for e in M["entries"]:
    m=re.search(r"(?i)Komercinis pasiulymas \+ ?(\d{1,2}) ?proc",e["rel"])
    if m: markup.setdefault(e["enquiry"],int(m.group(1)))
res={}
for enq in sorted({e["enquiry"] for e in M["entries"]}):
    goods={}; freight={}
    for e in M["entries"]:
        if e["enquiry"]!=enq or e["kind"]!="invoice_in": continue
        if any(seg.lower().startswith(("senas","sena ")) for seg in e["rel"].split("/")): continue
        for nm,doc in pdfs(e):
            v=page_total(doc)
            if not v: continue
            tgt=freight if FREIGHT.search(e["rel"]+" "+nm) else goods
            key=re.sub(r"[^0-9]","",nm)[-8:] or nm   # one invoice saved twice counts once
            tgt.setdefault((key,round(v,2)),(v,e["rel"].split("/")[-1][:70]))
    gsum=round(sum({round(v[0],2) for v in goods.values()}),2)
    res[enq]={"price":price.get(enq),"status":status.get(enq),"goods":gsum,"goods_n":len({round(v[0],2) for v in goods.values()}),
              "freight":round(sum({round(v[0],2) for v in freight.values()}),2),"markup":markup.get(enq),
              "paid_out":round(sum(p["amount"] for p in pays.get(enq,{}).values()),2),
              "docs":[v[1] for v in list(goods.values())[:6]]}
json.dump(res,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"costs.json"),"w"),ensure_ascii=False,indent=1)
won=[k for k,v in res.items() if v["status"]=="Gautas PO" or k.startswith("SK26")]
ok=[k for k in won if res[k]["goods"] and res[k]["price"] and 0.3*res[k]["price"]<=res[k]["goods"]<=1.05*res[k]["price"]]
print("won",len(won),"with supplier invoice totals",sum(1 for k in won if res[k]["goods"]),"plausible",len(ok),"markup",sum(1 for k in won if res[k]["markup"]))
