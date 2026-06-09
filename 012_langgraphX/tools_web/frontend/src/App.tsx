import { useState, useEffect, useCallback } from 'react'
import Swal from 'sweetalert2'

import { InputPanel } from './components/InputPanel'
import { ResultPanel } from './components/ResultPanel'
import { HistoryGallery } from './components/HistoryGallery'
import { generateText2Img, generateImg2Img, fetchImages, clearImages } from './api/client'
import type { Mode, ImageItem } from './types'

export default function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ImageItem | null>(null)
  const [images, setImages] = useState<ImageItem[]>([])

  const loadImages = useCallback(async () => {
    try {
      const data = await fetchImages()
      setImages(data)
    } catch { /* 서버 미연결 무시 */ }
  }, [])

  useEffect(() => { loadImages() }, [loadImages])

  const showLoadingModal = (mode: Mode) => {
    Swal.fire({
      title: mode === 'text2img' ? '이미지 생성 중...' : '이미지 변환 중...',
      html: `
        <div style="display:flex;flex-direction:column;align-items:center;gap:16px;padding:8px 0">
          <div style="position:relative;width:64px;height:64px">
            <div style="position:absolute;inset:0;border-radius:50%;border:3px solid #2a4a2a"></div>
            <div style="position:absolute;inset:0;border-radius:50%;border:3px solid transparent;border-top-color:#86efac;animation:spin 1s linear infinite"></div>
            <div style="position:absolute;inset:8px;border-radius:50%;border:2px solid transparent;border-top-color:#4ade80;animation:spin 0.7s linear infinite reverse"></div>
          </div>
          <p style="color:#a3c9a8;font-size:13px;margin:0">
            ${mode === 'text2img' ? 'ComfyUI에서 이미지를 생성하고 있습니다...' : '입력 이미지를 바탕으로 변환 중입니다...'}
          </p>
          <p style="color:#5a7a5a;font-size:11px;margin:0">최대 5분이 소요될 수 있습니다</p>
        </div>
        <style>@keyframes spin{to{transform:rotate(360deg)}}</style>
      `,
      showConfirmButton: false,
      allowOutsideClick: false,
      allowEscapeKey: false,
      background: '#161b22',
      customClass: {
        popup: 'rounded-2xl',
        title: 'text-[#86efac] text-base font-semibold',
      },
    })
  }

  const handleGenerate = async (prompt: string, mode: Mode, image?: File, denoise?: number) => {
    setIsLoading(true)
    showLoadingModal(mode)

    try {
      const res = mode === 'text2img'
        ? await generateText2Img(prompt)
        : await generateImg2Img(prompt, image!, denoise ?? 0.75)

      Swal.close()

      if (res.image_url) {
        const newItem: ImageItem = {
          filename: res.image_url.split('/').pop() ?? 'image.png',
          url: res.image_url,
          created_at: Date.now() / 1000,
          prompt,
          mode,
        }
        setResult(newItem)
        await loadImages()

        Swal.fire({
          icon: 'success',
          title: '생성 완료!',
          text: mode === 'text2img' ? '이미지가 성공적으로 생성되었습니다.' : '이미지 변환이 완료되었습니다.',
          timer: 2500,
          timerProgressBar: true,
          showConfirmButton: false,
          background: '#161b22',
          customClass: { popup: 'rounded-2xl' },
        })
      } else {
        Swal.fire({
          icon: 'warning',
          title: '생성 결과 없음',
          text: res.message || '이미지가 생성되지 않았습니다.',
          background: '#161b22',
          customClass: { popup: 'rounded-2xl' },
        })
      }
    } catch (err: unknown) {
      Swal.close()
      let msg = '알 수 없는 오류가 발생했습니다.'
      if (err instanceof Error) msg = err.message
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosErr = err as { response?: { data?: { error?: string } } }
        msg = axiosErr.response?.data?.error ?? msg
      }
      Swal.fire({
        icon: 'error',
        title: '오류 발생',
        text: msg,
        background: '#161b22',
        customClass: { popup: 'rounded-2xl' },
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleClear = async () => {
    const confirm = await Swal.fire({
      title: '히스토리 삭제',
      text: '모든 히스토리 기록이 삭제됩니다. 계속하시겠습니까?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
      background: '#161b22',
      customClass: { popup: 'rounded-2xl' },
    })

    if (confirm.isConfirmed) {
      await clearImages()
      setImages([])
      Swal.fire({
        icon: 'success',
        title: '삭제 완료',
        timer: 1500,
        showConfirmButton: false,
        background: '#161b22',
        customClass: { popup: 'rounded-2xl' },
      })
    }
  }

  return (
    <div className="min-h-screen bg-dark-bg flex flex-col">

      {/* 헤더 */}
      <header className="border-b border-dark-border bg-dark-surface/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="w-[1280px] mx-auto px-6 py-3 flex items-center gap-3">
          <div className="w-9 h-9 bg-green-active/20 rounded-xl border border-green-dim flex items-center justify-center">
            <span className="text-lg">🌿</span>
          </div>
          <div>
            <h1 className="text-white font-bold text-base leading-tight">AI Image Studio</h1>
            <p className="text-txt-muted text-[11px]">LangGraph · ComfyUI · Gemini</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs">
              <span className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-400 animate-pulse' : 'bg-green-active'}`} />
              <span className={`${isLoading ? 'text-yellow-400' : 'text-txt-secondary'}`}>
                {isLoading ? '처리 중...' : '준비 완료'}
              </span>
            </div>
            <div className="h-4 w-px bg-dark-border" />
            <span className="text-[11px] text-txt-muted font-mono">
              이미지 {images.length}개
            </span>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 w-[1280px] mx-auto px-6 py-8 flex flex-col gap-6">

        {/* 상단: 입력 + 결과 패널 */}
        <div className="flex gap-6 items-start">
          {/* 왼쪽: 입력 패널 */}
          <div className="w-[440px] shrink-0">
            <InputPanel onGenerate={handleGenerate} isLoading={isLoading} />
          </div>

          {/* 오른쪽: 결과 패널 */}
          <div className="flex-1">
            <ResultPanel result={result} isLoading={isLoading} />
          </div>
        </div>

        {/* 하단: 히스토리 갤러리 */}
        <HistoryGallery
          images={images}
          onRefresh={loadImages}
          onClear={handleClear}
          onSelect={setResult}
        />
      </main>

      {/* 푸터 */}
      <footer className="border-t border-dark-border py-4 text-center">
        <p className="text-[11px] text-txt-muted">
          AI Image Studio &copy; 2024 &nbsp;·&nbsp; Powered by LangGraph &amp; ComfyUI
        </p>
      </footer>
    </div>
  )
}
