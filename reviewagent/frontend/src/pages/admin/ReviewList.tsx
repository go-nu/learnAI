import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../../components/AdminLayout';
import EmotionBadge from '../../components/EmotionBadge';
import Pagination from '../../components/Pagination';
import StatusBadge from '../../components/StatusBadge';
import Stars from '../../components/Stars';
import client from '../../api/client';

interface Review {
  id: number;
  user_name: string;
  text: string;
  rating: number;
  emotion_label: string | null;
  status: string;
  created_at: string;
}

const PER = 10;

export default function ReviewList() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [emotion, setEmotion] = useState('');
  const [status, setStatus]   = useState('');
  const [page, setPage]       = useState(1);
  const navigate = useNavigate();

  const fetchReviews = () => {
    const params = new URLSearchParams();
    if (emotion) params.set('emotion', emotion);
    if (status)  params.set('status', status);
    client.get(`/reviews/?${params}`).then((res) => { setReviews(res.data); setPage(1); });
  };

  useEffect(() => { fetchReviews(); }, []);

  const totalPages = Math.ceil(reviews.length / PER);
  const paged = reviews.slice((page - 1) * PER, page * PER);

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-ink">리뷰 목록</h1>
        <button
          onClick={fetchReviews}
          className="text-sm px-3 py-1.5 rounded-lg border border-divider text-ink2 hover:bg-hover-bg transition-all duration-150"
        >↻ 새로고침</button>
      </div>

      {/* 필터 */}
      <div className="bg-white rounded-2xl shadow-card p-4 mb-5 flex gap-3 items-center">
        <select
          className="w-[160px] border border-divider rounded-lg px-3 py-2 text-sm text-ink bg-white focus:outline-none focus:border-primary cursor-pointer"
          value={emotion}
          onChange={(e) => setEmotion(e.target.value)}
        >
          <option value="">감성 · 전체</option>
          <option value="good">긍정</option>
          <option value="normal">중립</option>
          <option value="bad">부정</option>
        </select>
        <select
          className="w-[190px] border border-divider rounded-lg px-3 py-2 text-sm text-ink bg-white focus:outline-none focus:border-primary cursor-pointer"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">상태 · 전체</option>
          <option value="pending">대기 중</option>
          <option value="processing">처리 중</option>
          <option value="done">완료</option>
        </select>
        <button
          className="px-4 py-2 bg-primary text-white text-sm font-semibold rounded-lg hover:bg-primary-dark transition-all duration-150"
          onClick={fetchReviews}
        >검색</button>
      </div>

      {/* 테이블 */}
      <div className="border border-divider rounded-xl overflow-hidden bg-white">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr>
              {['No', '작성자', '리뷰', '별점', '감성', '상태', '작성일'].map((h) => (
                <th key={h} className="bg-gray-50 text-ink2 text-left font-semibold text-xs py-3 px-4 whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.map((r, i) => (
              <tr
                key={r.id}
                className="border-t border-divider cursor-pointer hover:bg-hover-bg transition-all duration-150"
                onClick={() => navigate(`/admin/reviews/${r.id}`)}
              >
                <td className="py-3 px-4">{(page - 1) * PER + i + 1}</td>
                <td className="py-3 px-4">{r.user_name}</td>
                <td className="py-3 px-4 max-w-[360px] truncate">{r.text}</td>
                <td className="py-3 px-4"><Stars rating={r.rating} /></td>
                <td className="py-3 px-4"><EmotionBadge emotion={r.emotion_label} /></td>
                <td className="py-3 px-4"><StatusBadge status={r.status} /></td>
                <td className="py-3 px-4 whitespace-nowrap">{new Date(r.created_at).toLocaleDateString('ko-KR')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination page={page} totalPages={totalPages} onChange={(p) => { setPage(p); window.scrollTo(0, 0); }} />
      <div className="text-center text-xs text-ink2 mt-2.5">행을 클릭하면 리뷰 상세로 이동합니다</div>
    </AdminLayout>
  );
}
