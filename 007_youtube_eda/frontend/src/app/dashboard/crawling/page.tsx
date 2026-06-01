'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import Link from 'next/link';

// ── 타입 정의 ─────────────────────────────────────────────────────────────────
interface ChannelInfo {
  channel_id: string;
  channel_name: string;
  channel_url: string;
  subscriber_count: number;
  video_count: number;
  thumbnail_url: string;
  description: string;
  country: string;
}

interface CollectionStatus {
  status: 'pending' | 'running' | 'done' | 'error';
  total_videos: number;
  collected_videos: number;
  percent: number;
  current: string;
  current_type: string;
  videos_found: number;
  shorts_found: number;
  error_message: string;
  started_at: string | null;
  finished_at: string | null;
}

// ── 유틸 ──────────────────────────────────────────────────────────────────────
const fmtNum = (n: number) =>
  n >= 100000000 ? `${(n / 100000000).toFixed(1)}억`
  : n >= 10000   ? `${(n / 10000).toFixed(1)}만`
  : n.toLocaleString();

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  pending: { label: '대기 중',   cls: 'bg-gray-100 text-gray-600' },
  running: { label: '수집 중',   cls: 'bg-blue-50  text-blue-600' },
  done:    { label: '수집 완료', cls: 'bg-green-50  text-green-700' },
  error:   { label: '오류',      cls: 'bg-red-50    text-red-600' },
};

