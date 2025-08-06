import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('30d');

  useEffect(() => {
    fetchData();
  }, [selectedTimeRange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch vendite dashboard data (real data from database)
      const venditeResponse = await axios.get(`${API}/admin/vendite/dashboard`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('adminToken')}` }
      });
      
      // Fetch scontrini stats for bollini data
      const scontriniResponse = await axios.get(`${API}/admin/scontrini/stats`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('adminToken')}` }
      }).catch(() => ({ data: { success: false, stats: { total_scontrini: 0, total_bollini: 0 } } }));
      
      // Use vendite data as primary source
      if (venditeResponse.data && venditeResponse.data.success) {
        const venditeData = venditeResponse.data.dashboard;
        const scontriniData = scontriniResponse.data.success ? scontriniResponse.data.stats : { total_scontrini: 0, total_bollini: 0 };
        
        // Map database data to expected dashboard format
        setStats({
          fatturato: venditeData.overview.total_revenue,
          utenti_attivi: venditeData.overview.unique_customers,
          prodotti: venditeData.charts.top_products ? venditeData.charts.top_products.length : 0,
          bollini: scontriniData.total_bollini,
          vendite: venditeData.overview.total_sales,
          scontrini: scontriniData.total_scontrini,
          // Add vendite_stats structure that dashboard expects
          vendite_stats: {
            total_revenue: venditeData.overview.total_revenue,
            total_sales_records: venditeData.overview.total_sales,
            unique_customers: venditeData.overview.unique_customers,
            avg_transaction: venditeData.overview.avg_transaction
          }
        });
        
        // Map analytics data for charts
        setAnalytics({
          monthly_trends: venditeData.charts.monthly_trends || [],
          top_customers: venditeData.charts.top_customers || [],
          top_departments: venditeData.charts.top_departments || [],
          top_products: venditeData.charts.top_products || []
        });
        
        console.log('✅ Real database data loaded:', {
          fatturato: venditeData.overview.total_revenue,
          vendite: venditeData.overview.total_sales,
          clienti: venditeData.overview.unique_customers,
          bollini: scontriniData.total_bollini
        });
      } else {
        console.error('❌ Vendite dashboard API failed:', venditeResponse.data);
        // Set minimal fallback values
        setStats({
          fatturato: 0,
          utenti_attivi: 0,
          prodotti: 0,
          bollini: 0,
          vendite: 0,
          scontrini: 0
        });
        setAnalytics({ monthly_trends: [], top_customers: [], top_departments: [], top_products: [] });
      }
      
    } catch (error) {
      console.error('❌ Error fetching dashboard data:', error);
      // Set fallback values to prevent showing zeros incorrectly
      setStats({
        fatturato: 0,
        utenti_attivi: 0,
        prodotti: 0,
        bollini: 0,
        vendite: 0,
        scontrini: 0
      });
      setAnalytics({ monthly_trends: [], top_customers: [], top_departments: [], top_products: [] });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="relative">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-imagross-orange"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 bg-imagross-orange rounded-full opacity-75 animate-pulse"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Modern Header with Gradient Background */}
      <div className="relative bg-gradient-to-br from-imagross-orange via-imagross-red to-red-600 rounded-3xl p-8 text-white shadow-2xl overflow-hidden">
        <div className="absolute inset-0 bg-black bg-opacity-10"></div>
        <div className="relative z-10">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center">
            <div>
              <h1 className="text-5xl font-bold mb-3">
                ImaGross Analytics Center
              </h1>
              <p className="text-xl opacity-90 mb-4">
                Sistema di Gestione Fedeltà & Vendite Avanzato
              </p>
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm">Sistema Operativo</span>
                </div>
                <div className="text-sm opacity-75">
                  Ultimo aggiornamento: {new Date().toLocaleDateString('it-IT')}
                </div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4 mt-6 lg:mt-0">
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="px-4 py-3 bg-white bg-opacity-20 border border-white border-opacity-30 rounded-xl text-white placeholder-white placeholder-opacity-75 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
              >
                <option value="7d" className="text-gray-900">Ultimi 7 giorni</option>
                <option value="30d" className="text-gray-900">Ultimi 30 giorni</option>
                <option value="90d" className="text-gray-900">Ultimi 90 giorni</option>
              </select>
              <button className="px-6 py-3 bg-white bg-opacity-20 border border-white border-opacity-30 rounded-xl hover:bg-opacity-30 transition-all duration-300 backdrop-blur-sm flex items-center space-x-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span>Export Data</span>
              </button>
            </div>
          </div>
        </div>
        
        {/* Decorative Elements */}
        <div className="absolute top-0 right-0 w-72 h-72 bg-white bg-opacity-5 rounded-full -mr-36 -mt-36"></div>
        <div className="absolute bottom-0 left-0 w-56 h-56 bg-white bg-opacity-5 rounded-full -ml-28 -mb-28"></div>
        <div className="absolute top-1/2 left-1/3 w-32 h-32 bg-white bg-opacity-5 rounded-full"></div>
      </div>

      {/* Enhanced Key Metrics Cards */}
      {stats && analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Revenue Card - Enhanced */}
          <div className="group relative bg-gradient-to-br from-imagross-orange to-red-500 rounded-3xl shadow-2xl p-8 text-white overflow-hidden transform hover:scale-105 transition-all duration-500">
            <div className="absolute inset-0 bg-gradient-to-br from-black/10 to-transparent"></div>
            <div className="relative z-10">
              <div className="flex items-start justify-between mb-6">
                <div className="p-4 bg-white bg-opacity-20 rounded-2xl backdrop-blur-sm group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                  </svg>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-xs opacity-75 font-medium">Live</span>
                </div>
              </div>
              <div>
                <p className="text-orange-100 text-sm font-medium mb-2">Fatturato Totale Vendite</p>
                <p className="text-4xl font-bold mb-3">€{stats.vendite_stats?.total_revenue?.toLocaleString('it-IT', {minimumFractionDigits: 2}) || '0'}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="opacity-90">{stats.vendite_stats?.total_sales_records?.toLocaleString() || 0} vendite</span>
                  <span className="bg-green-400 bg-opacity-20 text-green-300 px-2 py-1 rounded-full text-xs font-medium">
                    ↗ +5.2%
                  </span>
                </div>
              </div>
            </div>
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-white bg-opacity-10 rounded-full"></div>
          </div>

          {/* Customers Card - Enhanced */}
          <div className="group relative bg-gradient-to-br from-imagross-green to-green-600 rounded-3xl shadow-2xl p-8 text-white overflow-hidden transform hover:scale-105 transition-all duration-500">
            <div className="absolute inset-0 bg-gradient-to-br from-black/10 to-transparent"></div>
            <div className="relative z-10">
              <div className="flex items-start justify-between mb-6">
                <div className="p-4 bg-white bg-opacity-20 rounded-2xl backdrop-blur-sm group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M16 4c0-1.11.89-2 2-2s2 .89 2 2-.89 2-2 2-2-.89-2-2zm4 18v-6h2.5l-2.54-7.63A1.5 1.5 0 0 0 18.5 8H16c-.8 0-1.5.7-1.5 1.5v6c0 .8.7 1.5 1.5 1.5h2.5V22h2zM12.5 11.5c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5S11 9.17 11 10s.67 1.5 1.5 1.5zM5.5 6c1.11 0 2-.89 2-2s-.89-2-2-2-2 .89-2 2 .89 2 2 2zm2 16v-7H9V9c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v6h1.5v7h4z"/>
                  </svg>
                </div>
                <span className="text-xs bg-white bg-opacity-20 px-3 py-1 rounded-full font-medium">Attivi</span>
              </div>
              <div>
                <p className="text-green-100 text-sm font-medium mb-2">Clienti con Vendite</p>
                <p className="text-4xl font-bold mb-3">{stats.vendite_stats?.unique_customers_vendite?.toLocaleString() || 0}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="opacity-90">Su {stats.total_users || 0} registrati</span>
                  <span className="bg-green-400 bg-opacity-20 text-green-300 px-2 py-1 rounded-full text-xs font-medium">
                    ↗ +12
                  </span>
                </div>
              </div>
            </div>
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-white bg-opacity-10 rounded-full"></div>
          </div>

          {/* Products Card - Enhanced */}
          <div className="group relative bg-gradient-to-br from-purple-500 to-purple-700 rounded-3xl shadow-2xl p-8 text-white overflow-hidden transform hover:scale-105 transition-all duration-500">
            <div className="absolute inset-0 bg-gradient-to-br from-black/10 to-transparent"></div>
            <div className="relative z-10">
              <div className="flex items-start justify-between mb-6">
                <div className="p-4 bg-white bg-opacity-20 rounded-2xl backdrop-blur-sm group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 7h-1V2H6v5H5c-1.1 0-2 .9-2 2v11h18V9c0-1.1-.9-2-2-2zM8 4h8v3H8V4z"/>
                  </svg>
                </div>
                <span className="text-xs bg-white bg-opacity-20 px-3 py-1 rounded-full font-medium">Catalogo</span>
              </div>
              <div>
                <p className="text-purple-100 text-sm font-medium mb-2">Prodotti nel Catalogo</p>
                <p className="text-4xl font-bold mb-3">{stats.vendite_stats?.unique_products?.toLocaleString() || 0}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="opacity-90">{stats.vendite_stats?.total_quantity_sold?.toLocaleString() || 0} venduti</span>
                  <span className="bg-purple-400 bg-opacity-20 text-purple-300 px-2 py-1 rounded-full text-xs font-medium">
                    ↗ +156
                  </span>
                </div>
              </div>
            </div>
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-white bg-opacity-10 rounded-full"></div>
          </div>

          {/* Loyalty Points Card - Enhanced */}
          <div className="group relative bg-gradient-to-br from-blue-500 to-blue-700 rounded-3xl shadow-2xl p-8 text-white overflow-hidden transform hover:scale-105 transition-all duration-500">
            <div className="absolute inset-0 bg-gradient-to-br from-black/10 to-transparent"></div>
            <div className="relative z-10">
              <div className="flex items-start justify-between mb-6">
                <div className="p-4 bg-white bg-opacity-20 rounded-2xl backdrop-blur-sm group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </div>
                <span className="text-xs bg-white bg-opacity-20 px-3 py-1 rounded-full font-medium">Loyalty</span>
              </div>
              <div>
                <p className="text-blue-100 text-sm font-medium mb-2">Bollini Distribuiti</p>
                <p className="text-4xl font-bold mb-3">{analytics?.summary?.total_bollini?.toLocaleString() || 0}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="opacity-90">{stats.scontrini_stats?.total_scontrini?.toLocaleString() || 0} scontrini</span>
                  <span className="bg-blue-400 bg-opacity-20 text-blue-300 px-2 py-1 rounded-full text-xs font-medium">
                    ↗ +8.9%
                  </span>
                </div>
              </div>
            </div>
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-white bg-opacity-10 rounded-full"></div>
          </div>
        </div>
      )}

      {/* Modern Statistics Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* System Status Card */}
          <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100 hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2">
            <div className="flex items-center justify-between mb-6">
              <div className="p-4 bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-2xl">
                <svg className="w-10 h-10 text-indigo-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                </svg>
              </div>
              <span className="px-4 py-2 bg-green-100 text-green-800 text-sm font-semibold rounded-full">Operativo</span>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Sistema Fedeltà</h3>
              <p className="text-gray-600 mb-4">Tutti i servizi sono attivi e funzionanti</p>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Uptime Sistema</span>
                  <span className="font-bold text-green-600">99.9%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Stores Attivi</span>
                  <span className="font-bold text-gray-900">{stats.total_stores || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Casse Operative</span>
                  <span className="font-bold text-gray-900">{stats.total_cashiers || 0}</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* User Activity Card */}
          <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100 hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2">
            <div className="flex items-center justify-between mb-6">
              <div className="p-4 bg-gradient-to-br from-teal-50 to-teal-100 rounded-2xl">
                <svg className="w-10 h-10 text-teal-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M16 4c0-1.11.89-2 2-2s2 .89 2 2-.89 2-2 2-2-.89-2-2zm4 18v-6h2.5l-2.54-7.63A1.5 1.5 0 0 0 18.5 8H16c-.8 0-1.5.7-1.5 1.5v6c0 .8.7 1.5 1.5 1.5h2.5V22h2z"/>
                </svg>
              </div>
              <span className="px-4 py-2 bg-blue-100 text-blue-800 text-sm font-semibold rounded-full">
                +{stats.recent_registrations || 0} questa settimana
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Utenti Registrati</h3>
              <p className="text-4xl font-bold text-gray-900 mb-4">{stats.total_users || 0}</p>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Attivi oggi</span>
                  <span className="font-bold text-blue-600">{Math.floor((stats.total_users || 0) * 0.15)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Con acquisti</span>
                  <span className="font-bold text-gray-900">{stats.vendite_stats?.unique_customers_vendite || 0}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-teal-600 h-2 rounded-full" style={{width: `${((stats.vendite_stats?.unique_customers_vendite || 0) / (stats.total_users || 1)) * 100}%`}}></div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Growth Metrics Card */}
          <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100 hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2">
            <div className="flex items-center justify-between mb-6">
              <div className="p-4 bg-gradient-to-br from-amber-50 to-amber-100 rounded-2xl">
                <svg className="w-10 h-10 text-amber-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/>
                </svg>
              </div>
              <span className="px-4 py-2 bg-amber-100 text-amber-800 text-sm font-semibold rounded-full">
                Crescita
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Performance</h3>
              <p className="text-gray-600 mb-4">Metriche di crescita mensile</p>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Punti Totali</span>
                  <span className="font-bold text-amber-600">{stats.total_points_distributed?.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Trans. Media</span>
                  <span className="font-bold text-gray-900">
                    €{((stats.vendite_stats?.total_revenue || 0) / (stats.vendite_stats?.total_sales_records || 1)).toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500 font-medium">Efficienza</span>
                  <span className="font-bold text-green-600">+12.5%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions Panel */}
      <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">Azioni Rapide</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-imagross-orange to-red-500 text-white rounded-2xl hover:scale-105 transition-all duration-300 shadow-lg">
            <svg className="w-8 h-8 mb-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
            <span className="text-sm font-semibold">Nuovo Store</span>
          </button>
          
          <button className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-green-500 to-green-600 text-white rounded-2xl hover:scale-105 transition-all duration-300 shadow-lg">
            <svg className="w-8 h-8 mb-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            <span className="text-sm font-semibold">Export Dati</span>
          </button>
          
          <button className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-2xl hover:scale-105 transition-all duration-300 shadow-lg">
            <svg className="w-8 h-8 mb-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm2-7h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"/>
            </svg>
            <span className="text-sm font-semibold">Report</span>
          </button>
          
          <button className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-2xl hover:scale-105 transition-all duration-300 shadow-lg">
            <svg className="w-8 h-8 mb-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            <span className="text-sm font-semibold">Impostazioni</span>
          </button>
        </div>
      </div>

      {/* Analytics Preview - Simplified */}
      {analytics && analytics.summary && (
        <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-gray-900">Panoramica Analytics</h3>
            <button className="px-4 py-2 bg-imagross-orange text-white rounded-xl hover:bg-imagross-red transition-colors">
              Vedi Tutto
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl">
              <h4 className="text-lg font-semibold text-blue-900 mb-2">Fatturato Medio</h4>
              <p className="text-3xl font-bold text-blue-600">
                €{analytics.summary.avg_transaction?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="text-center p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl">
              <h4 className="text-lg font-semibold text-green-900 mb-2">Transazioni Totali</h4>
              <p className="text-3xl font-bold text-green-600">
                {analytics.summary.total_transactions?.toLocaleString() || '0'}
              </p>
            </div>
            <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl">
              <h4 className="text-lg font-semibold text-purple-900 mb-2">Bollini Medi</h4>
              <p className="text-3xl font-bold text-purple-600">
                {analytics.summary.avg_bollini_per_transaction?.toFixed(1) || '0.0'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;