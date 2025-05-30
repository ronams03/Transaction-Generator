import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Components
const Header = () => (
  <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-6 shadow-lg">
    <div className="container mx-auto px-4">
      <h1 className="text-3xl font-bold flex items-center">
        <span className="mr-3">💳</span>
        PayPal Mock Transaction Generator
      </h1>
      <p className="text-blue-100 mt-2">Generate realistic PayPal transactions for testing and development</p>
    </div>
  </header>
);

const TransactionGenerator = ({ onGenerate, loading }) => {
  const [formData, setFormData] = useState({
    count: 10,
    transaction_type: '',
    status: '',
    min_amount: 1.0,
    max_amount: 1000.0,
    currency: 'USD',
    days_back: 30
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = { ...formData };
    // Remove empty strings
    Object.keys(payload).forEach(key => {
      if (payload[key] === '') {
        delete payload[key];
      }
    });
    onGenerate(payload);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name.includes('amount') || name === 'count' || name === 'days_back' 
        ? parseFloat(value) || 0 
        : value
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <span className="mr-2">⚙️</span>
        Generate Transactions
      </h2>
      
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Count</label>
          <input
            type="number"
            name="count"
            value={formData.count}
            onChange={handleChange}
            min="1"
            max="1000"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Transaction Type</label>
          <select
            name="transaction_type"
            value={formData.transaction_type}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Any</option>
            <option value="payment">Payment</option>
            <option value="refund">Refund</option>
            <option value="subscription">Subscription</option>
            <option value="dispute">Dispute</option>
            <option value="chargeback">Chargeback</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            name="status"
            value={formData.status}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Any</option>
            <option value="completed">Completed</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
            <option value="refunded">Refunded</option>
            <option value="disputed">Disputed</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
          <select
            name="currency"
            value={formData.currency}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
            <option value="CAD">CAD</option>
            <option value="AUD">AUD</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Min Amount</label>
          <input
            type="number"
            name="min_amount"
            value={formData.min_amount}
            onChange={handleChange}
            min="0.01"
            step="0.01"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Max Amount</label>
          <input
            type="number"
            name="max_amount"
            value={formData.max_amount}
            onChange={handleChange}
            min="0.01"
            step="0.01"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Days Back</label>
          <input
            type="number"
            name="days_back"
            value={formData.days_back}
            onChange={handleChange}
            min="1"
            max="365"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Generating...' : 'Generate Transactions'}
          </button>
        </div>
      </form>
    </div>
  );
};

const StatsCard = ({ title, value, icon, color = "blue" }) => (
  <div className={`bg-white rounded-lg shadow-md p-4 border-l-4 border-${color}-500`}>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
      <span className="text-2xl">{icon}</span>
    </div>
  </div>
);

const TransactionCard = ({ transaction }) => {
  const getStatusColor = (status) => {
    const colors = {
      completed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
      refunded: 'bg-orange-100 text-orange-800',
      disputed: 'bg-purple-100 text-purple-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getTypeIcon = (type) => {
    const icons = {
      payment: '💰',
      refund: '↩️',
      subscription: '🔄',
      dispute: '⚠️',
      chargeback: '❌'
    };
    return icons[type] || '💳';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-3 border border-gray-200">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center">
          <span className="text-lg mr-2">{getTypeIcon(transaction.transaction_type)}</span>
          <div>
            <p className="font-semibold text-gray-900">{transaction.transaction_id}</p>
            <p className="text-sm text-gray-600">{new Date(transaction.timestamp).toLocaleString()}</p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(transaction.status)}`}>
          {transaction.status}
        </span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div>
          <p><strong>Amount:</strong> {transaction.currency} {transaction.amount.toFixed(2)}</p>
          <p><strong>Fee:</strong> {transaction.currency} {transaction.fee.toFixed(2)}</p>
          <p><strong>Net:</strong> {transaction.currency} {transaction.net_amount.toFixed(2)}</p>
        </div>
        <div>
          <p><strong>From:</strong> {transaction.payer_name} ({transaction.payer_email})</p>
          <p><strong>To:</strong> {transaction.recipient_name} ({transaction.recipient_email})</p>
          <p><strong>Description:</strong> {transaction.description}</p>
        </div>
      </div>
    </div>
  );
};

const ExportSection = ({ onExport, loading }) => {
  const [exportFormat, setExportFormat] = useState('json');

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <span className="mr-2">📥</span>
        Export Transactions
      </h2>
      
      <div className="flex items-center space-x-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
          </select>
        </div>
        
        <div className="flex items-end">
          <button
            onClick={() => onExport(exportFormat)}
            disabled={loading}
            className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
          >
            {loading ? 'Exporting...' : 'Export All'}
          </button>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchTransactions();
    fetchStats();
  }, []);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions`);
      setTransactions(response.data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      showNotification('Error fetching transactions', 'error');
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/transactions/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleGenerate = async (formData) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/transactions/generate`, formData);
      showNotification(`Generated ${response.data.length} transactions successfully!`);
      await fetchTransactions();
      await fetchStats();
    } catch (error) {
      console.error('Error generating transactions:', error);
      showNotification('Error generating transactions', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/transactions/export`,
        { format },
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `transactions.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      showNotification(`Exported transactions as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Error exporting transactions:', error);
      showNotification('Error exporting transactions', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    if (window.confirm('Are you sure you want to clear all transactions?')) {
      try {
        await axios.delete(`${API}/transactions`);
        showNotification('All transactions cleared successfully!');
        await fetchTransactions();
        await fetchStats();
      } catch (error) {
        console.error('Error clearing transactions:', error);
        showNotification('Error clearing transactions', 'error');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-md text-white ${
          notification.type === 'error' ? 'bg-red-500' : 'bg-green-500'
        }`}>
          {notification.message}
        </div>
      )}
      
      <div className="container mx-auto px-4 py-6">
        <TransactionGenerator onGenerate={handleGenerate} loading={loading} />
        
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatsCard 
              title="Total Transactions" 
              value={stats.total_transactions} 
              icon="📊" 
              color="blue" 
            />
            <StatsCard 
              title="Recent (7 days)" 
              value={stats.recent_transactions} 
              icon="📈" 
              color="green" 
            />
            <StatsCard 
              title="Payment Count" 
              value={stats.by_type?.payment?.count || 0} 
              icon="💰" 
              color="yellow" 
            />
            <StatsCard 
              title="Completed" 
              value={stats.by_status?.completed || 0} 
              icon="✅" 
              color="green" 
            />
          </div>
        )}
        
        <ExportSection onExport={handleExport} loading={loading} />
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <span className="mr-2">📋</span>
              Recent Transactions ({transactions.length})
            </h2>
            <button
              onClick={handleClearAll}
              className="bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              Clear All
            </button>
          </div>
          
          {transactions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <span className="text-4xl block mb-2">📝</span>
              <p>No transactions generated yet. Use the form above to generate some!</p>
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto">
              {transactions.map((transaction) => (
                <TransactionCard key={transaction.id} transaction={transaction} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
