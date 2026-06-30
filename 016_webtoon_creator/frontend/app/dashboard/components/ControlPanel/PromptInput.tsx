'use client';

import { useState } from 'react';

const MAX_LENGTH = 400;

// 결과물 묘사 텍스트에리어
export default function PromptInput() {
  const [value, setValue] = useState('');

  return (
    <div className="mb-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold" style={{ color: 'var(--dash-text)' }}>결과물 묘사</span>
        <span
          className="text-xs px-1.5 py-0.5 rounded font-medium"
          style={{ backgroundColor: 'var(--dash-surface)', color: 'var(--dash-text-sub)', border: '1px solid var(--dash-border)' }}
        >
          55+
        </span>
      </div>

      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value.slice(0, MAX_LENGTH))}
        placeholder="원하는 웹툰 컷의 내용을 입력해주세요."
        className="w-full rounded-lg p-3 text-sm resize-none focus:outline-none transition"
        style={{
          backgroundColor: 'var(--dash-surface)',
          color: 'var(--dash-text)',
          border: '1px solid var(--dash-border)',
          minHeight: '100px',
          caretColor: 'var(--dash-text)',
        }}
        rows={4}
      />

      <div className="text-right mt-1">
        <span className="text-xs" style={{ color: 'var(--dash-text-muted)' }}>
          {value.length}/{MAX_LENGTH}
        </span>
      </div>
    </div>
  );
}
