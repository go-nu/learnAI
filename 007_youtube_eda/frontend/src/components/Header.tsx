'use client';

import { useRouter } from 'next/navigation';

export default function Header() {
  const router = useRouter();

  const handleLogin = async () => {
    const Swal = (await import('sweetalert2')).default;
    const { value } = await Swal.fire({
      title: '로그인',
      html: `
        <div style="text-align:left;font-family:'Nanum Gothic',sans-serif">
          <label style="display:block;font-size:12px;font-weight:700;color:#374151;margin-bottom:4px">아이디</label>
          <input id="swal-id" class="swal2-input" placeholder="아이디를 입력하세요" style="font-size:13px;margin-bottom:8px"/>
          <label style="display:block;font-size:12px;font-weight:700;color:#374151;margin-bottom:4px">비밀번호</label>
          <input id="swal-pw" type="password" class="swal2-input" placeholder="비밀번호를 입력하세요" style="font-size:13px"/>
        </div>
      `,
      showCancelButton: true,
      confirmButtonColor: '#FF0000',
      cancelButtonColor: '#9CA3AF',
      confirmButtonText: '로그인',
      cancelButtonText: '취소',
      preConfirm: () => {
        const id = (document.getElementById('swal-id') as HTMLInputElement)?.value;
        const pw = (document.getElementById('swal-pw') as HTMLInputElement)?.value;
        if (!id || !pw) { Swal.showValidationMessage('아이디와 비밀번호를 입력해주세요.'); return false; }
        return { id, pw };
      },
    });
    if (value) {
      await Swal.fire({ title: '로그인 성공', icon: 'success', timer: 1200, showConfirmButton: false });
    }
  };

  const handleLogout = async () => {
    const Swal = (await import('sweetalert2')).default;
    const result = await Swal.fire({
      title: '로그아웃',
      text: '정말 로그아웃 하시겠습니까?',
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#FF0000',
      cancelButtonColor: '#9CA3AF',
      confirmButtonText: '로그아웃',
      cancelButtonText: '취소',
    });
    if (result.isConfirmed) {
      await Swal.fire({ title: '로그아웃 완료', icon: 'success', timer: 1200, showConfirmButton: false });
      router.push('/');
    }
  };

  const handleProfile = async () => {
    const Swal = (await import('sweetalert2')).default;
    await Swal.fire({
      title: '개인정보 수정',
      html: `
        <div style="text-align:left;font-family:'Nanum Gothic',sans-serif">
          <label style="display:block;font-size:12px;font-weight:700;color:#374151;margin-bottom:4px">이름</label>
          <input id="swal-name" class="swal2-input" value="관리자" style="font-size:13px;margin-bottom:8px"/>
          <label style="display:block;font-size:12px;font-weight:700;color:#374151;margin-bottom:4px">이메일</label>
          <input id="swal-email" class="swal2-input" value="admin@youtubeeda.com" style="font-size:13px"/>
        </div>
      `,
      showCancelButton: true,
      confirmButtonColor: '#FF0000',
      cancelButtonColor: '#9CA3AF',
      confirmButtonText: '저장',
      cancelButtonText: '취소',
    });
  };

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-[#E8ECF0] sticky top-0 z-40 shrink-0 shadow-sm">

      {/* 로고 */}
      <div className="flex items-center gap-2.5">
        <div className="flex items-center justify-center w-8 h-8 bg-[#FF0000] rounded-lg shadow-sm">
          <svg className="w-[18px] h-[18px] text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z" />
          </svg>
        </div>
        <div className="leading-tight">
          <span className="text-[14px] font-extrabold text-gray-800">YouTube</span>
          <span className="ml-1 text-[14px] font-extrabold text-[#FF0000]">EDA 분석</span>
        </div>
        <span className="ml-1 hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-50 text-red-500 border border-red-100">
          BETA
        </span>
      </div>

      {/* 우측 메뉴 버튼 */}
      <div className="flex items-center gap-2">

        {/* 로그인 */}
        <button
          onClick={handleLogin}
          className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-bold text-white bg-[#FF0000] hover:bg-red-600 rounded-lg transition-colors shadow-sm"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
              d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
          </svg>
          로그인
        </button>

        {/* 로그아웃 */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300 rounded-lg transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          로그아웃
        </button>

        {/* 개인정보수정 */}
        <button
          onClick={handleProfile}
          className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300 rounded-lg transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          개인정보수정
        </button>

        {/* 프로필 아바타 */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-red-600 flex items-center justify-center text-[12px] font-extrabold text-white cursor-pointer hover:opacity-90 transition-opacity shadow-sm ml-1">
          A
        </div>
      </div>
    </header>
  );
}
