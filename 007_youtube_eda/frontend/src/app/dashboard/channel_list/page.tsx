'use client';

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

// ── 타입 ──────────────────────────────────────────────────────────────────────
interface Log {
  id: number;
  status: string;
  total_videos: number;
  collected_videos: number;
  started_at: string;
  finished_at: string;
}

interface Channel {
  channel_id: string;
  channel_name: string;
  channel_url: string;
  subscriber_count: number;
  video_count: number;
  total_view_count: number;
  thumbnail_url: string;
  banner_url: string;
  country: string;
  description: string;
  fetched_at: string;
  log: Log | null;
}

interface ListResponse {
  success: boolean;
  total: number;
  total_videos: number;
  total_views: number;
  channels: Channel[];
}

// ── 유틸 ──────────────────────────────────────────────────────────────────────
const fmtNum = (n: number) =>
  n >= 100_000_000 ? `${(n / 100_000_000).toFixed(1)}억`
  : n >= 10_000    ? `${(n / 10_000).toFixed(1)}만`
  : n.toLocaleString();

const STATUS = {
  done:    { label: '수집 완료', cls: 'bg-emerald-400/20 text-emerald-300 border-emerald-400/30' },
  running: { label: '수집 중',   cls: 'bg-blue-400/20   text-blue-300   border-blue-400/30' },
  pending: { label: '대기 중',   cls: 'bg-white/10      text-white/60   border-white/20' },
  error:   { label: '오류',      cls: 'bg-red-400/20    text-red-300    border-red-400/30' },
} as const;

