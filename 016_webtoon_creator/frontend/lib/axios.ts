import axios from 'axios';

// 브라우저 쿠키에서 특정 이름의 값을 읽는 헬퍼
function getCookie(name: string): string {
  if (typeof document === 'undefined') return '';
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : '';
}

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true,          // 세션 쿠키 자동 포함
  headers: { 'Content-Type': 'application/json' },
});

// 요청 인터셉터: POST/PUT/PATCH/DELETE 에 CSRF 토큰 자동 첨부
api.interceptors.request.use((config) => {
  const method = (config.method ?? '').toLowerCase();
  if (['post', 'put', 'patch', 'delete'].includes(method)) {
    const csrf = getCookie('csrftoken');
    if (csrf) config.headers['X-CSRFToken'] = csrf;
  }
  return config;
});

// 응답 인터셉터: 401 → 세션 만료, 로그인 페이지로 이동
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && typeof window !== 'undefined') {
      const isLoginPage = window.location.pathname === '/login';
      if (!isLoginPage) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

export default api;
