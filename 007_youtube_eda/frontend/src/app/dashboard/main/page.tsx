'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { Line, Bar, Doughnut, Scatter } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler,
);

// ── 공통 폰트 옵션 ────────────────────────────────────────────────────────────
const font = { family: "'Nanum Gothic', sans-serif" };
const tickStyle = { font: { ...font, size: 11 }, color: '#94A3B8' };
const gridColor = 'rgba(148,163,184,0.15)';

// ── 임시 데이터 ───────────────────────────────────────────────────────────────

// 1) 월별 업로드 추이
const uploadTrendData = {
  labels: ['24.06', '24.07', '24.08', '24.09', '24.10', '24.11', '24.12', '25.01', '25.02', '25.03', '25.04', '25.05'],
  datasets: [{
    label: '업로드 수',
    data: [42, 38, 61, 47, 58, 53, 35, 49, 55, 67, 61, 74],
    fill: true,
    borderColor: '#FF4757',
    backgroundColor: 'rgba(255,71,87,0.10)',
    tension: 0.45,
    pointBackgroundColor: '#FF4757',
    pointBorderColor: '#fff',
    pointBorderWidth: 2,
    pointRadius: 5,
    pointHoverRadius: 7,
    borderWidth: 2.5,
  }],
};

// 2) 조회수 분포 히스토그램
const viewsDistData = {
  labels: ['~1만', '1~5만', '5~10만', '10~50만', '50~100만', '100만+'],
  datasets: [{
    label: '영상 수',
    data: [312, 498, 187, 164, 58, 28],
    backgroundColor: [
      'rgba(99,179,237,0.85)',
      'rgba(72,187,120,0.85)',
      'rgba(246,173,85,0.85)',
      'rgba(237,100,166,0.85)',
      'rgba(154,117,234,0.85)',
      'rgba(255,71,87,0.85)',
    ],
    borderColor: ['#63B3ED','#48BB78','#F6AD55','#ED64A6','#9A75EA','#FF4757'],
    borderWidth: 1.5,
    borderRadius: 8,
    borderSkipped: false,
  }],
};

// 3) 영상 길이 vs 조회수 산점도
const scatterData = {
  datasets: [
    {
      label: '일반 영상',
      data: [
        {x:180,y:520000},{x:620,y:340000},{x:900,y:780000},{x:480,y:210000},
        {x:1200,y:950000},{x:750,y:430000},{x:360,y:180000},{x:540,y:620000},
        {x:840,y:280000},{x:1500,y:1200000},{x:660,y:390000},{x:420,y:155000},
        {x:1080,y:840000},{x:300,y:95000},{x:960,y:560000},{x:720,y:320000},
        {x:1320,y:740000},{x:240,y:72000},{x:600,y:450000},{x:780,y:610000},
        {x:1440,y:1050000},{x:390,y:235000},{x:870,y:490000},{x:510,y:175000},
      ],
      backgroundColor: 'rgba(255,71,87,0.65)',
      pointRadius: 5,
      pointHoverRadius: 7,
    },
    {
      label: 'Shorts (60초↓)',
      data: [
        {x:15,y:980000},{x:32,y:1850000},{x:45,y:2400000},{x:28,y:760000},
        {x:55,y:3100000},{x:18,y:540000},{x:42,y:1650000},{x:38,y:2050000},
        {x:22,y:890000},{x:50,y:2750000},{x:12,y:320000},{x:48,y:1980000},
      ],
      backgroundColor: 'rgba(59,130,246,0.65)',
      pointRadius: 5,
      pointHoverRadius: 7,
    },
  ],
};

// 4) Shorts vs 일반 비율
const shortsData = {
  labels: ['일반 영상 (843개)', 'YouTube Shorts (404개)'],
  datasets: [{
    data: [843, 404],
    backgroundColor: ['#FF4757', '#3B82F6'],
    borderColor: ['#fff', '#fff'],
    borderWidth: 3,
    hoverOffset: 10,
  }],
};

// 5) 요일별 업로드
const weekdayData = {
  labels: ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'],
  datasets: [{
    label: '업로드 수',
    data: [142, 168, 195, 173, 221, 187, 161],
    backgroundColor: [
      'rgba(99,179,237,0.75)',
      'rgba(72,187,120,0.75)',
      'rgba(246,173,85,0.75)',
      'rgba(154,117,234,0.75)',
      'rgba(255,71,87,0.90)',
      'rgba(246,173,85,0.75)',
      'rgba(99,179,237,0.75)',
    ],
    borderColor: ['#63B3ED','#48BB78','#F6AD55','#9A75EA','#FF4757','#F6AD55','#63B3ED'],
    borderWidth: 1.5,
    borderRadius: 8,
    borderSkipped: false,
  }],
};

// 6) 좋아요 vs 댓글 (채널별 비교 바)
const engagementData = {
  labels: ['채널A', '채널B', '채널C', '채널D', '채널E', '채널F', '채널G', '채널H'],
  datasets: [
    {
      label: '평균 좋아요 수',
      data: [8420, 6350, 12100, 4870, 9240, 7680, 5430, 11300],
      backgroundColor: 'rgba(255,71,87,0.75)',
      borderColor: '#FF4757',
      borderWidth: 1.5,
      borderRadius: 6,
      borderSkipped: false,
    },
    {
      label: '평균 댓글 수',
      data: [580, 430, 820, 310, 650, 490, 370, 760],
      backgroundColor: 'rgba(59,130,246,0.75)',
      borderColor: '#3B82F6',
      borderWidth: 1.5,
      borderRadius: 6,
      borderSkipped: false,
    },
  ],
};

