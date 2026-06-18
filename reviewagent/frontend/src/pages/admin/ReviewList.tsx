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
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div className="h-page">리뷰 목록</div>
        <button className="btn btn-sm" onClick={fetchReviews}>↻ 새로고침</button>
      </div>

      {/* 필터 */}
      <div className="card" style={{ padding: 16, marginBottom: 20, display: 'flex', gap: 12, alignItems: 'center' }}>
        <select className="field" style={{ width: 160 }} value={emotion} onChange={(e) => setEmotion(e.target.value)}>
          <option value="">감성 · 전체</option>
          <option value="good">긍정</option>
          <option value="normal">중립</option>
          <option value="bad">부정</option>
        </select>
        <select className="field" style={{ width: 190 }} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">상태 · 전체</option>
          <option value="pending">대기 중</option>
          <option value="processing">처리 중</option>
          <option value="done">완료</option>
        </select>
        <button className="btn btn-primary" onClick={fetchReviews}>검색</button>
      </div>

      {/* 테이블 */}
      <div style={{ border: '1px solid var(--light)', borderRadius: 12, overflow: 'hidden' }}>
        <table className="tbl">
          <thead>
            <tr>
              <th>No</th><th>작성자</th><th>리뷰</th><th>별점</th><th>감성</th><th>상태</th><th>작성일</th>
            </tr>
          </thead>
          <tbody>
            {paged.map((r, i) => (
              <tr key={r.id} className="clickrow" onClick={() => navigate(`/admin/reviews/${r.id}`)}>
                <td>{(page - 1) * PER + i + 1}</td>
                <td>{r.user_name}</td>
                <td className="ell">{r.text}</td>
                <td><Stars rating={r.rating} /></td>
                <td><EmotionBadge emotion={r.emotion_label} /></td>
                <td><StatusBadge status={r.status} /></td>
                <td>{new Date(r.created_at).toLocaleDateString('ko-KR')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination page={page} totalPages={totalPages} onChange={(p) => { setPage(p); window.scrollTo(0, 0); }} />
      <div className="muted" style={{ textAlign: 'center', fontSize: 12, marginTop: 10 }}>행을 클릭하면 리뷰 상세로 이동합니다</div>
    </AdminLayout>
  );
}
