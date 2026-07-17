"""HRPayroll L98 — web rebuild of the original PowerBuilder HRIS.

Faithful two-mode application (Payroll + HR) over the restored HRPayroll_L98
database (localhost\\SQLEXPRESS). Read-only: every query is a parameterized SELECT.
Structure mirrors APP_BLUEPRINT.md.
"""
from __future__ import annotations

import datetime
import os
import secrets
from functools import wraps
from flask import (Flask, abort, flash, get_flashed_messages, redirect,
                   render_template, request, session, url_for)

import db
from db import q, one
import auth
import emp_tables

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4 MB file-upload cap
app.teardown_appcontext(db.close_conn)


# ─────────────────────────────────────────────────────────────── CSRF

def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


@app.before_request
def csrf_protect():
    if request.method == "POST":
        if not session.get("csrf") or request.form.get("csrf") != session["csrf"]:
            abort(400, "Invalid or missing CSRF token — reload the page and try again.")


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("user"):
            return redirect(url_for("login", next=request.full_path))
        return view(*a, **kw)
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        uid = (request.form.get("user_id") or "").strip().upper()
        pwd = request.form.get("password") or ""
        u = auth.verify(uid, pwd)
        if u:
            session["user"] = {"id": u["user_id"], "name": u["user_name"]}
            dest = request.args.get("next") or url_for("dashboard")
            return redirect(dest)
        error = "Invalid user ID or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.before_request
def guard():
    if request.endpoint in ("login", "static") or request.path.startswith("/static"):
        return
    if not session.get("user"):
        return redirect(url_for("login", next=request.full_path))


# ─────────────────────────────────────────────────────────── lookups / filters

LOOKUPS: dict = {}


def load_lookups() -> None:
    LOOKUPS["companies"] = q(
        "SELECT company, RTRIM(companynam) AS companynam, RTRIM(COALESCE(shortname,'')) AS shortname "
        "FROM company ORDER BY company"
    )
    LOOKUPS["comp"] = {c["company"]: c["companynam"] for c in LOOKUPS["companies"]}
    LOOKUPS["est"] = {
        (r["fldcode"] or "").strip(): (r["descrip"] or "").strip()
        for r in q("SELECT fldcode, descrip FROM tablecode1 WHERE tblcode='EST'")
    }


STATUS_TONE = {"R": "ok", "P": "warn", "X": "off", "C": "warn", "F": "warn", "U": "warn"}


@app.template_filter("peso")
def peso(v):
    if v is None:
        return ""
    try:
        return f"{float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


@app.template_filter("dt")
def dt(v):
    if v in (None, ""):
        return ""
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.strftime("%d %b %Y")
    return str(v)


@app.template_filter("intf")
def intf(v):
    if v is None or v == "":
        return ""
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return str(v)


@app.template_filter("est")
def est(v):
    v = (v or "").strip()
    return LOOKUPS["est"].get(v, v or "—")


@app.template_filter("tone")
def tone(v):
    return STATUS_TONE.get((v or "").strip(), "warn")


def sel_company():
    c = (request.args.get("company") or "001").strip()
    if c not in LOOKUPS["comp"]:
        c = "001"
    return c


@app.context_processor
def inject():
    from menus import PAYROLL_MENU, HR_MENU
    mode = request.args.get("mode", "PY")
    return {
        "companies": LOOKUPS["companies"], "comp_map": LOOKUPS["comp"],
        "PAYROLL_MENU": PAYROLL_MENU, "HR_MENU": HR_MENU,
        "mode": mode, "company": sel_company(),
        "csrf_token": csrf_token,
    }


# ──────────────────────────────────────────────────────────────────── grids

from grids import GRIDS  # noqa: E402


@app.route("/s/<key>")
def screen(key):
    g = GRIDS.get(key)
    if not g:
        abort(404)
    company = sel_company()
    params = [company] if g.get("company") else []
    rows = q(g["sql"], *params)
    return render_template(
        "grid.html", g=g, rows=rows, key=key,
        title=g["title"], subtitle=g.get("subtitle", ""),
    )


def _cast(v, typ):
    v = (v or "").strip()
    if v == "":
        return None
    if typ == "num":
        try:
            return float(v.replace(",", ""))
        except ValueError:
            return None
    if typ == "int":
        try:
            return int(float(v))
        except ValueError:
            return None
    return v  # text / date (ISO string; Postgres casts)


@app.route("/s/<key>/row", methods=["GET", "POST"])
def grid_row(key):
    g = GRIDS.get(key)
    if not g or not g.get("edit"):
        abort(404)
    e, company = g["edit"], sel_company()
    scoped = bool(g.get("company"))
    user = session.get("user", {}).get("id", "")
    if request.method == "POST":
        data = {c: _cast(request.form.get(c), t) for c, _, t in e["fields"]}
        if request.form.get("_update") == "1":
            where = " AND ".join(f"{c}=?" for c in e["pk"])
            wvals = [company if c == "company" else request.form.get("pk_" + c) for c in e["pk"]]
            setcols = [c for c, _, _ in e["fields"] if c not in e["pk"]]
            sets = ", ".join(f"{c}=?" for c in setcols) + ", changeby=?, changedate=?"
            svals = [data[c] for c in setcols] + [user, datetime.datetime.now()]
            db.execute(f"UPDATE {e['table']} SET {sets} WHERE {where}", *(svals + wvals))
            flash("Record updated.", "ok")
        else:
            cols = [c for c, _, _ in e["fields"]]
            vals = [data[c] for c in cols]
            if scoped and "company" not in cols:
                cols, vals = ["company"] + cols, [company] + vals
            cols += ["changeby", "changedate"]
            vals += [user, datetime.datetime.now()]
            ph = ",".join("?" for _ in cols)
            try:
                db.execute(f"INSERT INTO {e['table']} ({','.join(cols)}) VALUES ({ph})", *vals)
                flash("Record added.", "ok")
            except Exception as ex:
                flash("Could not add — " + (str(ex).split("\n")[0][:120]), "error")
        return redirect(url_for("screen", key=key, mode=request.args.get("mode", "PY"), company=company))
    editing = any(("pk_" + c) in request.args for c in e["pk"])
    f = {}
    if editing:
        where = " AND ".join(f"{c}=?" for c in e["pk"])
        wvals = [company if c == "company" else request.args.get("pk_" + c) for c in e["pk"]]
        row = one(f"SELECT * FROM {e['table']} WHERE {where}", *wvals)
        if row:
            for c, _, t in e["fields"]:
                v = row.get(c)
                f[c] = v.strftime("%Y-%m-%d") if (t == "date" and v) else ("" if v is None else (v.strip() if isinstance(v, str) else v))
            f["_pk"] = {c: (company if c == "company" else request.args.get("pk_" + c)) for c in e["pk"]}
    return render_template("grid_row.html", g=g, e=e, key=key, f=f, editing=editing)


@app.route("/s/<key>/delete", methods=["POST"])
def grid_delete(key):
    g = GRIDS.get(key)
    if not g or not g.get("edit"):
        abort(404)
    e, company = g["edit"], sel_company()
    where = " AND ".join(f"{c}=?" for c in e["pk"])
    wvals = [company if c == "company" else request.form.get("pk_" + c) for c in e["pk"]]
    db.execute(f"DELETE FROM {e['table']} WHERE {where}", *wvals)
    flash("Record deleted.", "ok")
    return redirect(url_for("screen", key=key, mode=request.args.get("mode", "PY"), company=company))


from reports import REPORTS  # noqa: E402


@app.route("/report/<key>")
def report(key):
    r = REPORTS.get(key)
    if not r:
        abort(404)
    company = sel_company()
    level = r["level"]
    years = [int(row["y"]) for row in
             q("SELECT DISTINCT payyear AS y FROM paytranh WHERE company=? ORDER BY payyear DESC", company)]
    latest = one("SELECT payyear, paymonth, payperiod FROM paytranh WHERE company=? "
                 "ORDER BY payyear DESC, paymonth DESC, payperiod DESC LIMIT 1", company)
    year = int(request.args.get("year", type=int) or (latest["payyear"] if latest else 2025))
    month = int(request.args.get("month", type=int) or (latest["paymonth"] if latest else 1))
    period = (request.args.get("period") or (latest["payperiod"] if latest else "1")).strip()
    if level == "month":
        start = f"{year:04d}-{month:02d}-01"
        ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
        end = f"{ny:04d}-{nm:02d}-01"
        params = [company, start, end]
    elif level == "year":
        params = [company, year]
    else:
        params = [company, year, month, period]
    rows = q(r["sql"], *params)
    return render_template("report.html", r=r, key=key, rows=rows, level=level,
                           years=years, year=year, month=month, period=period)


# ─────────────────────────────────────────────────────────────── dashboard

@app.route("/")
def dashboard():
    by_status = q(
        "SELECT RTRIM(empsts) AS empsts, COUNT(*) AS cnt FROM personnel GROUP BY empsts ORDER BY COUNT(*) DESC"
    )
    active_total = sum(r["cnt"] for r in by_status if r["empsts"] != "X")
    by_company = q(
        "SELECT company, COUNT(*) AS cnt, SUM(CASE WHEN empsts<>'X' THEN 1 ELSE 0 END) AS active "
        "FROM personnel GROUP BY company ORDER BY company"
    )
    ph = one(
        "SELECT MIN(payyear) AS miny, MAX(payyear) AS maxy, COUNT(*) AS rows, "
        "COUNT(DISTINCT emp_id) AS emps FROM paytranh"
    )
    periods = q(
        "SELECT TOP 8 payyear, paymonth, payperiod, COUNT(*) AS lines, COUNT(DISTINCT emp_id) AS emps "
        "FROM paytranh GROUP BY payyear, paymonth, payperiod "
        "ORDER BY payyear DESC, paymonth DESC, payperiod DESC"
    )
    counters = one(
        "SELECT (SELECT COUNT(*) FROM timecard) AS timecard, (SELECT COUNT(*) FROM loans) AS loans, "
        "(SELECT COUNT(*) FROM leavetran) AS leavetran, (SELECT COUNT(*) FROM ratechange) AS ratechange, "
        "(SELECT COUNT(*) FROM users) AS users, "
        "(SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public') AS tables"
    )
    return render_template(
        "dashboard.html", by_status=by_status, active_total=active_total,
        by_company=by_company, ph=ph, periods=periods, counters=counters,
    )


