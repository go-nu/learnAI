'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/axios';

// 장르/상태 레이블 매핑
const GENRE_LABEL: Record<string, string> = {
  romance: '로맨스', action: '액션', fantasy: '판타지', comedy: '개그',
  horror: '공포', drama: '드라마', daily: '일상', sports: '스포츠', etc: '기타',
};

const STATUS_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  draft:     { bg: 'rgba(85,85,85,0.35)',      color: '#AAAAAA', label: '초안' },
  ongoing:   { bg: 'rgba(0,199,60,0.15)',       color: '#00C73C', label: '연재 중' },
  completed: { bg: 'rgba(59,130,246,0.15)',     color: '#60A5FA', label: '완결' },
  hiatus:    { bg: 'rgba(230,168,23,0.15)',     color: '#E6A817', label: '휴재' },
};

type Webtoon = {
  id: number; title: string; genre: string; status: string;
  description: string; cover_image: string | null; created_at: string;
};

const PAGE_SIZE = 10;

export default function WebtoonWorksContent() {
  const router = useRouter();
  const [webtoons, setWebtoons]       = useState<Webtoon[]>([]);
  const [total, setTotal]             = useState(0);
  const [totalPages, setTotalPages]   = useState(1);
  const [page, setPage]               = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch]           = useState('');
  const [loading, setLoading]         = useState(false);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 목록 조회
  const fetchWebtoons = useCallback(async (pg: number, q: string) => {
    setLoading(true);
    try {
      const res = await api.get('/api/webtoons/', {
        params: { page: pg, page_size: PAGE_SIZE, ...(q ? { search: q } : {}) },
      });
      const d = res.data.data;
      setWebtoons(d.webtoons);
      setTotal(d.total);
      setTotalPages(d.total_pages);
    } catch {
      setWebtoons([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWebtoons(page, search);
  }, [page, search, fetchWebtoons]);

  // 검색 디바운스 (500ms)
  const handleSearchChange = (val: string) => {
    setSearchInput(val);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setPage(1);
      setSearch(val);
    }, 500);
  };

  // 삭제 (SweetAlert2 확인)
  const handleDelete = async (id: number, title: string) => {
    const Swal = (await import('sweetalert2')).default;
    const { isConfirmed } = await Swal.fire({
      title: '웹툰 삭제',
      html: `<b>"${title}"</b>을(를) 삭제하시겠습니까?<br/><span style="font-size:13px;color:#888">삭제된 웹툰은 복구할 수 없습니다.</span>`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
      confirmButtonColor: '#EF4444',
      cancelButtonColor: '#4B5563',
    });
    if (!isConfirmed) return;

    try {
      await api.delete(`/api/webtoons/${id}/`);
      await Swal.fire({
        icon: 'success', title: '삭제 완료', text: '웹툰이 삭제되었습니다.',
        confirmButtonColor: '#00C73C', timer: 1200, showConfirmButton: false,
      });
      // 현재 페이지에 항목이 하나뿐이면 이전 페이지로
      const nextPage = webtoons.length === 1 && page > 1 ? page - 1 : page;
      setPage(nextPage);
      fetchWebtoons(nextPage, search);
    } catch {
      await Swal.fire({ icon: 'error', title: '삭제 실패', text: '삭제 중 오류가 발생했습니다.', confirmButtonColor: '#00C73C' });
    }
  };

  return (
    <main
      className="flex-1 flex flex-col overflow-y-auto scrollbar-hidden"
      style={{ backgroundColor: 'var(--dash-bg)' }}
    >
      {/* ── 섹션 헤더 ── */}
      <div
        className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: '1px solid var(--dash-border)' }}
      >
        <div>
          <h1 className="text-lg font-bold" style={{ color: 'var(--dash-text)' }}>웹툰 작품</h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--dash-text-muted)' }}>총 {total}개</p>
        </div>
        <Link
          href="/dashboard/ai_image_generator/generator"
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
          style={{ backgroundColor: '#00C73C', color: '#FFFFFF', textDecoration: 'none' }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          새 웹툰 추가
        </Link>
      </div>

      {/* ── 검색 바 ── */}
      <div className="px-8 pt-5 pb-3 flex-shrink-0">
        <div className="relative" style={{ maxWidth: '360px' }}>
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
            style={{ color: 'var(--dash-text-muted)' }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="제목으로 검색..."
            style={{
              width: '100%',
              paddingLeft: '36px',
              paddingRight: searchInput ? '36px' : '12px',
              paddingTop: '8px', paddingBottom: '8px',
              backgroundColor: 'var(--dash-surface)',
              border: '1px solid var(--dash-border)',
              borderRadius: '8px',
              fontSize: '13px',
              color: 'var(--dash-text)',
              outline: 'none',
            }}
          />
          {searchInput && (
            <button
              onClick={() => { setSearchInput(''); setPage(1); setSearch(''); }}
              style={{
                position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--dash-text-muted)', padding: 0, display: 'flex',
              }}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* ── 테이블 ── */}
      <div className="flex-1 px-8 pb-4 overflow-x-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div
              className="w-8 h-8 rounded-full border-2 animate-spin"
              style={{ borderColor: 'var(--dash-border)', borderTopColor: '#00C73C' }}
            />
          </div>
        ) : (
          <table className="w-full" style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--dash-surface)' }}>
                {[
                  { label: '커버', width: '72px' },
                  { label: '제목', width: 'auto' },
                  { label: '장르', width: '90px' },
                  { label: '연재 상태', width: '100px' },
                  { label: '생성일', width: '110px' },
                  { label: '관리', width: '100px' },
                ].map((col, i) => (
                  <th
                    key={col.label}
                    className="text-left px-4 py-3 text-xs font-bold uppercase tracking-wider"
                    style={{
                      color: 'var(--dash-text-muted)',
                      width: col.width,
                      borderBottom: '1px solid var(--dash-border)',
                      borderRadius: i === 0 ? '8px 0 0 8px' : i === 5 ? '0 8px 8px 0' : undefined,
                    }}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {webtoons.length > 0 ? (
                webtoons.map((webtoon) => {
                  const ss = STATUS_STYLE[webtoon.status] ?? STATUS_STYLE.draft;
                  return (
                    <tr key={webtoon.id} style={{ borderBottom: '1px solid var(--dash-border)' }}>
                      {/* 커버 이미지 */}
                      <td className="px-4 py-3">
                        <div
                          className="rounded overflow-hidden flex items-center justify-center"
                          style={{ width: '40px', height: '54px', backgroundColor: 'var(--dash-surface)', flexShrink: 0 }}
                        >
                          {webtoon.cover_image ? (
                            <img src={webtoon.cover_image} alt={webtoon.title}
                              style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          ) : (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                              style={{ color: 'var(--dash-text-muted)' }}>
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                          )}
                        </div>
                      </td>
                      {/* 제목 */}
                      <td className="px-4 py-3 text-sm font-medium" style={{ color: 'var(--dash-text)' }}>
                        {webtoon.title}
                      </td>
                      {/* 장르 */}
                      <td className="px-4 py-3">
                        <span className="px-2.5 py-1 rounded text-xs"
                          style={{ backgroundColor: 'var(--dash-surface)', color: 'var(--dash-text-sub)' }}>
                          {GENRE_LABEL[webtoon.genre] ?? webtoon.genre}
                        </span>
                      </td>
                      {/* 연재 상태 */}
                      <td className="px-4 py-3">
                        <span className="px-2.5 py-1 rounded text-xs font-medium"
                          style={{ backgroundColor: ss.bg, color: ss.color }}>
                          {ss.label}
                        </span>
                      </td>
                      {/* 생성일 */}
                      <td className="px-4 py-3 text-xs" style={{ color: 'var(--dash-text-muted)' }}>
                        {webtoon.created_at}
                      </td>
                      {/* 관리 */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => router.push(`/dashboard/ai_image_generator/edit?id=${webtoon.id}`)}
                            className="text-xs px-2.5 py-1 rounded transition-opacity hover:opacity-70"
                            style={{ color: 'var(--dash-text-sub)', border: '1px solid var(--dash-border)' }}
                          >
                            수정
                          </button>
                          <button
                            onClick={() => handleDelete(webtoon.id, webtoon.title)}
                            className="text-xs px-2.5 py-1 rounded transition-opacity hover:opacity-70"
                            style={{ color: '#EF4444', border: '1px solid rgba(239,68,68,0.3)' }}
                          >
                            삭제
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6}>
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                      <div className="w-14 h-14 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: 'var(--dash-surface)' }}>
                        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                          style={{ color: 'var(--dash-text-muted)' }}>
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                      <p className="text-sm" style={{ color: 'var(--dash-text-sub)' }}>
                        {search ? `"${search}" 검색 결과가 없습니다.` : '아직 등록된 웹툰 작품이 없습니다.'}
                      </p>
                      {!search && (
                        <Link
                          href="/dashboard/ai_image_generator/generator"
                          className="px-5 py-2.5 rounded-lg text-sm font-bold transition-opacity hover:opacity-85"
                          style={{ backgroundColor: '#00C73C', color: '#FFFFFF', textDecoration: 'none' }}
                        >
                          + 새 웹툰 만들기
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* ── 페이지네이션 ── */}
      {!loading && totalPages > 1 && (
        <div
          className="flex items-center justify-center gap-3 px-8 py-4 flex-shrink-0"
          style={{ borderTop: '1px solid var(--dash-border)' }}
        >
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="flex items-center gap-1 px-3 py-1.5 rounded text-xs"
            style={{
              backgroundColor: 'var(--dash-surface)',
              border: '1px solid var(--dash-border)',
              color: page <= 1 ? 'var(--dash-text-muted)' : 'var(--dash-text-sub)',
              cursor: page <= 1 ? 'not-allowed' : 'pointer',
              opacity: page <= 1 ? 0.5 : 1,
            }}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            이전
          </button>

          <div className="flex items-center gap-1">
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter(p => p === 1 || p === totalPages || Math.abs(p - page) <= 2)
              .reduce<(number | '...')[]>((acc, p, idx, arr) => {
                if (idx > 0 && (p as number) - (arr[idx - 1] as number) > 1) acc.push('...');
                acc.push(p);
                return acc;
              }, [])
              .map((p, idx) =>
                p === '...' ? (
                  <span key={`el-${idx}`} style={{ color: 'var(--dash-text-muted)', fontSize: '12px', padding: '0 2px' }}>…</span>
                ) : (
                  <button
                    key={p}
                    onClick={() => setPage(p as number)}
                    style={{
                      width: '28px', height: '28px', borderRadius: '6px', fontSize: '12px',
                      backgroundColor: page === p ? '#00C73C' : 'var(--dash-surface)',
                      color: page === p ? '#FFFFFF' : 'var(--dash-text-sub)',
                      border: `1px solid ${page === p ? '#00C73C' : 'var(--dash-border)'}`,
                      fontWeight: page === p ? 700 : 400,
                      cursor: 'pointer',
                    }}
                  >
                    {p}
                  </button>
                )
              )}
          </div>

          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="flex items-center gap-1 px-3 py-1.5 rounded text-xs"
            style={{
              backgroundColor: 'var(--dash-surface)',
              border: '1px solid var(--dash-border)',
              color: page >= totalPages ? 'var(--dash-text-muted)' : 'var(--dash-text-sub)',
              cursor: page >= totalPages ? 'not-allowed' : 'pointer',
              opacity: page >= totalPages ? 0.5 : 1,
            }}
          >
            다음
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      )}
    </main>
  );
}
