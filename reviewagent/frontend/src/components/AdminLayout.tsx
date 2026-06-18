import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="stage">
      <div className="app">
        <div className="layout">
          <aside className="sidebar">
            <div className="logo">리뷰 에이전트</div>
            <nav>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,.45)', letterSpacing: '0.08em', padding: '4px 14px 6px', marginTop: 4 }}>관리자</div>
              <NavLink className={({ isActive }) => `snav${isActive ? ' on' : ''}`} to="/admin/dashboard">대시보드</NavLink>
              <NavLink className={({ isActive }) => `snav${isActive ? ' on' : ''}`} to="/admin/reviews">리뷰 목록</NavLink>
              <NavLink className={({ isActive }) => `snav${isActive ? ' on' : ''}`} to="/admin/insights">인사이트</NavLink>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,.45)', letterSpacing: '0.08em', padding: '4px 14px 6px', marginTop: 12 }}>서비스</div>
              <NavLink className={({ isActive }) => `snav${isActive ? ' on' : ''}`} to="/products">상품 목록</NavLink>
            </nav>
            <div className="foot">
              <button className="btn btn-sm btn-block btn-onslate" style={{ background: 'rgba(0,0,0,.18)' }} onClick={handleLogout}>로그아웃</button>
            </div>
          </aside>
          <div className="main">{children}</div>
        </div>
      </div>
    </div>
  );
}