# ─────────────────────────────────────────────────────────────── employees

@app.route("/employees")
def employees():
    qs = (request.args.get("q") or "").strip()
    status = request.args.get("status", "active")
    company = (request.args.get("company") or "").strip()

    where, params = [], []
    if status == "active":
        where.append("p.empsts <> 'X'")
    elif status and status != "all":
        where.append("p.empsts = ?")
        params.append(status)
    if company:
        where.append("p.company = ?")
        params.append(company)
    if qs:
        where.append("(p.lastname ILIKE ? OR p.firstname ILIKE ? OR p.emp_id ILIKE ?)")
        like = f"%{qs}%"
        params += [like, like, qs + "%"]

    sql = (
        "SELECT TOP 500 p.company, RTRIM(p.emp_id) AS emp_id, RTRIM(p.firstname) AS firstname, "
        "RTRIM(COALESCE(p.middlename,'')) AS middlename, RTRIM(p.lastname) AS lastname, "
        "RTRIM(COALESCE(p.division,'')) AS division, RTRIM(COALESCE(p.dept,'')) AS dept, "
        "RTRIM(COALESCE(p.section,'')) AS section, RTRIM(COALESCE(j.descrip, p.jobcode, '')) AS job, "
        "RTRIM(p.empsts) AS empsts, p.datehired "
        "FROM personnel p "
        "LEFT JOIN jobcode j ON j.company = p.company AND j.code = p.jobcode "
        + ("WHERE " + " AND ".join(where) if where else "")
        + " ORDER BY p.lastname, p.firstname"
    )
    emps = q(sql, *params)
    statuses = q(
        "SELECT RTRIM(empsts) AS code, COUNT(*) AS cnt FROM personnel GROUP BY empsts ORDER BY COUNT(*) DESC"
    )
    return render_template("employees.html", emps=emps, qs=qs, status=status,
                           company=company, statuses=statuses)


EMP_TABS = [
    ("personal", "Personal Info"), ("employment", "Employment"), ("education", "Education"),
    ("training", "Training"), ("workexp", "Work Exp"), ("dependents", "Dependents"),
    ("leaves", "Leaves"), ("medical", "Medical Hist"), ("appraisal", "Appraisal"),
    ("disciplinary", "Disciplinary"), ("doc", "Documents"), ("payroll", "Payroll"),
    ("fixallow", "Fix Allow"), ("fixded", "Fix Ded'n"),
]


@app.route("/employee/<company>/<emp_id>")
def employee(company, emp_id):
    p = one(
        "SELECT company, RTRIM(emp_id) AS emp_id, RTRIM(firstname) AS firstname, "
        "RTRIM(COALESCE(middlename,'')) AS middlename, RTRIM(lastname) AS lastname, "
        "RTRIM(COALESCE(address,'')) AS address, RTRIM(COALESCE(addrcity,'')) AS addrcity, "
        "RTRIM(COALESCE(addrprov,'')) AS addrprov, RTRIM(COALESCE(barangay,'')) AS barangay, "
        "birthdate, RTRIM(COALESCE(birthplace,'')) AS birthplace, RTRIM(COALESCE(sex,'')) AS sex, "
        "RTRIM(COALESCE(civilsts,'')) AS civilsts, RTRIM(COALESCE(nationality,'')) AS nationality, "
        "RTRIM(COALESCE(religion,'')) AS religion, RTRIM(COALESCE(bloodtype,'')) AS bloodtype, "
        "RTRIM(COALESCE(telno,'')) AS telno, RTRIM(COALESCE(cellphone,'')) AS cellphone, "
        "age, RTRIM(COALESCE(zipcode,'')) AS zipcode, "
        "RTRIM(COALESCE(sssno,'')) AS sssno, RTRIM(COALESCE(tin,'')) AS tin, "
        "RTRIM(COALESCE(phealthno,'')) AS phealthno, RTRIM(COALESCE(hdmfno,'')) AS hdmfno, "
        "RTRIM(COALESCE(division,'')) AS division, RTRIM(COALESCE(dept,'')) AS dept, "
        "RTRIM(COALESCE(section,'')) AS section, RTRIM(COALESCE(jobcode,'')) AS jobcode, "
        "RTRIM(COALESCE(jobgrade,'')) AS jobgrade, RTRIM(empsts) AS empsts, "
        "datehired, datereg, dateresgnd, RTRIM(COALESCE(reasonresg,'')) AS reasonresg, "
        "RTRIM(COALESCE(reports_to,'')) AS reports_to, RTRIM(COALESCE(shift,'')) AS shift, "
        "RTRIM(COALESCE(contactper,'')) AS contactper, RTRIM(COALESCE(contactrel,'')) AS contactrel, "
        "RTRIM(COALESCE(contactadd,'')) AS contactadd, RTRIM(COALESCE(contacttel,'')) AS contacttel "
        "FROM personnel WHERE company = ? AND emp_id = ?", company, emp_id,
    )
    if not p:
        abort(404)
    tab = request.args.get("tab", "personal")
    data = load_emp_tab(tab, company, emp_id, p)
    job = one("SELECT RTRIM(descrip) AS descrip FROM jobcode WHERE company=? AND code=?",
              company, p["jobcode"])
    div = one("SELECT RTRIM(COALESCE(descrip,'')) AS d FROM division WHERE company=? AND RTRIM(code)=?",
              company, p["division"]) if p["division"] else None
    dept = one("SELECT RTRIM(COALESCE(descrip,'')) AS d FROM department WHERE company=? AND RTRIM(division)=? AND RTRIM(code)=?",
               company, p["division"], p["dept"]) if p["dept"] else None
    sec = one("SELECT RTRIM(COALESCE(descrip,'')) AS d FROM section WHERE company=? AND RTRIM(division)=? AND RTRIM(dept)=? AND RTRIM(code)=?",
              company, p["division"], p["dept"], p["section"]) if p["section"] else None
    shf = one("SELECT RTRIM(COALESCE(shiftdesc,'')) AS d FROM shifttable WHERE company=? AND RTRIM(shift)=?",
              company, p["shift"]) if p["shift"] else None
    rep = one("SELECT RTRIM(lastname)||', '||RTRIM(COALESCE(firstname,'')) AS d FROM personnel WHERE company=? AND RTRIM(emp_id)=?",
              company, p["reports_to"]) if p["reports_to"] else None
    asg = {"division": div["d"] if div else "", "dept": dept["d"] if dept else "",
           "section": sec["d"] if sec else "", "shift": shf["d"] if shf else "",
           "reports_to": rep["d"] if rep else ""}
    return render_template("employee.html", p=p, job=job, asg=asg, tab=tab, tabs=EMP_TABS, d=data)


