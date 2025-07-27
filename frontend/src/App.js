import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Payment method options
const PAYMENT_METHODS = [
  "PayPal", "Venmo", "Visa", "Mastercard", "American Express", 
  "Discover", "Debit Card", "Other"
];

const STATUS_OPTIONS = [
  "Ordered", "Shipped", "Delivered", "Returned"
];

const STATUS_COLORS = {
  "Ordered": "bg-yellow-100 text-yellow-800",
  "Shipped": "bg-blue-100 text-blue-800", 
  "Delivered": "bg-green-100 text-green-800",
  "Returned": "bg-red-100 text-red-800",
  "Archived": "bg-gray-100 text-gray-800"
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [purchases, setPurchases] = useState([]);
  const [stores, setStores] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [showAddPurchase, setShowAddPurchase] = useState(false);
  const [showAddStore, setShowAddStore] = useState(false);
  const [editingPurchase, setEditingPurchase] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Form states
  const [newPurchase, setNewPurchase] = useState({
    store_name: '',
    store_url: '',
    product_name: '',
    price: '',
    payment_method: 'PayPal',
    order_date: '',
    expected_delivery: '',
    delivered_date: '',
    status: 'Ordered',
    notes: ''
  });
  
  const [newStore, setNewStore] = useState({
    name: '',
    url: ''
  });

  // Fetch data functions
  const fetchPurchases = async () => {
    try {
      const url = statusFilter === 'all' ? `${API}/purchases` : `${API}/purchases?status=${statusFilter}`;
      const response = await axios.get(url);
      setPurchases(response.data);
    } catch (error) {
      console.error('Error fetching purchases:', error);
    }
  };

  const fetchStores = async () => {
    try {
      const response = await axios.get(`${API}/stores`);
      setStores(response.data);
    } catch (error) {
      console.error('Error fetching stores:', error);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    }
  };

  useEffect(() => {
    fetchPurchases();
    fetchStores();
    fetchDashboardStats();
  }, []);

  useEffect(() => {
    fetchPurchases();
  }, [statusFilter]);

  // Handle form submissions
  const handleAddPurchase = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const purchaseData = {
        ...newPurchase,
        price: parseFloat(newPurchase.price)
      };
      await axios.post(`${API}/purchases`, purchaseData);
      setNewPurchase({
        store_name: '', store_url: '', product_name: '', price: '',
        payment_method: 'PayPal', order_date: '', expected_delivery: '',
        delivered_date: '', status: 'Ordered', notes: ''
      });
      setShowAddPurchase(false);
      fetchPurchases();
      fetchStores();
      fetchDashboardStats();
    } catch (error) {
      console.error('Error adding purchase:', error);
    }
    setLoading(false);
  };

  const handleAddStore = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/stores`, newStore);
      setNewStore({ name: '', url: '' });
      setShowAddStore(false);
      fetchStores();
    } catch (error) {
      console.error('Error adding store:', error);
    }
    setLoading(false);
  };

  const handleUpdatePurchase = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const updateData = {
        ...editingPurchase,
        price: parseFloat(editingPurchase.price)
      };
      await axios.put(`${API}/purchases/${editingPurchase.id}`, updateData);
      setEditingPurchase(null);
      fetchPurchases();
      fetchDashboardStats();
    } catch (error) {
      console.error('Error updating purchase:', error);
    }
    setLoading(false);
  };

  const handleArchivePurchase = async (purchaseId) => {
    try {
      await axios.post(`${API}/purchases/${purchaseId}/archive`);
      fetchPurchases();
      fetchDashboardStats();
    } catch (error) {
      console.error('Error archiving purchase:', error);
    }
  };

  const handleDeletePurchase = async (purchaseId) => {
    if (window.confirm('Are you sure you want to delete this purchase?')) {
      try {
        await axios.delete(`${API}/purchases/${purchaseId}`);
        fetchPurchases();
        fetchDashboardStats();
      } catch (error) {
        console.error('Error deleting purchase:', error);
      }
    }
  };

  const handleDeleteStore = async (storeId) => {
    if (window.confirm('Are you sure you want to delete this store?')) {
      try {
        await axios.delete(`${API}/stores/${storeId}`);
        fetchStores();
      } catch (error) {
        console.error('Error deleting store:', error);
      }
    }
  };

  // Dashboard Component
  const Dashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium text-gray-900">Total Purchases</h3>
          <p className="text-3xl font-bold text-blue-600">{dashboardStats.total_purchases || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium text-gray-900">Total Spent</h3>
          <p className="text-3xl font-bold text-green-600">{formatCurrency(dashboardStats.total_spent || 0)}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium text-gray-900">Active Orders</h3>
          <p className="text-3xl font-bold text-orange-600">
            {(dashboardStats.status_breakdown?.Ordered || 0) + (dashboardStats.status_breakdown?.Shipped || 0)}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <h3 className="text-lg font-medium text-gray-900">Recent Purchases</h3>
        </div>
        <div className="divide-y">
          {(dashboardStats.recent_purchases || []).map((purchase) => (
            <div key={purchase.id} className="p-4 flex justify-between items-center">
              <div>
                <p className="font-medium text-gray-900">{purchase.product_name}</p>
                <p className="text-sm text-gray-500">{purchase.store_name} • {formatDate(purchase.order_date)}</p>
              </div>
              <div className="text-right">
                <p className="font-medium text-gray-900">{formatCurrency(purchase.price)}</p>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${STATUS_COLORS[purchase.status]}`}>
                  {purchase.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Purchase Form Component
  const PurchaseForm = ({ purchase, onSubmit, onCancel, isEdit = false }) => (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Store Name *</label>
          <input
            type="text"
            required
            value={purchase.store_name}
            onChange={(e) => isEdit 
              ? setEditingPurchase({...purchase, store_name: e.target.value})
              : setNewPurchase({...purchase, store_name: e.target.value})
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Store URL</label>
          <input
            type="url"
            value={purchase.store_url}
            onChange={(e) => isEdit 
              ? setEditingPurchase({...purchase, store_url: e.target.value})
              : setNewPurchase({...purchase, store_url: e.target.value})
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Product Name *</label>
        <input
          type="text"
          required
          value={purchase.product_name}
          onChange={(e) => isEdit 
            ? setEditingPurchase({...purchase, product_name: e.target.value})
            : setNewPurchase({...purchase, product_name: e.target.value})
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Price *</label>
          <input
            type="number"
            step="0.01"
            required
            value={purchase.price}
            onChange={(e) => isEdit 
              ? setEditingPurchase({...purchase, price: e.target.value})
              : setNewPurchase({...purchase, price: e.target.value})
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method *</label>
          <select
            required
            value={purchase.payment_method}
            onChange={(e) => isEdit 
              ? setEditingPurchase({...purchase, payment_method: e.target.value})
              : setNewPurchase({...purchase, payment_method: e.target.value})
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {PAYMENT_METHODS.map(method => (
              <option key={method} value={method}>{method}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Order Date *</label>
          <input
            type="date"
            required
            value={purchase.order_date}
            onChange={(e) => isEdit 
              ? setEditingPurchase({...purchase, order_date: e.target.value})
              : setNewPurchase({...purchase, order_date: e.target.value})
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Expected Delivery</label>
          <input
            type="date"
            value={purchase.expected_delivery}
            onChange={(e) => isEdit 
              ? setEditingPurchase({...purchase, expected_delivery: e.target.value})
              : setNewPurchase({...purchase, expected_delivery: e.target.value})
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Delivered Date</label>
          <input
            type="date"
            value={purchase.delivered_date}
            onChange={(e) => isEdit 
              ? setEditingPurchase({...purchase, delivered_date: e.target.value})
              : setNewPurchase({...purchase, delivered_date: e.target.value})
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
        <select
          value={purchase.status}
          onChange={(e) => isEdit 
            ? setEditingPurchase({...purchase, status: e.target.value})
            : setNewPurchase({...purchase, status: e.target.value})
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {STATUS_OPTIONS.map(status => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          rows={3}
          value={purchase.notes}
          onChange={(e) => isEdit 
            ? setEditingPurchase({...purchase, notes: e.target.value})
            : setNewPurchase({...purchase, notes: e.target.value})
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {loading ? 'Saving...' : (isEdit ? 'Update Purchase' : 'Add Purchase')}
        </button>
      </div>
    </form>
  );

  // Purchases Component
  const Purchases = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Purchases</h2>
          <p className="text-gray-600">Track all your online purchases</p>
        </div>
        <button
          onClick={() => setShowAddPurchase(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Add Purchase
        </button>
      </div>

      <div className="flex space-x-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Purchases</option>
          {STATUS_OPTIONS.map(status => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
      </div>

      {showAddPurchase && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Purchase</h3>
          <PurchaseForm
            purchase={newPurchase}
            onSubmit={handleAddPurchase}
            onCancel={() => setShowAddPurchase(false)}
          />
        </div>
      )}

      {editingPurchase && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Purchase</h3>
          <PurchaseForm
            purchase={editingPurchase}
            onSubmit={handleUpdatePurchase}
            onCancel={() => setEditingPurchase(null)}
            isEdit={true}
          />
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Store</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {purchases.map((purchase) => (
                <tr key={purchase.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{purchase.product_name}</p>
                      {purchase.notes && <p className="text-sm text-gray-500">{purchase.notes}</p>}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <p className="text-sm text-gray-900">{purchase.store_name}</p>
                      {purchase.store_url && (
                        <a href={purchase.store_url} target="_blank" rel="noopener noreferrer" 
                           className="text-sm text-blue-600 hover:text-blue-800">
                          Visit Store
                        </a>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(purchase.price)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {purchase.payment_method}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${STATUS_COLORS[purchase.status]}`}>
                      {purchase.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(purchase.order_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => setEditingPurchase(purchase)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleArchivePurchase(purchase.id)}
                      className="text-green-600 hover:text-green-900"
                    >
                      Archive
                    </button>
                    <button
                      onClick={() => handleDeletePurchase(purchase.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  // Stores Component
  const Stores = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Shopping Stores</h2>
          <p className="text-gray-600">Manage your favorite online shopping sites</p>
        </div>
        <button
          onClick={() => setShowAddStore(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Add Store
        </button>
      </div>

      {showAddStore && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Store</h3>
          <form onSubmit={handleAddStore} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Store Name *</label>
              <input
                type="text"
                required
                value={newStore.name}
                onChange={(e) => setNewStore({...newStore, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Store URL *</label>
              <input
                type="url"
                required
                value={newStore.url}
                onChange={(e) => setNewStore({...newStore, url: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowAddStore(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Store'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stores.map((store) => (
          <div key={store.id} className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-medium text-gray-900">{store.name}</h3>
              <button
                onClick={() => handleDeleteStore(store.id)}
                className="text-red-600 hover:text-red-900 text-sm"
              >
                Delete
              </button>
            </div>
            <a
              href={store.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 text-sm break-all"
            >
              {store.url}
            </a>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">ShopTracker</h1>
              <p className="text-gray-600">Your personal online shopping assistant</p>
            </div>
          </div>
          
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: '📊' },
              { id: 'purchases', label: 'Purchases', icon: '📦' },
              { id: 'stores', label: 'Stores', icon: '🏪' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'purchases' && <Purchases />}
        {activeTab === 'stores' && <Stores />}
      </main>
    </div>
  );
}

export default App;