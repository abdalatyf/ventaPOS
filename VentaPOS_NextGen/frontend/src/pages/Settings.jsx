import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

const MOCK_BRANCHES = [
  { id: 1, name: 'فرع القاهرة', location: 'مدينة نصر' },
  { id: 2, name: 'فرع الإسكندرية', location: 'سموحة' }
];

const MOCK_SALESPERSONS = [
  { id: 1, name: 'أحمد محمود', branch: 1, phone: '01000000001' },
  { id: 2, name: 'سيد علي', branch: 2, phone: '01111111111' }
];

const Settings = () => {
  const [activeTab, setActiveTab] = useState('branches');
  
  const [branches, setBranches] = useState([]);
  const [salespersons, setSalespersons] = useState([]);
  const [loading, setLoading] = useState(true);

  // Branch modal state
  const [showBranchModal, setShowBranchModal] = useState(false);
  const [branchModalType, setBranchModalType] = useState('add');
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [branchFormData, setBranchFormData] = useState({ name: '', location: '' });

  // Salesperson modal state
  const [showSpModal, setShowSpModal] = useState(false);
  const [spModalType, setSpModalType] = useState('add');
  const [selectedSp, setSelectedSp] = useState(null);
  const [spFormData, setSpFormData] = useState({ name: '', branch: '', phone: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [branchesRes, spRes] = await Promise.all([
        api.get('/api/v1/branches/').catch(() => ({ data: MOCK_BRANCHES })),
        api.get('/api/v1/salespersons/').catch(() => ({ data: MOCK_SALESPERSONS }))
      ]);
      const branchData = branchesRes.data?.results || branchesRes.data;
      const spData = spRes.data?.results || spRes.data;
      setBranches(Array.isArray(branchData) ? branchData : []);
      setSalespersons(Array.isArray(spData) ? spData : []);
    } catch (err) {
      console.warn("Error fetching data, using mocks", err);
      setBranches(MOCK_BRANCHES);
      setSalespersons(MOCK_SALESPERSONS);
    } finally {
      setLoading(false);
    }
  };

  // --- Branch Handlers ---
  const openBranchModal = (type, branch = null) => {
    setBranchModalType(type);
    setSelectedBranch(branch);
    if (branch) {
      setBranchFormData({ name: branch.name || '', location: branch.location || '' });
    } else {
      setBranchFormData({ name: '', location: '' });
    }
    setShowBranchModal(true);
  };

  const handleBranchChange = (e) => {
    setBranchFormData({ ...branchFormData, [e.target.name]: e.target.value });
  };

  const handleBranchSave = (e) => {
    e.preventDefault();
    if (branchModalType === 'add') {
      const newBranch = { id: Date.now(), ...branchFormData };
      setBranches([...branches, newBranch]);
    } else if (branchModalType === 'edit') {
      setBranches(branches.map(b => b.id === selectedBranch.id ? { ...b, ...branchFormData } : b));
    } else if (branchModalType === 'delete') {
      setBranches(branches.filter(b => b.id !== selectedBranch.id));
    }
    setShowBranchModal(false);
  };

  // --- Salesperson Handlers ---
  const openSpModal = (type, sp = null) => {
    setSpModalType(type);
    setSelectedSp(sp);
    if (sp) {
      setSpFormData({ name: sp.name || '', branch: sp.branch || '', phone: sp.phone || '' });
    } else {
      setSpFormData({ name: '', branch: branches.length > 0 ? branches[0].id : '', phone: '' });
    }
    setShowSpModal(true);
  };

  const handleSpChange = (e) => {
    setSpFormData({ ...spFormData, [e.target.name]: e.target.value });
  };

  const handleSpSave = (e) => {
    e.preventDefault();
    if (spModalType === 'add') {
      const newSp = { id: Date.now(), ...spFormData, branch: parseInt(spFormData.branch, 10) };
      setSalespersons([...salespersons, newSp]);
    } else if (spModalType === 'edit') {
      setSalespersons(salespersons.map(s => s.id === selectedSp.id ? { ...s, ...spFormData, branch: parseInt(spFormData.branch, 10) } : s));
    } else if (spModalType === 'delete') {
      setSalespersons(salespersons.filter(s => s.id !== selectedSp.id));
    }
    setShowSpModal(false);
  };

  const getBranchName = (branchId) => {
    const branch = branches.find(b => b.id === branchId);
    return branch ? branch.name : 'فرع غير معروف';
  };

  return (
    <div className="page-wrapper bg-light">
      <div className="container-xl">
        {/* Page title */}
        <div className="page-header d-print-none">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title text-primary fw-bold">إعدادات النظام</h2>
              <p className="text-muted mt-1">ظبط بيانات الفروع والمناديب قبل ما تشتغل</p>
            </div>
            <div className="col-auto ms-auto d-print-none">
              <Link to="/" className="btn btn-outline-secondary">
                العودة للدفتر
              </Link>
            </div>
          </div>
        </div>
      </div>
      
      <div className="page-body">
        <div className="container-xl">
          <div className="card shadow-sm border-0">
            <div className="card-header">
              <ul className="nav nav-tabs card-header-tabs" data-bs-toggle="tabs">
                <li className="nav-item">
                  <a href="#tabs-branches" className={`nav-link fw-bold ${activeTab === 'branches' ? 'active' : ''}`} data-bs-toggle="tab" onClick={() => setActiveTab('branches')}>
                    الفروع
                  </a>
                </li>
                <li className="nav-item">
                  <a href="#tabs-salespersons" className={`nav-link fw-bold ${activeTab === 'salespersons' ? 'active' : ''}`} data-bs-toggle="tab" onClick={() => setActiveTab('salespersons')}>
                    المناديب
                  </a>
                </li>
              </ul>
            </div>
            
            <div className="card-body">
              <div className="tab-content">
                {/* Branches Tab */}
                <div className={`tab-pane ${activeTab === 'branches' ? 'active show' : ''}`} id="tabs-branches">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <h4 className="card-title mb-0">قائمة الفروع</h4>
                    <button className="btn btn-primary" onClick={() => openBranchModal('add')}>
                      إضافة فرع جديد
                    </button>
                  </div>
                  
                  {loading ? (
                    <div className="text-center py-4">
                      <div className="spinner-border text-primary" role="status"></div>
                      <div className="mt-2 text-muted">جاري التحميل...</div>
                    </div>
                  ) : (
                    <div className="table-responsive">
                      <table className="table card-table table-vcenter text-nowrap datatable">
                        <thead>
                          <tr>
                            <th>الرقم</th>
                            <th>اسم الفرع</th>
                            <th>المكان</th>
                            <th className="text-end">الإجراءات</th>
                          </tr>
                        </thead>
                        <tbody>
                          {branches.length > 0 ? branches.map(branch => (
                            <tr key={branch.id}>
                              <td><span className="text-muted">{branch.id}</span></td>
                              <td>{branch.name}</td>
                              <td>{branch.location}</td>
                              <td className="text-end">
                                <button onClick={() => openBranchModal('edit', branch)} className="btn btn-sm btn-outline-primary me-2">
                                  تعديل
                                </button>
                                <button onClick={() => openBranchModal('delete', branch)} className="btn btn-sm btn-outline-danger">
                                  مسح
                                </button>
                              </td>
                            </tr>
                          )) : (
                            <tr>
                              <td colSpan="4" className="text-center text-muted py-4">مافيش فروع متسجلة لسه.</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Salespersons Tab */}
                <div className={`tab-pane ${activeTab === 'salespersons' ? 'active show' : ''}`} id="tabs-salespersons">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <h4 className="card-title mb-0">قائمة المناديب</h4>
                    <button className="btn btn-primary" onClick={() => openSpModal('add')}>
                      إضافة مندوب جديد
                    </button>
                  </div>
                  
                  {loading ? (
                    <div className="text-center py-4">
                      <div className="spinner-border text-primary" role="status"></div>
                      <div className="mt-2 text-muted">جاري التحميل...</div>
                    </div>
                  ) : (
                    <div className="table-responsive">
                      <table className="table card-table table-vcenter text-nowrap datatable">
                        <thead>
                          <tr>
                            <th>الرقم</th>
                            <th>اسم المندوب</th>
                            <th>الفرع التابع ليه</th>
                            <th>رقم التليفون</th>
                            <th className="text-end">الإجراءات</th>
                          </tr>
                        </thead>
                        <tbody>
                          {salespersons.length > 0 ? salespersons.map(sp => (
                            <tr key={sp.id}>
                              <td><span className="text-muted">{sp.id}</span></td>
                              <td>{sp.name}</td>
                              <td><span className="badge bg-blue-lt">{getBranchName(sp.branch)}</span></td>
                              <td>{sp.phone}</td>
                              <td className="text-end">
                                <button onClick={() => openSpModal('edit', sp)} className="btn btn-sm btn-outline-primary me-2">
                                  تعديل
                                </button>
                                <button onClick={() => openSpModal('delete', sp)} className="btn btn-sm btn-outline-danger">
                                  مسح
                                </button>
                              </td>
                            </tr>
                          )) : (
                            <tr>
                              <td colSpan="5" className="text-center text-muted py-4">مافيش مناديب متسجلين لسه.</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Branch Modal */}
      {showBranchModal && (
        <div className="modal modal-blur fade show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  {branchModalType === 'add' && 'تسجيل فرع جديد'}
                  {branchModalType === 'edit' && 'تعديل بيانات الفرع'}
                  {branchModalType === 'delete' && 'تأكيد مسح الفرع'}
                </h5>
                <button type="button" className="btn-close" onClick={() => setShowBranchModal(false)} aria-label="Close"></button>
              </div>
              <form onSubmit={handleBranchSave}>
                <div className="modal-body">
                  {branchModalType === 'delete' ? (
                    <p>متأكد إنك عايز تمسح فرع <strong>{selectedBranch?.name}</strong>؟</p>
                  ) : (
                    <div className="row">
                      <div className="col-md-12 mb-3">
                        <label className="form-label">اسم الفرع</label>
                        <input type="text" className="form-control" name="name" value={branchFormData.name} onChange={handleBranchChange} required />
                      </div>
                      <div className="col-md-12 mb-3">
                        <label className="form-label">المكان / العنوان</label>
                        <input type="text" className="form-control" name="location" value={branchFormData.location} onChange={handleBranchChange} required />
                      </div>
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-link link-secondary" onClick={() => setShowBranchModal(false)}>
                    إلغاء
                  </button>
                  <button type="submit" className={`btn ${branchModalType === 'delete' ? 'btn-danger' : 'btn-primary'} ms-auto`}>
                    {branchModalType === 'delete' ? 'أيوة، امسح' : 'حفظ التعديلات'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Salesperson Modal */}
      {showSpModal && (
        <div className="modal modal-blur fade show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  {spModalType === 'add' && 'تسجيل مندوب جديد'}
                  {spModalType === 'edit' && 'تعديل بيانات المندوب'}
                  {spModalType === 'delete' && 'تأكيد مسح المندوب'}
                </h5>
                <button type="button" className="btn-close" onClick={() => setShowSpModal(false)} aria-label="Close"></button>
              </div>
              <form onSubmit={handleSpSave}>
                <div className="modal-body">
                  {spModalType === 'delete' ? (
                    <p>متأكد إنك عايز تمسح المندوب <strong>{selectedSp?.name}</strong>؟</p>
                  ) : (
                    <div className="row">
                      <div className="col-md-12 mb-3">
                        <label className="form-label">اسم المندوب</label>
                        <input type="text" className="form-control" name="name" value={spFormData.name} onChange={handleSpChange} required />
                      </div>
                      <div className="col-md-12 mb-3">
                        <label className="form-label">الفرع التابع ليه</label>
                        <select className="form-select" name="branch" value={spFormData.branch} onChange={handleSpChange} required>
                          <option value="" disabled>اختار الفرع...</option>
                          {branches.map(b => (
                            <option key={b.id} value={b.id}>{b.name}</option>
                          ))}
                        </select>
                      </div>
                      <div className="col-md-12 mb-3">
                        <label className="form-label">رقم التليفون</label>
                        <input type="text" className="form-control" name="phone" value={spFormData.phone} onChange={handleSpChange} />
                      </div>
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-link link-secondary" onClick={() => setShowSpModal(false)}>
                    إلغاء
                  </button>
                  <button type="submit" className={`btn ${spModalType === 'delete' ? 'btn-danger' : 'btn-primary'} ms-auto`}>
                    {spModalType === 'delete' ? 'أيوة، امسح' : 'حفظ التعديلات'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;