// ── 스텝 인디케이터 ───────────────────────────────────────────────────────────
function StepBar({ step }: { step: number }) {
  const steps = ['채널 확인', '영상 수집', '완료'];
  return (
    <div className="flex items-center gap-0 mb-6">
      {steps.map((s, i) => {
        const n = i + 1;
        const done    = step > n;
        const active  = step === n;
        return (
          <div key={s} className="flex items-center">
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-extrabold transition-all
                ${done   ? 'bg-emerald-500 text-white'
                : active ? 'bg-[#FF0000] text-white shadow-md'
                :          'bg-gray-100 text-gray-400'}`}>
                {done ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                ) : n}
              </div>
              <span className={`mt-1 text-[10px] font-bold whitespace-nowrap
                ${active ? 'text-[#FF0000]' : done ? 'text-emerald-600' : 'text-gray-400'}`}>
                {s}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`h-0.5 w-20 mx-1 mb-4 rounded transition-all
                ${step > n + 1 ? 'bg-emerald-400' : step > n ? 'bg-emerald-300' : 'bg-gray-200'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
export default function CrawlingPage() {
  const [step,       setStep]       = useState<1|2|3>(1);
  const [url,        setUrl]        = useState('');
  const [channel,    setChannel]    = useState<ChannelInfo | null>(null);
  const [loadingCh,  setLoadingCh]  = useState(false);
  const [logId,      setLogId]      = useState<number | null>(null);
  const [colStatus,  setColStatus]  = useState<CollectionStatus | null>(null);
  const [logs,       setLogs]       = useState<string[]>([]);
  const [error,      setError]      = useState('');
  const [maxVideos,  setMaxVideos]  = useState(50);
  const [maxShorts,  setMaxShorts]  = useState(50);
  const logRef  = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 로그 자동 스크롤
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  // 폴링 중단 정리
  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current); }, []);

  // ── 수집 상태 폴링 ─────────────────────────────────────────────────────────
  const startPolling = useCallback((id: number) => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(async () => {
      try {
        const { data } = await axios.get<CollectionStatus & { success: boolean }>(
          `/api/v1/youtube/collection-log/${id}/`
        );
        setColStatus(data);
        if (data.current) {
          setLogs(prev => {
            if (prev.at(-1) === data.current) return prev;
            return [...prev.slice(-99), data.current];
          });
        }
        if (data.status === 'done' || data.status === 'error') {
          clearInterval(timerRef.current!);
          setStep(3);
        }
      } catch { /* 네트워크 오류 무시 */ }
    }, 2000);
  }, []);

  // ── 1단계: 채널 가져오기 ───────────────────────────────────────────────────
  const handleFetchChannel = async () => {
    setError('');
    if (!url.trim()) { setError('YouTube 채널 URL을 입력해주세요.'); return; }
    setLoadingCh(true);
    setChannel(null);
    try {
      const { data } = await axios.post('/api/v1/youtube/fetch-channel/', { url: url.trim() });
      if (data.success) {
        setChannel(data.channel);
        setLogs([`✅ 채널 정보 수집 완료 — ${data.channel.channel_name}`]);
        setStep(2);
      } else {
        setError(data.error || '채널 정보를 가져오지 못했습니다.');
      }
    } catch (e: unknown) {
      const msg = axios.isAxiosError(e) ? e.response?.data?.error : '서버에 연결할 수 없습니다.';
      setError(msg || '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoadingCh(false);
    }
  };

  // ── 2단계: 영상 수집 시작 ─────────────────────────────────────────────────
  const handleFetchVideos = async () => {
    if (!channel) return;
    setError('');
    setLogs(prev => [...prev, `🚀 일반 영상 ${maxVideos}개 + Shorts ${maxShorts}개 수집을 시작합니다...`]);
    try {
      const { data } = await axios.post('/api/v1/youtube/fetch-videos', {
        channel_id: channel.channel_id,
        max_videos: maxVideos,
        max_shorts: maxShorts,
      });
      if (data.success) {
        setLogId(data.log_id);
        startPolling(data.log_id);
        if (data.already_running) {
          setLogs(prev => [...prev, '⚠️ 이미 수집 중인 작업이 있습니다. 진행 상황을 이어서 표시합니다.']);
        }
      } else {
        setError(data.error || '영상 수집을 시작하지 못했습니다.');
      }
    } catch (e: unknown) {
      const msg = axios.isAxiosError(e) ? e.response?.data?.error : '서버에 연결할 수 없습니다.';
      setError(msg || '알 수 없는 오류가 발생했습니다.');
    }
  };

  const pct = colStatus?.percent ?? 0;
  const st  = colStatus?.status;

  return (
    <div className="max-w-3xl mx-auto space-y-5">

      {/* 페이지 헤더 */}
      <div>
        <h1 className="text-[18px] font-extrabold text-gray-800">데이터 수집</h1>
        <p className="text-[12px] text-gray-400 mt-0.5">
          YouTube 채널 URL을 입력하면 채널 정보와 영상 데이터를 자동으로 수집합니다.
        </p>
      </div>

      {/* 스텝 바 */}
      <StepBar step={step} />

      {/* ── STEP 1: 채널 URL 입력 ── */}
      <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm p-6">
        <div className="flex items-center gap-2.5 mb-4">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-extrabold
            ${step >= 1 ? 'bg-[#FF0000] text-white' : 'bg-gray-100 text-gray-400'}`}>1</div>
          <h2 className="text-[14px] font-extrabold text-gray-800">채널 URL 입력</h2>
          {channel && (
            <span className="ml-auto text-[10px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-200 px-2 py-0.5 rounded-full">
              ✓ 수집 완료
            </span>
          )}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loadingCh && handleFetchChannel()}
            placeholder="https://www.youtube.com/@channelname"
            className="flex-1 px-4 py-2.5 text-[13px] border border-gray-200 rounded-xl
              focus:outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100
              placeholder:text-gray-300 transition-all"
            disabled={loadingCh}
          />
          <button
            onClick={handleFetchChannel}
            disabled={loadingCh}
            className="flex items-center gap-2 px-5 py-2.5 text-[13px] font-bold text-white
              bg-[#FF0000] hover:bg-red-600 disabled:bg-red-300 rounded-xl transition-colors shadow-sm shrink-0"
          >
            {loadingCh ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                조회 중...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                가져오기
              </>
            )}
          </button>
        </div>

        <p className="mt-2 text-[11px] text-gray-400">
          예) https://www.youtube.com/@MrBeast &nbsp;|&nbsp; https://www.youtube.com/channel/UCxxxx
        </p>

        {error && (
          <div className="mt-3 flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl">
            <svg className="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-[12px] text-red-600 font-bold">{error}</span>
          </div>
        )}
      </div>

      {/* ── STEP 2: 채널 정보 + 영상 수집 ── */}
      {channel && (
        <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm p-6 space-y-5">
          <div className="flex items-center gap-2.5 mb-1">
            <div className="w-7 h-7 rounded-lg bg-[#FF0000] flex items-center justify-center text-[11px] font-extrabold text-white">2</div>
            <h2 className="text-[14px] font-extrabold text-gray-800">채널 정보 확인</h2>
          </div>

          {/* 채널 카드 */}
          <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl border border-gray-100">
            {channel.thumbnail_url ? (
              <img
                src={channel.thumbnail_url}
                alt={channel.channel_name}
                className="w-16 h-16 rounded-full object-cover border-2 border-white shadow-sm shrink-0"
                onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
            ) : (
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-red-400 to-rose-500 flex items-center justify-center text-white text-xl font-extrabold shrink-0 shadow-sm">
                {channel.channel_name.slice(0, 1)}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-[15px] font-extrabold text-gray-800 truncate">{channel.channel_name}</h3>
                {channel.country && (
                  <span className="text-[10px] font-bold bg-blue-50 text-blue-500 px-2 py-0.5 rounded-full border border-blue-100">
                    {channel.country}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-gray-400 mt-0.5 truncate">{channel.channel_url}</p>
              <div className="flex items-center gap-4 mt-2 flex-wrap">
                <div className="text-center">
                  <p className="text-[16px] font-extrabold text-gray-800">{fmtNum(channel.subscriber_count)}</p>
                  <p className="text-[10px] text-gray-400 font-bold">구독자</p>
                </div>
                <div className="w-px h-6 bg-gray-200" />
                <div className="text-center">
                  <p className="text-[16px] font-extrabold text-gray-800">
                    {channel.video_count > 0 ? channel.video_count.toLocaleString() : '—'}
                  </p>
                  <p className="text-[10px] text-gray-400 font-bold">기존 수집 영상</p>
                </div>
              </div>
              {channel.description && (
                <p className="text-[11px] text-gray-500 mt-2 line-clamp-2 leading-relaxed">
                  {channel.description}
                </p>
              )}
            </div>
          </div>

          {/* 수집 개수 설정 + 영상 수집 시작 */}
          {!logId && (
            <>
              {/* 수집 설정 */}
              <div className="p-4 bg-gray-50 border border-gray-100 rounded-xl space-y-5">
                <p className="text-[12px] font-extrabold text-gray-700">수집 설정</p>

                {/* 일반 영상 슬라이더 */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-red-400 shrink-0" />
                      <span className="text-[12px] font-bold text-gray-700">일반 영상</span>
                    </div>
                    <span className="text-[13px] font-extrabold text-[#FF0000]">
                      {maxVideos === 0 ? '수집 안 함' : `최대 ${maxVideos}개`}
                    </span>
                  </div>
                  <input
                    type="range" min={0} max={50} value={maxVideos}
                    onChange={e => setMaxVideos(Number(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-red-500"
                  />
                  <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                    <span>0</span><span>10</span><span>25</span><span>50개</span>
                  </div>
                </div>

                {/* Shorts 슬라이더 */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-blue-400 shrink-0" />
                      <span className="text-[12px] font-bold text-gray-700">YouTube Shorts</span>
                    </div>
                    <span className="text-[13px] font-extrabold text-blue-500">
                      {maxShorts === 0 ? '수집 안 함' : `최대 ${maxShorts}개`}
                    </span>
                  </div>
                  <input
                    type="range" min={0} max={50} value={maxShorts}
                    onChange={e => setMaxShorts(Number(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-blue-500"
                  />
                  <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                    <span>0</span><span>10</span><span>25</span><span>50개</span>
                  </div>
                </div>

                {/* 요약 */}
                <div className="flex items-center gap-3 pt-1 border-t border-gray-200 text-[11px] text-gray-500">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    일반 영상 <strong className="text-gray-700">{maxVideos}개</strong>
                  </span>
                  <span className="text-gray-300">+</span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-blue-400" />
                    Shorts <strong className="text-gray-700">{maxShorts}개</strong>
                  </span>
                  <span className="text-gray-300">=</span>
                  <span>최대 <strong className="text-gray-700">{maxVideos + maxShorts}개</strong> 수집</span>
                </div>
              </div>

              <button
                onClick={handleFetchVideos}
                disabled={maxVideos === 0 && maxShorts === 0}
                className="w-full flex items-center justify-center gap-2 py-3 text-[13px] font-bold
                  text-white bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-600 hover:to-rose-600
                  disabled:from-gray-300 disabled:to-gray-300 rounded-xl transition-all shadow-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                일반 영상 {maxVideos}개 + Shorts {maxShorts}개 수집 시작
              </button>
            </>
          )}
        </div>
      )}

      {/* ── STEP 2→3: 수집 진행 상태 ── */}
      {logId && colStatus && (
        <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#FF0000] flex items-center justify-center text-[11px] font-extrabold text-white">2</div>
              <h2 className="text-[14px] font-extrabold text-gray-800">영상 수집 진행 상황</h2>
            </div>
            {st && (
              <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${STATUS_MAP[st]?.cls ?? ''}`}>
                {st === 'running' && <span className="inline-block w-1.5 h-1.5 bg-blue-500 rounded-full mr-1 animate-pulse" />}
                {STATUS_MAP[st]?.label}
              </span>
            )}
          </div>

          {/* 일반 영상 / Shorts 발견 수 요약 */}
          {(colStatus.videos_found > 0 || colStatus.shorts_found > 0) && (
            <div className="flex items-center gap-4 p-3 bg-gray-50 border border-gray-100 rounded-xl text-[11px] font-bold">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-400" />
                <span className="text-gray-600">일반 영상</span>
                <span className="text-gray-900">{colStatus.videos_found}개</span>
              </span>
              <span className="text-gray-300">+</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                <span className="text-gray-600">Shorts</span>
                <span className="text-gray-900">{colStatus.shorts_found}개</span>
              </span>
              <span className="text-gray-300">=</span>
              <span className="text-gray-900">총 {colStatus.total_videos}개</span>
            </div>
          )}

          {/* 진행률 바 */}
          <div>
            <div className="flex justify-between text-[11px] font-bold text-gray-500 mb-1.5">
              <span>
                수집 진행률
                {colStatus.current_type && st === 'running' && (
                  <span className={`ml-2 px-1.5 py-0.5 rounded text-[9px] font-bold
                    ${colStatus.current_type.includes('Shorts') ? 'bg-blue-100 text-blue-600' : 'bg-red-100 text-red-600'}`}>
                    {colStatus.current_type}
                  </span>
                )}
              </span>
              <span className="text-gray-800">
                {colStatus.collected_videos.toLocaleString()} / {colStatus.total_videos.toLocaleString()}개
                &nbsp;({pct}%)
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-500
                  ${st === 'error' ? 'bg-red-400'
                  : st === 'done'  ? 'bg-emerald-500'
                  : colStatus.current_type?.includes('Shorts') ? 'bg-gradient-to-r from-blue-400 to-blue-500'
                  :                  'bg-gradient-to-r from-red-400 to-rose-500'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>

          {/* 현재 수집 중인 영상 */}
          {colStatus.current && (
            <div className={`flex items-start gap-2.5 p-3 border rounded-xl
              ${colStatus.current_type?.includes('Shorts')
                ? 'bg-blue-50 border-blue-100'
                : 'bg-red-50 border-red-100'}`}>
              {st === 'running' && (
                <span className={`w-3.5 h-3.5 mt-0.5 border-2 rounded-full animate-spin shrink-0
                  ${colStatus.current_type?.includes('Shorts')
                    ? 'border-blue-300 border-t-blue-600'
                    : 'border-red-300 border-t-red-600'}`} />
              )}
              <p className={`text-[12px] font-bold leading-snug break-all
                ${colStatus.current_type?.includes('Shorts') ? 'text-blue-700' : 'text-red-700'}`}>
                {colStatus.current}
              </p>
            </div>
          )}

          {/* 수집 로그 */}
          <div>
            <p className="text-[11px] font-bold text-gray-400 mb-1.5">수집 로그</p>
            <div
              ref={logRef}
              className="h-44 overflow-y-auto bg-gray-900 rounded-xl p-3 space-y-0.5 font-mono"
            >
              {logs.length === 0 ? (
                <p className="text-[11px] text-gray-500">수집 로그가 여기에 표시됩니다...</p>
              ) : (
                logs.map((l, i) => (
                  <p key={i} className="text-[11px] text-gray-300 leading-relaxed break-all">
                    <span className="text-gray-600 mr-1 select-none">›</span>
                    {l}
                  </p>
                ))
              )}
            </div>
          </div>

          {/* 오류 표시 */}
          {st === 'error' && colStatus.error_message && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
              <p className="text-[11px] font-bold text-red-600">오류: {colStatus.error_message}</p>
            </div>
          )}
        </div>
      )}

      {/* ── STEP 3: 완료 ── */}
      {step === 3 && st === 'done' && (
        <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm p-8 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-[16px] font-extrabold text-gray-800">수집이 완료되었습니다!</h3>
            <p className="text-[12px] text-gray-400 mt-1">
              <strong className="text-gray-700">{channel?.channel_name}</strong> 채널의&nbsp;
              <strong className="text-gray-700">{colStatus?.collected_videos.toLocaleString()}개</strong> 영상 데이터가 저장되었습니다.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3">
            <Link href="/dashboard/main"
              className="flex items-center gap-1.5 px-5 py-2.5 text-[13px] font-bold text-white
                bg-[#FF0000] hover:bg-red-600 rounded-xl transition-colors shadow-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              채널 분석 보기
            </Link>
            <button
              onClick={() => { setStep(1); setChannel(null); setLogId(null); setColStatus(null); setLogs([]); setUrl(''); setError(''); }}
              className="px-5 py-2.5 text-[13px] font-bold text-gray-600 bg-white border border-gray-200
                hover:bg-gray-50 rounded-xl transition-colors">
              다른 채널 수집
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
