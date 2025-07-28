import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
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
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [token]);

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

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/register`, userData);
      return { success: true, user: response.data };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.response?.data?.detail || 'Errore durante la registrazione' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Components
const Header = () => {
  const { user, logout } = useAuth();
  
  return (
    <header className="bg-gradient-to-r from-imagross-orange to-imagross-red text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <div className="text-2xl font-bold">
            <span className="text-white">ima</span>
            <span className="text-imagross-green block text-sm">supermercati</span>
          </div>
        </div>
        {user && (
          <div className="flex items-center space-x-4">
            <span className="text-sm">Ciao, {user.nome}!</span>
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
  const { isAuthenticated, loading } = useAuth();

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
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />} 
      />
      <Route 
        path="/dashboard" 
        element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} 
      />
      <Route 
        path="/" 
        element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} 
      />
    </Routes>
  );
};

export default App;