"""Employee mobile time clock — the /me/ portal (installable PWA).

Employees sign in with company + badge + PIN (emp_auth, separate from back-office
users), tap Time In / Time Out, and see their own attendance. Every tap is recorded
immutably in punchlog (server time is authoritative, Philippine time), then folded
into the legacy pipeline via attendance_engine.rebuild_punch_day.

The staff login guard in app.py skips this blueprint; _gate() below is the
employee-session gate instead.
"""
from __future__ import annotations

import datetime
import time
from zoneinfo import ZoneInfo

from flask import (Blueprint, Response, abort, flash, jsonify, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash

import attendance_engine as ae
from db import q, one, execute

bp = Blueprint("me", __name__, url_prefix="/me")

PH = ZoneInfo("Asia/Manila")
OVERNIGHT_HOURS = 14           # an OUT within this many hours of an open IN closes that day


def now_ph() -> datetime.datetime:
    return datetime.datetime.now(PH)


@bp.before_request
def _gate():
    if request.endpoint in ("me.login", "me.manifest_json", "me.sw_js"):
        return
    m = session.get("me")
    if not m:
        return redirect(url_for("me.login"))
    if m.get("must_change") and request.endpoint not in ("me.pin", "me.logout"):
        return redirect(url_for("me.pin"))


def _employee(company: str, emp_id: str):
    return one("SELECT RTRIM(lastname)||', '||RTRIM(COALESCE(firstname,'')) AS empname, "
               "RTRIM(COALESCE(empsts,'')) AS empsts FROM personnel "
               "WHERE company=? AND RTRIM(emp_id)=?", company, emp_id)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    companies = q("SELECT RTRIM(company) AS co, RTRIM(companynam) AS nam FROM company ORDER BY company")
    if request.method == "POST":
        company = (request.form.get("company") or "").strip()
        emp_id = (request.form.get("emp_id") or "").strip()
        pin = request.form.get("pin") or ""
        a = one("SELECT pin_hash, must_change, active FROM emp_auth "
                "WHERE company=? AND RTRIM(emp_id)=?", company, emp_id)
        p = _employee(company, emp_id)
        if (a and a["active"] and p and p["empsts"] != "X"
                and check_password_hash(a["pin_hash"], pin)):
            session["me"] = {"co": company, "emp": emp_id, "name": p["empname"],
                             "must_change": bool(a["must_change"])}
            return redirect(url_for("me.pin" if a["must_change"] else "me.profile"))
        time.sleep(0.5)                       # slow the guessing down a little
        error = "Wrong badge number or PIN — or the mobile clock isn't enabled for you yet (ask HR)."
    return render_template("me_login.html", companies=companies, error=error)


@bp.route("/logout")
def logout():
    session.pop("me", None)
    return redirect(url_for("me.login"))


@bp.route("/pin", methods=["GET", "POST"])
def pin():
    m = session["me"]
    error = None
    if request.method == "POST":
        p1, p2 = request.form.get("pin1") or "", request.form.get("pin2") or ""
        if not (p1.isdigit() and 4 <= len(p1) <= 8):
            error = "The PIN must be 4 to 8 digits."
        elif p1 != p2:
            error = "The two entries don't match."
        else:
            from auth import hash_password
            execute("UPDATE emp_auth SET pin_hash=?, must_change=false, changed_at=? "
                    "WHERE company=? AND RTRIM(emp_id)=?",
                    hash_password(p1), datetime.datetime.now(), m["co"], m["emp"])
            m["must_change"] = False
            session["me"] = m
            flash("PIN changed. Keep it to yourself.", "ok")
            return redirect(url_for("me.profile"))
    return render_template("me_pin.html", me=m, error=error, forced=m.get("must_change"))


def _assign_day(company: str, emp_id: str, now: datetime.datetime):
    """Which attendance day a punch belongs to, and whether it's an IN or an OUT.
    A punch shortly after midnight closes yesterday's open IN (night shifts)."""
    d = now.date()
    last = one("SELECT local_date, kind, punch_at FROM punchlog WHERE company=? AND emp_id=? "
               "ORDER BY punch_at DESC, id DESC LIMIT 1", company, emp_id)
    if (last and last["kind"] == "IN" and last["local_date"] < d
            and (now - last["punch_at"].astimezone(PH)).total_seconds() <= OVERNIGHT_HOURS * 3600):
        d = last["local_date"]
    n = one("SELECT COUNT(*) AS n FROM punchlog WHERE company=? AND emp_id=? AND local_date=?",
            company, emp_id, d.isoformat())["n"]
    return d, ("OUT" if int(n) % 2 else "IN")


@bp.route("/", methods=["GET"])
def index():
    m = session["me"]
    now = now_ph()
    day, next_kind = _assign_day(m["co"], m["emp"], now)
    punches = q("SELECT local_hhmm, kind, punch_at, lat FROM punchlog "
                "WHERE company=? AND emp_id=? AND local_date=? ORDER BY punch_at, id",
                m["co"], m["emp"], day.isoformat())
    sch = ae.schedule(m["co"], m["emp"], day)
    tc = one("SELECT tlhours, reghrs, tardy, undertime, nphrs FROM timecard "
             "WHERE company=? AND emp_id=? AND trdate=?", m["co"], m["emp"], day.isoformat())
    return render_template("me_clock.html", me=m, now=now, day=day, next_kind=next_kind,
                           punches=punches, sch=sch, tc=tc, active="clock")


@bp.route("/punch", methods=["POST"])
def punch():
    m = session["me"]
    now = now_ph()
    day, kind = _assign_day(m["co"], m["emp"], now)

    def _f(name, lo, hi):
        try:
            v = float(request.form.get(name, ""))
            return v if lo <= v <= hi else None
        except (TypeError, ValueError):
            return None

    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
          or request.remote_addr or "")[:45]
    execute("INSERT INTO punchlog (company, emp_id, punch_at, local_date, local_hhmm, kind, "
            "lat, lng, accuracy, ip, ua) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            m["co"], m["emp"], now, day.isoformat(), now.hour * 100 + now.minute, kind,
            _f("lat", -90, 90), _f("lng", -180, 180), _f("acc", 0, 99999),
            ip, (request.user_agent.string or "")[:200])
    ae.rebuild_punch_day(m["co"], m["emp"], day, user=m["emp"])
    flash(f"Timed {kind} at {now:%H:%M}.", "ok")
    if (request.form.get("back") or "").strip() == "profile":
        return redirect(url_for("me.profile", att=1))
    return redirect(url_for("me.index"))


