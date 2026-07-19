# Payroll Calculation — verified against the original app

The original computation lived in the PowerBuilder client (`pycalc*`, `pyams*`). These formulas
were reverse-engineered from the calc libraries **and** validated to the centavo against the
closed payroll history (`paytranh`). The rebuilt engine (`app/payroll_engine.py`) implements them.

## Rates
- **Daily rate** = `salary` (daily-paid, `paytype='D'`) or `salary ÷ baseday` (monthly-paid, `'M'`).
  `baseday` and `hours/day` come from the `company` table **per company** —
  001/002: 26.083 days, 003/004: 26.1666667 days; all at 8 hrs/day.
- **Hourly rate** = daily rate ÷ hours-per-day.
- `otrates` is the original app's per-paygroup multiplier lookup (`otcode` 1=daily, 2=monthly, …)
  with the night-premium percent per OT type in `nprate` (regular 10%, spl-holiday 13%,
  legal-holiday 20%, …). The live multipliers the history follows are `payitem.mult/multm`;
  audit note: `otrates` co 001 otcode 1 item 703 has `nprate=0.690` — a transposition of the
  0.169 every sibling row carries (editable in-app if it ever matters).

## Pay lines (hours-based, `payitem.unmsr='H'`)
```
amount = hours × hourly_rate × multiplier
multiplier = payitem.multm   for monthly-paid   (premium portion only)
           = payitem.mult    for daily-paid
```
A monthly-paid worker already earns the holiday/base in their salary, so only the premium
(`multm`) applies; a daily-paid worker earns the full `mult`. Confirmed by pay item **704**
(Special-Holiday OT): `mult=1.30`, `multm=0.30` — a monthly employee's line used 0.30.

Covers: Regular/Rest-day/Holiday OT (701–711), Night Premium (715), Late/Tardy (103),
Undertime (102), Leave-without-pay (101/106/204).

## Basic pay & attendance
- Monthly-paid **Basic Pay** (item 001) = `salary ÷ 2` per semi-monthly period (full);
  tardiness / undertime / absences are **separate negative lines**, not prorated into basic.
- Daily-paid **Basic Pay** (item 001) = `paid hours × (daily rate ÷ 8)` — verified **100%**
  across companies 002/003/004 (2025-08). The *paid hours* come from the attendance posting
  over the period's **`payperiod` window** (`fromdate`–`todate`, which lags the calendar —
  e.g. co 004's August P1 covers Jul 26–Aug 10 — capped at `maxhr`). The legacy posting nets
  per-day adjustments (tardy minutes, holiday hours split to item 002) the old client computed;
  the draft calculator approximates paid hours as Σ per-day `min(tlhours, stdhours)` within
  the window, so drafts for legacy periods can differ by those nets while the rate law is exact.
- **Night premium** (item 715, `unmsr='A'`; plus `NIA` allowance) —
  `Σ per-day night hours × hourly × otrates.nprate for that day's type`:
  10% regular/rest-day nights, 13% special holiday (15% on a rest day), 20% legal holiday
  (26% on a rest day); day type from the `holidays` table (`hflag` L/S, company days as S)
  + the time card's day-off flag. **Implemented in the draft calculator** from per-day
  `timecard.nphrs` over the pay-period window — verified **94.2%** against stored 2025
  lines (100% in co 001/002/004; the co 003 misses are the same salary-drift cases as OT).

## Statutory & tax (employee share)
- **SSS** — `ssstable` lookup by monthly gross → `sssee`.
- **PhilHealth** — 2.5% of salary (5% total), floor ₱10k / ceiling ₱100k.
- **Pag-IBIG (HDMF)** — 2% of salary, capped ₱200 EE.
- **Withholding tax** — BIR TRAIN table (`taxtable`) on per-period taxable gross.

## Verification (match vs. stored history)
Recomputing the closed periods and comparing to what the original app stored:

| Component | Match |
|---|---|
| Withholding tax | 100% |
| OT / hours-based lines (after the `multm` rule) | **100%** (2025-08 P1: 166/166; 2025-07 P2: 138/138) |
| PhilHealth | ~96% |
| SSS | matches when the loaded `ssstable` is contemporaneous; 2025 rows need the current SSS schedule |

The `/engine/verify` screen runs this live per period, including the **OT / hours lines** scorecard.
Residual sub-100% cases are salary drift (an employee's rate changed after the historical period)
or the known stale-`ssstable` issue — not formula differences.
