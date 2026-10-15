import re
import os

frontend_reports = r"D:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\reports"

# 1. ReportsLayout.jsx
layout_path = os.path.join(frontend_reports, "ReportsLayout.jsx")
with open(layout_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace states
content = re.sub(r'const \[startYear, setStartYear\] = useState\([^)]*\);\n\s*const \[startMonth, setStartMonth\] = useState\([^)]*\);\n\s*const \[endYear, setEndYear\] = useState\([^)]*\);\n\s*const \[endMonth, setEndMonth\] = useState\([^)]*\);', 
                 r"const [year, setYear] = useState('');\n  const [month, setMonth] = useState('');", content)

# Replace sync logic
old_sync = """  useEffect(() => {
    if (!dateLoading) {
      const searchParams = new URLSearchParams(location.search);
      const urlStartYear = searchParams.get('start_year');
      const urlStartMonth = searchParams.get('start_month');
      const urlEndYear = searchParams.get('end_year');
      const urlEndMonth = searchParams.get('end_month');
      
      if (urlStartYear && urlStartMonth && urlEndYear && urlEndMonth) {
        setStartYear(urlStartYear);
        setStartMonth(urlStartMonth);
        setEndYear(urlEndYear);
        setEndMonth(urlEndMonth);
      } else if (!startYear || !startMonth || !endYear || !endMonth) {
        // Fallback to single month default
        const urlYear = searchParams.get('year') || defaultYear;
        const urlMonth = searchParams.get('month') || defaultMonth;
        setStartYear(urlYear);
        setStartMonth(urlMonth);
        setEndYear(urlYear);
        setEndMonth(urlMonth);
      }
    }
  }, [dateLoading, defaultYear, defaultMonth, location.search]);"""
new_sync = """  useEffect(() => {
    if (!dateLoading) {
      const searchParams = new URLSearchParams(location.search);
      const urlYear = searchParams.get('year') || defaultYear;
      const urlMonth = searchParams.get('month') || defaultMonth;
      if (!year || !month) {
        setYear(urlYear);
        setMonth(urlMonth);
      }
    }
  }, [dateLoading, defaultYear, defaultMonth, location.search]);"""
content = content.replace(old_sync, new_sync)

# Replace URL update logic
old_url = """  useEffect(() => {
    if (startYear && startMonth && endYear && endMonth) {
      const searchParams = new URLSearchParams(location.search);
      searchParams.set('start_year', startYear);
      searchParams.set('start_month', startMonth);
      searchParams.set('end_year', endYear);
      searchParams.set('end_month', endMonth);
      
      // Keep legacy params for backend backward compatibility just in case
      searchParams.set('year', startYear);
      searchParams.set('month', startMonth);

      const newSearch = searchParams.toString();
      if (location.search !== `?${newSearch}`) {
        navigate(`${location.pathname}?${newSearch}`, { replace: true });
      }
    }
  }, [startYear, startMonth, endYear, endMonth, navigate, location.pathname, location.search]);"""
new_url = """  useEffect(() => {
    if (year && month) {
      const searchParams = new URLSearchParams(location.search);
      searchParams.set('year', year);
      searchParams.set('month', month);

      const newSearch = searchParams.toString();
      if (location.search !== `?${newSearch}`) {
        navigate(`${location.pathname}?${newSearch}`, { replace: true });
      }
    }
  }, [year, month, navigate, location.pathname, location.search]);"""
content = content.replace(old_url, new_url)

# Replace Loading check
content = re.sub(r'if \(dateLoading \|\| !startYear \|\| !startMonth \|\| !endYear \|\| !endMonth\) \{', r'if (dateLoading || !year || !month) {', content)

# Replace Context Provider
content = re.sub(r'<ReportsContext.Provider value={{ startYear, startMonth, endYear, endMonth, branchId }}>', r'<ReportsContext.Provider value={{ year, month, branchId }}>', content)

# Replace UI layout for ranges
old_ui = """                  {/* Date Range Inputs */}
                  <span className="text-muted small fw-bold ms-1">من:</span>
                  <input
                    type="number"
                    className="form-control form-control-sm fw-bold text-center"
                    min="1" max="12" placeholder="شهر"
                    value={startMonth} onChange={(e) => setStartMonth(e.target.value)}
                    style={{ width: '70px' }}
                  />
                  <input
                    type="number"
                    className="form-control form-control-sm fw-bold text-center"
                    min="2000" max="2100" placeholder="سنة"
                    value={startYear} onChange={(e) => setStartYear(e.target.value)}
                    style={{ width: '80px' }}
                  />
                  
                  <span className="text-muted small fw-bold ms-2 me-1">إلى:</span>
                  <input
                    type="number"
                    className="form-control form-control-sm fw-bold text-center"
                    min="1" max="12" placeholder="شهر"
                    value={endMonth} onChange={(e) => setEndMonth(e.target.value)}
                    style={{ width: '70px' }}
                  />
                  <input
                    type="number"
                    className="form-control form-control-sm fw-bold text-center"
                    min="2000" max="2100" placeholder="سنة"
                    value={endYear} onChange={(e) => setEndYear(e.target.value)}
                    style={{ width: '80px' }}
                  />"""
new_ui = """                  {/* Date Inputs */}
                  <span className="text-muted small fw-bold ms-1">شهر:</span>
                  <input
                    type="number"
                    className="form-control form-control-sm fw-bold text-center"
                    min="1" max="12" placeholder="شهر"
                    value={month} onChange={(e) => setMonth(e.target.value)}
                    style={{ width: '70px' }}
                  />
                  <span className="text-muted small fw-bold ms-1">سنة:</span>
                  <input
                    type="number"
                    className="form-control form-control-sm fw-bold text-center"
                    min="2000" max="2100" placeholder="سنة"
                    value={year} onChange={(e) => setYear(e.target.value)}
                    style={{ width: '80px' }}
                  />"""
content = content.replace(old_ui, new_ui)

with open(layout_path, "w", encoding="utf-8") as f:
    f.write(content)

# 2. Iterate over all other reports to revert startYear/startMonth to year/month
def replace_in_file(filename):
    path = os.path.join(frontend_reports, filename)
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    
    # Destructuring
    c = c.replace("const { startYear, startMonth, endYear, endMonth, branchId } = useContext(ReportsContext);", "const { year, month, branchId } = useContext(ReportsContext);")
    c = c.replace("const { startYear, startMonth, endYear, endMonth } = useContext(ReportsContext);", "const { year, month } = useContext(ReportsContext);")
    
    # Dependencies and conditions
    c = c.replace("startYear, startMonth, endYear, endMonth", "year, month")
    c = c.replace("!startYear || !startMonth || !endYear || !endMonth", "!year || !month")
    c = c.replace("startYear && startMonth && endYear && endMonth", "year && month")
    
    # API params (manual replacements where we changed it)
    c = c.replace("start_year: startYear,", "year: year,")
    c = c.replace("start_month: startMonth,", "month: month,")
    c = c.replace("end_year: endYear,", "")
    c = c.replace("end_month: endMonth,", "")
    c = c.replace("end_year: endYear", "")
    c = c.replace("end_month: endMonth", "")
    c = c.replace("start_year: startYear", "year: year")
    c = c.replace("start_month: startMonth", "month: month")
    
    c = c.replace("if (startMonth) params.append('start_month', startMonth);\n      if (endMonth) params.append('end_month', endMonth);", "if (month) params.append('month', month);")
    c = c.replace("if (startYear) params.append('start_year', startYear);\n      if (endYear) params.append('end_year', endYear);", "if (year) params.append('year', year);")

    # Links
    c = c.replace("start_year=${startYear}&start_month=${startMonth}&end_year=${endYear}&end_month=${endMonth}", "year=${year}&month=${month}")
    c = c.replace("{startMonth}/{startYear} - {endMonth}/{endYear}", "{month}/{year}")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)

for report in ["DashboardReport.jsx", "InventoryMovementReport.jsx", "ReceiptsReport.jsx", "InstallmentsReport.jsx", "CashDrawerReport.jsx", "SalespersonPerformanceReport.jsx", "ProfitAndLossReport.jsx"]:
    replace_in_file(report)

print("Frontend revert complete")
