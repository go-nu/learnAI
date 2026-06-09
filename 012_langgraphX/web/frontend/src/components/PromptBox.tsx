import { useState } from 'react'
import type { KeyboardEvent } from 'react'

interface PromptBoxProps {
  onSubmit: (prompt: string) => void
  disabled?: boolean
}

export function PromptBox({ onSubmit, disabled }: PromptBoxProps) {
  const [prompt, setPrompt] = useState('')

  const handleSubmit = () => {
    if (prompt.trim() && !disabled) {
      onSubmit(prompt.trim())
      setPrompt('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex gap-2 w-full">
      <div className="flex-1 relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-daum-subtle">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </span>
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="궁금한 것을 물어보거나 이미지 생성을 요청하세요 (예: 고양이 이미지 생성)"
          disabled={disabled}
          className="w-full pl-10 pr-4 py-3 border-2 border-daum-border rounded-xl
                     focus:outline-none focus:border-daum-blue focus:shadow-[0_0_0_3px_rgba(0,104,195,0.12)]
                     disabled:bg-gray-100 disabled:cursor-not-allowed
                     text-daum-text placeholder-daum-subtle text-sm transition-all duration-200"
        />
      </div>
      <button
        onClick={handleSubmit}
        disabled={disabled || !prompt.trim()}
        className="px-7 py-3 bg-daum-blue text-white font-semibold rounded-xl
                   hover:bg-daum-blue-dark active:scale-95 transition-all duration-200
                   disabled:bg-gray-300 disabled:cursor-not-allowed
                   flex items-center gap-2 whitespace-nowrap shadow-sm"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
        생성
      </button>
    </div>
  )
}
