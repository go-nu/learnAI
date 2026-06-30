'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';
import StyleSelector from '../../components/ControlPanel/StyleSelector';
import PromptInput from '../../components/ControlPanel/PromptInput';
import RatioSelector from '../../components/ControlPanel/RatioSelector';
import ImageUpload from '../../components/ControlPanel/ImageUpload';
import ImagePreview from '../../components/PreviewPanel/ImagePreview';
import WarningBanner from '../../components/PreviewPanel/WarningBanner';

// ── Webtoon 모델 기반 웹툰 선택 목록 (실제 구현 시 API로 교체) ──
const SAMPLE_WEBTOONS: { id: number; title: string }[] = [];

// ── WebtoonCut 모델 기반 컷 타입 ──
type EpisodeCut = { id: number; order: number; image: string | null; caption: string };
const SAMPLE_CUTS: EpisodeCut[] = [];

// ── 공통 인풋 스타일 ──
const INPUT_STYLE: React.CSSProperties = {
  width: '100%',
  backgroundColor: 'var(--dash-surface)',
  color: 'var(--dash-text)',
  border: '1px solid var(--dash-border)',
  borderRadius: '8px',
  padding: '9px 12px',
  fontSize: '13px',
  outline: 'none',
  caretColor: 'var(--dash-text)',
};

const LABEL_STYLE: React.CSSProperties = {
  display: 'block',
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--dash-text-muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  marginBottom: '6px',
};

