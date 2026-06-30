'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/axios';
import StyleSelector from '../../components/ControlPanel/StyleSelector';
import PromptInput from '../../components/ControlPanel/PromptInput';
import RatioSelector from '../../components/ControlPanel/RatioSelector';
import ImageUpload from '../../components/ControlPanel/ImageUpload';
import ImagePreview from '../../components/PreviewPanel/ImagePreview';
import WarningBanner from '../../components/PreviewPanel/WarningBanner';

// Webtoon 모델 기반 선택지
const GENRE_OPTIONS = [
  { value: 'romance', label: '로맨스' },
  { value: 'action',  label: '액션' },
  { value: 'fantasy', label: '판타지' },
  { value: 'comedy',  label: '개그' },
  { value: 'horror',  label: '공포' },
  { value: 'drama',   label: '드라마' },
  { value: 'daily',   label: '일상' },
  { value: 'sports',  label: '스포츠' },
  { value: 'etc',     label: '기타' },
];

const STATUS_OPTIONS = [
  { value: 'draft',     label: '초안' },
  { value: 'ongoing',   label: '연재 중' },
  { value: 'completed', label: '완결' },
  { value: 'hiatus',    label: '휴재' },
];

// 저장된 컷 목록 (실제 구현 시 API 연동)
type SavedCut = { id: number; order: number; image: string | null; caption: string };
const SAMPLE_CUTS: SavedCut[] = [];

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

