# HRPayroll_L98 — Full Schema (restored 2026-07-15)

Server: `localhost\SQLEXPRESS` · DB: `HRPayroll_L98` · Tables: 101 · Foreign keys: 3 (all integrity was app-enforced)

## Row counts

|Table|Rows|
|---|---|
|timecard|387,859|
|timecardtr|380,647|
|paytranh|352,719|
|dailyattrw|45,781|
|paydates|40,666|
|authority|13,392|
|chglog|5,408|
|leavetran|4,133|
|empshift|3,080|
|loans|2,611|
|paytranc|2,257|
|ratechange|1,102|
|payperiod|1,086|
|tablecode1|1,063|
|timecardtm|1,060|
|shiftexcpt|727|
|alphalist|683|
|paytran|652|
|payitem|618|
|empstschg|617|
|optionsx|595|
|unappdedpp|560|
|jobchange|511|
|multi_hiredresgnd_dt|497|
|personnel|497|
|deptchange|493|
|payroll|491|
|leaves|444|
|discipline|299|
|payrollemp|265|
|fixallow|244|
|jobcode|243|
|otrates|236|
|holidays|204|
|companychg|189|
|dailyattsm|183|
|shifttable|154|
|paygroupsc|150|
|edutrain|115|
|taxtable|96|
|acctable|76|
|compusers|69|
|stdleaves|56|
|appraisal|53|
|workexp|53|
|ssstable|51|
|dependents|42|
|phtable|32|
|department|27|
|edoc|22|
|lcargolist_copy|21|
|pbcatedt|21|
|pbcatfmt|20|
|section|19|
|users|17|
|holidaytbl|13|
|division|10|
|holidayf|10|
|fixded|9|
|banks|8|
|paytranb|6|
|company|4|
|empfinalpy|4|
|applicatn|3|
|training|3|
|policy|1|

Empty tables (35): absentism_workf, acctcodes, applicant_evaluation, applicant_ext, bankxmit, careerplan, centelim, compben, ctoalloc, ctoalloch, dailyatt, ddsaut, empnotes, exemptable, glcodea, glcodeb, glworka, glworkb, jobcat, jobgrade, medical, pa_exception, padatexc, payattend, payexcept, payrollemp_recalc, paytrana, paytrancytd, paytrand, pbcatcol, pbcattbl, pbcatvld, perfectat1, tablecode3, timeinout

## Tables

### absentism_workf  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|trdate|datetime||
|pay_item|varchar(3)||
|daycd|char(1)|Y|
|absday|decimal(2,1)|Y|

Indexes: `absentism_workf_x` PK (company,emp_id,trdate,pay_item)

