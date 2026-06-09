import React from 'react'
import Swal from 'sweetalert2'
import type { ImageItem } from '../types'

interface HistoryGalleryProps {
  images: ImageItem[]
  onRefresh: () => void
  onClear: () => void
  onSelect: (img: ImageItem) => void
}

const MODE_LABEL: Record<string, string> = {
  text2img: 'T→I',
  img2img: 'I→I',
}
const MODE_COLOR: Record<string, string> = {
  text2img: 'bg-blue-900/60 text-blue-300 border-blue-800',
  img2img:  'bg-purple-900/60 text-purple-300 border-purple-800',
}

export function HistoryGallery({ images, onRefresh, onClear, onSelect }: HistoryGalleryProps) {
  const handleImageClick = (img: ImageItem) => {
    onSelect(img)
  }

  const handleZoom = (e: React.MouseEvent, img: ImageItem) => {
    e.stopPropagation()
    Swal.fire({
      imageUrl: img.url,
      imageAlt: img.filename,
      title: `<span style="font-size:12px;color:#a3c9a8">${img.filename}</span>`,
      showConfirmButton: false,
      showCloseButton: true,
      width: 'auto',
      background: '#161b22',
      customClass: {
        popup: 'rounded-2xl',
        title: 'mt-0',
      },
    })
  }

  return (
    <div className="bg-dark-surface border border-dark-border rounded-2xl p-6 shadow-card">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-green-soft" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="text-sm font-semibold text-green-soft">생성 히스토리</h3>
          {images.length > 0 && (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-dark-card border border-dark-border text-txt-muted">
              {images.length}개
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="text-xs text-txt-muted hover:text-green-soft transition-colors duration-200 flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-dark-hover"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            새로고침
          </button>
          {images.length > 0 && (
            <button
              onClick={onClear}
              className="text-xs text-red-400/60 hover:text-red-400 transition-colors duration-200 flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-red-900/20"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              히스토리 삭제
            </button>
          )}
        </div>
      </div>

      {/* 갤러리 그리드 */}
      {images.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-32 text-txt-muted select-none">
          <svg className="w-10 h-10 mb-2 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p className="text-sm">생성된 이미지가 없습니다</p>
        </div>
      ) : (
        <div className="grid grid-cols-6 gap-3">
          {images.map((img) => (
            <div
              key={img.filename}
              onClick={() => handleImageClick(img)}
              className="group relative aspect-square rounded-xl overflow-hidden bg-dark-card cursor-pointer
                         border border-dark-border hover:border-green-dim
                         hover:shadow-[0_0_12px_rgba(134,239,172,0.15)] transition-all duration-200"
            >
              <img
                src={img.url}
                alt={img.filename}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
              />
              {/* 모드 배지 */}
              <div className={`absolute top-1.5 left-1.5 text-[9px] font-bold px-1.5 py-0.5 rounded border ${MODE_COLOR[img.mode] ?? 'bg-gray-800 text-gray-300 border-gray-700'}`}>
                {MODE_LABEL[img.mode] ?? img.mode}
              </div>
              {/* 확대 버튼 */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all duration-200
                              flex items-center justify-center opacity-0 group-hover:opacity-100">
                <button
                  onClick={(e) => handleZoom(e, img)}
                  className="w-8 h-8 bg-black/50 rounded-full flex items-center justify-center
                             text-white hover:bg-green-active hover:text-dark-bg transition-colors duration-200"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                  </svg>
                </button>
              </div>
              {/* 프롬프트 툴팁 */}
              {img.prompt && (
                <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent
                                px-2 py-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <p className="text-[10px] text-white line-clamp-2">{img.prompt}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
