import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CustomerLayout from '../components/CustomerLayout';
import client from '../api/client';

interface Product {
  id: number;
  name: string;
  category: string;
  description: string;
}

export default function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    client.get('/products/').then((res) => setProducts(res.data));
  }, []);

  return (
    <CustomerLayout>
      <h1 className="text-xl font-bold text-ink mb-6">상품 목록</h1>
      <div className="grid grid-cols-3 gap-6">
        {products.map((p) => (
          <div
            key={p.id}
            className="bg-white rounded-2xl shadow-card overflow-hidden cursor-pointer hover:shadow-lg hover:-translate-y-0.5 transition-all duration-150"
            onClick={() => navigate(`/products/${p.id}`)}
          >
            {/* 이미지 플레이스홀더 */}
            <div className="h-[180px] bg-[var(--primary-glow)] flex items-center justify-center">
              <span className="text-5xl font-bold text-primary opacity-80">{p.name.charAt(0)}</span>
            </div>
            <div className="p-4">
              <div className="font-bold text-base text-ink">{p.name}</div>
              <div className="text-xs text-ink2 mt-1 mb-3">{p.category}</div>
              <button className="w-full py-2.5 bg-primary text-white text-sm font-semibold rounded-lg hover:bg-primary-dark transition-all duration-150">
                리뷰 작성하기
              </button>
            </div>
          </div>
        ))}
      </div>
    </CustomerLayout>
  );
}
