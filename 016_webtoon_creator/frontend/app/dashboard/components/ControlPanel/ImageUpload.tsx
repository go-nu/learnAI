'use client';

// 참조 이미지 첨부 영역
export default function ImageUpload() {
  return (
    <div className="mb-5">
      <span className="text-xs font-semibold block mb-2" style={{ color: 'var(--dash-text)' }}>이미지 첨부</span>

      <button
        className="w-full rounded-lg p-4 flex flex-col items-center gap-2 border-2 border-dashed transition-opacity hover:opacity-70"
        style={{ borderColor: 'var(--dash-border)', backgroundColor: 'var(--dash-surface)' }}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"
          style={{ color: 'var(--dash-text-muted)' }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M12 16v-8m0 0l-3 3m3-3l3 3M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1" />
        </svg>
        <span className="text-xs" style={{ color: 'var(--dash-text-muted)' }}>
          이미지를 드래그하거나 클릭해서 첨부
        </span>
      </button>
    </div>
  );
}
