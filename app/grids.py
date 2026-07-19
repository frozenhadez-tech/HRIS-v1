"""Declarative data-grid registry for maintenance & report screens.

Each entry: title, optional subtitle, sql (parameterized), cols [(field,label,align)],
and company=True if the sql takes a single company parameter (?).
align: '' left, 'n' numeric/right, 'm' mono, 'c' center.
"""

# name-join fragment for employee-keyed tables
NAME = ("LEFT JOIN personnel p ON p.company=t.company AND p.emp_id=t.emp_id")
EMPNAME = "RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname"

GRIDS = {
    # ── Payroll database maintenance ───────────────────────────────────────
    "tablecodes": {
        "title": "Table Codes", "subtitle": "Lookup/reference codes (tablecode1)",
        "sql": "SELECT RTRIM(tblcode) AS tblcode, RTRIM(fldcode) AS fldcode, RTRIM(COALESCE(descrip,'')) AS descrip, "
               "RTRIM(COALESCE(vardata,'')) AS vardata, RTRIM(COALESCE(applicat,'')) AS applicat "
               "FROM tablecode1 ORDER BY tblcode, fldcode",
        "cols": [("tblcode", "Table", "m"), ("fldcode", "Code", "m"), ("descrip", "Description", ""),
                 ("vardata", "Value", ""), ("applicat", "App", "c")],
    },
    "taxtable": {
        "title": "Withholding Tax Table", "subtitle": "BIR compensation tax brackets (taxtable)",
        "sql": "SELECT RTRIM(xtype) AS xtype, RTRIM(COALESCE(xunit,'')) AS xunit, RTRIM(COALESCE(xdesc,'')) AS xdesc, "
               "seqno, exemption, range01, range02, range03, range04, range05 "
               "FROM taxtable ORDER BY xtype, seqno",
        "cols": [("xtype", "Type", "m"), ("xunit", "Unit", "m"), ("xdesc", "Description", ""),
                 ("exemption", "Exemption", "n"), ("range01", "Bracket", "n"), ("range02", "Base Tax", "n"),
                 ("range03", "% Over", "n"), ("range04", "R4", "n"), ("range05", "R5", "n")],
    },
    "ssstable": {
        "title": "SSS Contribution Table", "subtitle": "ssstable",
        "sql": "SELECT frgross, togross, credit, ssser, mcrer, eccer, sssee, mcree FROM ssstable ORDER BY frgross",
        "cols": [("frgross", "From Gross", "n"), ("togross", "To Gross", "n"), ("credit", "MSC", "n"),
                 ("ssser", "SSS ER", "n"), ("mcrer", "MPF ER", "n"), ("eccer", "EC ER", "n"),
                 ("sssee", "SSS EE", "n"), ("mcree", "MPF EE", "n")],
    },
    "phtable": {
        "title": "PhilHealth Table", "subtitle": "phtable",
        "sql": "SELECT bracket, frgross, togross, salarybase, mcrer, mcree FROM phtable ORDER BY frgross",
        "cols": [("bracket", "Bracket", "i"), ("frgross", "From", "n"), ("togross", "To", "n"),
                 ("salarybase", "Salary Base", "n"), ("mcrer", "ER Share", "n"), ("mcree", "EE Share", "n")],
    },
    "company": {
        "title": "Company Parameters", "subtitle": "company",
        "sql": "SELECT RTRIM(company) AS company, RTRIM(companynam) AS companynam, RTRIM(COALESCE(address,'')) AS address, "
               "RTRIM(COALESCE(tin,'')) AS tin, RTRIM(COALESCE(sssno,'')) AS sssno, RTRIM(COALESCE(hdmfno,'')) AS hdmfno, "
               "RTRIM(COALESCE(phidno,'')) AS phidno, baseday, hourspday, maxdlyrate, maxmorate FROM company ORDER BY company",
        "cols": [("company", "Code", "m"), ("companynam", "Company", ""), ("tin", "TIN", "m"),
                 ("sssno", "SSS No", "m"), ("hdmfno", "HDMF No", "m"), ("phidno", "PhilHealth", "m"),
                 ("baseday", "Base Days", "n"), ("hourspday", "Hrs/Day", "n"),
                 ("maxdlyrate", "Max Daily", "n"), ("maxmorate", "Max Monthly", "n")],
    },
    "payitem": {
        "title": "Payroll Items", "subtitle": "Earnings & deductions setup (payitem)", "company": True,
        "sql": "SELECT RTRIM(payitem) AS payitem, RTRIM(COALESCE(descrip,'')) AS descrip, category, "
               "RTRIM(COALESCE(b4tax,'')) AS b4tax, priority, RTRIM(COALESCE(freq,'')) AS freq, "
               "RTRIM(COALESCE(taxscheme,'')) AS taxscheme FROM payitem WHERE company=? ORDER BY payitem",
        "cols": [("payitem", "Item", "m"), ("descrip", "Description", ""), ("category", "Cat", "c"),
                 ("b4tax", "B4Tax", "c"), ("priority", "Prio", "i"), ("freq", "Freq", "c"),
                 ("taxscheme", "TaxSch", "c")],
    },
    "otrates": {
        "title": "Overtime Rates", "subtitle": "otrates", "company": True,
        "sql": "SELECT RTRIM(o.otcode) AS otcode, RTRIM(o.payitem) AS payitem, RTRIM(COALESCE(i.descrip,'')) AS descrip, "
               "o.otrate, o.nprate FROM otrates o LEFT JOIN payitem i ON i.company=o.company AND i.payitem=o.payitem "
               "WHERE o.company=? ORDER BY o.otcode, o.payitem",
        "cols": [("otcode", "OT Code", "m"), ("payitem", "Item", "m"), ("descrip", "Description", ""),
                 ("otrate", "OT Rate", "n"), ("nprate", "Nite Prem", "n")],
    },
    "shifttable": {
        "title": "Shift Table", "subtitle": "shifttable", "company": True,
        "sql": "SELECT RTRIM(shift) AS shift, RTRIM(COALESCE(shiftdesc,'')) AS shiftdesc, "
               "to_char(timein,'HH24:MI') AS timein, to_char(timeout,'HH24:MI') AS timeout, "
               "stdhours, stdot, RTRIM(COALESCE(flextime,'')) AS flextime FROM shifttable WHERE company=? ORDER BY shift",
        "cols": [("shift", "Shift", "m"), ("shiftdesc", "Description", ""), ("timein", "Time In", "m"),
                 ("timeout", "Time Out", "m"), ("stdhours", "Std Hrs", "n"), ("stdot", "Std OT", "n"),
                 ("flextime", "Flex", "c")],
    },
    "banks": {
        "title": "Banks", "subtitle": "banks", "company": True,
        "sql": "SELECT RTRIM(code) AS code, RTRIM(COALESCE(bankname,'')) AS bankname, "
               "RTRIM(COALESCE(branchname,'')) AS branchname, RTRIM(COALESCE(acctformat,'')) AS acctformat "
               "FROM banks WHERE company=? ORDER BY code",
        "cols": [("code", "Code", "m"), ("bankname", "Bank", ""), ("branchname", "Branch", ""),
                 ("acctformat", "Acct Format", "m")],
    },
    "users": {
        "title": "Users", "subtitle": "Application accounts — create, edit, reset passwords, remove",
        "sql": "SELECT RTRIM(u.user_id) AS user_id, RTRIM(COALESCE(u.user_name,'')) AS user_name, RTRIM(COALESCE(u.class,'')) AS class, "
               "CASE WHEN u.disabled IS NULL THEN 'Active' ELSE 'Disabled' END AS state, "
               "u.lastsignon, RTRIM(COALESCE(u.emp_id,'')) AS emp_id "
               "FROM users u ORDER BY u.user_id",
        "cols": [("user_id", "User ID", "m"), ("user_name", "Name", ""), ("class", "Class", "c"),
                 ("state", "State", "c"), ("lastsignon", "Last Sign-on", "d"),
                 ("emp_id", "Emp No", "m")],
    },
    # ── Org structure ──────────────────────────────────────────────────────
    "jobcode": {
        "title": "Position Titles", "subtitle": "jobcode", "company": True,
        "sql": "SELECT RTRIM(code) AS code, RTRIM(COALESCE(descrip,'')) AS descrip, RTRIM(COALESCE(category,'')) AS category, "
               "RTRIM(COALESCE(jobgrade,'')) AS jobgrade, min_salary, max_salary FROM jobcode WHERE company=? ORDER BY descrip",
        "cols": [("code", "Code", "m"), ("descrip", "Position Title", ""), ("category", "Cat", "c"),
                 ("jobgrade", "Grade", "c"), ("min_salary", "Min Salary", "n"), ("max_salary", "Max Salary", "n")],
    },
    "division": {
        "title": "Divisions", "subtitle": "division", "company": True,
        "sql": "SELECT RTRIM(code) AS code, RTRIM(COALESCE(descrip,'')) AS descrip, RTRIM(COALESCE(head,'')) AS head "
               "FROM division WHERE company=? ORDER BY code",
        "cols": [("code", "Code", "m"), ("descrip", "Division", ""), ("head", "Head (Emp)", "m")],
    },
    "department": {
        "title": "Departments", "subtitle": "department", "company": True,
        "sql": "SELECT RTRIM(division) AS division, RTRIM(code) AS code, RTRIM(COALESCE(descrip,'')) AS descrip, "
               "RTRIM(COALESCE(head,'')) AS head FROM department WHERE company=? ORDER BY division, code",
        "cols": [("division", "Div", "m"), ("code", "Code", "m"), ("descrip", "Department", ""), ("head", "Head", "m")],
    },
    "section": {
        "title": "Sections", "subtitle": "section", "company": True,
        "sql": "SELECT RTRIM(division) AS division, RTRIM(dept) AS dept, RTRIM(code) AS code, "
               "RTRIM(COALESCE(descrip,'')) AS descrip, RTRIM(COALESCE(head,'')) AS head "
               "FROM section WHERE company=? ORDER BY division, dept, code",
        "cols": [("division", "Div", "m"), ("dept", "Dept", "m"), ("code", "Code", "m"),
                 ("descrip", "Section", ""), ("head", "Head", "m")],
    },
    "holidays": {
        "title": "Holiday Table", "subtitle": "holidays",
        "sql": "SELECT hyear, hdate, RTRIM(COALESCE(hflag,'')) AS hflag, RTRIM(COALESCE(hdesc,'')) AS hdesc "
               "FROM holidays ORDER BY hdate DESC",
        "cols": [("hyear", "Year", "i"), ("hdate", "Date", "d"), ("hflag", "Type", "c"), ("hdesc", "Holiday", "")],
    },
    "payperiod": {
        "title": "Pay Periods", "subtitle": "payperiod", "company": True,
        "sql": "SELECT payyear, paymonth, RTRIM(payperiod) AS payperiod, RTRIM(COALESCE(paygrp,'')) AS paygrp, "
               "fromdate, todate, empcount, RTRIM(COALESCE(payclose,'')) AS payclose "
               "FROM payperiod WHERE company=? ORDER BY payyear DESC, paymonth DESC, payperiod DESC",
        "cols": [("payyear", "Year", "i"), ("paymonth", "Mo", "i"), ("payperiod", "Per", "c"),
                 ("paygrp", "Grp", "c"), ("fromdate", "From", "d"), ("todate", "To", "d"),
                 ("empcount", "Emps", "i"), ("payclose", "Closed", "c")],
    },
    # ── Transactions (employee-keyed) ──────────────────────────────────────
    "ratechange": {
        "title": "Rate Change", "subtitle": "ratechange",
        "sql": f"SELECT TOP 300 RTRIM(t.emp_id) AS emp_id, {EMPNAME}, t.effdate, t.oldrate, t.newrate, "
               "RTRIM(COALESCE(t.oldpaytype,'')) AS op, RTRIM(COALESCE(t.newpaytype,'')) AS np, "
               "RTRIM(COALESCE(t.reason,'')) AS reason FROM ratechange t " + NAME +
               " ORDER BY t.effdate DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("effdate", "Effective", "d"),
                 ("oldrate", "Old Rate", "n"), ("newrate", "New Rate", "n"), ("op", "Old", "c"),
                 ("np", "New", "c"), ("reason", "Reason", "")],
    },
    "deptchange": {
        "title": "Department Change", "subtitle": "deptchange",
        "sql": f"SELECT TOP 300 RTRIM(t.emp_id) AS emp_id, {EMPNAME}, t.effdate, RTRIM(COALESCE(t.olddept,'')) AS od, "
               "RTRIM(COALESCE(t.newdept,'')) AS nd, RTRIM(COALESCE(t.reason,'')) AS reason FROM deptchange t " + NAME +
               " ORDER BY t.effdate DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("effdate", "Effective", "d"),
                 ("od", "Old Dept", "m"), ("nd", "New Dept", "m"), ("reason", "Reason", "")],
    },
    "jobchange": {
        "title": "Job Position Change", "subtitle": "jobchange",
        "sql": f"SELECT TOP 300 RTRIM(t.emp_id) AS emp_id, {EMPNAME}, t.effdate, RTRIM(COALESCE(t.oldjobcode,'')) AS oj, "
               "RTRIM(COALESCE(t.newjobcode,'')) AS nj, RTRIM(COALESCE(t.promotion,'')) AS promo, "
               "RTRIM(COALESCE(t.reason,'')) AS reason FROM jobchange t " + NAME + " ORDER BY t.effdate DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("effdate", "Effective", "d"),
                 ("oj", "Old Job", "m"), ("nj", "New Job", "m"), ("promo", "Promo", "c"), ("reason", "Reason", "")],
    },
    "companychg": {
        "title": "Company Change", "subtitle": "companychg",
        "sql": "SELECT TOP 300 RTRIM(t.emp_id) AS emp_id, t.effdate, RTRIM(COALESCE(t.oldcom,'')) AS oc, "
               "RTRIM(COALESCE(t.newcom,'')) AS nc, RTRIM(COALESCE(t.reason,'')) AS reason "
               "FROM companychg t ORDER BY t.effdate DESC",
        "cols": [("emp_id", "Emp No", "m"), ("effdate", "Effective", "d"), ("oc", "Old Co", "m"),
                 ("nc", "New Co", "m"), ("reason", "Reason", "")],
    },
    "loans": {
        "title": "Loans", "subtitle": "loans",
        "sql": f"SELECT TOP 400 RTRIM(t.emp_id) AS emp_id, {EMPNAME}, RTRIM(COALESCE(i.descrip,t.payitem)) AS descrip, "
               "RTRIM(COALESCE(t.refno,'')) AS refno, t.loanamt, t.payded, t.no_of_pay, t.no_paid, "
               "t.totalpaid, ((COALESCE(t.loanamt,0)+COALESCE(t.intamt,0))-(COALESCE(t.totalpaid,0)+COALESCE(t.totalpaidi,0))) AS bal FROM loans t " + NAME +
               " LEFT JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem ORDER BY t.dateapprov DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("descrip", "Loan", ""),
                 ("refno", "Ref No", "m"), ("loanamt", "Amount", "n"), ("payded", "Per Pay", "n"),
                 ("no_paid", "Paid", "i"), ("no_of_pay", "Terms", "i"), ("bal", "Balance", "n")],
    },
    "leavetran": {
        "title": "Leaves and Absences", "subtitle": "leavetran",
        "sql": f"SELECT TOP 400 RTRIM(t.emp_id) AS emp_id, {EMPNAME}, RTRIM(COALESCE(i.descrip,t.payitem)) AS descrip, "
               "t.frdate, t.todate, RTRIM(COALESCE(t.reason,'')) AS reason FROM leavetran t " + NAME +
               " LEFT JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem ORDER BY t.frdate DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("descrip", "Leave Type", ""),
                 ("frdate", "From", "d"), ("todate", "To", "d"), ("reason", "Reason", "")],
    },
    "empshift": {
        "title": "Employee Shifts", "subtitle": "empshift", "page_size": 25,
        "sql": f"SELECT RTRIM(t.emp_id) AS emp_id, {EMPNAME}, t.frdate, RTRIM(COALESCE(t.shift,'')) AS shift "
               "FROM empshift t " + NAME + " ORDER BY t.frdate DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("frdate", "From Date", "d"), ("shift", "Shift", "m")],
    },
    # ── Masterlists ────────────────────────────────────────────────────────
    "ml_dept": {
        "title": "Masterlist by Department", "company": True,
        "sql": "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "RTRIM(COALESCE(p.division,'')) AS division, RTRIM(COALESCE(p.dept,'')) AS dept, "
               "RTRIM(COALESCE(p.section,'')) AS section, RTRIM(COALESCE(j.descrip,'')) AS job, RTRIM(p.empsts) AS empsts "
               "FROM personnel p LEFT JOIN jobcode j ON j.company=p.company AND j.code=p.jobcode "
               "WHERE p.company=? AND p.empsts<>'X' ORDER BY p.division, p.dept, p.section, p.lastname",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("division", "Div", "m"),
                 ("dept", "Dept", "m"), ("section", "Sect", "m"), ("job", "Position", ""), ("empsts", "Sts", "c")],
    },
    "ml_paygroup": {
        "title": "Masterlist by Pay Group", "company": True,
        "sql": "SELECT RTRIM(COALESCE(pr.paygroup,'')) AS paygroup, RTRIM(p.emp_id) AS emp_id, "
               "RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, RTRIM(COALESCE(pr.paytype,'')) AS paytype, "
               "pr.salary FROM personnel p JOIN payroll pr ON pr.company=p.company AND pr.emp_id=p.emp_id "
               "WHERE p.company=? AND p.empsts<>'X' ORDER BY pr.paygroup, p.lastname",
        "cols": [("paygroup", "Pay Grp", "c"), ("emp_id", "Emp No", "m"), ("empname", "Name", ""),
                 ("paytype", "Type", "c"), ("salary", "Rate", "n")],
    },
    "ml_shift": {
        "title": "Masterlist by Shift", "company": True,
        "sql": "SELECT RTRIM(COALESCE(p.shift,'')) AS shift, RTRIM(p.emp_id) AS emp_id, "
               "RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, RTRIM(COALESCE(p.dept,'')) AS dept "
               "FROM personnel p WHERE p.company=? AND p.empsts<>'X' ORDER BY p.shift, p.lastname",
        "cols": [("shift", "Shift", "m"), ("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("dept", "Dept", "m")],
    },
    # ── Government / payroll reports ───────────────────────────────────────
    "rpt_sss": {
        "title": "SSS Monthly Remittance", "subtitle": "Employees with SSS numbers", "company": True,
        "sql": "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "RTRIM(COALESCE(p.sssno,'')) AS sssno, pr.salary FROM personnel p "
               "LEFT JOIN payroll pr ON pr.company=p.company AND pr.emp_id=p.emp_id "
               "WHERE p.company=? AND p.empsts<>'X' AND RTRIM(COALESCE(p.sssno,''))<>'' ORDER BY p.lastname",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("sssno", "SSS No", "m"), ("salary", "Rate", "n")],
    },
    "rpt_phic": {
        "title": "PhilHealth Monthly Remittance", "company": True,
        "sql": "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "RTRIM(COALESCE(p.phealthno,'')) AS phealthno, pr.salary FROM personnel p "
               "LEFT JOIN payroll pr ON pr.company=p.company AND pr.emp_id=p.emp_id "
               "WHERE p.company=? AND p.empsts<>'X' AND RTRIM(COALESCE(p.phealthno,''))<>'' ORDER BY p.lastname",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("phealthno", "PhilHealth No", "m"), ("salary", "Rate", "n")],
    },
    "rpt_hdmf": {
        "title": "HDMF (Pag-IBIG) Monthly Remittance", "company": True,
        "sql": "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "RTRIM(COALESCE(p.hdmfno,'')) AS hdmfno, pr.salary FROM personnel p "
               "LEFT JOIN payroll pr ON pr.company=p.company AND pr.emp_id=p.emp_id "
               "WHERE p.company=? AND p.empsts<>'X' AND RTRIM(COALESCE(p.hdmfno,''))<>'' ORDER BY p.lastname",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("hdmfno", "HDMF No", "m"), ("salary", "Rate", "n")],
    },
    "rpt_alpha": {
        "title": "Alphalist of Employees", "subtitle": "BIR alphalist (personnel with TIN)", "company": True,
        "sql": "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname)||' '||RTRIM(COALESCE(p.middlename,'')) AS empname, "
               "RTRIM(COALESCE(p.tin,'')) AS tin, RTRIM(p.empsts) AS empsts, p.datehired, p.dateresgnd "
               "FROM personnel p WHERE p.company=? ORDER BY p.lastname",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("tin", "TIN", "m"),
                 ("empsts", "Sts", "c"), ("datehired", "Hired", "d"), ("dateresgnd", "Separated", "d")],
    },
    "rpt_loans": {
        "title": "Loans History", "company": True,
        "sql": f"SELECT RTRIM(t.emp_id) AS emp_id, {EMPNAME}, RTRIM(COALESCE(i.descrip,t.payitem)) AS descrip, "
               "t.loanamt, t.totalpaid, ((COALESCE(t.loanamt,0)+COALESCE(t.intamt,0))-(COALESCE(t.totalpaid,0)+COALESCE(t.totalpaidi,0))) AS bal, t.dateapprov FROM loans t " + NAME +
               " LEFT JOIN payitem i ON i.company=t.company AND i.payitem=t.payitem WHERE t.company=? ORDER BY t.dateapprov DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("descrip", "Loan", ""),
                 ("loanamt", "Amount", "n"), ("totalpaid", "Paid", "n"), ("bal", "Balance", "n"),
                 ("dateapprov", "Approved", "d")],
    },
    # ── HR reports ─────────────────────────────────────────────────────────
    "hr_hired": {
        "title": "Hired This Period", "subtitle": "Most recent hires", "company": True,
        "sql": "SELECT TOP 200 RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "p.datehired, RTRIM(COALESCE(p.dept,'')) AS dept, RTRIM(p.empsts) AS empsts FROM personnel p "
               "WHERE p.company=? AND p.datehired IS NOT NULL ORDER BY p.datehired DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("datehired", "Date Hired", "d"),
                 ("dept", "Dept", "m"), ("empsts", "Sts", "c")],
    },
    "hr_dueregular": {
        "title": "Due for Regularization", "subtitle": "Probationary employees", "company": True,
        "sql": "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "p.datehired, RTRIM(COALESCE(p.dept,'')) AS dept FROM personnel p "
               "WHERE p.company=? AND p.empsts='P' ORDER BY p.datehired",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("datehired", "Date Hired", "d"), ("dept", "Dept", "m")],
    },
    "hr_resigned": {
        "title": "Resigned / Separated", "company": True,
        "sql": "SELECT TOP 300 RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "p.dateresgnd, RTRIM(COALESCE(p.reasonresg,'')) AS reasonresg FROM personnel p "
               "WHERE p.company=? AND p.empsts='X' ORDER BY p.dateresgnd DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("dateresgnd", "Separated", "d"),
                 ("reasonresg", "Reason", "")],
    },
    "hr_birthdays": {
        "title": "Birthday Celebrants", "company": True,
        "sql": "SELECT EXTRACT(MONTH FROM p.birthdate)::int AS mo, EXTRACT(DAY FROM p.birthdate)::int AS dy, RTRIM(p.emp_id) AS emp_id, "
               "RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, p.birthdate FROM personnel p "
               "WHERE p.company=? AND p.empsts<>'X' AND p.birthdate IS NOT NULL ORDER BY EXTRACT(MONTH FROM p.birthdate)::int, EXTRACT(DAY FROM p.birthdate)::int",
        "cols": [("mo", "Mo", "i"), ("dy", "Day", "i"), ("emp_id", "Emp No", "m"), ("empname", "Name", ""),
                 ("birthdate", "Birth Date", "d")],
    },
    "hr_headcount": {
        "title": "Headcount by Dept / Status", "company": True,
        "sql": "SELECT RTRIM(COALESCE(p.division,'')) AS division, RTRIM(COALESCE(p.dept,'')) AS dept, "
               "RTRIM(p.empsts) AS empsts, COUNT(*) AS cnt FROM personnel p WHERE p.company=? "
               "GROUP BY p.division, p.dept, p.empsts ORDER BY p.division, p.dept, p.empsts",
        "cols": [("division", "Div", "m"), ("dept", "Dept", "m"), ("empsts", "Status", "c"), ("cnt", "Count", "i")],
    },
    "hr_yos": {
        "title": "Years of Service", "company": True,
        "sql": "SELECT RTRIM(p.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "p.datehired, EXTRACT(YEAR FROM age(CURRENT_DATE, p.datehired))::int AS yos, RTRIM(p.empsts) AS empsts "
               "FROM personnel p WHERE p.company=? AND p.empsts<>'X' AND p.datehired IS NOT NULL "
               "ORDER BY p.datehired",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("datehired", "Date Hired", "d"),
                 ("yos", "Yrs", "i"), ("empsts", "Sts", "c")],
    },
    "hr_leavebal": {
        "title": "Leave Balances", "company": True,
        "sql": "SELECT RTRIM(l.emp_id) AS emp_id, RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, "
               "RTRIM(l.lvcode) AS lvcode, l.tyent, l.dayern, l.dayuse, (l.tyent+l.dayern-l.dayuse) AS bal "
               "FROM leaves l JOIN personnel p ON p.company=l.company AND p.emp_id=l.emp_id "
               "WHERE l.company=? AND p.empsts<>'X' ORDER BY p.lastname, l.lvcode",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("lvcode", "Leave", "m"),
                 ("tyent", "Entitled", "n"), ("dayern", "Earned", "n"), ("dayuse", "Used", "n"), ("bal", "Balance", "n")],
    },
    "hr_training": {
        "title": "Employee Training Report", "company": True,
        "sql": f"SELECT TOP 300 RTRIM(t.emp_id) AS emp_id, {EMPNAME}, RTRIM(COALESCE(t.coursedesc,'')) AS coursedesc, "
               "t.fromdate, t.todate, t.tlhours FROM training t " + NAME + " WHERE t.company=? ORDER BY t.fromdate DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("coursedesc", "Course", ""),
                 ("fromdate", "From", "d"), ("todate", "To", "d"), ("tlhours", "Hours", "n")],
    },
    "hr_blood": {
        "title": "Employee List by Blood Type", "company": True,
        "sql": "SELECT RTRIM(COALESCE(p.bloodtype,'—')) AS bloodtype, RTRIM(p.emp_id) AS emp_id, "
               "RTRIM(p.lastname)||', '||RTRIM(p.firstname) AS empname, RTRIM(COALESCE(p.dept,'')) AS dept "
               "FROM personnel p WHERE p.company=? AND p.empsts<>'X' ORDER BY p.bloodtype, p.lastname",
        "cols": [("bloodtype", "Blood", "c"), ("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("dept", "Dept", "m")],
    },
    "hr_education": {
        "title": "Educational Attainment", "company": True,
        "sql": f"SELECT TOP 400 RTRIM(t.emp_id) AS emp_id, {EMPNAME}, RTRIM(COALESCE(t.instdesc,'')) AS instdesc, "
               "RTRIM(COALESCE(t.coursedesc,'')) AS coursedesc, t.todate FROM edutrain t " + NAME +
               " WHERE t.company=? ORDER BY p.lastname",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("instdesc", "School", ""),
                 ("coursedesc", "Course", ""), ("todate", "Completed", "d")],
    },
    "hr_medical": {
        "title": "Medical History", "company": True,
        "sql": f"SELECT TOP 300 RTRIM(t.emp_id) AS emp_id, {EMPNAME}, t.chkdate, RTRIM(COALESCE(t.chktype,'')) AS chktype, "
               "RTRIM(COALESCE(t.findings,'')) AS findings FROM medical t " + NAME + " WHERE t.company=? ORDER BY t.chkdate DESC",
        "cols": [("emp_id", "Emp No", "m"), ("empname", "Name", ""), ("chkdate", "Date", "d"),
                 ("chktype", "Type", ""), ("findings", "Findings", "")],
    },
}


