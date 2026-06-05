import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../types'

interface ChatHistoryProps {
  messages: ChatMessage[]
  onClear: () => void
}

export function ChatHistory({ messages, onClear }: ChatHistoryProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-72 text-daum-subtle select-none">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-14 w-14 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p className="text-sm font-medium">아직 대화 기록이 없습니다.</p>
        <p className="text-xs mt-1 opacity-70">위 입력창에 질문을 입력해 보세요.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-end mb-3">
        <button
          onClick={onClear}
          className="text-xs text-daum-subtle hover:text-red-500 transition-colors flex items-center gap-1"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          대화 초기화
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-1 max-h-[520px]">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex items-end gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>

            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-daum-blue flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                AI
              </div>
            )}

            <div className={`max-w-[72%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm
              ${msg.role === 'user'
                ? 'bg-daum-blue text-white rounded-br-none'
                : msg.type === 'image'
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-bl-none'
                  : 'bg-white text-daum-text border border-daum-border rounded-bl-none'
              }`}
            >
              {msg.type === 'image' && msg.role === 'assistant' && (
                <span className="block text-xs font-semibold text-emerald-600 mb-1">🖼️ 이미지 생성 완료</span>
              )}
              <span className="whitespace-pre-wrap break-words">{msg.content}</span>
              <span className={`block text-[10px] mt-1 ${msg.role === 'user' ? 'text-blue-200' : 'text-daum-subtle'}`}>
                {new Date(msg.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-xs font-bold flex-shrink-0">
                나
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
