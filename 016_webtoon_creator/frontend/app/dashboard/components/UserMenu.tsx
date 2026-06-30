'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/axios';

type UserInfo = { id: number; username: string; email: string; nickname: string };

export default function UserMenu() {
  const router = useRouter();
  const [user, setUser]     = useState<UserInfo | null>(null);
  const [open, setOpen]     = useState(false);
  const [loading, setLoading] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // 로그인된 유저 정보 조회
  useEffect(() => {
    api.get('/api/auth/me/')
      .then(res => setUser(res.data.data))
      .catch(() => {});
  }, []);

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, []);

  // 로그아웃
  const handleLogout = async () => {
    setLoading(true);
    try {
      await api.post('/api/auth/logout/');
    } finally {
      router.replace('/login');
    }
  };

  // 회원정보수정 모달 (SweetAlert2)
  const handleEditProfile = async () => {
    setOpen(false);
    const Swal = (await import('sweetalert2')).default;

    const { value } = await Swal.fire({
      title: '회원정보 수정',
      html: `
        <div style="text-align:left;display:flex;flex-direction:column;gap:12px;margin-top:8px">
          <div>
            <label style="font-size:12px;font-weight:600;color:#666;display:block;margin-bottom:4px">닉네임</label>
            <input id="swal-nickname" class="swal2-input" placeholder="닉네임"
              value="${user?.nickname || ''}"
              style="margin:0;width:100%;box-sizing:border-box;font-size:14px" />
          </div>
          <div>
            <label style="font-size:12px;font-weight:600;color:#666;display:block;margin-bottom:4px">이메일</label>
            <input id="swal-email" class="swal2-input" type="email" placeholder="이메일"
              value="${user?.email || ''}"
              style="margin:0;width:100%;box-sizing:border-box;font-size:14px" />
          </div>
          <div>
            <label style="font-size:12px;font-weight:600;color:#666;display:block;margin-bottom:4px">새 비밀번호 (변경 시만 입력)</label>
            <input id="swal-password" class="swal2-input" type="password" placeholder="8자 이상"
              style="margin:0;width:100%;box-sizing:border-box;font-size:14px" />
          </div>
        </div>
      `,
      showCancelButton: true,
      confirmButtonText: '저장',
      cancelButtonText: '취소',
      confirmButtonColor: '#00C73C',
      preConfirm: () => ({
        nickname: (document.getElementById('swal-nickname') as HTMLInputElement)?.value.trim(),
        email:    (document.getElementById('swal-email')    as HTMLInputElement)?.value.trim(),
        password: (document.getElementById('swal-password') as HTMLInputElement)?.value.trim(),
      }),
    });

    if (!value) return;

    try {
      const payload: Record<string, string> = {};
      if (value.nickname) payload.nickname = value.nickname;
      if (value.email)    payload.email    = value.email;
      if (value.password) payload.password = value.password;

      await api.patch('/api/auth/me/', payload);
      const res = await api.get('/api/auth/me/');
      setUser(res.data.data);

      await Swal.fire({
        icon: 'success', title: '저장 완료', text: '회원정보가 수정되었습니다.',
        confirmButtonColor: '#00C73C', timer: 1500, showConfirmButton: false,
      });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })
        ?.response?.data?.message ?? '수정 중 오류가 발생했습니다.';
      await Swal.fire({ icon: 'error', title: '수정 실패', text: msg, confirmButtonColor: '#00C73C' });
    }
  };

  const initial = (user?.nickname || user?.username || 'U')[0].toUpperCase();

  return (
    <div ref={menuRef} style={{ position: 'relative' }}>
      {/* 아바타 버튼 */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '32px', height: '32px', borderRadius: '50%',
          backgroundColor: '#00C73C', color: '#FFFFFF',
          border: open ? '2px solid rgba(0,199,60,0.6)' : '2px solid transparent',
          fontSize: '13px', fontWeight: 700, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'border-color 0.15s',
        }}
      >
        {initial}
      </button>

      {/* 드롭다운 */}
      {open && (
        <div style={{
          position: 'absolute', top: '40px', right: 0, minWidth: '200px',
          backgroundColor: '#16213E', border: '1px solid #2A2A4A',
          borderRadius: '10px', boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          overflow: 'hidden', zIndex: 200,
        }}>
          {/* 유저 정보 헤더 */}
          <div style={{ padding: '14px 16px', borderBottom: '1px solid #2A2A4A' }}>
            <p style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#FFFFFF' }}>
              {user?.nickname || user?.username || '사용자'}
            </p>
            <p style={{ margin: '3px 0 0', fontSize: '12px', color: '#A0A0C0' }}>
              {user?.email || ''}
            </p>
          </div>

          {/* 메뉴 아이템 */}
          <div style={{ padding: '6px 0' }}>
            <button
              onClick={handleEditProfile}
              style={{
                width: '100%', padding: '10px 16px', textAlign: 'left',
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: '13px', color: '#A0A0C0', display: 'flex', alignItems: 'center', gap: '10px',
                transition: 'background 0.1s, color 0.1s',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#0F3460';
                (e.currentTarget as HTMLButtonElement).style.color = '#FFFFFF';
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent';
                (e.currentTarget as HTMLButtonElement).style.color = '#A0A0C0';
              }}
            >
              {/* 펜 아이콘 */}
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              회원정보 수정
            </button>

            <button
              onClick={handleLogout}
              disabled={loading}
              style={{
                width: '100%', padding: '10px 16px', textAlign: 'left',
                background: 'none', border: 'none', cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '13px', color: '#A0A0C0', display: 'flex', alignItems: 'center', gap: '10px',
                transition: 'background 0.1s, color 0.1s',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'rgba(255,80,80,0.1)';
                (e.currentTarget as HTMLButtonElement).style.color = '#FF6B6B';
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent';
                (e.currentTarget as HTMLButtonElement).style.color = '#A0A0C0';
              }}
            >
              {/* 로그아웃 아이콘 */}
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {loading ? '로그아웃 중...' : '로그아웃'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
