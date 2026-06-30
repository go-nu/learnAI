'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/axios';

// 장르/상태 선택지
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

// ── 공통 스타일 ──
const INPUT_STYLE: React.CSSProperties = {
  width: '100%',
  backgroundColor: 'var(--dash-surface)',
  color: 'var(--dash-text)',
  border: '1px solid var(--dash-border)',
  borderRadius: '8px',
  padding: '9px 12px',
  fontSize: '14px',
  outline: 'none',
  caretColor: 'var(--dash-text)',
};

const LABEL_STYLE: React.CSSProperties = {
  display: 'block',
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--dash-text-muted)',
  textTransform: 'uppercase' as const,
  letterSpacing: '0.05em',
  marginBottom: '6px',
};

const SELECT_STYLE: React.CSSProperties = {
  ...INPUT_STYLE,
  cursor: 'pointer',
  appearance: 'none' as const,
  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23555555'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`,
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right 10px center',
  backgroundSize: '14px',
  paddingRight: '32px',
};

// useSearchParams를 사용하는 내부 컴포넌트 (Suspense 필요)
function EditForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = searchParams.get('id');

  const [title, setTitle]             = useState('');
  const [genre, setGenre]             = useState('etc');
  const [status, setStatus]           = useState('draft');
  const [description, setDescription] = useState('');
  const [coverPreview, setCoverPreview] = useState<string | null>(null);
  const [coverFile, setCoverFile]     = useState<File | null>(null);
  const [fetching, setFetching]       = useState(true);
  const [saving, setSaving]           = useState(false);
  const [fetchError, setFetchError]   = useState('');
  const coverInputRef = useRef<HTMLInputElement>(null);

  // 기존 데이터 로드
  useEffect(() => {
    if (!id) {
      setFetchError('웹툰 ID가 없습니다.');
      setFetching(false);
      return;
    }
    api.get(`/api/webtoons/${id}/`)
      .then((res) => {
        const d = res.data.data;
        setTitle(d.title ?? '');
        setGenre(d.genre ?? 'etc');
        setStatus(d.status ?? 'draft');
        setDescription(d.description ?? '');
        if (d.cover_image) setCoverPreview(d.cover_image);
      })
      .catch(() => setFetchError('웹툰 정보를 불러오지 못했습니다.'))
      .finally(() => setFetching(false));
  }, [id]);

  const handleCoverChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCoverFile(file);
    setCoverPreview(URL.createObjectURL(file));
  };

  // 수정 저장 (PATCH /api/webtoons/{id}/)
  const handleSubmit = async () => {
    if (!title.trim() || saving || !id) return;
    setSaving(true);
    const Swal = (await import('sweetalert2')).default;
    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('genre', genre);
      formData.append('status', status);
      formData.append('description', description);
      if (coverFile) formData.append('cover_image', coverFile);

      await api.patch(`/api/webtoons/${id}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      await Swal.fire({
        icon: 'success', title: '수정 완료', text: '웹툰이 수정되었습니다.',
        confirmButtonColor: '#00C73C', timer: 1400, showConfirmButton: false,
      });
      router.push('/dashboard/ai_image_generator');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })
        ?.response?.data?.message ?? '수정 중 오류가 발생했습니다.';
      await Swal.fire({ icon: 'error', title: '수정 실패', text: msg, confirmButtonColor: '#00C73C' });
    } finally {
      setSaving(false);
    }
  };

  // ── 렌더 ──
  return (
    <div
      className="flex flex-col h-screen"
      style={{ backgroundColor: 'var(--dash-bg)', color: 'var(--dash-text)', fontFamily: "'Noto Sans KR', Arial, sans-serif" }}
    >
      {/* ── GNB ── */}
      <header
        className="flex items-center justify-between px-6 h-14 flex-shrink-0"
        style={{ backgroundColor: 'var(--dash-panel)', borderBottom: '1px solid var(--dash-border)', zIndex: 10 }}
      >
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
            웹툰 작품
          </Link>
          <span style={{ color: 'var(--dash-text-muted)' }}>›</span>
          <span className="text-sm font-medium" style={{ color: 'var(--dash-text)' }}>웹툰 수정</span>
        </div>
      </header>

      {/* ── 본문 ── */}
      <main className="flex-1 overflow-y-auto scrollbar-hidden">
        <div className="max-w-2xl mx-auto px-6 py-10">

          {/* 뒤로가기 */}
          <Link
            href="/dashboard/ai_image_generator"
            className="inline-flex items-center gap-1.5 text-sm mb-6 transition-opacity hover:opacity-70"
            style={{ color: 'var(--dash-text-sub)', textDecoration: 'none' }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            목록으로 돌아가기
          </Link>

          {/* 카드 */}
          <div
            className="rounded-2xl p-8"
            style={{ backgroundColor: 'var(--dash-panel)', border: '1px solid var(--dash-border)' }}
          >
            <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--dash-text)' }}>웹툰 수정</h1>
            <p className="text-sm mb-8" style={{ color: 'var(--dash-text-muted)' }}>작품 정보를 수정하세요</p>

            {/* 에러 상태 */}
            {fetchError && (
              <div
                className="rounded-lg px-4 py-3 mb-6 text-sm"
                style={{ backgroundColor: 'rgba(239,68,68,0.1)', color: '#EF4444', border: '1px solid rgba(239,68,68,0.2)' }}
              >
                {fetchError}
              </div>
            )}

            {/* 로딩 */}
            {fetching ? (
              <div className="flex items-center justify-center py-20">
                <div
                  className="w-8 h-8 rounded-full border-2 animate-spin"
                  style={{ borderColor: 'var(--dash-border)', borderTopColor: '#00C73C' }}
                />
              </div>
            ) : !fetchError && (
              <div className="flex flex-col gap-6">

                {/* 제목 */}
                <div>
                  <label style={LABEL_STYLE}>제목 *</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="웹툰 제목을 입력하세요"
                    style={INPUT_STYLE}
                    maxLength={200}
                  />
                  <div className="text-right mt-1">
                    <span className="text-xs" style={{ color: 'var(--dash-text-muted)' }}>{title.length}/200</span>
                  </div>
                </div>

                {/* 장르 + 연재 상태 (2열) */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label style={LABEL_STYLE}>장르</label>
                    <select value={genre} onChange={(e) => setGenre(e.target.value)} style={SELECT_STYLE}>
                      {GENRE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value} style={{ backgroundColor: '#1A1A2E' }}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={LABEL_STYLE}>연재 상태</label>
                    <select value={status} onChange={(e) => setStatus(e.target.value)} style={SELECT_STYLE}>
                      {STATUS_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value} style={{ backgroundColor: '#1A1A2E' }}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* 작품 설명 */}
                <div>
                  <label style={LABEL_STYLE}>작품 설명</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="작품 소개를 간단히 입력하세요."
                    rows={4}
                    style={{ ...INPUT_STYLE, resize: 'none', lineHeight: '1.6' }}
                  />
                </div>

                {/* 커버 이미지 */}
                <div>
                  <label style={LABEL_STYLE}>커버 이미지</label>
                  <div className="flex items-start gap-4">
                    {/* 미리보기 */}
                    <div
                      className="relative rounded-lg overflow-hidden cursor-pointer transition-opacity hover:opacity-80 flex-shrink-0"
                      style={{
                        width: '120px', height: '160px',
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
                          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                            style={{ color: 'var(--dash-text-muted)' }}>
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                              d="M12 4v16m8-8H4" />
                          </svg>
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
                    {/* 안내 */}
                    <div className="pt-1">
                      <p className="text-sm font-medium mb-1" style={{ color: 'var(--dash-text)' }}>
                        {coverFile ? coverFile.name : '이미지 변경'}
                      </p>
                      <p className="text-xs mb-3" style={{ color: 'var(--dash-text-muted)', lineHeight: 1.5 }}>
                        클릭하여 새 커버 이미지를 업로드하세요.<br />권장 비율: 3:4
                      </p>
                      <button
                        type="button"
                        onClick={() => coverInputRef.current?.click()}
                        className="px-3 py-1.5 rounded text-xs transition-opacity hover:opacity-70"
                        style={{
                          backgroundColor: 'var(--dash-surface)',
                          border: '1px solid var(--dash-border)',
                          color: 'var(--dash-text-sub)',
                          cursor: 'pointer',
                        }}
                      >
                        이미지 선택
                      </button>
                    </div>
                  </div>
                </div>

                {/* 버튼 그룹 */}
                <div
                  className="flex items-center gap-3 pt-4"
                  style={{ borderTop: '1px solid var(--dash-border)' }}
                >
                  <Link
                    href="/dashboard/ai_image_generator"
                    className="flex-1 py-3 rounded-lg text-sm font-medium text-center transition-opacity hover:opacity-70"
                    style={{
                      backgroundColor: 'var(--dash-surface)',
                      border: '1px solid var(--dash-border)',
                      color: 'var(--dash-text-sub)',
                      textDecoration: 'none',
                    }}
                  >
                    취소
                  </Link>
                  <button
                    onClick={handleSubmit}
                    disabled={!title.trim() || saving}
                    className="flex-1 py-3 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
                    style={{
                      backgroundColor: '#00C73C',
                      color: '#FFFFFF',
                      opacity: !title.trim() || saving ? 0.6 : 1,
                      cursor: !title.trim() || saving ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {saving ? '저장 중...' : '수정 저장하기'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// useSearchParams requires Suspense boundary
export default function EditPage() {
  return (
    <Suspense
      fallback={
        <div
          className="flex items-center justify-center h-screen"
          style={{ backgroundColor: 'var(--dash-bg)' }}
        >
          <div
            className="w-8 h-8 rounded-full border-2 animate-spin"
            style={{ borderColor: 'rgba(255,255,255,0.1)', borderTopColor: '#00C73C' }}
          />
        </div>
      }
    >
      <EditForm />
    </Suspense>
  );
}
