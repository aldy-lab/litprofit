import os, re, json, csv, collections, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
H=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(H,"costs.py")).read().split("rows=list(csv")[0])   # page_total, pdfs, FREIGHT, tonum, M, ROOT
import openpyxl, xlrd
C=json.load(open("/Users/aldy/Desktop/LITPROFIT importas 2026/costs.json"))
OURS=re.compile(r"(?i)issiunc|uzsakov|buhalter|prasau|siunciu|kolega|pridedu|praso|informuo|patikrin|fyi|pakoreguot|replikuo|commercial offer|komercinis|nuo litprofit|invoice to|packing|cmr|label|delivery note|enquiry no|juodrast|avan")
SUP=re.compile(r"(?i)\b(saskaita|proforma|invoice|rechnung|faktura|order confirmation|confirmation|kp|kom\.? ?pas|quotation|offer|angebot|pasiulym)\b")
RANK=lambda n: 0 if re.search(r"(?i)saskaita|invoice|rechnung|faktura",n) else 1 if re.search(r"(?i)confirmation|patvirt",n) else 2 if re.search(r"(?i)proforma",n) else 3
LBL=re.compile(r"(?i)^(final amount|total sum|invoice total|total amount|grand total|total net|net total|net value|total eur|total|suma|iš viso|viso|gesamt|summe|nettobetrag)\b")
def xlsx_total(path=None, data=None):
    try:
        if data is not None:
            import io; wb=openpyxl.load_workbook(io.BytesIO(data),data_only=True,read_only=True)
        else: wb=openpyxl.load_workbook(path,data_only=True,read_only=True)
        rows=list(wb.worksheets[0].iter_rows(values_only=True))
    except Exception: return None
    best=None
    for r in rows:
        cells=[c for c in r if c not in (None,"")]
        if not cells or not isinstance(cells[0],str) or not LBL.match(cells[0].strip()): continue
        nums=[c for c in cells[1:] if isinstance(c,(int,float)) and c>0]
        if nums: best=float(nums[-1])
    return best
def docs(e):
    p=os.path.join(ROOT,e["rel"]); out=[]
    low=p.lower()
    if low.endswith(".pdf"):
        try: out.append((e["rel"].split("/")[-1],"pdf",pymupdf.open(p)))
        except Exception: pass
    elif low.endswith((".xlsx",".xls")) and low.endswith(".xlsx"):
        out.append((e["rel"].split("/")[-1],"xlsx",p))
    elif low.endswith(".msg"):
        try:
            m=extract_msg.openMsg(p)
            for a in m.attachments:
                d=getattr(a,"data",None); nm=(getattr(a,"longFilename",None) or "")
                if not isinstance(d,bytes): continue
                if nm.lower().endswith(".pdf"):
                    try: out.append((nm,"pdf",pymupdf.open(stream=d,filetype="pdf")))
                    except Exception: pass
                elif nm.lower().endswith(".xlsx"): out.append((nm,"xlsxb",d))
            m.close()
        except Exception: pass
    return out
def value(kind,obj):
    if kind=="pdf": return page_total(obj)
    if kind=="xlsx": return xlsx_total(path=obj)
    if kind=="xlsxb": return xlsx_total(data=obj)
# Litprofit's own invoices give the sale price where the register has none
invsum=collections.defaultdict(dict)
for e in M["entries"]:
    if e["kind"]=="invoice_out" and e.get("ref") and e.get("amount") and not any(s.lower().startswith(("senas","sena ")) for s in e["rel"].split("/")):
        invsum[e["enquiry"]][e["ref"]]=e["amount"]
res={}
todo=[k for k,v in C.items() if not v["cost"] and v.get("open")]
for enq in todo:
    v=C[enq]; price=v["price"] or round(sum(invsum.get(enq,{}).values()),2) or None
    cands=[]
    for e in M["entries"]:
        if e["enquiry"]!=enq: continue
        name=e["rel"].split("/")[-1]
        if any(s.lower().startswith(("senas","sena ")) for s in e["rel"].split("/")): continue
        if OURS.search(name) or not SUP.search(name) or FREIGHT.search(name): continue
        for nm,kind,obj in docs(e):
            if OURS.search(nm) or FREIGHT.search(nm): continue
            val=value(kind,obj)
            if val and val>1: cands.append((RANK(name+" "+nm),val,name[:70],re.findall(r"SK26-\d{3}",name+" "+nm)))
    res[enq]={"price":price,"price_from_invoices":not v["price"] and bool(price),"cands":sorted(set((c[0],round(c[1],2),c[2],tuple(c[3])) for c in cands))}
json.dump(res,open(os.path.join(H,"costs3_open.json"),"w"),ensure_ascii=False,indent=1)
n_c=sum(1 for r in res.values() if r["cands"]); n_p=sum(1 for r in res.values() if r["price"])
print("todo",len(todo),"with candidates",n_c,"with price",n_p)
