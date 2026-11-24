import os, re, csv, json, hashlib, collections, urllib.parse
ROOT="/Users/aldy/Downloads/Pardavimai 2026"
CSV="/Users/aldy/Downloads/Litprofit tiekimo užklausos.csv"
OUT=os.path.dirname(os.path.abspath(__file__))
rows=list(csv.DictReader(open(CSV,encoding="utf-8-sig")))
nums=[" ".join(r["Numeris"].split()) for r in rows]+["26.1","26.5-12","26.5-12.2","26.6-25.1","SK26-062"]
numset=set(nums)
def norm(code):
    c=re.sub(r"\s*-\s*","-",code.strip())
    c=re.sub(r"\.(\d)-",lambda m:"."+m.group(1)+"-",c)
    return c
# folder name -> enquiry number from the CSV's own folder links
link2num={}
for r in rows:
    u=urllib.parse.unquote(r["Aplanko nuoroda"] or "")
    m=re.search(r"Pardavimai 2026/([^?&/]+)",u)
    if m: link2num[m.group(1).strip()]=" ".join(r["Numeris"].split())
CODE=re.compile(r"^(SK26-\d{3}|\d{2}\.\d{1,2}\s*-\s*\d{1,2}(?:\.\d+)?[A-Z]?)")
REF=re.compile(r"\((\d{2}[._]\d{1,2}-\d{1,2}(?:[._]\d+)?)\)")
folders=[]
for d in sorted(os.listdir(ROOT)):
    p=os.path.join(ROOT,d)
    if not os.path.isdir(p) or d.startswith("1 SK00"): continue
    m=CODE.match(d); code=norm(m.group(1)) if m else None
    cands=[]
    if code in numset: cands.append(("name",code))
    if d.strip() in link2num: cands.append(("csvlink",link2num[d.strip()]))
    refs=collections.Counter()
    for dp,_,fs in os.walk(p):
        for f in fs:
            for x in REF.findall(f): refs[x.replace("_",".",1).replace("_",".")]+=1
    for x,n in refs.most_common(3):
        if x in numset: cands.append(("fileref",x))
    folders.append({"folder":d,"code":code,"cands":cands,"refs":refs.most_common(4)})
json.dump(folders,open(OUT+"/folders.json","w"),ensure_ascii=False,indent=1)
ok=[f for f in folders if f["cands"]]
print("folders",len(folders),"matched",len(ok))
for f in folders:
    if not f["cands"]: print("  NO MATCH:",f["folder"],f["refs"])
multi=[f for f in folders if len({c[1] for c in f["cands"]})>1]
print("ambiguous",len(multi))
for f in multi[:40]: print("  ",f["folder"][:50],sorted({c[1] for c in f["cands"]}))
