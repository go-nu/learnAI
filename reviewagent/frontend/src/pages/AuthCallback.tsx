import React, { useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';
import { useAuth } from '../context/AuthContext';

interface JwtPayload { role: string; exp: number; }

export default function AuthCallback() {
  const { login } = useAuth();

  useEffect(() => {
    const params  = new URLSearchParams(window.location.search);
    const access  = params.get('access');
    const refresh = params.get('refresh');
    const error   = params.get('error');

    if (error || !access || !refresh) {
      window.location.replace('/login');
      return;
    }

    try {
      login(access, refresh);
      const { role } = jwtDecode<JwtPayload>(access);
      // window.location.replace 로 전체 재로드 → AuthProvider가 localStorage에서
      // 동기적으로 user를 읽어 RequireAdmin/RequireAuth 타이밍 문제를 원천 차단
      window.location.replace(role === 'admin' ? '/admin/dashboard' : '/products');
    } catch {
      window.location.replace('/login');
    }
  }, []);

  return (
    <div className="min-h-screen bg-page-bg flex items-center justify-center">
      <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
    </div>
  );
}
