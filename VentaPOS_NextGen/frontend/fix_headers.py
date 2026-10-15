import os

file_path = r"D:\Projects\VentaPOS\VentaPOS_NextGen\frontend\src\pages\reports\InstallmentsReport.jsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_headers = """                  <th className="text-center w-1">#</th>
                  <th className="text-center">تاريخ القسط</th>
                  <th className="text-start px-2">العميل</th>
                  <th className="text-center">رقم الموبايل</th>
                  <th className="text-center">المنطقة</th>
                  <th className="text-center">المندوب</th>
                  <th className="text-center">رقم الفاتورة</th>
                  <th className="text-center">تاريخ البيع</th>
                  <th className="text-end px-2">قيمة القسط</th>"""

new_headers = """                  <th className="text-center w-1">#</th>
                  <th className="text-center text-nowrap">تاريخ القسط</th>
                  <th className="text-center text-nowrap">المندوب</th>
                  <th className="text-center text-nowrap">المنطقة</th>
                  <th className="text-center text-nowrap">رقم الفاتورة</th>
                  <th className="text-center text-nowrap">تاريخ البيع</th>
                  <th className="text-start px-2 w-100">اسم العميل</th>
                  <th className="text-center text-nowrap">رقم الموبايل</th>
                  <th className="text-end px-2 text-nowrap">المبلغ</th>"""

content = content.replace(old_headers, new_headers)

# Let's also check if the customer name cell has w-100 to fix stretching
old_row_cust = '<td className="text-start px-2 align-middle border-secondary-subtle fw-bold text-primary">\n        {payment.customer_name}\n      </td>'
new_row_cust = '<td className="text-start px-2 align-middle border-secondary-subtle fw-bold text-primary w-100">\n        {payment.customer_name}\n      </td>'
content = content.replace(old_row_cust, new_row_cust)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Headers replaced")
