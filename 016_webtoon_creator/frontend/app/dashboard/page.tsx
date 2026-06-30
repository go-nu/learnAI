import Link from 'next/link';
import UserMenu from './components/UserMenu';

export const metadata = {
  title: '대시보드 — ToonCraft',
};

// 메뉴 구성 (사이드바와 동일한 구조)
const FEATURE_GROUPS = [
  {
    key: 'webtoon',
    icon: '🎨',
    title: '웹툰만들기',
    desc: '작품·에피소드·컷을 만들고 관리하세요',
    items: [
      { label: '웹툰 작품', href: '#', count: 0 },
      { label: '웹툰 에피소드(회차)', href: '#', count: 0 },
      { label: '웹툰 컷(개별 패널)', href: '#', count: 0 },
    ],
    cta: { label: '웹툰 만들기 시작', href: '/dashboard/ai_image_generator', variant: 'primary' as const },
  },
  {
    key: 'image',
    icon: '✨',
    title: '이미지생성',
    desc: 'AI로 웹툰 이미지를 생성하세요',
    items: [
      { label: 'AI 이미지 만들기', href: '/dashboard/ai_image_generator', count: null },
      { label: 'AI 이미지 생성 이력', href: '#', count: 0 },
    ],
    cta: { label: '이미지 생성하기', href: '/dashboard/ai_image_generator', variant: 'white' as const },
  },
];

export default function DashboardOverviewPage() {
  return (
    <div
      className="flex flex-col min-h-screen"
      style={{ backgroundColor: 'var(--dash-bg)', color: 'var(--dash-text)', fontFamily: "'Noto Sans KR', Arial, sans-serif" }}
    >

      {/* ── 상단 GNB ── */}
      <header
        className="flex items-center justify-between px-6 h-14 flex-shrink-0"
        style={{ backgroundColor: 'var(--dash-panel)', borderBottom: '1px solid var(--dash-border)' }}
      >
        <Link
          href="/dashboard"
          className="text-lg font-black tracking-tight transition-opacity hover:opacity-70"
          style={{ color: 'var(--dash-text)', textDecoration: 'none' }}
        >
          ToonCraft
        </Link>
        <div className="flex items-center gap-3">
          <button
            className="flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg"
            style={{ color: 'var(--dash-text-sub)', backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)' }}
          >
            한국어
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <UserMenu />
        </div>
      </header>

      {/* ── 메인 콘텐츠 ── */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-10">

        {/* ── 웰컴 배너 ── */}
        <div
          className="flex items-center justify-between rounded-xl px-7 py-5 mb-10"
          style={{ backgroundColor: 'var(--dash-panel)', border: '1px solid var(--dash-border)' }}
        >
          <div>
            <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--dash-text)' }}>
              안녕하세요, User님! 👋
            </h1>
            <p className="text-sm" style={{ color: 'var(--dash-text-sub)' }}>
              오늘도 멋진 웹툰을 만들어 보세요.
            </p>
          </div>
          {/* 크레딧 배지 */}
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold"
            style={{ backgroundColor: 'rgba(0, 199, 60, 0.12)', color: '#00C73C', border: '1px solid rgba(0,199,60,0.25)' }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            1,000 크레딧 보유
          </div>
        </div>

        {/* ── 기능 카드 그리드 ── */}
        <div className="grid grid-cols-2 gap-5 mb-10">
          {FEATURE_GROUPS.map((group) => (
            <div
              key={group.key}
              className="flex flex-col rounded-xl p-7"
              style={{ backgroundColor: 'var(--dash-panel)', border: '1px solid var(--dash-border)' }}
            >
              {/* 카드 헤더 */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xl">{group.icon}</span>
                  <h2 className="text-base font-bold" style={{ color: 'var(--dash-text)' }}>
                    {group.title}
                  </h2>
                </div>
                <p className="text-xs" style={{ color: 'var(--dash-text-sub)' }}>
                  {group.desc}
                </p>
              </div>

              {/* 메뉴 아이템 목록 */}
              <div className="flex flex-col gap-2 flex-1 mb-6">
                {group.items.map((item) => (
                  <Link key={item.label} href={item.href} style={{ textDecoration: 'none' }}>
                    <div
                      className="flex items-center justify-between px-4 py-3 rounded-lg transition-colors"
                      style={{
                        backgroundColor: 'var(--dash-surface)',
                        border: '1px solid var(--dash-border)',
                        cursor: 'pointer',
                      }}
                    >
                      <span className="text-sm" style={{ color: 'var(--dash-text)' }}>
                        {item.label}
                      </span>
                      <span className="text-xs font-medium" style={{
                        color: item.count === null ? '#00C73C' : 'var(--dash-text-muted)',
                      }}>
                        {item.count === null ? '시작 →' : `${item.count}개`}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>

              {/* CTA 버튼 */}
              <Link href={group.cta.href} style={{ textDecoration: 'none' }}>
                <button
                  className="w-full py-3 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
                  style={
                    group.cta.variant === 'primary'
                      ? { backgroundColor: '#00C73C', color: '#FFFFFF' }
                      : { backgroundColor: 'var(--dash-btn-primary)', color: 'var(--dash-btn-primary-text)' }
                  }
                >
                  {group.cta.label} →
                </button>
              </Link>
            </div>
          ))}
        </div>

        {/* ── 최근 생성 이미지 섹션 ── */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold" style={{ color: 'var(--dash-text)' }}>
              최근 생성 이미지
            </h2>
            <Link
              href="#"
              className="text-xs"
              style={{ color: 'var(--dash-text-muted)', textDecoration: 'none' }}
            >
              전체 보기 →
            </Link>
          </div>

          {/* 빈 상태 */}
          <div
            className="flex flex-col items-center justify-center rounded-xl py-16 gap-3"
            style={{ backgroundColor: 'var(--dash-panel)', border: '1px solid var(--dash-border)' }}
          >
            <div
              className="w-14 h-14 rounded-full flex items-center justify-center"
              style={{ backgroundColor: 'var(--dash-surface)' }}
            >
              <svg
                className="w-7 h-7"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                style={{ color: 'var(--dash-text-muted)' }}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <p className="text-sm" style={{ color: 'var(--dash-text-sub)' }}>
              아직 생성된 이미지가 없습니다.
            </p>
            <Link href="/dashboard/ai_image_generator" style={{ textDecoration: 'none' }}>
              <button
                className="mt-1 px-5 py-2.5 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
                style={{ backgroundColor: '#00C73C', color: '#FFFFFF' }}
              >
                첫 이미지 생성하기
              </button>
            </Link>
          </div>
        </section>

      </main>
    </div>
  );
}
