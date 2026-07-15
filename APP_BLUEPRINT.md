# HRPayroll L98 — Original Application Blueprint

Captured 2026-07-15 by running the **original** `hrpayroll.exe` (Build #18) live against the
restored `HRPayroll_L98` database. This is the authoritative spec for rebuilding the system
"exactly like the old app": every menu, screen section, and workflow below was read from the
running program, cross-referenced to the database schema in [SCHEMA.md](SCHEMA.md).

---

## 1. What the original app is

| | |
|---|---|
| Technology | PowerBuilder 9 desktop app (32-bit), MDI (multiple-document) frame |
| Vendor string | "HR-Payroll System by DGSoft" / "MS HR-Payroll" |
| Database | SQL Server, ODBC connection (DSN `HRPayroll_L98`) |
| Build | #18 |
| Libraries | ~50 `.pbd` runtime libraries (menus `pymenu`, `hrmenu`; logic `pycalc*`, `pyams*`, `pytrn*`; reports `pyrep*`, `hrrep*`) |
| Companies | Multi-company: 001 L98 Brokerage & Logistics, 002 LCARGO, 003 LDL 17 Holdings, 004 FASTGEAR Transport |

### Two applications in one
The program runs in **two switchable modes**, selected from the toolbar/menus:

- **Payroll Application (PY)** — payroll master data, attendance, payroll processing, government reports
- **HR Application (HR)** — employee 201 files, org structure, movements, leaves, medical, HR reports

The title bar reflects the active mode ("… - Payroll Application" / "… - HR Application"). Each
user's default landing program is stored per-user (e.g. `PY/Attendance/Time Card Update`).

### Login
Two layers, in order:
1. **Database connection** — ODBC to SQL Server (see §6). Invisible to end users.
2. **Application login** — the app's own screen: Company + User ID + Password (case-sensitive),
   validated against the `users` table. Example user `RARA` = "REY ARNEL GUINTO".
   Passwords are stored obfuscated in `users.password`; user rights are row-level
   (`maxearn`, `maxdedn`, `currentpgm`, `disabled`).

---

## 2. Payroll Application — full menu tree

**File**
- Print Setup · Exit (plus standard Save-as / Print / Print Preview on data windows)

**Database** *(payroll master tables)*
- Table Codes · Tax Table · SSS Table · PhilHealth Table
- Company · Payroll Items · Overtime Rates · Shift Table
- Employee Data

**Transactions**
- Rate Change · Department Change · Job Position Change
- Loans
- YTD Data Adjustments · Previous Employment YTD Gross and Tax

**Attendance**
- Holiday Table · Holiday Table By Branch · Employee Shifts
- Import Time In/Time Out Data · Import Attendance-Biometrics · Time Card Update
- Time Card Inquiry · Daily Attendance Report · Daily Tardiness Report · Employee Tardiness Report
  · Daily Overtime Report · Daily AWOL Report · Attendance Exception Report
  · Attendance Exception Report-Late/Undertime/Absent
- Hours Worked Transfer

**Payroll Processing** *(the core workflow — see §5)*
- Define Pay Period · Post Attendance Transactions
- Hold Pay · Posted Attendance · Overtime Entry · Leaves/Absences Entry
  · Additional Earnings/Deductions Entry
- **Payroll Calculation**
- Payroll Register · Deduction Register · Deduction Register-By Type · Unapplied Deductions
  · Payslip · E-Mail Payslip · Bank Summary · Cash Summary
- Government remittances submenu: SSS Contribution · PhilHealth Contribution · HDMF Contribution
  · Withholding Tax · Loans Register
- **Payroll Close**

**Inquiries/Reports**
- Employee Data · Employee By Department · Rate Change
- Masterlist By Department · Masterlist by Pay Group · Masterlist by Shift
- Monthly Summary of Compensation and Withholding Tax
- SSS: Employee Pre-Validation · Monthly Remittance · Monthly Loans Remittance
  · Monthly Delinquent Loans Remittance · Contribution Summary By Employee
- HDMF: Monthly Remittance · Monthly Loans Remittance · Modified Pag-ibig II Monthly Contributions
- PhilHealth: Monthly Remittance · Quarterly Contribution
- 13th Month Pay Accrual Report · Convertible Leaves · Deminimis Allowance Report
- Payroll Summary · Payroll Report - Monthly · Alphalist of Employees · Certificate of Tax Withheld
  · Payslip History · Loans History

**HR** → switches to HR Application (§3)

**Special Processing** · **Tools** *(Change Password, Select Company, Calculator, Toolbar Text)* · **Help**

---

## 3. HR Application — full menu tree

**Database**
- Users · Table Codes · Banks
- Company · Position Titles · Divisions · Departments · Sections · Div/Dept/Section Tree
  · Shift Table · Company Policy
- Employee Data · Employee Address
- Export Employee Data

**Transactions**
- Company Change · Department Change · Job Position Change
- Rate Change
- Print Personnel Action Notice · Date Hired/Date Resigned
- Leave Entitlement Update · Leave Credit Entry
- Leaves and Absences · Leaves and Absences Prooflist

**Inquiries/Reports**
- Employee Data Inquiry · Employee By Department · Employee Profile
- Hired This Period · Due for Regularization · Regularized This Period · Resigned This Period
  · Due for Annual Physical Exam · Birthday Celebrants
- Accountability Report
- Masterlist by Department · Masterlist by Position Title
- Headcount By Dept/Section/Employee Status · Demographic Profile · Work Experiences
  · Educational Attainment
- Years of Service Report · Leaves Balances
- Employees with Applied TIN · SSS R1-A Report · SSS R-3 Report · PhilHealth Er2

**Inquiries/Reports-2** *(training & medical)*
- Employee List By Length of Service · Employee List For SEC · Employee Training Report
- Employee List By Blood Type · Annual PE Result · Medical Follow-up · Medical History
  · Monthly Medical Report · Prevalent Illness/Diseases

**Payroll** → switches back to Payroll Application · **Tools** · **Help**

---

## 4. Employee 201-file screen (the "tabs")

`Database ▸ Employee Data` opens an **Employees** list (columns: No., Emp. No., Employee Name,
Status; with "Position to" quick-search and Include-Resigned / Show-Pictures toggles).
Selecting an employee exposes their record **sections** as a context toolbar — these are the tabs
to replicate, each backed by its own table:

| Section | Backing table(s) |
|---|---|
| Personal Info | `personnel` |
| Employment | `personnel` (empsts, datehired, datereg, jobcode, division/dept/section) |
| Education | `edutrain` |
| Training | `training` / `edutrain` |
| Work Exp | `workexp` |
| Dependents | `dependents` |
| Accountabilities | (accountability table) |
| Leaves | `leaves`, `leavetran`, `stdleaves` |
| Medical Hist | `medical` |
| Appraisal | `appraisal` |
| Disciplinary | `discipline` |
| Doc | `edoc` |
| Payroll | `payroll` (salary, paytype, paygroup, bank) |
| Fix Allow | `fixallow` |
| Fix Ded'n | `fixded` |

### Personal Data Entry — field layout
`Emp. No.` · `Status` · `Last name` · `Nationality` · `First name` · `Sex` · `Middle name` ·
`Status`(civil) · `Birth date` + `Age` + `Blood type` · `Birth place` · `Religion` · `Address` ·
`Zip code` · `Barangay` · `Tel. no.` · `City/Town` · `Cell. no.` · `Province` · photo box ·
**Contact person in case of emergency**: `Name` · `Relationship` · `Address` · `Tel. No`.
→ every field maps 1:1 to a `personnel` column (see [SCHEMA.md](SCHEMA.md)).

---

## 5. Core payroll workflow (per pay period)

1. **Define Pay Period** — open the period (year/month/period 1, 2, or X special) → `payperiod`, `paydates`
2. **Import attendance** — Import Time In/Out or Biometrics → `timeinout`, then **Time Card Update** → `timecard`, `timecardtr`
3. **Post Attendance Transactions** — posts hours/tardiness/OT/absences into the payroll working set
4. **Entry screens** — Overtime Entry, Leaves/Absences Entry, Additional Earnings/Deductions Entry, Hold Pay
5. **Payroll Calculation** — computes gross, statutory deductions (SSS/PhilHealth/HDMF), withholding tax, loans, net → `paytran*`
6. **Registers & outputs** — Payroll Register, Deduction Register, Payslip / E-Mail Payslip, Bank Summary, Cash Summary; government remittance reports
7. **Payroll Close** — finalizes the period; history lands in `paytranh` (352,719 rows, 2017–2025)

The salary-cap validation trigger (`tgr_payroll_update`, checking `company.maxdlyrate` / `maxmorate`)
and the audit triggers on `personnel` and `ratechange` fire during these steps.

---

## 6. How it was made to run locally (2026-07-15)

The original binaries were pointed at the restored database with **no code changes**:

1. Restored `HRPayroll_L98` to `localhost\SQLEXPRESS` (SQL Server 2022 Express).
2. Repointed the app's existing ODBC User DSN `HRPayroll_L98` from the old server name
   `MYSQLSERVER\SQLEXPRESS` to `localhost\SQLEXPRESS`.
3. Because the fresh instance is Windows-auth-only (the old SQL login no longer exists), switched
   the connection to **Windows authentication**: edited `[DataBase]` in `HRPayroll.ini` to
   `DBParm=ConnectString='DSN=HRPayroll_L98;Trusted_Connection=Yes'` and cleared the stored
   SQL `LogID`/`LogPassword`. (Original INI saved as `HRPayroll.ini.bak_claude`.)
4. Launched `hrpayroll.exe`; it connected and reached its own login screen. The app then
   authenticated the pre-filled `RARA` user against the `users` table.

> To run SQL-authentication instead (closer to the original deployment), enable mixed-mode auth on
> the instance and recreate the app's SQL login; then restore the original `[DataBase]` INI section.

---

## 7. Rebuild guidance

- **Fastest faithful replica:** keep the SQL Server schema as-is; rebuild the two-mode UI (Payroll + HR)
  as a web app following the menu trees in §2–§3 and the 201 sections in §4.
- **Payroll engine:** re-implement step 5. The old calculation logic lived in the PowerBuilder
  libraries (`pycalc01/02/03`, `pyams*`); it is **not** in the database. Rebuild from the field
  semantics + `payitem` setup, and **regression-test against `paytranh`** by recomputing closed periods.
- **Reports:** the government forms (SSS/PhilHealth/HDMF remittances, BIR Alphalist & 2316,
  Modified Pag-IBIG II) are the highest-value outputs; their layouts are recoverable from the
  original `.psr`/report DataWindows and the report menus in §2/§3.
- **Statutory tables** (`ssstable`, `phtable`, `taxtable`, `exemptable`) hold Aug-2025 rates —
  refresh to current law before any live use.
