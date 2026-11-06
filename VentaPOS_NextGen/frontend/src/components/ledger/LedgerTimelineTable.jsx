import React from 'react';
import { 
  IconFilter, IconCash, IconCreditCard, IconAlertTriangle, IconClockHour4 
} from '@tabler/icons-react';
import { fmtNum } from '../../utils/formatUtils';

export default function LedgerTimelineTable({
  filteredTimeline,
  eventFilter,
  setEventFilter,
  monthlySummary
}) {
  const renderEventBadge = (ev) => {
    switch (ev.type) {
      case 'INITIAL':
        return <span className="badge bg-secondary text-white px-2 py-1">رصيد افتتاحي</span>;
      case 'PURCHASE':
        return (
          <span className="badge bg-success-subtle text-success border border-success-subtle px-2 py-1">
            فاتورة شراء
            {ev.is_price_change && <span className="ms-1 badge bg-warning text-dark py-0 px-1 font-monospace">سعر شراء جديد</span>}
          </span>
        );
      case 'RETURN':
        return <span className="badge bg-danger-subtle text-danger border border-danger-subtle px-2 py-1">مرتجع للمورد</span>;
      case 'SALE':
        return ev.is_cash_sale ? (
          <span className="badge bg-primary text-white px-2 py-1"><IconCash size={14} className="me-1 inline" />فاتورة بيع كاش</span>
        ) : (
          <span className="badge bg-info text-white px-2 py-1"><IconCreditCard size={14} className="me-1 inline" />فاتورة بيع قسط</span>
        );
      case 'SALE_RETURN':
        return <span className="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle px-2 py-1">مرتجع مبيعات عميل</span>;
      case 'DEFICIT':
        return <span className="badge bg-danger text-white px-2 py-1"><IconAlertTriangle size={14} className="me-1 inline" />تسوية عجز مخزن</span>;
      case 'COMMISSION_CHANGE':
        return <span className="badge bg-purple-subtle text-purple border border-purple-subtle px-2 py-1"><IconClockHour4 size={14} className="me-1 inline" />تعديل مندبة</span>;
      default:
        return <span className="badge bg-light text-dark">{ev.type}</span>;
    }
  };

  return (
    <>
      {/* Full Chronological Timeline Table */}
      <div className="card shadow-sm mb-3" style={{ border: '1px solid #dee2e6' }}>
        <div className="card-header bg-light py-2 d-flex justify-content-between align-items-center">
          <span className="fw-bold text-dark fs-4">
            سجل حياة الصنف من الإضافة لآخر عملية ({filteredTimeline.length} حركة)
          </span>

          {/* Event Type Filter */}
          <div className="d-flex align-items-center gap-1">
            <span className="text-muted small me-1"><IconFilter size={14} className="me-1 inline" />تصفية:</span>
            <select 
              className="form-select form-select-sm" 
              style={{ width: '150px' }}
              value={eventFilter} 
              onChange={(e) => setEventFilter(e.target.value)}
            >
              <option value="ALL">جميع الحركات</option>
              <option value="PURCHASES">المشتريات والمرتجع</option>
              <option value="SALES">المبيعات والمرتجع</option>
              <option value="DEFICITS">العجز المخزني</option>
              <option value="COMMISSIONS">تعديلات المندبة</option>
            </select>
          </div>
        </div>

        <div className="table-responsive" style={{ overflow: 'visible' }}>
          <table className="table table-vcenter table-bordered table-hover text-nowrap table-sticky-header tabular-nums mb-0">
            <thead className="bg-light">
              <tr>
                <th className="w-1 text-center align-middle">#</th>
                <th className="text-center align-middle" style={{ width: '100px' }}>التاريخ</th>
                <th className="text-center align-middle">العملية / الحركة</th>
                <th className="text-start px-2 align-middle">الطرف / البيان</th>
                <th className="text-center align-middle text-success">وارد (+)</th>
                <th className="text-center align-middle text-danger">منصرف (-)</th>
                <th className="text-center align-middle bg-light-subtle">الرصيد بعد العملية</th>
                <th className="text-center align-middle">سعر الوحدة / التكلفة</th>
                <th className="text-center align-middle">الأثر المالي (ربح / خسارة)</th>
              </tr>
            </thead>
            <tbody>
              {filteredTimeline.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center text-muted py-4">لا توجد حركات مسجلة لهذا الصنف</td>
                </tr>
              ) : (
                filteredTimeline.map((ev, idx) => {
                  const isInitial = ev.type === 'INITIAL';
                  const isPurchase = ev.type === 'PURCHASE';
                  const isReturn = ev.type === 'RETURN';
                  const isSale = ev.type === 'SALE';
                  const isSaleReturn = ev.type === 'SALE_RETURN';
                  const isDeficit = ev.type === 'DEFICIT';
                  const isCommission = ev.type === 'COMMISSION_CHANGE';

                  const incomingQty = (isInitial || isPurchase || isSaleReturn) ? ev.quantity : null;
                  const outgoingQty = (isReturn || isSale || isDeficit) ? ev.quantity : null;

                  let detailsText = ev.description || '-';
                  if (isPurchase || isReturn) {
                    detailsText = `فاتورة #${ev.invoice_number || '-'} — المورد: ${ev.supplier || '-'}`;
                  } else if (isSale || isSaleReturn) {
                    detailsText = `فاتورة #${ev.receipt_number || '-'} — العميل: ${ev.customer_name || '-'} (المندوب: ${ev.salesperson || '-'})`;
                  } else if (isDeficit) {
                    detailsText = `سبب العجز: ${ev.reason || 'عجز مخزن'}`;
                  }

                  return (
                    <tr key={idx} className={isDeficit ? 'table-danger-subtle' : (ev.is_price_change ? 'table-warning-subtle' : '')}>
                      <td className="text-center align-middle text-muted small">{idx + 1}</td>
                      <td className="text-center align-middle font-monospace fw-semibold">
                        {ev.year}/{String(ev.month).padStart(2, '0')}
                      </td>
                      <td className="text-center align-middle">
                        {renderEventBadge(ev)}
                      </td>
                      <td className="text-start px-2 align-middle text-wrap" style={{ maxWidth: '320px' }}>
                        <span className="small fw-semibold">{detailsText}</span>
                      </td>
                      <td className="text-center align-middle fw-bold text-success">
                        {incomingQty !== null ? `+${incomingQty}` : '-'}
                      </td>
                      <td className="text-center align-middle fw-bold text-danger">
                        {outgoingQty !== null ? `-${outgoingQty}` : '-'}
                      </td>
                      <td className="text-center align-middle bg-light-subtle">
                        <span className="badge bg-primary-subtle text-primary border border-primary-subtle fs-5 px-3 py-1 fw-bolder">
                          {ev.running_stock}
                        </span>
                      </td>
                      <td className="text-center align-middle">
                        {isInitial && <span className="small text-muted">شراء: {fmtNum(ev.price)} | مندبة: {fmtNum(ev.commission)}</span>}
                        {isPurchase && <span className="small fw-bold text-dark">{fmtNum(ev.price)} جنيه</span>}
                        {isReturn && <span className="small text-muted">{fmtNum(ev.price)} جنيه</span>}
                        {isSale && (
                          <span className="small">
                            بيع: <strong className="text-primary">{fmtNum(ev.price)}</strong> | تكلفة: <span className="text-muted">{fmtNum(ev.unit_cost)}</span>
                          </span>
                        )}
                        {isSaleReturn && (
                          <span className="small">
                            استرجاع: <strong className="text-warning">{fmtNum(ev.price)}</strong>
                          </span>
                        )}
                        {isDeficit && (
                          <span className="small text-danger">
                            تكلفة الوحدة: {fmtNum(ev.unit_cost)} جنيه
                          </span>
                        )}
                        {isCommission && (
                          <span className="small fw-bold text-purple" style={{ color: '#6f42c1' }}>
                            مندبة: {fmtNum(ev.commission_amount)} جنيه
                          </span>
                        )}
                      </td>
                      <td className="text-center align-middle fw-bold">
                        {(isSale || isSaleReturn) && (
                          <span className={ev.net_profit >= 0 ? 'text-success' : 'text-danger'}>
                            {ev.net_profit >= 0 ? `+${fmtNum(ev.net_profit)}` : fmtNum(ev.net_profit)}
                          </span>
                        )}
                        {isDeficit && (
                          <span className="text-danger fw-bolder">
                            - {fmtNum(ev.loss_amount)} (خسارة)
                          </span>
                        )}
                        {!isSale && !isSaleReturn && !isDeficit && (
                          <span className="text-muted small">-</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Monthly Movement Summary Table */}
      {monthlySummary.length > 0 && (
        <div className="card shadow-sm mb-4" style={{ border: '1px solid #dee2e6' }}>
          <div className="card-header bg-light py-2">
            <span className="fw-bold text-dark fs-5">ملخص الحركة الشهري للصنف ({monthlySummary.length} شهر)</span>
          </div>
          <div className="table-responsive" style={{ overflow: 'visible' }}>
            <table className="table table-vcenter table-bordered table-hover table-sm text-nowrap tabular-nums mb-0">
              <thead className="bg-light">
                <tr>
                  <th className="text-center align-middle">الشهر</th>
                  <th className="text-center align-middle text-success">إجمالي الوارد (+)</th>
                  <th className="text-center align-middle text-danger">إجمالي المنصرف (-)</th>
                  <th className="text-center align-middle text-success">أرباح المبيعات</th>
                  <th className="text-center align-middle text-danger">خسائر العجز (-)</th>
                  <th className="text-center align-middle text-primary">صافي أرباح الشهر</th>
                  <th className="text-center align-middle bg-light-subtle">الرصيد في نهاية الشهر</th>
                </tr>
              </thead>
              <tbody>
                {monthlySummary.map((m, idx) => (
                  <tr key={idx}>
                    <td className="text-center align-middle font-monospace fw-bold">
                      {m.year}/{String(m.month).padStart(2, '0')}
                    </td>
                    <td className="text-center align-middle text-success fw-bold">
                      {m.incoming > 0 ? `+${m.incoming}` : '0'}
                    </td>
                    <td className="text-center align-middle text-danger fw-bold">
                      {m.outgoing > 0 ? `-${m.outgoing}` : '0'}
                    </td>
                    <td className="text-center align-middle fw-semibold text-success">
                      {fmtNum(m.sales_profit)}
                    </td>
                    <td className="text-center align-middle fw-semibold text-danger">
                      {m.deficit_loss > 0 ? `- ${fmtNum(m.deficit_loss)}` : '0'}
                    </td>
                    <td className="text-center align-middle fw-bold text-primary">
                      {fmtNum(m.net_profit)}
                    </td>
                    <td className="text-center align-middle bg-light-subtle">
                      <span className="badge bg-secondary-subtle text-dark border px-3 py-1 fs-5 fw-bold">
                        {m.running_stock}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
