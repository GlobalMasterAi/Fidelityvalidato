import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useSearchParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { RewardsList, RedemptionsList, RewardAnalytics } from './RewardComponents';
import { CreateRewardModal, EditRewardModal, ProcessRedemptionModal } from './RewardModals';
import { VenditeDashboard, CustomerAnalytics } from './VenditeComponents';
import { ProductAnalytics, DepartmentAnalytics, PromotionAnalytics, ReportsGenerator } from './VenditeReports';
import AdminDashboard from './AdminDashboard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [admin, setAdmin] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [adminToken, setAdminToken] = useState(localStorage.getItem('adminToken'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else if (adminToken) {
      // Admin is logged in
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, [token, adminToken]);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/login`, { username, password });
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(user);
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const adminLogin = async (username, password) => {
    try {
      const response = await axios.post(`${API}/admin/login`, { username, password });
      
      if (response.data && response.data.access_token && response.data.admin) {
        const { access_token, admin } = response.data;
        localStorage.setItem('adminToken', access_token);
        setAdminToken(access_token);
        setAdmin(admin);
        return true;
      } else {
        console.error('Invalid response structure:', response.data);
        return false;
      }
    } catch (error) {
      console.error('Admin login error:', error);
      if (error.response) {
        console.error('Response error:', error.response.data);
        console.error('Response status:', error.response.status);
      }
      return false;
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/register`, userData);
      return { success: true, user: response.data };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.response?.data?.detail || 'Errore durante la registrazione' };
    }
  };

  const checkTessera = async (tesseraFisica, cognome = null) => {
    try {
      const payload = { tessera_fisica: tesseraFisica };
      if (cognome && cognome.trim()) {
        payload.cognome = cognome.trim();
      }
      const response = await axios.post(`${API}/check-tessera`, payload);
      return response.data;
    } catch (error) {
      console.error('Check tessera error:', error);
      return { found: false, migrated: false };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('adminToken');
    setToken(null);
    setAdminToken(null);
    setUser(null);
    setAdmin(null);
  };

  const value = {
    user,
    admin,
    login,
    adminLogin,
    register,
    checkTessera,
    logout,
    loading,
    isAuthenticated: !!user,
    isAdminAuthenticated: !!admin,
    adminToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Components
const Header = () => {
  const { user, admin, logout } = useAuth();
  
  return (
    <header className="bg-gradient-to-r from-imagross-orange to-imagross-red text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <div className="text-2xl font-bold">
            <span className="text-white">ima</span>
            <span className="text-imagross-green block text-sm">supermercati</span>
          </div>
        </div>
        {(user || admin) && (
          <div className="flex items-center space-x-4">
            <span className="text-sm">
              Ciao, {user ? user.nome : admin?.full_name}!
              {admin && <span className="ml-1 bg-yellow-500 text-black px-2 py-1 rounded text-xs">
                {admin.role === 'super_admin' ? 'SUPER ADMIN' : 'ADMIN'}
              </span>}
            </span>
            <button 
              onClick={logout}
              className="bg-white text-imagross-orange px-4 py-2 rounded hover:bg-gray-100 transition"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

const TesseraCheckPage = () => {
  const [step, setStep] = useState('check'); // 'check', 'register', 'import'
  const [tesseraFisica, setTesseraFisica] = useState('');
  const [cognomeVerifica, setCognomeVerifica] = useState(''); // For validation
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();
  const [qrInfo, setQrInfo] = useState(null);
  const { checkTessera, register } = useAuth();

  const qrCode = searchParams.get('qr');

  // Registration form state
  const [formData, setFormData] = useState({
    nome: '',
    cognome: '',
    sesso: 'M',
    email: '',
    telefono: '',
    localita: '',
    tessera_fisica: '',
    password: '',
    indirizzo: '',
    provincia: '',
    newsletter: false
  });

  useEffect(() => {
    if (qrCode) {
      fetchQRInfo();
    }
  }, [qrCode]);

  const fetchQRInfo = async () => {
    try {
      const response = await axios.get(`${API}/qr/${qrCode}`);
      setQrInfo(response.data);
    } catch (error) {
      setError('Codice QR non valido o scaduto');
    }
  };

  const handleTesseraCheck = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await checkTessera(tesseraFisica, cognomeVerifica);
      
      if (result.found) {
        if (result.migrated) {
          setError('Tessera già migrata. Puoi registrarti normalmente o aprire un ticket di supporto.');
          setStep('register');
        } else {
          setUserData(result.user_data);
          setFormData({
            ...formData,
            ...result.user_data,
            tessera_fisica: tesseraFisica
          });
          setStep('import');
        }
      } else {
        setError(result.message || 'Tessera non trovata o dati non corrispondenti');
        // Don't change step if validation failed due to cognome mismatch
        if (!result.message || !result.message.includes('combaciano')) {
          setStep('register');
          setFormData({
            ...formData,
            tessera_fisica: tesseraFisica
          });
        }
      }
    } catch (error) {
      setError('Errore durante la verifica della tessera');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value
    });
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    
    const registrationData = {
      ...formData,
      store_id: qrInfo?.store?.id,
      cashier_id: qrInfo?.cashier?.id
    };
    
    const result = await register(registrationData);
    if (result.success) {
      alert('Registrazione completata! Ora puoi accedere.');
      window.location.href = '/login';
    } else {
      setError(result.error);
    }
  };

  const openSupportTicket = () => {
    alert('Funzionalità ticket di supporto sarà disponibile a breve. Contatta il customer service.');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Verifica tessera in corso...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex items-center justify-center py-12 px-4">
        <div className="max-w-2xl w-full space-y-8">
          {qrInfo && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Benvenuto in ImaGross!
              </h2>
              <div className="bg-gradient-to-r from-imagross-orange to-imagross-red text-white p-4 rounded-lg">
                <p className="text-lg font-semibold">{qrInfo.store.name}</p>
                <p>{qrInfo.store.address}, {qrInfo.store.city}</p>
                <p className="text-sm mt-2">
                  Cassa: {qrInfo.cashier.name} (#{qrInfo.cashier.cashier_number})
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
              {error.includes('tessera già migrata') && (
                <div className="mt-2">
                  <button
                    onClick={openSupportTicket}
                    className="bg-blue-500 text-white px-4 py-2 rounded text-sm hover:bg-blue-600 transition"
                  >
                    Apri Ticket di Supporto
                  </button>
                </div>
              )}
            </div>
          )}

          {step === 'check' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                🎯 Benvenuto nel programma fedeltà ImaGross!
              </h3>
              <p className="text-gray-600 mb-6">
                Hai già una tessera fisica ImaGross? Inserisci il numero per importare automaticamente i tuoi dati, 
                oppure procedi con una nuova registrazione.
              </p>
              
              <form onSubmit={handleTesseraCheck} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Numero Tessera Fisica (opzionale)
                  </label>
                  <input
                    type="text"
                    value={tesseraFisica}
                    onChange={(e) => setTesseraFisica(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    placeholder="es. 2013000002194"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Se non hai una tessera fisica, verrà generata automaticamente
                  </p>
                </div>

                {tesseraFisica && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cognome (obbligatorio per importazione tessera) *
                    </label>
                    <input
                      type="text"
                      value={cognomeVerifica}
                      onChange={(e) => setCognomeVerifica(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                      placeholder="Inserisci il tuo cognome"
                      required={tesseraFisica.length > 0}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Il cognome deve corrispondere a quello presente nella tessera
                    </p>
                  </div>
                )}
                
                <div className="flex flex-col space-y-4">
                  {tesseraFisica && cognomeVerifica && (
                    <button
                      type="submit"
                      className="w-full bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-3 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
                    >
                      🔍 Verifica e Importa Dati Tessera
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      setTesseraFisica('');
                      setCognomeVerifica('');
                      setStep('register');
                    }}
                    className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 transition duration-200 font-medium"
                  >
                    ✨ Nuova Registrazione (senza tessera esistente)
                  </button>
                </div>
              </form>
            </div>
          )}

          {step === 'import' && userData && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                🎉 Tessera trovata! Dati importati automaticamente
              </h3>
              <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                <div className="flex items-center">
                  <span className="text-green-600 text-xl mr-2">✅</span>
                  <div>
                    <strong>Importazione completata!</strong><br/>
                    Tessera: {tesseraFisica} | 
                    Bollini: {userData.bollini || 0} | 
                    Spesa totale: €{(userData.progressivo_spesa || 0).toFixed(2)}
                  </div>
                </div>
              </div>
              
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-md mb-4">
                  <h4 className="font-medium text-gray-800 mb-2">📋 Dati importati dal sistema fedeltà:</h4>
                  <div className="text-sm text-gray-600 grid grid-cols-2 gap-2">
                    <div><strong>Nome:</strong> {formData.nome}</div>
                    <div><strong>Cognome:</strong> {formData.cognome}</div>
                    <div><strong>Telefono:</strong> {formData.telefono}</div>
                    <div><strong>Località:</strong> {formData.localita}</div>
                    <div><strong>Indirizzo:</strong> {formData.indirizzo}</div>
                    <div><strong>Provincia:</strong> {formData.provincia}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                    <input
                      type="text"
                      name="nome"
                      value={formData.nome}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Cognome *</label>
                    <input
                      type="text"
                      name="cognome"
                      value={formData.cognome}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email * (aggiorna se necessario)</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    placeholder="Inserisci la tua email"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
                    <input
                      type="tel"
                      name="telefono"
                      value={formData.telefono}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Località</label>
                    <input
                      type="text"
                      name="localita"
                      value={formData.localita}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password per accesso digitale *</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    placeholder="Crea una password per accedere online"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    💡 Per accedere potrai usare: Email, Numero Tessera o Telefono + questa password
                  </p>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="newsletter"
                    checked={formData.newsletter}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-imagross-orange focus:ring-imagross-orange border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    Mantieni le preferenze newsletter esistenti
                  </label>
                </div>

                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-3 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
                >
                  🚀 Completa Migrazione Digitale
                </button>
              </form>
            </div>
          )}

          {step === 'register' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                ✨ Nuova Registrazione Cliente
              </h3>
              <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
                <div className="flex items-center">
                  <span className="text-blue-600 text-xl mr-2">ℹ️</span>
                  <div>
                    <strong>Nuova tessera digitale</strong><br/>
                    La tua tessera fisica verrà generata automaticamente al momento della registrazione
                  </div>
                </div>
              </div>
              
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                    <input
                      type="text"
                      name="nome"
                      value={formData.nome}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Cognome *</label>
                    <input
                      type="text"
                      name="cognome"
                      value={formData.cognome}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sesso *</label>
                  <select
                    name="sesso"
                    value={formData.sesso}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    required
                  >
                    <option value="M">Maschio</option>
                    <option value="F">Femmina</option>
                    <option value="Other">Altro</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Telefono *</label>
                    <input
                      type="tel"
                      name="telefono"
                      value={formData.telefono}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Località *</label>
                    <input
                      type="text"
                      name="localita"
                      value={formData.localita}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    required
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="newsletter"
                    checked={formData.newsletter}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-imagross-orange focus:ring-imagross-orange border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    Accetto di ricevere newsletter e comunicazioni promozionali
                  </label>
                </div>

                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-3 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
                >
                  🎯 Crea Nuova Tessera Digitale
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const LoginPage = () => {
  const [username, setUsername] = useState(''); // Changed from email to username
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const { login, register } = useAuth();

  // Registration form state
  const [formData, setFormData] = useState({
    nome: '',
    cognome: '',
    sesso: 'M',
    email: '',
    telefono: '',
    localita: '',
    tessera_fisica: '',
    password: ''
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    const success = await login(username, password); // Changed from email to username
    if (!success) {
      setError('Credenziali non valide');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    
    const result = await register(formData);
    if (result.success) {
      setIsLogin(true);
      setUsername(formData.email); // Set username with email for login convenience
      setError('');
      alert('Registrazione completata! Ora puoi accedere.');
    } else {
      setError(result.error);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              {isLogin ? 'Accedi' : 'Registrati'}
            </h2>
            <p className="text-gray-600">
              {isLogin ? 'Accedi al tuo account ImaGross' : 'Crea il tuo account ImaGross'}
            </p>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {isLogin ? (
            <form className="space-y-6" onSubmit={handleLogin}>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username (Email, Tessera o Telefono)
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                  placeholder="email@esempio.com oppure 2020000028284 oppure 3331234567"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Puoi usare email, numero tessera o telefono per accedere
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-2 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
              >
                Accedi
              </button>
            </form>
          ) : (
            <form className="space-y-4" onSubmit={handleRegister}>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome
                  </label>
                  <input
                    type="text"
                    name="nome"
                    value={formData.nome}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cognome
                  </label>
                  <input
                    type="text"
                    name="cognome"
                    value={formData.cognome}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sesso
                </label>
                <select
                  name="sesso"
                  value={formData.sesso}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                  required
                >
                  <option value="M">Maschio</option>
                  <option value="F">Femmina</option>
                  <option value="Other">Altro</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefono
                </label>
                <input
                  type="tel"
                  name="telefono"
                  value={formData.telefono}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Località
                </label>
                <input
                  type="text"
                  name="localita"
                  value={formData.localita}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Numero Tessera Fisica
                </label>
                <input
                  type="text"
                  name="tessera_fisica"
                  value={formData.tessera_fisica}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                  placeholder="es. 1234567890"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-2 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
              >
                Registrati
              </button>
            </form>
          )}

          <div className="text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-imagross-orange hover:text-imagross-red transition duration-200"
            >
              {isLogin ? 'Non hai un account? Registrati' : 'Hai già un account? Accedi'}
            </button>
          </div>

          <div className="text-center mt-6">
            <a 
              href="/admin/login"
              className="text-sm text-gray-500 hover:text-imagross-orange transition duration-200"
            >
              Area Amministratori
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

const AdminLoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { adminLogin } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const success = await adminLogin(username, password);
      if (success) {
        // Successo: reindirizza alla dashboard admin
        navigate('/admin');
      } else {
        setError('Credenziali amministratore non valide');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Errore durante il login. Riprova.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Accesso Amministratori
            </h2>
            <p className="text-gray-600">
              Area riservata agli amministratori ImaGross
            </p>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleLogin}>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-2 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium disabled:opacity-50"
            >
              {loading ? 'Accesso in corso...' : 'Accedi come Admin'}
            </button>
          </form>

          <div className="text-center">
            <a 
              href="/login"
              className="text-sm text-imagross-orange hover:text-imagross-red transition duration-200"
            >
              ← Torna al login utenti
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

const ProfileManagement = ({ profile, user, onRefresh }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (profile) {
      setEditForm(profile);
    }
  }, [profile]);

  const handleInputChange = (field, value) => {
    setEditForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.put(`${API}/user/profile`, editForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.status === 200) {
        alert('Profilo aggiornato con successo!');
        setIsEditing(false);
        onRefresh(); // Refresh the profile data
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Errore nell\'aggiornamento del profilo');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setEditForm(profile);
    setIsEditing(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr.length !== 8) return '';
    const year = dateStr.slice(0, 4);
    const month = dateStr.slice(4, 6);
    const day = dateStr.slice(6, 8);
    return `${year}-${month}-${day}`;
  };

  const formatDateBack = (dateStr) => {
    if (!dateStr) return '';
    return dateStr.replace(/-/g, '');
  };

  if (!profile) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Gestione Profilo</h2>
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-imagross-orange text-white rounded-lg hover:bg-imagross-red transition-colors"
            >
              Modifica Profilo
            </button>
          ) : (
            <div className="space-x-3">
              <button
                onClick={handleCancel}
                disabled={loading}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors disabled:opacity-50"
              >
                Annulla
              </button>
              <button
                onClick={handleSave}
                disabled={loading}
                className="px-4 py-2 bg-imagross-green text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 flex items-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Salvando...
                  </>
                ) : (
                  'Salva Modifiche'
                )}
              </button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Dati Personali */}
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Dati Personali</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.nome || ''}
                    onChange={(e) => handleInputChange('nome', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.nome || 'Non specificato'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cognome</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.cognome || ''}
                    onChange={(e) => handleInputChange('cognome', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.cognome || 'Non specificato'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                {isEditing ? (
                  <input
                    type="email"
                    value={editForm.email || ''}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.email || 'Non specificato'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
                {isEditing ? (
                  <input
                    type="tel"
                    value={editForm.telefono || ''}
                    onChange={(e) => handleInputChange('telefono', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.telefono || 'Non specificato'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data di Nascita</label>
                {isEditing ? (
                  <input
                    type="date"
                    value={formatDate(editForm.data_nascita)}
                    onChange={(e) => handleInputChange('data_nascita', formatDateBack(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.data_nascita ? formatDate(profile.data_nascita) : 'Non specificato'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sesso</label>
                {isEditing ? (
                  <select
                    value={editForm.sesso || ''}
                    onChange={(e) => handleInputChange('sesso', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  >
                    <option value="">Seleziona</option>
                    <option value="M">Maschio</option>
                    <option value="F">Femmina</option>
                  </select>
                ) : (
                  <p className="text-gray-900">
                    {profile.sesso === 'M' ? 'Maschio' : profile.sesso === 'F' ? 'Femmina' : 'Non specificato'}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Indirizzo e Contatti */}
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Indirizzo e Contatti</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Indirizzo</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.indirizzo || ''}
                    onChange={(e) => handleInputChange('indirizzo', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.indirizzo || 'Non specificato'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Località</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.localita || ''}
                    onChange={(e) => handleInputChange('localita', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.localita || 'Non specificato'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Provincia</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.provincia || ''}
                    onChange={(e) => handleInputChange('provincia', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.provincia || 'Non specificato'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CAP</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.cap || ''}
                    onChange={(e) => handleInputChange('cap', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900">{profile.cap || 'Non specificato'}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dati Fidelity (Read Only) */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 border-b pb-2 mb-4">Dati Fidelity</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">Tessera Fisica</div>
            <div className="text-lg font-semibold text-imagross-orange">{profile.tessera_fisica}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">Punti Accumulati</div>
            <div className="text-lg font-semibold text-purple-600">{profile.punti || 0}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">Bollini</div>
            <div className="text-lg font-semibold text-imagross-green">{profile.bollini || 0}</div>
          </div>
        </div>
      </div>

      {/* Preferenze e Consensi */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 border-b pb-2 mb-4">Preferenze e Consensi</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">Newsletter</label>
            {isEditing ? (
              <input
                type="checkbox"
                checked={editForm.newsletter || false}
                onChange={(e) => handleInputChange('newsletter', e.target.checked)}
                className="h-4 w-4 text-imagross-orange focus:ring-imagross-orange border-gray-300 rounded"
              />
            ) : (
              <span className={`px-2 py-1 text-xs rounded-full ${profile.newsletter ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                {profile.newsletter ? 'Attiva' : 'Non attiva'}
              </span>
            )}
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">Consenso Dati Personali</label>
            <span className={`px-2 py-1 text-xs rounded-full ${profile.consenso_dati_personali ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {profile.consenso_dati_personali ? 'Accordato' : 'Non accordato'}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">Consenso Marketing</label>
            {isEditing ? (
              <input
                type="checkbox"
                checked={editForm.consenso_marketing || false}
                onChange={(e) => handleInputChange('consenso_marketing', e.target.checked)}
                className="h-4 w-4 text-imagross-orange focus:ring-imagross-orange border-gray-300 rounded"
              />
            ) : (
              <span className={`px-2 py-1 text-xs rounded-full ${profile.consenso_marketing ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                {profile.consenso_marketing ? 'Accordato' : 'Non accordato'}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const RewardsSection = ({ analytics, profile }) => {
  const [availableRewards, setAvailableRewards] = useState([]);
  const [redeemedRewards, setRedeemedRewards] = useState([]);
  const [activeTab, setActiveTab] = useState('available');

  useEffect(() => {
    generateRewards();
  }, [analytics, profile]);

  const generateRewards = () => {
    if (!analytics || !profile) return;

    const userLevel = analytics.loyalty_level;
    const totalSpent = analytics.total_spending || 0;
    const bollini = profile.bollini || 0;

    // Generate dynamic rewards based on user data
    const rewards = [
      {
        id: 1,
        title: "Sconto 10% sul prossimo acquisto",
        description: "Valido su tutti i prodotti, minimo €20",
        type: "discount",
        value: "10%",
        cost: 50,
        bolliniRequired: 50,
        available: bollini >= 50,
        category: "Sconti",
        validUntil: "2025-12-31",
        icon: "💰"
      },
      {
        id: 2,
        title: "Prodotto omaggio",
        description: "Scegli un prodotto fino a €5",
        type: "free_product",
        value: "€5",
        cost: 100,
        bolliniRequired: 100,
        available: bollini >= 100,
        category: "Omaggi",
        validUntil: "2025-12-31",
        icon: "🎁"
      },
      {
        id: 3,
        title: "Sconto VIP 20%",
        description: "Sconto esclusivo per clienti " + userLevel,
        type: "vip_discount",
        value: "20%",
        cost: 150,
        bolliniRequired: 150,
        available: bollini >= 150 && ['Gold', 'Platinum'].includes(userLevel),
        category: "VIP",
        validUntil: "2025-12-31",
        icon: "⭐"
      },
      {
        id: 4,
        title: "Buono spesa €10",
        description: "Valido su tutti i reparti",
        type: "voucher",
        value: "€10",
        cost: 200,
        bolliniRequired: 200,
        available: bollini >= 200,
        category: "Buoni",
        validUntil: "2025-12-31",
        icon: "🎫"
      },
      {
        id: 5,
        title: "Spedizione gratuita",
        description: "Per acquisti online",
        type: "free_shipping",
        value: "Gratis",
        cost: 30,
        bolliniRequired: 30,
        available: bollini >= 30,
        category: "Servizi",
        validUntil: "2025-12-31",
        icon: "🚚"
      },
      {
        id: 6,
        title: "Evento esclusivo VIP",
        description: "Accesso prioritario alle anteprime",
        type: "vip_event",
        value: "Esclusivo",
        cost: 300,
        bolliniRequired: 300,
        available: bollini >= 300 && userLevel === 'Platinum',
        category: "Eventi",
        validUntil: "2025-12-31",
        icon: "🎊"
      }
    ];

    // Offerte speciali basate sul livello
    const specialOffers = [
      {
        id: 100,
        title: "Benvenuto nuovo cliente!",
        description: "Sconto 5% sul primo acquisto",
        type: "welcome",
        value: "5%",
        cost: 0,
        bolliniRequired: 0,
        available: totalSpent < 50,
        category: "Speciali",
        validUntil: "2025-12-31",
        icon: "👋"
      },
      {
        id: 101,
        title: "Cliente fedele",
        description: "Grazie per la tua fedeltà - Sconto 15%",
        type: "loyalty",
        value: "15%",
        cost: 0,
        bolliniRequired: 0,
        available: totalSpent > 500,
        category: "Speciali",
        validUntil: "2025-12-31",
        icon: "💝"
      }
    ];

    const allRewards = [...rewards, ...specialOffers];
    setAvailableRewards(allRewards.filter(r => r.available));

    // Mock redeemed rewards
    setRedeemedRewards([
      {
        id: 200,
        title: "Sconto 5% utilizzato",
        description: "Utilizzato il 15/01/2025",
        type: "used",
        value: "5%",
        redeemedDate: "2025-01-15",
        icon: "✅"
      }
    ]);
  };

  const handleRedeemReward = async (reward) => {
    try {
      // In a real app, this would call an API
      alert(`Premio "${reward.title}" riscattato con successo! Controlla la tua email per i dettagli.`);
      
      // Move reward to redeemed list
      setRedeemedRewards(prev => [...prev, {
        ...reward,
        id: Date.now(),
        redeemedDate: new Date().toISOString().split('T')[0]
      }]);
      
      // Remove from available rewards
      setAvailableRewards(prev => prev.filter(r => r.id !== reward.id));
      
    } catch (error) {
      alert('Errore nel riscatto del premio. Riprova più tardi.');
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Sconti': 'bg-blue-100 text-blue-800',
      'Omaggi': 'bg-green-100 text-green-800',
      'VIP': 'bg-purple-100 text-purple-800',
      'Buoni': 'bg-yellow-100 text-yellow-800',
      'Servizi': 'bg-indigo-100 text-indigo-800',
      'Eventi': 'bg-pink-100 text-pink-800',
      'Speciali': 'bg-red-100 text-red-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  if (!analytics || !profile) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Premi & Offerte</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
            <div className="text-sm opacity-90">Bollini Disponibili</div>
            <div className="text-2xl font-bold">{profile.bollini || 0}</div>
          </div>
          <div className="bg-gradient-to-r from-imagross-orange to-imagross-red rounded-lg p-4 text-white">
            <div className="text-sm opacity-90">Livello Fidelity</div>
            <div className="text-xl font-bold">{analytics.loyalty_level}</div>
          </div>
          <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
            <div className="text-sm opacity-90">Premi Disponibili</div>
            <div className="text-2xl font-bold">{availableRewards.length}</div>
          </div>
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
            <div className="text-sm opacity-90">Premi Riscattati</div>
            <div className="text-2xl font-bold">{redeemedRewards.length}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('available')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === 'available' 
                ? 'bg-white text-imagross-orange shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Premi Disponibili ({availableRewards.length})
          </button>
          <button
            onClick={() => setActiveTab('redeemed')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === 'redeemed' 
                ? 'bg-white text-imagross-orange shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Premi Riscattati ({redeemedRewards.length})
          </button>
        </div>
      </div>

      {/* Rewards Grid */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        {activeTab === 'available' ? (
          <div>
            {availableRewards.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {availableRewards.map((reward) => (
                  <div key={reward.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-3xl">{reward.icon}</span>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(reward.category)}`}>
                        {reward.category}
                      </span>
                    </div>
                    
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{reward.title}</h3>
                    <p className="text-gray-600 text-sm mb-4">{reward.description}</p>
                    
                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Valore:</span>
                        <span className="font-semibold text-imagross-green">{reward.value}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Costo:</span>
                        <span className="font-semibold">{reward.bolliniRequired} bollini</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Valido fino al:</span>
                        <span className="text-gray-900">{reward.validUntil}</span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleRedeemReward(reward)}
                      disabled={!reward.available}
                      className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                        reward.available
                          ? 'bg-imagross-orange text-white hover:bg-imagross-red'
                          : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      {reward.available ? 'Riscatta Premio' : 'Bollini Insufficienti'}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🎁</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Nessun premio disponibile</h3>
                <p className="text-gray-600">Accumula più bollini per sbloccare fantastici premi!</p>
              </div>
            )}
          </div>
        ) : (
          <div>
            {redeemedRewards.length > 0 ? (
              <div className="space-y-4">
                {redeemedRewards.map((reward) => (
                  <div key={reward.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{reward.icon}</span>
                        <div>
                          <h3 className="font-semibold text-gray-900">{reward.title}</h3>
                          <p className="text-sm text-gray-600">{reward.description}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-600">Riscattato il</div>
                        <div className="font-semibold text-gray-900">{reward.redeemedDate}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📋</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Nessun premio riscattato</h3>
                <p className="text-gray-600">I premi che riscatterai appariranno qui.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* How it works */}
      <div className="bg-gradient-to-r from-imagross-orange to-imagross-red rounded-lg p-6 text-white">
        <h3 className="text-xl font-bold mb-4">Come Funziona il Sistema Premi</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-3xl mb-2">🛒</div>
            <h4 className="font-semibold mb-1">1. Fai Shopping</h4>
            <p className="text-sm opacity-90">Ogni acquisto ti fa guadagnare bollini</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">💎</div>
            <h4 className="font-semibold mb-1">2. Accumula Bollini</h4>
            <p className="text-sm opacity-90">Più spendi, più bollini guadagni</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">🎁</div>
            <h4 className="font-semibold mb-1">3. Riscatta Premi</h4>
            <p className="text-sm opacity-90">Usa i bollini per ottenere fantastici premi</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({});

  const fetchPersonalAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/user/personal-analytics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPersonalAnalytics();
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/user/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfile(response.data);
      setProfileForm(response.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const handleProfileSave = async () => {
    try {
      setProfileLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.put(`${API}/user/profile`, profileForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfile(response.data);
      setEditingProfile(false);
      alert('Profilo aggiornato con successo!');
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Errore nell\'aggiornamento del profilo');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleProfileInputChange = (field, value) => {
    setProfileForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr.length !== 8) return '';
    const year = dateStr.slice(0, 4);
    const month = dateStr.slice(4, 6);
    const day = dateStr.slice(6, 8);
    return `${year}-${month}-${day}`;
  };

  const formatDateBack = (dateStr) => {
    if (!dateStr) return '';
    return dateStr.replace(/-/g, '');
  };

  const getLoyaltyLevelColor = (level) => {
    switch(level) {
      case 'Platinum': return 'from-purple-500 to-purple-700';
      case 'Gold': return 'from-yellow-400 to-yellow-600';
      case 'Silver': return 'from-gray-400 to-gray-600';
      default: return 'from-orange-400 to-orange-600';
    }
  };

  const getLoyaltyLevelIcon = (level) => {
    switch(level) {
      case 'Platinum': return '💎';
      case 'Gold': return '🏆';
      case 'Silver': return '🥈';
      default: return '🥉';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento la tua area personale...</p>
        </div>
      </div>
    );
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Loyalty Card Digital */}
      <div className={`bg-gradient-to-r ${getLoyaltyLevelColor(analytics?.summary?.loyalty_level)} text-white rounded-xl p-6 shadow-lg relative overflow-hidden`}>
        <div className="absolute top-0 right-0 text-6xl opacity-20">
          {getLoyaltyLevelIcon(analytics?.summary?.loyalty_level)}
        </div>
        <div className="relative z-10">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-2xl font-bold">{user?.nome} {user?.cognome}</h2>
              <p className="text-lg opacity-90">{analytics?.summary?.loyalty_level} Member</p>
            </div>
            <div className="text-right">
              <div className="text-sm opacity-75">Tessera</div>
              <div className="font-mono text-lg">{user?.tessera_fisica}</div>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{user?.punti || 0}</div>
              <div className="text-sm opacity-75">Punti</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{analytics?.summary?.total_bollini || 0}</div>
              <div className="text-sm opacity-75">Bollini</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">€{analytics?.summary?.total_spent || 0}</div>
              <div className="text-sm opacity-75">Spesa Totale</div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <span className="text-2xl">🛒</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Acquisti Totali</p>
              <p className="text-2xl font-semibold text-gray-900">{analytics?.summary?.total_transactions || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <span className="text-2xl">💰</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Spesa Media</p>
              <p className="text-2xl font-semibold text-gray-900">€{analytics?.summary?.avg_transaction || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <span className="text-2xl">📅</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Frequenza</p>
              <p className="text-2xl font-semibold text-gray-900">{analytics?.summary?.shopping_frequency || 0}/mese</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 rounded-lg">
              <span className="text-2xl">🕒</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Ultimo Acquisto</p>
              <p className="text-lg font-semibold text-gray-900">
                {analytics?.summary?.days_since_last_shop === 0 ? 'Oggi' : 
                 analytics?.summary?.days_since_last_shop === 1 ? 'Ieri' :
                 `${analytics?.summary?.days_since_last_shop} giorni fa`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Achievements & Next Rewards */}
      {analytics?.achievements?.length > 0 && (
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🏆</span>
            I Tuoi Achievement
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {analytics.achievements.map((achievement, index) => (
              <div key={index} className="flex items-center p-3 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg border border-yellow-200">
                <span className="text-2xl mr-3">{achievement.icon}</span>
                <div>
                  <p className="font-semibold text-gray-900 text-sm">{achievement.name}</p>
                  <p className="text-xs text-gray-600">{achievement.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next Rewards */}
      {analytics?.next_rewards?.length > 0 && (
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🎯</span>
            Prossimi Traguardi
          </h3>
          <div className="space-y-3">
            {analytics.next_rewards.map((reward, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gradient-to-r from-imagross-orange to-imagross-red text-white rounded-lg">
                <div>
                  <p className="font-semibold">{reward.reward}</p>
                  <p className="text-sm opacity-90">{reward.description}</p>
                </div>
                <div className="text-right">
                  <span className="text-2xl">🎁</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Spending Insights */}
      {analytics?.spending_insights?.length > 0 && (
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">💡</span>
            I Tuoi Insights
          </h3>
          <div className="space-y-3">
            {analytics.spending_insights.map((insight, index) => (
              <div key={index} className={`flex items-center p-4 rounded-lg ${
                insight.type === 'positive' ? 'bg-green-50 border border-green-200' :
                insight.type === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                'bg-blue-50 border border-blue-200'
              }`}>
                <span className="text-2xl mr-3">{insight.icon}</span>
                <p className="text-gray-800">{insight.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderAnalytics = () => (
    <div className="space-y-6">
      {/* Monthly Trend Chart */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Trend Spesa Mensile</h3>
        {analytics?.monthly_trend?.length > 0 ? (
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={analytics.monthly_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#374151" fontSize={12} />
                <YAxis stroke="#374151" fontSize={12} tickFormatter={(value) => `€${value}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #d1d5db', borderRadius: '8px' }}
                  formatter={(value) => [`€${value}`, 'Spesa']}
                />
                <Line type="monotone" dataKey="spent" stroke="#F97316" strokeWidth={3} dot={{ fill: '#F97316', strokeWidth: 2, r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">Nessun dato disponibile</p>
        )}
      </div>

      {/* Shopping Patterns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">I Tuoi Pattern di Acquisto</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Giorno Preferito:</span>
              <span className="font-semibold text-imagross-orange">{analytics?.shopping_patterns?.favorite_day}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Orario Preferito:</span>
              <span className="font-semibold text-imagross-orange">{analytics?.shopping_patterns?.favorite_hour}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Giorno Top:</span>
              <span className="font-semibold text-imagross-orange">{analytics?.shopping_patterns?.peak_shopping_day}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Sfide Attive</h3>
          {analytics?.challenges?.length > 0 ? (
            <div className="space-y-4">
              {analytics.challenges.map((challenge, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-semibold text-gray-900">{challenge.name}</h4>
                    <span className="text-sm text-imagross-orange font-medium">{challenge.reward}</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{challenge.description}</p>
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                      <div 
                        className="bg-imagross-orange h-2 rounded-full" 
                        style={{ width: `${Math.min(100, (challenge.progress / challenge.target) * 100)}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {challenge.progress}/{challenge.target}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">Nessuna sfida attiva</p>
          )}
        </div>
      </div>
    </div>
  );

  const sections = [
    { id: 'overview', name: 'Panoramica', icon: '🏠' },
    { id: 'analytics', name: 'Le Tue Analytics', icon: '📊' },
    { id: 'profile', name: 'Profilo', icon: '👤' },
    { id: 'rewards', name: 'Premi & Offerte', icon: '🎁' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Ciao, {user?.nome}! 👋</h1>
              <p className="text-lg opacity-90 mt-1">Ecco la tua area personale ImaGross</p>
            </div>
            <div className="hidden md:block">
              <div className="text-right">
                <p className="text-sm opacity-75">Il tuo livello</p>
                <p className="text-2xl font-bold flex items-center justify-end">
                  {getLoyaltyLevelIcon(analytics?.summary?.loyalty_level)} {analytics?.summary?.loyalty_level}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex items-center py-4 px-2 border-b-2 font-medium text-sm ${
                  activeSection === section.id
                    ? 'border-imagross-orange text-imagross-orange'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{section.icon}</span>
                {section.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {activeSection === 'overview' && renderOverview()}
        {activeSection === 'analytics' && renderAnalytics()}
        {activeSection === 'profile' && (
          <ProfileManagement profile={profile} user={user} onRefresh={fetchUserProfile} />
        )}
        {activeSection === 'rewards' && (
          <RewardsSection analytics={analytics} profile={profile} />
        )}
      </div>
    </div>
  );
};

// Admin Dashboard Components

// AdminDashboard imported from separate file


const StoreManagement = ({ setActiveTab }) => {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    address: '',
    city: '',
    province: '',
    phone: '',
    manager_name: ''
  });
  const { adminToken } = useAuth();

  useEffect(() => {
    fetchStores();
  }, []);

  const fetchStores = async () => {
    try {
      const response = await axios.get(`${API}/admin/stores`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setStores(response.data);
    } catch (error) {
      console.error('Error fetching stores:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleCreateStore = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/stores`, formData, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      setFormData({
        name: '',
        code: '',
        address: '',
        city: '',
        province: '',
        phone: '',
        manager_name: ''
      });
      setShowCreateForm(false);
      fetchStores();
      alert('Supermercato creato con successo!');
    } catch (error) {
      alert('Errore nella creazione del supermercato: ' + error.response?.data?.detail);
    }
  };

  const goToCashiers = (storeId) => {
    // Update the activeTab to cashiers and add store filter to URL
    setActiveTab('cashiers');
    // Update URL with parameters
    const newUrl = `${window.location.pathname}?tab=cashiers&store=${storeId}`;
    window.history.pushState(null, '', newUrl);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento supermercati...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Gestione Supermercati</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-imagross-orange text-white px-4 py-2 rounded hover:bg-imagross-red transition"
        >
          + Nuovo Supermercato
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Crea Nuovo Supermercato</h2>
          <form onSubmit={handleCreateStore} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Codice</label>
              <input
                type="text"
                name="code"
                value={formData.code}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="es. IMAGROSS 1"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Indirizzo</label>
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Città</label>
              <input
                type="text"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provincia</label>
              <input
                type="text"
                name="province"
                value={formData.province}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Manager</label>
              <input
                type="text"
                name="manager_name"
                value={formData.manager_name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div className="col-span-2 flex space-x-4">
              <button
                type="submit"
                className="bg-imagross-orange text-white px-4 py-2 rounded hover:bg-imagross-red transition"
              >
                Crea Supermercato
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition"
              >
                Annulla
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Supermercati ({stores.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Codice</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Città</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Casse</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Azioni</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stores.map((store) => (
                <tr key={store.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{store.name}</div>
                    <div className="text-sm text-gray-500">{store.address}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{store.code}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{store.city}, {store.province}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      store.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {store.status === 'active' ? 'Attivo' : 'Inattivo'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{store.total_cashiers}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button 
                      onClick={() => goToCashiers(store.id)}
                      className="text-imagross-orange hover:text-imagross-red"
                    >
                      Gestisci Casse
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
};

const CashierManagement = () => {
  const [cashiers, setCashiers] = useState([]);
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [regeneratingQR, setRegeneratingQR] = useState(false);
  const [regeneratingQRId, setRegeneratingQRId] = useState(null);
  const [selectedStore, setSelectedStore] = useState('');
  const [formData, setFormData] = useState({
    store_id: '',
    cashier_number: '',
    name: ''
  });
  const { adminToken } = useAuth();

  useEffect(() => {
    fetchCashiers();
    fetchStores();
    
    // Check for store filter in URL
    const params = new URLSearchParams(window.location.search);
    const storeId = params.get('store');
    if (storeId) {
      setSelectedStore(storeId);
    }
  }, []);

  const fetchCashiers = async () => {
    try {
      const response = await axios.get(`${API}/admin/cashiers`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setCashiers(response.data);
    } catch (error) {
      console.error('Error fetching cashiers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStores = async () => {
    try {
      const response = await axios.get(`${API}/admin/stores`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setStores(response.data);
    } catch (error) {
      console.error('Error fetching stores:', error);
    }
  };

  const regenerateAllQRCodes = async () => {
    setRegeneratingQR(true);
    try {
      const response = await axios.post(`${API}/admin/regenerate-qr-codes`, {}, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      alert(`QR codes rigenerati: ${response.data.updated} di ${response.data.total_cashiers}`);
      fetchCashiers(); // Refresh the list
    } catch (error) {
      alert('Errore durante la rigenerazione dei QR codes: ' + error.response?.data?.detail);
    } finally {
      setRegeneratingQR(false);
    }
  };

  const regenerateSingleQR = async (cashierId) => {
    setRegeneratingQRId(cashierId);
    try {
      const response = await axios.post(`${API}/admin/regenerate-qr/${cashierId}`, {}, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      alert(`QR code rigenerato per: ${response.data.qr_data}`);
      fetchCashiers(); // Refresh the list
    } catch (error) {
      alert('Errore durante la rigenerazione del QR code: ' + error.response?.data?.detail);
    } finally {
      setRegeneratingQRId(null);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleCreateCashier = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/cashiers`, {
        ...formData,
        cashier_number: parseInt(formData.cashier_number)
      }, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      setFormData({
        store_id: '',
        cashier_number: '',
        name: ''
      });
      setShowCreateForm(false);
      fetchCashiers();
      alert('Cassa creata con successo!');
    } catch (error) {
      alert('Errore nella creazione della cassa: ' + error.response?.data?.detail);
    }
  };

  const printQR = (cashier) => {
    const printWindow = window.open('', '_blank');
    const qrUrl = `${window.location.origin}/register?qr=${cashier.qr_code}`;
    printWindow.document.write(`
      <html>
        <head>
          <title>QR Code - ${cashier.name}</title>
          <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
            .qr-container { display: inline-block; border: 2px solid #000; padding: 20px; margin: 20px; background: white; }
            .store-info { margin-bottom: 15px; font-size: 16px; font-weight: bold; }
            .cashier-info { margin-bottom: 15px; font-size: 14px; }
            .qr-code { margin: 10px 0; }
            .url-info { margin: 10px 0; font-size: 10px; color: #666; word-break: break-all; }
            .instructions { margin-top: 15px; font-size: 12px; color: #333; font-weight: bold; }
            @media print {
              body { margin: 0; padding: 10px; }
              .qr-container { page-break-inside: avoid; }
            }
          </style>
        </head>
        <body>
          <div class="qr-container">
            <div class="store-info">🏪 ImaGross - ${cashier.store_name}</div>
            <div class="cashier-info">💳 ${cashier.name} - Cassa #${cashier.cashier_number}</div>
            <div class="qr-code">
              <img src="data:image/png;base64,${cashier.qr_code_image}" alt="QR Code" style="width: 200px; height: 200px;"/>
            </div>
            <div class="url-info">
              URL: ${qrUrl}
            </div>
            <div class="instructions">
              📱 SCANSIONA PER REGISTRARTI<br>
              AL PROGRAMMA FEDELTÀ IMAGROSS
            </div>
            <div style="font-size: 8px; margin-top: 10px; color: #999;">
              Codice: ${cashier.qr_code} | Generato: ${new Date().toLocaleDateString('it-IT')}
            </div>
          </div>
          <script>
            window.onload = function() {
              window.print();
              window.onafterprint = function() {
                window.close();
              };
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  // Filter cashiers by selected store
  const filteredCashiers = selectedStore 
    ? cashiers.filter(cashier => cashier.store_id === selectedStore)
    : cashiers;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento casse...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Gestione Casse</h1>
        <div className="flex space-x-4">
          <select
            value={selectedStore}
            onChange={(e) => setSelectedStore(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
          >
            <option value="">Tutti i supermercati</option>
            {stores.map(store => (
              <option key={store.id} value={store.id}>{store.name}</option>
            ))}
          </select>
          <button
            onClick={regenerateAllQRCodes}
            disabled={regeneratingQR}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition disabled:opacity-50"
          >
            {regeneratingQR ? 'Rigenerando...' : '🔄 Rigenera Tutti'}
          </button>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-imagross-orange text-white px-4 py-2 rounded hover:bg-imagross-red transition"
          >
            + Nuova Cassa
          </button>
        </div>
      </div>

      {showCreateForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Crea Nuova Cassa</h2>
          <form onSubmit={handleCreateCashier} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Supermercato</label>
              <select
                name="store_id"
                value={formData.store_id}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              >
                <option value="">Seleziona supermercato</option>
                {stores.map(store => (
                  <option key={store.id} value={store.id}>{store.name} - {store.code}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Numero Cassa</label>
              <input
                type="number"
                name="cashier_number"
                value={formData.cashier_number}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                min="1"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome Cassa</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="es. Cassa 1"
                required
              />
            </div>
            <div className="flex space-x-4">
              <button
                type="submit"
                className="bg-imagross-orange text-white px-4 py-2 rounded hover:bg-imagross-red transition"
              >
                Crea Cassa
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition"
              >
                Annulla
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Casse ({filteredCashiers.length}{selectedStore ? ` filtrate di ${cashiers.length} totali` : ''})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supermercato</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Numero</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">QR Code</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Registrazioni</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Azioni</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredCashiers.map((cashier) => (
                <tr key={cashier.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{cashier.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {cashier.store_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    #{cashier.cashier_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <code className="bg-gray-100 px-2 py-1 text-xs rounded">{cashier.qr_code}</code>
                      <img 
                        src={`data:image/png;base64,${cashier.qr_code_image}`}
                        alt="QR Code"
                        className="w-8 h-8"
                        title={`QR: ${cashier.qr_code}`}
                      />
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {cashier.total_registrations}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      cashier.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {cashier.is_active ? 'Attiva' : 'Inattiva'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex flex-col space-y-1">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => {
                            const url = `${window.location.origin}/register?qr=${cashier.qr_code}`;
                            navigator.clipboard.writeText(url);
                            alert('Link di registrazione copiato!');
                          }}
                          className="text-imagross-orange hover:text-imagross-red"
                        >
                          Copia Link
                        </button>
                        <button
                          onClick={() => printQR(cashier)}
                          className="text-green-600 hover:text-green-800"
                        >
                          Stampa
                        </button>
                      </div>
                      <button
                        onClick={() => regenerateSingleQR(cashier.id)}
                        disabled={regeneratingQRId === cashier.id}
                        className="text-blue-600 hover:text-blue-800 disabled:opacity-50 text-xs"
                      >
                        {regeneratingQRId === cashier.id ? 'Rigenerando...' : '🔄 Rigenera QR'}
                      </button>
                    </div>
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

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false);
  const [isEditingUser, setIsEditingUser] = useState(false);
  const [editUserForm, setEditUserForm] = useState({});
  const [savingUser, setSavingUser] = useState(false);
  const { adminToken } = useAuth();

  const limit = 20;

  useEffect(() => {
    fetchUsers();
  }, [page, searchTerm]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/fidelity-users?page=${page}&limit=${limit}&search=${searchTerm}`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      setUsers(response.data.users);
      setTotalPages(response.data.pages);
      setTotalUsers(response.data.total);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setPage(1); // Reset to first page when searching
  };

  const handleUserClick = (user) => {
    setSelectedUser(user);
    setEditUserForm(user);
    setIsEditingUser(false);
    setShowUserModal(true);
  };

  const handleEditUser = () => {
    setIsEditingUser(true);
  };

  const handleCancelEdit = () => {
    setIsEditingUser(false);
    setEditUserForm(selectedUser);
  };

  const handleSaveUser = async () => {
    try {
      setSavingUser(true);
      
      // Prepare update data for the registered user
      const updateData = {
        nome: editUserForm.nome,
        cognome: editUserForm.cognome,
        email: editUserForm.email,
        telefono: editUserForm.telefono,
        localita: editUserForm.localita,
        indirizzo: editUserForm.indirizzo,
        provincia: editUserForm.provincia,
        sesso: editUserForm.sesso
      };

      // Find the registered user by tessera_fisica and update
      const response = await axios.put(`${API}/admin/user-profile/${editUserForm.tessera_fisica}`, updateData, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });

      if (response.status === 200) {
        // Update the local state
        setSelectedUser({...selectedUser, ...updateData});
        setUsers(users.map(user => 
          user.tessera_fisica === editUserForm.tessera_fisica 
            ? {...user, ...updateData}
            : user
        ));
        setIsEditingUser(false);
        alert('Profilo utente aggiornato con successo!');
      }
    } catch (error) {
      console.error('Error updating user:', error);
      alert('Errore nell\'aggiornamento del profilo utente. Verifica che l\'utente sia registrato nella piattaforma.');
    } finally {
      setSavingUser(false);
    }
  };

  const handleInputChange = (field, value) => {
    setEditUserForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr.length !== 8) return 'N/D';
    const year = dateStr.slice(0, 4);
    const month = dateStr.slice(4, 6);
    const day = dateStr.slice(6, 8);
    return `${day}/${month}/${year}`;
  };

  if (loading && page === 1) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento utenti fidelity...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Database Utenti Fidelity</h1>
          <p className="text-gray-600 mt-1">
            {totalUsers.toLocaleString()} utenti nel database fidelity
          </p>
        </div>
        
        {/* Search */}
        <div className="mt-4 sm:mt-0 w-full sm:w-auto">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Cerca per tessera, nome, cognome, email..."
              value={searchTerm}
              onChange={handleSearch}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full sm:w-96 focus:ring-2 focus:ring-imagross-orange focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tessera
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cliente
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contatti
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Località
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Spesa
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bollini
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Registrazione
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr 
                  key={user.tessera_fisica} 
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleUserClick(user)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-imagross-orange">
                      {user.tessera_fisica}
                    </div>
                    <div className="text-xs text-gray-500">
                      {user.negozio || 'N/D'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {user.nome} {user.cognome}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center">
                      <span className={`inline-block w-2 h-2 rounded-full mr-1 ${user.sesso === 'F' ? 'bg-pink-400' : 'bg-blue-400'}`}></span>
                      {user.sesso === 'F' ? 'Femmina' : 'Maschio'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{user.email || 'N/D'}</div>
                    <div className="text-xs text-gray-500">{user.telefono || 'N/D'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{user.localita || 'N/D'}</div>
                    <div className="text-xs text-gray-500">{user.provincia || 'N/D'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-semibold text-imagross-green">
                      €{user.progressivo_spesa.toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-purple-600">
                      {user.bollini.toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-xs text-gray-500">
                      {formatDate(user.data_creazione)}
                    </div>
                    <div className="text-xs text-gray-400">
                      {user.stato_tessera === '01' ? 'Attiva' : 'Inattiva'}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Precedente
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Successivo
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Mostrando <span className="font-medium">{((page - 1) * limit) + 1}</span> a{' '}
                <span className="font-medium">{Math.min(page * limit, totalUsers)}</span> di{' '}
                <span className="font-medium">{totalUsers}</span> risultati
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                >
                  Prec
                </button>
                <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                  {page} di {totalPages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                >
                  Succ
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* User Details Modal */}
      {showUserModal && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">
                Dettagli Utente Fidelity: {selectedUser.tessera_fisica}
              </h3>
              <button
                onClick={() => setShowUserModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Dati Anagrafici */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Dati Anagrafici</h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-600">Nome:</span>
                    {isEditingUser ? (
                      <input
                        type="text"
                        value={editUserForm.nome || ''}
                        onChange={(e) => handleInputChange('nome', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                      />
                    ) : (
                      <span className="text-gray-900">{selectedUser.nome || 'N/D'}</span>
                    )}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-600">Cognome:</span>
                    {isEditingUser ? (
                      <input
                        type="text"
                        value={editUserForm.cognome || ''}
                        onChange={(e) => handleInputChange('cognome', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                      />
                    ) : (
                      <span className="text-gray-900">{selectedUser.cognome || 'N/D'}</span>
                    )}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-600">Sesso:</span>
                    {isEditingUser ? (
                      <select
                        value={editUserForm.sesso || ''}
                        onChange={(e) => handleInputChange('sesso', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                      >
                        <option value="M">Maschio</option>
                        <option value="F">Femmina</option>
                      </select>
                    ) : (
                      <span className="text-gray-900">{selectedUser.sesso === 'F' ? 'Femmina' : 'Maschio'}</span>
                    )}
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium text-gray-600">Data Nascita:</span>
                    <span className="text-gray-900">{formatDate(selectedUser.data_nascita)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-600">Email:</span>
                    {isEditingUser ? (
                      <input
                        type="email"
                        value={editUserForm.email || ''}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                      />
                    ) : (
                      <span className="text-gray-900">{selectedUser.email || 'N/D'}</span>
                    )}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-600">Telefono:</span>
                    {isEditingUser ? (
                      <input
                        type="tel"
                        value={editUserForm.telefono || ''}
                        onChange={(e) => handleInputChange('telefono', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                      />
                    ) : (
                      <span className="text-gray-900">{selectedUser.telefono || 'N/D'}</span>
                    )}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-600">Indirizzo:</span>
                    {isEditingUser ? (
                      <input
                        type="text"
                        value={editUserForm.indirizzo || ''}
                        onChange={(e) => handleInputChange('indirizzo', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                      />
                    ) : (
                      <span className="text-gray-900">{selectedUser.indirizzo || 'N/D'}</span>
                    )}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-600">Località:</span>
                    {isEditingUser ? (
                      <input
                        type="text"
                        value={editUserForm.localita || ''}
                        onChange={(e) => handleInputChange('localita', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                      />
                    ) : (
                      <span className="text-gray-900">{selectedUser.localita || 'N/D'}</span>
                    )}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-600">Provincia:</span>
                    {isEditingUser ? (
                      <input
                        type="text"
                        value={editUserForm.provincia || ''}
                        onChange={(e) => handleInputChange('provincia', e.target.value)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm w-32"
                      />
                    ) : (
                      <span className="text-gray-900">{selectedUser.provincia || 'N/D'}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Dati Fidelity */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Dati Fidelity</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="font-medium text-gray-600">Tessera Fisica:</span>
                    <span className="text-imagross-orange font-semibold">{selectedUser.tessera_fisica}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium text-gray-600">Stato Tessera:</span>
                    <span className={selectedUser.stato_tessera === '01' ? 'text-green-600' : 'text-red-600'}>
                      {selectedUser.stato_tessera === '01' ? 'Attiva' : 'Inattiva'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium text-gray-600">Data Registrazione:</span>
                    <span className="text-gray-900">{formatDate(selectedUser.data_creazione)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium text-gray-600">Negozio Origine:</span>
                    <span className="text-gray-900">{selectedUser.negozio || 'N/D'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium text-gray-600">Progressivo Spesa:</span>
                    <span className="text-imagross-green font-bold text-lg">€{selectedUser.progressivo_spesa.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium text-gray-600">Bollini Accumulati:</span>
                    <span className="text-purple-600 font-bold text-lg">{selectedUser.bollini.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              {isEditingUser ? (
                <>
                  <button
                    onClick={handleCancelEdit}
                    disabled={savingUser}
                    className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors disabled:opacity-50"
                  >
                    Annulla
                  </button>
                  <button
                    onClick={handleSaveUser}
                    disabled={savingUser}
                    className="px-6 py-2 bg-imagross-green text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 flex items-center"
                  >
                    {savingUser ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Salvando...
                      </>
                    ) : (
                      'Salva Modifiche'
                    )}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setShowUserModal(false)}
                    className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                  >
                    Chiudi
                  </button>
                  <button
                    onClick={handleEditUser}
                    className="px-6 py-2 bg-imagross-orange text-white rounded-lg hover:bg-imagross-red transition-colors"
                  >
                    Modifica Profilo
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
const QRRegistrationPage = () => {
  return <div>QR Registration Page - Coming Soon</div>;
};

const RewardManagement = () => {
  const [activeSubTab, setActiveSubTab] = useState('overview');
  const [rewards, setRewards] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedReward, setSelectedReward] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showRedemptionModal, setShowRedemptionModal] = useState(false);
  const [selectedRedemption, setSelectedRedemption] = useState(null);
  const { adminToken } = useAuth();

  // Pagination states
  const [rewardsPage, setRewardsPage] = useState(1);
  const [redemptionsPage, setRedemptionsPage] = useState(1);
  const [rewardsTotal, setRewardsTotal] = useState(0);
  const [redemptionsTotal, setRedemptionsTotal] = useState(0);
  
  // Filter states
  const [rewardFilters, setRewardFilters] = useState({
    status: '',
    category: '',
    search: ''
  });
  const [redemptionFilters, setRedemptionFilters] = useState({
    status: '',
    reward_id: '',
    date_from: '',
    date_to: ''
  });

  const rewardCategories = [
    'Sconti', 'Omaggi', 'VIP', 'Buoni', 'Servizi', 'Eventi', 'Speciali'
  ];

  const rewardStatuses = [
    { value: 'active', label: 'Attivo' },
    { value: 'inactive', label: 'Inattivo' },
    { value: 'expired', label: 'Scaduto' },
    { value: 'out_of_stock', label: 'Esaurito' }
  ];

  const redemptionStatuses = [
    { value: 'pending', label: 'In Attesa' },
    { value: 'approved', label: 'Approvato' },
    { value: 'used', label: 'Utilizzato' },
    { value: 'rejected', label: 'Rifiutato' },
    { value: 'expired', label: 'Scaduto' }
  ];

  useEffect(() => {
    fetchData();
  }, [activeSubTab, rewardsPage, redemptionsPage, rewardFilters, redemptionFilters]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      if (activeSubTab === 'overview' || activeSubTab === 'rewards') {
        await fetchRewards();
      }
      
      if (activeSubTab === 'overview' || activeSubTab === 'redemptions') {
        await fetchRedemptions();
      }
      
      if (activeSubTab === 'overview' || activeSubTab === 'analytics') {
        await fetchAnalytics();
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRewards = async () => {
    try {
      const params = new URLSearchParams({
        page: rewardsPage.toString(),
        limit: '10'
      });
      
      // Add only non-empty filters
      if (rewardFilters.status) params.append('status', rewardFilters.status);
      if (rewardFilters.category) params.append('category', rewardFilters.category);
      if (rewardFilters.search) params.append('search', rewardFilters.search);
      
      const response = await axios.get(`${API}/admin/rewards?${params}`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      setRewards(response.data.rewards);
      setRewardsTotal(response.data.total);
    } catch (error) {
      console.error('Error fetching rewards:', error);
    }
  };

  const fetchRedemptions = async () => {
    try {
      const params = new URLSearchParams({
        page: redemptionsPage.toString(),
        limit: '10'
      });
      
      // Add only non-empty filters
      if (redemptionFilters.status) params.append('status', redemptionFilters.status);
      if (redemptionFilters.reward_id) params.append('reward_id', redemptionFilters.reward_id);
      if (redemptionFilters.date_from) params.append('date_from', redemptionFilters.date_from);
      if (redemptionFilters.date_to) params.append('date_to', redemptionFilters.date_to);
      
      const response = await axios.get(`${API}/admin/redemptions?${params}`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      setRedemptions(response.data.redemptions);
      setRedemptionsTotal(response.data.total);
    } catch (error) {
      console.error('Error fetching redemptions:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/admin/rewards/analytics`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const handleCreateReward = async (rewardData) => {
    try {
      await axios.post(`${API}/admin/rewards`, rewardData, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      alert('Premio creato con successo!');
      setShowCreateModal(false);
      fetchRewards();
    } catch (error) {
      console.error('Error creating reward:', error);
      alert('Errore nella creazione del premio');
    }
  };

  const handleEditReward = async (rewardId, updateData) => {
    try {
      await axios.put(`${API}/admin/rewards/${rewardId}`, updateData, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      alert('Premio aggiornato con successo!');
      setShowEditModal(false);
      setSelectedReward(null);
      fetchRewards();
    } catch (error) {
      console.error('Error updating reward:', error);
      alert('Errore nell\'aggiornamento del premio');
    }
  };

  const handleDeleteReward = async (rewardId) => {
    if (!confirm('Sei sicuro di voler disattivare questo premio?')) return;
    
    try {
      await axios.delete(`${API}/admin/rewards/${rewardId}`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      alert('Premio disattivato con successo!');
      fetchRewards();
    } catch (error) {
      console.error('Error deleting reward:', error);
      alert('Errore nella disattivazione del premio');
    }
  };

  const handleProcessRedemption = async (redemptionId, action, notes = '', rejectionReason = '') => {
    try {
      await axios.put(`${API}/admin/redemptions/${redemptionId}`, {
        action,
        admin_notes: notes,
        rejection_reason: rejectionReason
      }, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      const actionText = action === 'approve' ? 'approvato' : 'rifiutato';
      alert(`Riscatto ${actionText} con successo!`);
      setShowRedemptionModal(false);
      setSelectedRedemption(null);
      fetchRedemptions();
    } catch (error) {
      console.error('Error processing redemption:', error);
      alert('Errore nel processare il riscatto');
    }
  };

  const handleMarkRedemptionUsed = async (redemptionId, usageData) => {
    try {
      await axios.post(`${API}/admin/redemptions/${redemptionId}/use`, usageData, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      alert('Utilizzo registrato con successo!');
      fetchRedemptions();
    } catch (error) {
      console.error('Error marking redemption as used:', error);
      alert('Errore nella registrazione utilizzo');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      expired: 'bg-red-100 text-red-800',
      out_of_stock: 'bg-yellow-100 text-yellow-800',
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      used: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Sconti': 'bg-blue-100 text-blue-800',
      'Omaggi': 'bg-green-100 text-green-800',
      'VIP': 'bg-purple-100 text-purple-800',
      'Buoni': 'bg-yellow-100 text-yellow-800',
      'Servizi': 'bg-indigo-100 text-indigo-800',
      'Eventi': 'bg-pink-100 text-pink-800',
      'Speciali': 'bg-red-100 text-red-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const subTabs = [
    { id: 'overview', name: 'Panoramica', icon: '📊' },
    { id: 'rewards', name: 'Gestione Premi', icon: '🎁' },
    { id: 'redemptions', name: 'Riscatti', icon: '🎫' },
    { id: 'analytics', name: 'Analytics', icon: '📈' }
  ];

  if (loading && activeSubTab === 'overview') {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento gestione premi...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Gestione Premi Avanzata</h1>
            <p className="text-gray-600 mt-1">Sistema completo per la gestione premi e riscatti</p>
          </div>
          
          {activeSubTab === 'rewards' && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-imagross-orange text-white rounded-lg hover:bg-imagross-red transition-colors flex items-center"
            >
              <span className="mr-2">➕</span>
              Crea Nuovo Premio
            </button>
          )}
        </div>

        {/* Sub Navigation */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {subTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center justify-center ${
                activeSubTab === tab.id 
                  ? 'bg-white text-imagross-orange shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </div>
      </div>

      {/* Content based on active sub-tab */}
      {activeSubTab === 'overview' && (
        <RewardOverview 
          analytics={analytics}
          rewards={rewards.slice(0, 5)}
          redemptions={redemptions.slice(0, 5)}
          onViewAllRewards={() => setActiveSubTab('rewards')}
          onViewAllRedemptions={() => setActiveSubTab('redemptions')}
        />
      )}

      {activeSubTab === 'rewards' && (
        <RewardsList 
          rewards={rewards}
          total={rewardsTotal}
          page={rewardsPage}
          onPageChange={setRewardsPage}
          filters={rewardFilters}
          onFiltersChange={setRewardFilters}
          onEdit={(reward) => {
            setSelectedReward(reward);
            setShowEditModal(true);
          }}
          onDelete={handleDeleteReward}
          getStatusColor={getStatusColor}
          getCategoryColor={getCategoryColor}
          loading={loading}
        />
      )}

      {activeSubTab === 'redemptions' && (
        <RedemptionsList 
          redemptions={redemptions}
          total={redemptionsTotal}
          page={redemptionsPage}
          onPageChange={setRedemptionsPage}
          filters={redemptionFilters}
          onFiltersChange={setRedemptionFilters}
          onProcess={(redemption) => {
            setSelectedRedemption(redemption);
            setShowRedemptionModal(true);
          }}
          onMarkUsed={handleMarkRedemptionUsed}
          getStatusColor={getStatusColor}
          loading={loading}
        />
      )}

      {activeSubTab === 'analytics' && (
        <RewardAnalytics 
          analytics={analytics}
          loading={loading}
        />
      )}

      {/* Modals */}
      {showCreateModal && (
        <CreateRewardModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateReward}
          categories={rewardCategories}
        />
      )}

      {showEditModal && selectedReward && (
        <EditRewardModal
          reward={selectedReward}
          onClose={() => {
            setShowEditModal(false);
            setSelectedReward(null);
          }}
          onUpdate={handleEditReward}
          categories={rewardCategories}
        />
      )}

      {showRedemptionModal && selectedRedemption && (
        <ProcessRedemptionModal
          redemption={selectedRedemption}
          onClose={() => {
            setShowRedemptionModal(false);
            setSelectedRedemption(null);
          }}
          onProcess={handleProcessRedemption}
        />
      )}
    </div>
  );
};

const RewardOverview = ({ analytics, rewards, redemptions, onViewAllRewards, onViewAllRedemptions }) => {
  if (!analytics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white rounded-lg p-6 shadow-sm border animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    );
  }

  const { overview } = analytics;

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">Premi Totali</div>
              <div className="text-3xl font-bold">{overview.total_rewards}</div>
            </div>
            <div className="text-4xl opacity-75">🎁</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">Premi Attivi</div>
              <div className="text-3xl font-bold">{overview.active_rewards}</div>
            </div>
            <div className="text-4xl opacity-75">✅</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">Riscatti Totali</div>
              <div className="text-3xl font-bold">{overview.total_redemptions}</div>
            </div>
            <div className="text-4xl opacity-75">🎫</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">In Attesa</div>
              <div className="text-3xl font-bold">{overview.pending_redemptions}</div>
            </div>
            <div className="text-4xl opacity-75">⏳</div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Stats */}
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Premi per Categoria</h3>
          <div className="space-y-3">
            {Object.entries(analytics.category_stats).map(([category, stats]) => (
              <div key={category} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-imagross-orange"></div>
                  <span className="text-sm font-medium text-gray-700">{category}</span>
                </div>
                <div className="flex space-x-4 text-sm text-gray-600">
                  <span>Tot: {stats.total}</span>
                  <span>Attivi: {stats.active}</span>
                  <span>Riscatti: {stats.redemptions}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Attività Recente</h3>
          <div className="space-y-3">
            {redemptions.map((redemption, index) => (
              <div key={redemption.id} className="flex items-center space-x-3 p-2 bg-gray-50 rounded">
                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {redemption.reward_info?.title || 'Premio'}
                  </div>
                  <div className="text-sm text-gray-600">
                    {redemption.user_info?.nome} {redemption.user_info?.cognome}
                  </div>
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(redemption.redeemed_at).toLocaleDateString('it-IT')}
                </div>
              </div>
            ))}
          </div>
          {redemptions.length === 0 && (
            <p className="text-gray-500 text-sm">Nessuna attività recente</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Premi Recenti</h3>
          <div className="space-y-3 mb-4">
            {rewards.map((reward) => (
              <div key={reward.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{reward.icon}</span>
                  <div>
                    <div className="text-sm font-medium text-gray-900">{reward.title}</div>
                    <div className="text-xs text-gray-600">{reward.bollini_required} bollini</div>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${reward.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                  {reward.status === 'active' ? 'Attivo' : 'Inattivo'}
                </span>
              </div>
            ))}
          </div>
          <button
            onClick={onViewAllRewards}
            className="w-full px-4 py-2 text-sm bg-imagross-orange text-white rounded-lg hover:bg-imagross-red transition-colors"
          >
            Vedi Tutti i Premi
          </button>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Riscatti in Attesa</h3>
          <div className="space-y-3 mb-4">
            {redemptions.filter(r => r.status === 'pending').map((redemption) => (
              <div key={redemption.id} className="flex items-center justify-between p-2 bg-yellow-50 rounded border border-yellow-200">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {redemption.reward_info?.title || 'Premio'}
                  </div>
                  <div className="text-xs text-gray-600">
                    {redemption.user_info?.nome} {redemption.user_info?.cognome}
                  </div>
                </div>
                <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                  In Attesa
                </span>
              </div>
            ))}
          </div>
          <button
            onClick={onViewAllRedemptions}
            className="w-full px-4 py-2 text-sm bg-imagross-orange text-white rounded-lg hover:bg-imagross-red transition-colors"
          >
            Gestisci Riscatti
          </button>
        </div>
      </div>
    </div>
  );
};

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { admin, adminToken } = useAuth();

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'segmentation', name: 'Segmentazione Clienti', icon: '🎯' },
    { id: 'stores', name: 'Supermercati', icon: '🏪' },
    { id: 'cashiers', name: 'Casse', icon: '💳' },
    { id: 'users', name: 'Utenti', icon: '👥' },
    { id: 'rewards', name: 'Gestione Premi', icon: '🎁' },
    { id: 'vendite-dashboard', name: 'Dashboard Vendite', icon: '💰' },
    { id: 'customer-analytics', name: 'Analytics Clienti', icon: '👤' },
    { id: 'product-analytics', name: 'Analytics Prodotti', icon: '📦' },
    { id: 'department-analytics', name: 'Analytics Reparti', icon: '🏬' },
    { id: 'promotion-analytics', name: 'Analytics Promozioni', icon: '🎯' },
    { id: 'reports-generator', name: 'Report & Export', icon: '📋' },
    { id: 'statistics', name: 'Statistiche', icon: '📈' }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <AdminDashboard />;
      case 'segmentation':
        return <CustomerSegmentation />;
      case 'stores':
        return <StoreManagement setActiveTab={setActiveTab} />;
      case 'cashiers':
        return <CashierManagement />;
      case 'users':
        return <UserManagement />;
      case 'rewards':
        return <RewardManagement />;
      case 'vendite-dashboard':
        return <VenditeDashboard adminToken={adminToken} />;
      case 'customer-analytics':
        return <CustomerAnalytics adminToken={adminToken} />;
      case 'product-analytics':
        return <ProductAnalytics adminToken={adminToken} />;
      case 'department-analytics':
        return <DepartmentAnalytics adminToken={adminToken} />;
      case 'promotion-analytics':
        return <PromotionAnalytics adminToken={adminToken} />;
      case 'reports-generator':
        return <ReportsGenerator adminToken={adminToken} />;
      case 'statistics':
        return <div className="text-center py-12"><p className="text-gray-500">Statistiche avanzate in arrivo...</p></div>;
      default:
        return <AdminDashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-lg">
          <div className="p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-6">Admin Panel</h2>
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-imagross-orange text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span className="mr-3 text-lg">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 p-8">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

const CustomerSegmentation = () => {
  const [segmentationData, setSegmentationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [showCustomersModal, setShowCustomersModal] = useState(false);
  const { adminToken } = useAuth();

  useEffect(() => {
    fetchSegmentationData();
  }, []);

  const fetchSegmentationData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/customer-segmentation`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setSegmentationData(response.data);
    } catch (error) {
      console.error('Error fetching segmentation data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSegmentClick = (segment) => {
    setSelectedSegment(segment);
    setShowCustomersModal(true);
  };

  const getSegmentCustomers = () => {
    if (!selectedSegment || !segmentationData) return [];
    return segmentationData.customers.filter(c => c.segment === selectedSegment.name);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Analisi segmentazione clienti...</p>
        </div>
      </div>
    );
  }

  if (!segmentationData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Errore nel caricamento dei dati di segmentazione</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Segmentazione Clienti RFM</h1>
          <p className="text-gray-600 mt-1">
            Analisi di {segmentationData.total_customers.toLocaleString()} clienti basata su Recency, Frequency, Monetary
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-imagross-green">
            €{segmentationData.total_analyzed_value.toLocaleString()}
          </div>
          <div className="text-sm text-gray-500">Valore totale analizzato</div>
        </div>
      </div>

      {/* Segments Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {segmentationData.segments_summary.map((segment, index) => (
          <div
            key={segment.name}
            onClick={() => handleSegmentClick(segment)}
            className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow border-l-4"
            style={{ borderLeftColor: segment.color }}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 text-sm">{segment.name}</h3>
              <div 
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: segment.color }}
              ></div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Clienti:</span>
                <span className="font-semibold">{segment.count.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Valore Tot:</span>
                <span className="font-semibold text-imagross-green">€{segment.total_value.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Valore Medio:</span>
                <span className="font-semibold">€{segment.avg_value}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Freq. Media:</span>
                <span className="font-semibold">{segment.avg_frequency}</span>
              </div>
            </div>
            
            <div className="mt-3 pt-3 border-t border-gray-100">
              <p className="text-xs text-gray-500 leading-tight">{segment.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* RFM Analysis Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Distribuzione Segmenti</h3>
        <div style={{ width: '100%', height: 400 }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={segmentationData.segments_summary}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, count, percent }) => `${name}: ${count} (${(percent * 100).toFixed(1)}%)`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="count"
              >
                {segmentationData.segments_summary.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #d1d5db', borderRadius: '8px' }}
                formatter={(value, name) => [value, 'Clienti']}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Segment Value Comparison */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Valore per Segmento</h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={segmentationData.segments_summary} margin={{ bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="name" 
                stroke="#374151" 
                fontSize={10}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis stroke="#374151" fontSize={12} tickFormatter={(value) => `€${value.toLocaleString()}`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #d1d5db', borderRadius: '8px' }}
                formatter={(value) => [`€${value.toLocaleString()}`, 'Valore Totale']}
              />
              <Bar dataKey="total_value" radius={[4, 4, 0, 0]}>
                {segmentationData.segments_summary.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Customer Details Modal */}
      {showCustomersModal && selectedSegment && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">
                Clienti Segmento: {selectedSegment.name}
              </h3>
              <button
                onClick={() => setShowCustomersModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mb-4 p-4 rounded-lg" style={{ backgroundColor: selectedSegment.color + '20' }}>
              <p className="text-sm text-gray-700">{selectedSegment.description}</p>
              <div className="mt-2 flex space-x-6 text-sm">
                <span><strong>Clienti:</strong> {selectedSegment.count}</span>
                <span><strong>Valore Medio:</strong> €{selectedSegment.avg_value}</span>
                <span><strong>Frequenza Media:</strong> {selectedSegment.avg_frequency}</span>
              </div>
            </div>

            <div className="overflow-x-auto max-h-96">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">RFM Score</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recency</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Frequency</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Monetary</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contatti</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {getSegmentCustomers().slice(0, 50).map((customer, index) => (
                    <tr key={customer.customer_id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {customer.nome} {customer.cognome}
                        </div>
                        <div className="text-xs text-gray-500">{customer.customer_id}</div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                          {customer.rfm_score}
                        </span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        {customer.recency} giorni
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        {customer.frequency} acquisti
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-imagross-green">
                        €{customer.monetary.toLocaleString()}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>{customer.email || 'N/D'}</div>
                        <div>{customer.telefono || 'N/D'}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {getSegmentCustomers().length > 50 && (
                <div className="p-4 text-center text-gray-500 text-sm">
                  Mostrati primi 50 clienti di {getSegmentCustomers().length}
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowCustomersModal(false)}
                className="px-6 py-2 bg-imagross-orange text-white rounded-lg hover:bg-imagross-red transition-colors"
              >
                Chiudi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const AuthRoutes = () => {
  const { isAuthenticated, isAdminAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/register" element={<TesseraCheckPage />} />
      
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />} 
      />
      
      <Route 
        path="/admin/login" 
        element={isAdminAuthenticated ? <Navigate to="/admin" /> : <AdminLoginPage />} 
      />
      
      <Route 
        path="/admin/*" 
        element={isAdminAuthenticated ? <AdminPanel /> : <Navigate to="/admin/login" />} 
      />
      
      <Route 
        path="/dashboard" 
        element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} 
      />
      
      <Route 
        path="/" 
        element={<Navigate to={isAuthenticated ? "/dashboard" : (isAdminAuthenticated ? "/admin" : "/login")} />} 
      />
    </Routes>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AuthRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;