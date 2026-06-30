'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/axios';

// 루트 진입 시 로그인 여부를 확인해 적절한 페이지로 이동
export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    api.get('/api/auth/me/')
      .then(() => router.replace('/dashboard'))
      .catch(() => router.replace('/login'));
  }, [router]);

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', backgroundColor: '#f8f8f8', flexDirection: 'column', gap: '16px',
    }}>
      <div style={{
        width: '36px', height: '36px', border: '3px solid #e8e8e8',
        borderTopColor: '#00C73C', borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }}/>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <p style={{ fontSize: '13px', color: '#999999', fontFamily: 'Noto Sans KR, sans-serif' }}>
        잠시만 기다려 주세요...
      </p>
    </div>
  );
}