def load_emp_tab(tab, co, emp, p):
    if tab in emp_tables.SECTION_TABS:
        sections = []
        for s in emp_tables.SECTIONS[tab]:
            if s.get("list_sql"):        # section brings its own list query (joins / derived columns)
                rows = q(s["list_sql"], co, emp)
            else:
                fcols = [c for c, _, _ in s["fields"]]
                cols = fcols if s.get("single") else (["rowid"] + fcols)
                sel = ", ".join(cols)
                if s.get("file"):
                    sel += f", ({s['file']['col']} IS NOT NULL) AS hasfile"
                sql = (f"SELECT {sel} FROM {s['table']} WHERE company=? AND emp_id=?"
                       + (f" ORDER BY {s['order']}" if s.get("order") else ""))
                rows = q(sql, co, emp)
            sections.append({"spec": s, "rows": rows})
        return {"sections": sections}
    if tab == "employment":
        return {
            "movements": {
                "rate": q("SELECT TOP 20 effdate, oldrate, newrate, RTRIM(COALESCE(oldpaytype,'')) AS op, "
                          "RTRIM(COALESCE(newpaytype,'')) AS np, RTRIM(COALESCE(reason,'')) AS reason "
                          "FROM ratechange WHERE company=? AND emp_id=? ORDER BY effdate DESC", co, emp),
                "dept": q("SELECT TOP 20 effdate, RTRIM(COALESCE(olddiv,'')) AS od, RTRIM(COALESCE(olddept,'')) AS odp, "
                          "RTRIM(COALESCE(oldsect,'')) AS os, RTRIM(COALESCE(newdiv,'')) AS nd, "
                          "RTRIM(COALESCE(newdept,'')) AS ndp, RTRIM(COALESCE(newsect,'')) AS ns, "
                          "RTRIM(COALESCE(reason,'')) AS reason FROM deptchange "
                          "WHERE company=? AND emp_id=? ORDER BY effdate DESC", co, emp),
                "job": q("SELECT TOP 20 effdate, RTRIM(COALESCE(oldjobcode,'')) AS oj, RTRIM(COALESCE(newjobcode,'')) AS nj, "
                         "RTRIM(COALESCE(promotion,'')) AS promotion, RTRIM(COALESCE(reason,'')) AS reason "
                         "FROM jobchange WHERE company=? AND emp_id=? ORDER BY effdate DESC", co, emp),
                "empsts": q("SELECT TOP 20 effdate, RTRIM(COALESCE(oldempsts,'')) AS oe, RTRIM(COALESCE(newempsts,'')) AS ne, "
                            "RTRIM(COALESCE(reason,'')) AS reason FROM empstschg "
                            "WHERE company=? AND emp_id=? ORDER BY effdate DESC", co, emp),
            }
        }
    if tab == "education":
        return {"rows": q("SELECT RTRIM(COALESCE(instdesc,'')) AS instdesc, RTRIM(COALESCE(coursedesc,'')) AS coursedesc, "
                          "fromdate, todate, RTRIM(COALESCE(edu_level,'')) AS lvl FROM edutrain "
                          "WHERE company=? AND emp_id=? ORDER BY fromdate", co, emp)}
    if tab == "training":
        return {"rows": q("SELECT RTRIM(COALESCE(coursedesc,'')) AS coursedesc, RTRIM(COALESCE(instdesc,'')) AS instdesc, "
                          "fromdate, todate, tlhours FROM training WHERE company=? AND emp_id=? ORDER BY fromdate DESC", co, emp)}
    if tab == "workexp":
        return {"rows": q("SELECT RTRIM(COALESCE(prevcompnm,'')) AS prevcompnm, RTRIM(COALESCE(workexpdsc,'')) AS workexpdsc, "
                          "fromdate, todate FROM workexp WHERE company=? AND emp_id=? ORDER BY fromdate DESC", co, emp)}
    if tab == "dependents":
        return {"rows": q("SELECT RTRIM(COALESCE(name,'')) AS name, RTRIM(COALESCE(relcde,'')) AS relcde, "
                          "birtdate, RTRIM(COALESCE(sex,'')) AS sex FROM dependents WHERE company=? AND emp_id=? ORDER BY seqno", co, emp)}
    if tab == "leaves":
        return {
            "balances": q("SELECT RTRIM(lvcode) AS lvcode, tyent, dayern, dayuse, (tyent+dayern-dayuse) AS bal "
                          "FROM leaves WHERE company=? AND emp_id=? ORDER BY lvcode", co, emp),
            "trans": q("SELECT TOP 30 RTRIM(COALESCE(l.payitem,'')) AS payitem, RTRIM(COALESCE(i.descrip,'')) AS descrip, "
                       "l.frdate, l.todate, RTRIM(COALESCE(l.reason,'')) AS reason FROM leavetran l "
                       "LEFT JOIN payitem i ON i.company=l.company AND i.payitem=l.payitem "
                       "WHERE l.company=? AND l.emp_id=? ORDER BY l.frdate DESC", co, emp),
        }
    if tab == "medical":
        return {"rows": q("SELECT chkdate, RTRIM(COALESCE(chktype,'')) AS chktype, RTRIM(COALESCE(findings,'')) AS findings, "
                          "RTRIM(COALESCE(illtype,'')) AS illtype, RTRIM(COALESCE(medication,'')) AS medication, "
                          "follow_up_date FROM medical WHERE company=? AND emp_id=? ORDER BY chkdate DESC", co, emp)}
    if tab == "appraisal":
        return {"rows": q("SELECT apdate, aprating, RTRIM(COALESCE(apprby,'')) AS apprby, RTRIM(COALESCE(remarks,'')) AS remarks "
                          "FROM appraisal WHERE company=? AND emp_id=? ORDER BY apdate DESC", co, emp)}
    if tab == "disciplinary":
        return {"rows": q("SELECT discpdate, RTRIM(COALESCE(violation,'')) AS violation, RTRIM(COALESCE(penalty,'')) AS penalty, "
                          "frdate, todate, RTRIM(COALESCE(remarks,'')) AS remarks FROM discipline "
                          "WHERE company=? AND emp_id=? ORDER BY discpdate DESC", co, emp)}
    if tab == "doc":
        return {"rows": q("SELECT docdate, RTRIM(COALESCE(docname,'')) AS docname, RTRIM(COALESCE(docimgext,'')) AS ext, "
                          "RTRIM(COALESCE(remarks,'')) AS remarks FROM edoc WHERE company=? AND emp_id=? ORDER BY docdate DESC", co, emp)}
    if tab == "payroll":
        return {
            "pay": one("SELECT salary, RTRIM(COALESCE(paytype,'')) AS paytype, RTRIM(COALESCE(paygroup,'')) AS paygroup, "
                       "RTRIM(COALESCE(paymode,'')) AS paymode, RTRIM(COALESCE(bankcode,'')) AS bankcode, "
                       "RTRIM(COALESCE(bankacct,'')) AS bankacct, mintakepay, RTRIM(COALESCE(oteligible,'')) AS ot "
                       "FROM payroll WHERE company=? AND emp_id=?", co, emp),
            "loans": q("SELECT RTRIM(COALESCE(l.payitem,'')) AS payitem, RTRIM(COALESCE(i.descrip,'')) AS descrip, "
                       "RTRIM(COALESCE(l.refno,'')) AS refno, l.loanamt, l.payded, l.no_of_pay, l.no_paid, "
                       "l.totalpaid, ((COALESCE(l.loanamt,0)+COALESCE(l.intamt,0))"
                       "-(COALESCE(l.totalpaid,0)+COALESCE(l.totalpaidi,0))) AS bal FROM loans l "
                       "LEFT JOIN payitem i ON i.company=l.company AND i.payitem=l.payitem "
                       "WHERE l.company=? AND l.emp_id=? ORDER BY l.dateapprov DESC", co, emp),
        }
    if tab == "fixallow":
        return {"rows": q("SELECT RTRIM(COALESCE(f.payitem,'')) AS payitem, RTRIM(COALESCE(i.descrip,'')) AS descrip, "
                          "f.amount, RTRIM(COALESCE(f.freq,'')) AS freq, RTRIM(COALESCE(f.paytype,'')) AS paytype, f.effdate "
                          "FROM fixallow f LEFT JOIN payitem i ON i.company=f.company AND i.payitem=f.payitem "
                          "WHERE f.company=? AND f.emp_id=? ORDER BY f.payitem", co, emp)}
    if tab == "fixded":
        return {"rows": q("SELECT RTRIM(COALESCE(f.payitem,'')) AS payitem, RTRIM(COALESCE(i.descrip,'')) AS descrip, "
                          "f.amount, RTRIM(COALESCE(f.freq,'')) AS freq, RTRIM(COALESCE(f.b4tax,'')) AS b4tax "
                          "FROM fixded f LEFT JOIN payitem i ON i.company=f.company AND i.payitem=f.payitem "
                          "WHERE f.company=? AND f.emp_id=? ORDER BY f.payitem", co, emp)}
    # personal (default) — payroll summary strip
    return {
        "pay": one("SELECT salary, RTRIM(COALESCE(paytype,'')) AS paytype, RTRIM(COALESCE(paygroup,'')) AS paygroup "
                   "FROM payroll WHERE company=? AND emp_id=?", co, emp),
        "years": q("SELECT payyear, COUNT(*) AS lines FROM paytranh WHERE company=? AND emp_id=? "
                   "GROUP BY payyear ORDER BY payyear DESC", co, emp),
    }


# ───────────────────────────────────────────────────── add / delete employee

EMP_FIELDS = [
    ("lastname", "Last name"), ("firstname", "First name"), ("middlename", "Middle name"),
    ("sex", "Sex"), ("civilsts", "Civil status"), ("birthdate", "Birth date"),
    ("nationality", "Nationality"), ("religion", "Religion"), ("bloodtype", "Blood type"),
    ("address", "Address"), ("barangay", "Barangay"), ("addrcity", "City / Town"),
    ("addrprov", "Province"), ("zipcode", "Zip"), ("telno", "Telephone"), ("cellphone", "Cellphone"),
    ("sssno", "SSS No."), ("tin", "TIN"), ("phealthno", "PhilHealth No."), ("hdmfno", "Pag-IBIG No."),
    ("division", "Division"), ("dept", "Department"), ("section", "Section"), ("jobcode", "Position code"),
    ("empsts", "Status"), ("datehired", "Date hired"), ("datereg", "Date regularized"),
    ("reports_to", "Reports to"), ("shift", "Shift"),
    ("contactper", "Emergency contact"), ("contactrel", "Relationship"), ("contacttel", "Contact tel"),
]
DATE_FIELDS = {"birthdate", "datehired", "datereg"}


def _assignment_lookups(company):
    """Option lists (code + description) for the Assignment dropdowns, scoped to a company.
    The stored value stays the code — only the label shows the name (like the Status field)."""
    def dedupe(rows):                       # dept/section codes can repeat across divisions
        seen = {}
        for r in rows:
            seen.setdefault(r["code"], r["descrip"])
        return [{"code": k, "descrip": v} for k, v in seen.items()]
    return {
        "divisions": q("SELECT RTRIM(code) AS code, RTRIM(COALESCE(descrip,'')) AS descrip "
                       "FROM division WHERE company=? ORDER BY code", company),
        "departments": dedupe(q("SELECT RTRIM(code) AS code, RTRIM(COALESCE(descrip,'')) AS descrip "
                                "FROM department WHERE company=? ORDER BY code", company)),
        "sections": dedupe(q("SELECT RTRIM(code) AS code, RTRIM(COALESCE(descrip,'')) AS descrip "
                             "FROM section WHERE company=? ORDER BY code", company)),
        "positions": q("SELECT RTRIM(code) AS code, RTRIM(COALESCE(descrip,'')) AS descrip "
                       "FROM jobcode WHERE company=? ORDER BY descrip", company),
        "shifts": q("SELECT RTRIM(shift) AS code, RTRIM(COALESCE(shiftdesc,'')) AS descrip "
                    "FROM shifttable WHERE company=? ORDER BY shift", company),
        "employees": q("SELECT RTRIM(emp_id) AS code, RTRIM(lastname)||', '||RTRIM(COALESCE(firstname,'')) AS descrip "
                       "FROM personnel WHERE company=? AND empsts<>'X' ORDER BY lastname, firstname", company),
    }


