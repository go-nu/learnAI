'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  {
    href: '/dashboard/crawling',
    label: '데이터 수집',
    description: 'YouTube 채널 데이터 수집',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
    ),
  },
  {
    href: '/dashboard/channel_list',
    label: '채널 리스트',
    description: '수집한 유튜브 채널',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M4 6h16M4 10h16M4 14h16M4 18h16" />
      </svg>
    ),
  },
  {
    href: '/dashboard/main',
    label: '채널 분석',
    description: '채널 EDA 시각화 분석',
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex flex-col w-[220px] min-h-screen bg-white border-r border-[#E8ECF0] shrink-0">

      {/* 로고 */}
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-[#E8ECF0]">
        <div className="flex items-center justify-center w-8 h-8 bg-[#FF0000] rounded-lg shadow-sm">
          <svg className="w-[18px] h-[18px] text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z" />
          </svg>
        </div>
        <div className="leading-tight">
          <p className="text-[13px] font-extrabold text-gray-800">YouTube</p>
          <p className="text-[11px] font-bold text-[#FF0000]">EDA 분석 플랫폼</p>
        </div>
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 px-3 py-5 space-y-0.5">
        <p className="px-3 pb-2 text-[10px] font-extrabold text-gray-400 uppercase tracking-widest">
          메인 메뉴
        </p>
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-150 group
                ${isActive
                  ? 'bg-red-50 border border-red-100'
                  : 'hover:bg-gray-50 border border-transparent'
                }`}
            >
              <span className={`flex items-center justify-center w-8 h-8 rounded-lg shrink-0 transition-colors
                ${isActive ? 'bg-[#FF0000] text-white shadow-sm' : 'bg-gray-100 text-gray-400 group-hover:bg-gray-200 group-hover:text-gray-600'}`}>
                {item.icon}
              </span>
              <div className="min-w-0">
                <p className={`text-[13px] font-bold leading-tight truncate
                  ${isActive ? 'text-[#FF0000]' : 'text-gray-700 group-hover:text-gray-900'}`}>
                  {item.label}
                </p>
                <p className="text-[10px] text-gray-400 truncate leading-tight mt-0.5">{item.description}</p>
              </div>
            </Link>
          );
        })}
      </nav>

      {/* 하단 사용자 정보 */}
      <div className="px-4 py-4 border-t border-[#E8ECF0]">
        <div className="flex items-center gap-2.5 p-2 rounded-xl hover:bg-gray-50 cursor-pointer transition-colors">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-red-600 flex items-center justify-center text-xs font-extrabold text-white shadow-sm shrink-0">
            A
          </div>
          <div className="min-w-0">
            <p className="text-[12px] font-bold text-gray-800 truncate">관리자</p>
            <p className="text-[10px] text-gray-400 truncate">admin@youtubeeda.com</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
