#!/usr/bin/env python3
"""Put a few demonstration projects into the calculator database.

    CALC_EMAIL=you@litprofit.com CALC_PASSWORD=... python3 tools/seed-demo.py
    CALC_EMAIL=... CALC_PASSWORD=... python3 tools/seed-demo.py --remove

Every project it writes has a `DEMO-` project number, which is the whole
safety mechanism: --remove deletes exactly those and can never touch a real
job. Nothing else identifies them, so a demo project renamed to a real number
stops being demo data and stops being deletable by this script -- which is the
right way round.

The project URL and publishable key are read out of the built calculator page
rather than passed in. They are public by design and, more to the point, that
guarantees this writes to the same project the published page reads from.
The password is not: it comes from the environment, like every other
credential here.
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "calculator", "index.html")

BURDEN, ALLOWANCE, ADMIN, CONTINGENCY, TARGET = 0.35, 60, 0.08, 0.05, 0.20


def config():
    if not os.path.exists(PAGE):
        sys.exit("calculator/index.html not found — run tools/build-calc.py first.")
    html = io.open(PAGE, encoding="utf-8").read()
    url = re.search(r"const API = '([^']*)'", html)
    key = re.search(r"const KEY = '([^']*)'", html)
    if not (url and key and url.group(1).startswith("http")):
        sys.exit("The built calculator has no database configured.\n"
                 "Build it with CALC_SUPABASE_URL and CALC_SUPABASE_KEY first.")
    return url.group(1).rstrip("/"), key.group(1)


def api(url, key, token, method, path, body=None):
    """Through curl, not urllib.

    A python.org install on macOS commonly ships without a CA bundle, and
    urllib then fails every HTTPS call with CERTIFICATE_VERIFY_FAILED -- an
    error about certificates, for a script about demo data, on a machine where
    the network is fine. curl uses the system keychain and is already there."""
    cmd = ["curl", "-sS", "--max-time", "40", "-X", method, url + path,
           "-H", "apikey: " + key,
           "-H", "Authorization: Bearer " + (token or key),
           "-H", "Content-Type: application/json",
           "-H", "Prefer: return=representation",
           "-w", "\n%{http_code}"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode:
        sys.exit("Could not reach the database:\n" + out.stderr.strip())
    text, _, code = out.stdout.rpartition("\n")
    if code == "403" and "manager" in text:
        sys.exit("That account is staff. Creating and deleting projects needs a\n"
                 "manager or admin -- set the role in profiles, or use another login.")
    if not code.isdigit() or int(code) >= 400:
        sys.exit("%s %s failed (HTTP %s):\n%s" % (method, path, code, text[:300]))
    return json.loads(text) if text.strip() else []


def sign_in(url, key):
    email, password = os.environ.get("CALC_EMAIL"), os.environ.get("CALC_PASSWORD")
    if not (email and password):
        sys.exit("CALC_EMAIL and CALC_PASSWORD must be set.\n"
                 "Use a MANAGER or ADMIN account -- creating and deleting a\n"
                 "project is refused for staff, by the database, not by this script.")
    out = api(url, key, None, "POST", "/auth/v1/token?grant_type=password",
              {"email": email, "password": password})
    if "access_token" not in out:
        sys.exit("Sign-in refused. Check the email and password.")
    return out["access_token"]


# ---------- row builders, matching emptyRow() in the app exactly ----------
def rev(cat, desc, plan, actual, status="approved", invoice="", paid=False):
    return {"cat": cat, "desc": desc, "plan": plan, "actual": actual,
            "status": status, "invoice": invoice, "paid": paid}


def lab(name, role, days, hours, rate, travel_days, actual):
    return {"name": name, "role": role, "days": days, "hours": hours,
            "rate": rate, "travelDays": travel_days, "actual": actual}


def sub(name, scope, hours, rate, travel, accom, materials, other, actual):
    return {"name": name, "scope": scope, "hours": hours, "rate": rate,
            "travel": travel, "accom": accom, "materials": materials,
            "other": other, "actual": actual}


def trv(kind, desc, qty, unit, actual, supplier):
    return {"type": kind, "desc": desc, "qty": qty, "unit": unit,
            "actual": actual, "supplier": supplier}


def mat(cat, desc, qty, unit, actual, rebill=False, rebill_amt=None):
    return {"cat": cat, "desc": desc, "qty": qty, "unit": unit,
            "actual": actual, "rebill": rebill, "rebillAmt": rebill_amt}


def log(cat, desc, plan, actual, recoverable=False, rebill=None, notes=""):
    return {"cat": cat, "desc": desc, "plan": plan, "actual": actual,
            "recoverable": recoverable, "rebill": rebill, "notes": notes}


def project(pid, client, site, pm, start, end, currency, contract, advance,
            terms, locked, revenue, labor, subs, travel, materials, logistics):
    return {
        "settings": {"currency": currency, "burden": BURDEN, "allowance": ALLOWANCE,
                     "contingency": CONTINGENCY, "admin": ADMIN, "targetMargin": TARGET},
        "card": {"projectId": pid, "client": client, "site": site, "pm": pm,
                 "start": start, "end": end, "contract": contract,
                 "advance": advance, "terms": terms},
        "locked": locked,
        "revenue": revenue, "labor": labor, "subs": subs,
        "travel": travel, "materials": materials, "logistics": logistics,
    }


# Four jobs that between them exercise everything the dashboard and the two
# reports can show: two comfortably on target, one losing most of its margin to
# a subcontractor overrun, one closed, and one in another currency so the
# per-currency totals have something to separate.
#
# The figures are built from the cost side and hold together: labour actuals
# sit within a few per cent of hours x rate x (1 + burden) + travel allowance,
# which is what a real sheet looks like. A demo that shows a crew costing seven
# times its own rate teaches people to distrust the tool.
DEMOS = [
    project(
        "DEMO-01", "Sealord", "M/V BALTIC PRIDE", "R. Fedotovas",
        "2026-02-02", "2026-03-13", "EUR", 53000, 15900, 45, False,
        revenue=[
            rev("Refrigeration", "Provision plant overhaul", 40000, 41000, "invoiced", "2026-0141", True),
            rev("Refrigeration", "Compressor replacement", 7800, 7500, "invoiced", "2026-0142", True),
            rev("Service", "Sea trial attendance", 1600, 1600, "approved", "", False),
        ],
        labor=[
            lab("Vytautas Petrauskas", "Refrigeration engineer", 28, 224, 34, 6, 11280),
            lab("Tomas Jankauskas", "Welder", 18, 144, 29, 4, 5470),
            lab("Andrius Kazlauskas", "Fitter", 22, 176, 27, 6, 6910),
        ],
        subs=[sub("Baltic Weld", "Pipe prefabrication", 96, 42, 0, 0, 1800, 0, 6100)],
        travel=[trv("Accommodation", "Crew, Klaipeda", 34, 62, 2180, "Hotel Navalis")],
        materials=[
            mat("Refrigerant", "R404A, 60 kg", 60, 21, 1290, True, 1550),
            mat("Spare parts", "BITZER valve set", 4, 640, 2610, False, None),
        ],
        logistics=[log("Freight", "Parts from BITZER, DE", 1400, 1520, True, 1520, "Rebilled to client")],
    ),
    project(
        "DEMO-02", "Seafish Trade", "M/V NERINGA", "R. Fedotovas",
        "2026-03-09", "2026-04-24", "EUR", 72000, 21600, 45, False,
        revenue=[
            rev("Engine repair", "Main engine top overhaul", 61000, 62000, "invoiced", "2026-0155", False),
            rev("Service", "Alignment check", 7400, 6900, "approved", "", False),
        ],
        labor=[
            lab("Mindaugas Urbonas", "Engine fitter", 30, 240, 31, 8, 11160),
            lab("Darius Sakalauskas", "Mechanic", 24, 192, 28, 8, 7200),
        ],
        # the overrun: scope grew on board and both subcontractors stayed longer
        subs=[
            sub("Klaipeda Machining", "Crankshaft grinding", 120, 55, 900, 1400, 3200, 0, 18900),
            sub("Nord Diesel", "Injector testing", 40, 61, 1200, 900, 0, 0, 9800),
        ],
        travel=[trv("Flights", "Specialist, Rotterdam", 2, 340, 940, "Air Baltic")],
        materials=[mat("Spare parts", "Liner and ring set", 6, 1150, 7420, False, None)],
        logistics=[log("Port charges", "Berth and crane", 3800, 5200, False, None, "Two extra crane days")],
    ),
    project(
        "DEMO-03", "Limarko Group", "M/V VENTA", "R. Fedotovas",
        "2025-11-10", "2025-12-19", "EUR", 29000, 8700, 30, True,
        revenue=[
            rev("Hull & piping", "Ballast line renewal", 25800, 26200, "invoiced", "2025-0388", True),
            rev("Service", "Class attendance", 2500, 2500, "invoiced", "2025-0389", True),
        ],
        labor=[
            lab("Tomas Jankauskas", "Welder", 20, 160, 29, 0, 6640),
            lab("Andrius Kazlauskas", "Fitter", 16, 128, 27, 0, 4340),
        ],
        subs=[sub("Baltic Weld", "Pipe spools", 72, 42, 0, 0, 1200, 0, 4300)],
        travel=[],
        materials=[mat("Steel", "Seamless pipe, 6 m", 48, 96, 4520, False, None)],
        logistics=[log("Freight", "Material delivery", 700, 680, False, None, "")],
    ),
    project(
        "DEMO-04", "Ocean Whale Company", "M/V AUDRA", "R. Fedotovas",
        "2026-04-06", "", "USD", 48000, 0, 60, False,
        revenue=[
            rev("Spare parts", "DANFOSS controls package", 34000, 34000, "invoiced", "2026-0163", False),
            rev("Service", "Commissioning, 1 engineer", 12500, 11000, "pending", "", False),
        ],
        labor=[lab("Vytautas Petrauskas", "Refrigeration engineer", 12, 96, 34, 10, 5310)],
        subs=[],
        travel=[
            trv("Flights", "Crew, Las Palmas", 2, 780, 1690, "Iberia"),
            trv("Accommodation", "Crew, 12 nights", 12, 95, 1210, "Local agent"),
        ],
        # bought at cost and sold on the revenue sheet, so it is NOT also
        # rebilled here -- that would count the same parts as income twice
        materials=[mat("Spare parts", "DANFOSS valves and controllers", 1, 24800, 24800, False, None)],
        logistics=[log("Freight", "Air freight to vessel", 2600, 3050, True, 3050, "Rebilled to client")],
    ),
]


def main():
    url, key = config()
    token = sign_in(url, key)
    remove = "--remove" in sys.argv

    # projects_v and the RPCs, because public.projects is revoked from the
    # app -- and creating or deleting a project now needs manager or admin.
    existing = api(url, key, token, "GET",
                   "/rest/v1/projects_v?select=id,project_id&project_id=like.DEMO-*")
    if remove:
        if not existing:
            print("No DEMO- projects to remove.")
            return
        for row in existing:
            api(url, key, token, "POST", "/rest/v1/rpc/delete_project",
                {"p_id": row["id"]})
            print("removed  %s" % row["project_id"])
        print("\n%d demo project(s) removed. Real jobs are untouched." % len(existing))
        return

    if existing:
        print("These are already there — remove them first if you want them rebuilt:")
        for row in existing:
            print("  %s" % row["project_id"])
        print("\n  CALC_EMAIL=... CALC_PASSWORD=... python3 tools/seed-demo.py --remove")
        return

    for p in DEMOS:
        api(url, key, token, "POST", "/rest/v1/rpc/create_project", {"p_data": p})
        d = summarise(p)
        print("added    %-8s %-22s %s%s  margin %5.1f%%  %s"
              % (p["card"]["projectId"], p["card"]["client"],
                 fmt(d["rev"]), p["settings"]["currency"], d["margin"] * 100,
                 "closed" if p["locked"] else "open"))
    print("\n%d demo projects added. Remove them with --remove." % len(DEMOS))


def fmt(v):
    return "{:,.0f} ".format(v)


def summarise(p):
    """The app's own arithmetic, so the printed margins are the ones it shows."""
    n = lambda v: float(v or 0)
    s = p["settings"]
    revenue = (sum(n(r["actual"]) for r in p["revenue"])
               + sum(n(r["rebillAmt"]) for r in p["materials"])
               + sum(n(r["rebill"]) for r in p["logistics"]))
    direct = (sum(n(r["actual"]) for r in p["labor"])
              + sum(n(r["actual"]) for r in p["subs"])
              + sum(n(r["actual"]) for r in p["travel"])
              + sum(n(r["actual"]) for r in p["materials"])
              + sum(n(r["actual"]) for r in p["logistics"]))
    cost = direct * (1 + n(s["admin"]))
    return {"rev": revenue, "cost": cost,
            "margin": (revenue - cost) / revenue if revenue else 0}


if __name__ == "__main__":
    main()
