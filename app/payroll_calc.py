"""Full-period payroll calculation — computes an employee's payslip the way the
original app does, from master setup + entered lines. Every rule here was verified
against the app's stored history (see CALC_SPEC.md and /engine/verify):

  Basic pay (monthly) = salary / 2 per semi-monthly period
  Pay line            = hours * hourly_rate * multiplier   (multm monthly / mult daily)
  SSS/PhilHealth/HDMF = statutory calculators
  Gross               = Σ earnings (categories 0,1,2,3,5,6,7)
  Withholding taxable = Σ regular comp (cat 0,1,2,7, taxscheme='3') − mandatory EE
                        (0 for minimum-wage earners)
  Withholding tax     = BIR TRAIN table on the per-period taxable
  Total deductions    = Σ deductions (categories 4,8,9)
  Net                 = Gross − Total deductions
"""
from __future__ import annotations

import datetime
import psycopg

import db
from db import q, one
from payroll_engine import engine, r2

EARN_CATS = {"0", "1", "2", "3", "5", "6", "7"}
REG_TAX_CATS = {"0", "1", "2", "7"}       # regular compensation (subject to per-period withholding)


def is_mwe(company, salary, paytype):
    """Minimum-wage earner: daily rate <= regional minimum daily wage → tax-exempt."""
    p = engine().coparam.get(company, {})
    md = p.get("mindaily", 0)
    if not md:
        return False
    daily = salary if paytype == "D" else (salary / p.get("baseday", 26.083))
    return daily <= md + 0.005


def _core(company, emp_id, salary, paytype, period, fixallow, fixded, loans, ot_resolved, eng):
    """Core payslip math from already-loaded inputs. Shared by compute() and compute_batch().
    fixallow/fixded/loans: lists of dicts; ot_resolved: list of {payitem,descrip,hours,mult,multm,cat,ts}."""
    p = eng.coparam.get(company, {"baseday": 26.083, "hrspday": 8})
    earnings, deductions = [], []

    def add_e(item, desc, amt, cat, ts, hours=None):
        earnings.append({"payitem": item, "descrip": desc, "amount": r2(amt), "cat": cat, "ts": ts, "hours": hours})

    def add_d(item, desc, amt, cat):
        deductions.append({"payitem": item, "descrip": desc, "amount": r2(amt), "cat": cat})

    basic = salary / 2 if paytype == "M" else salary * (p["baseday"] / 2)
    add_e("001", "Basic Pay", basic, "0", "3")
    for ot in (ot_resolved or []):
        hrs = float(ot.get("hours") or 0)
        if not hrs:
            continue
        amt = eng.line_amount(hrs, salary, paytype, float(ot.get("mult") or 0), float(ot.get("multm") or 0), company)
        add_e(ot["payitem"], ot["descrip"], amt, ot.get("cat", "7"), ot.get("ts", "3"), hours=hrs)
    for a in fixallow:
        add_e(a["payitem"].strip(), a["descrip"], float(a["amount"] or 0), (a.get("cat") or "3"), (a.get("ts") or "0"))
    sss, ph, hd = eng.sss(salary), eng.philhealth(salary), eng.hdmf(salary)
    if period == "1":
        add_d("403", "PhilHealth Contribution", ph["ee"], "4")
        add_d("404", "HDMF Contribution", hd["ee"], "4")
    elif period == "2":
        add_d("402", "SSS Contribution", sss["ee"], "4")
    for d in fixded:
        add_d(d["payitem"].strip(), d["descrip"], float(d["amount"] or 0), "4")
    for ln in loans:
        add_d(ln["payitem"].strip(), ln["descrip"], float(ln["payded"] or 0), "8")

    gross = r2(sum(e["amount"] for e in earnings))
    mandatory = sum(d["amount"] for d in deductions if d["payitem"] in ("402", "403", "404"))
    reg_taxable = sum(e["amount"] for e in earnings if e["cat"] in REG_TAX_CATS and e["ts"] == "3")
    mwe = is_mwe(company, salary, paytype)
    taxable = 0.0 if mwe else r2(reg_taxable - mandatory)
    tax = 0.0 if mwe else eng.withholding_tax(taxable, "S")
    if tax:
        add_d("401", "Withholding Tax", tax, "4")
    total_ded = r2(sum(d["amount"] for d in deductions))
    return {"emp_id": emp_id, "salary": salary, "paytype": paytype, "mwe": mwe,
            "earnings": earnings, "deductions": deductions, "gross": gross, "taxable": taxable,
            "tax": tax, "total_ded": total_ded, "net": r2(gross - total_ded),
            "er": {"sss": sss["er"], "ec": sss["ec"], "philhealth": ph["er"], "hdmf": hd["er"]}}


