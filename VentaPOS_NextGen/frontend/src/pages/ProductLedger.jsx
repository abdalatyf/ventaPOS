import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import CommissionModal from '../components/CommissionModal';

const MOCK_LEDGER = {
    item: { id: 1, name: 'لاب توب ديل', quantity: 15, purchase_price: 10000 },
    dashboard: {
        cash_profit: 15000,
        installment_profit: 8000,
        adjustment_impact: -500,
        total_profit: 22500
    },
    movements: [
        { id: 101, date: '2026-06-01', type: 'IN', desc: 'رصيد افتتاحي', qty: 20 },
        { id: 102, date: '2026-06-05', type: 'OUT', desc: 'فاتورة مبيعات #1001', qty: 2 },
        { id: 103, date: '2026-06-10', type: 'OUT', desc: 'فاتورة مبيعات #1005', qty: 3 },
    ],
    financials: [
        { month: 'يونيو 2026', revenue: 60000, cost: 50000, profit: 10000, commission: 500 },
        { month: 'مايو 2026', revenue: 120000, cost: 100000, profit: 20000, commission: 1000 },
    ],
    commissions: [
        { id: 201, month: '06', year: '2026', amount: 500, status: 'مدفوعة' },
        { id: 202, month: '05', year: '2026', amount: 1000, status: 'مدفوعة' },
    ]
};

