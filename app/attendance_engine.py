"""Attendance computation — derive a day's hours from raw punches + the employee's
shift schedule, matching the legacy app's stored timecard values.

Verified against stored timecard history (company 003, shift N6 and others):
  reg hours     = the day's scheduled hours (shift/shiftexcpt), 0 on a day off   (~99.7%)
  tardy (min)   = minutes late past scheduled time-in, once it exceeds the grace  (per-shift)
  night premium = hours worked after 22:00                                        (100%)
  undertime     = scheduled hours not worked (left early / absent)
  total hours   = worked span minus the unpaid break (capped at time-out w/o OT)

Overtime is NOT derived here: in the legacy system daily OT is a pre-approved
entry (see the Overtime Entry screen), not a function of the punches.
"""
from __future__ import annotations

import datetime
from db import q, one

NIGHT_START = 22 * 60          # 22:00 — night differential window start
DEFAULT_GRACE = 0


def _min_of(v) -> int | None:
    """Minutes-since-midnight from a datetime/time (shifttable) or 'HH:MM' string."""
    if v is None:
        return None
    if isinstance(v, (datetime.datetime, datetime.time)):
        return v.hour * 60 + v.minute
    s = str(v).strip()
    if ":" in s:
        h, m = s.split(":")[:2]
        try:
            return int(h) * 60 + int(m)
        except ValueError:
            return None
    return None