@app.route("/employee/new", methods=["GET", "POST"])
def employee_new():
    mode = request.args.get("mode", "PY")
    est = q("SELECT RTRIM(fldcode) AS code, RTRIM(descrip) AS descrip "
            "FROM tablecode1 WHERE tblcode='EST' ORDER BY fldcode")
    if request.method == "POST":
        company = (request.form.get("company") or "001").strip()
        emp_id = (request.form.get("emp_id") or "").strip()
        errors = []
        if not emp_id:
            errors.append("Employee No. is required.")
        if not (request.form.get("lastname") or "").strip():
            errors.append("Last name is required.")
        if emp_id and one("SELECT 1 AS x FROM personnel WHERE company=? AND emp_id=?", company, emp_id):
            errors.append(f"Employee {emp_id} already exists in company {company}.")
        if not errors:
            cols, vals = ["company", "emp_id"], [company, emp_id]
            for f, _ in EMP_FIELDS:
                v = (request.form.get(f) or "").strip()
                cols.append(f)
                vals.append((v or None) if f in DATE_FIELDS else v)
            ph = ",".join("?" for _ in cols)
            db.execute(f"INSERT INTO personnel ({','.join(cols)}) VALUES ({ph})", *vals)
            flash(f"Employee {emp_id} added.", "ok")
            return redirect(url_for("employee", company=company, emp_id=emp_id, mode=mode))
        for e in errors:
            flash(e, "error")
    return render_template("employee_new.html", est=est, form=request.form, is_edit=False,
                           heading="Add Employee", action_url=url_for("employee_new", mode=mode),
                           **_assignment_lookups(request.form.get("company") or sel_company()))


@app.route("/employee/<company>/<emp_id>/edit", methods=["GET", "POST"])
def employee_edit(company, emp_id):
    mode = request.args.get("mode", "PY")
    est = q("SELECT RTRIM(fldcode) AS code, RTRIM(descrip) AS descrip "
            "FROM tablecode1 WHERE tblcode='EST' ORDER BY fldcode")
    if not one("SELECT 1 AS x FROM personnel WHERE company=? AND emp_id=?", company, emp_id):
        abort(404)
    if request.method == "POST":
        if not (request.form.get("lastname") or "").strip():
            flash("Last name is required.", "error")
        else:
            sets, vals = [], []
            for f, _ in EMP_FIELDS:
                v = (request.form.get(f) or "").strip()
                sets.append(f"{f}=?")
                vals.append((v or None) if f in DATE_FIELDS else v)
            vals += [company, emp_id]
            db.execute(f"UPDATE personnel SET {','.join(sets)} WHERE company=? AND emp_id=?", *vals)
            flash(f"Employee {emp_id} updated.", "ok")
            return redirect(url_for("employee", company=company, emp_id=emp_id, mode=mode))
        f = request.form
    else:
        cols = "company, emp_id, " + ", ".join(c for c, _ in EMP_FIELDS)
        row = one(f"SELECT {cols} FROM personnel WHERE company=? AND emp_id=?", company, emp_id)
        f = {}
        for k, v in row.items():
            if k in DATE_FIELDS and v:
                f[k] = v.strftime("%Y-%m-%d")
            else:
                f[k] = "" if v is None else (v.strip() if isinstance(v, str) else v)
    return render_template("employee_new.html", est=est, form=f, is_edit=True,
                           heading="Edit Employee",
                           action_url=url_for("employee_edit", company=company, emp_id=emp_id, mode=mode),
                           back_url=url_for("employee", company=company, emp_id=emp_id, mode=mode),
                           **_assignment_lookups(company))


@app.route("/employee/<company>/<emp_id>/delete", methods=["POST"])
def employee_delete(company, emp_id):
    mode = request.args.get("mode", "PY")
    p = one("SELECT RTRIM(lastname) AS lastname, RTRIM(firstname) AS firstname "
            "FROM personnel WHERE company=? AND emp_id=?", company, emp_id)
    if not p:
        abort(404)
    db.execute("DELETE FROM personnel WHERE company=? AND emp_id=?", company, emp_id)
    flash(f"Deleted employee {emp_id} — {p['lastname']}, {p['firstname']}.", "ok")
    return redirect(url_for("employees", mode=mode, company=company))


# ── editable employee 201-file sections (education, training, docs, payroll, …) ──

@app.route("/employee/<company>/<emp_id>/t/<table>/row", methods=["GET", "POST"])
def emp_row(company, emp_id, table):
    mode = request.args.get("mode", "PY")
    s = emp_tables.SECTION_BY_TABLE.get(table)
    if not s or not one("SELECT 1 AS x FROM personnel WHERE company=? AND emp_id=?", company, emp_id):
        abort(404)
    single, fileF = s.get("single"), s.get("file")
    if request.method == "POST":
        data = {c: _cast(request.form.get(c), t) for c, _, t in s["fields"]}
        user, now = session.get("user", {}).get("id", ""), datetime.datetime.now()
        if fileF and request.files.get("file") and request.files["file"].filename:
            up = request.files["file"]
            data[fileF["col"]] = up.read()
            data[fileF["ext"]] = up.filename.rsplit(".", 1)[-1].lower() if "." in up.filename else ""
            if not data.get(fileF["name"]):
                data[fileF["name"]] = up.filename
        if single:
            exists = one(f"SELECT 1 AS x FROM {table} WHERE company=? AND emp_id=?", company, emp_id)
            cols = list(data.keys())
            if exists:
                sets = ", ".join(f"{c}=?" for c in cols) + ", changeby=?, changedate=?"
                db.execute(f"UPDATE {table} SET {sets} WHERE company=? AND emp_id=?",
                           *([data[c] for c in cols] + [user, now, company, emp_id]))
            else:
                allc = ["company", "emp_id"] + cols + ["changeby", "changedate"]
                vals = [company, emp_id] + [data[c] for c in cols] + [user, now]
                db.execute(f"INSERT INTO {table} ({','.join(allc)}) VALUES ({','.join(['?']*len(allc))})", *vals)
            flash(f"{s['label']} saved.", "ok")
        else:
            rowid = request.form.get("rowid")
            if rowid:
                setcols = list(data.keys())
                sets = ", ".join(f"{c}=?" for c in setcols) + ", changeby=?, changedate=?"
                db.execute(f"UPDATE {table} SET {sets} WHERE company=? AND emp_id=? AND rowid=?",
                           *([data[c] for c in setcols] + [user, now, company, emp_id, rowid]))
                flash(f"{s['label']} record updated.", "ok")
            else:
                cols = ["company", "emp_id"] + list(data.keys()) + ["changeby", "changedate"]
                vals = [company, emp_id] + [data[c] for c in data] + [user, now]
                db.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", *vals)
                flash(f"{s['label']} record added.", "ok")
        return redirect(url_for("employee", company=company, emp_id=emp_id, mode=mode, tab=s["tab"]))
    # GET — build the form (prefill for edit / single)
    f, rowid = {}, request.args.get("rowid")
    if rowid or single:
        if single:
            row = one(f"SELECT * FROM {table} WHERE company=? AND emp_id=?", company, emp_id)
        else:
            row = one(f"SELECT * FROM {table} WHERE company=? AND emp_id=? AND rowid=?", company, emp_id, rowid)
        if row:
            for c, _, t in s["fields"]:
                v = row.get(c)
                f[c] = v.strftime("%Y-%m-%d") if (t == "date" and v) else ("" if v is None else (v.strip() if isinstance(v, str) else v))
    return render_template("emp_row.html", s=s, company=company, emp_id=emp_id, f=f,
                           rowid=rowid, single=single, editing=bool(rowid or (single and f)))


@app.route("/employee/<company>/<emp_id>/t/<table>/delete", methods=["POST"])
def emp_delete_row(company, emp_id, table):
    mode = request.args.get("mode", "PY")
    s = emp_tables.SECTION_BY_TABLE.get(table)
    if not s:
        abort(404)
    db.execute(f"DELETE FROM {table} WHERE company=? AND emp_id=? AND rowid=?",
               company, emp_id, request.form.get("rowid"))
    flash(f"{s['label']} record deleted.", "ok")
    return redirect(url_for("employee", company=company, emp_id=emp_id, mode=mode, tab=s["tab"]))


@app.route("/employee/<company>/<emp_id>/t/<table>/file/<rowid>")
def emp_file(company, emp_id, table, rowid):
    import mimetypes
    from flask import Response
    s = emp_tables.SECTION_BY_TABLE.get(table)
    if not s or not s.get("file"):
        abort(404)
    fl = s["file"]
    row = one(f"SELECT {fl['col']} AS blob, {fl['ext']} AS ext, {fl['name']} AS name "
              f"FROM {table} WHERE company=? AND emp_id=? AND rowid=?", company, emp_id, rowid)
    if not row or row["blob"] is None:
        abort(404)
    ext = (row["ext"] or "").strip().lower()
    name = ((row["name"] or "document").strip() + (("." + ext) if ext else ""))
    mime = mimetypes.types_map.get("." + ext, "application/octet-stream")
    return Response(bytes(row["blob"]), mimetype=mime,
                    headers={"Content-Disposition": f'inline; filename="{name}"'})


# ───────────────────────────────────────────────────────── payroll register

