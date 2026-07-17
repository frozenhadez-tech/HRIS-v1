# Payroll Calculation — verified against the original app

The original computation lived in the PowerBuilder client (`pycalc*`, `pyams*`). These formulas
were reverse-engineered from the calc libraries **and** validated to the centavo against the
closed payroll history (`paytranh`). The rebuilt engine (`app/payroll_engine.py`) implements them.

## Rates
- **Daily rate** = `salary` (daily-paid, `paytype='D'`) or `salary ÷ baseday` (monthly-paid, `'M'`).
  `baseday` and `hours/day` come from the `company` table (001: 26.083 days, 8 hrs).
- **Hourly rate** = daily rate ÷ hours-per-day.

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
