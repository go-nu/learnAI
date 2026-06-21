import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Swal from 'sweetalert2';
import CustomerLayout from '../components/CustomerLayout';
import EmotionBadge from '../components/EmotionBadge';
import Pagination from '../components/Pagination';
import Stars from '../components/Stars';
import client from '../api/client';

interface ReviewReply { reply_text: string; created_at: string; }
interface Review {
  id: number;
  user_name: string;
  text: string;
  rating: number;
  emotion_label: string | null;
  status: string;
  created_at: string;
  reply: ReviewReply | null;
}
interface Product {
  id: number;
  name: string;
  category: string;
  description: string;
  reviews: Review[];
}

const PER = 5;

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [rating, setRating]   = useState(3);
  const [text, setText]       = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [page, setPage] = useState(1);

  const fetchProduct = () => {
    client.get(`/products/${id}/`).then((res) => setProduct(res.data));
  };

  useEffect(() => { fetchProduct(); }, [id]);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setSubmitting(true);
    try {
      await client.post('/reviews/create/', { product: id, text, rating });
      await Swal.fire({
        icon: 'success',
        title: '리뷰가 등록되었습니다.',
        text: 'AI 답변은 약 10분 후 생성됩니다.',
        confirmButtonColor: '#1E7A5E',
      });
      setText('');
      setRating(3);
      setPage(1);
      fetchProduct();
    } finally {
      setSubmitting(false);
    }
  };

  if (!product) return null;

  const totalPages = Math.ceil(product.reviews.length / PER);
  const paged = product.reviews.slice((page - 1) * PER, page * PER);

  return (
    <CustomerLayout>
      <div className="text-xs text-ink2 mb-4">
        <Link to="/products" className="hover:text-primary hover:underline">← 상품 목록</Link>
      </div>

      <div className="grid gap-8 items-start" style={{ gridTemplateColumns: '40fr 60fr' }}>
        {/* 좌측: 상품 정보 */}
        <div>
          <div className="h-[260px] rounded-xl bg-[var(--primary-glow)] flex items-center justify-center mb-4">
            <span className="text-6xl font-bold text-primary opacity-80">{product.name.charAt(0)}</span>
          </div>
          <div className="text-2xl font-bold text-ink">{product.name}</div>
          <div className="text-xs text-ink2 mt-1.5 mb-3">{product.category}</div>
          <p className="text-sm text-ink2 leading-relaxed">{product.description}</p>
        </div>

        {/* 우측: 리뷰 작성 + 리뷰 목록 */}
        <div>
          <h2 className="text-lg font-semibold text-ink mb-3">리뷰 작성</h2>
          <div className="bg-white rounded-2xl shadow-card p-5 flex flex-col mb-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-sm text-ink2">별점</span>
              <span className="text-3xl cursor-pointer leading-none select-none">
                {[1, 2, 3, 4, 5].map((n) => (
                  <span
                    key={n}
                    onClick={() => setRating(n)}
                    className={n <= rating ? 'text-yellow-400' : 'text-divider'}
                  >★</span>
                ))}
              </span>
            </div>
            <textarea
              className="border border-divider rounded-lg px-3.5 py-2.5 text-sm text-ink resize-vertical leading-relaxed focus:outline-none focus:border-primary focus:ring-2 focus:ring-[var(--primary-glow)] min-h-[100px]"
              rows={5}
              placeholder="리뷰를 작성해 주세요..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <button
              className="mt-3 w-full py-3 bg-primary text-white font-semibold text-base rounded-lg hover:bg-primary-dark transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed"
              onClick={handleSubmit}
              disabled={submitting || !text.trim()}
            >
              {submitting ? '등록 중...' : '리뷰 등록'}
            </button>
          </div>

          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-lg font-semibold text-ink">리뷰 목록</h2>
            <span className="text-sm text-ink2">총 {product.reviews.length}개</span>
          </div>
          <hr className="border-0 border-t border-divider mb-1" />

          {paged.map((r) => (
            <div key={r.id} className="py-4 border-b border-divider last:border-0">
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="font-bold text-sm text-ink">{r.user_name}</span>
                <Stars rating={r.rating} />
                <EmotionBadge emotion={r.emotion_label} />
                <span className="ml-auto text-xs text-ink2">{new Date(r.created_at).toLocaleDateString('ko-KR')}</span>
              </div>
              <p className="text-sm text-ink2 mt-2 leading-relaxed">{r.text}</p>
              {r.reply && (
                <div className="mt-3 ml-3.5 pl-3.5 border-l-[3px] border-l-green-100">
                  <div className="text-xs font-bold text-primary mb-0.5">관리자 답변</div>
                  <div className="text-sm text-ink2 leading-relaxed">{r.reply.reply_text}</div>
                </div>
              )}
            </div>
          ))}

          <Pagination page={page} totalPages={totalPages} onChange={(p) => setPage(p)} />
        </div>
      </div>
    </CustomerLayout>
  );
}
