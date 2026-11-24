import os, re, json, hashlib, unicodedata, datetime as dt, mimetypes, sys, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
import openpyxl, pymupdf, extract_msg, xlrd
ROOT="/Users/aldy/Downloads/Pardavimai 2026"
OUT=sys.argv[1]
folders={f["folder"]:f for f in json.load(open(os.path.join(os.path.dirname(__file__),"folders.json")))}
# folders the SharePoint list does not carry: the SK order or enquiry number of the folder itself
ALIAS={"SK26-062":"SK26-062 ir SK26-063","SK26-063":"SK26-062 ir SK26-063"}
def enquiry_of(name):
    f=folders[name]
    if f["code"] in ALIAS: return ALIAS[f["code"]], False
    names=[c[1] for c in f["cands"] if c[0]=="name"]
    if names: return names[0], False
    links=[c[1] for c in f["cands"] if c[0]=="csvlink"]
    if links: return links[0], False
    return f["code"], True      # new row needed
def fold(s): return unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
def num(s):
    s=s.strip().replace(" ","").replace(" ","")
    if re.match(r"^\d{1,3}(\.\d{3})+,\d{2}$",s): s=s.replace(".","").replace(",",".")
    elif re.match(r"^\d{1,3}(,\d{3})+\.\d{2}$",s): s=s.replace(",","")
    elif re.match(r"^\d+,\d{1,2}$",s): s=s.replace(",",".")
    try: return round(float(s),2)
    except: return None
def classify(fn):
    n=fold(fn); ext=n.rsplit(".",1)[-1] if "." in n else ""
    if ext in ("jpg","jpeg","png","heic","mp4","gif","webp"): return "photo","Nuotrauka"
    if "mok.paved" in n or "mok. paved" in n: return "other","Mokėjimo pavedimas"
    if "isklotine" in n: return "other","Banko išrašas"
    if n.startswith("avan") or "avansin" in n: return "invoice_out","Išankstinė sąskaita (Litprofit)"
    if "saskaita" in n or "invoice" in n or "proforma" in n:
        if "nuo litprofit" in n or "invoice to" in n or re.search(r"\blit\s*-?\s*\d{4}\b",n): return "invoice_out","Sąskaita (Litprofit)"
        if "proforma" in n: return "invoice_in","Proforma (tiekėjas)"
        if "nuo " in n: return "invoice_in","Sąskaita (tiekėjas)"
        return "invoice_out" if "litprofit" in n else "invoice_in","Sąskaita"
    if re.search(r"commercial offer|\bkp\b|kom\.? ?pas|komercinis|pasiulym|quotation|\boffer\b",n):
        return "quote","Komercinis pasiūlymas"
    if "enquiry no" in n or "uzklaus" in n: return "other","Užklausa"
    if re.search(r"order confirmation|purchase order|patvirtin|confirmation|\border\b|uzsakym|\bpo\b",n): return "contract","Užsakymas / patvirtinimas"
    if re.search(r"delivery note|cmr|packing list|label|\bpod\b|eksport|siunt|issiunc",n): return "report","Siuntimo dokumentai"
    if re.search(r"certif|sertifik|declaration|deklarac|3\.1",n): return "certificate","Sertifikatas"
    return "other",""
def party(fn):
    n=fn
    m=re.search(r"nuo\s+([^-–()]+?)\s+(?:o|io|s|os|e|u)?\s*(?:ui|-|\(|$|KP|kp)",n)
    if m: return m.group(1).strip()
    m=re.search(r"!*\s*([A-Za-z][A-Za-z0-9 .&]+?)\s+(?:o|io|s)\s+KP",n)
    if m: return m.group(1).strip()
    m=re.search(r"Invoice to\s+([^-–]+)",n)
    if m: return m.group(1).strip()
    return None
AMT_NAME=re.compile(r"EUR\s*([\d\s.,]+\d)",re.I)
def xlsx_invoice(path):
    out={}
    try:
        if path.lower().endswith(".xls"):
            b=xlrd.open_workbook(path); sh=b.sheet_by_index(0); rows=[sh.row_values(i) for i in range(sh.nrows)]
        else:
            wb=openpyxl.load_workbook(path,data_only=True,read_only=True); rows=list(wb.worksheets[0].iter_rows(values_only=True))
    except Exception: return out
    flat=[[str(c).strip() for c in r if c not in (None,"")] for r in rows]
    for r in flat:
        t=" | ".join(r)
        m=re.search(r"\bLIT\s*-?\s*(\d{4})\b",t)
        if m and "ref" not in out: out["ref"]="LIT"+m.group(1)
        m=re.search(r"Data:\s*(\d{4}-\d{2}-\d{2})",t)
        if m and "date" not in out: out["date"]=m.group(1)
        if re.search(r"I[šs] viso/Total Amount|Total Amount|Iš viso su PVM|Viso su PVM",t,re.I):
            vals=[num(x) for x in r[1:]]; vals=[v for v in vals if v is not None]
            if vals: out["amount"]=vals[-1]
        if "amount" not in out and re.search(r"^Viso/Total",t):
            vals=[num(x) for x in r[1:]]; vals=[v for v in vals if v is not None]
            if vals: out["subtotal"]=vals[-1]
        m=re.search(r"Project:\s*(\S+)",t)
        if m: out["project"]=m.group(1)
    if "amount" not in out and "subtotal" in out: out["amount"]=out["subtotal"]
    return out
