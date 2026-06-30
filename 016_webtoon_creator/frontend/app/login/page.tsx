'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/axios';

type Tab = 'login' | 'register';

// 다양한 에러 응답 포맷에서 메시지 추출
function extractErrorMessage(err: unknown): string | null {
  const e = err as { response?: { status?: number; data?: unknown }; message?: string };
  const data = e?.response?.data;
  if (!data) return e?.message ?? null;
  if (typeof data === 'string') {
    // Django 500 HTML 페이지 등 → 상태 코드로 안내
    return e?.response?.status ? `서버 오류가 발생했습니다. (${e.response.status})` : null;
  }
  const d = data as Record<string, unknown>;
  if (typeof d.message === 'string') return d.message;
  if (typeof d.detail === 'string') return d.detail;
  // DRF 필드 단위 오류 {"username": ["..."]} 형태
  const firstField = Object.values(d).find(v => Array.isArray(v));
  if (Array.isArray(firstField) && typeof firstField[0] === 'string') return firstField[0];
  return null;
}

// Google 로고 SVG
function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
      <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
      <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
      <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
      <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
    </svg>
  );
}

export default function LoginPage() {
  const router       = useRouter();
  const searchParams = useSearchParams();
  // 로그인 성공 후 돌아갈 경로 (미들웨어가 ?next= 로 전달)
  const nextPath     = searchParams.get('next') || '/dashboard';
  const [tab, setTab]       = useState<Tab>('login');
  const [loading, setLoading]     = useState(false);
  const [csrfReady, setCsrfReady] = useState(false);

  // 로그인 폼 상태
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });

  // 회원가입 폼 상태
  const [regForm, setRegForm] = useState({
    nickname: '', username: '', email: '', password: '', passwordConfirm: '',
  });

  // SweetAlert2 동적 임포트 (SSR 방지)
  const swal = async (opts: object) => {
    const Swal = (await import('sweetalert2')).default;
    return Swal.fire(opts as Parameters<typeof Swal.fire>[0]);
  };

  // 페이지 마운트 시 CSRF 토큰 취득 + 이미 로그인된 경우 리다이렉트
  useEffect(() => {
    api.get('/api/auth/me/')
      .then(() => router.replace(nextPath))
      .catch(() => {
        // 미로그인 — CSRF 쿠키 발급
        api.get('/api/auth/csrf/').finally(() => setCsrfReady(true));
      });
  }, [router, nextPath]);

  // ── 로그인 제출 ──────────────────────────────────────────
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csrfReady) return;
    setLoading(true);
    try {
      await api.post('/api/auth/login/', loginForm);
      router.replace(nextPath);
    } catch (err: unknown) {
      const msg = extractErrorMessage(err) ?? '로그인 중 오류가 발생했습니다.';
      await swal({ icon: 'error', title: '로그인 실패', text: msg, confirmButtonColor: '#00C73C' });
    } finally {
      setLoading(false);
    }
  };

  // ── 회원가입 제출 ────────────────────────────────────────
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csrfReady) return;

    if (regForm.password !== regForm.passwordConfirm) {
      await swal({ icon: 'warning', title: '비밀번호 불일치', text: '비밀번호와 비밀번호 확인이 일치하지 않습니다.', confirmButtonColor: '#00C73C' });
      return;
    }
    setLoading(true);
    try {
      await api.post('/api/auth/register/', {
        username: regForm.username,
        email:    regForm.email,
        password: regForm.password,
        nickname: regForm.nickname,
      });
      await swal({ icon: 'success', title: '가입 완료!', text: '환영합니다! 대시보드로 이동합니다.', confirmButtonColor: '#00C73C', timer: 1500, showConfirmButton: false });
      router.replace(nextPath);
    } catch (err: unknown) {
      const msg = extractErrorMessage(err) ?? '회원가입 중 오류가 발생했습니다.';
      await swal({ icon: 'error', title: '회원가입 실패', text: msg, confirmButtonColor: '#00C73C' });
    } finally {
      setLoading(false);
    }
  };

  // ── Google 로그인 ────────────────────────────────────────
  const handleGoogleLogin = () => {
    // 백엔드 social-auth 엔드포인트로 리다이렉트
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/login/google-oauth2/`;
  };

  // ── 공통 인풋 스타일 ─────────────────────────────────────
  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '11px 14px', fontSize: '14px',
    border: '1px solid #E8E8E8', borderRadius: '8px', outline: 'none',
    backgroundColor: '#FAFAFA', color: '#1A1A1A', transition: 'border-color 0.15s',
    boxSizing: 'border-box',
  };

  return (
    <div style={{
      minHeight: '100vh', backgroundColor: '#F8F8F8',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif",
      padding: '20px',
    }}>
      {/* 구글 폰트 로드 */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
        input:focus { border-color: #00C73C !important; background-color: #FFFFFF !important; }
        .tab-btn { transition: all 0.2s; }
        .tab-btn:hover { color: #00C73C; }
        .google-btn:hover { background-color: #f5f5f5 !important; }
        .primary-btn:hover { background-color: #00A832 !important; }
      `}</style>

      <div style={{ width: '100%', maxWidth: '420px' }}>

        {/* 로고 */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '28px', fontWeight: 900, color: '#1A1A1A', letterSpacing: '-0.5px', marginBottom: '6px' }}>
            Toon<span style={{ color: '#00C73C' }}>Craft</span>
          </div>
          <p style={{ fontSize: '13px', color: '#999999', margin: 0 }}>AI와 함께, 나만의 웹툰</p>
        </div>

        {/* 카드 */}
        <div style={{
          backgroundColor: '#FFFFFF', borderRadius: '16px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.08)', overflow: 'hidden',
        }}>
          {/* 탭 */}
          <div style={{ display: 'flex', borderBottom: '1px solid #F0F0F0' }}>
            {(['login', 'register'] as Tab[]).map(t => (
              <button key={t} onClick={() => setTab(t)} className="tab-btn"
                style={{
                  flex: 1, padding: '16px', fontSize: '14px', fontWeight: tab === t ? 700 : 400,
                  color: tab === t ? '#00C73C' : '#999999', backgroundColor: 'transparent',
                  border: 'none', cursor: 'pointer',
                  borderBottom: tab === t ? '2px solid #00C73C' : '2px solid transparent',
                }}>
                {t === 'login' ? '로그인' : '회원가입'}
              </button>
            ))}
          </div>

          <div style={{ padding: '28px 32px 32px' }}>

            {/* Google 로그인 버튼 */}
            <button onClick={handleGoogleLogin} className="google-btn"
              style={{
                width: '100%', padding: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                backgroundColor: '#FFFFFF', border: '1px solid #E8E8E8', borderRadius: '8px',
                fontSize: '14px', fontWeight: 500, color: '#1A1A1A', cursor: 'pointer',
                boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
              }}>
              <GoogleIcon />
              Google로 {tab === 'login' ? '로그인' : '시작하기'}
            </button>

            {/* 구분선 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '20px 0' }}>
              <div style={{ flex: 1, height: '1px', backgroundColor: '#F0F0F0' }}/>
              <span style={{ fontSize: '12px', color: '#BBBBBB', flexShrink: 0 }}>또는</span>
              <div style={{ flex: 1, height: '1px', backgroundColor: '#F0F0F0' }}/>
            </div>

            {/* ── 로그인 폼 ── */}
            {tab === 'login' && (
              <form onSubmit={handleLogin}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#666666', marginBottom: '5px' }}>아이디</label>
                    <input
                      type="text" placeholder="아이디를 입력하세요" required
                      value={loginForm.username}
                      onChange={e => setLoginForm(f => ({ ...f, username: e.target.value }))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#666666', marginBottom: '5px' }}>비밀번호</label>
                    <input
                      type="password" placeholder="비밀번호를 입력하세요" required
                      value={loginForm.password}
                      onChange={e => setLoginForm(f => ({ ...f, password: e.target.value }))}
                      style={inputStyle}
                    />
                  </div>
                </div>

                <button type="submit" disabled={loading} className="primary-btn"
                  style={{
                    width: '100%', padding: '13px', marginTop: '20px',
                    backgroundColor: loading ? '#CCCCCC' : '#00C73C', color: '#FFFFFF',
                    border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: 700,
                    cursor: loading ? 'not-allowed' : 'pointer',
                  }}>
                  {loading ? '로그인 중...' : '로그인'}
                </button>

                <p style={{ textAlign: 'center', fontSize: '12px', color: '#AAAAAA', marginTop: '16px' }}>
                  아직 계정이 없으신가요?{' '}
                  <button type="button" onClick={() => setTab('register')}
                    style={{ color: '#00C73C', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontSize: '12px' }}>
                    회원가입
                  </button>
                </p>
              </form>
            )}

            {/* ── 회원가입 폼 ── */}
            {tab === 'register' && (
              <form onSubmit={handleRegister}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#666666', marginBottom: '5px' }}>닉네임</label>
                    <input
                      type="text" placeholder="닉네임을 입력하세요"
                      value={regForm.nickname}
                      onChange={e => setRegForm(f => ({ ...f, nickname: e.target.value }))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#666666', marginBottom: '5px' }}>
                      아이디 <span style={{ color: '#FF4500' }}>*</span>
                    </label>
                    <input
                      type="text" placeholder="영문, 숫자 조합" required
                      value={regForm.username}
                      onChange={e => setRegForm(f => ({ ...f, username: e.target.value }))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#666666', marginBottom: '5px' }}>
                      이메일 <span style={{ color: '#FF4500' }}>*</span>
                    </label>
                    <input
                      type="email" placeholder="example@email.com" required
                      value={regForm.email}
                      onChange={e => setRegForm(f => ({ ...f, email: e.target.value }))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#666666', marginBottom: '5px' }}>
                      비밀번호 <span style={{ color: '#FF4500' }}>*</span>
                    </label>
                    <input
                      type="password" placeholder="8자 이상" required minLength={8}
                      value={regForm.password}
                      onChange={e => setRegForm(f => ({ ...f, password: e.target.value }))}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#666666', marginBottom: '5px' }}>
                      비밀번호 확인 <span style={{ color: '#FF4500' }}>*</span>
                    </label>
                    <input
                      type="password" placeholder="비밀번호를 다시 입력하세요" required
                      value={regForm.passwordConfirm}
                      onChange={e => setRegForm(f => ({ ...f, passwordConfirm: e.target.value }))}
                      style={{
                        ...inputStyle,
                        borderColor: regForm.passwordConfirm && regForm.password !== regForm.passwordConfirm ? '#FF4500' : '#E8E8E8',
                      }}
                    />
                    {regForm.passwordConfirm && regForm.password !== regForm.passwordConfirm && (
                      <p style={{ fontSize: '11px', color: '#FF4500', margin: '4px 0 0 2px' }}>비밀번호가 일치하지 않습니다.</p>
                    )}
                  </div>
                </div>

                <button type="submit" disabled={loading} className="primary-btn"
                  style={{
                    width: '100%', padding: '13px', marginTop: '20px',
                    backgroundColor: loading ? '#CCCCCC' : '#00C73C', color: '#FFFFFF',
                    border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: 700,
                    cursor: loading ? 'not-allowed' : 'pointer',
                  }}>
                  {loading ? '처리 중...' : '회원가입'}
                </button>

                <p style={{ textAlign: 'center', fontSize: '12px', color: '#AAAAAA', marginTop: '16px' }}>
                  이미 계정이 있으신가요?{' '}
                  <button type="button" onClick={() => setTab('login')}
                    style={{ color: '#00C73C', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontSize: '12px' }}>
                    로그인
                  </button>
                </p>
              </form>
            )}

          </div>
        </div>

        {/* 하단 안내 */}
        <p style={{ textAlign: 'center', fontSize: '11px', color: '#CCCCCC', marginTop: '20px' }}>
          가입 시 <span style={{ color: '#AAAAAA' }}>이용약관</span> 및 <span style={{ color: '#AAAAAA' }}>개인정보처리방침</span>에 동의합니다.
        </p>
      </div>
    </div>
  );
}
