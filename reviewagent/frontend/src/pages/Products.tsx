import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../components/AdminLayout';
import CustomerLayout from '../components/CustomerLayout';
import { useAuth } from '../context/AuthContext';
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
  const { user } = useAuth();
  const Layout = user?.role === 'admin' ? AdminLayout : CustomerLayout;

  useEffect(() => {
    client.get('/products/').then((res) => setProducts(res.data));
  }, []);

  return (
    <Layout>
      <div className="h-page" style={{ marginBottom: 22 }}>상품 목록</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 24 }}>
        {products.map((p) => (
          <div key={p.id} className="card prodcard" style={{ padding: 0 }} onClick={() => navigate(`/products/${p.id}`)}>
            <div className="imgph" style={{ height: 180 }}>
              <span className="init">{p.name.charAt(0)}</span>
            </div>
            <div style={{ padding: 16 }}>
              <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--navy)' }}>{p.name}</div>
              <div style={{ fontSize: 13, color: 'var(--ink2)', margin: '4px 0 14px' }}>{p.category}</div>
              <span className="btn btn-primary btn-block">리뷰 작성하기</span>
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
}
