'use client';

import Link from 'next/link';

// WebtoonEpisode 모델 필드:
// webtoon(FK), episode_number, title, thumbnail, is_published, created_at, published_at

const PUBLISHED_STYLE = {
  true:  { bg: 'rgba(0,199,60,0.15)',    color: '#00C73C', label: '발행됨' },
  false: { bg: 'rgba(85,85,85,0.35)',    color: '#AAAAAA', label: '미발행' },
};

// 샘플 데이터 (실제 구현 시 API로 교체)
const SAMPLE_EPISODES: {
  id: number; episode_number: number; title: string;
  thumbnail: string | null; is_published: boolean;
  created_at: string; published_at: string | null;
}[] = [];

export default function WebtoonEpisodesContent() {
  return (
    <main
      className="flex-1 flex flex-col overflow-y-auto scrollbar-hidden"
      style={{ backgroundColor: 'var(--dash-bg)' }}
    >
      {/* ── 섹션 헤더 ── */}
      <div
        className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: '1px solid var(--dash-border)' }}
      >
        <div>
          <h1 className="text-lg font-bold" style={{ color: 'var(--dash-text)' }}>
            웹툰 에피소드(회차)
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--dash-text-muted)' }}>
            총 {SAMPLE_EPISODES.length}개
          </p>
        </div>
        <Link
          href="/dashboard/ai_image_generator/episode"
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
          style={{ backgroundColor: '#00C73C', color: '#FFFFFF', textDecoration: 'none' }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          에피소드 추가
        </Link>
      </div>

      {/* ── 테이블 영역 ── */}
      <div className="flex-1 px-8 py-6 overflow-x-auto">
        <table className="w-full" style={{ borderCollapse: 'separate', borderSpacing: 0 }}>

          {/* 테이블 헤더 — WebtoonEpisode 모델 필드 기반 */}
          <thead>
            <tr style={{ backgroundColor: 'var(--dash-surface)' }}>
              {[
                { label: '썸네일', width: '72px' },
                { label: '회차', width: '70px' },
                { label: '에피소드 제목', width: 'auto' },
                { label: '발행 여부', width: '100px' },
                { label: '생성일', width: '120px' },
                { label: '발행일', width: '120px' },
                { label: '관리', width: '90px' },
              ].map((col, i) => (
                <th
                  key={col.label}
                  className="text-left px-4 py-3 text-xs font-bold uppercase tracking-wider"
                  style={{
                    color: 'var(--dash-text-muted)',
                    width: col.width,
                    borderBottom: '1px solid var(--dash-border)',
                    borderRadius: i === 0 ? '8px 0 0 8px' : i === 6 ? '0 8px 8px 0' : undefined,
                  }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {SAMPLE_EPISODES.length > 0 ? (
              SAMPLE_EPISODES.map((ep) => {
                const pubStyle = PUBLISHED_STYLE[String(ep.is_published) as 'true' | 'false'];
                return (
                  <tr
                    key={ep.id}
                    className="transition-colors"
                    style={{ borderBottom: '1px solid var(--dash-border)' }}
                  >
                    {/* 썸네일 */}
                    <td className="px-4 py-3">
                      <div
                        className="rounded flex items-center justify-center"
                        style={{ width: '40px', height: '54px', backgroundColor: 'var(--dash-surface)', flexShrink: 0 }}
                      >
                        {ep.thumbnail ? (
                          <img src={ep.thumbnail} alt={ep.title}
                            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '4px' }} />
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                            style={{ color: 'var(--dash-text-muted)' }}>
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        )}
                      </div>
                    </td>
                    {/* 회차 번호 */}
                    <td className="px-4 py-3 text-sm font-bold" style={{ color: 'var(--dash-text-sub)' }}>
                      {ep.episode_number}화
                    </td>
                    {/* 제목 */}
                    <td className="px-4 py-3 text-sm font-medium" style={{ color: 'var(--dash-text)' }}>
                      {ep.title}
                    </td>
                    {/* 발행 여부 */}
                    <td className="px-4 py-3">
                      <span className="px-2.5 py-1 rounded text-xs font-medium"
                        style={{ backgroundColor: pubStyle.bg, color: pubStyle.color }}>
                        {pubStyle.label}
                      </span>
                    </td>
                    {/* 생성일 */}
                    <td className="px-4 py-3 text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                      {ep.created_at}
                    </td>
                    {/* 발행일 */}
                    <td className="px-4 py-3 text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                      {ep.published_at ?? '—'}
                    </td>
                    {/* 관리 버튼 */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button className="text-xs px-2 py-1 rounded transition-opacity hover:opacity-70"
                          style={{ color: 'var(--dash-text-sub)', border: '1px solid var(--dash-border)' }}>
                          수정
                        </button>
                        <button className="text-xs px-2 py-1 rounded transition-opacity hover:opacity-70"
                          style={{ color: '#EF4444', border: '1px solid rgba(239,68,68,0.3)' }}>
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            ) : (
              /* 빈 상태 */
              <tr>
                <td colSpan={7}>
                  <div className="flex flex-col items-center justify-center py-20 gap-4">
                    <div className="w-14 h-14 rounded-full flex items-center justify-center"
                      style={{ backgroundColor: 'var(--dash-surface)' }}>
                      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        style={{ color: 'var(--dash-text-muted)' }}>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                          d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
                      </svg>
                    </div>
                    <p className="text-sm" style={{ color: 'var(--dash-text-sub)' }}>
                      등록된 에피소드가 없습니다.
                    </p>
                    <Link
                      href="/dashboard/ai_image_generator/episode"
                      className="px-5 py-2.5 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
                      style={{ backgroundColor: '#00C73C', color: '#FFFFFF', textDecoration: 'none' }}
                    >
                      + 에피소드 추가
                    </Link>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
