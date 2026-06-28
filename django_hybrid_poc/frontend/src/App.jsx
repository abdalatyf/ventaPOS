import { useState, useEffect } from 'react';
import axios from 'axios';
import { IconEdit, IconTrash, IconPlus } from '@tabler/icons-react';
import './App.css';

const API_URL = 'http://127.0.0.1:8085/api/items/';

function App() {
  const [items, setItems] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    quantity: ''
  });

  const fetchItems = async () => {
    try {
      const response = await axios.get(API_URL);
      setItems(response.data);
    } catch (error) {
      console.error("Error fetching items:", error);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const openAddModal = () => {
    setEditingItem(null);
    setFormData({ name: '', description: '', price: '', quantity: '' });
    setShowModal(true);
  };

  const openEditModal = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name || '',
      description: item.description || '',
      price: item.price || '',
      quantity: item.quantity || ''
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await axios.put(`${API_URL}${editingItem.id}/`, formData);
      } else {
        await axios.post(API_URL, formData);
      }
      closeModal();
      fetchItems();
    } catch (error) {
      console.error("Error saving item:", error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this item?")) {
      try {
        await axios.delete(`${API_URL}${id}/`);
        fetchItems();
      } catch (error) {
        console.error("Error deleting item:", error);
      }
    }
  };

  return (
    <div className="page">
      <div className="page-wrapper">
        <div className="page-header d-print-none">
          <div className="container-xl">
            <div className="row g-2 align-items-center">
              <div className="col">
                <h2 className="page-title">Items Management</h2>
              </div>
              <div className="col-auto ms-auto d-print-none">
                <div className="btn-list">
                  <button className="btn btn-primary" onClick={openAddModal}>
                    <IconPlus className="icon" />
                    Add Item
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="page-body">
          <div className="container-xl">
            <div className="card">
              <div className="table-responsive">
                <table className="table table-vcenter card-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Description</th>
                      <th>Price</th>
                      <th>Quantity</th>
                      <th className="w-1"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map(item => (
                      <tr key={item.id}>
                        <td>{item.name}</td>
                        <td className="text-secondary">{item.description}</td>
                        <td>{item.price}</td>
                        <td>{item.quantity}</td>
                        <td>
                          <div className="btn-list flex-nowrap">
                            <button className="btn btn-sm btn-outline-primary" onClick={() => openEditModal(item)}>
                              <IconEdit className="icon" />
                              Edit
                            </button>
                            <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(item.id)}>
                              <IconTrash className="icon" />
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {items.length === 0 && (
                      <tr>
                        <td colSpan="5" className="text-center py-4">No items found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="modal modal-blur fade show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">{editingItem ? 'Edit Item' : 'Add New Item'}</h5>
                <button type="button" className="btn-close" onClick={closeModal} aria-label="Close"></button>
              </div>
              <form onSubmit={handleSubmit}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label">Name</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      name="name" 
                      value={formData.name} 
                      onChange={handleInputChange} 
                      required 
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Description</label>
                    <textarea 
                      className="form-control" 
                      name="description" 
                      value={formData.description} 
                      onChange={handleInputChange} 
                    ></textarea>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Price</label>
                    <input 
                      type="number" 
                      step="0.01" 
                      className="form-control" 
                      name="price" 
                      value={formData.price} 
                      onChange={handleInputChange} 
                      required 
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Quantity</label>
                    <input 
                      type="number" 
                      className="form-control" 
                      name="quantity" 
                      value={formData.quantity} 
                      onChange={handleInputChange} 
                      required 
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-link link-secondary" onClick={closeModal}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary ms-auto">
                    {editingItem ? 'Save Changes' : 'Create Item'}
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

export default App;