@app.route("/payroll")
def payroll():
    periods = q("SELECT DISTINCT TOP 40 payyear, paymonth, payperiod FROM paytranh "
                "ORDER BY payyear DESC, paymonth DESC, payperiod DESC")
    if not periods:
        abort(404)
    d0 = periods[0]
    year = request.args.get("year", type=int) or d0["payyear"]
    month = request.args.get("month", type=int) or d0["paymonth"]
    period = (request.args.get("period") or d0["payperiod"]).strip()
    company = sel_company()
    items = q(
        "SELECT t.payitem, RTRIM(COALESCE(MAX(i.descrip), t.payitem)) AS descrip, MAX(i.category) AS category, "
        "COUNT(DISTINCT t.emp_id) AS emps, SUM(t.trhours) AS hrs, SUM(t.trdays) AS dys, SUM(t.tramount) AS amt "
        "FROM paytranh t LEFT JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem "
        "WHERE t.payyear=? AND t.paymonth=? AND t.payperiod=? AND t.company=? "
        "GROUP BY t.payitem ORDER BY t.payitem", year, month, period, company)
    totals = {
        "emps": one("SELECT COUNT(DISTINCT emp_id) AS n FROM paytranh WHERE payyear=? AND paymonth=? "
                    "AND payperiod=? AND company=?", year, month, period, company)["n"],
        "amt": sum(r["amt"] or 0 for r in items),
    }
    return render_template("payroll.html", periods=periods, items=items, totals=totals,
                           year=year, month=month, period=period)


# ────────────────────────────────────────────────── payroll engine screens

import payroll_engine as pe  # noqa: E402


@app.route("/calculator")
def calculator():
    salary = request.args.get("salary", type=float)
    paytype = (request.args.get("paytype") or "M").strip()
    eng = pe.engine()
    result = eng.compute_monthly(salary) if salary else None
    rates = eng.ot_rates(salary, paytype, sel_company()) if salary else None
    return render_template("calculator.html", salary=salary, r=result, rates=rates, paytype=paytype)


@app.route("/payroll/compute")
def payroll_compute():
    import payroll_calc as pc
    company = sel_company()
    periods = q("SELECT DISTINCT TOP 40 payyear, paymonth, payperiod FROM paytranh WHERE company=? "
                "ORDER BY payyear DESC, paymonth DESC, payperiod DESC", company)
    d0 = periods[0] if periods else {"payyear": 2025, "paymonth": 8, "payperiod": "1"}
    year = int(request.args.get("year", type=int) or d0["payyear"])
    month = int(request.args.get("month", type=int) or d0["paymonth"])
    period = (request.args.get("period") or str(d0["payperiod"])).strip()
    emp_id = (request.args.get("emp_id") or "").strip()
    ot_items = q("SELECT RTRIM(payitem) AS payitem, RTRIM(COALESCE(descrip,payitem)) AS descrip FROM payitem "
                 "WHERE company=? AND category='7' AND RTRIM(COALESCE(unmsr,''))='H' ORDER BY payitem", company)[:6]
    ot_lines = [{"payitem": it["payitem"], "hours": request.args.get("ot_" + it["payitem"], type=float)}
                for it in ot_items if request.args.get("ot_" + it["payitem"], type=float)]
    result = pc.compute(company, emp_id, year, month, period, ot_lines) if emp_id else None
    emps = q("SELECT RTRIM(emp_id) AS emp_id, RTRIM(lastname)||', '||RTRIM(firstname) AS empname "
             "FROM personnel WHERE company=? AND empsts<>'X' ORDER BY lastname, firstname", company)
    p = one("SELECT RTRIM(lastname) AS lastname, RTRIM(firstname) AS firstname, RTRIM(COALESCE(jobcode,'')) AS jobcode "
            "FROM personnel WHERE company=? AND emp_id=?", company, emp_id) if emp_id else None
    return render_template("payroll_compute.html", periods=periods, year=year, month=month, period=period,
                           emp_id=emp_id, emps=emps, ot_items=ot_items, result=result, p=p,
                           ot_hours={it["payitem"]: request.args.get("ot_" + it["payitem"], "") for it in ot_items})


@app.route("/payroll/ot", methods=["GET", "POST"])
def payroll_ot():
    company = sel_company()
    mode = request.args.get("mode", "PY")
    periods = q("SELECT DISTINCT TOP 40 payyear, paymonth, payperiod FROM paytranh WHERE company=? "
                "ORDER BY payyear DESC, paymonth DESC, payperiod DESC", company)
    d0 = periods[0] if periods else {"payyear": 2025, "paymonth": 8, "payperiod": "1"}
    year = int(request.values.get("year", type=int) or d0["payyear"])
    month = int(request.values.get("month", type=int) or d0["paymonth"])
    period = (request.values.get("period") or str(d0["payperiod"])).strip()
    if request.method == "POST":
        emp_id = (request.form.get("emp_id") or "").strip()
        payitem = (request.form.get("payitem") or "").strip()
        hours = request.form.get("hours", type=float)
        if emp_id and payitem and hours:
            db.execute("INSERT INTO ot_entry (company,payyear,paymonth,payperiod,emp_id,payitem,hours,changeby,changedate) "
                       "VALUES (?,?,?,?,?,?,?,?,?)", company, year, month, period, emp_id, payitem, hours,
                       session.get("user", {}).get("id", ""), datetime.datetime.now())
            flash(f"Overtime added for {emp_id}.", "ok")
        else:
            flash("Employee, OT type and hours are all required.", "error")
        return redirect(url_for("payroll_ot", company=company, mode=mode, year=year, month=month, period=period))
    entries = q("SELECT o.rowid, RTRIM(o.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
                "RTRIM(o.payitem) AS payitem, RTRIM(COALESCE(i.descrip,o.payitem)) AS descrip, o.hours "
                "FROM ot_entry o LEFT JOIN personnel p ON p.company=o.company AND p.emp_id=o.emp_id "
                "LEFT JOIN payitem i ON i.company=o.company AND i.payitem=o.payitem "
                "WHERE o.company=? AND o.payyear=? AND o.paymonth=? AND o.payperiod=? "
                "ORDER BY p.lastname, o.payitem", company, year, month, period)
    emps = q("SELECT RTRIM(emp_id) AS emp_id, RTRIM(lastname)||', '||RTRIM(firstname) AS empname "
             "FROM personnel WHERE company=? AND empsts<>'X' ORDER BY lastname, firstname", company)
    ot_items = q("SELECT RTRIM(payitem) AS payitem, RTRIM(COALESCE(descrip,payitem)) AS descrip FROM payitem "
                 "WHERE company=? AND category='7' AND RTRIM(COALESCE(unmsr,''))='H' ORDER BY payitem", company)
    return render_template("payroll_ot.html", periods=periods, year=year, month=month, period=period,
                           entries=entries, emps=emps, ot_items=ot_items)


@app.route("/payroll/ot/delete", methods=["POST"])
def payroll_ot_delete():
    company = sel_company()
    db.execute("DELETE FROM ot_entry WHERE company=? AND rowid=?", company, request.form.get("rowid"))
    flash("Overtime entry removed.", "ok")
    return redirect(url_for("payroll_ot", company=company, mode=request.form.get("mode", "PY"),
                            year=request.form.get("year"), month=request.form.get("month"), period=request.form.get("period")))


@app.route("/payroll/reopen", methods=["POST"])
def payroll_reopen():
    company = sel_company()
    year = int(request.form.get("year") or 0); month = int(request.form.get("month") or 0)
    period = (request.form.get("period") or "1").strip()
    db.execute("DELETE FROM period_close WHERE company=? AND payyear=? AND paymonth=? AND payperiod=?",
               company, year, month, period)
    flash(f"Reopened {year}-{month:02d} Period {period}. You can re-post it now.", "ok")
    return redirect(url_for("payroll_compute_all", company=company, mode=request.form.get("mode", "PY"),
                            year=year, month=month, period=period))


@app.route("/payroll/compute_all")
def payroll_compute_all():
    import payroll_calc as pc
    company = sel_company()
    periods = q("SELECT DISTINCT TOP 40 payyear, paymonth, payperiod FROM paytranh WHERE company=? "
                "ORDER BY payyear DESC, paymonth DESC, payperiod DESC", company)
    d0 = periods[0] if periods else {"payyear": 2025, "paymonth": 8, "payperiod": "1"}
    year = int(request.args.get("year", type=int) or d0["payyear"])
    month = int(request.args.get("month", type=int) or d0["paymonth"])
    period = (request.args.get("period") or str(d0["payperiod"])).strip()
    rows, totals = pc.compute_batch(company, year, month, period)
    status = pc.period_status(company, year, month, period)
    ot_count = one("SELECT COUNT(*) AS n FROM ot_entry WHERE company=? AND payyear=? AND paymonth=? AND payperiod=?",
                   company, year, month, period)["n"]
    return render_template("payroll_compute_all.html", periods=periods, year=year, month=month, period=period,
                           rows=rows, totals=totals, existing=status["rows"], status=status, ot_count=ot_count)


@app.route("/payroll/post", methods=["POST"])
def payroll_post():
    import payroll_calc as pc
    company = sel_company()
    mode = request.form.get("mode", "PY")
    year = int(request.form.get("year") or 0)
    month = int(request.form.get("month") or 0)
    period = (request.form.get("period") or "1").strip()
    overwrite = request.form.get("overwrite") == "1"
    st = pc.period_status(company, year, month, period)
    if st["closed"]:
        flash(f"{year}-{month:02d} Period {period} is CLOSED (by {st['closed_by']}). Reopen it before re-posting.", "error")
    elif st["rows"] and not overwrite:
        flash(f"{year}-{month:02d} Period {period} already has {st['rows']:,} rows. "
              f"Use “Re-post (overwrite)” to replace them.", "error")
    else:
        res = pc.post_period(company, year, month, period, session.get("user", {}).get("id", ""), overwrite)
        flash(f"Posted {res['lines']:,} lines for {res['employees']} employees to {year}-{month:02d} "
              f"Period {period} (net ₱{res['net']:,.2f}) and marked it CLOSED. Now in payslips, registers and forms.", "ok")
    return redirect(url_for("payroll_compute_all", company=company, year=year, month=month, period=period, mode=mode))


