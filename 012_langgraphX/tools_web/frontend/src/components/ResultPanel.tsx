import Swal from 'sweetalert2'
import type { ImageItem } from '../types'

interface ResultPanelProps {
  result: ImageItem | null
  isLoading: boolean
}

const MODE_LABEL: Record<string, string> = {
  text2img: 'Text → Image',
  img2img: 'Image → Image',
}

export function ResultPanel({ result, isLoading }: ResultPanelProps) {
  const handleDownload = async () => {
    if (!result) return
    const res = await fetch(result.url)
    const blob = await res.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = result.filename
    link.click()
  }

  const handleZoom = () => {
    if (!result) return
    Swal.fire({
      imageUrl: result.url,
      imageAlt: result.filename,
      showConfirmButton: false,
      showCloseButton: true,
      width: 'auto',
      background: '#161b22',
      customClass: { popup: 'rounded-2xl border border-[#2a4a2a]', closeButton: 'text-[#86efac]' },
    })
  }

  return (
    <div className="bg-dark-surface border border-dark-border rounded-2xl p-6 flex flex-col gap-4 shadow-card h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-green-soft flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          생성 결과
        </h2>
        {result && (
          <span className="text-[10px] font-semibold px-2 py-1 rounded-full bg-dark-card border border-dark-border text-green-soft">
            {MODE_LABEL[result.mode] ?? result.mode}
          </span>
        )}
      </div>

      {/* 이미지 표시 영역 */}
      <div
        className={`flex-1 rounded-xl overflow-hidden border border-dark-border flex items-center justify-center
                    min-h-64 relative group
                    ${result ? 'bg-black cursor-zoom-in' : 'bg-dark-card'}`}
        onClick={result ? handleZoom : undefined}
      >
        {isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-dark-card z-10">
            <div className="w-12 h-12 border-4 border-dark-border border-t-green-soft rounded-full animate-spin mb-4" />
            <p className="text-sm text-txt-secondary">이미지 생성 중...</p>
          </div>
        )}

        {result && !isLoading ? (
          <>
            <img
              src={result.url}
              alt={result.filename}
              className="max-w-full max-h-full object-contain w-full h-full"
              style={{ maxHeight: '420px' }}
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all duration-200
                            flex items-center justify-center opacity-0 group-hover:opacity-100">
              <svg className="w-10 h-10 text-white drop-shadow-lg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
              </svg>
            </div>
          </>
        ) : !isLoading ? (
          <div className="flex flex-col items-center text-txt-muted select-none">
            <svg className="w-16 h-16 mb-3 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-sm">생성된 이미지가 여기에 표시됩니다</p>
          </div>
        ) : null}
      </div>

      {/* 이미지 정보 + 다운로드 */}
      {result && !isLoading && (
        <div className="flex flex-col gap-3">
          <div className="bg-dark-card rounded-xl p-3 border border-dark-border flex flex-col gap-1.5">
            <div className="flex items-start gap-2">
              <span className="text-[10px] text-txt-muted w-12 shrink-0 pt-0.5">파일명</span>
              <span className="text-xs text-txt-secondary font-mono break-all">{result.filename}</span>
            </div>
            {result.prompt && (
              <div className="flex items-start gap-2">
                <span className="text-[10px] text-txt-muted w-12 shrink-0 pt-0.5">프롬프트</span>
                <span className="text-xs text-txt-secondary line-clamp-2">{result.prompt}</span>
              </div>
            )}
            <div className="flex items-start gap-2">
              <span className="text-[10px] text-txt-muted w-12 shrink-0 pt-0.5">생성일</span>
              <span className="text-xs text-txt-secondary">
                {new Date(result.created_at * 1000).toLocaleString('ko-KR')}
              </span>
            </div>
          </div>

          <button
            onClick={handleDownload}
            className="w-full py-2.5 rounded-xl border border-green-dim text-green-soft font-semibold text-sm
                       flex items-center justify-center gap-2
                       hover:bg-green-glow hover:border-green-soft hover:text-green-bright
                       transition-all duration-200 active:scale-95"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            이미지 다운로드
          </button>
        </div>
      )}
    </div>
  )
}
