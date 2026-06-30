// 생성 이미지 프리뷰 영역
export default function ImagePreview() {
  return (
    <div
      className="relative rounded-xl overflow-hidden flex items-center justify-center"
      style={{
        backgroundColor: 'var(--dash-surface)',
        border: '1px solid var(--dash-border)',
        aspectRatio: '3/4',
        maxHeight: '520px',
      }}
    >
      {/* 이미지 미생성 플레이스홀더 */}
      <div className="flex flex-col items-center gap-3">
        <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24"
          style={{ color: 'var(--dash-text-muted)' }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
            d="M4 16l4-4 4 4 4-8 4 8M3 3h18v18H3z" />
          <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor" />
        </svg>
        <p className="text-sm text-center px-4" style={{ color: 'var(--dash-text-sub)' }}>
          왼쪽에서 설정 후 생성 버튼을 눌러주세요.
        </p>
      </div>

      {/* 다운로드 버튼 (우하단) */}
      <button
        className="absolute bottom-3 right-3 p-2 rounded-full transition-opacity hover:opacity-70"
        style={{
          backgroundColor: 'var(--dash-panel)',
          border: '1px solid var(--dash-border)',
          color: 'var(--dash-text-sub)',
        }}
        title="다운로드"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
        </svg>
      </button>
    </div>
  );
}
