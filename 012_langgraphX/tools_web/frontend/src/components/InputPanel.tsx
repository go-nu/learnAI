import React, { useState, useRef, useCallback } from 'react'
import type { Mode } from '../types'

interface InputPanelProps {
  onGenerate: (prompt: string, mode: Mode, image?: File, denoise?: number) => void
  isLoading: boolean
}

export function InputPanel({ onGenerate, isLoading }: InputPanelProps) {
  const [mode, setMode] = useState<Mode>('text2img')
  const [prompt, setPrompt] = useState('')
  const [uploadedImage, setUploadedImage] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [denoise, setDenoise] = useState(0.75)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleImageSelect = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return
    setUploadedImage(file)
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      const file = e.dataTransfer.files[0]
      if (file) handleImageSelect(file)
    },
    [handleImageSelect],
  )

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleImageSelect(file)
  }

  const handleRemoveImage = () => {
    setUploadedImage(null)
    setPreviewUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSubmit = () => {
    if (!prompt.trim() || isLoading) return
    if (mode === 'img2img' && !uploadedImage) return
    onGenerate(prompt.trim(), mode, uploadedImage ?? undefined, denoise)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) handleSubmit()
  }

  const canSubmit = prompt.trim() && !isLoading && (mode === 'text2img' || uploadedImage !== null)

  return (
    <div className="bg-dark-surface border border-dark-border rounded-2xl p-6 flex flex-col gap-5 shadow-card">
      {/* 모드 탭 */}
      <div className="flex rounded-xl overflow-hidden border border-dark-border">
        {(['text2img', 'img2img'] as Mode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex-1 py-2.5 text-sm font-semibold transition-all duration-200 flex items-center justify-center gap-2
              ${mode === m
                ? 'bg-green-active text-dark-bg'
                : 'bg-dark-card text-txt-secondary hover:bg-dark-hover hover:text-green-soft'
              }`}
          >
            {m === 'text2img' ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                </svg>
                텍스트 → 이미지
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                이미지 → 이미지
              </>
            )}
          </button>
        ))}
      </div>

      {/* 프롬프트 */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-semibold text-green-soft tracking-wide uppercase">
          프롬프트
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            mode === 'text2img'
              ? 'a beautiful mountain landscape at golden hour...'
              : '이미지를 변환할 스타일이나 설명을 입력하세요...'
          }
          disabled={isLoading}
          rows={4}
          className="w-full px-4 py-3 rounded-xl border border-dark-border bg-dark-input
                     text-txt-primary placeholder-txt-muted text-sm resize-none
                     focus:outline-none focus:border-green-soft focus:shadow-green
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all duration-200"
        />
        <p className="text-[11px] text-txt-muted text-right">Ctrl+Enter로 생성</p>
      </div>

      {/* 이미지 업로드 (img2img 전용) */}
      {mode === 'img2img' && (
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-green-soft tracking-wide uppercase">
            입력 이미지
          </label>
          {previewUrl ? (
            <div className="relative rounded-xl overflow-hidden border border-dark-border group">
              <img
                src={previewUrl}
                alt="입력 이미지"
                className="w-full h-48 object-cover"
              />
              <button
                onClick={handleRemoveImage}
                className="absolute top-2 right-2 w-7 h-7 bg-black/60 rounded-full
                           flex items-center justify-center text-white hover:bg-red-600
                           transition-colors duration-200 opacity-0 group-hover:opacity-100"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <div className="absolute bottom-0 inset-x-0 bg-black/50 px-3 py-1.5">
                <p className="text-xs text-white truncate">{uploadedImage?.name}</p>
              </div>
            </div>
          ) : (
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl h-36 flex flex-col items-center justify-center
                          cursor-pointer transition-all duration-200 select-none
                          ${isDragging
                            ? 'border-green-soft bg-green-glow'
                            : 'border-dark-border hover:border-green-dim hover:bg-dark-hover'
                          }`}
            >
              <svg className="w-8 h-8 text-txt-muted mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-sm text-txt-secondary font-medium">이미지를 드래그하거나 클릭</p>
              <p className="text-xs text-txt-muted mt-1">PNG, JPG, WEBP 지원</p>
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>
      )}

      {/* 노이즈 강도 (img2img 전용) */}
      {mode === 'img2img' && (
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <label className="text-xs font-semibold text-green-soft tracking-wide uppercase">
              노이즈 강도 (Denoise)
            </label>
            <span className="text-sm font-bold text-green-bright bg-dark-card px-2.5 py-0.5 rounded-lg border border-dark-border">
              {denoise.toFixed(2)}
            </span>
          </div>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={denoise}
            onChange={(e) => setDenoise(Number(e.target.value))}
            className="w-full"
            style={{
              background: `linear-gradient(to right, #22c55e ${(denoise - 0.1) / 0.9 * 100}%, #2a4a2a ${(denoise - 0.1) / 0.9 * 100}%)`,
            }}
          />
          <div className="flex justify-between text-[10px] text-txt-muted">
            <span>원본 유지 (0.1)</span>
            <span>완전 변환 (1.0)</span>
          </div>
        </div>
      )}

      {/* 생성 버튼 */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={`w-full py-3.5 rounded-xl font-bold text-sm tracking-wide
                    flex items-center justify-center gap-2 transition-all duration-200
                    ${canSubmit
                      ? 'bg-green-active text-dark-bg hover:bg-green-bright active:scale-95 shadow-[0_0_20px_rgba(34,197,94,0.3)]'
                      : 'bg-dark-border text-txt-muted cursor-not-allowed'
                    }`}
      >
        {isLoading ? (
          <>
            <span className="w-4 h-4 border-2 border-dark-bg/30 border-t-dark-bg rounded-full animate-spin" />
            생성 중...
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {mode === 'text2img' ? '이미지 생성' : '이미지 변환'}
          </>
        )}
      </button>
    </div>
  )
}
