import React from 'react';

const Login = () => {
  return (
    <div className="page page-center bg-light">
      <div className="container container-tight py-4">
        <div className="text-center mb-4">
          <h1 className="fw-bolder fs-1">Venta<span className="text-primary">POS</span></h1>
        </div>
        <div className="card shadow-sm border-0 rounded-4">
          <div className="card-body p-5">
            <h2 className="h3 text-center mb-4">تسجيل الدخول إلى النظام</h2>
            <form>
              <div className="mb-3">
                <label className="form-label">الإيميل</label>
                <input type="email" className="form-control form-control-lg" placeholder="admin@store.com" />
              </div>
              <div className="mb-4">
                <label className="form-label">كلمة السر</label>
                <input type="password" className="form-control form-control-lg" placeholder="أدخل كلمة المرور" />
              </div>
              <div className="form-footer">
                <button type="button" className="btn btn-primary w-100 btn-lg rounded-3">تسجيل الدخول</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
