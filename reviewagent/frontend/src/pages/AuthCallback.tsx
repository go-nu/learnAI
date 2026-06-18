import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AuthCallback() {
  const [params] = useSearchParams();
  const { login, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const access = params.get('access');
    const refresh = params.get('refresh');

    if (!access || !refresh) {
      navigate('/login', { replace: true });
      return;
    }

    login(access, refresh);
  }, []);

  useEffect(() => {
    if (!user) return;
    navigate(user.role === 'admin' ? '/admin/dashboard' : '/products', { replace: true });
  }, [user]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--page-bg)' }}>
      <span className="spin" style={{ color: 'var(--navy)', width: 32, height: 32 }} />
    </div>
  );
}
