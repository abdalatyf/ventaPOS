import re

file_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\reports\DashboardReport.jsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add import
import_code = "import { CardSkeleton, SkeletonLoader } from '../../components/SkeletonLoader';\n"
if "CardSkeleton" not in content:
    content = content.replace("import { fmtNum } from '../../utils/formatUtils';", "import { fmtNum } from '../../utils/formatUtils';\n" + import_code)

# Replace loading state
loading_old = """  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center h-100">
        <div className="spinner-border text-primary" role="status"></div>
        <div className="text-muted ms-3 fw-bold">جاري تجميع بيانات الملخص...</div>
      </div>
    );
  }"""

loading_new = """  if (loading) {
    return (
      <div className="container-fluid px-3 py-3">
        <div className="row row-cards mb-3">
          {[1, 2, 3, 4].map(i => (
            <div className="col-12 col-md-6 col-lg-3" key={i}>
              <CardSkeleton />
            </div>
          ))}
        </div>
        <div className="row row-cards">
          <div className="col-lg-6">
            <div className="card" style={{height: '300px'}}>
              <div className="card-body">
                <SkeletonLoader style={{width: '100%', height: '100%'}} />
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="card" style={{height: '300px'}}>
              <div className="card-body">
                <SkeletonLoader style={{width: '100%', height: '100%'}} />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }"""

content = content.replace(loading_old, loading_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied skeleton loader to DashboardReport.jsx")