### acctable  (76 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|accode|varchar(3)||
|acctabdesc|varchar(30)||
|datiss|datetime||
|qtyiss|numeric(5,1)|Y|
|unmsr|varchar(2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|etstdate|datetime|Y|
|refno|varchar(15)|Y|
|issuedby|varchar(30)|Y|
|datereturn|datetime|Y|
|terms|numeric(3,0)|Y|
|repldate|datetime|Y|

Indexes: `acctable_x` PK (company,emp_id,accode,acctabdesc,datiss)

### acctcodes  (0 rows)

|Column|Type|Null|
|---|---|---|
|acctno|varchar(15)||
|acctdesc|varchar(50)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|aclass|char(1)|Y|

Indexes: `PK_acctcodes` PK (acctno)

### alphalist  (683 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|form_type|varchar(6)||
|employer_tin|varchar(20)|Y|
|employer_branch_code|varchar(3)||
|retrn_period|datetime||
|schedule_num|varchar(4)||
|sequence_num|numeric(5,0)||
|registered_name|varchar(50)||
|first_name|varchar(30)||
|last_name|varchar(30)||
|middle_name|varchar(30)||
|tin|varchar(20)|Y|
|branch_code|varchar(3)||
|employment_from|datetime|Y|
|employment_to|datetime|Y|
|atc_code|varchar(5)||
|status_code|char(1)||
|actual_amt_wthld|numeric(12,2)||
|income_payment|numeric(12,2)||
|pres_taxable_salaries|numeric(12,2)||
|pres_taxable_13th_month|numeric(12,2)||
|pres_tax_wthld|numeric(12,2)||
|pres_nontax_salaries|numeric(12,2)||
|pres_nontax_13th_month|numeric(12,2)||
|prev_taxable_salaries|numeric(12,2)||
|prev_taxable_13th_month|numeric(12,2)||
|prev_tax_wthld|numeric(12,2)||
|prev_nontax_salaries|numeric(12,2)||
|prev_nontax_13th_month|numeric(12,2)||
|pres_nontax_sss_gsis_oth_cont|numeric(12,2)||
|prev_nontax_sss_gsis_oth_cont|numeric(12,2)||
|prev_deminimis|numeric(12,2)|Y|
|prev_basic|numeric(12,2)|Y|
|tax_rate|numeric(12,2)||
|over_wthld|numeric(12,2)||
|amt_wthld_dec|numeric(12,2)||
|exmpn_amt|numeric(12,2)||
|tax_due|numeric(12,2)||
|heath_premium|numeric(12,2)||
|fringe_benefit|numeric(12,2)||
|monetary_value|numeric(12,2)||
|refresh|char(1)|Y|
|exemptcode|char(6)|Y|
|fixtax|char(1)|Y|
|pcttax|decimal(4,4)|Y|
|pres_gross|numeric(12,2)|Y|
|pres_basic|numeric(12,2)|Y|
|pres_deminimis|numeric(12,2)|Y|
|gross|char(10)|Y|
|basic|char(10)|Y|
|prev_gross|numeric(12,2)|Y|
|pres_basicsmwpd|numeric(12,2)|Y|
|pres_basicsmwpm|numeric(12,2)|Y|
|pres_basicsmwpy|numeric(12,2)|Y|
|factorused|numeric(12,5)|Y|
|pres_holiday_pay|numeric(12,2)|Y|
|pres_ot_pay|numeric(12,2)|Y|
|pres_nightdiff|numeric(12,2)|Y|
|pres_hazardpay|numeric(12,2)|Y|
|prev_holiday_pay|numeric(12,2)|Y|
|prev_ot_pay|numeric(12,2)|Y|
|prev_nightdiff|numeric(12,2)|Y|
|prev_hazardpay|numeric(12,2)|Y|
|createdby|varchar(10)|Y|
|createdate|datetime|Y|
|mwe|char(1)|Y|
|closed|char(1)|Y|

Indexes: `alphalist_x` PK (company,emp_id,retrn_period)

### applicant_evaluation  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|char(3)||
|applicant_id|char(6)||
|code|char(3)||
|score|numeric(6,2)|Y|
|percentage|numeric(5,2)|Y|
|changeby|char(10)|Y|
|changedate|datetime|Y|
|remarks|char(20)|Y|

Indexes: `applicant_evaluation_x` PK (company,applicant_id,code)

### applicant_ext  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|char(3)||
|applicant_id|char(6)||
|posapply1|char(30)|Y|
|dateapply1|datetime|Y|
|posapply2|char(30)|Y|
|dateapply2|datetime|Y|
|posapply3|char(30)|Y|
|dateapply3|datetime|Y|
|height|char(10)|Y|
|weight|char(10)|Y|
|complexion|char(10)|Y|
|hair|char(10)|Y|
|eyes|char(10)|Y|
|endorsedby|char(6)|Y|
|endorsedto|char(4)|Y|
|changeby|char(10)|Y|
|changedate|datetime|Y|
|changeby2|char(10)|Y|
|changedat2|datetime|Y|
|emp_id|char(6)|Y|
|emailadd|char(100)|Y|
|pos1recomnd|char(45)|Y|
|pos2recomnd|char(45)|Y|
|pos3recomnd|char(45)|Y|
|endorsedto2|char(4)|Y|
|endorsedto3|char(4)|Y|
|remarks|char(30)|Y|

Indexes: `applicant_ext_x` PK (company,applicant_id)

### applicatn  (3 rows)

|Column|Type|Null|
|---|---|---|
|appname|varchar(2)||
|appdesc|varchar(50)|Y|

Indexes: `applicatn_x` PK (appname)

### appraisal  (53 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|apdate|datetime||
|apprby|varchar(6)|Y|
|aprating|numeric(6,2)|Y|
|remarks|varchar(100)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|incupdflag|char(1)|Y|

Indexes: `appraisal_x` PK (company,emp_id,apdate)

### authority  (13,392 rows)

|Column|Type|Null|
|---|---|---|
|appname|varchar(2)||
|menuname|varchar(30)||
|optionname|varchar(60)||
|company|varchar(3)||
|username|varchar(10)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|x_add|char(1)|Y|
|x_change|char(1)|Y|
|x_delete|char(1)|Y|
|usecount|numeric(9,0)|Y|
|dateused|datetime|Y|

Indexes: `PK_authority` PK (appname,menuname,optionname,company,username)

### banks  (8 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|code|varchar(5)||
|bankname|varchar(35)|Y|
|branchname|varchar(15)|Y|
|address|varchar(100)|Y|
|acctnum|varchar(20)|Y|
|acctformat|varchar(20)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|batchno|numeric(10,0)|Y|

Indexes: `banks_x` PK (code,company)

### bankxmit  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|bankcode|varchar(5)||
|seqno (identity)|numeric(10,0)||
|crduedate|datetime||
|batchno|numeric(10,0)||
|empcount|numeric(7,0)||
|tlamount|decimal(13,2)||
|createdby|varchar(10)||
|createdate|datetime||
|paygroup|char(1)||

Indexes: `PK_bankxmit` PK (company,bankcode,seqno)

### careerplan  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|responsibl|varchar(255)|Y|
|strengths|varchar(255)|Y|
|devneeds|varchar(255)|Y|
|potnextpos|varchar(30)|Y|
|posreplace|varchar(6)|Y|
|belnextpos|varchar(30)|Y|
|devactplan|varchar(150)|Y|
|eduattain|varchar(50)|Y|
|profattain|varchar(50)|Y|
|profintrst|varchar(50)|Y|
|compprof|char(1)|Y|

Indexes: `careerplan_x` PK (company,emp_id)

### centelim  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|amount|numeric(5,2)|Y|
|prevamount|numeric(5,2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `centelim_x` PK (company,emp_id)

### chglog  (5,408 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|changenfo|varchar(50)|Y|
|oldvalue|varchar(20)|Y|
|newvalue|varchar(20)|Y|
|changedby|varchar(10)|Y|
|changedate|datetime|Y|
|ctlno (identity)|numeric(12,0)||

Indexes: `chglog_x` PK (ctlno)

### company  (4 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|companynam|varchar(50)|Y|
|address|varchar(100)|Y|
|period|datetime|Y|
|currency|varchar(3)|Y|
|esipct|numeric(5,2)|Y|
|attendunit|char(1)|Y|
|sssepi|varchar(3)|Y|
|rgapi|varchar(3)|Y|
|wtxpi|varchar(3)|Y|
|vlapi|varchar(3)|Y|
|abapi|varchar(3)|Y|
|abupi|varchar(3)|Y|
|otlpi|varchar(3)|Y|
|ssscpi|varchar(3)|Y|
|npaypi|varchar(3)|Y|
|bpaypi|varchar(3)|Y|
|tdedpi|varchar(3)|Y|
|slapi|varchar(3)|Y|
|sssno|varchar(15)|Y|
|autobadge|char(1)|Y|
|mod11|char(1)|Y|
|dftnatcd|varchar(3)|Y|
|dftrelgn|varchar(3)|Y|
|dftareacd|varchar(5)|Y|
|dftzipcd|varchar(5)|Y|
|dfthdmfmbr|char(1)|Y|
|dftcoopmbr|char(1)|Y|
|dftshift|char(1)|Y|
|dfteligot|char(1)|Y|
|dftpaytype|char(1)|Y|
|dftpaygrp|char(1)|Y|
|dftpayctr|char(1)|Y|
|dftpaymode|char(1)|Y|
|baseday|numeric(9,7)|Y|
|hourspday|numeric(4,2)|Y|
|idprefix|varchar(4)|Y|
|tin|varchar(20)|Y|
|w2sign|varchar(6)|Y|
|emp_id_fmt|varchar(10)|Y|
|emp_id_zro|char(1)|Y|
|picpath|varchar(120)|Y|
|w2signame|varchar(60)|Y|
|bonusmax|numeric(9,2)|Y|
|hdmfpct|numeric(3,2)|Y|
|hdmfmax|numeric(7,2)|Y|
|vlnontax|numeric(2,0)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|mintakepay|numeric(3,2)|Y|
|xadd_col|varchar(50)|Y|
|lcrundt|datetime|Y|
|lcrunby|varchar(10)|Y|
|phidno|varchar(15)|Y|
|pattrdat|datetime|Y|
|lvclorundt|datetime|Y|
|lvclorunby|char(10)|Y|
|zipcode|varchar(10)|Y|
|giveawaydt|datetime|Y|
|maxdlyrate|numeric(9,2)|Y|
|maxmorate|numeric(9,2)|Y|
|mindlyrate|numeric(9,2)|Y|
|minmorate|numeric(9,2)|Y|
|shortname|varchar(10)|Y|
|hdmfno|varchar(15)|Y|
|imgsign|image|Y|
|appbg|image|Y|

Indexes: `company_x` PK (company)

### companychg  (189 rows)

|Column|Type|Null|
|---|---|---|
|emp_id|varchar(6)||
|effdate|datetime||
|firstrec|char(1)|Y|
|oldcom|char(3)|Y|
|newcom|char(3)|Y|
|reason|varchar(30)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `companychg_x` PK (emp_id,effdate)

### compben  (0 rows)

|Column|Type|Null|
|---|---|---|
|position|varchar(50)||
|empcount|numeric(5,0)||
|totalmosal|numeric(11,2)||
|totalmoall|numeric(11,2)||
|totalbonus|numeric(11,2)||

Indexes: `compben_pk` PK (position)

### compusers  (69 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|user_id|varchar(10)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `compusers_x` PK (company,user_id)

### ctoalloc  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payyear|numeric(4,0)||
|paymonth|numeric(2,0)||
|payperiod|char(1)||
|paygroup|char(1)||
|emp_id|varchar(6)||
|trdate|datetime||
|trdate2|datetime||
|payitem|varchar(3)||
|allochrs|numeric(4,2)|Y|

Indexes: `ctoalloc_x` PK (company,payyear,paymonth,payperiod,paygroup,emp_id,trdate,trdate2,payitem)

### ctoalloch  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payyear|numeric(4,0)||
|paymonth|numeric(2,0)||
|payperiod|char(1)||
|paygroup|char(1)||
|emp_id|varchar(6)||
|trdate|datetime||
|trdate2|datetime||
|payitem|varchar(3)||
|allochrs|numeric(4,2)|Y|

Indexes: `ctoalloch_x` PK (company,payyear,paymonth,payperiod,paygroup,emp_id,trdate,trdate2,payitem)

### dailyatt  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|trdate|datetime||
|seqno|numeric(2,0)||
|timein|datetime|Y|
|timeout|datetime|Y|
|tlhours|numeric(4,2)|Y|
|fld|varchar(100)|Y|

Indexes: `dailyatt_x` PK (company,emp_id,trdate,seqno)

### dailyattrw  (45,781 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|badgeno|varchar(4)|Y|
|emp_id|varchar(6)||
|trdate|datetime||
|trtimex|numeric(4,0)||
|trtype|char(1)||
|doorno|varchar(3)|Y|
|procflg|char(1)|Y|
|machinealias|varchar(20)|Y|

Indexes: `dailyattrw_x` PK (company,emp_id,trdate,trtimex,trtype)

### dailyattsm  (183 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|trdate|datetime||
|shift|char(2)|Y|
|tlhours|numeric(4,2)|Y|
|reghrs|numeric(4,2)|Y|
|othrs|numeric(4,2)|Y|
|xothrs|numeric(4,2)|Y|
|rnphrs|numeric(4,2)|Y|
|onphrs|numeric(4,2)|Y|
|xonphrs|numeric(4,2)|Y|

Indexes: `dailyattsm_x` PK (company,emp_id,trdate)

### ddsaut  (0 rows)

|Column|Type|Null|
|---|---|---|
|user_id|varchar(10)||
|company|varchar(3)||
|division|varchar(4)||
|dept|varchar(6)||
|section|varchar(4)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `ddsaut_pk` PK (user_id,company,division,dept,section)

### department  (27 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|division|varchar(4)||
|code|varchar(6)||
|descrip|varchar(30)|Y|
|head|varchar(6)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|mindlyrate|numeric(9,2)|Y|

Indexes: `department_x` PK (company,division,code)

### dependents  (42 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|name|varchar(30)||
|relcde|varchar(3)|Y|
|birtdate|datetime|Y|
|sex|char(1)|Y|
|seqno|int|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `dependents_x` PK (company,emp_id,name)

### deptchange  (493 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|effdate|datetime||
|reason|varchar(30)|Y|
|olddiv|varchar(4)|Y|
|olddept|varchar(6)|Y|
|oldsect|varchar(4)|Y|
|newdiv|varchar(4)|Y|
|newdept|varchar(6)|Y|
|newsect|varchar(4)|Y|
|firstrec|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `deptchange_x` PK (company,emp_id,effdate)

### discipline  (299 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|discpdate|datetime||
|violation|varchar(512)||
|penalty|varchar(30)|Y|
|frdate|datetime|Y|
|todate|datetime|Y|
|remarks|varchar(100)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|codeno|varchar(15)|Y|
|noofdays|decimal(3,0)|Y|

Indexes: `discipline_x` PK (company,emp_id,discpdate,violation)

### division  (10 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|code|varchar(4)||
|descrip|varchar(30)|Y|
|head|varchar(6)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|mindlyrate|numeric(9,2)|Y|

Indexes: `division_x` PK (company,code)

### edoc  (22 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|seqno|numeric(3,0)||
|docname|varchar(50)|Y|
|docimg|image|Y|
|docdate|datetime|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|docimgext|varchar(4)|Y|
|docloc|varchar(256)|Y|
|remarks|varchar(256)|Y|

Indexes: `PK_edoc` PK (company,emp_id,seqno)

### edutrain  (115 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|inst|varchar(3)||
|instdesc|varchar(90)||
|course|varchar(3)||
|coursedesc|varchar(90)||
|fromdate|datetime||
|todate|datetime||
|compcd|varchar(30)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|edu_level|char(3)|Y|

Indexes: `edutrain_x` PK (company,emp_id,inst,instdesc,course,coursedesc,fromdate,todate)

### empfinalpy  (4 rows)

|Column|Type|Null|
|---|---|---|
|company|char(3)||
|emp_id|char(6)||
|dateresgnd|datetime|Y|
|reasonresg|char(100)|Y|
|changeby|char(10)|Y|
|changedate|datetime|Y|
|noofyrs|numeric(5,2)|Y|
|onemoadv|char(1)|Y|
|recsts|char(1)|Y|
|seppaypct|numeric(3,2)|Y|
|mo13|char(1)|Y|
|dedhdmf|char(1)|Y|
|daysperyr|numeric(5,2)|Y|
|noticedate|datetime|Y|

Indexes: `empfinalpy_pk` PK (company,emp_id)

### empnotes  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|seqno|int||
|notes|varchar(200)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|eventdate|datetime|Y|

Indexes: `empnotes_pk` PK (company,emp_id,seqno)

### empshift  (3,080 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|frdate|datetime||
|shift|char(2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `empshift_x` PK (emp_id,frdate)

### empstschg  (617 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|effdate|datetime||
|reason|varchar(30)|Y|
|oldempsts|varchar(4)|Y|
|newempsts|varchar(4)|Y|
|firstrec|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `empstschg_x` PK (company,emp_id,effdate)

### exemptable  (0 rows)

|Column|Type|Null|
|---|---|---|
|xunit|varchar(5)||
|range01|numeric(7,0)||
|range02|numeric(7,0)||
|range03|numeric(7,0)||
|range04|numeric(7,0)||
|range05|numeric(7,0)||
|range06|numeric(7,0)||
|range07|numeric(7,0)||
|range08|numeric(7,0)||
|range09|numeric(7,0)||
|range10|numeric(7,0)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `exemptable_x` PK (xunit)

### fixallow  (244 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|payitem|varchar(3)||
|amount|numeric(9,2)|Y|
|freq|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|partofbasic|char(1)|Y|
|paytype|char(1)|Y|
|effdate|datetime|Y|
|presmwe|char(1)|Y|

Indexes: `fixallow_x` PK (company,emp_id,payitem)

### fixded  (9 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|payitem|varchar(3)||
|amount|numeric(9,2)|Y|
|freq|char(1)|Y|
|b4tax|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `fixded_x` PK (company,emp_id,payitem)

### glcodea  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|jobcode|varchar(4)||
|section|varchar(4)||
|glcode1|varchar(7)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `PK_glcodea` PK (company,jobcode,section)

### glcodeb  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|glcode1|varchar(7)||
|payitem|varchar(3)||
|glcode2|varchar(7)|Y|
|drcrflg|char(1)|Y|
|chgdept|varchar(5)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|glcode3|varchar(7)|Y|

Indexes: `PK_glcodeb` PK (company,glcode1,payitem)

### glworka  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payyear|decimal(4,0)||
|paymonth|decimal(2,0)||
|paycat|char(1)||
|payitem|char(3)||
|glcode1|char(7)||
|rtype|char(1)||
|section|char(4)||
|tramount|decimal(11,2)|Y|
|seqno|decimal(5,0)||
|paygroup|char(3)||

Indexes: `PK_glworka` PK (company,payyear,paymonth,paycat,payitem,glcode1,rtype,section,seqno,paygroup)

### glworkb  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payyear|decimal(4,0)||
|paymonth|decimal(2,0)||
|rtype|char(1)||
|glcode|char(7)|Y|
|drcrflg|char(1)|Y|
|section|char(4)|Y|
|chgdept|char(4)|Y|
|dbamt|decimal(11,2)|Y|
|cramt|decimal(11,2)|Y|
|seqno|decimal(5,0)||
|paygroup|char(3)||
|gltype|char(1)||

Indexes: `PK_glworkb` PK (company,payyear,paymonth,rtype,seqno,paygroup,gltype)

### holidayf  (10 rows)

|Column|Type|Null|
|---|---|---|
|hdate|datetime||
|hflag|char(1)|Y|
|hdesc|varchar(30)|Y|
|hfix|char(1)|Y|

Indexes: `holidayf_x` PK (hdate)

### holidays  (204 rows)

|Column|Type|Null|
|---|---|---|
|hyear|numeric(4,0)||
|hdate|datetime||
|hflag|char(1)|Y|
|hdesc|varchar(30)|Y|
|halfday|char(1)|Y|
|advvl|char(1)|Y|
|chargetovl|char(1)|Y|
|chargeto|varchar(3)|Y|
|appifpres|char(1)|Y|
|chargeto2|varchar(3)|Y|
|chargeto3|varchar(3)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `holidays_x` PK (hyear,hdate)

### holidaytbl  (13 rows)

|Column|Type|Null|
|---|---|---|
|company|char(3)||
|shift|char(2)||
|emp_id|char(6)||
|hdate|datetime||
|hflag|char(1)|Y|
|hdesc|varchar(30)|Y|
|halfday|char(1)|Y|
|advvl|char(1)|Y|
|section|char(4)||
|chargetovl|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|inlieuof|datetime|Y|
|division|varchar(4)|Y|
|dept|varchar(6)|Y|

Indexes: `pk_holidaytbl` UQ (company,shift,emp_id,hdate,division,dept)

### jobcat  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|category|varchar(4)||
|descrip|varchar(30)|Y|
|min_salary|numeric(8,2)|Y|
|max_salary|numeric(8,2)|Y|
|jobclass|char(1)|Y|
|allowot|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `jobcat_x` PK (company,category)

### jobchange  (511 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|effdate|datetime||
|oldjobcode|varchar(4)|Y|
|oldjobcat|varchar(4)|Y|
|oldjobgrd|varchar(3)|Y|
|newjobcode|varchar(4)|Y|
|newjobcat|varchar(4)|Y|
|newjobgrd|varchar(3)|Y|
|reason|varchar(30)|Y|
|firstrec|char(1)|Y|
|promotion|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|noofyears|decimal(5,2)|Y|

Indexes: `jobchange_x` PK (company,emp_id,effdate)

### jobcode  (243 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|code|varchar(4)||
|descrip|varchar(30)|Y|
|category|varchar(4)|Y|
|emptype|varchar(3)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|min_salary|numeric(8,2)|Y|
|max_salary|numeric(8,2)|Y|
|jobgrade|varchar(4)|Y|
|jobgroup|varchar(2)|Y|
|jobclass|char(1)|Y|
|confiagr|char(1)|Y|
|fbncoc|char(1)|Y|
|recid|char(1)|Y|

Indexes: `jobcode_x` PK (company,code)

### jobgrade  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|grade|varchar(4)||
|descrip|char(30)|Y|
|min_salary|numeric(9,2)|Y|
|q1_salary|numeric(9,2)|Y|
|mid_salary|numeric(9,2)|Y|
|q3_salary|numeric(9,2)|Y|
|max_salary|numeric(9,2)|Y|
|jobclass|char(1)|Y|
|allowot|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|otcode|varchar(3)|Y|
|tdyundalw|numeric(5,2)|Y|
|seqno|numeric(4,2)|Y|
|pa|char(1)|Y|
|hrlysal|char(1)|Y|
|gradeno|int|Y|
|allowcto|char(1)|Y|

Indexes: `jobgrade_x` PK (company,grade)

### lcargolist_copy  (21 rows)

|Column|Type|Null|
|---|---|---|
|co|varchar(3)|Y|
|emp_id|varchar(6)||
|firstname|varchar(30)|Y|
|middlename|varchar(30)|Y|
|lastname|varchar(30)|Y|
|designation|varchar(20)|Y|
|basic|float|Y|

Indexes: `lcargolist_x` PK (emp_id)

### leaves  (444 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|lvcode|varchar(3)||
|enttyp|char(1)|Y|
|freqmo|numeric(2,0)|Y|
|lycovr|numeric(5,2)|Y|
|nofday|numeric(3,1)|Y|
|tyent|numeric(5,2)|Y|
|dayern|numeric(5,2)|Y|
|dayuse|numeric(5,2)|Y|
|strdte|datetime|Y|
|nxtdte|datetime|Y|
|lastld|datetime|Y|
|eoyprc|char(1)|Y|
|percnt|numeric(3,2)|Y|
|lvcrdt|numeric(5,2)|Y|
|percntcash|numeric(3,2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|forconv|numeric(5,2)|Y|
|payitem2|varchar(3)|Y|
|moaccrual|numeric(5,2)|Y|

Indexes: `leaves_x` PK (company,emp_id,lvcode)

### leavetran  (4,133 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|payitem|varchar(3)||
|frdate|datetime||
|todate|datetime||
|datefiled|datetime|Y|
|reason|varchar(50)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|allowadv|char(1)|Y|
|payitem2|varchar(3)|Y|
|affectpa|char(1)|Y|

Indexes: `PK_leavetran` PK (company,emp_id,payitem,frdate,todate)

### loans  (2,611 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|payitem|varchar(3)||
|refno|varchar(15)||
|loanamt|numeric(9,2)|Y|
|no_of_pay|int|Y|
|payded|numeric(9,2)|Y|
|dateapprov|datetime||
|datefpay|datetime|Y|
|datelpay|datetime|Y|
|totalpaid|numeric(9,2)|Y|
|no_paid|int|Y|
|freq|char(1)|Y|
|loantype|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|pctint|numeric(7,6)|Y|
|intpaid|numeric(9,2)|Y|
|remarks|varchar(60)|Y|
|docno|varchar(10)||
|intamt|numeric(9,2)|Y|
|totalpaidi|numeric(9,2)|Y|

Indexes: `PK_loans` PK (company,emp_id,payitem,refno,dateapprov)

### medical  (0 rows)

|Column|Type|Null|
|---|---|---|
|emp_id|char(6)||
|company|char(3)||
|findings|char(100)|Y|
|changedate|datetime|Y|
|changeby|char(10)|Y|
|remarks|char(50)|Y|
|follow_up_date|datetime|Y|
|medication|char(100)|Y|
|chktype|char(50)|Y|
|illtype|char(50)|Y|
|severity|char(50)|Y|
|medcat|char(50)|Y|
|chkdate|datetime||
|chktype_cd|char(5)|Y|
|illtype_cd|char(5)|Y|
|medcat_cd|char(5)|Y|
|severity_cd|char(5)|Y|

### multi_hiredresgnd_dt  (497 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|datehired|datetime||
|dateresgnd|datetime|Y|
|reasonresg|varchar(100)|Y|
|changedate|datetime|Y|
|changeby|varchar(10)|Y|
|empsts|varchar(1)|Y|
|contractdue|datetime|Y|
|noofyears|numeric(5,2)|Y|

Indexes: `pk_multi_hiredresgnd_dt` PK (emp_id,datehired)

### optionsx  (595 rows)

|Column|Type|Null|
|---|---|---|
|appname|varchar(2)||
|menuname|varchar(30)||
|optioname|varchar(60)||
|menulevel|int|Y|
|optype|varchar(1)|Y|
|secured|char(1)|Y|
|usecount|numeric(9,0)|Y|
|dateused|datetime|Y|

Indexes: `PK_optionsx` PK (appname,menuname,optioname)

### otrates  (236 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|otcode|varchar(3)||
|payitem|varchar(3)||
|otrate|numeric(5,3)|Y|
|nprate|numeric(5,3)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `PK_otrates` PK (company,otcode,payitem)

### pa_exception  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|char(3)||
|emp_id|char(6)||
|trdate|datetime||
|reason|char(30)|Y|
|changeby|char(10)|Y|
|changedate|datetime|Y|

Indexes: `pa_exception_x` PK (company,emp_id,trdate)

### padatexc  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|padatex|datetime||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `padatexc_x` PK (company,padatex)

### payattend  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|hourswork|numeric(5,2)|Y|
|absent|numeric(5,2)|Y|
|undertime|numeric(5,2)|Y|
|regot|numeric(5,2)|Y|
|regotnp|numeric(5,2)|Y|
|sunot|numeric(5,2)|Y|
|sunotnp|numeric(5,2)|Y|
|sunotx|numeric(5,2)|Y|
|sunotxnp|numeric(5,2)|Y|
|leghot|numeric(5,2)|Y|
|leghotnp|numeric(5,2)|Y|
|leghxot|numeric(5,2)|Y|
|leghxotnp|numeric(5,2)|Y|
|leghsot|numeric(5,2)|Y|
|leghsotnp|numeric(5,2)|Y|
|leghsotx|numeric(5,2)|Y|
|leghsotxnp|numeric(5,2)|Y|
|splhot|numeric(5,2)|Y|
|splhotnp|numeric(5,2)|Y|
|splhxot|numeric(5,2)|Y|
|splhxotnp|numeric(5,2)|Y|
|splhsot|numeric(5,2)|Y|
|splhsotnp|numeric(5,2)|Y|
|splhsotx|numeric(5,2)|Y|
|splhsotxnp|numeric(5,2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `payattend_x` PK (company,emp_id)

### paydates  (40,666 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|paygroup|char(1)||
|trdate|datetime||
|hflag|char(1)|Y|

Indexes: `paydates_x` PK (company,paygroup,trdate)

### payexcept  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payyear|numeric(4,0)||
|paymonth|numeric(2,0)||
|payperiod|char(1)||
|emp_id|varchar(6)||
|remarks|varchar(50)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `payexcept_pk` PK (company,payyear,paymonth,payperiod,emp_id)

### paygroupsc  (150 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|userid|varchar(10)||
|paygroup|varchar(10)||
|rateautho|char(1)|Y|
|trentry|char(1)|Y|
|paycalc|char(1)|Y|
|empdata|char(1)|Y|

Indexes: `paygroupsc_x` PK (company,userid,paygroup)

### payitem  (618 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payitem|varchar(3)||
|descrip|varchar(30)|Y|
|category|char(1)|Y|
|sysgen|char(1)|Y|
|unmsr|char(1)|Y|
|mult|numeric(5,3)|Y|
|multm|numeric(5,3)|Y|
|nitepremd|numeric(5,3)|Y|
|niteprem|numeric(5,3)|Y|
|b4tax|char(1)|Y|
|priority|numeric(1,0)|Y|
|profitctr|varchar(15)|Y|
|acctno|varchar(15)|Y|
|dbcr|char(1)|Y|
|timrel|char(1)|Y|
|freq|char(1)|Y|
|trnallw|char(1)|Y|
|userseq|tinyint|Y|
|payregseq|tinyint|Y|
|xmult|numeric(5,3)|Y|
|xmultm|numeric(5,3)|Y|
|otratee3|numeric(5,3)|Y|
|otratee4|numeric(5,3)|Y|
|npratee3|numeric(5,3)|Y|
|npratee4|numeric(5,3)|Y|
|profitctr2|varchar(15)|Y|
|acctno2|varchar(15)|Y|
|dbcr2|char(1)|Y|
|glgroup|char(1)|Y|
|autogive|char(1)|Y|
|xdayscash|numeric(3,0)|Y|
|pcntcash|numeric(3,2)|Y|
|forfeitbal|char(1)|Y|
|nodays|numeric(4,2)|Y|
|mocredit|char(1)|Y|
|affectpa|char(1)|Y|
|entity|char(1)|Y|
|loantype|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|shortdesc|varchar(5)|Y|
|nontaxdays|numeric(3,0)|Y|
|payitem2|varchar(3)|Y|
|sssphhdmf|char(1)|Y|
|taxscheme|char(1)|Y|
|nontaxamt|numeric(9,2)|Y|
|dedfinalpy|char(1)|Y|
|incinbir|char(1)|Y|
|birclass|char(1)|Y|
|splpayout|char(1)|Y|
|affectdmnm|char(1)|Y|
|partofbasic|char(1)|Y|
|paytype|char(1)|Y|
|prorateatt|char(1)|Y|
|payleave|char(1)|Y|
|payrd|char(1)|Y|
|paysh|char(1)|Y|
|paylh|char(1)|Y|
|formwe|char(1)|Y|
|dedonbonus|varchar(1)|Y|
|dedonbopct|decimal(5,4)|Y|
|loanpayitm|varchar(3)|Y|

Indexes: `payitem_x` PK (company,payitem)

### payperiod  (1,086 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payyear|numeric(4,0)||
|paymonth|numeric(2,0)||
|payperiod|char(1)||
|paygrp|varchar(3)||
|fromdate|datetime|Y|
|todate|datetime|Y|
|maxday|numeric(5,2)|Y|
|maxhr|numeric(5,2)|Y|
|runmod|char(1)|Y|
|gensts|char(1)|Y|
|permnt|char(1)|Y|
|tfrent|char(1)|Y|
|emptrm|char(1)|Y|
|lvent|char(1)|Y|
|lvrent|char(1)|Y|
|paytent|char(1)|Y|
|paycalc|char(1)|Y|
|register|char(1)|Y|
|payslip|char(1)|Y|
|appded|char(1)|Y|
|unappded|char(1)|Y|
|bankrep|char(1)|Y|
|payclose|char(1)|Y|
|taxtable|char(1)|Y|
|empcount|numeric(7,0)|Y|
|salarysum|numeric(11,2)|Y|
|lastpay|char(1)|Y|
|seqno|int||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|taxrefund|char(1)|Y|
|pa|char(1)|Y|
|vlconv|char(1)|Y|
|slconv|char(1)|Y|
|mo13|char(1)|Y|
|effdate|datetime|Y|
|cpy2nxtprd|char(1)|Y|
|rtype|char(1)|Y|
|incrate|decimal(5,4)|Y|
|donotusedq|char(1)|Y|
|attposted|char(1)|Y|
|rpstattreq|char(1)|Y|
|prtwrksht|char(1)|Y|

Indexes: `payperiod_x` PK (company,payyear,paymonth,payperiod,paygrp,seqno)

### payroll  (491 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|paycenter|varchar(3)|Y|
|salary|numeric(9,2)|Y|
|oteligible|char(1)|Y|
|paytype|char(1)|Y|
|paymode|char(1)|Y|
|lastpay|datetime|Y|
|baseday|numeric(4,2)|Y|
|paygroup|varchar(3)|Y|
|bankcode|varchar(5)|Y|
|bankacct|varchar(20)|Y|
|prevgross|numeric(9,2)|Y|
|onhold|char(1)|Y|
|onholdby|varchar(10)|Y|
|onholddate|datetime|Y|
|onholdreas|varchar(50)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|fixtax|char(1)|Y|
|pcttax|decimal(4,4)|Y|
|emailpslip|char(1)|Y|
|emailadd|varchar(100)|Y|
|prevsalary|numeric(9,2)|Y|
|mintakepay|numeric(3,2)|Y|
|lastviewby|varchar(10)|Y|
|lastviewdt|datetime|Y|
|mosal|numeric(9,2)|Y|
|bankacct_old|varchar(20)|Y|
|bankcode_old|varchar(5)|Y|
|opt13thmo|char(1)|Y|
|attreq|varchar(1)|Y|
|autoout|varchar(1)|Y|

Indexes: `payroll_x` PK (company,emp_id)

### payrollemp  (265 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|paycenter|varchar(3)|Y|
|salary|numeric(9,2)|Y|
|comprule|varchar(3)|Y|
|oteligible|char(1)|Y|
|paytype|char(1)|Y|
|paymode|char(1)|Y|
|baseday|numeric(4,2)|Y|
|paygroup|varchar(3)|Y|
|bankcode|varchar(5)|Y|
|bankacct|varchar(20)|Y|
|grosspay|numeric(9,2)|Y|
|grossded|numeric(9,2)|Y|
|netpay|numeric(9,2)|Y|
|hourlyrate|numeric(13,8)|Y|
|dailyrate|numeric(13,8)|Y|
|exemptcode|varchar(6)|Y|
|hdmfmbr|char(1)|Y|
|coopmbr|char(1)|Y|
|division|varchar(4)|Y|
|dept|varchar(6)|Y|
|section|varchar(4)|Y|
|sssno|varchar(15)|Y|
|hdmfno|varchar(15)|Y|
|prevgross|numeric(9,2)|Y|
|rtype|char(1)||
|otcode|varchar(3)|Y|
|phealthno|varchar(15)|Y|
|datehired|datetime|Y|
|fixtax|char(1)|Y|
|pcttax|decimal(4,4)|Y|
|attfrdate|datetime|Y|
|atttodate|datetime|Y|
|deminimis|numeric(9,2)|Y|
|hourlyrate2|numeric(13,8)|Y|
|dailyrate2|numeric(13,8)|Y|
|mwe|char(1)|Y|
|opt13thmo|char(1)|Y|
|salary2|numeric(9,2)|Y|

Indexes: `payrollemp_x` PK (company,emp_id,rtype)

### payrollemp_recalc  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|paygroup|varchar(3)|Y|
|grosspay|numeric(9,2)|Y|
|grossded|numeric(9,2)|Y|
|paymode|char(1)|Y|

Indexes: `payrollemp_recalc_x` PK (company,emp_id)

### paytran  (652 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|payitem|varchar(3)||
|paycat|char(1)|Y|
|trhours|numeric(5,2)|Y|
|trminutes|numeric(2,0)|Y|
|trdays|numeric(5,2)|Y|
|tramount|numeric(9,2)|Y|
|trdate1|datetime||
|trdate2|datetime|Y|
|refno|varchar(10)||
|trunit|char(1)|Y|
|nphours|numeric(5,2)|Y|
|otmealallw|numeric(7,2)|Y|
|source|char(1)|Y|
|paygroup|char(3)|Y|
|rtype|char(1)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|remarks|char(50)|Y|
|incdq|char(1)|Y|
|oincdq|char(1)|Y|
|dqchgby|varchar(10)|Y|
|dqchgdt|datetime|Y|
|salary|numeric(9,2)|Y|
|paytype|char(1)|Y|
|salary2|numeric(9,2)|Y|

Indexes: `paytran_x` PK (company,emp_id,payitem,trdate1,refno,rtype)

### paytrana  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payitem|varchar(6)||
|paycat|char(1)|Y|
|trhours|decimal(5,2)|Y|
|trminutes|decimal(2,0)|Y|
|trdays|decimal(7,2)|Y|
|tramount|decimal(9,2)|Y|
|trdate1|datetime|Y|
|trdate2|datetime|Y|
|refno|varchar(10)|Y|
|trunit|char(1)|Y|
|paygroup|varchar(3)||
|rtype|char(1)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `PK_paytrana` PK (company,payitem,paygroup,rtype)

### paytranb  (6 rows)

|Column|Type|Null|
|---|---|---|
|company|char(3)||
|emp_id|char(6)||
|payitem|char(3)|Y|
|paycat|char(1)|Y|
|tramount|decimal(9,2)|Y|
|trdate1|datetime|Y|
|paygroup|char(3)|Y|
|recno|decimal(7,0)||
|changeby|char(10)|Y|
|changedate|datetime|Y|
|rtype|char(1)|Y|

Indexes: `PK_paytranb` PK (company,emp_id,recno)

### paytranc  (2,257 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)|Y|
|entrytype|char(1)|Y|
|payitem|varchar(3)|Y|
|paycat|char(1)|Y|
|trhours|numeric(5,2)|Y|
|trminutes|numeric(2,0)|Y|
|trdays|numeric(5,2)|Y|
|tramount|numeric(9,2)|Y|
|trdate1|datetime|Y|
|trdate2|datetime|Y|
|acctno|varchar(15)|Y|
|refno|varchar(15)|Y|
|trunit|char(1)|Y|
|trqty|numeric(9,2)|Y|
|trsource|char(1)|Y|
|paygroup|varchar(3)||
|priority|numeric(1,0)|Y|
|recno|numeric(7,0)||
|b4tax|char(1)|Y|
|unappded|numeric(9,2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|profitctr|varchar(15)|Y|
|premamt|numeric(9,2)|Y|
|rtype|char(1)||
|remarks|char(50)|Y|
|sssphhdmf|char(1)|Y|
|taxscheme|char(1)|Y|
|origamt|numeric(9,2)|Y|
|payyear|numeric(4,0)|Y|
|paymonth|numeric(2,0)|Y|
|payperiod|char(1)|Y|
|mwe|char(1)|Y|
|incinbir|char(1)|Y|
|birclass|char(1)|Y|
|repyear|numeric(4,0)|Y|
|repmonth|numeric(2,0)|Y|
|repperiod|char(1)|Y|

Indexes: `paytranc_x` PK (company,paygroup,recno,rtype)

### paytrancytd  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|paygroup|varchar(3)||
|emp_id|varchar(6)||
|payitem|varchar(3)||
|tramount|numeric(11,2)|Y|
|rtype|char(1)||

Indexes: `paytrancytd_x` PK (company,paygroup,emp_id,payitem,rtype)

### paytrand  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|payitem|varchar(3)||
|paycat|char(1)|Y|
|trhours|decimal(5,2)|Y|
|trminutes|decimal(2,0)|Y|
|trdays|decimal(5,2)|Y|
|tramount|decimal(9,2)|Y|
|trdate1|datetime||
|trdate2|datetime|Y|
|refno|varchar(10)||
|trunit|char(1)|Y|
|nphours|decimal(5,2)|Y|
|otmealallw|decimal(7,2)|Y|
|source|char(1)|Y|
|paygroup|char(3)|Y|
|rtype|char(1)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|remarks|char(50)|Y|
|procflg|char(1)|Y|

Indexes: `paytrand_x` PK (company,emp_id,payitem,trdate1,refno,rtype)

### paytranh  (352,719 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|payyear|numeric(4,0)||
|paymonth|numeric(2,0)||
|payperiod|char(1)||
|emp_id|varchar(6)|Y|
|payitem|varchar(3)|Y|
|paycat|char(1)|Y|
|trhours|numeric(5,2)|Y|
|trminutes|numeric(2,0)|Y|
|trdays|numeric(5,2)|Y|
|tramount|numeric(9,2)|Y|
|trdate1|datetime|Y|
|trdate2|datetime|Y|
|refno|varchar(15)|Y|
|trunit|char(1)|Y|
|trqty|numeric(9,2)|Y|
|paygroup|varchar(3)||
|priority|numeric(1,0)|Y|
|recno|numeric(7,0)||
|b4tax|char(1)|Y|
|premamt|numeric(9,2)|Y|
|seqno|int||
|rtype|char(1)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|sssphhdmf|char(1)|Y|
|taxscheme|char(1)|Y|
|incinbir|char(1)|Y|
|mwe|char(1)|Y|
|birclass|char(1)|Y|
|repyear|numeric(4,0)|Y|
|repmonth|numeric(2,0)|Y|
|repperiod|char(1)|Y|

Indexes: `paytranh_x` PK (company,payyear,paymonth,payperiod,paygroup,recno,seqno,rtype)

### pbcatcol  (0 rows)

|Column|Type|Null|
|---|---|---|
|pbc_tnam|char(129)||
|pbc_tid|int|Y|
|pbc_ownr|char(129)||
|pbc_cnam|char(129)||
|pbc_cid|smallint|Y|
|pbc_labl|varchar(254)|Y|
|pbc_lpos|smallint|Y|
|pbc_hdr|varchar(254)|Y|
|pbc_hpos|smallint|Y|
|pbc_jtfy|smallint|Y|
|pbc_mask|varchar(31)|Y|
|pbc_case|smallint|Y|
|pbc_hght|smallint|Y|
|pbc_wdth|smallint|Y|
|pbc_ptrn|varchar(31)|Y|
|pbc_bmap|char(1)|Y|
|pbc_init|varchar(254)|Y|
|pbc_cmnt|varchar(254)|Y|
|pbc_edit|varchar(31)|Y|
|pbc_tag|varchar(254)|Y|

Indexes: `pbcatc_x` UQ (pbc_tnam,pbc_ownr,pbc_cnam)

### pbcatedt  (21 rows)

|Column|Type|Null|
|---|---|---|
|pbe_name|varchar(30)||
|pbe_edit|varchar(254)|Y|
|pbe_type|smallint|Y|
|pbe_cntr|int|Y|
|pbe_seqn|smallint||
|pbe_flag|int|Y|
|pbe_work|char(32)|Y|

Indexes: `pbcate_x` UQ (pbe_name,pbe_seqn)

### pbcatfmt  (20 rows)

|Column|Type|Null|
|---|---|---|
|pbf_name|varchar(30)||
|pbf_frmt|varchar(254)|Y|
|pbf_type|smallint|Y|
|pbf_cntr|int|Y|

Indexes: `pbcatf_x` UQ (pbf_name)

### pbcattbl  (0 rows)

|Column|Type|Null|
|---|---|---|
|pbt_tnam|char(129)||
|pbt_tid|int|Y|
|pbt_ownr|char(129)||
|pbd_fhgt|smallint|Y|
|pbd_fwgt|smallint|Y|
|pbd_fitl|char(1)|Y|
|pbd_funl|char(1)|Y|
|pbd_fchr|smallint|Y|
|pbd_fptc|smallint|Y|
|pbd_ffce|char(18)|Y|
|pbh_fhgt|smallint|Y|
|pbh_fwgt|smallint|Y|
|pbh_fitl|char(1)|Y|
|pbh_funl|char(1)|Y|
|pbh_fchr|smallint|Y|
|pbh_fptc|smallint|Y|
|pbh_ffce|char(18)|Y|
|pbl_fhgt|smallint|Y|
|pbl_fwgt|smallint|Y|
|pbl_fitl|char(1)|Y|
|pbl_funl|char(1)|Y|
|pbl_fchr|smallint|Y|
|pbl_fptc|smallint|Y|
|pbl_ffce|char(18)|Y|
|pbt_cmnt|varchar(254)|Y|

Indexes: `pbcatt_x` UQ (pbt_tnam,pbt_ownr)

### pbcatvld  (0 rows)

|Column|Type|Null|
|---|---|---|
|pbv_name|varchar(30)||
|pbv_vald|varchar(254)|Y|
|pbv_type|smallint|Y|
|pbv_cntr|int|Y|
|pbv_msg|varchar(254)|Y|

Indexes: `pbcatv_x` UQ (pbv_name)

### perfectat1  (0 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|refdate|datetime|Y|
|trdate|datetime||
|daycount|numeric(5,0)|Y|
|lastdqdt|datetime|Y|
|lastdqreas|varchar(50)|Y|
|paygroup|char(3)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `perfectat1_x` PK (company,emp_id,trdate)

### personnel  (497 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|firstname|varchar(30)|Y|
|middlename|varchar(30)|Y|
|lastname|varchar(30)|Y|
|address|varchar(60)|Y|
|areacode|varchar(3)|Y|
|zipcode|varchar(6)|Y|
|telno|varchar(15)|Y|
|birthdate|datetime|Y|
|birthplace|varchar(20)|Y|
|sex|char(1)|Y|
|nationality|varchar(3)|Y|
|civilsts|char(1)|Y|
|religion|varchar(3)|Y|
|bloodtype|varchar(3)|Y|
|nospou|int|Y|
|no_of_dep|int|Y|
|contactper|varchar(35)|Y|
|contactrel|varchar(3)|Y|
|contactadd|varchar(60)|Y|
|sssno|varchar(15)|Y|
|tin|varchar(20)|Y|
|exemptcode|varchar(6)|Y|
|hdmfmbr|char(1)|Y|
|facility|varchar(3)|Y|
|division|varchar(4)|Y|
|dept|varchar(6)|Y|
|section|varchar(4)|Y|
|extno|varchar(4)|Y|
|reports_to|varchar(6)|Y|
|empsts|char(1)|Y|
|datehired|datetime|Y|
|prob_perd|int|Y|
|datereg|datetime|Y|
|jobcode|varchar(4)|Y|
|jobgrade|varchar(3)|Y|
|bankcode|varchar(5)|Y|
|bankacct|varchar(20)|Y|
|picturebmp|varchar(12)|Y|
|dateresgnd|datetime|Y|
|reasonresg|varchar(100)|Y|
|shift|char(2)|Y|
|coopmbr|char(1)|Y|
|lastpedate|datetime|Y|
|lastapdate|datetime|Y|
|swipe|char(1)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|changeby2|varchar(10)|Y|
|changedat2|datetime|Y|
|hdmfno|varchar(15)|Y|
|contacttel|varchar(15)|Y|
|exemptcode2|varchar(6)|Y|
|phealthno|varchar(15)|Y|
|cellphone|varchar(15)|Y|
|barangay|varchar(30)|Y|
|cleardate|datetime|Y|
|pinno|varchar(10)|Y|
|old_empid|varchar(6)|Y|
|address1|varchar(30)|Y|
|address2|varchar(30)|Y|
|addrcity|varchar(20)|Y|
|addrprov|varchar(20)|Y|
|contrperd|int|Y|
|contrenddt|datetime|Y|
|jobcat|varchar(4)|Y|
|logbox1|char(1)|Y|
|logbox2|char(1)|Y|
|logbox3|char(1)|Y|
|glcode|varchar(7)|Y|
|aclass|char(1)|Y|
|emppic|image|Y|
|prevcom|char(3)|Y|
|emppicext|varchar(3)|Y|
|flextime|char(1)|Y|
|curshift|char(2)|Y|
|confiagrok|char(1)|Y|
|birsched|char(1)|Y|
|hotlinenot|char(1)|Y|
|middlename2|varchar(30)|Y|
|lastname2|varchar(30)|Y|
|birsched2|char(1)|Y|
|birsched3|char(1)|Y|
|nogift|char(1)|Y|
|noofyears|numeric(5,2)|Y|
|oldhdmfno|varchar(15)|Y|
|hclass|varchar(2)|Y|
|logboxpc|varchar(1)|Y|
|erehire|char(1)|Y|
|filedcase|char(1)|Y|
|caseno|varchar(20)|Y|
|fbncoc|char(1)|Y|
|datehired_1st|datetime|Y|
|went2dole|char(1)|Y|
|leader|char(1)|Y|
|losdate|datetime|Y|
|jobcodedat|datetime|Y|
|age|int|Y|
|jobclass|char(1)|Y|
|fte|char(1)|Y|
|empsts2|char(1)|Y|

Indexes: `personnel_x` PK (company,emp_id)

### phtable  (32 rows)

|Column|Type|Null|
|---|---|---|
|frgross|money||
|togross|money|Y|
|salarybase|money|Y|
|mcrer|money|Y|
|mcree|money|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|bracket|decimal(3,0)|Y|

Indexes: `phtable_x` PK (frgross)

### policy  (1 rows)

|Column|Type|Null|
|---|---|---|
|ruleno|varchar(15)||
|infraction|varchar(512)|Y|
|sanction|decimal(1,0)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|r1|decimal(3,0)|Y|
|r2|decimal(3,0)|Y|
|r3|decimal(3,0)|Y|
|r4|decimal(3,0)|Y|
|sanction2|decimal(1,0)|Y|

Indexes: `policy_x` PK (ruleno)

### ratechange  (1,102 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|effdate|datetime||
|oldrate|numeric(9,2)|Y|
|newrate|numeric(9,2)|Y|
|crtperd|datetime|Y|
|allowdlt|char(1)|Y|
|modflg|char(1)|Y|
|reason|varchar(30)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|diffpay|char(1)|Y|
|oldpaytype|char(1)|Y|
|newpaytype|char(1)|Y|

Indexes: `ratechange_x` PK (company,emp_id,effdate)

### section  (19 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|division|varchar(4)||
|dept|varchar(6)||
|code|varchar(4)||
|descrip|varchar(30)|Y|
|head|varchar(6)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|dlabbudget|decimal(5,0)|Y|
|nlabbudget|decimal(5,0)|Y|
|areacd|varchar(4)|Y|
|groupcd|varchar(4)|Y|

Indexes: `section_x` PK (company,division,dept,code)

### shiftexcpt  (727 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|shift|char(2)||
|daycode|numeric(1,0)||
|keydate|datetime||
|timein|datetime|Y|
|breakout|datetime|Y|
|breakin|datetime|Y|
|timeout|datetime|Y|
|stdhours|numeric(4,2)|Y|
|stdot|numeric(4,2)|Y|
|allowtardy|numeric(3,0)|Y|
|flextime|char(1)|Y|
|brkhours|numeric(5,3)|Y|
|paidbrk|numeric(5,3)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|nonprodhrs|numeric(4,2)|Y|
|chg2dayoff|char(1)|Y|
|datereplcd|datetime|Y|
|cwwdoff|char(1)|Y|

Indexes: `shiftexcpt_x` PK (company,shift,keydate,daycode)

### shifttable  (154 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(10)||
|shift|char(2)||
|shiftdesc|varchar(30)|Y|
|timein|datetime|Y|
|breakout|datetime|Y|
|breakin|datetime|Y|
|timeout|datetime|Y|
|stdhours|numeric(4,2)|Y|
|stdot|numeric(4,2)|Y|
|dayoff|numeric(1,0)|Y|
|allowtardy|numeric(3,0)|Y|
|flextime|char(1)|Y|
|brkhours|numeric(5,3)|Y|
|paidbrk|numeric(5,3)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|nonprodhrs|numeric(4,2)|Y|
|shifttype|char(1)|Y|
|dayoff2|numeric(1,0)|Y|
|recid|char(1)|Y|

Indexes: `shifttable_x` PK (company,shift)

### ssstable  (51 rows)

|Column|Type|Null|
|---|---|---|
|frgross|numeric(7,2)||
|togross|numeric(9,2)||
|credit|numeric(7,2)|Y|
|ssser|numeric(7,2)|Y|
|mcrer|numeric(7,2)|Y|
|eccer|numeric(7,2)|Y|
|sssee|numeric(7,2)|Y|
|mcree|numeric(7,2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `ssstable_x` PK (frgross,togross)

### stdleaves  (56 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|lvcode|varchar(3)||
|noyears|numeric(2,0)||
|nodays|numeric(4,2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|jobcat|varchar(4)|Y|
|jobgrade|varchar(4)||

Indexes: `stdleaves_x` PK (company,lvcode,noyears,jobgrade)

### tablecode1  (1,063 rows)

|Column|Type|Null|
|---|---|---|
|tblcode|varchar(3)||
|fldcode|varchar(5)||
|descrip|varchar(50)|Y|
|vardata|varchar(30)|Y|
|reserved|char(1)|Y|
|applicat|varchar(2)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `tablecode1_x` PK (tblcode,fldcode)

### tablecode3  (0 rows)

|Column|Type|Null|
|---|---|---|
|tblcode|char(3)||
|fldcode|char(5)||
|min_score|numeric(5,0)|Y|
|max_score|numeric(5,0)|Y|
|rating|char(20)|Y|
|changeby|char(10)|Y|
|changedate|datetime|Y|

### taxtable  (96 rows)

|Column|Type|Null|
|---|---|---|
|xtype|char(1)||
|xunit|varchar(6)||
|xdesc|varchar(30)|Y|
|seqno|int|Y|
|range01|numeric(9,2)||
|range02|numeric(9,2)||
|range03|numeric(9,2)||
|range04|numeric(9,2)||
|range05|numeric(9,2)||
|range06|numeric(9,2)||
|range07|numeric(9,2)||
|range08|numeric(9,2)||
|range09|numeric(9,2)||
|range10|numeric(9,2)||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|exemption|numeric(7,0)|Y|

Indexes: `taxtable_x` PK (xtype,xunit)

### timecard  (387,859 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|trdate|datetime||
|daycd|char(1)|Y|
|stdhours|numeric(4,2)|Y|
|shift|char(2)|Y|
|dayoff|char(1)|Y|
|timein1|numeric(4,0)|Y|
|timeout1|numeric(4,0)|Y|
|timein2|numeric(4,0)|Y|
|timeout2|numeric(4,0)|Y|
|timein3|numeric(4,0)|Y|
|timeout3|numeric(4,0)|Y|
|timein4|numeric(4,0)|Y|
|timeout4|numeric(4,0)|Y|
|tlhours|numeric(4,2)|Y|
|tardy|numeric(4,0)|Y|
|undertime|numeric(4,2)|Y|
|reghrs|numeric(4,2)|Y|
|othrs|numeric(4,2)|Y|
|xothrs|numeric(4,2)|Y|
|nphrs|numeric(4,2)|Y|
|onphrs|numeric(4,2)|Y|
|xonphrs|numeric(4,2)|Y|
|stdtimein|varchar(5)|Y|
|stdbrkout|varchar(5)|Y|
|stdbrkin|varchar(5)|Y|
|stdtimeout|varchar(5)|Y|
|tardyitm|varchar(3)|Y|
|approvot|char(1)|Y|
|approvotby|varchar(10)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|procflg|char(1)|Y|
|payitem1|varchar(3)|Y|
|payitem2|varchar(3)|Y|
|hrday1|decimal(4,2)|Y|
|unmsr1|char(1)|Y|
|hrday2|decimal(4,2)|Y|
|unmsr2|char(1)|Y|
|section|varchar(4)|Y|
|lvprocflg|char(1)|Y|
|chargedhrs|numeric(4,2)|Y|
|approvut|char(1)|Y|
|recalcflg|char(1)|Y|
|secrhchgto|varchar(4)|Y|
|nofrhchgto|numeric(4,2)|Y|
|advvl|char(1)|Y|
|empsts|char(1)|Y|
|glcode|varchar(7)|Y|
|jobcode|varchar(4)|Y|
|osection|varchar(4)|Y|
|cwwdoff|varchar(1)|Y|
|ahrschg2lv|numeric(4,2)|Y|
|trfiled|char(1)|Y|
|tardyot|numeric(4,0)|Y|
|tardyaut|char(1)|Y|
|ctohrs|numeric(4,2)|Y|
|ctoearned|numeric(4,2)|Y|
|ctousedpst|numeric(4,2)|Y|
|ctousedunp|numeric(4,2)|Y|
|expirydate|datetime|Y|
|tchg2ctolv|numeric(4,2)|Y|
|uchg2ctolv|numeric(4,2)|Y|
|tardychg2cto|numeric(4,2)|Y|
|undchg2cto|numeric(4,2)|Y|
|inoutchgby|varchar(10)|Y|
|inoutchgdt|datetime|Y|
|kyear|numeric(4,0)|Y|
|kmonth|numeric(2,0)|Y|
|kww|numeric(2,0)|Y|
|areacd|varchar(4)|Y|
|groupcd|varchar(4)|Y|
|othrsbud|numeric(5,3)|Y|
|paygroup|varchar(3)|Y|
|areacd_ot|varchar(4)|Y|
|groupcd_ot|varchar(4)|Y|
|changeby2|varchar(10)|Y|
|changedate2|datetime|Y|
|nonprodhrs|numeric(4,2)|Y|
|upd2as400|char(1)|Y|
|tardy2|numeric(4,2)|Y|
|nocto|char(1)|Y|
|jobclass|char(1)|Y|
|cola|numeric(7,2)|Y|
|payitem3|varchar(3)|Y|
|timein1o|numeric(4,0)|Y|
|timeout1o|numeric(4,0)|Y|
|timein2o|numeric(4,0)|Y|
|timeout2o|numeric(4,0)|Y|
|timein3o|numeric(4,0)|Y|
|timeout3o|numeric(4,0)|Y|
|timein4o|numeric(4,0)|Y|
|timeout4o|numeric(4,0)|Y|
|autoout|varchar(1)|Y|
|autooutno|numeric(1,0)|Y|
|runsheetno|varchar(12)|Y|

Indexes: `timecard_x` PK (company,emp_id,trdate)

### timecardtm  (1,060 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|trdate|datetime||
|seqno|numeric(1,0)||
|rtype|varchar(1)||
|daycd|char(1)|Y|
|stdhours|decimal(4,2)|Y|
|shift|char(2)|Y|
|dayoff|char(1)|Y|
|tlhours|decimal(4,2)|Y|
|tardy|decimal(4,0)|Y|
|undertime|decimal(4,2)|Y|
|reghrs|decimal(4,2)|Y|
|holhrs|decimal(4,2)|Y|
|othrs|decimal(4,2)|Y|
|nphrs|decimal(4,2)|Y|
|tardyitm|varchar(3)|Y|
|approvot|char(1)|Y|
|approvotby|varchar(10)|Y|
|paygroup|char(1)|Y|
|regot|decimal(4,2)|Y|
|sunot|decimal(4,2)|Y|
|sunotx|decimal(4,2)|Y|
|splot|decimal(4,2)|Y|
|splotx|decimal(4,2)|Y|
|splotsun|decimal(4,2)|Y|
|splotsunx|decimal(4,2)|Y|
|legot|decimal(4,2)|Y|
|legotx|decimal(4,2)|Y|
|legotsun|decimal(4,2)|Y|
|legotsunx|decimal(4,2)|Y|
|regnp|decimal(4,2)|Y|
|sunnp|decimal(4,2)|Y|
|sunnpx|decimal(4,2)|Y|
|splnp|decimal(4,2)|Y|
|splnpx|decimal(4,2)|Y|
|splnpsun|decimal(4,2)|Y|
|splnpsunx|decimal(4,2)|Y|
|legnp|decimal(4,2)|Y|
|legnpx|decimal(4,2)|Y|
|legnpsun|decimal(4,2)|Y|
|legnpsunx|decimal(4,2)|Y|
|absent|decimal(4,2)|Y|
|vlchg|decimal(4,2)|Y|
|splhrs|decimal(4,2)|Y|
|holhrs2|decimal(4,2)|Y|
|payitem1|varchar(3)|Y|
|advvl|char(1)|Y|
|payitem2|varchar(3)|Y|
|cwwdoffhrs|numeric(4,2)|Y|
|cwwdoff|varchar(1)|Y|
|ahrschg2lv|numeric(4,2)|Y|
|trfiled|char(1)|Y|
|salary|numeric(9,2)|Y|
|paytype|char(1)|Y|
|tardy2|numeric(4,2)|Y|
|tardychgto|varchar(3)|Y|
|underchgto|varchar(3)|Y|
|cola|numeric(7,2)|Y|
|payitem3|varchar(3)|Y|

Indexes: `PK_timecardtm` PK (company,emp_id,trdate,seqno,rtype)

### timecardtr  (380,647 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|trdate|datetime||
|seqno|int||
|daycd|char(1)|Y|
|stdhours|numeric(4,2)|Y|
|shift|char(2)|Y|
|dayoff|char(1)|Y|
|cwwdoff|varchar(1)|Y|
|stdtimein|varchar(5)|Y|
|stdbrkout|varchar(5)|Y|
|stdbrkin|varchar(5)|Y|
|stdtimeout|varchar(5)|Y|
|timein1|numeric(4,0)|Y|
|timeout1|numeric(4,0)|Y|
|timein2|numeric(4,0)|Y|
|timeout2|numeric(4,0)|Y|
|timein3|numeric(4,0)|Y|
|timeout3|numeric(4,0)|Y|
|timein4|numeric(4,0)|Y|
|timeout4|numeric(4,0)|Y|
|othrs|numeric(4,2)|Y|
|approvot|char(1)|Y|
|source|varchar(1)|Y|
|createby|varchar(10)|Y|
|createdate|datetime|Y|

Indexes: `timecardtr_x` PK (company,emp_id,trdate,seqno)

### timeinout  (0 rows)

|Column|Type|Null|
|---|---|---|
|badge|numeric(8,0)||
|date_time|datetime||
|in_out|char(1)||
|updflg|char(1)|Y|
|changeby|char(10)|Y|
|changedate|datetime|Y|
|emp_id|char(6)|Y|
|cardno|varchar(14)||
|source|varchar(20)|Y|

Indexes: `timeinout_x` PK (badge,date_time,in_out,cardno)

### training  (3 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|inst|varchar(3)|Y|
|instdesc|varchar(90)|Y|
|course|varchar(3)|Y|
|coursedesc|varchar(90)|Y|
|fromdate|datetime|Y|
|todate|datetime|Y|
|compcd|varchar(30)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|
|tlhours|numeric(7,2)|Y|
|trntype|char(1)||
|seqno|numeric(3,0)||
|wrating1|numeric(5,2)|Y|
|wrating2|numeric(5,2)|Y|
|wrating3|numeric(5,2)|Y|
|prating1|numeric(5,2)|Y|
|prating2|numeric(5,2)|Y|
|prating3|numeric(5,2)|Y|
|nxtcrtdate|datetime|Y|
|trncode|char(1)|Y|

Indexes: `training_x` PK (company,emp_id,trntype,seqno)

### unappdedpp  (560 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|entrytype|char(1)|Y|
|payitem|varchar(3)|Y|
|paycat|char(1)|Y|
|trhours|numeric(5,2)|Y|
|trminutes|numeric(2,0)|Y|
|trdays|numeric(5,2)|Y|
|tramount|numeric(9,2)|Y|
|trdate1|datetime|Y|
|trdate2|datetime|Y|
|acctno|varchar(15)|Y|
|refno|varchar(15)|Y|
|trunit|char(1)|Y|
|trqty|numeric(9,2)|Y|
|trsource|char(1)|Y|
|paygroup|varchar(3)||
|priority|numeric(1,0)|Y|
|payyear|numeric(4,0)||
|paymonth|numeric(2,0)||
|payperiod|char(1)||
|recno|int||
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `PK_unappdedpp` PK (company,emp_id,paygroup,payyear,paymonth,payperiod,recno)

### users  (17 rows)

|Column|Type|Null|
|---|---|---|
|user_id|varchar(10)||
|password|varchar(20)||
|user_name|varchar(50)|Y|
|class|char(1)|Y|
|change_date|datetime|Y|
|lastsignon|datetime|Y|
|status|char(1)|Y|
|expint|int|Y|
|nvldsignon|tinyint|Y|
|signonsts|char(1)|Y|
|currentpgm|varchar(50)|Y|
|emp_id|varchar(6)|Y|
|maxearn|numeric(9,2)|Y|
|maxdedn|numeric(9,2)|Y|
|maxsign|numeric(2,0)|Y|
|minpwd|numeric(2,0)|Y|
|disabled|datetime|Y|
|pwdlchgd|datetime|Y|
|pwdxpired|char(1)|Y|

Indexes: `users_x` PK (user_id)

### workexp  (53 rows)

|Column|Type|Null|
|---|---|---|
|company|varchar(3)||
|emp_id|varchar(6)||
|fromdate|datetime||
|todate|datetime|Y|
|workexpcd|varchar(3)|Y|
|workexpdsc|varchar(30)|Y|
|prevcompnm|varchar(50)|Y|
|changeby|varchar(10)|Y|
|changedate|datetime|Y|

Indexes: `workexp_x` PK (company,emp_id,fromdate)