# ── editable reference tables: {grid key: {table, pk, fields[(col,label,type)]}} ──
# type: text | num | int | date.  company-scoped grids inject company from the selector.
EDITABLE = {
    "payitem": {"table": "payitem", "pk": ["company", "payitem"], "fields": [
        ("payitem", "Item code", "text"), ("descrip", "Description", "text"),
        ("category", "Category (0-9)", "text"), ("b4tax", "Before tax (Y/N)", "text"),
        ("priority", "Priority", "int"), ("freq", "Frequency", "text"), ("taxscheme", "Tax scheme", "text")]},
    "ssstable": {"table": "ssstable", "pk": ["frgross", "togross"], "fields": [
        ("frgross", "From gross", "num"), ("togross", "To gross", "num"), ("credit", "MSC / credit", "num"),
        ("ssser", "SSS employer", "num"), ("sssee", "SSS employee", "num"), ("eccer", "EC employer", "num")]},
    "phtable": {"table": "phtable", "pk": ["frgross"], "fields": [
        ("bracket", "Bracket", "int"), ("frgross", "From", "num"), ("togross", "To", "num"),
        ("salarybase", "Salary base", "num"), ("mcrer", "ER share", "num"), ("mcree", "EE share", "num")]},
    "taxtable": {"table": "taxtable", "pk": ["xtype", "xunit"], "fields": [
        ("xtype", "Type (S/M/D/W)", "text"), ("xunit", "Row (Z/S/M/FIXAM/PRCNT)", "text"),
        ("xdesc", "Description", "text"), ("exemption", "Exemption", "num"),
        ("range01", "Col 1", "num"), ("range02", "Col 2", "num"), ("range03", "Col 3", "num"),
        ("range04", "Col 4", "num"), ("range05", "Col 5", "num")]},
    "holidays": {"table": "holidays", "pk": ["hyear", "hdate"], "fields": [
        ("hyear", "Year", "int"), ("hdate", "Date", "date"), ("hflag", "Type", "text"), ("hdesc", "Holiday", "text")]},
    "banks": {"table": "banks", "pk": ["company", "code"], "fields": [
        ("code", "Code", "text"), ("bankname", "Bank name", "text"),
        ("branchname", "Branch", "text"), ("acctformat", "Account format", "text")]},
    "otrates": {"table": "otrates", "pk": ["company", "otcode", "payitem"], "fields": [
        ("otcode", "OT code", "text"), ("payitem", "Pay item", "text"),
        ("otrate", "OT rate", "num"), ("nprate", "Night-prem rate", "num")]},
    "shifttable": {"table": "shifttable", "pk": ["company", "shift"], "fields": [
        ("shift", "Shift", "text"), ("shiftdesc", "Description", "text"),
        ("stdhours", "Std hours", "num"), ("stdot", "Std OT", "num"), ("flextime", "Flex (Y/N)", "text")]},
    "jobcode": {"table": "jobcode", "pk": ["company", "code"], "fields": [
        ("code", "Code", "text"), ("descrip", "Position title", "text"), ("category", "Category", "text"),
        ("jobgrade", "Grade", "text"), ("min_salary", "Min salary", "num"), ("max_salary", "Max salary", "num")]},
    "division": {"table": "division", "pk": ["company", "code"], "fields": [
        ("code", "Code", "text"), ("descrip", "Division", "text"), ("head", "Head (emp no)", "text")]},
    "department": {"table": "department", "pk": ["company", "division", "code"], "fields": [
        ("division", "Division", "text"), ("code", "Code", "text"),
        ("descrip", "Department", "text"), ("head", "Head (emp no)", "text")]},
    "section": {"table": "section", "pk": ["company", "division", "dept", "code"], "fields": [
        ("division", "Division", "text"), ("dept", "Department", "text"), ("code", "Code", "text"),
        ("descrip", "Section", "text"), ("head", "Head (emp no)", "text")]},
    "tablecodes": {"table": "tablecode1", "pk": ["tblcode", "fldcode"], "fields": [
        ("tblcode", "Table code", "text"), ("fldcode", "Field code", "text"),
        ("descrip", "Description", "text"), ("vardata", "Value", "text"), ("applicat", "App", "text")]},
    # staff sign-ins: global (no company), stamps change_date only; creating one seeds a
    # generated password (shown once in the flash) and rows get a reset-password action
    "users": {"table": "users", "pk": ["user_id"], "stamps": [("change_date", "now")], "fields": [
        ("user_id", "User ID", "text"), ("user_name", "Full name", "text"),
        ("class", "Class (Q/U)", "text"), ("emp_id", "Badge / Emp No", "text")]},
}
for _k, _meta in EDITABLE.items():
    if _k in GRIDS:
        GRIDS[_k]["edit"] = _meta
