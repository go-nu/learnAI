import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import AuthCallback from './pages/AuthCallback';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Dashboard from './pages/admin/Dashboard';
import ReviewList from './pages/admin/ReviewList';
import ReviewDetail from './pages/admin/ReviewDetail';
import Insights from './pages/admin/Insights';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'admin') return <Navigate to="/products" replace />;
  return <>{children}</>;
}

function RootRedirect() {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={user?.role === 'admin' ? '/admin/dashboard' : '/products'} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<Login />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/products" element={<RequireAuth><Products /></RequireAuth>} />
          <Route path="/products/:id" element={<RequireAuth><ProductDetail /></RequireAuth>} />
          <Route path="/admin/dashboard" element={<RequireAdmin><Dashboard /></RequireAdmin>} />
          <Route path="/admin/reviews" element={<RequireAdmin><ReviewList /></RequireAdmin>} />
          <Route path="/admin/reviews/:id" element={<RequireAdmin><ReviewDetail /></RequireAdmin>} />
          <Route path="/admin/insights" element={<RequireAdmin><Insights /></RequireAdmin>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
