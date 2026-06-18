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

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const navigate = useNavigate();

  const fetchData = () => {
    setData(null);
    client.get('/dashboard/').then((res) => setData(res.data));
  };

  useEffect(() => { fetchData(); }, []);

  if (!data) return null;

  const total     = data.status_stats.reduce((s, i) => s + i.count, 0);
  const pending   = data.status_stats.find((s) => s.status === 'pending')?.count ?? 0;
  const done      = data.status_stats.find((s) => s.status === 'done')?.count ?? 0;

  const good  = data.emotion_stats.find((e) => e.emotion_label === 'good')?.count  ?? 0;
  const normal= data.emotion_stats.find((e) => e.emotion_label === 'normal')?.count?? 0;
  const bad   = data.emotion_stats.find((e) => e.emotion_label === 'bad')?.count   ?? 0;
  const analyzed = good + normal + bad;
  const goodPct  = analyzed ? Math.round(good / analyzed * 100) : 0;
  const normalPct= analyzed ? Math.round(normal / analyzed * 100) : 0;
  const badPct   = analyzed ? Math.round(bad / analyzed * 100) : 0;

  const donutBg = `conic-gradient(var(--light) 0 ${goodPct}%, var(--slate) ${goodPct}% ${goodPct + normalPct}%, var(--neg) ${goodPct + normalPct}% 100%)`;

  return (
    <AdminLayout>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 22 }}>
        <div className="h-page">대시보드</div>
        <button className="btn btn-sm" onClick={fetchData}>↻ 새로고침</button>
      </div>

      {/* 통계 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { ico: '▤', lbl: '전체 리뷰',  val: total.toLocaleString() },
          { ico: '⏳', lbl: '대기 중',    val: pending.toLocaleString(), highlight: true },
          { ico: '✓',  lbl: '처리 완료', val: done.toLocaleString() },
          { ico: '☺',  lbl: '분석된 리뷰', val: analyzed.toLocaleString() },
        ].map((s) => (
          <div key={s.lbl} className="card stat" style={{ display: 'flex', alignItems: 'center', gap: 14, borderColor: s.highlight ? 'var(--navy)' : undefined }}>
            <div className="ico">{s.ico}</div>
            <div><div className="lbl">{s.lbl}</div><div className="val">{s.val}</div></div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 20, marginBottom: 24, alignItems: 'stretch' }}>
        {/* 감성 분포 */}
        <div className="card" style={{ flex: '0 0 56%' }}>
          <div className="h-sec" style={{ marginBottom: 18 }}>감성 분포</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 36 }}>
            <div className="donut" style={{ background: donutBg }}>
              <div className="ctr"><b>{goodPct}%</b><span>긍정</span></div>
            </div>
            <div className="legend">
              <div><i style={{ background: 'var(--light)' }} />긍정 &nbsp;{goodPct}% <span className="muted">({good})</span></div>
              <div><i style={{ background: 'var(--slate)' }} />중립 &nbsp;{normalPct}% <span className="muted">({normal})</span></div>
              <div><i style={{ background: 'var(--neg)' }} />부정 &nbsp;{badPct}% <span className="muted">({bad})</span></div>
            </div>
          </div>
        </div>

        {/* 최근 리뷰 */}
        <div className="card" style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
          <div className="h-sec" style={{ marginBottom: 10 }}>최근 리뷰</div>
          {data.recent_reviews.map((r) => (
            <div
              key={r.id}
              style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 6px', borderRadius: 8, cursor: 'pointer', minWidth: 0, overflow: 'hidden' }}
              onClick={() => navigate(`/admin/reviews/${r.id}`)}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(173,216,230,.20)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '')}
            >
              <span style={{ fontWeight: 800, fontSize: 13, flexShrink: 0, maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.user_name}</span>
              <span style={{ fontSize: 13, color: '#666', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.text}</span>
              <span style={{ flexShrink: 0 }}><EmotionBadge emotion={r.emotion_label} /></span>
              <span style={{ flexShrink: 0 }}><StatusBadge status={r.status} /></span>
            </div>
          ))}
        </div>
      </div>
    </AdminLayout>
  );
}
