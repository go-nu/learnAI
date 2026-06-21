import React, { useState } from 'react';

function GoogleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
    </svg>
  );
}

export default function Login() {
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = () => {
    setLoading(true);
    window.location.href = 'http://localhost:8000/accounts/google/login/';
  };

  return (
    <div className="min-h-screen bg-page-bg flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl w-[400px] max-w-full p-10" style={{ boxShadow: '0 12px 36px rgba(20,40,70,.10)' }}>
        {/* 로고 */}
        <div className="flex flex-col items-center gap-3 text-center mb-8">
          <span className="w-11 h-11 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-xl">리</span>
          <div>
            <div className="text-xl font-bold text-ink tracking-tight">리뷰 에이전트</div>
            <div className="text-xs text-ink2 mt-1">AI 기반 리뷰 자동 답변 서비스</div>
          </div>
        </div>

        {/* Google 로그인 버튼 */}
        <button
          onClick={handleGoogleLogin}
          disabled={loading}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-divider rounded-lg bg-white text-[#3c4043] text-sm font-semibold hover:bg-hover-bg transition-all duration-150 disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <span className="spin" />
              로그인 중...
            </>
          ) : (
            <>
              <GoogleIcon />
              Google로 계속하기
            </>
          )}
        </button>

        <p className="text-center text-xs text-ink2 mt-6">관리자 계정은 별도 문의 바랍니다</p>
      </div>
    </div>
  );
}
