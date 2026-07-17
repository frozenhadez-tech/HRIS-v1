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


def compute(company, emp_id, year, month, period, ot_lines=None):
    """Compute one employee's payslip for a period. ot_lines: optional list of
    {payitem, hours} to add overtime/hours-based entries. Returns the full breakdown."""
    eng = engine()
    pr = one("SELECT salary, RTRIM(COALESCE(paytype,'')) AS paytype, RTRIM(COALESCE(paygroup,'')) AS paygroup "
             "FROM payroll WHERE company=? AND emp_id=?", company, emp_id)
    if not pr:
        return None
    salary = float(pr["salary"] or 0)
    paytype = pr["paytype"] or "M"
    p = eng.coparam.get(company, {"baseday": 26.083, "hrspday": 8})
    earnings, deductions = [], []

    def add_e(item, desc, amt, cat, ts, hours=None):
        earnings.append({"payitem": item, "descrip": desc, "amount": r2(amt), "cat": cat, "ts": ts, "hours": hours})

    def add_d(item, desc, amt, cat):
        deductions.append({"payitem": item, "descrip": desc, "amount": r2(amt), "cat": cat})

    # 1) Basic pay
    basic = salary / 2 if paytype == "M" else salary * (p["baseday"] / 2)
    add_e("001", "Basic Pay", basic, "0", "3")

    # 2) Overtime / hours-based entries (item multipliers from payitem)
    for ot in (ot_lines or []):
        hrs = float(ot.get("hours") or 0)
        if not hrs:
            continue
        pit = one("SELECT RTRIM(COALESCE(descrip,payitem)) AS descrip, mult, multm, RTRIM(COALESCE(category,'7')) AS cat, "
                  "RTRIM(COALESCE(taxscheme,'3')) AS ts FROM payitem WHERE company=? AND payitem=?", company, ot["payitem"])
        if not pit:
            continue
        amt = eng.line_amount(hrs, salary, paytype, float(pit["mult"] or 0), float(pit["multm"] or 0), company)
        add_e(ot["payitem"], pit["descrip"], amt, pit["cat"], pit["ts"], hours=hrs)

    # 3) Fixed allowances
    for a in q("SELECT f.payitem, RTRIM(COALESCE(i.descrip,f.payitem)) AS descrip, f.amount, "
               "RTRIM(COALESCE(i.category,'3')) AS cat, RTRIM(COALESCE(i.taxscheme,'0')) AS ts "
               "FROM fixallow f LEFT JOIN payitem i ON i.company=f.company AND i.payitem=f.payitem "
               "WHERE f.company=? AND f.emp_id=?", company, emp_id):
        add_e(a["payitem"], a["descrip"], float(a["amount"] or 0), a["cat"], a["ts"])

    # 4) Statutory contributions — the app deducts PhilHealth+HDMF in period 1, SSS in period 2
    sss, ph, hd = eng.sss(salary), eng.philhealth(salary), eng.hdmf(salary)
    if period == "1":
        add_d("403", "PhilHealth Contribution", ph["ee"], "4")
        add_d("404", "HDMF Contribution", hd["ee"], "4")
    elif period == "2":
        add_d("402", "SSS Contribution", sss["ee"], "4")

    # 5) Fixed deductions + active loans
    for d in q("SELECT f.payitem, RTRIM(COALESCE(i.descrip,f.payitem)) AS descrip, f.amount "
               "FROM fixded f LEFT JOIN payitem i ON i.company=f.company AND i.payitem=f.payitem "
               "WHERE f.company=? AND f.emp_id=?", company, emp_id):
        add_d(d["payitem"], d["descrip"], float(d["amount"] or 0), "4")
    for ln in q("SELECT l.payitem, RTRIM(COALESCE(i.descrip,l.payitem)) AS descrip, l.payded "
                "FROM loans l LEFT JOIN payitem i ON i.company=l.company AND i.payitem=l.payitem "
                "WHERE l.company=? AND l.emp_id=? AND COALESCE(l.loanamt,0)-COALESCE(l.totalpaid,0) > 0 "
                "AND COALESCE(l.payded,0) > 0", company, emp_id):
        add_d(ln["payitem"], ln["descrip"], float(ln["payded"] or 0), "8")

    # 6) Totals
    gross = r2(sum(e["amount"] for e in earnings))
    mandatory = sum(d["amount"] for d in deductions if d["payitem"] in ("402", "403", "404"))
    reg_taxable = sum(e["amount"] for e in earnings if e["cat"] in REG_TAX_CATS and e["ts"] == "3")
    mwe = is_mwe(company, salary, paytype)
    taxable = 0.0 if mwe else r2(reg_taxable - mandatory)
    tax = 0.0 if mwe else eng.withholding_tax(taxable, "S")
    if tax:
        add_d("401", "Withholding Tax", tax, "4")
    total_ded = r2(sum(d["amount"] for d in deductions))
    net = r2(gross - total_ded)

    return {"emp_id": emp_id, "salary": salary, "paytype": paytype, "mwe": mwe,
            "earnings": earnings, "deductions": deductions,
            "gross": gross, "taxable": taxable, "tax": tax, "total_ded": total_ded, "net": net}


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
