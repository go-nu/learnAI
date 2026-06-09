import Swal from 'sweetalert2'
import type { ImageItem } from '../types'

interface ImageGalleryProps {
  images: ImageItem[]
  onRefresh: () => void
}

export function ImageGallery({ images, onRefresh }: ImageGalleryProps) {
  const handleImageClick = (img: ImageItem) => {
    Swal.fire({
      imageUrl: img.url,
      imageAlt: img.filename,
      title: `<span style="font-size:13px;color:#767676;font-weight:normal">${img.filename}</span>`,
      showConfirmButton: false,
      showCloseButton: true,
      width: 'auto',
      background: '#fff',
      customClass: { popup: 'rounded-2xl' },
    })
  }

  if (images.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-72 text-daum-subtle select-none">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-14 w-14 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p className="text-sm font-medium">생성된 이미지가 없습니다.</p>
        <p className="text-xs mt-1 opacity-70">"고양이 이미지 생성"처럼 입력해 보세요.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm text-daum-subtle">
          총 <strong className="text-daum-blue">{images.length}</strong>개의 이미지
        </span>
        <button
          onClick={onRefresh}
          className="text-xs text-daum-blue hover:text-daum-blue-dark transition-colors flex items-center gap-1 font-medium"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          새로고침
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {images.map((img) => (
          <div
            key={img.filename}
            onClick={() => handleImageClick(img)}
            className="group relative aspect-square rounded-xl overflow-hidden bg-gray-100 cursor-pointer
                       border border-daum-border hover:border-daum-blue
                       hover:shadow-lg transition-all duration-200"
          >
            <img
              src={img.url}
              alt={img.filename}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200
                            flex items-center justify-center opacity-0 group-hover:opacity-100">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white drop-shadow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
              </svg>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
