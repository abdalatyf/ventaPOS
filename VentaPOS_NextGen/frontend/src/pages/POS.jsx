import React from 'react';
import { Link } from 'react-router-dom';

const POS = () => {
  return (
    <div className="page-wrapper bg-dark text-white">
      <div className="page-header d-print-none mb-0 pb-3 border-bottom border-dark-subtle">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title text-white">
                شاشة الخزنة
              </h2>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <Link to="/" className="btn btn-dark border-secondary">
                إغلاق الخزنة
              </Link>
            </div>
          </div>
        </div>
      </div>
      <div className="page-body mt-0">
        <div className="container-fluid pt-3">
          <div className="row h-100">
            <div className="col-md-8">
              <div className="card bg-secondary text-white border-0 h-100 min-vh-100">
                <div className="card-body d-flex align-items-center justify-content-center">
                  <h3 className="text-white-50">قائمة البضاعة ستظهر هنا</h3>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card bg-secondary text-white border-0 h-100 min-vh-100">
                <div className="card-body d-flex align-items-center justify-content-center">
                  <h3 className="text-white-50">تفاصيل الحساب والنقدية ستظهر هنا</h3>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default POS;
