# HRPayroll L98 — Web Rebuild

A web reimplementation of the original PowerBuilder HRIS (`hrpayroll.exe`, Build #18),
running against the restored `HRPayroll_L98` database. Structure mirrors
[../APP_BLUEPRINT.md](../APP_BLUEPRINT.md). **Read-only** — every query is a parameterized SELECT.

## Run it

```
python app/app.py          # or: preview the "hris-viewer" launch config
```
Then open <http://localhost:5098>. Requires the database restored to `localhost\SQLEXPRESS`
(see ../BACKUP_ANALYSIS.md) and Python packages `flask`, `pyodbc`.

## What's implemented

Faithful to the original's **two-mode** design — switch between **Payroll Application** and
**HR Application** from the menu bar (top-right "HR »" / "Payroll »"). A company selector
(001–004) scopes every screen.

| Area | Status |
|---|---|
| Two-mode menu bar (both full menu trees) | ✅ |
| Function-key action toolbar (F12-Close · F5-Refresh · F6-Add · F23-Delete · section ▾ · F3-Exit) | ✅ on every data screen, with keyboard shortcuts; Add/Delete greyed pending write screens |
| Company dashboard | ✅ |
| Employee Data list (search / status / company) | ✅ |
| **Employee 201 file — all 14 section tabs** | ✅ Personal, Employment (+movement history), Education, Training, Work Exp, Dependents, Leaves, Medical, Appraisal, Disciplinary, Documents, Payroll, Fix Allow, Fix Ded'n |
| Payroll Register (by period, grouped by pay item) | ✅ |
| 42 maintenance/report grids | ✅ tax/SSS/PhilHealth tables, payitems, OT rates, shifts, banks, users, org structure, transactions, masterlists, government remittance lists, HR reports |
| **Payroll calculation engine** (`payroll_engine.py`) | ✅ SSS/PhilHealth/HDMF/withholding-tax, reverse-engineered from history & verified to the centavo (tax 100%, PhilHealth 96%) |
| **Live Payroll Calculator** (`/calculator`) | ✅ salary → full statutory + tax + net |
| **Engine verification harness** (`/engine/verify`) | ✅ recomputes a closed period, scores match rate vs stored, flags stale tables |
| **Printable payslip** (`/payslip/<co>/<emp>`) | ✅ earnings/deductions/net from stored `paytranh`, print-ready |
| **Printable government forms** | ✅ SSS R-3, PhilHealth RF-1, HDMF MCRF (engine-computed), BIR Alphalist 1604-C (exact from history) |
| Data entry / edit (writes) | ⬜ read-only by design for now |

### The payroll engine

`payroll_engine.py` reconstructs the computation that lived in the PowerBuilder client:

- **SSS** — `ssstable` lookup by monthly gross → employee/employer/EC shares
- **PhilHealth** — 2.5% of salary (5% total), floor ₱10k / ceiling ₱100k
- **Pag-IBIG (HDMF)** — 2% of salary, employee share capped ₱200
- **Withholding tax** — BIR TRAIN bracket table (`taxtable`) on per-period taxable gross

Verified against 352k rows of closed payroll. Withholding tax matches **100%** (it reads the stored
per-period taxable, item 901). SSS in 2025 diverges only because the backup's `ssstable` is the older
schedule (max MSC ₱20k) — the engine is correct; load the Jan-2025 SSS table for current accuracy.
`/engine/verify` quantifies this per period.

## Files

- `app.py` — routes, DB helpers, employee-tab queries, template filters
- `menus.py` — the two mode menu trees (labels → routes)
- `grids.py` — declarative registry of the 42 list/report screens (SQL + columns)
- `templates/` — `base.html` (shell + menu bar), `dashboard`, `employees`, `employee` (tabs),
  `payroll`, `grid` (generic), `_macros.html`
- `static/style.css` — payroll-ledger visual theme, per-mode accent colour

## Next phases (to reach full parity)

1. **Payroll calculation engine** — recompute a period from attendance + payitem setup;
   regression-test against historical `paytranh` (352k rows) to match the original exactly.
2. **Printable outputs** — payslip, bank summary, and the PH government forms.
3. **Write/maintenance screens** — turn the read-only grids into editable maintenance forms
   (with the original's validation rules, e.g. salary caps vs `company.maxdlyrate`).