// ── KPI 카드 데이터 ────────────────────────────────────────────────────────────
const kpiCards = [
  {
    label: '수집 채널 수', value: '8', unit: '개', delta: '+2', up: true,
    gradient: 'from-red-500 to-rose-400',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z" />
      </svg>
    ),
  },
  {
    label: '총 영상 수', value: '1,247', unit: '개', delta: '+83', up: true,
    gradient: 'from-blue-500 to-sky-400',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M15 10l4.553-2.069A1 1 0 0121 8.914V15.086a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    label: '총 조회수', value: '45,230,000', unit: '회', delta: '+1.2M', up: true,
    gradient: 'from-emerald-500 to-green-400',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
  },
  {
    label: '평균 조회수', value: '36,272', unit: '회', delta: '-2,100', up: false,
    gradient: 'from-violet-500 to-purple-400',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
];

// ── TOP 10 영상 ───────────────────────────────────────────────────────────────
const top10 = [
  { rank:1, title:'2024년 최고의 유튜브 성장 전략 총정리', channel:'채널A', views:3850000, likes:142000, comments:8320, duration:'18:32', is_short:false },
  { rank:2, title:'알고리즘이 좋아하는 영상 만드는 법',    channel:'채널B', views:2640000, likes:98500,  comments:5670, duration:'12:47', is_short:false },
  { rank:3, title:'[#] 조회수 폭발하는 썸네일 공식',       channel:'채널A', views:1920000, likes:187000, comments:3210, duration:'0:58',  is_short:true  },
  { rank:4, title:'구독자 10만 달성까지 내가 한 것들',     channel:'채널C', views:1540000, likes:76300,  comments:4890, duration:'22:14', is_short:false },
  { rank:5, title:'ChatGPT로 유튜브 스크립트 쓰는 방법',  channel:'채널D', views:1280000, likes:54200,  comments:6120, duration:'15:33', is_short:false },
  { rank:6, title:'[#] 1분만에 배우는 영상 편집 꿀팁',    channel:'채널B', views: 980000, likes:92100,  comments:1830, duration:'0:55',  is_short:true  },
  { rank:7, title:'유튜브 수익화 조건 & 실제 수익 공개',  channel:'채널E', views: 870000, likes:43700,  comments:9540, duration:'19:08', is_short:false },
  { rank:8, title:'조회수 올리는 제목 짓는 공식 10가지',  channel:'채널A', views: 760000, likes:38900,  comments:3280, duration:'11:22', is_short:false },
  { rank:9, title:'SEO 최적화로 검색 노출 10배 늘리기',   channel:'채널C', views: 650000, likes:29400,  comments:2760, duration:'16:45', is_short:false },
  { rank:10,title:'유튜브 분석으로 채널 성장 방향 찾기',  channel:'채널D', views: 540000, likes:24800,  comments:2140, duration:'13:57', is_short:false },
];

// ── 수집 로그 ─────────────────────────────────────────────────────────────────
const logs = [
  { ch:'채널A', status:'done',    total:248, done:248, start:'2025-05-16 09:32', end:'2025-05-16 09:48' },
  { ch:'채널B', status:'running', total:187, done:124, start:'2025-05-16 10:05', end:null },
  { ch:'채널C', status:'done',    total:312, done:312, start:'2025-05-15 14:20', end:'2025-05-15 14:52' },
  { ch:'채널D', status:'error',   total:95,  done:63,  start:'2025-05-15 11:00', end:'2025-05-15 11:08' },
  { ch:'채널E', status:'pending', total:0,   done:0,   start:'2025-05-16 10:30', end:null },
];
const statusStyle: Record<string,string> = {
  done:'bg-emerald-50 text-emerald-700 border-emerald-200',
  running:'bg-blue-50 text-blue-700 border-blue-200',
  pending:'bg-gray-100 text-gray-500 border-gray-200',
  error:'bg-red-50 text-red-600 border-red-200',
};
const statusLabel: Record<string,string> = { done:'완료', running:'수집중', pending:'대기', error:'오류' };

