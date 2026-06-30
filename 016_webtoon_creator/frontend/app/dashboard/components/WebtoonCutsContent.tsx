'use client';

import Link from 'next/link';

// WebtoonCut 모델 필드:
// episode(FK), order(순서), image(컷 이미지), caption(대사/캡션), created_at

// 샘플 데이터 (실제 구현 시 API로 교체)
const SAMPLE_CUTS: {
  id: number; order: number; image: string | null;
  caption: string; created_at: string;
}[] = [];

export default function WebtoonCutsContent() {
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
            웹툰 컷(개별 패널)
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--dash-text-muted)' }}>
            총 {SAMPLE_CUTS.length}개
          </p>
        </div>
        <Link
          href="/dashboard/ai_image_generator/cut_add"
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
          style={{ backgroundColor: '#00C73C', color: '#FFFFFF', textDecoration: 'none' }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          컷 추가
        </Link>
      </div>

      {/* ── 컷 그리드 / 빈 상태 ── */}
      <div className="flex-1 px-8 py-6">
        {SAMPLE_CUTS.length > 0 ? (
          /* 컷 그리드 — WebtoonCut 모델 필드 기반 */
          <div
            className="grid gap-4"
            style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))' }}
          >
            {SAMPLE_CUTS.map((cut) => (
              <div
                key={cut.id}
                className="rounded-xl overflow-hidden transition-transform hover:scale-[1.02]"
                style={{
                  backgroundColor: 'var(--dash-panel)',
                  border: '1px solid var(--dash-border)',
                  cursor: 'pointer',
                }}
              >
                {/* 순서 배지 + 이미지 영역 (3:4 비율) */}
                <div className="relative" style={{ paddingTop: '133.33%', backgroundColor: 'var(--dash-surface)' }}>
                  {cut.image ? (
                    <img
                      src={cut.image}
                      alt={`컷 ${cut.order}`}
                      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div
                      className="absolute inset-0 flex items-center justify-center"
                      style={{ color: 'var(--dash-text-muted)' }}
                    >
                      <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  )}
                  {/* 순서 번호 배지 */}
                  <span
                    className="absolute top-2 left-2 text-xs font-bold px-2 py-0.5 rounded"
                    style={{ backgroundColor: 'rgba(0,0,0,0.65)', color: '#FFFFFF' }}
                  >
                    {cut.order}
                  </span>
                  {/* 관리 오버레이 버튼 */}
                  <div
                    className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ opacity: 1 }}
                  >
                    <button
                      className="w-6 h-6 rounded flex items-center justify-center"
                      style={{ backgroundColor: 'rgba(0,0,0,0.65)' }}
                      title="수정"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        style={{ color: '#FFFFFF' }}>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      className="w-6 h-6 rounded flex items-center justify-center"
                      style={{ backgroundColor: 'rgba(0,0,0,0.65)' }}
                      title="삭제"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        style={{ color: '#EF4444' }}>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* 컷 정보 영역 */}
                <div className="px-3 py-2.5">
                  {/* 대사/캡션 (caption) */}
                  <p
                    className="text-xs mb-1"
                    style={{
                      color: cut.caption ? 'var(--dash-text-sub)' : 'var(--dash-text-muted)',
                      overflow: 'hidden',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      lineHeight: '1.5',
                    }}
                  >
                    {cut.caption || '대사/캡션 없음'}
                  </p>
                  {/* 생성일 (created_at) */}
                  <p className="text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                    {cut.created_at}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* 빈 상태 */
          <div className="flex flex-col items-center justify-center h-full py-20 gap-4">
            <div
              className="w-14 h-14 rounded-full flex items-center justify-center"
              style={{ backgroundColor: 'var(--dash-surface)' }}
            >
              <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                style={{ color: 'var(--dash-text-muted)' }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <p className="text-sm" style={{ color: 'var(--dash-text-sub)' }}>
              등록된 컷이 없습니다.
            </p>
            <Link
              href="/dashboard/ai_image_generator/cut_add"
              className="px-5 py-2.5 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
              style={{ backgroundColor: '#00C73C', color: '#FFFFFF', textDecoration: 'none' }}
            >
              + 컷 추가
            </Link>
          </div>
        )}
      </div>
    </main>
  );
}
