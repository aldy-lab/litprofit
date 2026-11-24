"""Load manifest.json into the calculator's database, without a browser.

Run through tools/import-sales.sh, which takes the project URL and the
service_role key out of the keychain and hands them over in the environment;
nothing here prints or stores them. The service role is what lets this write
past row level security, so it is only ever run by a person at the office Mac.

1. creates the enquiries the register does not have yet (the manifest's
   `create`), unless a row with that number already exists;
2. inserts one enquiry_records row per document, ignoring ones already there
   (unique enquiry_id + sha256), so it can be run again;
3. fills invoice_no on enquiries that have none, from Litprofit's invoice
   numbers found in their folders (LIT1869, LIT1874 ...).

    python3 4_load.py manifest.json"""
import json, os, sys, ssl, urllib.request, urllib.error, collections

# The python.org build of Python ships without CA certificates until its
# "Install Certificates" step is run, and then every HTTPS call fails with
# CERTIFICATE_VERIFY_FAILED. Use certifi when it is there, else the bundle
# macOS keeps at /etc/ssl/cert.pem.
CTX = ssl.create_default_context()
try:
    import certifi
    CTX.load_verify_locations(certifi.where())
except ImportError:
    if os.path.exists("/etc/ssl/cert.pem"):
        CTX.load_verify_locations("/etc/ssl/cert.pem")

URL = os.environ.get("CALC_REST") or os.environ["CALC_URL"].rstrip("/") + "/rest/v1/"   # CALC_REST: tests only
KEY = os.environ["CALC_KEY"]
H = {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json"}

def call(method, path, body=None, prefer=None):
    h = dict(H)
    if prefer: h["Prefer"] = prefer
    req = urllib.request.Request(URL + path, method=method, headers=h,
                                 data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
            t = r.read().decode()
            return json.loads(t) if t else None
    except urllib.error.HTTPError as e:
        raise SystemExit("%s %s -> %s %s" % (method, path.split("?")[0], e.code, e.read().decode()[:300]))

M = json.load(open(sys.argv[1]))
try:
    call("GET", "enquiry_records?select=id&limit=1")
except SystemExit as e:
    raise SystemExit("The enquiry_records table is not there yet: run apply-1-records-and-duplicates.sql "
                     "in the Supabase SQL editor first.\n" + str(e))

def enquiries():
    rows = []
    while True:   # PostgREST hands out at most max-rows per request
        part = call("GET", "enquiries?select=id,number,invoice_no&order=id&limit=1000&offset=%d" % len(rows)) or []
        rows += part
        if len(part) < 1000: break
    by = {}
    for r in rows:
        by.setdefault((r["number"] or "").strip(), r)
    return by

by = enquiries()
created = 0
for num, info in M["enquiries"].items():
    if num in by or not info.get("create"): continue
    row = dict(info["create"]); row["number"] = num
    call("POST", "enquiries", [row], prefer="return=minimal"); created += 1
by = enquiries()

recs, missing = [], collections.Counter()
for e in M["entries"]:
    tgt = by.get(e["enquiry"])
    if not tgt: missing[e["enquiry"]] += 1; continue
    note = e.get("note") or ""
    mail = "Laiškas: " in note
    name = e["rel"].split("/")[-1]
    title = note.split("Laiškas: ", 1)[1].split(" — priedai: ")[0] if mail else name
    detail = " · ".join(x for x in [
        ("Failas: " + name) if mail else (e.get("label") or ""),
        ("Priedai: " + note.split(" — priedai: ", 1)[1]) if mail and " — priedai: " in note else ""] if x)
    recs.append({"enquiry_id": tgt["id"], "sha256": e["sha256"], "kind": e.get("kind") or "other",
                 "doc_date": e.get("doc_date"), "ref": e.get("ref"), "amount": e.get("amount"),
                 "counterparty": e.get("counterparty"), "title": title[:500], "detail": detail[:2000],
                 "source": e["rel"][:600], "copies": 1 + len(e.get("copies") or [])})
for i in range(0, len(recs), 500):
    call("POST", "enquiry_records?on_conflict=enquiry_id,sha256", recs[i:i + 500],
         prefer="resolution=ignore-duplicates,return=minimal")
    sys.stdout.write("\r  records %d / %d" % (min(i + 500, len(recs)), len(recs))); sys.stdout.flush()
print()

inv = collections.defaultdict(list)
for e in M["entries"]:
    # "Senas"/"Sena" subfolders keep last year's deal that this one grew out of;
    # its invoices are not this enquiry's
    old = any(p.lower().startswith(("senas", "sena ", "sena-", "sena_")) for p in e["rel"].split("/"))
    if e.get("kind") == "invoice_out" and e.get("ref") and not old and e["ref"] not in inv[e["enquiry"]]:
        inv[e["enquiry"]].append(e["ref"])
filled = 0
for num, refs in inv.items():
    r = by.get(num)
    if r and not (r.get("invoice_no") or "").strip():
        call("PATCH", "enquiries?id=eq." + r["id"], {"invoice_no": ", ".join(sorted(refs))}, prefer="return=minimal")
        filled += 1

def count(path):
    req = urllib.request.Request(URL + path, method="HEAD", headers=dict(H, Prefer="count=exact"))
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        return int((r.headers.get("Content-Range") or "*/0").split("/")[-1])
print("Enquiries created: %d" % created)
print("Document records in the database: %d (manifest: %d)" % (count("enquiry_records?select=id"), len(M["entries"])))
print("Invoice numbers filled in: %d enquiries" % filled)
if missing: print("No enquiry for:", dict(missing))
