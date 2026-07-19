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
            return redirect(url_for("me.pin" if a["must_change"] else "me.index"))
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
            return redirect(url_for("me.index"))
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
                           punches=punches, sch=sch, tc=tc)


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
                           prev=prev, nxt=nxtm)


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
