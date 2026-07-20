import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { IconBuildingStore, IconPlus, IconEdit, IconCheck, IconTrash } from '@tabler/icons-react';

export default function BranchSelection() {
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // States for adding/editing a branch
  const [showModal, setShowModal] = useState(false);
  const [editingBranch, setEditingBranch] = useState(null);
  const [branchName, setBranchName] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    fetchBranches();
  }, []);

  const fetchBranches = async () => {
    try {
      const res = await api.get('/branches/');
      const fetchedBranches = res.data.results || res.data;
      setBranches(fetchedBranches);
      
      // Auto-skip if there is only 1 branch AND no branch is currently selected in localStorage
      if (fetchedBranches.length === 1 && !localStorage.getItem('branchId')) {
        handleSelectBranch(fetchedBranches[0]);
      }
    } catch (err) {
      setError('تعذر جلب الفروع. يرجى المحاولة لاحقاً.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectBranch = (branch) => {
    localStorage.setItem('branchId', branch.id);
    localStorage.setItem('branchName', branch.name);
    navigate('/');
  };

  const handleSaveBranch = async (e) => {
    e.preventDefault();
    if (!branchName.trim()) return;

    try {
      if (editingBranch) {
        await api.patch(`/branches/${editingBranch.id}/`, { name: branchName });
      } else {
        await api.post('/branches/', { name: branchName });
      }
      setShowModal(false);
      setEditingBranch(null);
      setBranchName('');
      fetchBranches();
    } catch (err) {
      alert('حدث خطأ أثناء حفظ الفرع.');
    }
  };

  const handleDeleteBranch = async (e, branch) => {
    e.stopPropagation();
    if (window.confirm(`هل أنت متأكد من حذف فرع "${branch.name}"؟ سيتم حذف جميع الفواتير والمنتجات والمصروفات المتعلقة بهذا الفرع نهائياً ولا يمكن التراجع عن هذه الخطوة!`)) {
      try {
        await api.delete(`/branches/${branch.id}/`);
        fetchBranches();
        if (localStorage.getItem('branchId') == branch.id) {
          localStorage.removeItem('branchId');
          localStorage.removeItem('branchName');
        }
      } catch (err) {
        alert('حدث خطأ أثناء الحذف.');
      }
    }
  };

  const openAddModal = () => {
    if (branches.length >= 10) {
      alert('تم الوصول للحد الأقصى لعدد الفروع (10).');
      return;
    }
    setEditingBranch(null);
    setBranchName('');
    setShowModal(true);
  };

  const openEditModal = (e, branch) => {
    e.stopPropagation(); // prevent selecting the branch
    setEditingBranch(branch);
    setBranchName(branch.name);
    setShowModal(true);
  };

  return (
    <div className="page page-center" style={{ backgroundColor: '#f8f9fa', overflow: 'hidden', height: '100vh', fontFamily: "'Cairo', sans-serif" }}>
      <div className="container-fluid px-4 py-5">
        <div className="text-center mb-4">
          <h2 className="fw-bold text-dark mb-1">اختيار الفرع</h2>
          <p className="text-muted">برجاء اختيار الفرع الذي ترغب في العمل عليه</p>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <div className="text-center py-5"><div className="spinner-border text-primary" role="status"></div></div>
        ) : (
          <div className="row row-cards">
            {branches.map(branch => (
              <div className="col-12 col-md-6 mb-3" key={branch.id}>
                <div 
                  className="card card-link card-link-pop cursor-pointer h-100" 
                  onClick={() => handleSelectBranch(branch)}
                  style={{ borderRadius: '12px', border: '1px solid #e0e6ed', transition: 'all 0.2s' }}
                >
                  <div className="card-body d-flex align-items-center justify-content-between p-4">
                    <div className="d-flex align-items-center">
                      <span className="bg-primary text-white avatar rounded me-3" style={{ width: '48px', height: '48px' }}>
                        <IconBuildingStore size={24} />
                      </span>
                      <div>
                        <div className="font-weight-medium fs-3 text-dark">{branch.name}</div>
                      </div>
                    </div>
                    <div className="d-flex gap-2">
                      <button 
                        className="btn btn-icon btn-light" 
                        onClick={(e) => openEditModal(e, branch)}
                        title="تعديل اسم الفرع"
                      >
                        <IconEdit size={18} />
                      </button>
                      <button 
                        className="btn btn-icon btn-danger-outline text-danger border-0" 
                        onClick={(e) => handleDeleteBranch(e, branch)}
                        title="حذف الفرع"
                      >
                        <IconTrash size={18} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {branches.length < 10 && (
              <div className="col-12 col-md-6 mb-3">
                <div 
                  className="card card-link card-link-pop cursor-pointer h-100 border-dashed" 
                  onClick={openAddModal}
                  style={{ borderRadius: '12px', borderColor: '#cbd5e1', backgroundColor: '#f1f5f9' }}
                >
                  <div className="card-body d-flex align-items-center justify-content-center p-4 text-secondary">
                    <IconPlus size={24} className="me-2" />
                    <span className="fs-3 font-weight-medium">إضافة فرع جديد</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal for Add/Edit Branch */}
      {showModal && (
        <div className="modal modal-blur fade show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content" style={{ borderRadius: '12px' }}>
              <div className="modal-header">
                <h5 className="modal-title fw-bold">{editingBranch ? 'تعديل الفرع' : 'إضافة فرع جديد'}</h5>
                <button type="button" className="btn-close" onClick={() => setShowModal(false)}></button>
              </div>
              <form onSubmit={handleSaveBranch}>
                <div className="modal-body p-4">
                  <div className="mb-3">
                    <label className="form-label fw-bold">اسم الفرع</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      value={branchName} 
                      onChange={(e) => setBranchName(e.target.value)} 
                      required 
                      autoFocus
                    />
                  </div>
                </div>
                <div className="modal-footer bg-light border-0 py-3" style={{ borderRadius: '0 0 12px 12px' }}>
                  <button type="button" className="btn btn-link link-secondary" onClick={() => setShowModal(false)}>
                    إلغاء
                  </button>
                  <button type="submit" className="btn btn-primary ms-auto fw-bold">
                    <IconCheck className="me-2" size={18} /> حفظ
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
