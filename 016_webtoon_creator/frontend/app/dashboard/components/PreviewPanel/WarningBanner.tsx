// 상단 경고/안내 배너 (다크 배경 + 앰버 텍스트)
export default function WarningBanner() {
  return (
    <div
      className="flex items-start gap-2 rounded-lg px-4 py-3 mb-5 text-sm"
      style={{
        backgroundColor: 'var(--dash-warning-bg)',
        border: '1px solid #3A3000',
        color: 'var(--dash-warning-text)',
      }}
    >
      <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd"
          d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
          clipRule="evenodd"
        />
      </svg>
      <span>
        로그인 또는 회원가입 시 생성 내역을 저장할 수 있어요. 마음에 드는 이미지는 미리 저장해 주세요.
      </span>
    </div>
  );
}