@bp.route("/attendance")
def attendance():
    m = session["me"]
    today = now_ph().date()
    try:
        ym = request.args.get("month") or today.strftime("%Y-%m")
        first = datetime.date.fromisoformat(ym + "-01")
    except ValueError:
        first = today.replace(day=1)
    nxt = (first.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    last = nxt - datetime.timedelta(days=1)

    rows = q("SELECT trdate, timein1, timeout1, timein2, timeout2, tlhours, reghrs, tardy, "
             "undertime, nphrs, othrs, COALESCE(dayoff,'') AS dayoff "
             "FROM timecard WHERE company=? AND emp_id=? AND trdate>=? AND trdate<=? "
             "ORDER BY trdate", m["co"], m["emp"], first.isoformat(), last.isoformat())
    tot = {"days": 0, "hours": 0.0, "tardy": 0, "ot": 0.0}
    for r in rows:
        if r["timein1"]:
            tot["days"] += 1
        tot["hours"] += float(r["tlhours"] or 0)
        tot["tardy"] += int(r["tardy"] or 0)
        tot["ot"] += float(r["othrs"] or 0)
    prev = (first - datetime.timedelta(days=1)).strftime("%Y-%m")
    nxtm = nxt.strftime("%Y-%m") if nxt <= today else None
    return render_template("me_att.html", me=m, rows=rows, first=first, tot=tot,
                           prev=prev, nxt=nxtm, active="att")


CONTACT_FIELDS = [("cellphone", "Cellphone"), ("telno", "Telephone"),
                  ("address1", "Address line 1"), ("address2", "Address line 2"),
                  ("barangay", "Barangay"), ("addrcity", "City / Town"), ("addrprov", "Province"),
                  ("zipcode", "Zip"), ("contactper", "Emergency contact"),
                  ("contactrel", "Relationship"), ("contacttel", "Contact tel."),
                  ("contactadd", "Emergency contact address")]
_WIDTHS: dict = {}


def _contact_widths():
    if not _WIDTHS:
        for r in q("SELECT column_name AS c, character_maximum_length AS n FROM information_schema.columns "
                   "WHERE table_name='personnel' AND character_maximum_length IS NOT NULL"):
            _WIDTHS[r["c"]] = int(r["n"])
    return _WIDTHS


def _profile_row(company, emp_id):
    return one(
        "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(COALESCE(p.firstname,'')) AS fn, "
        "RTRIM(COALESCE(p.middlename,'')) AS mn, RTRIM(p.lastname) AS ln, "
        "RTRIM(COALESCE(j.descrip,'')) AS job, RTRIM(COALESCE(d.descrip,'')) AS dept, "
        "RTRIM(COALESCE(p.empsts,'')) AS sts, p.datehired, p.datereg, p.birthdate, "
        "RTRIM(COALESCE(p.sex,'')) AS sex, RTRIM(COALESCE(p.civilsts,'')) AS civilsts, "
        "RTRIM(COALESCE(p.nationality,'')) AS nationality, RTRIM(COALESCE(p.bloodtype,'')) AS bloodtype, "
        "RTRIM(COALESCE(p.religion,'')) AS religion, "
        "RTRIM(COALESCE(p.cellphone,'')) AS cellphone, RTRIM(COALESCE(p.telno,'')) AS telno, "
        "RTRIM(COALESCE(p.address1,'')) AS address1, RTRIM(COALESCE(p.address2,'')) AS address2, "
        "RTRIM(COALESCE(p.barangay,'')) AS barangay, "
        "RTRIM(COALESCE(p.addrcity,'')) AS addrcity, RTRIM(COALESCE(p.addrprov,'')) AS addrprov, "
        "RTRIM(COALESCE(p.zipcode,'')) AS zipcode, RTRIM(COALESCE(p.sssno,'')) AS sssno, "
        "RTRIM(COALESCE(p.tin,'')) AS tin, RTRIM(COALESCE(p.phealthno,'')) AS phealthno, "
        "RTRIM(COALESCE(p.hdmfno,'')) AS hdmfno, RTRIM(COALESCE(p.contactper,'')) AS contactper, "
        "RTRIM(COALESCE(p.contactrel,'')) AS contactrel, RTRIM(COALESCE(p.contacttel,'')) AS contacttel, "
        "RTRIM(COALESCE(p.contactadd,'')) AS contactadd, "
        "(p.emppic IS NOT NULL) AS has_pic "
        "FROM personnel p "
        "LEFT JOIN jobcode j ON j.company=p.company AND j.code=p.jobcode "
        "LEFT JOIN department d ON d.company=p.company AND d.code=p.dept "
        "WHERE p.company=? AND RTRIM(p.emp_id)=?", company, emp_id)


def _haversine_m(lat1, lng1, lat2, lng2):
    import math
    r = 6371000.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp = p2 - p1
    dl = math.radians(float(lng2) - float(lng1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _hhmm_str(v):
    v = int(v)
    return f"{v // 100:02d}:{v % 100:02d}"


def _att_state(m):
    """Today's punch picture for the Quick Actions dialog (status, times, locations)."""
    now = now_ph()
    day, next_kind = _assign_day(m["co"], m["emp"], now)
    punches = q("SELECT local_hhmm, kind, lat, lng, accuracy FROM punchlog "
                "WHERE company=? AND emp_id=? AND local_date=? ORDER BY punch_at, id",
                m["co"], m["emp"], day.isoformat())
    first_in = next((p for p in punches if p["kind"] == "IN"), None)
    last_out = next((p for p in reversed(punches) if p["kind"] == "OUT"), None)

    def mins(h):
        h = int(h)
        return (h // 100) * 60 + h % 100

    dur = ""
    if first_in:
        start = mins(first_in["local_hhmm"])
        end = (mins(last_out["local_hhmm"]) if last_out and next_kind == "IN"
               else now.hour * 60 + now.minute)
        if end < start:
            end += 1440
        dur = f"{(end - start) // 60}h {(end - start) % 60:02d}m"
    dist = None
    if (first_in and last_out and first_in["lat"] is not None and last_out["lat"] is not None):
        dist = round(_haversine_m(first_in["lat"], first_in["lng"],
                                  last_out["lat"], last_out["lng"]))
    return {"day": day, "carry": day != now.date(), "next_kind": next_kind,
            "active": next_kind == "OUT", "punches": punches,
            "time_in": _hhmm_str(first_in["local_hhmm"]) if first_in else "",
            "time_out": _hhmm_str(last_out["local_hhmm"]) if last_out and next_kind == "IN" else "",
            "dur": dur, "dist": dist}


def _code_desc(tbl, code):
    if not code:
        return ""
    r = one("SELECT RTRIM(descrip) AS d FROM tablecode1 WHERE tblcode=? AND RTRIM(fldcode)=?", tbl, code)
    return r["d"] if r else code


def _digits(v):
    return "".join(ch for ch in (v or "") if ch.isdigit())


def _fmt_id(v, groups):
    """Dash-format a government ID when the digit count matches (e.g. TIN 3-3-3-3)."""
    d = _digits(v)
    if len(d) != sum(groups):
        return (v or "").strip()
    out, i = [], 0
    for g in groups:
        out.append(d[i:i + g])
        i += g
    return "-".join(out)


@bp.route("/profile")
def profile():
    m = session["me"]
    p = _profile_row(m["co"], m["emp"])
    if not p:
        abort(404)
    fullname = " ".join(x for x in (p["fn"], p["mn"], p["ln"]) if x)
    initials = ((p["fn"][:1] or "") + (p["ln"][:1] or "")).upper() or p["emp_id"][:2]
    addr = ", ".join(x for x in (p["address1"], p["address2"], p["barangay"],
                                 p["addrcity"], p["addrprov"]) if x)
    if p["zipcode"]:
        addr = (addr + " " + p["zipcode"]).strip()
    comp = one("SELECT RTRIM(companynam) AS n FROM company WHERE RTRIM(company)=?", m["co"])

    pay = one("SELECT COALESCE(salary,0) AS salary, RTRIM(COALESCE(paytype,'')) AS pt "
              "FROM payroll WHERE company=? AND RTRIM(emp_id)=?", m["co"], m["emp"])
    allow = one("SELECT COALESCE(SUM(amount * CASE WHEN RTRIM(COALESCE(freq,''))='9' THEN 2 ELSE 1 END),0) AS a "
                "FROM fixallow WHERE company=? AND RTRIM(emp_id)=?", m["co"], m["emp"])
    gov = {"tin": _fmt_id(p["tin"], (3, 3, 3, 3)) or _fmt_id(p["tin"], (3, 3, 3)),
           "sss": _fmt_id(p["sssno"], (2, 7, 1)),
           "phic": _fmt_id(p["phealthno"], (2, 9, 1)),
           "hdmf": _fmt_id(p["hdmfno"], (4, 4, 4))}
    personal = {"birthdate": p["birthdate"],
                "gender": {"M": "Male", "F": "Female"}.get(p["sex"], p["sex"]),
                "civil": _code_desc("CST", p["civilsts"]),
                "nat": _code_desc("NAT", p["nationality"]),
                "blood": p["bloodtype"],
                "religion": _code_desc("RLG", p["religion"])}
    return render_template("me_profile.html", me=m, p=p, fullname=fullname, initials=initials,
                           status=_code_desc("EST", p["sts"]), addr=addr,
                           rel=_code_desc("REL", p["contactrel"]),
                           compname=(comp["n"] if comp else m["co"]),
                           pay=pay, allow=float(allow["a"] or 0), gov=gov, personal=personal,
                           att=_att_state(m), open_att=bool(request.args.get("att")),
                           active="profile")


@bp.route("/photo")
def photo():
    m = session["me"]
    r = one("SELECT emppic, RTRIM(COALESCE(emppicext,'jpg')) AS ext FROM personnel "
            "WHERE company=? AND RTRIM(emp_id)=?", m["co"], m["emp"])
    if not r or not r["emppic"]:
        abort(404)
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "bmp": "image/bmp", "gif": "image/gif"}.get(r["ext"].lower(), "application/octet-stream")
    return Response(bytes(r["emppic"]), mimetype=mime,
                    headers={"Cache-Control": "private, max-age=3600"})


@bp.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    """Self-service for the employee's own contact details — nothing else is editable here."""
    m = session["me"]
    p = _profile_row(m["co"], m["emp"])
    if not p:
        abort(404)
    error = None
    if request.method == "POST":
        w = _contact_widths()
        vals, errs = {}, []
        for f, label in CONTACT_FIELDS:
            v = (request.form.get(f) or "").strip()
            if f in w and len(v) > w[f]:
                errs.append(f"{label} is too long (max {w[f]} characters).")
            vals[f] = v
        if errs:
            error = " ".join(errs)
        else:
            sets = ",".join(f"{f}=?" for f, _ in CONTACT_FIELDS)
            execute(f"UPDATE personnel SET {sets},changeby=?,changedate=? "
                    "WHERE company=? AND RTRIM(emp_id)=?",
                    *[vals[f] for f, _ in CONTACT_FIELDS], m["emp"],
                    datetime.datetime.now(), m["co"], m["emp"])
            flash("Contact details updated.", "ok")
            return redirect(url_for("me.profile"))
    rels = q("SELECT RTRIM(fldcode) AS code, RTRIM(descrip) AS descrip FROM tablecode1 "
             "WHERE tblcode='REL' AND RTRIM(fldcode)<>'' ORDER BY descrip")
    f = request.form if request.method == "POST" else p
    return render_template("me_profile_edit.html", me=m, f=f, rels=rels, error=error,
                           widths=_contact_widths(), active="profile")


PP_LABEL = {"1": "1st half", "2": "2nd half", "X": "special"}


@bp.route("/compensation")
def compensation():
    """My Compensation — salary structure, annual package and the deductions the
    payroll engine would take THIS month from the current setup (statutory tables,
    allowances, active loans). Estimates, clearly labeled; payslips stay authoritative."""
    m = session["me"]
    pay = one("SELECT COALESCE(salary,0) AS salary, RTRIM(COALESCE(paytype,'')) AS paytype "
              "FROM payroll WHERE company=? AND RTRIM(emp_id)=?", m["co"], m["emp"])
    salary = float(pay["salary"]) if pay else 0.0
    pt = (pay["paytype"] if pay else "") or "M"
    allow = one("SELECT COALESCE(SUM(amount * CASE WHEN RTRIM(COALESCE(freq,''))='9' THEN 2 ELSE 1 END),0) AS a "
                "FROM fixallow WHERE company=? AND RTRIM(emp_id)=?", m["co"], m["emp"])
    allow_m = float(allow["a"] or 0)

    if pt == "D":
        import payroll_engine as pe
        try:
            equiv = round(salary * float(pe.coparam(m["co"])["baseday"]), 2)
        except Exception:
            equiv = round(salary * 26.0, 2)
    else:
        equiv = salary
    annual = {"base": round(equiv * 12, 2), "allow": round(allow_m * 12, 2),
              "thirteenth": round(equiv, 2)}
    annual["total"] = round(annual["base"] + annual["allow"] + annual["thirteenth"], 2)

    today = now_ph().date()
    monthly, others = None, []
    try:
        import payroll_calc
        agg = {"gross": 0.0, "sss": 0.0, "phic": 0.0, "hdmf": 0.0, "tax": 0.0,
               "total": 0.0, "net": 0.0}
        oth = {}
        for per in ("1", "2"):
            r = payroll_calc.compute(m["co"], m["emp"], today.year, today.month, per)
            agg["gross"] += r["gross"]
            agg["tax"] += r["tax"]
            agg["total"] += r["total_ded"]
            agg["net"] += r["net"]
            for l in r["deductions"]:
                code = (l.get("payitem") or "").strip()
                if code == "402":
                    agg["sss"] += float(l["amount"])
                elif code == "403":
                    agg["phic"] += float(l["amount"])
                elif code == "404":
                    agg["hdmf"] += float(l["amount"])
                elif code != "401":                      # 401 (tax) already in agg["tax"]
                    d = l.get("descrip") or code
                    oth[d] = oth.get(d, 0.0) + float(l["amount"])
        monthly = {k: round(v, 2) for k, v in agg.items()}
        others = sorted(({"descrip": k, "amount": round(v, 2)} for k, v in oth.items()),
                        key=lambda x: -x["amount"])
    except Exception:
        pass                                             # no payroll setup yet — structure still shows

    latest = one("SELECT payyear, paymonth, RTRIM(payperiod) AS pp, "
                 "SUM(CASE WHEN RTRIM(payitem)='903' THEN tramount ELSE 0 END) AS net "
                 "FROM paytranh WHERE company=? AND RTRIM(emp_id)=? "
                 "GROUP BY payyear, paymonth, payperiod "
                 "ORDER BY payyear DESC, paymonth DESC, payperiod DESC LIMIT 1", m["co"], m["emp"])
    latest_label = ""
    if latest:
        latest_label = (f"{datetime.date(int(latest['payyear']), int(latest['paymonth']), 1):%b %Y}"
                        f" · {PP_LABEL.get(latest['pp'], latest['pp'])}")
    return render_template("me_comp.html", me=m, pt=pt, salary=salary, allow=allow_m,
                           equiv=equiv, total_monthly=round(equiv + allow_m, 2),
                           annual=annual, monthly=monthly, others=others,
                           latest=latest, latest_label=latest_label,
                           month_name=today.strftime("%B %Y"), active="comp")


@bp.route("/manifest.json")
def manifest_json():
    return jsonify({
        "name": "L98 Time Clock", "short_name": "Time Clock",
        "start_url": "/me/", "scope": "/me/", "display": "standalone",
        "background_color": "#f7f3e8", "theme_color": "#20242c",
        "icons": [{"src": "/static/clock-icon.svg", "sizes": "any",
                   "type": "image/svg+xml", "purpose": "any"}],
    })


@bp.route("/sw.js")
def sw_js():
    js = """
const SHELL = ['/static/me.css', '/static/clock-icon.svg'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open('me-v1').then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;                       // punches always hit the network
  e.respondWith(
    fetch(e.request).catch(() =>
      caches.match(e.request).then(hit => hit ||
        new Response('<meta name=viewport content="width=device-width">' +
          '<body style="font-family:sans-serif;padding:2em;text-align:center">' +
          '<h2>No connection</h2><p>Reconnect and try again — your punch was not recorded.</p>',
          {headers: {'Content-Type': 'text/html'}})))
  );
});
"""
    return Response(js, mimetype="text/javascript")
