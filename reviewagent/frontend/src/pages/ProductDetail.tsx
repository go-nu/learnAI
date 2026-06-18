import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Swal from 'sweetalert2';
import AdminLayout from '../components/AdminLayout';
import CustomerLayout from '../components/CustomerLayout';
import Pagination from '../components/Pagination';
import Stars from '../components/Stars';
import EmotionBadge from '../components/EmotionBadge';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';

interface Reply { reply_text: string; }
interface Review {
  id: number;
  user_name: string;
  text: string;
  rating: number;
  emotion_label: string | null;
  status: string;
  created_at: string;
  reply: Reply | null;
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
  const [rating, setRating] = useState(3);
  const [hoverRating, setHoverRating] = useState(0);
  const [text, setText] = useState('');
  const [page, setPage] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const { user } = useAuth();
  const Layout = user?.role === 'admin' ? AdminLayout : CustomerLayout;

  const fetchProduct = () => {
    client.get(`/products/${id}/`).then((res) => setProduct(res.data));
  };

  useEffect(() => { fetchProduct(); }, [id]);

  const reviews = product?.reviews ?? [];
  const totalPages = Math.ceil(reviews.length / PER);
  const paged = reviews.slice((page - 1) * PER, page * PER);

  const handleSubmit = async () => {
    if (!text.trim()) {
      Swal.fire({ icon: 'warning', title: '리뷰 내용을 입력해 주세요.', confirmButtonColor: '#000080' });
      return;
    }
    setSubmitting(true);
    try {
      await client.post('/reviews/create/', { product: Number(id), text, rating });
      Swal.fire({ icon: 'success', title: '리뷰가 등록되었습니다.', text: 'AI 답변은 잠시 후 생성됩니다.', confirmButtonColor: '#000080' });
      setText('');
      setRating(3);
      setPage(1);
      fetchProduct();
    } catch {
      Swal.fire({ icon: 'error', title: '등록에 실패했습니다.', confirmButtonColor: '#000080' });
    } finally {
      setSubmitting(false);
    }
  };

  if (!product) return null;

  return (
    <Layout>
      <div className="crumb" style={{ marginBottom: 16 }}>
        <Link className="clk linklike" to="/products" style={{ textDecoration: 'none' }}>← 상품 목록</Link>
      </div>
      <div style={{ display: 'flex', gap: 32, alignItems: 'flex-start' }}>
        {/* 상품 정보 */}
        <div style={{ flex: '0 0 40%' }}>
          <div className="imgph" style={{ height: 260, borderRadius: 12, marginBottom: 16 }}>
            <span className="cam">상품 이미지</span>
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--navy)' }}>{product.name}</div>
          <div style={{ fontSize: 13, color: 'var(--ink2)', margin: '6px 0 14px' }}>{product.category}</div>
          <p style={{ fontSize: 14, color: '#555', lineHeight: 1.8 }}>{product.description}</p>
        </div>

        {/* 리뷰 작성 + 목록 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="h-sec" style={{ marginBottom: 14 }}>리뷰 작성</div>
          <div className="card" style={{ padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14 }}>
              <span style={{ fontSize: 14, color: 'var(--ink2)' }}>별점</span>
              <span className="stars" style={{ fontSize: 28, cursor: 'pointer' }}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <span
                    key={n}
                    className={(hoverRating || rating) >= n ? '' : 'off'}
                    onClick={() => setRating(n)}
                    onMouseEnter={() => setHoverRating(n)}
                    onMouseLeave={() => setHoverRating(0)}
                  >★</span>
                ))}
              </span>
            </div>
            <textarea
              className="field"
              rows={5}
              placeholder="리뷰를 작성해 주세요..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <button className="btn btn-primary btn-block btn-lg" style={{ marginTop: 14 }} onClick={handleSubmit} disabled={submitting}>
              {submitting ? <><span className="spin" />등록 중...</> : '리뷰 등록'}
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', margin: '28px 0 10px' }}>
            <div className="h-sec">리뷰 목록</div>
            <div className="muted" style={{ fontSize: 13 }}>총 {reviews.length}개</div>
          </div>
          <hr className="divider" />

          {paged.map((r) => (
            <div className="rv" key={r.id}>
              <div className="top">
                <span style={{ fontWeight: 800 }}>{r.user_name}</span>
                <Stars rating={r.rating} />
                <EmotionBadge emotion={r.emotion_label} />
                <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--ink2)' }}>
                  {new Date(r.created_at).toLocaleDateString('ko-KR')}
                </span>
              </div>
              <p style={{ fontSize: 14, color: '#555', marginTop: 8, lineHeight: 1.7 }}>{r.text}</p>
              {r.reply && (
                <div className="reply">
                  <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--navy)', marginBottom: 3 }}>관리자 답변</div>
                  <div style={{ fontSize: 13, color: '#666', lineHeight: 1.7 }}>{r.reply.reply_text}</div>
                </div>
              )}
            </div>
          ))}

          <Pagination page={page} totalPages={totalPages} onChange={setPage} />
        </div>
      </div>
    </Layout>
  );
}