export default function EpisodePage() {
  // ── WebtoonEpisode 모델 필드 기반 폼 상태 ──
  const [selectedWebtoon, setSelectedWebtoon] = useState('');
  const [episodeNumber, setEpisodeNumber]     = useState(1);
  const [title, setTitle]                     = useState('');
  const [isPublished, setIsPublished]         = useState(false);
  const [publishedAt, setPublishedAt]         = useState('');
  const [thumbnailPreview, setThumbnailPreview] = useState<string | null>(null);
  const thumbnailInputRef = useRef<HTMLInputElement>(null);

  const handleThumbnailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setThumbnailPreview(URL.createObjectURL(file));
  };

  const isSaveable = !!title.trim() && !!selectedWebtoon;

  return (
    <div
      className="flex flex-col h-screen"
      style={{ backgroundColor: 'var(--dash-bg)', color: 'var(--dash-text)' }}
    >

      {/* ── 상단 GNB ── */}
      <header
        className="flex items-center justify-between px-6 h-14 flex-shrink-0"
        style={{ backgroundColor: 'var(--dash-panel)', borderBottom: '1px solid var(--dash-border)', zIndex: 10 }}
      >
        {/* 로고 + 브레드크럼 */}
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="text-lg font-black tracking-tight transition-opacity hover:opacity-70"
            style={{ color: 'var(--dash-text)', textDecoration: 'none' }}
          >
            ToonCraft
          </Link>
          <span style={{ color: 'var(--dash-text-muted)' }}>›</span>
          <Link
            href="/dashboard/ai_image_generator"
            className="text-sm transition-opacity hover:opacity-70"
            style={{ color: 'var(--dash-text-sub)', textDecoration: 'none' }}
          >
            AI 이미지 만들기
          </Link>
          <span style={{ color: 'var(--dash-text-muted)' }}>›</span>
          <span className="text-sm font-medium" style={{ color: 'var(--dash-text)' }}>
            에피소드 추가
          </span>
        </div>

        {/* 우측: 언어 + 유저 아바타 */}
        <div className="flex items-center gap-3">
          <button
            className="flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg"
            style={{ color: 'var(--dash-text-sub)', backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)' }}
          >
            한국어
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <button
            className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
            style={{ backgroundColor: 'var(--dash-btn-primary)', color: 'var(--dash-btn-primary-text)' }}
          >
            U
          </button>
        </div>
      </header>

      {/* ── 본문 3단 레이아웃 ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ────────────────────────────────────────────
            LEFT: 에피소드 설정 (300px)
            WebtoonEpisode 모델: webtoon(FK), episode_number,
            title, thumbnail, is_published, published_at
        ──────────────────────────────────────────── */}
        <aside
          className="flex flex-col flex-shrink-0 overflow-y-auto scrollbar-hidden"
          style={{
            width: '300px',
            backgroundColor: 'var(--dash-panel)',
            borderRight: '1px solid var(--dash-border)',
          }}
        >
          {/* 패널 헤더 */}
          <div
            className="px-5 py-4 flex-shrink-0"
            style={{ borderBottom: '1px solid var(--dash-border)' }}
          >
            <p className="text-sm font-bold" style={{ color: 'var(--dash-text)' }}>에피소드 설정</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--dash-text-muted)' }}>회차 정보를 입력하세요</p>
          </div>

          <div className="flex flex-col flex-1 p-5 gap-5">

            {/* 웹툰 선택 (webtoon FK) */}
            <div>
              <label style={LABEL_STYLE}>웹툰 선택</label>
              {SAMPLE_WEBTOONS.length > 0 ? (
                <select
                  value={selectedWebtoon}
                  onChange={(e) => setSelectedWebtoon(e.target.value)}
                  style={{
                    ...INPUT_STYLE, cursor: 'pointer', appearance: 'none',
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23555555'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 10px center',
                    backgroundSize: '14px',
                    paddingRight: '32px',
                  }}
                >
                  <option value="">웹툰을 선택하세요</option>
                  {SAMPLE_WEBTOONS.map((w) => (
                    <option key={w.id} value={String(w.id)} style={{ backgroundColor: '#2A2A2A' }}>
                      {w.title}
                    </option>
                  ))}
                </select>
              ) : (
                /* 웹툰 없을 때 안내 */
                <div
                  className="rounded-lg px-3 py-3 text-xs flex items-start gap-2"
                  style={{ backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)', color: 'var(--dash-text-sub)', lineHeight: 1.6 }}
                >
                  <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    style={{ color: '#E6A817' }}>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                  </svg>
                  <span>
                    등록된 웹툰이 없습니다.{' '}
                    <Link
                      href="/dashboard/ai_image_generator/generator"
                      style={{ color: '#00C73C', textDecoration: 'none', fontWeight: 600 }}
                    >
                      웹툰 먼저 만들기 →
                    </Link>
                  </span>
                </div>
              )}
            </div>

            {/* 회차 번호 (episode_number) */}
            <div>
              <label style={LABEL_STYLE}>회차 번호</label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setEpisodeNumber((n) => Math.max(1, n - 1))}
                  className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 transition-opacity hover:opacity-70"
                  style={{ backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)', color: 'var(--dash-text-sub)' }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                  </svg>
                </button>
                <input
                  type="number"
                  value={episodeNumber}
                  min={1}
                  onChange={(e) => setEpisodeNumber(Math.max(1, parseInt(e.target.value) || 1))}
                  style={{ ...INPUT_STYLE, textAlign: 'center', width: '100%' }}
                />
                <button
                  onClick={() => setEpisodeNumber((n) => n + 1)}
                  className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 transition-opacity hover:opacity-70"
                  style={{ backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)', color: 'var(--dash-text-sub)' }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </button>
              </div>
              <p className="mt-1 text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                {episodeNumber}화로 등록됩니다.
              </p>
            </div>

            {/* 에피소드 제목 (title) */}
            <div>
              <label style={LABEL_STYLE}>에피소드 제목</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="에피소드 제목을 입력하세요"
                maxLength={200}
                style={INPUT_STYLE}
              />
              <div className="text-right mt-1">
                <span className="text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                  {title.length}/200
                </span>
              </div>
            </div>

            {/* 썸네일 (thumbnail) */}
            <div>
              <label style={LABEL_STYLE}>썸네일 이미지</label>
              <div
                className="relative rounded-lg overflow-hidden cursor-pointer transition-opacity hover:opacity-80"
                style={{
                  aspectRatio: '16/9',
                  backgroundColor: 'var(--dash-surface)',
                  border: '1px dashed var(--dash-border)',
                }}
                onClick={() => thumbnailInputRef.current?.click()}
              >
                {thumbnailPreview ? (
                  <img
                    src={thumbnailPreview}
                    alt="썸네일 미리보기"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                    <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      style={{ color: 'var(--dash-text-muted)' }}>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span className="text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                      썸네일 업로드 (권장: 16:9)
                    </span>
                  </div>
                )}
                <input
                  ref={thumbnailInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleThumbnailChange}
                />
              </div>
            </div>

            {/* 발행 여부 (is_published) — 토글 스위치 */}
            <div>
              <label style={LABEL_STYLE}>발행 여부</label>
              <div className="flex items-center justify-between">
                <span className="text-sm" style={{ color: isPublished ? '#00C73C' : 'var(--dash-text-sub)' }}>
                  {isPublished ? '발행됨' : '미발행'}
                </span>
                <button
                  onClick={() => setIsPublished((v) => !v)}
                  className="relative flex-shrink-0 transition-colors"
                  style={{
                    width: '44px',
                    height: '24px',
                    borderRadius: '12px',
                    backgroundColor: isPublished ? '#00C73C' : 'var(--dash-surface)',
                    border: `1px solid ${isPublished ? '#00C73C' : 'var(--dash-border)'}`,
                  }}
                >
                  <span
                    className="absolute top-0.5 transition-all"
                    style={{
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      backgroundColor: '#FFFFFF',
                      left: isPublished ? '22px' : '2px',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.4)',
                    }}
                  />
                </button>
              </div>
            </div>

            {/* 발행일 (published_at) — is_published=true 일 때만 표시 */}
            {isPublished && (
              <div>
                <label style={LABEL_STYLE}>발행일</label>
                <input
                  type="datetime-local"
                  value={publishedAt}
                  onChange={(e) => setPublishedAt(e.target.value)}
                  style={{
                    ...INPUT_STYLE,
                    colorScheme: 'dark',
                  }}
                />
              </div>
            )}

            {/* 저장 버튼 */}
            <div className="mt-auto pt-2" style={{ borderTop: '1px solid var(--dash-border)' }}>
              <button
                className="w-full py-3 rounded-lg text-sm font-bold transition-opacity mt-4"
                style={{
                  backgroundColor: isSaveable ? '#00C73C' : 'var(--dash-surface)',
                  color: isSaveable ? '#FFFFFF' : 'var(--dash-text-muted)',
                  border: isSaveable ? 'none' : '1px solid var(--dash-border)',
                  cursor: isSaveable ? 'pointer' : 'not-allowed',
                  opacity: isSaveable ? 1 : 0.6,
                }}
                disabled={!isSaveable}
              >
                {!selectedWebtoon
                  ? '웹툰을 먼저 선택해 주세요'
                  : !title.trim()
                  ? '제목을 입력해 주세요'
                  : `${episodeNumber}화 저장하기`}
              </button>
            </div>
          </div>
        </aside>

        {/* ────────────────────────────────────────
            MIDDLE: AI 컷 생성 컨트롤 패널 (346px)
        ──────────────────────────────────────── */}
        <aside
          className="flex flex-col flex-shrink-0 p-4 overflow-y-auto scrollbar-hidden"
          style={{
            width: '346px',
            backgroundColor: 'var(--dash-panel)',
            borderRight: '1px solid var(--dash-border)',
          }}
        >
          {/* 뒤로가기 */}
          <Link
            href="/dashboard/ai_image_generator"
            className="flex items-center gap-1 text-sm mb-5 w-fit transition-opacity hover:opacity-70"
            style={{ color: 'var(--dash-text-sub)', textDecoration: 'none' }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            AI 이미지 만들기
          </Link>

          <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: 'var(--dash-text-muted)' }}>
            AI 컷 생성
          </p>

          <StyleSelector />
          <PromptInput />
          <RatioSelector />
          <ImageUpload />

          {/* 생성 버튼 */}
          <div className="mt-auto pt-4" style={{ borderTop: '1px solid var(--dash-border)' }}>
            <div
              className="rounded-lg px-3 py-2 mb-4 text-center text-xs"
              style={{ backgroundColor: 'var(--dash-surface)', color: 'var(--dash-text-sub)', border: '1px solid var(--dash-border)' }}
            >
              매일매일 1000크레딧 충전!
            </div>
            <div className="flex gap-2">
              <button
                className="flex-1 py-3 rounded-lg text-sm font-medium transition-opacity hover:opacity-70"
                style={{ backgroundColor: 'var(--dash-btn-secondary)', color: 'var(--dash-text-sub)', border: '1px solid var(--dash-border)' }}
              >
                초기화
              </button>
              <button
                className="py-3 rounded-lg text-sm font-bold transition-opacity hover:opacity-80"
                style={{ backgroundColor: 'var(--dash-btn-primary)', color: 'var(--dash-btn-primary-text)', flexGrow: 2 }}
              >
                생성
              </button>
            </div>
          </div>
        </aside>

        {/* ────────────────────────────────────────
            RIGHT: 이미지 프리뷰 + 에피소드 컷 목록
            WebtoonCut 모델: order, image, caption
        ──────────────────────────────────────── */}
        <main
          className="flex-1 flex flex-col overflow-y-auto scrollbar-hidden"
          style={{ backgroundColor: 'var(--dash-bg)' }}
        >
          {/* 경고 배너 + 이미지 프리뷰 */}
          <div className="p-6 flex-shrink-0">
            <WarningBanner />

            {/* 상단 액션 버튼 */}
            <div className="flex items-center justify-between mt-4 mb-3">
              <div className="flex items-center gap-2">
                <button
                  className="p-2 rounded-lg transition-opacity hover:opacity-70"
                  style={{ backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)', color: 'var(--dash-text-sub)' }}
                  title="복사"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
                <button
                  className="p-2 rounded-lg transition-opacity hover:opacity-70"
                  style={{ backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)', color: 'var(--dash-text-sub)' }}
                  title="재생성"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              </div>
              <button
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-opacity hover:opacity-85"
                style={{ backgroundColor: '#00C73C', color: '#FFFFFF' }}
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                컷으로 추가
              </button>
            </div>

            <ImagePreview />
          </div>

          {/* ── 에피소드 컷 목록 ── */}
          <div
            className="flex-1 px-6 pb-6"
            style={{ borderTop: '1px solid var(--dash-border)' }}
          >
            <div className="flex items-center justify-between py-4 mb-2">
              <div className="flex items-center gap-3">
                <p className="text-sm font-bold" style={{ color: 'var(--dash-text)' }}>
                  에피소드 컷
                </p>
                <span
                  className="text-xs px-2 py-0.5 rounded font-medium"
                  style={{ backgroundColor: 'var(--dash-surface)', color: 'var(--dash-text-muted)' }}
                >
                  {SAMPLE_CUTS.length}개
                </span>
                {/* 회차 표시 배지 */}
                {title.trim() && (
                  <span
                    className="text-xs px-2 py-0.5 rounded font-medium"
                    style={{ backgroundColor: 'rgba(0,199,60,0.12)', color: '#00C73C', border: '1px solid rgba(0,199,60,0.25)' }}
                  >
                    {episodeNumber}화 · {title}
                  </span>
                )}
              </div>
              {SAMPLE_CUTS.length > 0 && (
                <button className="text-xs transition-opacity hover:opacity-70" style={{ color: '#00C73C' }}>
                  순서 편집
                </button>
              )}
            </div>

            {SAMPLE_CUTS.length > 0 ? (
              /* 컷 가로 스크롤 (WebtoonCut: order, image, caption) */
              <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hidden">
                {SAMPLE_CUTS.map((cut) => (
                  <div
                    key={cut.id}
                    className="flex-shrink-0 rounded-lg overflow-hidden"
                    style={{
                      width: '100px',
                      aspectRatio: '3/4',
                      backgroundColor: 'var(--dash-surface)',
                      border: '1px solid var(--dash-border)',
                      position: 'relative',
                    }}
                  >
                    {cut.image ? (
                      <img src={cut.image} alt={`${cut.order}번 컷`}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center"
                        style={{ color: 'var(--dash-text-muted)' }}>
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                    )}
                    {/* 순서 배지 */}
                    <span
                      className="absolute top-1.5 left-1.5 font-bold rounded"
                      style={{ backgroundColor: 'rgba(0,0,0,0.65)', color: '#FFFFFF', fontSize: '10px', padding: '1px 5px' }}
                    >
                      {cut.order}
                    </span>
                    {/* 삭제 버튼 */}
                    <button
                      className="absolute top-1.5 right-1.5 rounded flex items-center justify-center"
                      style={{ width: '18px', height: '18px', backgroundColor: 'rgba(0,0,0,0.65)' }}
                      title="삭제"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        style={{ color: '#EF4444' }}>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    {/* 캡션 */}
                    {cut.caption && (
                      <div
                        className="absolute bottom-0 left-0 right-0 px-2 py-1 text-center"
                        style={{ backgroundColor: 'rgba(0,0,0,0.6)', fontSize: '9px', color: '#FFFFFF', lineHeight: 1.4,
                          overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}
                      >
                        {cut.caption}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              /* 빈 상태 */
              <div
                className="flex flex-col items-center justify-center py-10 rounded-xl gap-3"
                style={{ backgroundColor: 'var(--dash-surface)', border: '1px dashed var(--dash-border)' }}
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  style={{ color: 'var(--dash-text-muted)' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
                </svg>
                <p className="text-xs text-center" style={{ color: 'var(--dash-text-muted)', lineHeight: 1.6 }}>
                  AI로 이미지를 생성하고{' '}
                  <span style={{ color: '#00C73C', fontWeight: 600 }}>"컷으로 추가"</span>를 눌러<br />
                  이 에피소드의 컷을 등록하세요.
                </p>
              </div>
            )}
          </div>
        </main>

      </div>
    </div>
  );
}
