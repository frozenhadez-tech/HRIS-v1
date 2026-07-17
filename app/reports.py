"""Period/month/year report registry (attendance + payroll-processing screens).

Each entry: title, subtitle, level (month|period|year), sql (parameterized), cols.
Params passed by the /report route depend on level:
  month  -> (company, start_date, end_date)   # timecard filtered by trdate
  period -> (company, year, month, period)     # paytranh by pay period
  year   -> (company, year)                    # annual
cols: (field, label, align)  align: '' left, 'n' money, 'i' int, 'm' mono, 'c' center, 'd' date.
"""

TCNAME = ("LEFT JOIN personnel p ON p.company=t.company AND p.emp_id=t.emp_id")
EMPNAME = "RTRIM(COALESCE(p.lastname,''))||', '||RTRIM(COALESCE(p.firstname,'')) AS empname"

REPORTS = {
    # ── Attendance (month level, timecard by trdate) ───────────────────────
    "tc_view": {
        "title": "Time Card", "subtitle": "Daily time cards (timecard)", "level": "month",
        "sql": f"SELECT RTRIM(t.emp_id) AS emp_id, {EMPNAME}, t.trdate, RTRIM(COALESCE(t.shift,'')) AS shift, "
               "t.tlhours, t.reghrs, t.othrs, t.tardy, t.undertime FROM timecard t " + TCNAME +
               " WHERE t.company=? AND t.trdate >= ? AND t.trdate < ? ORDER BY t.emp_id, t.trdate LIMIT 1000",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("trdate", "Date", "d"),
                 ("shift", "Shift", "c"), ("tlhours", "Hours", "n"), ("reghrs", "Reg", "n"),
                 ("othrs", "OT", "n"), ("tardy", "Tardy", "n"), ("undertime", "Undertime", "n")],
    },
    "att_daily": {
        "title": "Daily Attendance Report", "subtitle": "Attendance by day (timecard)", "level": "month",
        "sql": f"SELECT t.trdate, RTRIM(t.emp_id) AS emp_id, {EMPNAME}, RTRIM(COALESCE(t.shift,'')) AS shift, "
               "t.tlhours, t.reghrs, CASE WHEN t.tlhours>0 THEN 'Present' ELSE 'Absent / Off' END AS status "
               "FROM timecard t " + TCNAME +
               " WHERE t.company=? AND t.trdate >= ? AND t.trdate < ? ORDER BY t.trdate, t.emp_id LIMIT 1000",
        "cols": [("trdate", "Date", "d"), ("emp_id", "Emp No", "m"), ("empname", "Name", ""),
                 ("shift", "Shift", "c"), ("tlhours", "Hours", "n"), ("reghrs", "Reg", "n"), ("status", "Status", "c")],
    },
    "att_ot": {
        "title": "Daily Overtime Report", "subtitle": "Days with overtime (timecard)", "level": "month",
        "sql": f"SELECT t.trdate, RTRIM(t.emp_id) AS emp_id, {EMPNAME}, t.othrs, t.xothrs, t.nphrs, "
               "RTRIM(COALESCE(t.approvotby,'')) AS approvedby FROM timecard t " + TCNAME +
               " WHERE t.company=? AND t.trdate >= ? AND t.trdate < ? AND t.othrs>0 "
               "ORDER BY t.trdate, t.emp_id LIMIT 1000",
        "cols": [("trdate", "Date", "d"), ("emp_id", "Emp No", "m"), ("empname", "Name", ""),
                 ("othrs", "OT Hrs", "n"), ("xothrs", "Ext OT", "n"), ("nphrs", "Night Prem", "n"),
                 ("approvedby", "Approved By", "m")],
    },
    "att_exception": {
        "title": "Attendance Exception Report", "subtitle": "Tardiness / undertime (timecard)", "level": "month",
        "sql": f"SELECT t.trdate, RTRIM(t.emp_id) AS emp_id, {EMPNAME}, t.tardy, t.undertime, t.tlhours "
               "FROM timecard t " + TCNAME +
               " WHERE t.company=? AND t.trdate >= ? AND t.trdate < ? AND (t.tardy>0 OR t.undertime>0) "
               "ORDER BY t.trdate, t.emp_id LIMIT 1000",
        "cols": [("trdate", "Date", "d"), ("emp_id", "Emp No", "m"), ("empname", "Name", ""),
                 ("tardy", "Tardy (hrs)", "n"), ("undertime", "Undertime", "n"), ("tlhours", "Worked", "n")],
    },
    # ── Payroll Processing (period level, paytranh) ────────────────────────
    "post_attend": {
        "title": "Posted Attendance Transactions", "subtitle": "Attendance-derived pay items for the period",
        "level": "period",
        "sql": "SELECT t.payitem, MAX(COALESCE(i.descrip,t.payitem)) AS descrip, COUNT(DISTINCT t.emp_id) AS emps, "
               "SUM(t.trhours) AS hrs, SUM(t.trdays) AS dys, SUM(t.tramount) AS amt "
               "FROM paytranh t JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem "
               "WHERE t.company=? AND t.payyear=? AND t.paymonth=? AND t.payperiod=? AND i.category IN ('0','1') "
               "GROUP BY t.payitem ORDER BY t.payitem",
        "cols": [("payitem", "Item", "m"), ("descrip", "Description", ""), ("emps", "Emps", "i"),
                 ("hrs", "Hours", "n"), ("dys", "Days", "n"), ("amt", "Amount (₱)", "n")],
    },
    "ot_entry": {
        "title": "Overtime Entry", "subtitle": "Overtime pay items for the period", "level": "period",
        "sql": "SELECT t.payitem, MAX(COALESCE(i.descrip,t.payitem)) AS descrip, COUNT(DISTINCT t.emp_id) AS emps, "
               "SUM(t.trhours) AS hrs, SUM(t.tramount) AS amt "
               "FROM paytranh t JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem "
               "WHERE t.company=? AND t.payyear=? AND t.paymonth=? AND t.payperiod=? AND i.category='7' "
               "GROUP BY t.payitem ORDER BY t.payitem",
        "cols": [("payitem", "Item", "m"), ("descrip", "Description", ""), ("emps", "Emps", "i"),
                 ("hrs", "Hours", "n"), ("amt", "Amount (₱)", "n")],
    },
    "addl_entry": {
        "title": "Additional Earnings / Deductions Entry", "subtitle": "Allowances, bonuses & adjustments for the period",
        "level": "period",
        "sql": "SELECT t.payitem, MAX(COALESCE(i.descrip,t.payitem)) AS descrip, MAX(i.category) AS cat, "
               "COUNT(DISTINCT t.emp_id) AS emps, SUM(t.tramount) AS amt "
               "FROM paytranh t JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem "
               "WHERE t.company=? AND t.payyear=? AND t.paymonth=? AND t.payperiod=? AND i.category IN ('3','5','6') "
               "GROUP BY t.payitem ORDER BY t.payitem",
        "cols": [("payitem", "Item", "m"), ("descrip", "Description", ""), ("cat", "Cat", "c"),
                 ("emps", "Emps", "i"), ("amt", "Amount (₱)", "n")],
    },
    "ded_register": {
        "title": "Deduction Register", "subtitle": "Statutory & other deductions for the period", "level": "period",
        "sql": "SELECT t.payitem, MAX(COALESCE(i.descrip,t.payitem)) AS descrip, COUNT(DISTINCT t.emp_id) AS emps, "
               "SUM(t.tramount) AS amt FROM paytranh t "
               "JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem "
               "WHERE t.company=? AND t.payyear=? AND t.paymonth=? AND t.payperiod=? AND i.category='4' "
               "GROUP BY t.payitem ORDER BY t.payitem",
        "cols": [("payitem", "Item", "m"), ("descrip", "Description", ""), ("emps", "Emps", "i"),
                 ("amt", "Amount (₱)", "n")],
    },
    "bank_summary": {
        "title": "Bank Summary", "subtitle": "Net pay by bank for the period", "level": "period",
        "sql": "SELECT COALESCE(NULLIF(RTRIM(pr.bankcode),''),'(cash)') AS bankcode, RTRIM(COALESCE(b.bankname,'')) AS bankname, "
               "COUNT(DISTINCT t.emp_id) AS emps, SUM(t.tramount) AS net "
               "FROM paytranh t JOIN payroll pr ON pr.company=t.company AND pr.emp_id=t.emp_id "
               "LEFT JOIN banks b ON b.company=pr.company AND b.code=pr.bankcode "
               "WHERE t.company=? AND t.payyear=? AND t.paymonth=? AND t.payperiod=? AND t.payitem='903' "
               "GROUP BY pr.bankcode, b.bankname ORDER BY pr.bankcode",
        "cols": [("bankcode", "Bank", "m"), ("bankname", "Bank Name", ""), ("emps", "Emps", "i"), ("net", "Net Pay (₱)", "n")],
    },
    "cash_summary": {
        "title": "Cash Summary", "subtitle": "Net pay for cash-paid employees", "level": "period",
        "sql": f"SELECT RTRIM(t.emp_id) AS emp_id, {EMPNAME}, SUM(t.tramount) AS net "
               "FROM paytranh t JOIN personnel p ON p.company=t.company AND p.emp_id=t.emp_id "
               "JOIN payroll pr ON pr.company=t.company AND pr.emp_id=t.emp_id "
               "WHERE t.company=? AND t.payyear=? AND t.paymonth=? AND t.payperiod=? AND t.payitem='903' "
               "AND (pr.paymode='C' OR COALESCE(RTRIM(pr.bankcode),'')='') "
               "GROUP BY t.emp_id, p.lastname, p.firstname ORDER BY p.lastname LIMIT 1000",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("net", "Net Pay (₱)", "n")],
    },
    # ── Transactions (year level) ──────────────────────────────────────────
    "ytd_adjust": {
        "title": "YTD Data Adjustments", "subtitle": "Year-to-date gross, taxable & tax per employee", "level": "year",
        "sql": f"SELECT RTRIM(t.emp_id) AS emp_id, {EMPNAME}, "
               "SUM(CASE WHEN t.payitem='900' THEN t.tramount ELSE 0 END) AS gross, "
               "SUM(CASE WHEN t.payitem='901' THEN t.tramount ELSE 0 END) AS taxable, "
               "SUM(CASE WHEN t.payitem='401' THEN t.tramount ELSE 0 END) AS tax "
               "FROM paytranh t JOIN personnel p ON p.company=t.company AND p.emp_id=t.emp_id "
               "WHERE t.company=? AND t.payyear=? GROUP BY t.emp_id, p.lastname, p.firstname "
               "ORDER BY p.lastname LIMIT 1000",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("gross", "YTD Gross", "n"),
                 ("taxable", "YTD Taxable", "n"), ("tax", "YTD Tax", "n")],
    },
    "prev_emp_ytd": {
        "title": "Previous Employment YTD Gross and Tax", "subtitle": "Employees hired during the year (may have prior-employer YTD)",
        "level": "year",
        "sql": "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "p.datehired, RTRIM(COALESCE(p.tin,'')) AS tin, RTRIM(p.empsts) AS empsts "
               "FROM personnel p WHERE p.company=? AND EXTRACT(YEAR FROM p.datehired)=? "
               "ORDER BY p.datehired LIMIT 1000",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("datehired", "Date Hired", "d"),
                 ("tin", "TIN", "m"), ("empsts", "Status", "c")],
    },
}
