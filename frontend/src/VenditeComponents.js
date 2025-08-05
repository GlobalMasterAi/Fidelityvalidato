import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Color palette for charts
const COLORS = ['#FF6B35', '#F7931E', '#FFD23F', '#06FFA5', '#3B82F6', '#8B5CF6', '#EF4444', '#10B981'];

const VenditeDashboard = ({ adminToken }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      console.log('AdminToken:', adminToken); // Debug
      if (!adminToken) {
        console.error('No admin token available');
        return;
      }
      
      const response = await axios.get(`${API}/admin/vendite/dashboard`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setDashboardData(response.data.dashboard);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      console.error('Error details:', error.response?.data);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange"></div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-500">Errore nel caricamento della dashboard vendite</p>
        <p className="text-sm text-gray-400 mt-2">
          Token: {adminToken ? 'Presente' : 'Mancante'} | API: {API}
        </p>
        <button 
          onClick={fetchDashboardData}
          className="mt-4 px-4 py-2 bg-imagross-orange text-white rounded-md hover:bg-imagross-red"
        >
          Riprova
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <div className="text-sm opacity-90">Vendite Totali</div>
          <div className="text-2xl font-bold">{dashboardData.overview.total_sales?.toLocaleString()}</div>
        </div>
        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
          <div className="text-sm opacity-90">Clienti Unici</div>
          <div className="text-2xl font-bold">{dashboardData.overview.unique_customers?.toLocaleString()}</div>
        </div>
        <div className="bg-gradient-to-r from-imagross-orange to-imagross-red rounded-lg p-6 text-white">
          <div className="text-sm opacity-90">Fatturato Totale</div>
          <div className="text-2xl font-bold">€{dashboardData.overview.total_revenue?.toLocaleString('it-IT', {minimumFractionDigits: 2})}</div>
        </div>
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
          <div className="text-sm opacity-90">Transazione Media</div>
          <div className="text-2xl font-bold">€{dashboardData.overview.avg_transaction?.toFixed(2)}</div>
        </div>
      </div>

      {/* Monthly Trends Chart */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Andamento Mensile</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dashboardData.monthly_trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip formatter={(value, name) => [
              name === 'revenue' ? `€${value.toLocaleString('it-IT', {minimumFractionDigits: 2})}` : value.toLocaleString(),
              name === 'revenue' ? 'Fatturato' : 'Transazioni'
            ]} />
            <Bar yAxisId="left" dataKey="revenue" fill="#FF6B35" name="revenue" />
            <Line yAxisId="right" type="monotone" dataKey="transactions" stroke="#3B82F6" name="transactions" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Customers */}
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">👑 Top Clienti (Mese Corrente)</h3>
          <div className="space-y-3">
            {dashboardData.top_customers?.slice(0, 10).map((customer, index) => (
              <div key={customer.codice_cliente} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-imagross-orange text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{customer.codice_cliente}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-imagross-green">€{customer.spent?.toFixed(2)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Departments */}
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🏪 Top Reparti</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={dashboardData.top_departments?.slice(0, 5)}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="total_revenue"
                nameKey="reparto_name"
              >
                {dashboardData.top_departments?.slice(0, 5).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [`€${value.toLocaleString('it-IT', {minimumFractionDigits: 2})}`, 'Fatturato']} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
            {dashboardData.top_departments?.slice(0, 5).map((dept, index) => (
              <div key={dept.reparto_code} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                ></div>
                <span className="truncate">{dept.reparto_name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Products */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🛍️ Top Prodotti</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Barcode</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reparto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fatturato</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantità</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clienti</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {dashboardData.top_products?.slice(0, 10).map((product, index) => (
                <tr key={product.barcode} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="w-6 h-6 bg-imagross-orange text-white rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {product.barcode}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {product.reparto}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-imagross-green">
                    €{product.total_revenue?.toLocaleString('it-IT', {minimumFractionDigits: 2})}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {product.total_quantity?.toFixed(0)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {product.unique_customers}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const CustomerAnalytics = ({ adminToken }) => {
  const [customerCode, setCustomerCode] = useState('');
  const [customerData, setCustomerData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchCustomer = async (e) => {
    e.preventDefault();
    if (!customerCode.trim()) return;

    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`${API}/admin/vendite/customer/${customerCode}`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setCustomerData(response.data.analytics);
    } catch (error) {
      setError('Cliente non trovato o errore nel caricamento dati');
      setCustomerData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🔍 Ricerca Cliente</h3>
        <form onSubmit={searchCustomer} className="flex space-x-4">
          <input
            type="text"
            value={customerCode}
            onChange={(e) => setCustomerCode(e.target.value)}
            placeholder="Inserisci codice cliente (es. 2020000028284)"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-imagross-orange text-white rounded-md hover:bg-imagross-red transition-colors disabled:opacity-50"
          >
            {loading ? 'Caricamento...' : 'Cerca'}
          </button>
        </form>
        
        {error && (
          <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>

      {/* Customer Analytics Results */}
      {customerData && (
        <div className="space-y-6">
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
              <div className="text-sm opacity-90">Spesa Totale</div>
              <div className="text-2xl font-bold">€{customerData.total_spent?.toFixed(2)}</div>
            </div>
            <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
              <div className="text-sm opacity-90">Transazioni</div>
              <div className="text-2xl font-bold">{customerData.total_transactions}</div>
            </div>
            <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
              <div className="text-sm opacity-90">Bollini</div>
              <div className="text-2xl font-bold">{customerData.total_bollini}</div>
            </div>
            <div className="bg-gradient-to-r from-imagross-orange to-imagross-red rounded-lg p-6 text-white">
              <div className="text-sm opacity-90">Segmento</div>
              <div className="text-2xl font-bold">{customerData.customer_segment}</div>
            </div>
          </div>

          {/* Customer Details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Monthly Trends */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Andamento Mensile</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={customerData.monthly_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`€${value.toFixed(2)}`, 'Spesa']} />
                  <Bar dataKey="spent" fill="#FF6B35" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Favorite Products */}
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🛍️ Prodotti Preferiti</h3>
              <div className="space-y-3">
                {customerData.favorite_products?.slice(0, 5).map((product, index) => (
                  <div key={product.barcode} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-6 h-6 bg-imagross-orange text-white rounded-full flex items-center justify-center text-xs font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{product.barcode}</div>
                        <div className="text-sm text-gray-500">Qtà: {product.quantity?.toFixed(1)}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-imagross-green">€{product.spent?.toFixed(2)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export { VenditeDashboard, CustomerAnalytics };