export default function GeneratorPage() {
  const router = useRouter();

  // ── 웹툰 프로젝트 폼 상태 (Webtoon 모델 필드 기반) ──
  const [title, setTitle]             = useState('');
  const [genre, setGenre]             = useState('etc');
  const [status, setStatus]           = useState('draft');
  const [description, setDescription] = useState('');
  const [coverPreview, setCoverPreview] = useState<string | null>(null);
  const [coverFile, setCoverFile]     = useState<File | null>(null);
  const [saving, setSaving]           = useState(false);
  const coverInputRef = useRef<HTMLInputElement>(null);

  const handleCoverChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCoverFile(file);
    setCoverPreview(URL.createObjectURL(file));
  };

  // 웹툰 저장 (POST /api/webtoons/)
  const handleSubmit = async () => {
    if (!title.trim() || saving) return;
    setSaving(true);
    const Swal = (await import('sweetalert2')).default;
    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('genre', genre);
      formData.append('status', status);
      formData.append('description', description);
      if (coverFile) formData.append('cover_image', coverFile);

      await api.post('/api/webtoons/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      await Swal.fire({
        icon: 'success', title: '저장 완료', text: '웹툰이 등록되었습니다.',
        confirmButtonColor: '#00C73C', timer: 1400, showConfirmButton: false,
      });
      router.push('/dashboard/ai_image_generator');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })
        ?.response?.data?.message ?? '저장 중 오류가 발생했습니다.';
      await Swal.fire({ icon: 'error', title: '저장 실패', text: msg, confirmButtonColor: '#00C73C' });
    } finally {
      setSaving(false);
    }
  };

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
            새 웹툰 만들기
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

        {/* ────────────────────────────────────────
            LEFT: 웹툰 프로젝트 설정 (300px)
            Webtoon 모델: title, genre, status, description, cover_image
        ──────────────────────────────────────── */}
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
            <p className="text-sm font-bold" style={{ color: 'var(--dash-text)' }}>웹툰 프로젝트 설정</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--dash-text-muted)' }}>작품 기본 정보를 입력하세요</p>
          </div>

          <div className="flex flex-col flex-1 p-5 gap-5">

            {/* 제목 (title) */}
            <div>
              <label style={LABEL_STYLE}>제목</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="웹툰 제목을 입력하세요"
                style={INPUT_STYLE}
                maxLength={200}
              />
              <div className="text-right mt-1">
                <span className="text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                  {title.length}/200
                </span>
              </div>
            </div>

            {/* 장르 (genre) */}
            <div>
              <label style={LABEL_STYLE}>장르</label>
              <select
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                style={{ ...INPUT_STYLE, cursor: 'pointer', appearance: 'none',
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23555555'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                  backgroundSize: '14px',
                  paddingRight: '32px',
                }}
              >
                {GENRE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value} style={{ backgroundColor: '#2A2A2A' }}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 연재 상태 (status) */}
            <div>
              <label style={LABEL_STYLE}>연재 상태</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                style={{ ...INPUT_STYLE, cursor: 'pointer', appearance: 'none',
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23555555'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                  backgroundSize: '14px',
                  paddingRight: '32px',
                }}
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value} style={{ backgroundColor: '#2A2A2A' }}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 설명 (description) */}
            <div>
              <label style={LABEL_STYLE}>작품 설명</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="작품 소개를 간단히 입력하세요."
                rows={4}
                style={{
                  ...INPUT_STYLE,
                  resize: 'none',
                  minHeight: '90px',
                  lineHeight: '1.6',
                }}
              />
            </div>

            {/* 커버 이미지 (cover_image) */}
            <div>
              <label style={LABEL_STYLE}>커버 이미지</label>
              <div
                className="relative rounded-lg overflow-hidden cursor-pointer transition-opacity hover:opacity-80"
                style={{
                  aspectRatio: '3/4',
                  backgroundColor: 'var(--dash-surface)',
                  border: '1px dashed var(--dash-border)',
                }}
                onClick={() => coverInputRef.current?.click()}
              >
                {coverPreview ? (
                  <img
                    src={coverPreview}
                    alt="커버 미리보기"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      style={{ color: 'var(--dash-text-muted)' }}>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M12 4v16m8-8H4" />
                    </svg>
                    <span className="text-xs text-center px-4" style={{ color: 'var(--dash-text-muted)', lineHeight: 1.5 }}>
                      클릭하여 커버 이미지 업로드
                      <br />(권장: 3:4 비율)
                    </span>
                  </div>
                )}
                <input
                  ref={coverInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleCoverChange}
                />
              </div>
            </div>

            {/* 저장 버튼 */}
            <div className="mt-auto pt-2" style={{ borderTop: '1px solid var(--dash-border)' }}>
              <button
                onClick={handleSubmit}
                className="w-full py-3 rounded-lg text-sm font-bold transition-opacity hover:opacity-85 mt-4"
                style={{
                  backgroundColor: '#00C73C', color: '#FFFFFF',
                  opacity: !title.trim() || saving ? 0.6 : 1,
                  cursor: !title.trim() || saving ? 'not-allowed' : 'pointer',
                }}
                disabled={!title.trim() || saving}
              >
                {saving ? '저장 중...' : title.trim() ? '웹툰 저장하기' : '제목을 입력해 주세요'}
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
            RIGHT: 이미지 프리뷰 + 저장된 컷 목록
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
                {/* 복사 */}
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
                {/* 재생성 */}
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

              {/* 컷으로 추가 */}
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

          {/* ── 저장된 컷 목록 (WebtoonCut 모델 기반) ── */}
          <div
            className="flex-1 px-6 pb-6"
            style={{ borderTop: '1px solid var(--dash-border)' }}
          >
            <div className="flex items-center justify-between py-4 mb-2">
              <p className="text-sm font-bold" style={{ color: 'var(--dash-text)' }}>
                저장된 컷
                <span
                  className="ml-2 text-xs px-2 py-0.5 rounded font-medium"
                  style={{ backgroundColor: 'var(--dash-surface)', color: 'var(--dash-text-muted)' }}
                >
                  {SAMPLE_CUTS.length}개
                </span>
              </p>
              {SAMPLE_CUTS.length > 0 && (
                <button
                  className="text-xs transition-opacity hover:opacity-70"
                  style={{ color: '#00C73C' }}
                >
                  순서 편집
                </button>
              )}
            </div>

            {SAMPLE_CUTS.length > 0 ? (
              /* 컷 가로 스크롤 목록 */
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
                      <img src={cut.image} alt={`컷 ${cut.order}`}
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
                    <span
                      className="absolute top-1.5 left-1.5 text-xs font-bold px-1.5 py-0.5 rounded"
                      style={{ backgroundColor: 'rgba(0,0,0,0.65)', color: '#FFFFFF', fontSize: '10px' }}
                    >
                      {cut.order}
                    </span>
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
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                  AI로 이미지를 생성하고 "컷으로 추가"를 눌러 컷을 등록하세요.
                </p>
              </div>
            )}
          </div>
        </main>

      </div>
    </div>
  );
}
