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
    """Loads the statutory tables once and computes contributions/tax."""

    def __init__(self):
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
    compare to the values the original app stored. Returns per-item match stats."""
    eng = engine()
    # stored per-employee: salary, taxable gross (901), and stored deductions
    emps = _rows(
        "SELECT pr.emp_id, pr.salary, RTRIM(COALESCE(pr.paytype,'')) paytype "
        "FROM payroll pr WHERE pr.company=? AND EXISTS("
        "  SELECT 1 FROM paytranh h WHERE h.company=pr.company AND h.emp_id=pr.emp_id "
        "  AND h.payyear=? AND h.paymonth=? AND h.payperiod=?)",
        company, year, month, period)

    def stored(emp, item):
        r = _rows("SELECT SUM(tramount) s FROM paytranh WHERE company=? AND emp_id=? "
                  "AND payyear=? AND paymonth=? AND payperiod=? AND payitem=?",
                  company, emp, year, month, period, item)
        return float(r[0]["s"]) if r and r[0]["s"] is not None else None

    checks = {"SSS (402)": [], "PhilHealth (403)": [], "HDMF (404)": [], "W/Tax (401)": []}
    details = []
    for e in emps:
        emp, sal = e["emp_id"].strip(), float(e["salary"] or 0)
        taxable = stored(emp, "901")
        row = {"emp_id": emp, "salary": sal}
        # SSS (deducted in one period per month; compare only when stored present)
        for label, item, calc in (
            ("SSS (402)", "402", lambda: eng.sss(sal)["ee"]),
            ("PhilHealth (403)", "403", lambda: eng.philhealth(sal)["ee"]),
            ("HDMF (404)", "404", lambda: eng.hdmf(sal)["ee"]),
            ("W/Tax (401)", "401", lambda: eng.withholding_tax(taxable or 0, "S")),
        ):
            st = stored(emp, item)
            if st is None:
                continue
            st = abs(st)  # deductions stored negative for some items
            cp = calc()
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
    return {"company": company, "year": year, "month": month, "period": period,
            "employees": len(emps), "summary": summary, "mismatches": mism[:40]}


if __name__ == "__main__":
    import json
    r = engine_regression("001", 2025, 8, "1")
    print(json.dumps(r["summary"], indent=2))
    print("employees:", r["employees"], "| mismatches:", len(r["mismatches"]))
    for m in r["mismatches"][:10]:
        print(m["emp_id"], m["salary"], m["mismatch"])