def _ot_for_period(company, year, month, period):
    """Persisted per-employee overtime entries for a period -> {emp_id: [ot dicts]}."""
    from collections import defaultdict
    m = defaultdict(list)
    for r in q("SELECT RTRIM(o.emp_id) AS emp_id, o.payitem, RTRIM(COALESCE(i.descrip,o.payitem)) AS descrip, "
               "o.hours, i.mult, i.multm, RTRIM(COALESCE(i.category,'7')) AS cat, RTRIM(COALESCE(i.taxscheme,'3')) AS ts "
               "FROM ot_entry o LEFT JOIN payitem i ON i.company=o.company AND i.payitem=o.payitem "
               "WHERE o.company=? AND o.payyear=? AND o.paymonth=? AND o.payperiod=?", company, year, month, period):
        m[r["emp_id"]].append({"payitem": r["payitem"].strip(), "descrip": r["descrip"], "hours": float(r["hours"] or 0),
                               "mult": r["mult"], "multm": r["multm"], "cat": r["cat"], "ts": r["ts"]})
    return m


def compute(company, emp_id, year, month, period, ot_lines=None):
    """Compute one employee's payslip for a period. ot_lines: optional [{payitem, hours}]
    added on top of the employee's persisted OT entries for the period."""
    eng = engine()
    pr = one("SELECT salary, RTRIM(COALESCE(paytype,'')) AS paytype FROM payroll WHERE company=? AND emp_id=?",
             company, emp_id)
    if not pr:
        return None
    fixallow = q("SELECT f.payitem, RTRIM(COALESCE(i.descrip,f.payitem)) AS descrip, f.amount, "
                 "RTRIM(COALESCE(i.category,'3')) AS cat, RTRIM(COALESCE(i.taxscheme,'0')) AS ts "
                 "FROM fixallow f LEFT JOIN payitem i ON i.company=f.company AND i.payitem=f.payitem "
                 "WHERE f.company=? AND f.emp_id=?", company, emp_id)
    fixded = q("SELECT f.payitem, RTRIM(COALESCE(i.descrip,f.payitem)) AS descrip, f.amount "
               "FROM fixded f LEFT JOIN payitem i ON i.company=f.company AND i.payitem=f.payitem "
               "WHERE f.company=? AND f.emp_id=?", company, emp_id)
    loans = q("SELECT l.payitem, RTRIM(COALESCE(i.descrip,l.payitem)) AS descrip, l.payded "
              "FROM loans l LEFT JOIN payitem i ON i.company=l.company AND i.payitem=l.payitem "
              "WHERE l.company=? AND l.emp_id=? AND COALESCE(l.loanamt,0)-COALESCE(l.totalpaid,0)>0 "
              "AND COALESCE(l.payded,0)>0", company, emp_id)
    otr = list(_ot_for_period(company, year, month, period).get(emp_id, []))
    for ot in (ot_lines or []):
        pit = one("SELECT RTRIM(COALESCE(descrip,payitem)) AS descrip, mult, multm, RTRIM(COALESCE(category,'7')) AS cat, "
                  "RTRIM(COALESCE(taxscheme,'3')) AS ts FROM payitem WHERE company=? AND payitem=?", company, ot["payitem"])
        if pit and ot.get("hours"):
            otr.append({"payitem": ot["payitem"], "hours": ot["hours"], **pit})
    return _core(company, emp_id, float(pr["salary"] or 0), pr["paytype"] or "M", period,
                 fixallow, fixded, loans, otr, eng)


