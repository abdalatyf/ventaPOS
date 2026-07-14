import React, { useState } from 'react';
import { IconBuildingStore, IconDeviceFloppy, IconReceiptTax } from '@tabler/icons-react';

export default function CompanyTab() {
  const [formData, setFormData] = useState({
    name: localStorage.getItem('company_name') || 'شركة النور والتطوير',
    description: 'مفروشات - ادوات منزلية - اجهزة كهربائية',
    phone1: '01114630467',
    phone2: '',
    footerText: 'رجاء الاحتفاظ بهذا الايصال'
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Save logic
    console.log('Saved company data', formData);
    alert('تم حفظ بيانات الشركة بنجاح');
  };

  const currentDate = new Date().toLocaleString('ar-EG', { dateStyle: 'short', timeStyle: 'short' });

  return (
    <div className="animate__animated animate__fadeIn">
      {/* Receipt Preview Section */}
      <div className="card shadow-sm border-0 mb-4 bg-light">
        <div className="card-header bg-white py-3 border-bottom-0 d-flex justify-content-between align-items-center">
          <h6 className="mb-0 fw-bold text-secondary"><IconReceiptTax className="me-2" /> معاينة شكل الإيصال الحراري</h6>
          <span className="badge bg-primary rounded-pill">تحديث مباشر</span>
        </div>
        <div className="card-body d-flex justify-content-center pt-2 pb-4">
          {/* Invoice Table Mockup */}
          <div className="bg-white p-3 shadow-sm border rounded" style={{ width: '100%', maxWidth: '600px', fontSize: '0.8rem' }}>
            <table className="table table-bordered table-sm mb-0 text-center align-middle" style={{ borderColor: '#444' }}>
              <tbody>
                <tr>
                  <td className="bg-light fw-bold" style={{ width: '15%' }}>رقم الوصل:</td>
                  <td className="fw-bold" style={{ width: '10%' }}>10045</td>
                  <td className="fw-bold bg-light" style={{ width: '5%' }}>1</td>
                  <td className="fw-bold fs-6 text-primary" style={{ width: '40%' }}>{formData.name || 'اسم المؤسسة'}</td>
                  <td className="bg-light fw-bold" style={{ width: '15%' }}>الإجمالي:</td>
                  <td className="fw-bold" style={{ width: '15%' }}>5000</td>
                </tr>
                <tr>
                  <td className="bg-light fw-bold">المنطقة:</td>
                  <td>المعادي</td>
                  <td className="fw-bold bg-light">12</td>
                  <td className="text-secondary" style={{ fontSize: '0.75rem' }}>{formData.description || 'وصف النشاط'}</td>
                  <td className="bg-light fw-bold">المقدم:</td>
                  <td className="fw-bold">1000</td>
                </tr>
                <tr>
                  <td className="bg-light fw-bold">اسم العميل:</td>
                  <td colSpan="3" className="text-start pe-2 fw-bold">أحمد محمد علي</td>
                  <td className="bg-light fw-bold" style={{ fontSize: '0.7rem' }}>الباقي بعد الإيصال:</td>
                  <td className="fw-bold text-danger">3500</td>
                </tr>
                <tr>
                  <td className="bg-light fw-bold">العنوان:</td>
                  <td colSpan="3" className="text-start pe-2">شارع 9 - المعادي</td>
                  <td className="bg-light fw-bold">هاتف:</td>
                  <td className="fw-bold">01012345678</td>
                </tr>
                <tr>
                  <td colSpan="4" className="text-center bg-light">
                    بموجب هذا الإيصال أتعهد بأن أدفع مبلغ <span className="border px-1 mx-1 fw-bold bg-white">500</span> (خمسمائة) جنيها فقط
                  </td>
                  <td className="bg-light fw-bold">تاريخ الدفع:</td>
                  <td>{currentDate}</td>
                </tr>
                <tr>
                  <td rowSpan="2" className="bg-light fw-bold">الصنف:</td>
                  <td colSpan="3" rowSpan="2">شاشة سامسونج 50 بوصة + ثلاجة شارب</td>
                  <td className="bg-light fw-bold">تاريخ البيع:</td>
                  <td>15/05/2026</td>
                </tr>
                <tr>
                  <td className="bg-light fw-bold">نظام القسط:</td>
                  <td>شهري</td>
                </tr>
                <tr>
                  <td className="bg-light fw-bold">المندوب:</td>
                  <td colSpan="2">محمود سعيد</td>
                  <td colSpan="3" className="text-center small bg-light text-primary">
                    {formData.footerText || '---'} | للإستعلام: <span dir="ltr">{formData.phone1 || '---'}</span>
                    {formData.phone2 ? ` - ${formData.phone2}` : ''}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Input Form Section */}
      <div className="card shadow-sm border-0 mb-4">
        <div className="card-header bg-white py-3">
          <h5 className="mb-0 fw-bold text-dark"><IconBuildingStore className="me-2 text-primary" /> تعديل بيانات المؤسسة</h5>
        </div>
        <div className="card-body bg-light">
          <form onSubmit={handleSubmit}>
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label fw-bold">اسم الشركة</label>
                <input type="text" className="form-control" name="name" value={formData.name} onChange={handleChange} required />
              </div>

              <div className="col-md-6">
                <label className="form-label fw-bold">وصف النشاط</label>
                <input type="text" className="form-control" name="description" value={formData.description} onChange={handleChange} />
              </div>

              <div className="col-md-6">
                <label className="form-label fw-bold">رقم الهاتف 1</label>
                <input type="text" className="form-control" name="phone1" value={formData.phone1} onChange={handleChange} required dir="ltr" />
              </div>

              <div className="col-md-6">
                <label className="form-label fw-bold">رقم الهاتف 2</label>
                <input type="text" className="form-control" name="phone2" value={formData.phone2} onChange={handleChange} dir="ltr" />
              </div>

              <div className="col-md-12">
                <label className="form-label fw-bold">نص ذيل الفاتورة (Footer)</label>
                <textarea className="form-control" name="footerText" rows="2" value={formData.footerText} onChange={handleChange}></textarea>
              </div>

              <div className="col-12 text-end border-top pt-3 mt-4">
                <button type="submit" className="btn btn-primary fw-bold px-4">
                  <IconDeviceFloppy className="me-2" /> حفظ التعديلات
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
