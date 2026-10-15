import re
import os

file_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\reports\InstallmentsReport.jsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace InstallmentRow
old_row = """const InstallmentRow = React.memo(({ payment, index, isSelected, toggleSelect, navigate }) => {
  return (
    <tr>
      <td className="text-center align-middle border-secondary-subtle">
        <input 
          type="checkbox" 
          className="form-check-input border-secondary-subtle" 
          checked={isSelected}
          onChange={() => toggleSelect(payment.payment_id)}
        />
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold">{toArabic(index + 1)}</td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {(() => {
          const d = new Date(payment.date);
          return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
        })()}
      </td>
      <td className="text-start px-2 align-middle border-secondary-subtle fw-bold text-primary">
        {payment.customer_name}
      </td>
      <td className="text-center align-middle border-secondary-subtle text-muted" dir="ltr">{toArabic(payment.phone)}</td>
      <td className="text-center align-middle border-secondary-subtle">{payment.area}</td>
      <td className="text-center align-middle border-secondary-subtle fw-bold">{payment.salesperson_name}</td>
      <td className="text-center align-middle border-secondary-subtle">
        <a href="#" onClick={(e) => { e.preventDefault(); navigate(`/pos?edit=${payment.receipt_id}`); }} className="drilldown-link text-decoration-none fw-bold text-primary" dir="ltr">
          {toArabic(payment.receipt_num)}
        </a>
      </td>
      <td className="text-center align-middle border-secondary-subtle text-muted" dir="ltr">{toArabic(payment.sale_date)}</td>
      <td className="text-end px-2 align-middle border-secondary-subtle fw-bold text-success">
        {toArabic(fmtNum(payment.amount))}
      </td>
    </tr>
  );
});"""

new_row = """const InstallmentRow = React.memo(({ payment, index, isSelected, toggleSelect, navigate }) => {
  return (
    <tr>
      <td className="text-center align-middle border-secondary-subtle">
        <input 
          type="checkbox" 
          className="form-check-input border-secondary-subtle" 
          checked={isSelected}
          onChange={() => toggleSelect(payment.payment_id)}
        />
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold">{toArabic(index + 1)}</td>
      <td className="text-center align-middle border-secondary-subtle" dir="ltr">
        {(() => {
          const d = new Date(payment.date);
          const month = String(d.getMonth() + 1).padStart(2, '0');
          const year = d.getFullYear();
          return toArabic(`${month}/${year}`);
        })()}
      </td>
      <td className="text-center align-middle border-secondary-subtle fw-bold">{payment.salesperson_name}</td>
      <td className="text-center align-middle border-secondary-subtle">{payment.area}</td>
      <td className="text-center align-middle border-secondary-subtle">
        <a href="#" onClick={(e) => { e.preventDefault(); navigate(`/pos?edit=${payment.receipt_id}`); }} className="drilldown-link text-decoration-none fw-bold text-primary" dir="ltr">
          {toArabic(payment.receipt_num)}
        </a>
      </td>
      <td className="text-center align-middle border-secondary-subtle text-muted" dir="ltr">{toArabic(payment.sale_date)}</td>
      <td className="text-start px-2 align-middle border-secondary-subtle fw-bold text-primary">
        {payment.customer_name}
      </td>
      <td className="text-center align-middle border-secondary-subtle text-muted" dir="ltr">{toArabic(payment.phone)}</td>
      <td className="text-end px-2 align-middle border-secondary-subtle fw-bold text-success">
        {toArabic(fmtNum(payment.amount))}
      </td>
    </tr>
  );
});"""

content = content.replace(old_row, new_row)

# Replace thead
old_thead = """                  <th className="text-center w-1">#</th>
                  <th className="text-center">تاريخ القسط</th>
                  <th className="text-start px-2">العميل</th>
                  <th className="text-center">رقم الموبايل</th>
                  <th className="text-center">المنطقة</th>
                  <th className="text-center">المندوب</th>
                  <th className="text-center">رقم الفاتورة</th>
                  <th className="text-center">تاريخ البيع</th>
                  <th className="text-end px-2">قيمة القسط</th>"""

new_thead = """                  <th className="text-center w-1">#</th>
                  <th className="text-center">تاريخ القسط</th>
                  <th className="text-center">المندوب</th>
                  <th className="text-center">المنطقة</th>
                  <th className="text-center">رقم الفاتورة</th>
                  <th className="text-center">تاريخ البيع</th>
                  <th className="text-start px-2">اسم العميل</th>
                  <th className="text-center">رقم الموبايل</th>
                  <th className="text-end px-2">المبلغ</th>"""

content = content.replace(old_thead, new_thead)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Installments report modified successfully.")