def compute_batch(company, year, month, period):
    """Compute every active employee for a period — bulk-preloads all inputs, then computes
    in Python (a handful of queries, not N×). Returns (rows, totals)."""
    from collections import defaultdict
    eng = engine()
    emps = q("SELECT RTRIM(pr.emp_id) AS emp_id, pr.salary, RTRIM(COALESCE(pr.paytype,'')) AS paytype, "
             "RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname "
             "FROM payroll pr JOIN personnel p ON p.company=pr.company AND p.emp_id=pr.emp_id "
             "WHERE pr.company=? AND p.empsts<>'X' ORDER BY p.lastname, p.firstname", company)
    fa = defaultdict(list)
    for r in q("SELECT RTRIM(f.emp_id) AS emp_id, f.payitem, RTRIM(COALESCE(i.descrip,f.payitem)) AS descrip, f.amount, "
               "RTRIM(COALESCE(i.category,'3')) AS cat, RTRIM(COALESCE(i.taxscheme,'0')) AS ts "
               "FROM fixallow f LEFT JOIN payitem i ON i.company=f.company AND i.payitem=f.payitem WHERE f.company=?", company):
        fa[r["emp_id"]].append(r)
    fd = defaultdict(list)
    for r in q("SELECT RTRIM(f.emp_id) AS emp_id, f.payitem, RTRIM(COALESCE(i.descrip,f.payitem)) AS descrip, f.amount "
               "FROM fixded f LEFT JOIN payitem i ON i.company=f.company AND i.payitem=f.payitem WHERE f.company=?", company):
        fd[r["emp_id"]].append(r)
    ln = defaultdict(list)
    for r in q("SELECT RTRIM(l.emp_id) AS emp_id, l.payitem, RTRIM(COALESCE(i.descrip,l.payitem)) AS descrip, l.payded "
               "FROM loans l LEFT JOIN payitem i ON i.company=l.company AND i.payitem=l.payitem "
               "WHERE l.company=? AND COALESCE(l.loanamt,0)-COALESCE(l.totalpaid,0)>0 AND COALESCE(l.payded,0)>0", company):
        ln[r["emp_id"]].append(r)
    ot = _ot_for_period(company, year, month, period)
    rows = []
    tot = {"gross": 0.0, "taxable": 0.0, "tax": 0.0, "total_ded": 0.0, "net": 0.0}
    for e in emps:
        emp = e["emp_id"]
        r = _core(company, emp, float(e["salary"] or 0), e["paytype"] or "M", period,
                  fa.get(emp, []), fd.get(emp, []), ln.get(emp, []), ot.get(emp, []), eng)
        r["empname"] = e["empname"]
        rows.append(r)
        for k in tot:
            tot[k] = r2(tot[k] + r[k])
    return rows, tot


def validate(company, year, month, period, tol=1.0):
    """Compute each employee from master setup + their stored OT hours, and compare the
    totals to what the app stored — proves the end-to-end calculation."""
    emps = q("SELECT DISTINCT h.emp_id FROM paytranh h WHERE h.company=? AND h.payyear=? "
             "AND h.paymonth=? AND h.payperiod=?", company, year, month, period)
    checks = {"gross": [0, 0], "taxable": [0, 0], "net": [0, 0]}
    for e in emps:
        emp = e["emp_id"].strip()
        stored = {r["payitem"].strip(): float(r["amt"]) for r in q(
            "SELECT payitem, SUM(tramount) AS amt FROM paytranh WHERE company=? AND emp_id=? "
            "AND payyear=? AND paymonth=? AND payperiod=? AND payitem IN ('900','901','903') "
            "GROUP BY payitem", company, emp, year, month, period)}
        if not stored:
            continue
        # feed the employee's actual OT hours from history so we compare like-for-like
        ot = q("SELECT h.payitem, SUM(h.trhours) AS hours FROM paytranh h "
               "JOIN payitem i ON i.company=h.company AND i.payitem=h.payitem "
               "WHERE h.company=? AND h.emp_id=? AND h.payyear=? AND h.paymonth=? AND h.payperiod=? "
               "AND RTRIM(COALESCE(i.unmsr,''))='H' AND i.category='7' GROUP BY h.payitem",
               company, emp, year, month, period)
        r = compute(company, emp, year, month, period, ot_lines=[{"payitem": o["payitem"], "hours": float(o["hours"])} for o in ot])
        if not r:
            continue
        for k, code in (("gross", "900"), ("taxable", "901"), ("net", "903")):
            if code in stored:
                checks[k][1] += 1
                if abs(r[k] - stored[code]) <= tol:
                    checks[k][0] += 1
    return {k: {"match": v[0], "n": v[1], "rate": (100 * v[0] / v[1]) if v[1] else None}
            for k, v in checks.items()}


