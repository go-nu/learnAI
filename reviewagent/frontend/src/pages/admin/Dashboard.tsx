import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../../components/AdminLayout';
import EmotionBadge from '../../components/EmotionBadge';
import StatusBadge from '../../components/StatusBadge';
import client from '../../api/client';

interface EmotionStat { emotion_label: string; count: number; }
interface StatusStat  { status: string; count: number; }
interface RecentReview { id: number; user_name: string; text: string; emotion_label: string | null; status: string; }
interface DashboardData {
  emotion_stats: EmotionStat[];
  status_stats:  StatusStat[];
  recent_reviews: RecentReview[];
}
interface TagStat { tag: string; count: number; }

const TAG_LIMIT = 10;

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [tags, setTags] = useState<TagStat[]>([]);
  const navigate = useNavigate();

  const fetchData = () => {
    setData(null);
    client.get('/dashboard/').then((res) => setData(res.data));
    client.get(`/insights/tags/?limit=${TAG_LIMIT}`).then((res) => setTags(res.data));
  };

  useEffect(() => { fetchData(); }, []);

  if (!data) return null;

  const total   = data.status_stats.reduce((s, i) => s + i.count, 0);
  const pending = data.status_stats.find((s) => s.status === 'pending')?.count ?? 0;
  const done    = data.status_stats.find((s) => s.status === 'done')?.count ?? 0;

  const good   = data.emotion_stats.find((e) => e.emotion_label === 'good')?.count   ?? 0;
  const normal = data.emotion_stats.find((e) => e.emotion_label === 'normal')?.count ?? 0;
  const bad    = data.emotion_stats.find((e) => e.emotion_label === 'bad')?.count    ?? 0;
  const analyzed  = good + normal + bad;
  const goodPct   = analyzed ? Math.round(good   / analyzed * 100) : 0;
  const normalPct = analyzed ? Math.round(normal / analyzed * 100) : 0;
  const badPct    = analyzed ? Math.round(bad    / analyzed * 100) : 0;

  const donutBg = `conic-gradient(var(--success) 0 ${goodPct}%, var(--ink2) ${goodPct}% ${goodPct + normalPct}%, var(--danger) ${goodPct + normalPct}% 100%)`;

  const stats = [
    { ico: '▤', lbl: '전체 리뷰',   val: total.toLocaleString() },
    { ico: '⏳', lbl: '대기 중',     val: pending.toLocaleString(), highlight: true },
    { ico: '✓',  lbl: '처리 완료',  val: done.toLocaleString() },
    { ico: '☺',  lbl: '분석된 리뷰', val: analyzed.toLocaleString() },
  ];

  const tagMax   = tags[0]?.count ?? 1;
  const tagTotal = tags.reduce((s, t) => s + t.count, 0);

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-ink">대시보드</h1>
        <button
          onClick={fetchData}
          className="text-sm px-3 py-1.5 rounded-lg border border-divider text-ink2 hover:bg-hover-bg transition-all duration-150"
        >↻ 새로고침</button>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {stats.map((s) => (
          <div
            key={s.lbl}
            className={`bg-white rounded-2xl shadow-card p-6 flex items-center gap-4${s.highlight ? ' border-l-4 border-primary' : ''}`}
          >
            <div className="text-2xl">{s.ico}</div>
            <div>
              <div className="text-xs text-ink2 mb-1">{s.lbl}</div>
              <div className="text-xl font-bold text-ink">{s.val}</div>
            </div>
          </div>
        ))}
      </div>

      {/* 감성 분포 + 최근 리뷰 */}
      <div className="flex gap-5 mb-6 items-stretch">
        <div className="bg-white rounded-2xl shadow-card p-6 flex-[0_0_56%]">
          <h2 className="text-lg font-semibold text-ink mb-4">감성 분포</h2>
          <div className="flex items-center gap-9">
            <div className="donut" style={{ background: donutBg }}>
              <div className="ctr"><b>{goodPct}%</b><span>긍정</span></div>
            </div>
            <div className="flex flex-col gap-2 text-sm">
              <div className="flex items-center gap-2">
                <i className="w-2.5 h-2.5 rounded-full bg-success inline-block" />
                긍정 {goodPct}% <span className="text-ink2 ml-1">({good})</span>
              </div>
              <div className="flex items-center gap-2">
                <i className="w-2.5 h-2.5 rounded-full bg-ink2 inline-block" />
                중립 {normalPct}% <span className="text-ink2 ml-1">({normal})</span>
              </div>
              <div className="flex items-center gap-2">
                <i className="w-2.5 h-2.5 rounded-full bg-danger inline-block" />
                부정 {badPct}% <span className="text-ink2 ml-1">({bad})</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-card p-6 flex-1 min-w-0 overflow-hidden">
          <h2 className="text-lg font-semibold text-ink mb-3">최근 리뷰</h2>
          {data.recent_reviews.map((r) => (
            <div
              key={r.id}
              className="flex items-center gap-3 px-2 py-2.5 rounded-lg cursor-pointer hover:bg-hover-bg transition-all duration-150 min-w-0"
              onClick={() => navigate(`/admin/reviews/${r.id}`)}
            >
              <span className="font-extrabold text-sm text-ink shrink-0 max-w-[80px] truncate">{r.user_name}</span>
              <span className="text-sm text-ink2 flex-1 min-w-0 truncate">{r.text}</span>
              <span className="shrink-0"><EmotionBadge emotion={r.emotion_label} /></span>
              <span className="shrink-0"><StatusBadge status={r.status} /></span>
            </div>
          ))}
        </div>
      </div>

      {/* ── 인사이트 ── */}
      <h2 className="text-lg font-bold text-ink mb-4">인사이트</h2>

      {/* 인사이트 요약 통계 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-2xl shadow-card p-6">
          <div className="text-xs text-ink2 mb-1">총 키워드 언급</div>
          <div className="text-2xl font-extrabold text-ink leading-none">{tagTotal.toLocaleString()}</div>
        </div>
        <div className="bg-white rounded-2xl shadow-card p-6">
          <div className="text-xs text-ink2 mb-1">집계 키워드 수</div>
          <div className="text-2xl font-extrabold text-ink leading-none">{tags.length}</div>
        </div>
        <div className="bg-white rounded-2xl shadow-card p-6">
          <div className="text-xs text-ink2 mb-1">최다 언급 키워드</div>
          <div className="text-2xl font-extrabold text-ink leading-none">{tags[0] ? `#${tags[0].tag}` : '-'}</div>
        </div>
      </div>

      {/* 바 차트 + 키워드 목록 */}
      <div className="flex gap-5 items-stretch">
        <div className="bg-white rounded-2xl shadow-card p-6 basis-[55%] shrink-0">
          <div className="text-base font-extrabold text-ink mb-5">자주 언급된 키워드 TOP {TAG_LIMIT}</div>
          {tags.map((t, i) => (
            <div className="flex items-center gap-3 mb-3" key={t.tag}>
              <span className="w-[70px] text-right shrink-0 text-sm text-ink">{t.tag}</span>
              <div className="flex-1 h-5 bg-gray-100 rounded-md overflow-hidden">
                <div
                  className="h-full bg-primary rounded-md"
                  style={{ width: `${Math.round(t.count / tagMax * 100)}%`, opacity: (1 - i * 0.07).toFixed(2) as unknown as number }}
                />
              </div>
              <span className="w-10 shrink-0 text-primary font-extrabold text-sm">{t.count}</span>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-2xl shadow-card p-6 flex-1">
          <div className="text-base font-extrabold text-ink mb-4">전체 키워드 순위</div>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="bg-gray-50 text-ink2 text-left font-semibold text-xs py-3 px-4 whitespace-nowrap w-[60px]">순위</th>
                <th className="bg-gray-50 text-ink2 text-left font-semibold text-xs py-3 px-4 whitespace-nowrap">키워드</th>
                <th className="bg-gray-50 text-ink2 text-left font-semibold text-xs py-3 px-4 whitespace-nowrap">언급 수</th>
              </tr>
            </thead>
            <tbody>
              {tags.map((t, i) => (
                <tr key={t.tag} className="border-t border-divider">
                  <td className="py-3 px-4 font-extrabold text-primary">{i + 1}</td>
                  <td className="py-3 px-4 font-bold">{t.tag}</td>
                  <td className="py-3 px-4">{t.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  );
}