@app.route("/timecard")
def timecard():
    """Time Card Inquiry — filter daily time-card rows by date range, pay group,
    employee and shift (mirrors the old app's Time Card Inquiry screen)."""
    company = sel_company()
    mode = request.args.get("mode", "PY")

    def hhmm(v):
        if v is None:
            return ""
        v = int(v)
        return "" if v <= 0 else f"{v // 100:02d}:{v % 100:02d}"

    def numf(v, dp=2):
        if v is None:
            return ""
        f = float(v)
        return "" if abs(f) < 0.005 else f"{f:.{dp}f}"

    # default window = the latest month with data for this company (ignore corrupt future dates)
    mx = one("SELECT MAX(trdate) AS d FROM timecard WHERE company=? AND trdate < '2100-01-01'", company)
    dmax = mx["d"].date() if mx and mx["d"] else datetime.date.today()
    dfrom = (request.args.get("dfrom") or dmax.replace(day=1).isoformat()).strip()
    dto = (request.args.get("dto") or dmax.isoformat()).strip()
    paygroup = (request.args.get("paygroup") or "").strip()
    emp_id = (request.args.get("emp_id") or "").strip()
    shift = (request.args.get("shift") or "").strip()
    recalc = "Y" if request.args.get("recalc") == "Y" else "N"

    where = ["t.company=?", "t.trdate>=?", "t.trdate<=?"]
    params = [company, dfrom, dto]
    if emp_id:
        where.append("t.emp_id=?"); params.append(emp_id)
    if paygroup:
        where.append("RTRIM(COALESCE(pr.paygroup,''))=?"); params.append(paygroup)
    if shift:
        where.append("RTRIM(COALESCE(t.shift,''))=?"); params.append(shift)
    if recalc == "Y":
        where.append("COALESCE(t.recalcflg,'')='Y'")

    CAP = 3000
    raw = q(
        "SELECT TOP " + str(CAP + 1) + " t.emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname)"
        "  ||CASE WHEN COALESCE(RTRIM(p.middlename),'')<>'' THEN ' '||LEFT(RTRIM(p.middlename),1) ELSE '' END AS empname, "
        "  t.trdate, RTRIM(COALESCE(t.shift,'')) AS shift, COALESCE(t.dayoff,'') AS dayoff, "
        "  COALESCE(t.cwwdoff,'') AS cwwdoff, t.timein1, t.timeout1, t.timein2, t.timeout2, "
        "  t.timein3, t.timeout3, t.timein4, t.timeout4, t.tlhours, t.reghrs, t.nphrs, t.tardy, "
        "  t.undertime, t.othrs, COALESCE(t.approvot,'') AS approvot, RTRIM(COALESCE(t.runsheetno,'')) AS runsheetno, "
        "  COALESCE(t.recalcflg,'') AS recalcflg, RTRIM(COALESCE(t.paygroup,'')) AS paygroup, "
        "  RTRIM(COALESCE(pi.shortdesc, t.payitem1)) AS chargeto "
        "FROM timecard t JOIN personnel p ON p.company=t.company AND p.emp_id=t.emp_id "
        "LEFT JOIN payroll pr ON pr.company=t.company AND pr.emp_id=t.emp_id "
        "LEFT JOIN payitem pi ON pi.company=t.company AND pi.payitem=t.payitem1 "
        "WHERE " + " AND ".join(where) +
        " ORDER BY p.lastname, p.firstname, t.emp_id, t.trdate", *params)

    truncated = len(raw) > CAP
    raw = raw[:CAP]
    DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    rows, total, prev = [], 0.0, None
    for r in raw:
        d = r["trdate"]
        dayoff = str(r["dayoff"]).strip() in ("1", "Y")
        cww = str(r["cwwdoff"]).strip() in ("1", "Y")
        absent = bool(r["undertime"] and float(r["undertime"]) > 0 and not r["timein1"])
        parts = []
        if absent:
            parts.append("Absent")
        else:
            if r["tardy"] and float(r["tardy"]) > 0:
                parts.append("Tardy")
            if r["othrs"] and float(r["othrs"]) > 0:
                parts.append("Overtime")
        total += float(r["tlhours"] or 0)
        rows.append({
            "show_emp": r["emp_id"] != prev, "emp_id": r["emp_id"], "empname": r["empname"],
            "date": d.strftime("%m/%d/%Y"), "dow": DOW[d.weekday()], "weekend": d.weekday() >= 5,
            "shift": r["shift"], "dayoff": dayoff, "cww": cww,
            "in1": hhmm(r["timein1"]), "out1": hhmm(r["timeout1"]), "in2": hhmm(r["timein2"]),
            "out2": hhmm(r["timeout2"]), "in3": hhmm(r["timein3"]), "out3": hhmm(r["timeout3"]),
            "in4": hhmm(r["timein4"]), "out4": hhmm(r["timeout4"]),
            "total": numf(r["tlhours"]), "reg": numf(r["reghrs"]), "np": numf(r["nphrs"]),
            "tardy": numf(float(r["tardy"] or 0) / 60.0), "absundtm": numf(r["undertime"]),
            "chargeto": r["chargeto"] or "", "ot": numf(r["othrs"]),
            "approvot": (r["approvot"] or "").strip(), "runsheetno": r["runsheetno"],
            "recalc": (r["recalcflg"] or "").strip() == "Y", "remarks": "/".join(parts),
        })
        prev = r["emp_id"]

    return render_template("timecard.html", rows=rows, total=total, count=len(rows),
                           dfrom=dfrom, dto=dto, paygroup=paygroup, emp_id=emp_id,
                           shift=shift, recalc=recalc, truncated=truncated, cap=CAP)


