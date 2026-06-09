import { useState, useEffect, useCallback } from 'react'
import Swal from 'sweetalert2'

import { PromptBox } from './components/PromptBox'
import { ChatHistory } from './components/ChatHistory'
import { ImageGallery } from './components/ImageGallery'
import { LoadingModal } from './components/LoadingModal'
import { generateResponse, fetchHistory, clearHistory, fetchImages } from './api/client'
import type { ChatMessage, ImageItem, TabType } from './types'

const IMAGE_KEYWORDS = ['이미지', 'comfyui', '이미지생성', 'image']

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('chat')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [images, setImages] = useState<ImageItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('처리 중입니다...')

  const loadHistory = useCallback(async () => {
    try {
      setMessages(await fetchHistory())
    } catch { /* 서버 연결 전 무시 */ }
  }, [])

  const loadImages = useCallback(async () => {
    try {
      setImages(await fetchImages())
    } catch { /* 서버 연결 전 무시 */ }
  }, [])

  useEffect(() => {
    loadHistory()
    loadImages()
  }, [loadHistory, loadImages])

  const handleGenerate = async (prompt: string) => {
    const isImage = IMAGE_KEYWORDS.some((kw) => prompt.toLowerCase().includes(kw))

    setLoadingMessage(isImage ? '🖼️ 이미지를 생성하고 있습니다...' : '🤖 AI가 답변을 작성 중입니다...')
    setIsLoading(true)

    try {
      const result = await generateResponse(prompt)
      await loadHistory()

      if (result.type === 'image') {
        await loadImages()
        setActiveTab('image')
        Swal.fire({
          icon: 'success',
          title: '이미지 생성 완료!',
          text: '이미지 탭에서 확인하세요.',
          confirmButtonColor: '#0068C3',
          confirmButtonText: '이미지 보기',
          timer: 4000,
          timerProgressBar: true,
        })
      }
    } catch (err: unknown) {
      let msg = '알 수 없는 오류가 발생했습니다.'
      if (err instanceof Error) msg = err.message
      Swal.fire({
        icon: 'error',
        title: '오류 발생',
        text: msg,
        confirmButtonColor: '#0068C3',
        confirmButtonText: '확인',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearHistory = async () => {
    const result = await Swal.fire({
      title: '대화 기록 삭제',
      text: '모든 대화 기록이 삭제됩니다. 계속하시겠습니까?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#0068C3',
      cancelButtonColor: '#999',
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
    })

    if (result.isConfirmed) {
      await clearHistory()
      setMessages([])
      Swal.fire({
        icon: 'success',
        title: '삭제 완료',
        confirmButtonColor: '#0068C3',
        timer: 1500,
        showConfirmButton: false,
      })
    }
  }

  return (
    <div className="min-h-screen bg-daum-bg flex flex-col">
      <LoadingModal isLoading={isLoading} message={loadingMessage} />

      {/* 헤더 */}
      <header className="bg-daum-blue shadow-md">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-9 h-9 bg-white rounded-full flex items-center justify-center shadow">
            <span className="text-daum-blue font-black text-sm tracking-tight">AI</span>
          </div>
          <div>
            <h1 className="text-white text-lg font-bold leading-tight">AI 생성 서비스</h1>
            <p className="text-blue-200 text-xs">LangGraph · ComfyUI · Gemini</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`} />
            <span className="text-blue-100 text-xs">{isLoading ? '처리 중' : '준비 완료'}</span>
          </div>
        </div>
      </header>

      {/* 프롬프트 입력 영역 */}
      <div className="bg-white border-b border-daum-border shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <PromptBox onSubmit={handleGenerate} disabled={isLoading} />
          <p className="text-[11px] text-daum-subtle mt-2 pl-1">
            💡 <strong>대화</strong>: 일반 질문 입력 &nbsp;|&nbsp; <strong>이미지 생성</strong>: "이미지", "image" 키워드 포함
          </p>
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="bg-white border-b border-daum-border">
        <div className="max-w-4xl mx-auto px-4">
          <nav className="flex">
            {([
              { id: 'chat' as TabType, label: '대화', icon: '💬', count: messages.length },
              { id: 'image' as TabType, label: '이미지', icon: '🖼️', count: images.length },
            ]).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-all duration-200
                  ${activeTab === tab.id
                    ? 'border-daum-blue text-daum-blue'
                    : 'border-transparent text-daum-subtle hover:text-daum-text hover:border-daum-border'
                  }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
                {tab.count > 0 && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold
                    ${activeTab === tab.id ? 'bg-daum-blue-light text-daum-blue' : 'bg-gray-100 text-daum-subtle'}`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* 컨텐츠 */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl shadow-sm border border-daum-border p-6 min-h-[420px]">
          {activeTab === 'chat' ? (
            <ChatHistory messages={messages} onClear={handleClearHistory} />
          ) : (
            <ImageGallery images={images} onRefresh={loadImages} />
          )}
        </div>
      </main>

      {/* 푸터 */}
      <footer className="text-center py-4 text-xs text-daum-subtle border-t border-daum-border bg-white">
        AI 생성 서비스 &copy; 2024 &nbsp;·&nbsp; Powered by LangGraph &amp; ComfyUI
      </footer>
    </div>
  )
}
