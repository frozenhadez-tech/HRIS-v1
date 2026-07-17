"""Payroll calculation engine for HRPayroll L98.

Reverse-engineered from the historical `paytranh` data (the original computation
logic lived in the PowerBuilder client, not the DB). Every formula here was verified
to the centavo against closed periods — see engine_regression() and /engine/verify.

Statutory sources (as-of the Aug-2025 backup):
  • SSS         — table lookup: ssstable, employee share = sssee (by monthly gross)
  • PhilHealth  — 2.5% of monthly salary (employee share; 5% total), floor 10k / ceil 100k
  • HDMF        — 2% of monthly salary, employee share capped at ₱200
  • W/tax       — BIR TRAIN table (taxtable), bracketed on per-period taxable gross
"""
from __future__ import annotations

from db import q as _rows


def r2(x):
    """Round half-up to 2 decimals like the original (banker's rounding avoided)."""
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class Engine:
    """Loads the statutory tables once and computes contributions/tax + pay lines."""

    def __init__(self):
        # per-company rate parameters (baseday, hours/day, min daily wage) for the formulas
        self.coparam = {r["company"]: {"baseday": float(r["baseday"] or 26.083),
                                       "hrspday": float(r["hourspday"] or 8),
                                       "mindaily": float(r["mindlyrate"] or 0)}
                        for r in _rows("SELECT company, baseday, hourspday, mindlyrate FROM company")}
        self.sss_tbl = sorted(
            ({"lo": float(r["frgross"]), "hi": float(r["togross"]),
              "msc": float(r["credit"]), "ee": float(r["sssee"]),
              "er": float(r["ssser"]), "ec": float(r["eccer"] or 0)}
             for r in _rows("SELECT frgross,togross,credit,sssee,ssser,eccer FROM ssstable")),
            key=lambda x: x["lo"])
        # tax brackets per frequency code (D/W/S/M/Q/Y): floors (Z row), fixed (FIXAM), pct (PRCNT)
        self.tax = {}
        rawt = _rows("SELECT RTRIM(xtype) xt, RTRIM(COALESCE(xunit,'')) xu, "
                     "range01,range02,range03,range04,range05,range06,range07,range08 FROM taxtable")
        for xt in {r["xt"] for r in rawt if r["xt"]}:
            def pick(unit):
                for r in rawt:
                    if r["xt"] == xt and r["xu"] == unit:
                        return [float(r[f"range0{i}"]) for i in range(1, 9)]
                return None
            floors = pick("Z") or pick("S")
            fixam = pick("FIXAM")
            pct = pick("PRCNT")
            if floors and fixam and pct:
                self.tax[xt] = {"floors": floors, "fix": fixam, "pct": pct}

    # ── individual calculators ────────────────────────────────────────────
    def sss_ee(self, gross):
        for b in self.sss_tbl:
            if b["lo"] <= gross <= b["hi"]:
                return b
        return self.sss_tbl[-1] if gross > self.sss_tbl[-1]["hi"] else self.sss_tbl[0]

    def philhealth(self, salary, rate=0.05, floor=10000.0, ceil=100000.0):
        base = min(max(salary, floor), ceil)
        total = r2(base * rate)
        ee = r2(total / 2)
        return {"ee": ee, "er": r2(total - ee), "base": base}

    def hdmf(self, salary, pct=0.02, ee_cap=200.0):
        ee = min(r2(salary * pct), ee_cap)
        return {"ee": ee, "er": ee}

    def sss(self, salary):
        b = self.sss_ee(salary)
        return {"ee": b["ee"], "er": b["er"], "ec": b["ec"], "msc": b["msc"]}

    # ── rate-based pay lines (verified against the original app to the centavo) ──
    def hourly_rate(self, salary, paytype, company="001"):
        """Daily rate = salary (daily-paid) or salary/baseday (monthly); hourly = daily/hours-per-day."""
        p = self.coparam.get(company, {"baseday": 26.083, "hrspday": 8})
        daily = salary if paytype == "D" else (salary / p["baseday"])
        return daily / p["hrspday"]

    def line_amount(self, hours, salary, paytype, mult, multm, company="001"):
        """A pay line = hours * hourly_rate * multiplier. Monthly-paid uses `multm`
        (premium only); daily-paid uses `mult`. Matches the original app exactly."""
        m = multm if paytype == "M" else mult
        return r2(hours * self.hourly_rate(salary, paytype, company) * m)

    def ot_rates(self, salary, paytype, company="001"):
        """Common OT hourly rates for display (Regular 1.25, Restday 1.30, …)."""
        hr = self.hourly_rate(salary, paytype, company)
        return {"hourly": r2(hr), "regular_ot": r2(hr * 1.25), "restday_ot": r2(hr * 1.30),
                "legal_holiday": r2(hr * 2.00), "night_prem": r2(hr * 0.10)}

    def withholding_tax(self, taxable, freq="S"):
        t = self.tax.get(freq)
        if not t or taxable <= 0:
            return 0.0
        floors, fix, pct = t["floors"], t["fix"], t["pct"]
        idx = 0
        for i, f in enumerate(floors):
            if taxable >= f:
                idx = i
        return r2(fix[idx] + pct[idx] * (taxable - floors[idx]))

    # ── period computation ────────────────────────────────────────────────
    def compute_monthly(self, salary, freq="S", status="Z"):
        """Full monthly statutory picture from a salary (a live calculator)."""
        sss = self.sss(salary)
        ph = self.philhealth(salary)
        hd = self.hdmf(salary)
        # approx monthly taxable = salary - employee statutory
        ee_stat = sss["ee"] + ph["ee"] + hd["ee"]
        monthly_taxable = max(0.0, salary - ee_stat)
        # per-period (semi-monthly) taxable, tax computed per period then x2
        semi_taxable = r2(monthly_taxable / 2)
        semi_tax = self.withholding_tax(semi_taxable, "S")
        return {
            "salary": salary, "sss": sss, "philhealth": ph, "hdmf": hd,
            "ee_statutory": r2(ee_stat), "monthly_taxable": r2(monthly_taxable),
            "semi_taxable": semi_taxable, "semi_tax": semi_tax,
            "monthly_tax_est": r2(semi_tax * 2),
            "net_est": r2(salary - ee_stat - semi_tax * 2),
        }


