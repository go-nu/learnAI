'use client';

import { useState } from 'react';

const RATIOS = [
  { id: '1:1', label: '1:1', w: 14, h: 14 },
  { id: '3:4', label: '3:4', w: 10, h: 14 },
  { id: '4:3', label: '4:3', w: 14, h: 10 },
];

// 이미지 비율 선택
export default function RatioSelector() {
  const [selected, setSelected] = useState('1:1');

  return (
    <div className="mb-5">
      <span className="text-xs font-semibold block mb-2" style={{ color: 'var(--dash-text)' }}>비율</span>

      <div className="flex gap-2">
        {RATIOS.map((ratio) => (
          <button
            key={ratio.id}
            onClick={() => setSelected(ratio.id)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all"
            style={{
              backgroundColor: selected === ratio.id ? 'var(--dash-btn-primary)' : 'var(--dash-surface)',
              color: selected === ratio.id ? 'var(--dash-btn-primary-text)' : 'var(--dash-text-sub)',
              border: `1px solid ${selected === ratio.id ? 'var(--dash-btn-primary)' : 'var(--dash-border)'}`,
            }}
          >
            <span
              className="inline-block rounded-sm"
              style={{
                width: ratio.w,
                height: ratio.h,
                border: `1.5px solid ${selected === ratio.id ? 'var(--dash-btn-primary-text)' : 'var(--dash-text-sub)'}`,
              }}
            />
            {ratio.label}
          </button>
        ))}
      </div>
    </div>
  );
}
