# Old HRIS Backup Analysis — `L98PAYROLL_08282025`

**Analyzed:** 2026-07-15 · **Method:** raw scan of the backup file, then full restore.

> **Status update (2026-07-15):** SQL Server 2022 Express is now installed; the database is **restored and ONLINE** at `localhost\SQLEXPRESS`, files at `D:\HRPayroll_L98\Data\`. Full schema docs: [SCHEMA.md](SCHEMA.md). A read-only web viewer runs at `http://localhost:5098` (see `app/`, start with the `hris-viewer` launch config: `python app/app.py`). Key data: 497 employees (188 current), payroll history 2017–2025 (352,719 lines), 387,859 timecard rows.

## What the file is

| Property | Value |
|---|---|
| Format | Microsoft SQL Server full database backup (uncompressed MTF/`.bak`) |
| Database | `HRPayroll_L98` |
| Backup label | "HRPayroll_L98 – Full Database Backup", taken as user `sa` |
| Source server | `MYSQLSERVER\SQLEXPRESS` — **SQL Server 2012 Express** (v11.0) |
| Original files | `D:\HRPayroll_L98\Data\HRPayroll_L98_data.mdf` / `_log.ldf` |
| Size | 479 MB (≈457 MB data) |
| Backup date | 2025-08-28 |

## What the old system was

- **Client:** a **PowerBuilder** desktop application (2-tier client/server). Evidence: PowerBuilder catalog tables `pbcattbl`, `pbcatcol`, `pbcatfmt`, `pbcatvld`, `pbcatedt` exist in the database.
- **Server:** SQL Server 2012 Express holding the data plus a thin layer of logic: 18 views and 6 triggers (validation + audit). **No stored procedures found** — payroll computation, screens, and reports lived inside the PowerBuilder executable, which is *not* in this backup.
- **Domain:** Philippine HR & payroll — SSS, PhilHealth (`phtable`, `phealthno`), Pag-IBIG/HDMF (`hdmfno`, `hdmfmbr`), BIR withholding tax (`taxtable`, `exemptable`) and BIR **Alphalist** (`alphalist`), TIN, barangay address fields.

## Recovered schema inventory (~80 user tables)

**Employee 201 file & HR:** `personnel` (100+ columns incl. photo `picturebmp`), `dependents`, `edutrain`, `workexp`, `empnotes`, `discipline`, `careerplan`, `appraisal`, `training`, `applicatn`, `applicant_ext`, `applicant_evaluation`

**Organization:** `company`, `division`, `department`, `section`, `jobcode`, `jobcat`, `jobgrade`, `policy`

**Movement history:** `jobchange`, `deptchange`, `empstschg`, `ratechange`, `companychg`, `chglog` (audit)

**Timekeeping:** `timecard`, `timecardtr`, `timeinout`, `dailyatt`, `dailyattrw`, `dailyattsm`, `payattend`, `shifttable`, `empshift`, `shiftexcpt`, `holidays`, `holidayf`, `holidaytbl`, `leaves`, `stdleaves`, `ctoalloc`, `ctoalloch`, `pa_exception`, `padatexc`, `payexcept`, `perfectat1`

**Payroll engine:** `payroll`, `payrollemp`, `paydates`, `payperiod`, `paygroupsc`, `payitem`, `paytran`, `paytranc`, `paytrand`, `paytranh` (multi-year history), `paytrancytd`, `fixallow`, `fixded`, `empfinalpy`

**Statutory (PH):** `ssstable`, `phtable`, `taxtable`, `exemptable`, `alphalist`

**Finance/banking:** `acctable` (GL mapping), `banks`, `ddsaut` (bank/direct-deposit), GL code fields

**App security/config:** `users`, `compusers`, `tablecode1` (lookup codes), `pbcat*` (PowerBuilder catalog)

**Site-specific:** `ntmc_employees`, `bntmc_employees_copy`, `lcargolist`, `multi_hiredresgnd_dt`

**Views (18):** `personnel_active`, `personnel_payroll`, `personnel_payroll2`, `personnel_section`, `personnel_fte_section`, `personnel_divdeptsect`, `personnel_vw1/vw3`, `paytranh_v1/v2/v3`, `paytranh_payperiod_z`, `empshift_v1`, `ratechange_v1`, `jobcode_jobgrade`, `tablecode1_est/lvl/zp1`

**Triggers (6):** `tgr_personnel_insert/update`, `tgr_payroll_update` (salary-cap validation vs `company.maxdlyrate`/`maxmorate` + audit), `tgr_ratechange_insert/update/delete`

## Feasibility verdict: YES — a replacement app is very feasible

The backup contains the two hardest things to recreate: the **complete data model** and **all historical data** (employee masters, multi-year payroll history in `paytranh`, timecards, statutory tables). What it does *not* contain is the PowerBuilder client itself — screens, reports, and the payroll calculation code must be rebuilt and validated.

### Recommended path

1. **Restore the backup** into free SQL Server Express 2019/2022 (restores 2012 backups directly). ~30 min. This unlocks the exact schema (columns, types, keys) and real data.
2. **Generate full schema documentation** from the restored DB (tables/columns/FKs + row counts).
3. **Rebuild as a web app**, keeping the database schema initially (fastest route to "runs the same"):
   - Backend API + SQL Server (or later PostgreSQL migration)
   - Phase 1: read-only — employee 201 file, payroll history, org setup
   - Phase 2: timekeeping entry & maintenance screens
   - Phase 3: payroll computation engine — **regression-test against historical `paytranh` results**, a huge advantage: recompute past periods and compare to the old app's actual output
   - Phase 4: outputs — payslips, government remittance reports (SSS/PhilHealth/Pag-IBIG), BIR Alphalist, GL export
4. **Update statutory rules to current law** — the tables hold rates as of Aug 2025; 2026 SSS/PhilHealth/tax rates must be loaded.

### Risks / unknowns

- Business rules embedded in the PowerBuilder client aren't in the backup — need payroll-staff walkthroughs and parallel runs to capture edge cases (rounding, proration, OT rules per `jobcode.allowot`/`otcode`).
- App-level user permissions are in `users`/`compusers` but the enforcement logic was client-side.
- Employee photos stored as BMPs (`picturebmp`, `emppicext`) — migrate carefully.
