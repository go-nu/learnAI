'use client';

// 초기화 / 생성 버튼
export default function ActionButtons() {
  return (
    <div className="mt-auto pt-4" style={{ borderTop: '1px solid var(--dash-border)' }}>
      {/* 크레딧 충전 배너 */}
      <div
        className="rounded-lg px-3 py-2 mb-4 text-center text-xs"
        style={{ backgroundColor: 'var(--dash-surface)', color: 'var(--dash-text-sub)', border: '1px solid var(--dash-border)' }}
      >
        매일매일 1000크레딧 충전!
      </div>

      <div className="flex gap-2">
        {/* 초기화 */}
        <button
          className="flex-1 py-3 rounded-lg text-sm font-medium transition-opacity hover:opacity-70"
          style={{
            backgroundColor: 'var(--dash-btn-secondary)',
            color: 'var(--dash-text-sub)',
            border: '1px solid var(--dash-border)',
          }}
        >
          초기화
        </button>

        {/* 생성 — 흰색 버튼 */}
        <button
          className="py-3 rounded-lg text-sm font-bold transition-opacity hover:opacity-80"
          style={{
            backgroundColor: 'var(--dash-btn-primary)',
            color: 'var(--dash-btn-primary-text)',
            flexGrow: 2,
          }}
        >
          생성
        </button>
      </div>
    </div>
  );
}
