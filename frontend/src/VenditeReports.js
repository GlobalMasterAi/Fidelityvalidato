import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const COLORS = ['#FF6B35', '#F7931E', '#FFD23F', '#06FFA5', '#3B82F6', '#8B5CF6', '#EF4444', '#10B981'];

const ProductAnalytics = ({ adminToken }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchBarcode, setSearchBarcode] = useState('');
  const [limit, setLimit] = useState(50);

  useEffect(() => {
    fetchProducts();
  }, [limit]);

  const fetchProducts = async (barcode = null) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (barcode) params.append('barcode', barcode);
      params.append('limit', limit);

      const response = await axios.get(`${API}/admin/vendite/products?${params}`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setProducts(response.data.products);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchProduct = (e) => {
    e.preventDefault();
    fetchProducts(searchBarcode.trim() || null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Controls */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🛍️ Analisi Prodotti</h3>
        <div className="flex space-x-4 mb-4">
          <form onSubmit={searchProduct} className="flex space-x-2 flex-1">
            <input
              type="text"
              value={searchBarcode}
              onChange={(e) => setSearchBarcode(e.target.value)}
              placeholder="Cerca per barcode specifico (lascia vuoto per tutti)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
            />
            <button
              type="submit"
              className="px-6 py-2 bg-imagross-orange text-white rounded-md hover:bg-imagross-red transition-colors"
            >
              Cerca
            </button>
          </form>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
          >
            <option value={25}>Top 25</option>
            <option value={50}>Top 50</option>
            <option value={100}>Top 100</option>
          </select>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Barcode</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reparto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fatturato</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantità</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prezzo Medio</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clienti</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {products.map((product, index) => (
                <tr key={product.barcode} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="w-6 h-6 bg-imagross-orange text-white rounded-full flex items-center justify-center text-xs font-bold">
                      {product.popularity_rank || index + 1}
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
                    €{product.avg_price?.toFixed(2)}
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

const DepartmentAnalytics = ({ adminToken }) => {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    try {
      const response = await axios.get(`${API}/admin/vendite/departments`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setDepartments(response.data.departments);
    } catch (error) {
      console.error('Error fetching departments:', error);
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

  return (
    <div className="space-y-6">
      {/* Department Performance Chart */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Performance Reparti</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={departments} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="reparto_name" angle={-45} textAnchor="end" height={100} />
            <YAxis />
            <Tooltip formatter={(value, name) => [
              name === 'total_revenue' ? `€${value.toLocaleString('it-IT', {minimumFractionDigits: 2})}` : value.toLocaleString(),
              name === 'total_revenue' ? 'Fatturato' : 'Quantità'
            ]} />
            <Bar dataKey="total_revenue" fill="#FF6B35" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Department Details Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {departments.map((dept, index) => (
          <div key={dept.reparto_code} className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold text-gray-900">{dept.reparto_name}</h4>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold"
                   style={{ backgroundColor: COLORS[index % COLORS.length] }}>
                {index + 1}
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Fatturato:</span>
                <span className="font-semibold text-imagross-green">
                  €{dept.total_revenue?.toLocaleString('it-IT', {minimumFractionDigits: 2})}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Quantità:</span>
                <span className="font-semibold">{dept.total_quantity?.toFixed(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Prodotti:</span>
                <span className="font-semibold">{dept.unique_products}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Clienti:</span>
                <span className="font-semibold">{dept.unique_customers}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Trans. Media:</span>
                <span className="font-semibold">€{dept.avg_transaction?.toFixed(2)}</span>
              </div>
            </div>

            {/* Top Products in Department */}
            <div className="mt-4 pt-4 border-t">
              <h5 className="text-sm font-medium text-gray-900 mb-2">Top Prodotti:</h5>
              <div className="space-y-1">
                {dept.top_products?.slice(0, 3).map((product, i) => (
                  <div key={product.barcode} className="flex justify-between text-xs">
                    <span className="text-gray-600 truncate">{product.barcode}</span>
                    <span className="font-medium">€{product.revenue?.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const PromotionAnalytics = ({ adminToken }) => {
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPromotions();
  }, []);

  const fetchPromotions = async () => {
    try {
      const response = await axios.get(`${API}/admin/vendite/promotions`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setPromotions(response.data.promotions);
    } catch (error) {
      console.error('Error fetching promotions:', error);
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

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Analisi Promozioni</h3>
        
        {promotions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Nessuna promozione trovata nei dati</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID Promozione</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Utilizzi</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sconto Tot.</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clienti</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Performance</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ROI</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {promotions.slice(0, 20).map((promo) => (
                  <tr key={promo.promotion_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {promo.promotion_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {promo.promotion_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {promo.total_usage}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-imagross-red">
                      €{promo.total_discount?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {promo.unique_customers}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-imagross-green">
                      {promo.performance_score?.toFixed(0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {promo.roi?.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

const ReportsGenerator = ({ adminToken }) => {
  const [reportType, setReportType] = useState('monthly_summary');
  const [filters, setFilters] = useState({
    month_from: '',
    month_to: '',
    department: '',
    customer: ''
  });
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateReport = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Clean filters - remove empty values
      const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([key, value]) => value.trim() !== '')
      );

      const response = await axios.post(`${API}/admin/vendite/reports`, {
        report_type: reportType,
        filters: cleanFilters
      }, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      setReportData(response.data.report);
    } catch (error) {
      console.error('Error generating report:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportData = async (format) => {
    try {
      const exportType = reportType === 'monthly_summary' ? 'customer_summary' : 'department_summary';
      const response = await axios.get(`${API}/admin/vendite/export/${exportType}?format=${format}`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      if (format === 'csv') {
        // Download CSV
        const blob = new Blob([response.data.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vendite_report_${Date.now()}.csv`;
        a.click();
      } else {
        // Download JSON
        const blob = new Blob([JSON.stringify(response.data.data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vendite_report_${Date.now()}.json`;
        a.click();
      }
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Report Generator Form */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Generatore Report</h3>
        
        <form onSubmit={generateReport} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Report</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
              >
                <option value="monthly_summary">Riepilogo Mensile</option>
                <option value="top_customers">Top Clienti</option>
                <option value="department_performance">Performance Reparti</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mese Da</label>
              <input
                type="text"
                value={filters.month_from}
                onChange={(e) => setFilters({...filters, month_from: e.target.value})}
                placeholder="202501"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mese A</label>
              <input
                type="text"
                value={filters.month_to}
                onChange={(e) => setFilters({...filters, month_to: e.target.value})}
                placeholder="202506"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Reparto</label>
              <input
                type="text"
                value={filters.department}
                onChange={(e) => setFilters({...filters, department: e.target.value})}
                placeholder="01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
              <input
                type="text"
                value={filters.customer}
                onChange={(e) => setFilters({...filters, customer: e.target.value})}
                placeholder="2020000028284"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
              />
            </div>
          </div>

          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-imagross-orange text-white rounded-md hover:bg-imagross-red transition-colors disabled:opacity-50"
            >
              {loading ? 'Generando...' : 'Genera Report'}
            </button>
            
            {reportData && (
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => exportData('json')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Export JSON
                </button>
                <button
                  type="button"
                  onClick={() => exportData('csv')}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                >
                  Export CSV
                </button>
              </div>
            )}
          </div>
        </form>
      </div>

      {/* Report Results */}
      {reportData && (
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Risultati Report</h3>
          
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-blue-600">Fatturato Totale</div>
              <div className="text-xl font-bold text-blue-900">
                €{reportData.summary.total_revenue?.toLocaleString('it-IT', {minimumFractionDigits: 2})}
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-600">Transazioni</div>
              <div className="text-xl font-bold text-green-900">
                {reportData.summary.total_transactions?.toLocaleString()}
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm text-purple-600">Clienti Unici</div>
              <div className="text-xl font-bold text-purple-900">
                {reportData.summary.unique_customers?.toLocaleString()}
              </div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-sm text-orange-600">Trans. Media</div>
              <div className="text-xl font-bold text-orange-900">
                €{reportData.summary.avg_transaction?.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Data Visualization */}
          {reportType === 'monthly_summary' && reportData.data && (
            <div className="mt-6">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={reportData.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value, name) => [
                    name === 'revenue' ? `€${value.toLocaleString('it-IT', {minimumFractionDigits: 2})}` : value.toLocaleString(),
                    name === 'revenue' ? 'Fatturato' : 'Transazioni'
                  ]} />
                  <Bar dataKey="revenue" fill="#FF6B35" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Data Table */}
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {reportData.data && reportData.data.length > 0 && 
                    Object.keys(reportData.data[0]).map((key) => (
                      <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {key.replace('_', ' ')}
                      </th>
                    ))
                  }
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reportData.data?.slice(0, 20).map((row, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    {Object.values(row).map((value, i) => (
                      <td key={i} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {typeof value === 'number' && i > 0 ? 
                          (value < 1000 ? value.toFixed(2) : value.toLocaleString()) : 
                          value
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export { ProductAnalytics, DepartmentAnalytics, PromotionAnalytics, ReportsGenerator };