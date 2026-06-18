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
    <div className="stage">
      <div className="app">
        <div className="appbar">
          <Link className="brand" to="/products" style={{ textDecoration: 'none', color: 'inherit' }}>리뷰 에이전트</Link>
          <span className="right">
            <span>{user?.name} 님</span>
            <button className="btn btn-sm btn-onslate" onClick={handleLogout}>로그아웃</button>
          </span>
        </div>
        <div className="wrap">{children}</div>
      </div>
    </div>
  );
}