// ── 카드 래퍼 컴포넌트 ─────────────────────────────────────────────────────────
function Card({ title, subtitle, badge, children }: {
  title: string; subtitle?: string; badge?: string; children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm hover:shadow-md transition-shadow p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-[13px] font-extrabold text-gray-800">{title}</h3>
          {subtitle && <p className="text-[11px] text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
        {badge && (
          <span className="text-[10px] font-bold text-gray-500 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded-lg shrink-0">
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

// ── 타입 ──────────────────────────────────────────────────────────────────────
interface ChOption { channel_id: string; channel_name: string; }
interface CollectionLog {
  id: number;
  channel_id: string;
  channel_name: string;
  status: string;
  total_videos: number;
  collected_videos: number;
  percent: number;
  error_message: string;
  started_at: string;
  finished_at: string;
}
interface EdaData {
  kpi: { channel_count:number; total_videos:number; total_views:number; avg_views:number };
  upload_trend: { labels:string[]; data:number[] };
  views_dist:   { labels:string[]; data:number[] };
  shorts_ratio: { regular:number; shorts:number };
  weekday:      { labels:string[]; data:number[] };
  scatter:      { regular:{x:number;y:number}[]; shorts:{x:number;y:number}[] };
  top10:        { rank:number; title:string; channel:string; views:number; likes:number; comments:number; duration:string; is_short:boolean }[];
  engagement:         { channel:string; avg_likes:number; avg_comments:number }[];
  engagement_summary: { avg_likes:number; avg_comments:number; like_rate:number };
}

interface AiInsight {
  icon: string; label: string; badge: string;
  color: string; badgeColor: string; points: string[];
}

interface AiReport { summary: string; insights: AiInsight[]; created_at?: string; }

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
export default function MainDashboard() {
  const [channelId,      setChannelId]      = useState('all');
  const [chOptions,      setChOptions]      = useState<ChOption[]>([]);
  const [edaData,        setEdaData]        = useState<EdaData | null>(null);
  const [analyzing,      setAnalyzing]      = useState(false);
  const [analyzeErr,     setAnalyzeErr]     = useState('');
  const [renderKey,      setRenderKey]      = useState(0);   // 차트 강제 리마운트용
  const [collectionLogs, setCollectionLogs] = useState<CollectionLog[]>([]);
  const [logsLoading,    setLogsLoading]    = useState(false);
  const [savedAiReport,  setSavedAiReport]  = useState<AiReport | null>(null);

  // 채널 목록 로드
  useEffect(() => {
    axios.get('/api/v1/channel/list').then(({ data }) => {
      if (data.success) setChOptions(data.channels);
    }).catch(() => {});
  }, []);

  // 수집 로그 로드
  const fetchLogs = useCallback(async (cid: string) => {
    setLogsLoading(true);
    try {
      const { data } = await axios.get(
        `/api/v1/channel/logs?channel_id=${cid}&limit=20`
      );
      if (data.success) setCollectionLogs(data.logs);
    } catch { /* 무시 */ } finally {
      setLogsLoading(false);
    }
  }, []);

  // 채널 변경 시 로그 새로고침
  useEffect(() => {
    fetchLogs(channelId);
  }, [channelId, fetchLogs]);

  // 데이터 분석 실행
  const handleAnalyze = async () => {
    setAnalyzing(true);
    setAnalyzeErr('');
    try {
      const { data } = await axios.get<EdaData & { success: boolean }>(
        `/api/v1/eda?channel_id=${channelId}`
      );
      if (data.success) {
        setEdaData(data);
        setRenderKey(k => k + 1);
        fetchLogs(channelId);

        // 저장된 AI 분석 리포트 로드
        try {
          const aiRes = await axios.get<{ success: boolean; report: AiReport | null }>(
            `/api/v1/ai-report/latest?channel_id=${channelId}`
          );
          setSavedAiReport(aiRes.data.success ? (aiRes.data.report ?? null) : null);
        } catch {
          setSavedAiReport(null);
        }
      } else {
        setAnalyzeErr('분석 데이터를 가져오지 못했습니다.');
      }
    } catch {
      setAnalyzeErr('백엔드 서버를 확인해주세요.');
    } finally {
      setAnalyzing(false);
    }
  };

  // ── 실제 데이터 기반 차트 데이터 계산 ────────────────────────────────────
  const liveUploadTrend = useMemo(() => !edaData ? uploadTrendData : {
    labels: edaData.upload_trend.labels,
    datasets: [{ ...uploadTrendData.datasets[0], data: edaData.upload_trend.data }],
  }, [edaData]);

  const liveViewsDist = useMemo(() => !edaData ? viewsDistData : {
    ...viewsDistData,
    labels: edaData.views_dist.labels,
    datasets: [{ ...viewsDistData.datasets[0], data: edaData.views_dist.data }],
  }, [edaData]);

  const liveScatter = useMemo(() => !edaData ? scatterData : {
    datasets: [
      { ...scatterData.datasets[0], data: edaData.scatter.regular },
      { ...scatterData.datasets[1], data: edaData.scatter.shorts  },
    ],
  }, [edaData]);

  const liveShortsRatio = useMemo(() => !edaData ? shortsData : {
    ...shortsData,
    datasets: [{ ...shortsData.datasets[0], data: [edaData.shorts_ratio.regular, edaData.shorts_ratio.shorts] }],
  }, [edaData]);

  const liveWeekday = useMemo(() => !edaData ? weekdayData : {
    ...weekdayData,
    datasets: [{ ...weekdayData.datasets[0], data: edaData.weekday.data }],
  }, [edaData]);

  const liveEngagement = useMemo(() => !edaData ? engagementData : {
    labels: edaData.engagement.map(e => e.channel),
    datasets: [
      { ...engagementData.datasets[0], data: edaData.engagement.map(e => e.avg_likes) },
      { ...engagementData.datasets[1], data: edaData.engagement.map(e => e.avg_comments) },
    ],
  }, [edaData]);

  // ── KPI 동적 값 ───────────────────────────────────────────────────────────
  const fmtNum = (n: number) =>
    n >= 100_000_000 ? `${(n/100_000_000).toFixed(1)}억`
    : n >= 10_000    ? `${(n/10_000).toFixed(1)}만`
    : n.toLocaleString();

  const liveKpi = edaData ? [
    { ...kpiCards[0], value: String(edaData.kpi.channel_count), unit: '개' },
    { ...kpiCards[1], value: edaData.kpi.total_videos.toLocaleString(), unit: '개' },
    { ...kpiCards[2], value: fmtNum(edaData.kpi.total_views), unit: '회' },
    { ...kpiCards[3], value: fmtNum(edaData.kpi.avg_views), unit: '회' },
  ] : kpiCards;

  const liveTop10   = edaData?.top10   ?? top10;
  const liveSummary = edaData?.engagement_summary ?? { avg_likes: 4820, avg_comments: 312, like_rate: 13.3 };

  return (
    <div className="space-y-5 min-h-full">

      {/* ── 페이지 헤더 ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-[18px] font-extrabold text-gray-800">채널 분석 대시보드</h1>
          <p className="text-[12px] text-gray-400 mt-0.5">수집된 YouTube 채널 데이터의 EDA 분석 결과입니다.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* 채널 선택 — 실제 수집 채널 목록 */}
          <select
            value={channelId}
            onChange={e => {
              setChannelId(e.target.value);
              setEdaData(null);
              setAnalyzeErr('');
              setSavedAiReport(null);
            }}
            className="text-[12px] font-bold text-gray-700 bg-white border border-gray-200 rounded-xl px-3 py-2 hover:border-red-300 focus:outline-none focus:border-red-400 cursor-pointer shadow-sm transition-colors"
          >
            <option value="all">전체 채널</option>
            {chOptions.map(c => (
              <option key={c.channel_id} value={c.channel_id}>{c.channel_name}</option>
            ))}
          </select>

          {/* 데이터 분석 버튼 */}
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex items-center gap-1.5 px-4 py-2 text-[12px] font-bold text-white
              bg-[#FF0000] hover:bg-red-600 disabled:bg-red-300 rounded-xl transition-colors shadow-sm"
          >
            {analyzing ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                분석 중...
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                데이터 분석
              </>
            )}
          </button>
        </div>
      </div>

      {/* 분석 오류 */}
      {analyzeErr && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-[12px] font-bold text-red-600">
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {analyzeErr}
        </div>
      )}

      {/* 분석 결과 배지 */}
      {edaData && !analyzing && (
        <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-[12px] font-bold text-emerald-700">
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/>
          </svg>
          실제 데이터 분석 완료 — {edaData.kpi.total_videos.toLocaleString()}개 영상 기준
        </div>
      )}

      {/* ── 분석 콘텐츠 래퍼 ── */}
      {/*
          오버레이 표시 조건:
          ① channelId === 'all'  → 채널을 아직 선택하지 않음
          ② channelId !== 'all' && !edaData  → 채널 선택했지만 "데이터 분석" 미클릭
          ③ analyzing  → 분석 진행 중 (별도 스피너)
          실제 데이터 표시: channelId !== 'all' && edaData !== null && !analyzing
      */}
      <div className="relative">

        {/* ① 채널 미선택 또는 ② 분석 미실행 오버레이 */}
        {(channelId === 'all' || !edaData) && !analyzing && (
          <>
            <div className="absolute inset-0 z-20 bg-white/75 backdrop-blur-sm pointer-events-auto" />
            <div
              className="fixed z-30 flex items-center justify-center pointer-events-none"
              style={{ left: 220, top: 64, right: 0, bottom: 0 }}
            >
              <div className="flex flex-col items-center gap-5 px-8 text-center">

                {channelId === 'all' ? (
                  /* ① 채널 미선택 */
                  <>
                    <div className="w-20 h-20 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center shadow-md">
                      <svg className="w-11 h-11 text-red-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/>
                      </svg>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[22px] font-extrabold text-gray-800">
                        채널을 선택하시면 분석정보가 제공됩니다.
                      </p>
                      <p className="text-[16px] text-gray-500 leading-relaxed">
                        위의 드롭다운에서 분석할 채널을 선택한 후&nbsp;
                        <strong className="text-[#FF0000]">데이터 분석</strong> 버튼을 클릭하세요.
                      </p>
                    </div>
                  </>
                ) : (
                  /* ② 채널 선택했지만 분석 미실행 */
                  <>
                    <div className="w-20 h-20 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center shadow-md">
                      <svg className="w-11 h-11 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                      </svg>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[22px] font-extrabold text-gray-800">
                        채널이 선택되었습니다.
                      </p>
                      <p className="text-[16px] text-gray-500 leading-relaxed">
                        <strong className="text-[#FF0000]">데이터 분석</strong> 버튼을 클릭하면&nbsp;
                        실제 분석 결과가 표시됩니다.
                      </p>
                    </div>
                  </>
                )}

              </div>
            </div>
          </>
        )}

        {/* ③ 분석 중 로딩 오버레이 */}
        {analyzing && (
          <div className="absolute inset-0 z-20 bg-white/60 backdrop-blur-[2px] flex items-center justify-center rounded-2xl pointer-events-auto">
            <div className="flex flex-col items-center gap-3">
              <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-4 border-red-100" />
                <div className="absolute inset-0 rounded-full border-4 border-t-[#FF0000] animate-spin" />
              </div>
              <p className="text-[13px] font-bold text-gray-700">데이터를 분석하고 있습니다...</p>
            </div>
          </div>
        )}

        {/* 콘텐츠 — 분석 완료 전까지 희미하게 */}
        <div className={`space-y-5 transition-all duration-300
          ${(channelId === 'all' || !edaData) && !analyzing
            ? 'opacity-20 pointer-events-none select-none'
            : analyzing
            ? 'opacity-40 pointer-events-none'
            : 'opacity-100'}`}>

      {/* ── KPI 카드 4개 ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {liveKpi.map(k => (
          <div key={k.label} className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm hover:shadow-md transition-shadow overflow-hidden">
            <div className={`h-1.5 w-full bg-gradient-to-r ${k.gradient}`} />
            <div className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[11px] font-bold text-gray-400">{k.label}</p>
                  <p className="text-[20px] font-extrabold text-gray-800 mt-1 leading-none">
                    {k.value}
                    <span className="text-[12px] font-bold text-gray-400 ml-1">{k.unit}</span>
                  </p>
                  <p className={`text-[11px] font-bold mt-2 ${k.up ? 'text-emerald-500' : 'text-red-400'}`}>
                    {k.up ? '▲' : '▼'} {k.delta} 이번 달
                  </p>
                </div>
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${k.gradient} flex items-center justify-center text-white shadow-sm shrink-0`}>
                  {k.icon}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── 차트 행 1: 업로드 추이 + 조회수 분포 ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="월별 업로드 추이" subtitle="게시일 기준 월별 영상 업로드 수" badge="최근 12개월">
          <div className="h-[200px]">
            <Line key={`upload-${renderKey}`} data={liveUploadTrend} options={{
              responsive: true, maintainAspectRatio: false,
              plugins: { legend: { display: false },
                tooltip: { titleFont: font, bodyFont: font, padding: 10, cornerRadius: 8 } },
              scales: {
                x: { grid: { display: false }, ticks: tickStyle, border: { display: false } },
                y: { grid: { color: gridColor }, ticks: tickStyle, border: { display: false } },
              },
            }} />
          </div>
        </Card>

        <Card title="조회수 구간별 분포" subtitle="조회수 구간별 영상 수 히스토그램" badge="1,247개 영상">
          <div className="h-[200px]">
            <Bar key={`viewsdist-${renderKey}`} data={liveViewsDist} options={{
              responsive: true, maintainAspectRatio: false,
              plugins: { legend: { display: false },
                tooltip: { titleFont: font, bodyFont: font, padding: 10, cornerRadius: 8 } },
              scales: {
                x: { grid: { display: false }, ticks: tickStyle, border: { display: false } },
                y: { grid: { color: gridColor }, ticks: tickStyle, border: { display: false } },
              },
            }} />
          </div>
        </Card>
      </div>

      {/* ── 차트 행 2: 산점도 + Doughnut ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="영상 길이 vs 조회수" subtitle="영상 길이(초)와 조회수 상관관계 산점도">
          <div className="flex items-center gap-4 mb-3">
            <span className="flex items-center gap-1.5 text-[11px] font-bold text-gray-500">
              <span className="w-2.5 h-2.5 rounded-full bg-red-400 inline-block" />일반 영상
            </span>
            <span className="flex items-center gap-1.5 text-[11px] font-bold text-gray-500">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-400 inline-block" />Shorts
            </span>
          </div>
          <div className="h-[210px]">
            <Scatter key={`scatter-${renderKey}`} data={liveScatter} options={{
              responsive: true, maintainAspectRatio: false,
              plugins: { legend: { display: false },
                tooltip: {
                  titleFont: font, bodyFont: font, padding: 10, cornerRadius: 8,
                  callbacks: {
                    label: (ctx) => {
                      const p = ctx.parsed;
                      return ` 길이: ${p.x}초  조회수: ${((p.y ?? 0)/10000).toFixed(0)}만`;
                    },
                  },
                },
              },
              scales: {
                x: { title: { display: true, text: '영상 길이 (초)', font, color: '#9CA3AF' },
                  grid: { color: gridColor }, ticks: tickStyle, border: { display: false } },
                y: { title: { display: true, text: '조회수', font, color: '#9CA3AF' },
                  grid: { color: gridColor }, ticks: { ...tickStyle,
                    callback: (v) => `${(Number(v)/10000).toFixed(0)}만` },
                  border: { display: false } },
              },
            }} />
          </div>
        </Card>

        <Card title="Shorts vs 일반 영상 비율" subtitle="전체 영상 중 Shorts(60초 이하) 비율">
          <div className="flex items-center gap-6">
            <div className="w-[170px] h-[170px] shrink-0">
              <Doughnut key={`shorts-${renderKey}`} data={liveShortsRatio} options={{
                responsive: true, maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                  legend: { display: false },
                  tooltip: { titleFont: font, bodyFont: font, padding: 10, cornerRadius: 8 },
                },
              }} />
            </div>
            <div className="flex-1 space-y-4">
              {[
                {
                  label: '일반 영상',
                  count: edaData?.shorts_ratio.regular ?? 843,
                  pct: edaData ? Math.round(edaData.shorts_ratio.regular / (edaData.kpi.total_videos || 1) * 1000) / 10 : 67.6,
                  avg: '일반 영상',
                  color: 'bg-red-400',
                },
                {
                  label: 'YouTube Shorts',
                  count: edaData?.shorts_ratio.shorts ?? 404,
                  pct: edaData ? Math.round(edaData.shorts_ratio.shorts / (edaData.kpi.total_videos || 1) * 1000) / 10 : 32.4,
                  avg: '60초 이하 영상',
                  color: 'bg-blue-400',
                },
              ].map(item => (
                <div key={item.label}>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className={`w-3 h-3 rounded-sm ${item.color} shrink-0`} />
                    <span className="text-[12px] font-bold text-gray-700">{item.label}</span>
                  </div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-[20px] font-extrabold text-gray-800">{count(item.count)}</span>
                    <span className="text-[11px] font-bold text-gray-400">개</span>
                    <span className="text-[11px] font-bold text-gray-400 ml-1">{item.pct}%</span>
                  </div>
                  <p className="text-[10px] text-gray-400 mt-0.5">{item.avg}</p>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* ── 차트 행 3: 요일별 + 참여도 비교 ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="요일별 업로드 패턴" subtitle="게시 요일 분포 분석" badge="금요일 최다">
          <div className="h-[185px]">
            <Bar key={`weekday-${renderKey}`} data={liveWeekday} options={{
              responsive: true, maintainAspectRatio: false,
              plugins: { legend: { display: false },
                tooltip: { titleFont: font, bodyFont: font, padding: 10, cornerRadius: 8 } },
              scales: {
                x: { grid: { display: false }, ticks: tickStyle, border: { display: false } },
                y: { grid: { color: gridColor }, ticks: tickStyle, border: { display: false } },
              },
            }} />
          </div>
        </Card>

        <Card title="참여도 지표" subtitle="좋아요율 · 댓글률 분석">
          <div className="space-y-5 mt-1">
            {[
              { label: '평균 좋아요 수', value: liveSummary.avg_likes.toLocaleString(), sub: `좋아요율 ${liveSummary.like_rate}%`, pct: Math.min(liveSummary.like_rate * 5, 100), color: 'bg-red-400' },
              { label: '평균 댓글 수', value: liveSummary.avg_comments.toLocaleString(), sub: `댓글/조회 비율`, pct: 18, color: 'bg-blue-400' },
              { label: '좋아요/조회수 비율', value: `${liveSummary.like_rate}%`, sub: '수집 영상 평균', pct: Math.min(liveSummary.like_rate * 5, 100), color: 'bg-emerald-400' },
            ].map(s => (
              <div key={s.label}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[11px] font-bold text-gray-500">{s.label}</span>
                  <span className="text-[12px] font-extrabold text-gray-800">{s.value}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className={`h-2 rounded-full ${s.color} transition-all duration-700`} style={{ width: `${s.pct}%` }} />
                </div>
                <p className="text-[10px] text-gray-400 mt-0.5">{s.sub}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ── AI 분석 ── */}
      <AiAnalysisCard key={channelId} edaData={edaData} channelId={channelId} savedReport={savedAiReport} />

      {/* ── 차트 행 4: 채널별 참여도 비교 (풀 width) ── */}
      <Card title="채널별 평균 좋아요 · 댓글 비교" subtitle="수집된 8개 채널의 영상 참여도 비교" badge="채널별 평균값">
        <div className="h-[200px]">
          <Bar key={`engagement-${renderKey}`} data={liveEngagement} options={{
            responsive: true, maintainAspectRatio: false,
            plugins: {
              legend: {
                display: true,
                position: 'top',
                labels: { font, boxWidth: 12, padding: 16, color: '#6B7280' },
              },
              tooltip: { titleFont: font, bodyFont: font, padding: 10, cornerRadius: 8 },
            },
            scales: {
              x: { grid: { display: false }, ticks: tickStyle, border: { display: false } },
              y: { grid: { color: gridColor }, ticks: { ...tickStyle,
                callback: v => Number(v) >= 1000 ? `${(Number(v)/1000).toFixed(0)}K` : v },
                border: { display: false } },
            },
          }} />
        </div>
      </Card>

      {/* ── TOP 10 영상 테이블 ── */}
      <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm hover:shadow-md transition-shadow overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#EEF2F7]">
          <div>
            <h3 className="text-[13px] font-extrabold text-gray-800">TOP 10 영상</h3>
            <p className="text-[11px] text-gray-400 mt-0.5">조회수 기준 상위 10개 영상</p>
          </div>
          <button className="text-[12px] font-bold text-red-500 hover:text-red-600 hover:underline transition-colors">전체 보기 →</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 text-[11px] font-bold text-gray-400 border-b border-[#EEF2F7]">
                <th className="px-4 py-3 text-center w-12">순위</th>
                <th className="px-4 py-3 text-left">영상 제목</th>
                <th className="px-4 py-3 text-center">채널</th>
                <th className="px-4 py-3 text-right">조회수</th>
                <th className="px-4 py-3 text-right">좋아요</th>
                <th className="px-4 py-3 text-right">댓글</th>
                <th className="px-4 py-3 text-center">길이</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {liveTop10.map(v => (
                <tr key={v.rank} className="hover:bg-red-50/30 transition-colors">
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-[11px] font-extrabold
                      ${v.rank <= 3 ? 'bg-gradient-to-br from-red-500 to-rose-400 text-white shadow-sm' : 'bg-gray-100 text-gray-500'}`}>
                      {v.rank}
                    </span>
                  </td>
                  <td className="px-4 py-3 max-w-[260px]">
                    <div className="flex items-center gap-2">
                      {v.is_short && (
                        <span className="shrink-0 text-[9px] font-extrabold bg-blue-50 text-blue-500 border border-blue-100 px-1.5 py-0.5 rounded-md">Shorts</span>
                      )}
                      <p className="text-[12px] font-bold text-gray-700 truncate">{v.title}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-[11px] font-bold text-gray-400 bg-gray-50 px-2 py-0.5 rounded-lg">{v.channel}</span>
                  </td>
                  <td className="px-4 py-3 text-right text-[12px] font-extrabold text-gray-800">
                    {v.views >= 1000000 ? `${(v.views/1000000).toFixed(1)}M` : `${(v.views/1000).toFixed(0)}K`}
                  </td>
                  <td className="px-4 py-3 text-right text-[11px] font-bold text-gray-400">
                    {v.likes >= 1000 ? `${(v.likes/1000).toFixed(0)}K` : v.likes}
                  </td>
                  <td className="px-4 py-3 text-right text-[11px] font-bold text-gray-400">{v.comments.toLocaleString()}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-[11px] font-bold text-gray-400">{v.duration}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── 최근 수집 로그 ── */}
      <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm hover:shadow-md transition-shadow overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#EEF2F7]">
          <div>
            <h3 className="text-[13px] font-extrabold text-gray-800">최근 수집 로그</h3>
            <p className="text-[11px] text-gray-400 mt-0.5">채널 데이터 수집 작업 현황</p>
          </div>
          <button
            onClick={() => fetchLogs(channelId)}
            className="flex items-center gap-1 text-[12px] font-bold text-red-500 hover:text-red-600 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            새로고침
          </button>
        </div>

        {/* 로딩 */}
        {logsLoading && (
          <div className="flex items-center justify-center py-10 gap-2 text-[12px] text-gray-400">
            <span className="w-4 h-4 border-2 border-gray-200 border-t-red-400 rounded-full animate-spin" />
            로그를 불러오는 중...
          </div>
        )}

        {/* 로그 없음 */}
        {!logsLoading && collectionLogs.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 gap-2 text-center">
            <svg className="w-8 h-8 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <p className="text-[12px] font-bold text-gray-400">수집 기록이 없습니다.</p>
            <p className="text-[11px] text-gray-400">데이터 수집 페이지에서 채널을 수집하면 로그가 표시됩니다.</p>
          </div>
        )}

        {/* 로그 테이블 */}
        {!logsLoading && collectionLogs.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 text-[11px] font-bold text-gray-400 border-b border-[#EEF2F7]">
                  <th className="px-4 py-3 text-left">채널명</th>
                  <th className="px-4 py-3 text-center">상태</th>
                  <th className="px-4 py-3 text-center min-w-[120px]">진행률</th>
                  <th className="px-4 py-3 text-right">수집 영상</th>
                  <th className="px-4 py-3 text-right">시작 시각</th>
                  <th className="px-4 py-3 text-right">완료 시각</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {collectionLogs.map((lg) => {
                  const barColor = lg.status === 'error' ? 'bg-red-400'
                    : lg.status === 'done' ? 'bg-emerald-400' : 'bg-blue-400';
                  return (
                    <tr key={lg.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-red-400 to-rose-500 flex items-center justify-center text-[10px] font-extrabold text-white shadow-sm shrink-0">
                            {lg.channel_name.slice(0, 1)}
                          </div>
                          <div className="min-w-0">
                            <p className="text-[12px] font-bold text-gray-700 truncate">{lg.channel_name}</p>
                            <p className="text-[10px] text-gray-400 truncate">#{lg.id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${statusStyle[lg.status] ?? ''}`}>
                          {lg.status === 'running' && <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />}
                          {statusLabel[lg.status] ?? lg.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                            <div className={`h-1.5 rounded-full ${barColor}`} style={{ width: `${lg.percent}%` }} />
                          </div>
                          <span className="text-[10px] font-bold text-gray-400 shrink-0 w-7 text-right">{lg.percent}%</span>
                        </div>
                        {lg.error_message && (
                          <p className="text-[10px] text-red-500 mt-0.5 truncate max-w-[160px]">{lg.error_message}</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-[11px] font-bold text-gray-500">
                        {lg.collected_videos.toLocaleString()} / {lg.total_videos.toLocaleString() || '-'}
                      </td>
                      <td className="px-4 py-3 text-right text-[11px] text-gray-400">{lg.started_at}</td>
                      <td className="px-4 py-3 text-right text-[11px]">
                        {lg.finished_at
                          ? <span className="text-gray-400">{lg.finished_at}</span>
                          : <span className="text-blue-400 font-bold">진행중...</span>
                        }
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

        </div>{/* space-y-5 콘텐츠 내부 end */}
      </div>{/* relative 오버레이 래퍼 end */}
    </div>
  );
}

// ── AI 분석 카드 ──────────────────────────────────────────────────────────────

function AiAnalysisCard({
  edaData, channelId, savedReport,
}: {
  edaData: EdaData | null;
  channelId: string;
  savedReport: AiReport | null;
}) {
  const [report,  setReport]  = useState<AiReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiError, setAiError] = useState('');

  // 부모에서 저장된 리포트가 로드되면 표시
  useEffect(() => {
    if (savedReport) setReport(savedReport);
  }, [savedReport]);

  const generate = async () => {
    setLoading(true);
    setAiError('');
    try {
      const { data } = await axios.post<AiReport & { success: boolean; error?: string }>(
        '/internal/ai-report',
        { edaData, channel_id: channelId }
      );
      if (data.success) {
        setReport({ summary: data.summary, insights: data.insights });
      } else {
        setAiError(data.error ?? 'AI 분석 생성에 실패했습니다.');
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { error?: string } } };
      setAiError(axiosErr.response?.data?.error ?? 'AI 서버 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = () => { generate(); };

  const handleRegenerate = async () => {
    const Swal = (await import('sweetalert2')).default;
    const result = await Swal.fire({
      title: 'AI 분석 재생성',
      text: '최신 데이터를 기반으로 AI 분석을 다시 생성하시겠습니까?',
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#7C3AED',
      cancelButtonColor: '#9CA3AF',
      confirmButtonText: '재생성',
      cancelButtonText: '취소',
    });
    if (result.isConfirmed) {
      setReport(null);
      generate();
    }
  };

  const videoCount    = edaData?.kpi.total_videos.toLocaleString() ?? '0';
  const channelCount  = edaData?.kpi.channel_count ?? 0;

  return (
    <div className="bg-white rounded-2xl border border-[#EEF2F7] shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#EEF2F7]"
        style={{ background: 'linear-gradient(135deg,#FAF5FF 0%,#EDE9FE 100%)' }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-sm shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div>
            <h3 className="text-[13px] font-extrabold text-gray-800">AI 분석 리포트</h3>
            <p className="text-[11px] text-gray-500 mt-0.5">수집 데이터를 AI가 종합 분석하여 인사이트를 제공합니다.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {report && !loading && (
            <button onClick={handleRegenerate}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold text-violet-600 border border-violet-200 bg-white hover:bg-violet-50 rounded-lg transition-colors">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              재생성
            </button>
          )}
          {!report && !loading && (
            <button onClick={handleGenerate}
              className="flex items-center gap-1.5 px-4 py-2 text-[12px] font-bold text-white bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 rounded-xl transition-all shadow-sm">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              AI 분석 생성
            </button>
          )}
        </div>
      </div>

      {/* 로딩 */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-12 gap-4">
          <div className="relative w-12 h-12">
            <div className="absolute inset-0 rounded-full border-4 border-violet-100" />
            <div className="absolute inset-0 rounded-full border-4 border-t-violet-500 animate-spin" />
          </div>
          <div className="text-center">
            <p className="text-[13px] font-bold text-gray-700">AI가 데이터를 분석하고 있습니다...</p>
            <p className="text-[11px] text-gray-400 mt-1">{videoCount}개 영상 · {channelCount}개 채널 데이터 처리 중</p>
          </div>
        </div>
      )}

      {/* 오류 */}
      {aiError && !loading && (
        <div className="m-5 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-[12px] font-bold text-red-600">
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {aiError}
        </div>
      )}

      {/* 미생성 상태 */}
      {!report && !loading && !aiError && (
        <div className="flex flex-col items-center justify-center py-12 gap-3 text-center px-6">
          <div className="w-14 h-14 rounded-2xl bg-violet-50 border border-violet-100 flex items-center justify-center">
            <svg className="w-7 h-7 text-violet-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <p className="text-[13px] font-bold text-gray-500">아직 AI 분석이 생성되지 않았습니다.</p>
          <p className="text-[11px] text-gray-400">위의 <strong className="text-violet-500">AI 분석 생성</strong> 버튼을 클릭하면 수집된 데이터를 기반으로<br/>성장 트렌드, 최적 업로드 패턴, 콘텐츠 전략 등을 자동 분석합니다.</p>
        </div>
      )}

      {/* 분석 결과 */}
      {report && !loading && (
        <div className="p-5 space-y-5">
          {/* 종합 요약 */}
          <div className="flex gap-3 p-4 bg-violet-50 border border-violet-100 rounded-xl">
            <span className="text-lg shrink-0 mt-0.5">🤖</span>
            <div>
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <p className="text-[12px] font-extrabold text-violet-800">종합 분석 요약</p>
                <span className="text-[9px] font-bold bg-violet-200 text-violet-700 px-2 py-0.5 rounded-full">AI 생성됨</span>
                {report?.created_at && (
                  <span className="text-[9px] text-gray-400 ml-auto">{report.created_at} 저장됨</span>
                )}
              </div>
              <p className="text-[12px] text-gray-600 leading-relaxed">{report.summary}</p>
            </div>
          </div>

          {/* 인사이트 4개 그리드 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {report.insights.map((item) => (
              <div key={item.label} className={`p-4 rounded-xl border ${item.color}`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-[16px]">{item.icon}</span>
                  <p className="text-[12px] font-extrabold text-gray-800">{item.label}</p>
                  <span className={`ml-auto text-[9px] font-bold px-2 py-0.5 rounded-full ${item.badgeColor}`}>
                    {item.badge}
                  </span>
                </div>
                <ul className="space-y-1.5">
                  {item.points.map((pt, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="mt-1.5 w-1 h-1 rounded-full bg-gray-400 shrink-0" />
                      <span className="text-[11px] text-gray-600 leading-relaxed">{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* 하단 면책 */}
          <p className="text-[10px] text-gray-400 text-center">
            ※ AI 분석은 수집된 데이터 기반의 참고용 인사이트이며, 실제 채널 운영 결과와 다를 수 있습니다.
          </p>
        </div>
      )}
    </div>
  );
}

function count(n: number) { return n.toLocaleString(); }