TOTAL=re.compile(r"(?:Iš viso/Total Amount|Total Amount|Invoice total|Total amount|Gesamtbetrag|Endbetrag|Total EUR|TOTAL EUR|Amount due|Iš viso mokėti|Mokėti|To pay|Grand total|Total)[^\d\n]{0,40}\n?\s*(?:EUR\s*)?([\d][\d .,]*\d)",re.I)
def pdf_text(path, pages=3):
    try:
        d=pymupdf.open(path); return "\n".join(d[i].get_text() for i in range(min(pages,len(d))))
    except Exception: return ""
def pdf_amount(t):
    best=None
    for m in TOTAL.finditer(t):
        v=num(m.group(1))
        if v and v<5_000_000: best=v
    return best
def msg_meta(path):
    try:
        m=extract_msg.openMsg(path)
        d=m.date
        date=d.date().isoformat() if hasattr(d,"date") else None
        atts=[]
        for a in m.attachments:
            nm=getattr(a,"longFilename",None) or getattr(a,"shortFilename",None) or ""
            if nm.lower().endswith(".pdf") and getattr(a,"data",None) and isinstance(a.data,bytes):
                try:
                    doc=pymupdf.open(stream=a.data,filetype="pdf"); t="\n".join(doc[i].get_text() for i in range(min(3,len(doc))))
                except Exception: t=""
                atts.append((nm,t))
            elif nm: atts.append((nm,None))
        r={"subject":(m.subject or "").strip()[:300],"sender":(m.sender or "").strip()[:200],"date":date,"atts":[a[0] for a in atts][:30]}
        r["_att_text"]=[(a[0],a[1]) for a in atts if a[1]]
        m.close(); return r
    except Exception as e:
        return {"error":str(e)[:120]}
entries={}; per_enq={}
total=0
for top in sorted(os.listdir(ROOT)):
    p=os.path.join(ROOT,top)
    if not os.path.isdir(p) or top.startswith("1 SK00"): continue
    enq,new=enquiry_of(top)
    per_enq.setdefault(enq,{"folder":top,"new":new,"files":0})
    for dp,_,fs in os.walk(p):
        for f in fs:
            if f.startswith(".") or f.lower().endswith(".lnk"): continue
            full=os.path.join(dp,f); rel=os.path.relpath(full,ROOT); total+=1
            h=hashlib.sha256(open(full,"rb").read()).hexdigest()
            key=enq+"|"+h
            per_enq[enq]["files"]+=1
            if key in entries: entries[key]["copies"].append(rel); continue
            kind,label=classify(f)
            e={"enquiry":enq,"rel":rel,"copies":[],"sha256":h,"size":os.path.getsize(full),
               "mime":mimetypes.guess_type(f)[0] or ("application/vnd.ms-outlook" if f.lower().endswith(".msg") else ""),
               "kind":kind,"label":label,"counterparty":party(f),"ref":None,"amount":None,"doc_date":None,"note":None}
            m=re.search(r"(20\d{2})[ ._-](\d{2})[ ._-](\d{2})",f)
            if m: e["doc_date"]="-".join(m.groups())
            m=AMT_NAME.search(f)
            if m and kind=="other": e["amount"]=num(m.group(1))
            low=f.lower()
            if kind=="invoice_out" and (low.endswith(".xlsx") or low.endswith(".xls")):
                x=xlsx_invoice(full); e["ref"]=x.get("ref"); e["amount"]=x.get("amount"); e["doc_date"]=x.get("date") or e["doc_date"]
            elif kind in ("invoice_out","invoice_in") and low.endswith(".pdf"):
                t=pdf_text(full)
                mref=re.search(r"\bLIT\s*-?\s*(\d{4})\b",t) if kind=="invoice_out" else re.search(r"(?:Invoice|Rechnung|Sąskaita|Faktura)\s*(?:No\.?|Nr\.?|number|Nummer)?\s*[:#]?\s*([A-Z0-9][A-Z0-9/-]{3,})",t,re.I)
                if mref: e["ref"]=("LIT"+mref.group(1)) if kind=="invoice_out" else mref.group(1)
                e["amount"]=pdf_amount(t)
            if low.endswith(".msg"):
                mm=msg_meta(full)
                if "error" not in mm:
                    e["doc_date"]=mm["date"] or e["doc_date"]
                    e["note"]=("Laiškas: "+mm["subject"]+(" — "+mm["sender"] if mm["sender"] else "")+((" — priedai: "+", ".join(mm["atts"])) if mm["atts"] else ""))[:900]
                    if kind=="invoice_in":
                        for an,at in mm["_att_text"]:
                            v=pdf_amount(at)
                            if v: e["amount"]=v; mref=re.search(r"(?:Invoice|Rechnung|Faktura)\s*(?:No\.?|Nr\.?|number|Nummer)?\s*[:#]?\s*([A-Z0-9][A-Z0-9/-]{3,})",at,re.I); e["ref"]=mref.group(1) if mref else None; break
                else: e["note"]="Laiškas (nepavyko perskaityti)"
            if e["note"] is None and label: e["note"]=label
            elif label and e["note"] and not e["note"].startswith(label): e["note"]=label+". "+e["note"]
            entries[key]=e
    sys.stderr.write("\r%d files" % total)
json.dump({"entries":list(entries.values()),"enquiries":per_enq,"total_files":total},open(OUT,"w"),ensure_ascii=False)
print("\ntotal files",total,"unique per enquiry",len(entries),"enquiries",len(per_enq))
