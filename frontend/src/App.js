import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useSearchParams } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/login`, { email, password });
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
      const { access_token, admin } = response.data;
      localStorage.setItem('adminToken', access_token);
      setAdminToken(access_token);
      setAdmin(admin);
      return true;
    } catch (error) {
      console.error('Admin login error:', error);
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

  const checkTessera = async (tesseraFisica) => {
    try {
      const response = await axios.post(`${API}/check-tessera`, { tessera_fisica: tesseraFisica });
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
      const result = await checkTessera(tesseraFisica);
      
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
        setStep('register');
        setFormData({
          ...formData,
          tessera_fisica: tesseraFisica
        });
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
                Hai già una tessera ImaGross?
              </h3>
              <p className="text-gray-600 mb-6">
                Se possiedi già una tessera fisica ImaGross, inserisci il numero per verificare i tuoi dati.
              </p>
              
              <form onSubmit={handleTesseraCheck} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Numero Tessera Fisica
                  </label>
                  <input
                    type="text"
                    value={tesseraFisica}
                    onChange={(e) => setTesseraFisica(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    placeholder="es. 2020000000013"
                    required
                  />
                </div>
                
                <div className="flex space-x-4">
                  <button
                    type="submit"
                    className="flex-1 bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-3 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
                  >
                    Verifica Tessera
                  </button>
                  <button
                    type="button"
                    onClick={() => setStep('register')}
                    className="flex-1 bg-gray-500 text-white py-3 px-4 rounded-md hover:bg-gray-600 transition duration-200 font-medium"
                  >
                    Non ho tessera
                  </button>
                </div>
              </form>
            </div>
          )}

          {step === 'import' && userData && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Tessera trovata! Conferma i tuoi dati
              </h3>
              <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                Abbiamo trovato la tua tessera e importato i dati esistenti. Verifica e completa la registrazione.
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

                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-3 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
                >
                  Completa Registrazione
                </button>
              </form>
            </div>
          )}

          {step === 'register' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Registrazione Nuovo Cliente
              </h3>
              
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
                  <label className="block text-sm font-medium text-gray-700 mb-1">Numero Tessera Fisica *</label>
                  <input
                    type="text"
                    name="tessera_fisica"
                    value={formData.tessera_fisica}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
                    placeholder="es. 2020000000013"
                    required
                  />
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
                  className="w-full bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-3 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
                >
                  Registrati ora
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
  const [email, setEmail] = useState('');
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
    
    const success = await login(email, password);
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
      setEmail(formData.email);
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
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
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
  const { adminLogin } = useAuth();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    const success = await adminLogin(username, password);
    if (!success) {
      setError('Credenziali amministratore non valide');
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
              className="w-full bg-gradient-to-r from-imagross-orange to-imagross-red text-white py-2 px-4 rounded-md hover:opacity-90 transition duration-200 font-medium"
            >
              Accedi come Admin
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

// Admin Dashboard Components
const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { adminToken } = useAuth();

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats/dashboard`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento statistiche...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Dashboard Amministratore</h1>
      
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-imagross-orange rounded-lg">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Utenti Totali</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.total_users}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-imagross-green rounded-lg">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H3.862a2 2 0 01-1.995-1.858L1 7m18 0l-2-4H3L1 7m18 0H1"/>
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Supermercati</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.total_stores}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-imagross-red rounded-lg">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4z"/>
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Casse Attive</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.total_cashiers}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-500 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Registrazioni Settimana</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.recent_registrations}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-500 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7a1 1 0 00-1-1H5a1 1 0 00-1 1v1m8 0v8a1 1 0 01-1 1H5a1 1 0 01-1-1v-8"/>
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Punti Distribuiti</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.total_points_distributed}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const StoreManagement = () => {
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
    // Navigate to cashiers tab with store filter
    window.location.href = `/admin?tab=cashiers&store=${storeId}`;
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
  const { adminToken } = useAuth();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => 
    user.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.cognome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.tessera_fisica.includes(searchTerm)
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-imagross-orange mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento utenti...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Gestione Utenti</h1>
        <div className="flex space-x-4">
          <input
            type="text"
            placeholder="Cerca utenti..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-imagross-orange"
          />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Utenti ({filteredUsers.length} di {users.length})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tessera Fisica</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Punti</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supermercato</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Registrato</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{user.nome} {user.cognome}</div>
                    <div className="text-sm text-gray-500">{user.telefono}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.tessera_fisica}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                      {user.punti} punti
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.store_name || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(user.created_at).toLocaleDateString('it-IT')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      user.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.active ? 'Attivo' : 'Disattivo'}
                    </span>
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

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { admin } = useAuth();

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', component: AdminDashboard },
    { id: 'stores', name: 'Supermercati', component: StoreManagement },
    { id: 'cashiers', name: 'Casse', component: CashierManagement },
    { id: 'users', name: 'Utenti', component: UserManagement },
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || AdminDashboard;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-sm">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Admin Panel</h2>
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left px-4 py-2 rounded-md text-sm font-medium transition ${
                    activeTab === tab.id
                      ? 'bg-imagross-orange text-white'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <ActiveComponent />
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Tessera Digitale */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                La tua Tessera Digitale
              </h2>
              <div className="bg-gradient-to-r from-imagross-orange to-imagross-red rounded-lg p-6 text-white">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold">ImaGross</h3>
                    <p className="text-sm opacity-90">LOYALTY CARD</p>
                    {user.store_name && (
                      <p className="text-xs opacity-75 mt-1">{user.store_name}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{user.punti}</p>
                    <p className="text-sm">punti</p>
                  </div>
                </div>
                <div className="mb-4">
                  <p className="text-sm opacity-90">Titolare</p>
                  <p className="font-semibold">{user.nome} {user.cognome}</p>
                </div>
                <div className="text-sm opacity-90">
                  <p>Tessera: {user.tessera_digitale}</p>
                </div>
              </div>
              
              {/* QR Code */}
              <div className="mt-6 text-center">
                <p className="text-sm text-gray-600 mb-2">
                  Mostra questo codice QR alla cassa
                </p>
                <div className="bg-white p-4 rounded-lg border inline-block">
                  <img 
                    src={`data:image/png;base64,${user.qr_code}`} 
                    alt="QR Code Tessera" 
                    className="w-32 h-32 mx-auto"
                  />
                </div>
              </div>
            </div>

            {/* Informazioni Profilo */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Il tuo Profilo
              </h2>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Nome:</span>
                  <span className="font-medium">{user.nome} {user.cognome}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Email:</span>
                  <span className="font-medium">{user.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Telefono:</span>
                  <span className="font-medium">{user.telefono}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Località:</span>
                  <span className="font-medium">{user.localita}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Tessera Fisica:</span>
                  <span className="font-medium">{user.tessera_fisica}</span>
                </div>
                {user.store_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Supermercato:</span>
                    <span className="font-medium">{user.store_name}</span>
                  </div>
                )}
                {user.cashier_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Registrato via:</span>
                    <span className="font-medium">{user.cashier_name}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">Membro dal:</span>
                  <span className="font-medium">
                    {new Date(user.created_at).toLocaleDateString('it-IT')}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Hero Image */}
          <div className="mt-8 bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="relative">
              <img 
                src="https://images.unsplash.com/photo-1649767727699-3a38a00dd984?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwzfHxzaG9wcGluZyUyMHBvaW50c3xlbnwwfHx8b3JhbmdlfDE3NTM3NDY0ODh8MA&ixlib=rb-4.1.0&q=85"
                alt="Shopping" 
                className="w-full h-64 object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-imagross-orange/80 to-imagross-red/80 flex items-center justify-center">
                <div className="text-center text-white">
                  <h3 className="text-3xl font-bold mb-2">Accumula punti ad ogni spesa!</h3>
                  <p className="text-lg">Più compri, più risparmi con ImaGross</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
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

export default App;