'use client';

import { useState } from 'react';

const TABS = ['디자인', '애니메이션', '기타'];

// 기능 탭 + 액션 버튼
export default function FeatureTabs() {
  const [activeTab, setActiveTab] = useState('디자인');
  const [bgRemove, setBgRemove] = useState(false);

  return (
    <div>
      <div className="flex items-center justify-between flex-wrap gap-3">

        {/* 탭 목록 */}
        <div className="flex items-center gap-1 flex-wrap">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="px-3 py-1.5 text-sm rounded-lg font-medium transition-all"
              style={{
                backgroundColor: activeTab === tab ? 'var(--dash-active)' : 'transparent',
                color: activeTab === tab ? 'var(--dash-btn-primary-text)' : 'var(--dash-text-sub)',
                border: `1px solid ${activeTab === tab ? 'var(--dash-active)' : 'var(--dash-border)'}`,
              }}
            >
              {tab}
            </button>
          ))}

          {/* 배경 제거 토글 */}
          <div className="flex items-center gap-2 ml-2">
            <span className="text-sm" style={{ color: 'var(--dash-text-sub)' }}>배경 제거</span>
            <button
              onClick={() => setBgRemove(!bgRemove)}
              className="relative inline-flex h-5 w-9 rounded-full transition-colors"
              style={{ backgroundColor: bgRemove ? 'var(--dash-active)' : 'var(--dash-border)' }}
            >
              <span
                className="inline-block h-4 w-4 rounded-full shadow transform transition-transform my-0.5"
                style={{
                  backgroundColor: bgRemove ? 'var(--dash-btn-primary-text)' : 'var(--dash-text-sub)',
                  transform: bgRemove ? 'translateX(18px)' : 'translateX(2px)',
                }}
              />
            </button>
          </div>
        </div>

        {/* 액션 버튼 */}
        <div className="flex items-center gap-2">
          {/* 복사 */}
          <button
            className="p-2 rounded-lg transition-opacity hover:opacity-70"
            style={{ backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)', color: 'var(--dash-text-sub)' }}
            title="복사"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-4 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>

          {/* 재생성 */}
          <button
            className="p-2 rounded-lg transition-opacity hover:opacity-70"
            style={{ backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)', color: 'var(--dash-text-sub)' }}
            title="재생성"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h5M20 20v-5h-5M4 9a9 9 0 0114.65-3.65M19.4 15A9 9 0 015 17.65" />
            </svg>
          </button>

          {/* 에디터 배우기 */}
          <button
            className="px-3 py-2 rounded-lg text-xs font-semibold transition-opacity hover:opacity-70"
            style={{ backgroundColor: 'var(--dash-surface)', border: '1px solid var(--dash-border)', color: 'var(--dash-text)' }}
          >
            에디터 배우기
          </button>
        </div>
      </div>
    </div>
  );
}