// ── 요약 카드 ─────────────────────────────────────────────────────────────────
function SummaryCard({ label, value, sub, icon, gradient }: {
  label: string; value: string; sub: string; gradient: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm p-4 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-sm shrink-0 text-white`}>
        {icon}
      </div>
      <div>
        <p className="text-[11px] font-bold text-gray-400">{label}</p>
        <p className="text-[18px] font-extrabold text-gray-800 leading-tight">{value}</p>
        <p className="text-[10px] text-gray-400">{sub}</p>
      </div>
    </div>
  );
}

// ── 채널 카드 (썸네일 블러 배경) ──────────────────────────────────────────────
function ChannelCard({ ch, onDelete }: { ch: Channel; onDelete: (id: string, name: string) => void }) {
  const router = useRouter();
  const st     = ch.log?.status ?? '';
  const badge  = STATUS[st as keyof typeof STATUS];
  const pct    = ch.log && ch.log.total_videos > 0
    ? Math.round((ch.log.collected_videos / ch.log.total_videos) * 100)
    : ch.video_count > 0 ? 100 : 0;

  // 배경 우선순위: 채널 배너 > 썸네일 블러 > 그라디언트
  const bgUrl = ch.banner_url || ch.thumbnail_url || '';

  return (
    <div className="relative rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 group">

      {/* ── 배경 이미지 ── */}
      {bgUrl ? (
        ch.banner_url ? (
          /* 배너: 실제 채널 배경이미지 — 그대로 cover */
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `url(${ch.banner_url})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center top',
            }}
          />
        ) : (
          /* 썸네일: 블러 처리해 배경으로 활용 */
          <div
            className="absolute inset-0 scale-125 transition-transform duration-700 group-hover:scale-110"
            style={{
              backgroundImage: `url(${ch.thumbnail_url})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              filter: 'blur(20px)',
            }}
          />
        )
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-rose-600 via-red-700 to-rose-900" />
      )}

      {/* ── 오버레이: 배너는 더 진하게, 썸네일 블러는 약하게 ── */}
      <div className={`absolute inset-0 bg-gradient-to-b
        ${ch.banner_url
          ? 'from-black/60 via-black/65 to-black/85'
          : 'from-black/50 via-black/60 to-black/80'
        }`}
      />

      {/* ── 콘텐츠 (relative z-10) ── */}
      <div className="relative z-10 p-5 flex flex-col gap-4">

        {/* 헤더: 아바타 + 채널명 + 뱃지 */}
        <div className="flex items-start gap-3">
          {ch.thumbnail_url ? (
            <img
              src={ch.thumbnail_url}
              alt={ch.channel_name}
              className="w-13 h-13 w-[52px] h-[52px] rounded-full object-cover border-2 border-white/40 shadow-lg shrink-0"
              onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
            />
          ) : (
            <div className="w-[52px] h-[52px] rounded-full bg-white/20 border-2 border-white/30 flex items-center justify-center text-white text-xl font-extrabold shadow-lg shrink-0">
              {ch.channel_name.slice(0, 1)}
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-[15px] font-extrabold text-white truncate leading-tight drop-shadow">
                {ch.channel_name}
              </h3>
              {ch.country && (
                <span className="text-[9px] font-bold bg-white/15 text-white/80 border border-white/20 px-1.5 py-0.5 rounded-full">
                  {ch.country}
                </span>
              )}
            </div>
            <a
              href={ch.channel_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] text-white/50 hover:text-white/90 transition-colors truncate block mt-0.5"
            >
              {ch.channel_url}
            </a>
            {badge && (
              <span className={`inline-flex items-center gap-1 mt-1.5 text-[9px] font-bold border px-2 py-0.5 rounded-full ${badge.cls}`}>
                {st === 'running' && <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />}
                {badge.label}
              </span>
            )}
          </div>
        </div>

        {/* 채널 설명 */}
        {ch.description && (
          <p className="text-[11px] text-white/60 line-clamp-2 leading-relaxed -mt-1">
            {ch.description}
          </p>
        )}

        {/* 구분선 */}
        <div className="w-full h-px bg-white/10" />

        {/* 통계 3개 */}
        <div className="grid grid-cols-3 gap-2 text-center">
          {[
            { label: '구독자',    value: fmtNum(ch.subscriber_count) },
            { label: '수집 영상', value: `${ch.video_count.toLocaleString()}개` },
            { label: '총 조회수', value: fmtNum(ch.total_view_count) },
          ].map(s => (
            <div key={s.label} className="bg-white/10 rounded-xl py-2 px-1 backdrop-blur-sm">
              <p className="text-[14px] font-extrabold text-white leading-tight">{s.value}</p>
              <p className="text-[9px] font-bold text-white/60 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* 수집 진행률 */}
        {ch.log && (
          <div>
            <div className="flex justify-between text-[10px] font-bold mb-1">
              <span className="text-white/60">수집 진행률</span>
              <span className="text-white/80">
                {ch.log.collected_videos.toLocaleString()} / {ch.log.total_videos.toLocaleString()}개 ({pct}%)
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-1.5 rounded-full transition-all duration-500
                  ${st === 'error'   ? 'bg-red-400'
                  : st === 'done'    ? 'bg-emerald-400'
                  :                    'bg-blue-400'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )}

        {/* 최근 수집일 */}
        {ch.fetched_at && (
          <p className="text-[10px] text-white/40 -mt-1">
            마지막 수집: {ch.fetched_at}
          </p>
        )}

        {/* 구분선 */}
        <div className="w-full h-px bg-white/10 -mt-1" />

        {/* 액션 버튼 */}
        <div className="flex items-center gap-2 -mt-1">
          <Link
            href="/dashboard/main"
            className="flex-1 flex items-center justify-center gap-1.5 py-2 text-[12px] font-bold
              text-white bg-[#FF0000]/80 hover:bg-[#FF0000] rounded-xl transition-colors backdrop-blur-sm"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            채널 분석
          </Link>

          <button
            onClick={() => router.push(`/dashboard/crawling?url=${encodeURIComponent(ch.channel_url)}`)}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 text-[12px] font-bold
              text-white/90 bg-white/10 hover:bg-white/20 border border-white/20
              rounded-xl transition-colors backdrop-blur-sm"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            재수집
          </button>

          <button
            onClick={() => onDelete(ch.channel_id, ch.channel_name)}
            title="채널 삭제"
            className="flex items-center justify-center w-9 h-9 text-white/40
              hover:text-red-400 hover:bg-red-400/10 border border-white/10
              hover:border-red-400/30 rounded-xl transition-all backdrop-blur-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>

      </div>
    </div>
  );
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────
export default function ChannelListPage() {
  const [data,    setData]    = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [keyword, setKeyword] = useState('');
  const [sort,    setSort]    = useState('fetched_at');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data: res } = await axios.get<ListResponse>(
        `/api/v1/channel/list?sort=${sort}&q=${encodeURIComponent(keyword)}`
      );
      setData(res);
    } catch {
      setError('채널 목록을 불러오지 못했습니다. 백엔드 서버를 확인해주세요.');
    } finally {
      setLoading(false);
    }
  }, [sort, keyword]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (channel_id: string, name: string) => {
    const Swal = (await import('sweetalert2')).default;
    const result = await Swal.fire({
      title: '채널 삭제',
      html: `<b>${name}</b> 채널과 수집된 모든 영상 데이터를 삭제합니다.<br>이 작업은 되돌릴 수 없습니다.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#9CA3AF',
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
    });
    if (!result.isConfirmed) return;
    try {
      await axios.delete(`/api/v1/channel/${channel_id}/delete`);
      await Swal.fire({ title: '삭제 완료', icon: 'success', timer: 1200, showConfirmButton: false });
      load();
    } catch {
      await Swal.fire({ title: '삭제 실패', text: '오류가 발생했습니다.', icon: 'error', confirmButtonColor: '#ef4444' });
    }
  };

  const channels = data?.channels ?? [];

  return (
    <div className="space-y-5">

      {/* 페이지 헤더 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-[18px] font-extrabold text-gray-800">채널 리스트</h1>
          <p className="text-[12px] text-gray-400 mt-0.5">수집된 YouTube 채널 목록입니다.</p>
        </div>
        <Link
          href="/dashboard/crawling"
          className="flex items-center gap-1.5 px-4 py-2 text-[12px] font-bold text-white
            bg-[#FF0000] hover:bg-red-600 rounded-xl transition-colors shadow-sm w-fit"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
          </svg>
          새 채널 수집
        </Link>
      </div>

      {/* 요약 카드 */}
      {data && (
        <div className="grid grid-cols-3 gap-4">
          <SummaryCard
            label="수집 채널 수" value={`${data.total}개`} sub="전체 채널"
            gradient="from-red-500 to-rose-400"
            icon={<svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z" /></svg>}
          />
          <SummaryCard
            label="총 수집 영상" value={`${data.total_videos.toLocaleString()}개`} sub="DB 저장 영상"
            gradient="from-blue-500 to-sky-400"
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.069A1 1 0 0121 8.914V15.086a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
          />
          <SummaryCard
            label="총 조회수 합계" value={fmtNum(data.total_views)} sub="VideoStats 합산"
            gradient="from-emerald-500 to-green-400"
            icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>}
          />
        </div>
      )}

      {/* 검색 + 정렬 */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300"
            fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="채널명 검색..."
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-[12px] bg-white border border-gray-200 rounded-xl
              focus:outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100 transition-all"
          />
        </div>
        <select
          value={sort}
          onChange={e => setSort(e.target.value)}
          className="text-[12px] font-bold text-gray-700 bg-white border border-gray-200 rounded-xl
            px-3 py-2 focus:outline-none focus:border-red-400 cursor-pointer shadow-sm"
        >
          <option value="fetched_at">최근 수집순</option>
          <option value="subscriber">구독자 많은순</option>
          <option value="video">영상 많은순</option>
        </select>
        <button onClick={load}
          className="flex items-center gap-1.5 px-3 py-2 text-[12px] font-bold text-gray-600
            bg-white border border-gray-200 hover:bg-gray-50 rounded-xl transition-colors">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          새로고침
        </button>
      </div>

      {/* 로딩 */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="relative w-10 h-10">
            <div className="absolute inset-0 rounded-full border-4 border-red-100" />
            <div className="absolute inset-0 rounded-full border-4 border-t-red-500 animate-spin" />
          </div>
          <p className="text-[13px] font-bold text-gray-400">채널 목록을 불러오는 중...</p>
        </div>
      )}

      {/* 에러 */}
      {!loading && error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-2xl">
          <svg className="w-5 h-5 text-red-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-[13px] font-bold text-red-700">{error}</p>
            <button onClick={load} className="mt-1 text-[12px] font-bold text-red-500 hover:underline">다시 시도</button>
          </div>
        </div>
      )}

      {/* 빈 상태 */}
      {!loading && !error && channels.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-300" fill="currentColor" viewBox="0 0 24 24">
              <path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z" />
            </svg>
          </div>
          <div>
            <p className="text-[14px] font-bold text-gray-500">
              {keyword ? `"${keyword}" 검색 결과가 없습니다.` : '아직 수집된 채널이 없습니다.'}
            </p>
            <p className="text-[12px] text-gray-400 mt-1">데이터 수집 페이지에서 YouTube 채널을 추가해보세요.</p>
          </div>
          <Link href="/dashboard/crawling"
            className="flex items-center gap-1.5 px-5 py-2.5 text-[13px] font-bold text-white
              bg-[#FF0000] hover:bg-red-600 rounded-xl transition-colors shadow-sm">
            채널 수집 시작
          </Link>
        </div>
      )}

      {/* 채널 카드 그리드 */}
      {!loading && !error && channels.length > 0 && (
        <>
          <p className="text-[11px] font-bold text-gray-400">
            총 <span className="text-gray-700">{channels.length}</span>개 채널
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-5">
            {channels.map(ch => (
              <ChannelCard key={ch.channel_id} ch={ch} onDelete={handleDelete} />
            ))}
          </div>
        </>
      )}

    </div>
  );
}
