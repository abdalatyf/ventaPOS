import React from 'react';
import { Link } from 'react-router-dom';
import { IconFileText, IconArrowRight } from '@tabler/icons-react';
import ReportAutocomplete from '../ReportAutocomplete';

export default function LedgerHeader({
  allProducts,
  productSearchQuery,
  setProductSearchQuery,
  handleSelectProduct
}) {
  return (
    <div className="card shadow-sm mb-3 border-0">
      <div className="card-body p-3">
        <div className="row g-2 align-items-center">
          <div className="col-md-3">
            <h2 className="mb-0 text-primary fw-bold fs-3 d-flex align-items-center">
              <IconFileText size={26} className="me-2" />
              كارت الصنف وسجل العمليات
            </h2>
            <div className="text-muted small mt-1">تتبع دورة حياة الصنف بالكامل من الإضافة لآخر حركة</div>
          </div>

          <div className="col-md-6">
            <div className="input-group">
              <span className="input-group-text bg-light fw-bold text-dark border-secondary-subtle">
                اختيار الصنف
              </span>
              <div style={{ flex: 1 }}>
                <ReportAutocomplete
                  items={allProducts}
                  value={productSearchQuery}
                  onChange={(text) => {
                    setProductSearchQuery(text);
                    if (!text) handleSelectProduct(null);
                  }}
                  onSelect={handleSelectProduct}
                  placeholder="ابحث بالاسم أو رقم الصنف..."
                  displayKey="name"
                  idKey="id"
                  searchKeys={['name', 'id']}
                  allowClear={true}
                  className="form-control fw-bold border-secondary-subtle"
                />
              </div>
            </div>
          </div>

          <div className="col-md-3 text-end">
            <Link to="/dimensions" className="btn btn-outline-secondary btn-sm">
              <IconArrowRight size={16} className="me-1" />
              الرجوع لقائمة البضاعة
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
