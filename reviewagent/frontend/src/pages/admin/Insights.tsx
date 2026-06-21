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
      <h1 className="text-xl font-bold text-ink mb-6">인사이트</h1>

      {/* 요약 통계 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-2xl shadow-card p-6">
          <div className="text-xs text-ink2 mb-1">총 키워드 언급</div>
          <div className="text-2xl font-extrabold text-ink leading-none">{total.toLocaleString()}</div>
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
          <div className="text-base font-extrabold text-ink mb-5">자주 언급된 키워드 TOP {LIMIT}</div>
          {tags.map((t, i) => (
            <div className="flex items-center gap-3 mb-3" key={t.tag}>
              <span className="w-[70px] text-right shrink-0 text-sm text-ink">{t.tag}</span>
              <div className="flex-1 h-5 bg-gray-100 rounded-md overflow-hidden">
                <div
                  className="h-full bg-primary rounded-md"
                  style={{ width: `${Math.round(t.count / max * 100)}%`, opacity: (1 - i * 0.07).toFixed(2) as unknown as number }}
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