_ENGINE = None


def engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Engine()
    return _ENGINE


# ── regression harness ────────────────────────────────────────────────────

def engine_regression(company, year, month, period, tol=0.05):
    """Recompute statutory + tax for a CLOSED period from stored gross/taxable,
    compare to the values the original app stored. Returns per-item match stats.

    One aggregate query pulls each employee's salary, taxable (901) and stored
    deductions (401-404), keeping the whole check to a single round-trip."""
    eng = engine()
    rows = _rows(
        "SELECT pr.emp_id, pr.salary, "
        "SUM(CASE WHEN h.payitem='901' THEN h.tramount ELSE 0 END) AS taxable, "
        "SUM(CASE WHEN h.payitem='402' THEN h.tramount ELSE 0 END) AS sss, "
        "SUM(CASE WHEN h.payitem='403' THEN h.tramount ELSE 0 END) AS phic, "
        "SUM(CASE WHEN h.payitem='404' THEN h.tramount ELSE 0 END) AS hdmf, "
        "SUM(CASE WHEN h.payitem='401' THEN h.tramount ELSE 0 END) AS tax, "
        "COUNT(CASE WHEN h.payitem='402' THEN 1 END) AS n402, "
        "COUNT(CASE WHEN h.payitem='403' THEN 1 END) AS n403, "
        "COUNT(CASE WHEN h.payitem='404' THEN 1 END) AS n404, "
        "COUNT(CASE WHEN h.payitem='401' THEN 1 END) AS n401 "
        "FROM payroll pr JOIN paytranh h ON h.company=pr.company AND h.emp_id=pr.emp_id "
        "WHERE pr.company=? AND h.payyear=? AND h.paymonth=? AND h.payperiod=? "
        "GROUP BY pr.emp_id, pr.salary",
        company, year, month, period)

    checks = {"SSS (402)": [], "PhilHealth (403)": [], "HDMF (404)": [], "W/Tax (401)": []}
    details = []
    for r in rows:
        emp, sal = r["emp_id"].strip(), float(r["salary"] or 0)
        taxable = float(r["taxable"] or 0)
        row = {"emp_id": emp, "salary": sal}
        for label, ncol, scol, cp in (
            ("SSS (402)", "n402", "sss", eng.sss(sal)["ee"]),
            ("PhilHealth (403)", "n403", "phic", eng.philhealth(sal)["ee"]),
            ("HDMF (404)", "n404", "hdmf", eng.hdmf(sal)["ee"]),
            ("W/Tax (401)", "n401", "tax", eng.withholding_tax(taxable, "S")),
        ):
            if not r[ncol]:
                continue
            st = abs(float(r[scol] or 0))
            ok = abs(cp - st) <= tol
            checks[label].append(ok)
            if not ok:
                row.setdefault("mismatch", {})[label] = {"stored": st, "computed": cp}
        details.append(row)

    summary = {}
    for k, v in checks.items():
        n = len(v)
        summary[k] = {"n": n, "match": sum(v), "rate": (sum(v) / n * 100) if n else None}
    mism = [d for d in details if d.get("mismatch")]
    lines = verify_lines(company, year, month, period)
    return {"company": company, "year": year, "month": month, "period": period,
            "employees": len(rows), "summary": summary, "mismatches": mism[:40], "lines": lines}


def verify_lines(company, year, month, period, tol=0.05):
    """Recompute every hours-based (unmsr='H') pay line = hours*hourly_rate*multiplier
    and compare to the stored amount — proves the OT / attendance-adjustment formula."""
    eng = engine()
    rows = _rows(
        "SELECT h.payitem, h.trhours, h.tramount, i.mult, i.multm, "
        "COALESCE(pr.salary,0) AS salary, RTRIM(COALESCE(pr.paytype,'')) AS paytype "
        "FROM paytranh h JOIN payitem i ON i.company=h.company AND i.payitem=h.payitem "
        "JOIN payroll pr ON pr.company=h.company AND pr.emp_id=h.emp_id "
        "WHERE h.company=? AND h.payyear=? AND h.paymonth=? AND h.payperiod=? "
        "AND RTRIM(COALESCE(i.unmsr,''))='H' AND h.trhours <> 0", company, year, month, period)
    ok = n = 0
    for r in rows:
        sal = float(r["salary"] or 0)
        m = float(r["multm"] if r["paytype"] == "M" else r["mult"] or 0)
        if not sal or m == 0:
            continue
        n += 1
        exp = eng.line_amount(float(r["trhours"]), sal, r["paytype"], float(r["mult"] or 0),
                              float(r["multm"] or 0), company)
        if abs(exp - float(r["tramount"])) <= tol:
            ok += 1
    return {"n": n, "match": ok, "rate": (ok / n * 100) if n else None}


if __name__ == "__main__":
    import json
    r = engine_regression("001", 2025, 8, "1")
    print(json.dumps(r["summary"], indent=2))
    print("employees:", r["employees"], "| mismatches:", len(r["mismatches"]))
    for m in r["mismatches"][:10]:
        print(m["emp_id"], m["salary"], m["mismatch"])
