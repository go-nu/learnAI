import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AdminLayout from '../../components/AdminLayout';
import EmotionBadge from '../../components/EmotionBadge';
import StatusBadge from '../../components/StatusBadge';
import Stars from '../../components/Stars';
import client from '../../api/client';

interface Tag { tag: string; }
interface Reply { reply_text: string; created_at: string; }
interface Review {
  id: number;
  user_name: string;
  text: string;
  rating: number;
  emotion_label: string | null;
  status: string;
  created_at: string;
  reply: Reply | null;
  tags: Tag[];
}

export default function ReviewDetail() {
  const { id } = useParams<{ id: string }>();
  const [review, setReview] = useState<Review | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    client.get(`/reviews/${id}/`).then((res) => setReview(res.data));
  }, [id]);

  if (!review) return null;

  return (
    <AdminLayout>
      <div className="crumb" style={{ marginBottom: 6 }}>
        <span className="clk" onClick={() => navigate('/admin/reviews')} style={{ textDecoration: 'none', color: 'inherit', cursor: 'pointer' }}>리뷰 목록</span> &gt; 리뷰 상세
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
        <span className="h-page" style={{ fontSize: 23 }}>리뷰 #{review.id}</span>
        <EmotionBadge emotion={review.emotion_label} />
        <StatusBadge status={review.status} />
      </div>

      {/* 리뷰 원문 */}
      <div className="card" style={{ marginBottom: 22 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap', fontSize: 14 }}>
          <span style={{ fontWeight: 800 }}>{review.user_name}</span>
          <Stars rating={review.rating} />
          <EmotionBadge emotion={review.emotion_label} />
          <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--ink2)' }}>
            {new Date(review.created_at).toLocaleDateString('ko-KR')}
          </span>
        </div>
        <hr className="divider" style={{ margin: '16px 0' }} />
        <p style={{ fontSize: 15, color: '#555', lineHeight: 1.8 }}>{review.text}</p>
        {review.tags.length > 0 && (
          <div className="tagwrap" style={{ marginTop: 12 }}>
            {review.tags.map((t) => <span key={t.tag} className="tag pos">{t.tag}</span>)}
          </div>
        )}
      </div>

      {/* AI 자동 생성 답변 */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
          <span className="h-sec">AI 자동 생성 답변</span>
          <span className="badge b-ok">자동 발행 완료</span>
        </div>
        {review.reply ? (
          <div style={{ background: '#fff', border: '1.5px solid var(--light)', borderRadius: 10, padding: 16, fontSize: 14, color: '#555', lineHeight: 1.8, minHeight: 120 }}>
            {review.reply.reply_text}
          </div>
        ) : (
          <div style={{ background: '#fff', border: '1.5px solid var(--light)', borderRadius: 10, padding: 16, fontSize: 14, color: 'var(--ink2)', lineHeight: 1.8, minHeight: 120 }}>
            {review.status === 'done' ? '답변이 없습니다.' : 'AI 답변 생성 중입니다...'}
          </div>
        )}
      </div>

      <div style={{ marginTop: 22 }}>
        <button className="btn btn-ghost" onClick={() => navigate('/admin/reviews')}>← 목록으로 돌아가기</button>
      </div>
    </AdminLayout>
  );
}
