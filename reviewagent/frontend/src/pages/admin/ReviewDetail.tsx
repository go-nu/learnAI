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
      {/* 브레드크럼 */}
      <div className="text-xs text-ink2 mb-1.5">
        <span className="cursor-pointer hover:underline" onClick={() => navigate('/admin/reviews')}>리뷰 목록</span>
        {' > '}리뷰 상세
      </div>

      <div className="flex items-center gap-3 mb-5">
        <h1 className="text-2xl font-extrabold text-ink tracking-tight">리뷰 #{review.id}</h1>
        <EmotionBadge emotion={review.emotion_label} />
        <StatusBadge status={review.status} />
      </div>

      {/* 리뷰 원문 */}
      <div className="bg-white rounded-2xl shadow-card p-6 mb-6">
        <div className="flex items-center gap-4 flex-wrap text-sm">
          <span className="font-extrabold">{review.user_name}</span>
          <Stars rating={review.rating} />
          <EmotionBadge emotion={review.emotion_label} />
          <span className="ml-auto text-xs text-ink2">
            {new Date(review.created_at).toLocaleDateString('ko-KR')}
          </span>
        </div>
        <hr className="border-0 border-t border-divider my-4" />
        <p className="text-sm text-ink2 leading-relaxed">{review.text}</p>
        {review.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {review.tags.map((t) => (
              <span key={t.tag} className="text-xs px-3 py-1 rounded-full font-bold bg-green-50 text-primary">{t.tag}</span>
            ))}
          </div>
        )}
      </div>

      {/* AI 자동 생성 답변 */}
      <div className="bg-white rounded-2xl shadow-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-base font-extrabold text-ink">AI 자동 생성 답변</span>
          <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-green-100 text-green-700">자동 발행 완료</span>
        </div>
        <div className="bg-white border border-divider rounded-lg p-4 text-sm text-ink2 leading-relaxed min-h-[120px]">
          {review.reply
            ? review.reply.reply_text
            : (review.status === 'done' ? '답변이 없습니다.' : 'AI 답변 생성 중입니다...')}
        </div>
      </div>

      <div className="mt-6">
        <button
          className="px-4 py-2 border border-divider text-ink2 text-sm font-medium rounded-lg hover:bg-hover-bg transition-all duration-150"
          onClick={() => navigate('/admin/reviews')}
        >← 목록으로 돌아가기</button>
      </div>
    </AdminLayout>
  );
}