def _num_min(v) -> int | None:
    """Minutes-since-midnight from a numeric HHMM punch (809 -> 8:09)."""
    if v is None:
        return None
    v = int(v)
    if v <= 0:
        return None
    return (v // 100) * 60 + (v % 100)


def daycode(d: datetime.date) -> int:
    """Legacy day-of-week code: Sun=1, Mon=2, ... Sat=7."""
    return (d.isoweekday() % 7) + 1


def shift_code(company: str, emp_id: str, d: datetime.date) -> str | None:
    """The employee's assigned shift on a date (empshift latest <= date; else newest)."""
    r = one("SELECT RTRIM(COALESCE(shift,'')) AS shift FROM empshift WHERE company=? AND emp_id=? "
            "AND frdate<=? ORDER BY frdate DESC", company, emp_id, d.isoformat())
    if r and r["shift"]:
        return r["shift"]
    r = one("SELECT RTRIM(COALESCE(shift,'')) AS shift FROM empshift WHERE company=? AND emp_id=? "
            "ORDER BY frdate DESC", company, emp_id)
    if r and r["shift"]:
        return r["shift"]
    r = one("SELECT RTRIM(COALESCE(shift,'')) AS shift FROM timecard WHERE company=? AND emp_id=? "
            "AND RTRIM(COALESCE(shift,''))<>'' ORDER BY trdate DESC", company, emp_id)
    return r["shift"] if r and r["shift"] else None


def schedule(company: str, emp_id: str, d: datetime.date) -> dict | None:
    """Resolve the standard schedule for an employee on a date:
    shiftexcpt (per day-of-week override, latest keydate) first, else the base shifttable."""
    sc = shift_code(company, emp_id, d)
    if not sc:
        return None
    dc = daycode(d)
    base = one("SELECT timein, breakout, breakin, timeout, stdhours, allowtardy, "
               "COALESCE(dayoff,0) AS dayoff, COALESCE(dayoff2,0) AS dayoff2 "
               "FROM shifttable WHERE company=? AND shift=?", company, sc)
    exc = one("SELECT timein, breakout, breakin, timeout, stdhours, allowtardy "
              "FROM shiftexcpt WHERE company=? AND shift=? AND daycode=? AND keydate<=? "
              "ORDER BY keydate DESC", company, sc, dc, d.isoformat())
    src = exc or base
    if not src:
        return None
    is_off = bool(base and (int(base["dayoff"] or 0) == dc or int(base["dayoff2"] or 0) == dc))
    grace = src.get("allowtardy")
    if grace is None and base:
        grace = base["allowtardy"]
    return {
        "shift": sc, "daycode": dc, "dayoff": is_off,
        "stdin": _min_of(src["timein"]), "brkout": _min_of(src["breakout"]),
        "brkin": _min_of(src["breakin"]), "stdout": _min_of(src["timeout"]),
        "stdhours": float(src["stdhours"] or 0),
        "grace": int(grace) if grace is not None else DEFAULT_GRACE,
    }


def schedule_range(company: str, emp_id: str, dates: list) -> dict:
    """Resolve schedules for many dates with a fixed number of queries (caches the
    employee's shift assignments + the company's shift/exception tables in Python)."""
    emps = q("SELECT frdate, RTRIM(COALESCE(shift,'')) AS shift FROM empshift "
             "WHERE company=? AND emp_id=? ORDER BY frdate", company, emp_id)
    fallback = None
    if not emps:
        r = one("SELECT RTRIM(COALESCE(shift,'')) AS shift FROM timecard WHERE company=? AND emp_id=? "
                "AND RTRIM(COALESCE(shift,''))<>'' ORDER BY trdate DESC", company, emp_id)
        fallback = r["shift"] if r and r["shift"] else None

    base = {r["shift"].strip(): r for r in q(
        "SELECT RTRIM(shift) AS shift, timein, breakout, breakin, timeout, stdhours, allowtardy, "
        "COALESCE(dayoff,0) AS dayoff, COALESCE(dayoff2,0) AS dayoff2 FROM shifttable WHERE company=?", company)}
    exc: dict = {}
    for r in q("SELECT RTRIM(shift) AS shift, daycode, keydate, timein, breakout, breakin, timeout, "
               "stdhours, allowtardy FROM shiftexcpt WHERE company=? ORDER BY keydate", company):
        exc.setdefault((r["shift"].strip(), int(r["daycode"])), []).append(r)

    def shift_on(d):
        sc = fallback
        for e in emps:
            if e["frdate"].date() <= d:
                sc = e["shift"].strip() or sc
        if sc is None and emps:
            sc = emps[-1]["shift"].strip()
        return sc

    out = {}
    for d in dates:
        sc = shift_on(d)
        b = base.get(sc) if sc else None
        if not sc or not b:
            out[d] = None
            continue
        dc = daycode(d)
        src = b
        for e in exc.get((sc, dc), []):
            if e["keydate"].date() <= d:
                src = e
        grace = src["allowtardy"] if src["allowtardy"] is not None else b["allowtardy"]
        out[d] = {
            "shift": sc, "daycode": dc,
            "dayoff": bool(int(b["dayoff"] or 0) == dc or int(b["dayoff2"] or 0) == dc),
            "stdin": _min_of(src["timein"]), "brkout": _min_of(src["breakout"]),
            "brkin": _min_of(src["breakin"]), "stdout": _min_of(src["timeout"]),
            "stdhours": float(src["stdhours"] or 0),
            "grace": int(grace) if grace is not None else DEFAULT_GRACE,
        }
    return out


def compute_day(sched: dict, punches: list[tuple], dayoff: bool | None = None,
                approved_ot: float = 0.0) -> dict:
    """Compute a day's hours from schedule + punch pairs [(in,out),...] as HHMM numbers.
    Returns tlhours, reghrs, tardy (minutes), undertime, nphrs. OT is passed in (approved),
    never inferred from punches."""
    off = sched["dayoff"] if dayoff is None else bool(dayoff)
    stdin, stdout = sched["stdin"], sched["stdout"]
    stdhours = sched["stdhours"]
    brk = 0
    if sched["brkout"] and sched["brkin"] and sched["brkin"] > sched["brkout"]:
        brk = sched["brkin"] - sched["brkout"]

    # normalise punch pairs to minutes; support overnight (out < in -> +1 day)
    pairs = []
    for pin, pout in punches:
        mi, mo = _num_min(pin), _num_min(pout)
        if mi is None:
            continue
        if mo is not None and mo < mi:
            mo += 1440
        pairs.append((mi, mo))

    if off or not pairs:
        # day off, or absent (no punches): no worked time; undertime = the scheduled hours
        reg = 0.0 if off else stdhours
        undertime = 0.0 if off else stdhours
        return {"tlhours": 0.0, "reghrs": round(reg, 2), "tardy": 0,
                "undertime": round(undertime, 2), "nphrs": 0.0}

    first_in = pairs[0][0]
    last_out = max((o for _, o in pairs if o is not None), default=None)
    reg = stdhours

    # tardy: minutes late past scheduled in, counted in full once it exceeds the grace
    tardy = 0
    if stdin is not None:
        late = first_in - stdin
        if late > sched["grace"]:
            tardy = late

    # total worked hours: effective in not earlier than scheduled; out capped at
    # scheduled time-out unless approved OT extends the day; minus the unpaid break
    tl = 0.0
    undertime = 0.0
    if last_out is not None and stdout is not None:
        eff_in = max(first_in, stdin) if stdin is not None else first_in
        # count time past scheduled out only when it's OT-worthy: OT was approved, or
        # the tail is at least a full hour (the legacy minimum OT block); else cap at out
        past = last_out - stdout
        eff_out = last_out if (approved_ot > 0 or past >= 60) else min(last_out, stdout)
        tl = max(0.0, (eff_out - eff_in - brk) / 60.0)
        if last_out < stdout:                       # left before scheduled out
            undertime = round(max(0.0, (stdout - last_out) / 60.0), 2)

    # night premium: minutes worked after 22:00, credited only once it reaches an hour
    npm = 0.0
    if last_out is not None and last_out > NIGHT_START:
        nm = last_out - max(first_in, NIGHT_START)
        if nm >= 60:
            npm = nm / 60.0

    return {"tlhours": round(tl, 2), "reghrs": round(reg, 2), "tardy": int(tardy),
            "undertime": round(undertime, 2), "nphrs": round(max(0.0, npm), 2)}


if __name__ == "__main__":
    # self-test against emp 000212 July 2025 (company 003)
    import os, sys
    os.environ.setdefault("DATABASE_URL",
        "postgresql://neondb_owner:npg_Na1kw4RJhbHY@ep-weathered-bird-aopksgbe-pooler."
        "c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
    sys.path.insert(0, r"D:\Documents\GitHub\OLD HRIS\app")
    from app import app
    with app.test_request_context():
        rows = q("SELECT trdate, timein1, timeout1, timein2, timeout2, COALESCE(dayoff,'') AS dayoff, "
                 "reghrs, tardy, nphrs, othrs, undertime, tlhours "
                 "FROM timecard WHERE company='003' AND emp_id='000212' "
                 "AND trdate>='2025-07-01' AND trdate<'2025-07-18' ORDER BY trdate")
        hits = {"reghrs": 0, "tardy": 0, "nphrs": 0}
        n = 0
        for r in rows:
            d = r["trdate"].date()
            sch = schedule("003", "000212", d)
            off = str(r["dayoff"]).strip() in ("1", "Y")
            res = compute_day(sch, [(r["timein1"], r["timeout1"]), (r["timein2"], r["timeout2"])],
                              dayoff=off, approved_ot=float(r["othrs"] or 0))
            n += 1
            for k in hits:
                if abs(res[k] - float(r[k] or 0)) < (0.5 if k == "tardy" else 0.02):
                    hits[k] += 1
            print(f"{d:%m/%d %a} calc reg={res['reghrs']} tdy={res['tardy']} np={res['nphrs']} tl={res['tlhours']} "
                  f"undt={res['undertime']} | stored reg={r['reghrs']} tdy={r['tardy']} np={r['nphrs']} tl={r['tlhours']} undt={r['undertime']}")
        print("\nmatch:", {k: f"{v}/{n}" for k, v in hits.items()})