const ProductLedger = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, financial, movement, commission
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [showCommissionModal, setShowCommissionModal] = useState(false);

  useEffect(() => {
     fetchLedger();
  }, [id]);

  const fetchLedger = async () => {
     try {
         setLoading(true);
         const res = await api.get(`/api/v1/inventory-items/${id}/ledger/`);
         setData(res.data);
     } catch (err) {
         console.warn("Backend not ready, using mock data for ledger.");
         setData(MOCK_LEDGER);
     } finally {
         setLoading(false);
     }
  };

  const handleSaveCommission = async (newCommission) => {
     try {
         // mock post
         // await api.post(`/api/v1/inventory-items/${id}/commissions/`, newCommission);
         
         const newComm = {
             id: Date.now(),
             month: newCommission.month,
             year: newCommission.year,
             amount: newCommission.amount,
             status: 'غير مدفوعة'
         };
         setData({
             ...data,
             commissions: [newComm, ...data.commissions]
         });
         setShowCommissionModal(false);
     } catch (err) {
         console.error(err);
     }
  };

  if (loading) return <div className="text-center p-5"><div className="spinner-border text-primary" role="status"></div></div>;
  if (!data) return <div className="text-center p-5 text-muted">الصنف مش موجود.</div>;

  return (
      <div className="page-wrapper">
      <div className="page-header d-print-none">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">
                كارت الصنف: {data.item.name} (#{data.item.id})
              </h2>
              <div className="text-muted mt-1">
                الرصيد: {data.item.quantity} حتة | سعر الشراء: {data.item.purchase_price}
              </div>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <Link to="/inventory" className="btn btn-outline-secondary">
                الرجوع للبضاعة
              </Link>
            </div>
          </div>
        </div>
      </div>
      
      <div className="page-body">
        <div className="container-fluid">
          <div className="card">
            <div className="card-header">
              <ul className="nav nav-tabs card-header-tabs" data-bs-toggle="tabs">
                <li className="nav-item">
                  <a href="#tabs-dashboard" className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}>
                    لوحة المعلومات
                  </a>
                </li>
                <li className="nav-item">
                  <a href="#tabs-financial" className={`nav-link ${activeTab === 'financial' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('financial'); }}>
                    تحليل مالي
                  </a>
                </li>
                <li className="nav-item">
                  <a href="#tabs-movement" className={`nav-link ${activeTab === 'movement' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('movement'); }}>
                    السجل التفصيلي (Timeline)
                  </a>
                </li>
                <li className="nav-item">
                  <a href="#tabs-commission" className={`nav-link ${activeTab === 'commission' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('commission'); }}>
                    سجل المندبات
                  </a>
                </li>
              </ul>
            </div>
            <div className="card-body">
              <div className="tab-content">
                
                {/* Dashboard Tab */}
                <div className={`tab-pane ${activeTab === 'dashboard' ? 'active show' : ''}`} id="tabs-dashboard">
                   <div className="row row-cards">
                      <div className="col-sm-6 col-lg-3">
                        <div className="card card-sm">
                          <div className="card-body">
                            <div className="row align-items-center">
                              <div className="col-auto">
                                <span className="bg-success text-white avatar">
                                  <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M16.7 8a3 3 0 0 0 -2.7 -2h-4a3 3 0 0 0 0 6h4a3 3 0 0 1 0 6h-4a3 3 0 0 1 -2.7 -2" /><path d="M12 3v3m0 12v3" /></svg>
                                </span>
                              </div>
                              <div className="col">
                                <div className="font-weight-medium">
                                  أرباح الكاش
                                </div>
                                <div className="text-muted">
                                  {data.dashboard.cash_profit.toLocaleString()}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="col-sm-6 col-lg-3">
                        <div className="card card-sm">
                          <div className="card-body">
                            <div className="row align-items-center">
                              <div className="col-auto">
                                <span className="bg-info text-white avatar">
                                  <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2z" /><path d="M9 7l1 0" /><path d="M9 13l6 0" /><path d="M13 17l2 0" /></svg>
                                </span>
                              </div>
                              <div className="col">
                                <div className="font-weight-medium">
                                  أرباح القسط
                                </div>
                                <div className="text-muted">
                                  {data.dashboard.installment_profit.toLocaleString()}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="col-sm-6 col-lg-3">
                        <div className="card card-sm">
                          <div className="card-body">
                            <div className="row align-items-center">
                              <div className="col-auto">
                                <span className="bg-danger text-white avatar">
                                  <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 9v2m0 4v.01" /></svg>
                                </span>
                              </div>
                              <div className="col">
                                <div className="font-weight-medium">
                                  تأثير التسويات
                                </div>
                                <div className="text-muted">
                                  {data.dashboard.adjustment_impact.toLocaleString()}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="col-sm-6 col-lg-3">
                        <div className="card card-sm">
                          <div className="card-body">
                            <div className="row align-items-center">
                              <div className="col-auto">
                                <span className="bg-primary text-white avatar">
                                  <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 3v18h18" /><path d="M20 18v3" /><path d="M16 16v5" /><path d="M12 13v8" /><path d="M8 16v5" /><path d="M3 11c6 0 5 -5 9 -5s3 5 9 5" /></svg>
                                </span>
                              </div>
                              <div className="col">
                                <div className="font-weight-medium">
                                  إجمالي الأرباح
                                </div>
                                <div className="text-muted">
                                  {data.dashboard.total_profit.toLocaleString()}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                   </div>
                </div>

                {/* Financial Tab */}
                <div className={`tab-pane ${activeTab === 'financial' ? 'active show' : ''}`} id="tabs-financial">
                   <div className="table-responsive">
                     <table className="table card-table table-vcenter text-nowrap datatable">
                       <thead>
                         <tr>
                           <th>الشهر</th>
                           <th>إجمالي المبيعات</th>
                           <th>التكلفة</th>
                           <th>الربح الصافي</th>
                           <th>إجمالي المندبات</th>
                         </tr>
                       </thead>
                       <tbody>
                         {data.financials.map((fin, idx) => (
                            <tr key={idx}>
                              <td>{fin.month}</td>
                              <td>{fin.revenue.toLocaleString()}</td>
                              <td>{fin.cost.toLocaleString()}</td>
                              <td><span className="text-success">{fin.profit.toLocaleString()}</span></td>
                              <td>{fin.commission.toLocaleString()}</td>
                            </tr>
                         ))}
                       </tbody>
                     </table>
                   </div>
                </div>

                {/* Movement Tab */}
                <div className={`tab-pane ${activeTab === 'movement' ? 'active show' : ''}`} id="tabs-movement">
                   <ul className="list list-timeline list-timeline-simple">
                     {data.movements.map(mov => (
                        <li key={mov.id}>
                          <div className={`list-timeline-icon ${mov.type === 'IN' ? 'bg-success' : 'bg-danger'}`}>
                            {mov.type === 'IN' ? 
                              <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 5l0 14" /><path d="M5 12l14 0" /></svg>
                              :
                              <svg xmlns="http://www.w3.org/2000/svg" className="icon" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 12l14 0" /></svg>
                            }
                          </div>
                          <div className="list-timeline-content">
                            <div className="list-timeline-time">{mov.date}</div>
                            <p className="list-timeline-title">{mov.desc}</p>
                            <p className="text-muted">الكمية: {mov.qty} حتة</p>
                          </div>
                        </li>
                     ))}
                     {data.movements.length === 0 && (
                        <li><div className="text-muted py-4">مفيش حركة على الصنف ده.</div></li>
                     )}
                   </ul>
                </div>

                {/* Commission Tab */}
                <div className={`tab-pane ${activeTab === 'commission' ? 'active show' : ''}`} id="tabs-commission">
                   <div className="mb-3 d-flex justify-content-end">
                      <button className="btn btn-primary" onClick={() => setShowCommissionModal(true)}>
                         <svg xmlns="http://www.w3.org/2000/svg" className="icon me-2" width="24" height="24" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 5l0 14" /><path d="M5 12l14 0" /></svg>
                         إضافة مندبة جديدة (آلة الزمن)
                      </button>
                   </div>
                   <div className="table-responsive">
                     <table className="table card-table table-vcenter text-nowrap datatable">
                       <thead>
                         <tr>
                           <th>الشهر</th>
                           <th>السنة</th>
                           <th>قيمة المندبة</th>
                           <th>الحالة</th>
                         </tr>
                       </thead>
                       <tbody>
                         {data.commissions.map(comm => (
                            <tr key={comm.id}>
                              <td>{comm.month}</td>
                              <td>{comm.year}</td>
                              <td>{comm.amount.toLocaleString()}</td>
                              <td>
                                 <span className={`badge ${comm.status === 'مدفوعة' ? 'bg-success-lt' : 'bg-warning-lt'}`}>
                                    {comm.status}
                                 </span>
                              </td>
                            </tr>
                         ))}
                       </tbody>
                     </table>
                   </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Commission Modal Component */}
      <CommissionModal 
         show={showCommissionModal} 
         onClose={() => setShowCommissionModal(false)} 
         onSave={handleSaveCommission} 
      />
    </div>
  );
};

export default ProductLedger;
