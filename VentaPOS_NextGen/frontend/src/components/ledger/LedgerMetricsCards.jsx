import React from 'react';
import { fmtNum } from '../../utils/formatUtils';

export default function LedgerMetricsCards({ itemInfo, metrics }) {
  if (!itemInfo) return null;

  return (
    <div className="row g-2 mb-3">
      {/* Card 1: Opening Stock */}
      <div className="col-sm-6 col-md-4 col-lg-2">
        <div className="card border-0 shadow-sm h-100 bg-light-subtle">
          <div className="card-body p-2 text-center">
            <div className="text-muted small fw-semibold">رصيد البداية</div>
            <div className="fs-3 fw-bold text-dark mt-1">{itemInfo.initial_quantity}</div>
            <div className="text-secondary small font-monospace">
              {itemInfo.initial_year}/{String(itemInfo.initial_month).padStart(2, '0')}
            </div>
          </div>
        </div>
      </div>

      {/* Card 2: Current Stock */}
      <div className="col-sm-6 col-md-4 col-lg-2">
        <div className="card border-0 shadow-sm h-100 border-start border-primary border-3">
          <div className="card-body p-2 text-center">
            <div className="text-muted small fw-semibold">الرصيد الحالي بالمخزن</div>
            <div className="fs-2 fw-bolder text-primary mt-1">{itemInfo.current_stock}</div>
            <div className="text-muted small">قطعة متاحة</div>
          </div>
        </div>
      </div>

      {/* Card 3: Current Buying Price */}
      <div className="col-sm-6 col-md-4 col-lg-2">
        <div className="card border-0 shadow-sm h-100">
          <div className="card-body p-2 text-center">
            <div className="text-muted small fw-semibold">سعر الشراء الحالي</div>
            <div className="fs-3 fw-bold text-dark mt-1">{fmtNum(itemInfo.current_purchase_price)}</div>
            <div className="text-muted small">جنيه / للقطعة</div>
          </div>
        </div>
      </div>

      {/* Card 4: Current Commission */}
      <div className="col-sm-6 col-md-4 col-lg-2">
        <div className="card border-0 shadow-sm h-100">
          <div className="card-body p-2 text-center">
            <div className="text-muted small fw-semibold">المندبة الحالية</div>
            <div className="fs-3 fw-bold text-purple mt-1" style={{ color: '#6f42c1' }}>
              {fmtNum(itemInfo.current_commission)}
            </div>
            <div className="text-muted small">جنيه / عمولة بيع</div>
          </div>
        </div>
      </div>

      {/* Card 5: Total Deficit Losses */}
      <div className="col-sm-6 col-md-4 col-lg-2">
        <div className="card border-0 shadow-sm h-100 border-start border-danger border-3">
          <div className="card-body p-2 text-center">
            <div className="text-danger small fw-bold">إجمالي خسائر العجز (-)</div>
            <div className="fs-3 fw-bolder text-danger mt-1">
              - {fmtNum(metrics.deficit_loss || 0)}
            </div>
            <div className="text-danger small">({itemInfo.total_deficit_qty || 0} قطعة عجز)</div>
          </div>
        </div>
      </div>

      {/* Card 6: Net Profit After Deficit */}
      <div className="col-sm-6 col-md-4 col-lg-2">
        <div className="card border-0 shadow-sm h-100 bg-success-subtle">
          <div className="card-body p-2 text-center">
            <div className="text-success small fw-bold">صافي المكسب بعد العجز</div>
            <div className={`fs-3 fw-bolder mt-1 ${metrics.total_profit >= 0 ? 'text-success' : 'text-danger'}`}>
              {fmtNum(metrics.total_profit || 0)}
            </div>
            <div className="text-muted small">جنيه</div>
          </div>
        </div>
      </div>
    </div>
  );
}
