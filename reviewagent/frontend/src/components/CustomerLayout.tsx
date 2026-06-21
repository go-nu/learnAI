import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function CustomerLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-page-bg">
      {/* Topbar */}
      <header className="sticky top-0 z-50 bg-surface shadow-nav h-16 flex items-center px-8">
        <div className="flex items-center gap-2.5 flex-1">
          <span className="w-7 h-7 rounded-md bg-primary block shrink-0" />
          <Link to="/products" className="font-bold text-ink text-[15px] tracking-tight no-underline">
            리뷰 에이전트
          </Link>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-ink2 font-medium">{user.name} 님</span>
          )}
          <button
            onClick={handleLogout}
            className="text-sm font-medium text-ink2 hover:text-danger transition-colors"
          >
            로그아웃
          </button>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-[1280px] mx-auto px-8 py-8">
        {children}
      </main>
    </div>
  );
}
