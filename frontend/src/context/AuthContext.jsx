import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../api/services';
import { setAccessToken } from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('fixit_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Attempt silent refresh via httpOnly cookie on app load
        const res = await authService.getMe();
        setUser(res.data);
        localStorage.setItem('fixit_user', JSON.stringify(res.data));
      } catch (err) {
        setUser(null);
        localStorage.removeItem('fixit_user');
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (email, password) => {
    const res = await authService.login({ email, password });
    const { access_token, user: userData } = res.data;
    setAccessToken(access_token);
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('fixit_user', JSON.stringify(userData));
    return userData;
  };

  const register = async (userData) => {
    const res = await authService.register(userData);
    const { access_token, user: newUser } = res.data;
    setAccessToken(access_token);
    setToken(access_token);
    setUser(newUser);
    localStorage.setItem('fixit_user', JSON.stringify(newUser));
    return newUser;
  };

  const completeRegistration = async (email, code, password) => {
    const res = await authService.verifyRegistrationCode({ email, code, password });
    const { access_token, user: userData } = res.data;
    setAccessToken(access_token);
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('fixit_user', JSON.stringify(userData));
    return userData;
  };

  const logout = async () => {
    try {
      await authService.logout?.();
    } catch {
      // ignore
    }
    setAccessToken(null);
    setToken(null);
    setUser(null);
    localStorage.removeItem('fixit_user');
  };

  const refreshUser = async () => {
    try {
      const res = await authService.getMe();
      setUser(res.data);
      localStorage.setItem('fixit_user', JSON.stringify(res.data));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      isAuthenticated: !!user,
      login,
      register,
      completeRegistration,
      logout,
      refreshUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