def _parse_punch(s):
    """Parse a punch input ('8:09', '08:09', '809', '0809') into a numeric HHMM, or None."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        if ":" in s:
            h, m = s.split(":")[:2]
            h, m = int(h), int(m)
        else:
            v = int(s.replace(".", ""))
            h, m = v // 100, v % 100
        if 0 <= h <= 47 and 0 <= m <= 59:
            return h * 100 + m
    except (ValueError, TypeError):
        pass
    return None


def _min_to_hhmm(mins):
    if mins is None:
        return None
    mins = int(mins) % 1440
    return f"{mins // 60:02d}:{mins % 60:02d}"


@app.route("/timecard/edit", methods=["GET", "POST"])
def timecard_edit():
    """Time Card Update — enter raw punches per day; the app derives regular hours,
    tardy, undertime and night premium from the employee's shift schedule and upserts
    the timecard. Overtime stays an approved entry (Overtime Entry screen)."""
    import attendance_engine as ae
    company = sel_company()
    mode = request.args.get("mode", "PY")
    emp_id = (request.values.get("emp_id") or "").strip()
    mx = one("SELECT MAX(trdate) AS d FROM timecard WHERE company=? AND trdate < '2100-01-01'", company)
    dmax = mx["d"].date() if mx and mx["d"] else datetime.date.today()
    dfrom = (request.values.get("dfrom") or dmax.replace(day=1).isoformat()).strip()
    dto = (request.values.get("dto") or dmax.isoformat()).strip()
    try:
        d0, d1 = datetime.date.fromisoformat(dfrom), datetime.date.fromisoformat(dto)
    except ValueError:
        d0, d1 = dmax.replace(day=1), dmax
    if d1 < d0:
        d0, d1 = d1, d0
    if (d1 - d0).days > 62:
        d1 = d0 + datetime.timedelta(days=62)
    dates = [d0 + datetime.timedelta(days=i) for i in range((d1 - d0).days + 1)]

    emp = one("SELECT RTRIM(lastname)||', '||RTRIM(firstname)"
              "||CASE WHEN COALESCE(RTRIM(middlename),'')<>'' THEN ' '||LEFT(RTRIM(middlename),1) ELSE '' END AS empname "
              "FROM personnel WHERE company=? AND emp_id=?", company, emp_id) if emp_id else None

    if request.method == "POST" and emp_id and emp:
        scheds = ae.schedule_range(company, emp_id, dates)
        existing_ot = {r["trdate"].date().isoformat(): float(r["othrs"] or 0) for r in q(
            "SELECT trdate, othrs FROM timecard WHERE company=? AND emp_id=? AND trdate>=? AND trdate<=?",
            company, emp_id, d0.isoformat(), d1.isoformat())}
        user = session.get("user", {}).get("id", "")
        now = datetime.datetime.now()
        saved = 0
        for d in dates:
            key = d.isoformat()
            in1, out1 = _parse_punch(request.form.get("in1_" + key)), _parse_punch(request.form.get("out1_" + key))
            in2, out2 = _parse_punch(request.form.get("in2_" + key)), _parse_punch(request.form.get("out2_" + key))
            dayoff = request.form.get("dayoff_" + key) == "1"
            if not any(v is not None for v in (in1, out1, in2, out2)) and not dayoff:
                continue                                  # untouched day — leave it alone
            sch = scheds.get(d)
            if not sch:
                continue
            res = ae.compute_day(sch, [(in1, out1), (in2, out2)], dayoff=dayoff,
                                 approved_ot=existing_ot.get(key, 0.0))
            db.execute(
                "INSERT INTO timecard (company,emp_id,trdate,daycd,shift,dayoff,timein1,timeout1,timein2,timeout2,"
                "stdhours,stdtimein,stdbrkout,stdbrkin,stdtimeout,tlhours,reghrs,tardy,undertime,nphrs,recalcflg,"
                "changeby,changedate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT (company,emp_id,trdate) DO UPDATE SET daycd=EXCLUDED.daycd, shift=EXCLUDED.shift, "
                "dayoff=EXCLUDED.dayoff, timein1=EXCLUDED.timein1, timeout1=EXCLUDED.timeout1, timein2=EXCLUDED.timein2, "
                "timeout2=EXCLUDED.timeout2, stdhours=EXCLUDED.stdhours, stdtimein=EXCLUDED.stdtimein, "
                "stdbrkout=EXCLUDED.stdbrkout, stdbrkin=EXCLUDED.stdbrkin, stdtimeout=EXCLUDED.stdtimeout, "
                "tlhours=EXCLUDED.tlhours, reghrs=EXCLUDED.reghrs, tardy=EXCLUDED.tardy, undertime=EXCLUDED.undertime, "
                "nphrs=EXCLUDED.nphrs, recalcflg='N', changeby=EXCLUDED.changeby, changedate=EXCLUDED.changedate",
                company, emp_id, key, str(sch["daycode"]), sch["shift"], ("1" if dayoff else "0"),
                in1, out1, in2, out2, sch["stdhours"], _min_to_hhmm(sch["stdin"]), _min_to_hhmm(sch["brkout"]),
                _min_to_hhmm(sch["brkin"]), _min_to_hhmm(sch["stdout"]), res["tlhours"], res["reghrs"],
                res["tardy"], res["undertime"], res["nphrs"], "N", user, now)
            saved += 1
        flash(f"Saved {saved} day(s) for {emp_id} — recomputed regular hours, tardy, undertime and night premium."
              if saved else "Nothing to save — enter time in/out (or tick Day Off) on at least one day.",
              "ok" if saved else "error")
        return redirect(url_for("timecard_edit", company=company, mode=mode, emp_id=emp_id,
                                dfrom=d0.isoformat(), dto=d1.isoformat()))

    rows = []
    if emp_id and emp:
        scheds = ae.schedule_range(company, emp_id, dates)
        stored = {r["trdate"].date().isoformat(): r for r in q(
            "SELECT trdate, COALESCE(dayoff,'') AS dayoff, timein1,timeout1,timein2,timeout2, "
            "reghrs,tardy,undertime,nphrs,othrs,tlhours, RTRIM(COALESCE(shift,'')) AS shift "
            "FROM timecard WHERE company=? AND emp_id=? AND trdate>=? AND trdate<=?",
            company, emp_id, d0.isoformat(), d1.isoformat())}
        DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        def hhmm(v):
            if v is None:
                return ""
            v = int(v)
            return "" if v <= 0 else f"{v // 100:02d}:{v % 100:02d}"

        def numf(v):
            if v is None:
                return ""
            f = float(v)
            return "" if abs(f) < 0.005 else f"{f:.2f}"

        for d in dates:
            key = d.isoformat()
            s = stored.get(key)
            sch = scheds.get(d)
            off = (str(s["dayoff"]).strip() in ("1", "Y")) if s else (sch["dayoff"] if sch else False)
            rows.append({
                "key": key, "date": d.strftime("%m/%d/%Y"), "dow": DOW[d.weekday()],
                "weekend": d.weekday() >= 5, "dayoff": off, "exists": bool(s),
                "shift": (s["shift"] if s and s["shift"] else (sch["shift"] if sch else "")),
                "sched": (_min_to_hhmm(sch["stdin"]) + "–" + _min_to_hhmm(sch["stdout"])) if sch and sch["stdin"] is not None else "",
                "in1": hhmm(s["timein1"]) if s else "", "out1": hhmm(s["timeout1"]) if s else "",
                "in2": hhmm(s["timein2"]) if s else "", "out2": hhmm(s["timeout2"]) if s else "",
                "reg": numf(s["reghrs"]) if s else (numf(sch["stdhours"]) if sch and not off else ""),
                "tardy": numf(float(s["tardy"] or 0) / 60.0) if s else "",
                "undt": numf(s["undertime"]) if s else "", "np": numf(s["nphrs"]) if s else "",
                "ot": numf(s["othrs"]) if s else "", "total": numf(s["tlhours"]) if s else "",
            })
    return render_template("timecard_edit.html", emp_id=emp_id, emp=emp, rows=rows,
                           dfrom=d0.isoformat(), dto=d1.isoformat())


FUND_SENTINEL = 99999          # loanamt=99999 marks an open-ended Provident Fund, not a fixed loan
PP_LABEL = {"1": "1st payroll", "2": "2nd payroll", "X": "Special payroll"}


def _emp_search(company, term):
    """Find employees by badge number, surname, first name or any part of the name."""
    t = f"%{term.strip().lower()}%"          # wildcards travel as a parameter, never inline
    return q("SELECT RTRIM(emp_id) AS emp_id, RTRIM(lastname)||', '||RTRIM(COALESCE(firstname,''))"
             "||CASE WHEN COALESCE(RTRIM(middlename),'')<>'' THEN ' '||RTRIM(middlename) ELSE '' END AS empname, "
             "RTRIM(COALESCE(empsts,'')) AS empsts, RTRIM(COALESCE(jobcode,'')) AS jobcode "
             "FROM personnel WHERE company=? AND ("
             "  LOWER(RTRIM(emp_id)) LIKE ? OR LOWER(RTRIM(lastname)) LIKE ? "
             "  OR LOWER(RTRIM(COALESCE(firstname,''))) LIKE ? "
             "  OR LOWER(RTRIM(lastname)||', '||RTRIM(COALESCE(firstname,''))) LIKE ?) "
             "ORDER BY lastname, firstname LIMIT 50", company, t, t, t, t)


@app.route("/loans")
def loans():
    """Loans — per-employee loan ledger, mirroring the old app's Loans window.
    Loan Amount = principal + interest; Total Paid = totalpaid + totalpaidi;
    Balance = the difference. Provident Fund rows (loanamt 99999) carry no fixed amount."""
    company = sel_company()
    mode = request.args.get("mode", "PY")
    emp_id = (request.args.get("emp_id") or "").strip()
    include_paid = (request.args.get("paid", "1") == "1")

    def _load(eid):
        return one("SELECT RTRIM(lastname)||', '||RTRIM(COALESCE(firstname,''))"
                   "||CASE WHEN COALESCE(RTRIM(middlename),'')<>'' THEN ' '||RTRIM(middlename) ELSE '' END AS empname, "
                   "RTRIM(COALESCE(empsts,'')) AS empsts FROM personnel WHERE company=? AND RTRIM(emp_id)=?",
                   company, eid)

    # the box takes a badge number, a name, or any part of one
    emp = _load(emp_id) if emp_id else None
    matches = []
    if emp_id and not emp:
        matches = _emp_search(company, emp_id)
        if len(matches) == 1:                       # a single hit just opens
            emp_id = matches[0]["emp_id"]
            emp, matches = _load(emp_id), []
    status = ""
    if emp and emp["empsts"]:
        s = one("SELECT RTRIM(descrip) AS d FROM tablecode1 WHERE tblcode='EST' AND RTRIM(fldcode)=?", emp["empsts"])
        status = s["d"] if s else emp["empsts"]

    rows, tot = [], {"amount": 0.0, "paid": 0.0, "balance": 0.0}
    if emp:
        for r in q("SELECT l.rowid, l.dateapprov, RTRIM(l.payitem) AS payitem, "
                   "RTRIM(COALESCE(i.descrip, l.payitem)) AS descrip, RTRIM(COALESCE(l.refno,'')) AS ltype, "
                   "COALESCE(l.loanamt,0) AS loanamt, COALESCE(l.intamt,0) AS intamt, "
                   "COALESCE(l.totalpaid,0) AS totalpaid, COALESCE(l.totalpaidi,0) AS totalpaidi, "
                   "RTRIM(COALESCE(l.docno,'')) AS docno, COALESCE(l.payded,0) AS payded "
                   "FROM loans l LEFT JOIN payitem i ON i.company=l.company AND i.payitem=l.payitem "
                   "WHERE l.company=? AND l.emp_id=? ORDER BY l.dateapprov DESC", company, emp_id):
            fund = float(r["loanamt"]) >= FUND_SENTINEL
            amount = None if fund else float(r["loanamt"]) + float(r["intamt"])
            paid = float(r["totalpaid"]) + float(r["totalpaidi"])
            balance = 0.0 if fund else round(amount - paid, 2)
            if not include_paid and balance <= 0.005:
                continue                                   # "Include Fully-paid" unticked
            rows.append({"rowid": r["rowid"], "descrip": r["descrip"], "date": r["dateapprov"],
                         "ltype": r["ltype"], "payitem": r["payitem"], "docno": r["docno"],
                         "amount": amount, "paid": paid, "balance": balance,
                         "payded": float(r["payded"]), "fund": fund})
            tot["amount"] += amount or 0.0
            tot["paid"] += paid
            tot["balance"] += balance
    return render_template("loans.html", emp=emp, emp_id=emp_id, status=status, rows=rows,
                           totals=tot, include_paid=include_paid, matches=matches)


@app.route("/loans/payments")
def loan_payments():
    """Payment history for ONE loan — the instalments actually deducted through payroll.
    Each deduction carries the loan's approval stamp in paytranh.trdate2, which is what
    ties it to this loan rather than to another loan of the same type; trdate1 is the
    payroll date the instalment was taken."""
    company = sel_company()
    mode = request.args.get("mode", "PY")
    rowid = request.args.get("rowid", type=int)
    ln = one("SELECT RTRIM(l.emp_id) AS emp_id, RTRIM(l.payitem) AS payitem, l.dateapprov, "
             "RTRIM(COALESCE(i.descrip, l.payitem)) AS descrip, COALESCE(l.loanamt,0) AS loanamt, "
             "COALESCE(l.intamt,0) AS intamt, RTRIM(COALESCE(l.docno,'')) AS docno "
             "FROM loans l LEFT JOIN payitem i ON i.company=l.company AND i.payitem=l.payitem "
             "WHERE l.company=? AND l.rowid=?", company, rowid) if rowid else None
    if not ln:
        abort(404)
    emp = one("SELECT RTRIM(lastname)||', '||RTRIM(COALESCE(firstname,''))"
              "||CASE WHEN COALESCE(RTRIM(middlename),'')<>'' THEN ' '||RTRIM(middlename) ELSE '' END AS empname "
              "FROM personnel WHERE company=? AND RTRIM(emp_id)=?", company, ln["emp_id"])
    raw = q("SELECT t.payyear, t.paymonth, RTRIM(t.payperiod) AS payperiod, t.trdate1 AS paydate, "
            "SUM(t.tramount) AS amt FROM paytranh t "
            "WHERE t.company=? AND RTRIM(t.emp_id)=? AND RTRIM(t.payitem)=? AND t.trdate2=? "
            "GROUP BY t.payyear, t.paymonth, t.payperiod, t.trdate1 "
            "ORDER BY t.payyear, t.paymonth, t.payperiod", company, ln["emp_id"], ln["payitem"], ln["dateapprov"])
    rows, py, pm = [], None, None
    for r in raw:
        y, m = int(r["payyear"]), int(r["paymonth"])
        rows.append({"year": y, "month": m, "show_year": y != py, "show_month": (y, m) != (py, pm),
                     "period": PP_LABEL.get(r["payperiod"], r["payperiod"]),
                     "paydate": r["paydate"], "amt": float(r["amt"] or 0)})
        py, pm = y, m
    amount = float(ln["loanamt"]) + float(ln["intamt"])
    paid = sum(r["amt"] for r in rows)
    return render_template("loan_payments.html", emp=emp, ln=ln, rows=rows, total=paid,
                           amount=(None if float(ln["loanamt"]) >= FUND_SENTINEL else amount))


@app.route("/engine/verify")
def engine_verify():
    company = sel_company()
    periods = q("SELECT DISTINCT TOP 30 payyear, paymonth, payperiod FROM paytranh "
                "WHERE company=? ORDER BY payyear DESC, paymonth DESC, payperiod DESC", company)
    if not periods:
        abort(404)
    d0 = periods[0]
    year = request.args.get("year", type=int) or d0["payyear"]
    month = request.args.get("month", type=int) or d0["paymonth"]
    period = (request.args.get("period") or d0["payperiod"]).strip()
    rep = pe.engine_regression(company, year, month, period)
    return render_template("verify.html", rep=rep, periods=periods,
                           year=year, month=month, period=period)


@app.route("/payslip/<company>/<emp_id>")
def payslip(company, emp_id):
    periods = q("SELECT DISTINCT TOP 40 payyear, paymonth, payperiod FROM paytranh "
                "WHERE company=? AND emp_id=? ORDER BY payyear DESC, paymonth DESC, payperiod DESC",
                company, emp_id)
    if not periods:
        abort(404)
    d0 = periods[0]
    year = request.args.get("year", type=int) or d0["payyear"]
    month = request.args.get("month", type=int) or d0["paymonth"]
    period = (request.args.get("period") or d0["payperiod"]).strip()
    p = one("SELECT RTRIM(firstname) AS firstname, RTRIM(COALESCE(middlename,'')) AS middlename, "
            "RTRIM(lastname) AS lastname, RTRIM(COALESCE(jobcode,'')) AS jobcode, "
            "RTRIM(COALESCE(division,'')) AS division, RTRIM(COALESCE(dept,'')) AS dept, "
            "RTRIM(COALESCE(sssno,'')) AS sssno, RTRIM(COALESCE(tin,'')) AS tin "
            "FROM personnel WHERE company=? AND emp_id=?", company, emp_id)
    if not p:
        abort(404)
    lines = q("SELECT t.payitem, RTRIM(COALESCE(MAX(i.descrip), t.payitem)) AS descrip, "
              "MAX(i.category) AS category, SUM(t.trhours) AS hrs, SUM(t.trdays) AS dys, "
              "SUM(t.tramount) AS amt FROM paytranh t "
              "LEFT JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem "
              "WHERE t.company=? AND t.emp_id=? AND t.payyear=? AND t.paymonth=? AND t.payperiod=? "
              "GROUP BY t.payitem ORDER BY t.payitem", company, emp_id, year, month, period)
    sysitems = {"900": "gross", "901": "taxable", "902": "deductions", "903": "net"}
    totals = {v: 0.0 for v in sysitems.values()}
    earnings, deductions = [], []
    for ln in lines:
        code = ln["payitem"].strip()
        amt = float(ln["amt"] or 0)
        ln["amt"] = amt
        cat = str(ln["category"]).strip() if ln["category"] is not None else ""
        if code in sysitems:
            totals[sysitems[code]] = amt
        elif code.startswith("9") or code.startswith("Z"):
            continue  # employer shares / provident — not on employee payslip body
        elif cat == "4":
            deductions.append(ln)   # statutory + loan deductions (stored positive) → total deductions (902)
        else:
            earnings.append(ln)     # basic/OT/allowances; attendance adjustments net into gross (900)
    return render_template("payslip.html", p=p, company=company, emp_id=emp_id,
                           periods=periods, year=year, month=month, period=period,
                           earnings=earnings, deductions=deductions, totals=totals,
                           comp=one("SELECT RTRIM(companynam) AS nm, RTRIM(COALESCE(address,'')) AS addr, "
                                    "RTRIM(COALESCE(tin,'')) AS tin FROM company WHERE company=?", company))


FORMS = {
    "sss": {"title": "SSS R-3 — Contribution Collection List", "no": "sssno",
            "cols": [("SSS No.", "gno"), ("SS EE", "ee"), ("SS ER", "er"), ("EC", "ec"), ("Total", "tot")]},
    "philhealth": {"title": "PhilHealth RF-1 — Employer Remittance", "no": "phealthno",
                   "cols": [("PhilHealth No.", "gno"), ("EE Share", "ee"), ("ER Share", "er"), ("Total", "tot")]},
    "hdmf": {"title": "Pag-IBIG (HDMF) MCRF — Membership Contribution", "no": "hdmfno",
             "cols": [("Pag-IBIG MID", "gno"), ("EE", "ee"), ("ER", "er"), ("Total", "tot")]},
}


@app.route("/forms/<kind>")
def forms(kind):
    company = sel_company()
    if kind == "alphalist":
        return alphalist_form(company)
    f = FORMS.get(kind)
    if not f:
        abort(404)
    eng = pe.engine()
    emps = q("SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
             f"RTRIM(COALESCE(p.{f['no']},'')) AS gno, pr.salary FROM personnel p "
             "JOIN payroll pr ON pr.company=p.company AND pr.emp_id=p.emp_id "
             "WHERE p.company=? AND p.empsts<>'X' AND RTRIM(COALESCE(p." + f["no"] + ",''))<>'' "
             "ORDER BY p.lastname", company)
    rows, tot = [], {"ee": 0.0, "er": 0.0, "ec": 0.0, "tot": 0.0}
    for e in emps:
        sal = float(e["salary"] or 0)
        if kind == "sss":
            c = eng.sss(sal); ee, er, ec = c["ee"], c["er"], c["ec"]
        elif kind == "philhealth":
            c = eng.philhealth(sal); ee, er, ec = c["ee"], c["er"], 0.0
        else:
            c = eng.hdmf(sal); ee, er, ec = c["ee"], c["er"], 0.0
        t = pe.r2(ee + er + ec)
        rows.append({**e, "ee": ee, "er": er, "ec": ec, "tot": t})
        for k, v in (("ee", ee), ("er", er), ("ec", ec), ("tot", t)):
            tot[k] += v
    tot = {k: pe.r2(v) for k, v in tot.items()}
    return render_template("form_remit.html", f=f, kind=kind, rows=rows, tot=tot,
                           comp=one("SELECT RTRIM(companynam) AS nm, RTRIM(COALESCE(tin,'')) AS tin, "
                                    "RTRIM(COALESCE(sssno,'')) AS sssno, RTRIM(COALESCE(hdmfno,'')) AS hdmfno, "
                                    "RTRIM(COALESCE(phidno,'')) AS phidno FROM company WHERE company=?", company))


def alphalist_form(company):
    year = request.args.get("year", type=int) or 2025
    rows = q("SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname)||' '||RTRIM(COALESCE(p.middlename,'')) AS empname, "
             "RTRIM(COALESCE(p.tin,'')) AS tin, RTRIM(p.empsts) AS empsts, "
             "SUM(CASE WHEN h.payitem='900' THEN h.tramount ELSE 0 END) AS gross, "
             "SUM(CASE WHEN h.payitem='901' THEN h.tramount ELSE 0 END) AS taxable, "
             "SUM(CASE WHEN h.payitem='401' THEN h.tramount ELSE 0 END) AS tax "
             "FROM personnel p JOIN paytranh h ON h.company=p.company AND h.emp_id=p.emp_id "
             "WHERE p.company=? AND h.payyear=? GROUP BY p.emp_id, p.lastname, p.firstname, p.middlename, p.tin, p.empsts "
             "ORDER BY p.lastname", company, year)
    yrs = q("SELECT DISTINCT payyear FROM paytranh WHERE company=? ORDER BY payyear DESC", company)
    tot = {k: pe.r2(sum(float(r[k] or 0) for r in rows)) for k in ("gross", "taxable", "tax")}
    return render_template("form_alphalist.html", rows=rows, tot=tot, year=year, yrs=yrs,
                           comp=one("SELECT RTRIM(companynam) AS nm, RTRIM(COALESCE(tin,'')) AS tin "
                                    "FROM company WHERE company=?", company))


load_lookups()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5098, debug=False)
