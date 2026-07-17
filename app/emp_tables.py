"""Editable employee 201-file sections. Each tab maps to one or more sections;
each section is a child table edited in the context of (company, emp_id).

section: {table, label, fields[(col,label,type)], order, single(bool), file{col,ext,name}}
type: text | num | int | date.  Rows are edited/deleted by the surrogate `rowid`
(added by setup_emptables.py); "single" sections (payroll) key on (company, emp_id).
"""

SECTIONS = {
    "education": [{"table": "edutrain", "label": "Education", "order": "fromdate", "fields": [
        ("instdesc", "School / Institution", "text"), ("coursedesc", "Course", "text"),
        ("edu_level", "Level", "text"), ("fromdate", "From", "date"), ("todate", "To", "date")]}],
    "training": [{"table": "training", "label": "Training", "order": "fromdate DESC", "fields": [
        ("coursedesc", "Training", "text"), ("instdesc", "Provider", "text"),
        ("fromdate", "From", "date"), ("todate", "To", "date"), ("tlhours", "Hours", "num")]}],
    "workexp": [{"table": "workexp", "label": "Work Experience", "order": "fromdate DESC", "fields": [
        ("prevcompnm", "Previous Employer", "text"), ("workexpdsc", "Position", "text"),
        ("fromdate", "From", "date"), ("todate", "To", "date")]}],
    "dependents": [{"table": "dependents", "label": "Dependents", "order": "name", "fields": [
        ("name", "Name", "text"), ("relcde", "Relation", "text"),
        ("sex", "Sex", "text"), ("birtdate", "Birth date", "date")]}],
    "leaves": [
        {"table": "leaves", "label": "Leave balances", "order": "lvcode", "fields": [
            ("lvcode", "Leave code", "text"), ("tyent", "Entitled", "num"),
            ("dayern", "Earned", "num"), ("dayuse", "Used", "num")]},
        {"table": "leavetran", "label": "Leave / absence transactions", "order": "frdate DESC", "fields": [
            ("payitem", "Leave item", "text"), ("frdate", "From", "date"),
            ("todate", "To", "date"), ("reason", "Reason", "text")]}],
    "medical": [{"table": "medical", "label": "Medical history", "order": "chkdate DESC", "fields": [
        ("chkdate", "Date", "date"), ("chktype", "Type", "text"), ("findings", "Findings", "text"),
        ("illtype", "Illness", "text"), ("medication", "Medication", "text"),
        ("follow_up_date", "Follow-up", "date")]}],
    "appraisal": [{"table": "appraisal", "label": "Appraisals", "order": "apdate DESC", "fields": [
        ("apdate", "Date", "date"), ("aprating", "Rating", "num"),
        ("apprby", "Appraiser", "text"), ("remarks", "Remarks", "text")]}],
    "disciplinary": [{"table": "discipline", "label": "Disciplinary records", "order": "discpdate DESC", "fields": [
        ("discpdate", "Date", "date"), ("violation", "Violation", "text"), ("penalty", "Penalty", "text"),
        ("frdate", "From", "date"), ("todate", "To", "date"), ("remarks", "Remarks", "text")]}],
    "doc": [{"table": "edoc", "label": "Documents", "order": "docdate DESC",
             "file": {"col": "docimg", "ext": "docimgext", "name": "docname"}, "fields": [
                 ("docname", "Document name", "text"), ("docdate", "Date", "date"), ("remarks", "Remarks", "text")]}],
    "payroll": [
        {"table": "payroll", "label": "Payroll setup", "single": True, "fields": [
            ("salary", "Salary rate", "num"), ("paytype", "Pay type (D/M)", "text"),
            ("paygroup", "Pay group", "text"), ("paymode", "Pay mode", "text"),
            ("bankcode", "Bank code", "text"), ("bankacct", "Bank account", "text")]}],
    # Loans get their own tab — the list joins payitem for the loan's name and derives the
    # same figures the Loans screen shows: Amount = principal + interest, Total Paid = paid
    # + paid adjustments, Balance = the difference. loanamt 99999 flags an open-ended fund,
    # which has no fixed amount — nulled so it renders blank. `fields` drives the edit form.
    "loans": [
        {"table": "loans", "label": "Loans", "order": "dateapprov DESC",
         "list_sql":
             "SELECT l.rowid, RTRIM(COALESCE(i.descrip, l.payitem)) AS descrip, l.dateapprov, "
             "RTRIM(COALESCE(l.refno,'')) AS ltype, "
             "CASE WHEN COALESCE(l.loanamt,0)>=99999 THEN NULL "
             "     ELSE COALESCE(l.loanamt,0)+COALESCE(l.intamt,0) END AS amount, "
             "COALESCE(l.payded,0) AS payded, "
             "COALESCE(l.totalpaid,0)+COALESCE(l.totalpaidi,0) AS paid, "
             "CASE WHEN COALESCE(l.loanamt,0)>=99999 THEN 0 "
             "     ELSE (COALESCE(l.loanamt,0)+COALESCE(l.intamt,0))"
             "          -(COALESCE(l.totalpaid,0)+COALESCE(l.totalpaidi,0)) END AS bal, "
             "RTRIM(COALESCE(l.docno,'')) AS docno "
             "FROM loans l LEFT JOIN payitem i ON i.company=l.company AND i.payitem=l.payitem "
             "WHERE l.company=? AND l.emp_id=? ORDER BY l.dateapprov DESC",
         "list_cols": [("descrip", "Loan", "text"), ("dateapprov", "Date", "date"),
                       ("ltype", "Type", "text"), ("amount", "Amount", "num"),
                       ("payded", "Per Pay", "num"), ("paid", "Total Paid", "num"),
                       ("bal", "Balance", "num"), ("docno", "Doc. No.", "text")],
         # per-row link column: each loan opens its own instalment history in a pop-out
         "row_link": {"endpoint": "loan_payments", "label": "Payments", "popout": True,
                      "title": "Payment History", "title_col": "descrip"},
         # add/change uses the dedicated Loan dialog rather than the generic row form
         "form": {"endpoint": "loan_form", "popout": True, "add_title": "Loan - Add",
                  "edit_title": "Loan - Change"},
         "fields": [
            ("payitem", "Loan item", "text"), ("refno", "Type", "text"), ("loanamt", "Principal", "num"),
            ("intamt", "Interest", "num"), ("payded", "Per pay", "num"),
            ("no_of_pay", "Terms", "int"), ("totalpaid", "Total paid", "num")]}],
    "fixallow": [{"table": "fixallow", "label": "Fixed allowances", "order": "payitem", "fields": [
        ("payitem", "Pay item", "text"), ("amount", "Amount", "num"), ("freq", "Frequency", "text"),
        ("paytype", "Pay type", "text"), ("effdate", "Effective", "date")]}],
    "fixded": [{"table": "fixded", "label": "Fixed deductions", "order": "payitem", "fields": [
        ("payitem", "Pay item", "text"), ("amount", "Amount", "num"),
        ("freq", "Frequency", "text"), ("b4tax", "Before tax", "text")]}],
}

SECTION_TABS = set(SECTIONS)
SECTION_BY_TABLE = {}
for _tab, _secs in SECTIONS.items():
    for _s in _secs:
        _s["tab"] = _tab
        SECTION_BY_TABLE[_s["table"]] = _s