def period_status(company, year, month, period):
    """Existing rows/employees + closed status for a period (posting guard + UI)."""
    r = one("SELECT COUNT(*) AS rows, COUNT(DISTINCT emp_id) AS emps FROM paytranh "
            "WHERE company=? AND payyear=? AND paymonth=? AND payperiod=?", company, year, month, period)
    cl = one("SELECT closed_by, closed_at FROM period_close "
             "WHERE company=? AND payyear=? AND paymonth=? AND payperiod=?", company, year, month, period)
    return {"rows": r["rows"], "emps": r["emps"], "closed": bool(cl),
            "closed_by": (cl["closed_by"] if cl else None), "closed_at": (cl["closed_at"] if cl else None)}


def post_period(company, year, month, period, user, overwrite=False):
    """Write the computed batch to paytranh so it flows into payslips/registers/forms.
    Writes each earning/deduction line plus the system totals 900-907. Atomic; if the
    period already has rows it only proceeds with overwrite=True (delete + replace)."""
    rows, totals = compute_batch(company, year, month, period)
    pg = {r["emp_id"].strip(): (r["paygroup"] or "M")
          for r in q("SELECT RTRIM(emp_id) AS emp_id, RTRIM(COALESCE(paygroup,'M')) AS paygroup "
                     "FROM payroll WHERE company=?", company)}
    now = datetime.datetime.now()
    cols = ("company,payyear,paymonth,payperiod,paygroup,recno,seqno,rtype,emp_id,payitem,"
            "paycat,trhours,tramount,changeby,changedate")
    ph = "(" + ",".join(["%s"] * 15) + ")"
    n = 0
    with psycopg.connect(db._dsn(), autocommit=False) as c:
        cur = c.cursor()
        if overwrite:
            cur.execute("DELETE FROM paytranh WHERE company=%s AND payyear=%s AND paymonth=%s AND payperiod=%s",
                        (company, year, month, period))
        batch = []
        for recno, r in enumerate(rows, start=1):
            emp, grp, seq = r["emp_id"], pg.get(r["emp_id"], "M"), 0
            lines = [(e["payitem"], e["cat"], e["amount"], e.get("hours")) for e in r["earnings"]]
            lines += [(d["payitem"], d["cat"], d["amount"], None) for d in r["deductions"]]
            er = r["er"]
            lines += [("900", "9", r["gross"], None), ("901", "9", r["taxable"], None),
                      ("902", "9", r["total_ded"], None), ("903", "9", r["net"], None),
                      ("904", "9", er["hdmf"], None), ("905", "9", er["sss"], None),
                      ("906", "9", er["philhealth"], None), ("907", "9", er["ec"], None)]
            for payitem, paycat, amt, hrs in lines:
                seq += 1
                batch.append((company, year, month, period, grp, recno, seq, "R", emp,
                              payitem, paycat, hrs, amt, user, now))
        cur.executemany(f"INSERT INTO paytranh ({cols}) VALUES {ph}", batch)
        n = len(batch)
        # mark the period closed (own status table) + best-effort legacy payperiod flag
        cur.execute("INSERT INTO period_close (company,payyear,paymonth,payperiod,closed_by,closed_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (company,payyear,paymonth,payperiod) "
                    "DO UPDATE SET closed_by=EXCLUDED.closed_by, closed_at=EXCLUDED.closed_at",
                    (company, year, month, period, user, now))
        cur.execute("UPDATE payperiod SET payclose='9', changeby=%s, changedate=%s "
                    "WHERE company=%s AND payyear=%s AND paymonth=%s AND payperiod=%s",
                    (user, now, company, year, month, period))
        c.commit()
    return {"employees": len(rows), "lines": n, "net": totals["net"]}
