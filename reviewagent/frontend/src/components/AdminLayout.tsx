import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface AdminLayoutProps { children: React.ReactNode }

const navItems = [
  { to: '/products',        label: '상품 목록' },
  { to: '/admin/dashboard', label: '대시보드' },
  { to: '/admin/reviews',   label: '리뷰 목록' },
];

export default function AdminLayout({ children }: AdminLayoutProps) {
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
        {/* 좌측: 로고 + 서비스명 + 네비 */}
        <div className="flex items-center gap-8 flex-1">
          {/* 로고 마크 + 서비스명 */}
          <div className="flex items-center gap-2.5 shrink-0">
            <span className="w-7 h-7 rounded-md bg-primary block" />
            <span className="font-bold text-ink text-[15px] tracking-tight">리뷰 에이전트</span>
          </div>

          {/* 네비 링크 */}
          <nav className="flex items-center gap-6">
            {navItems.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}

                className={({ isActive }) =>
                  isActive
                    ? 'text-primary font-semibold text-sm'
                    : 'text-ink2 font-medium text-sm hover:text-ink transition-colors'
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* 우측: 유저명 + 로그아웃 */}
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-ink2 font-medium">{user.name}</span>
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
      <main className="min-h-screen bg-page-bg p-8">
        <div className="max-w-[1280px] mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
