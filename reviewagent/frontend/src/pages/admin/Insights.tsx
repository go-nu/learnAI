import React, { useEffect, useState } from 'react';
import AdminLayout from '../../components/AdminLayout';
import client from '../../api/client';

interface TagStat { tag: string; count: number; }

const LIMIT = 10;

export default function Insights() {
  const [tags, setTags] = useState<TagStat[]>([]);

  useEffect(() => {
    client.get(`/insights/tags/?limit=${LIMIT}`).then((res) => setTags(res.data));
  }, []);

  const max = tags[0]?.count ?? 1;
  const total = tags.reduce((s, t) => s + t.count, 0);

  return (
    <AdminLayout>
      <div className="h-page" style={{ marginBottom: 20 }}>인사이트</div>

      {/* 요약 통계 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16, marginBottom: 24 }}>
        <div className="card stat"><div className="lbl">총 키워드 언급</div><div className="val">{total.toLocaleString()}</div></div>
        <div className="card stat"><div className="lbl">집계 키워드 수</div><div className="val">{tags.length}</div></div>
        <div className="card stat"><div className="lbl">최다 언급 키워드</div><div className="val">{tags[0] ? `#${tags[0].tag}` : '-'}</div></div>
      </div>

      {/* 바 차트 + 키워드 목록 */}
      <div style={{ display: 'flex', gap: 20, alignItems: 'stretch' }}>
        <div className="card" style={{ flex: '0 0 55%' }}>
          <div className="h-sec" style={{ marginBottom: 18 }}>자주 언급된 키워드 TOP {LIMIT}</div>
          {tags.map((t, i) => (
            <div className="barrow" key={t.tag}>
              <span className="lbl">{t.tag}</span>
              <span className="track">
                <span className="fill" style={{ width: `${Math.round(t.count / max * 100)}%`, opacity: (1 - i * 0.07).toFixed(2) as unknown as number }} />
              </span>
              <span className="num">{t.count}</span>
            </div>
          ))}
        </div>

        <div className="card" style={{ flex: 1 }}>
          <div className="h-sec" style={{ marginBottom: 14 }}>전체 키워드 순위</div>
          <table className="tbl">
            <thead>
              <tr><th style={{ width: 60 }}>순위</th><th>키워드</th><th>언급 수</th></tr>
            </thead>
            <tbody>
              {tags.map((t, i) => (
                <tr key={t.tag}>
                  <td style={{ fontWeight: 800, color: 'var(--navy)' }}>{i + 1}</td>
                  <td style={{ fontWeight: 700 }}>{t.tag}</td>
                  <td>{t.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  );
}
