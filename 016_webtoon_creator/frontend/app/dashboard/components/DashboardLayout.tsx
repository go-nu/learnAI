'use client';

import { useState } from 'react';
import Link from 'next/link';
import UserMenu from './UserMenu';
import StyleSelector from './ControlPanel/StyleSelector';
import PromptInput from './ControlPanel/PromptInput';
import RatioSelector from './ControlPanel/RatioSelector';
import ImageUpload from './ControlPanel/ImageUpload';
import ActionButtons from './ControlPanel/ActionButtons';
import WarningBanner from './PreviewPanel/WarningBanner';
import ImagePreview from './PreviewPanel/ImagePreview';
import FeatureTabs from './PreviewPanel/FeatureTabs';
import WebtoonWorksContent from './WebtoonWorksContent';
import WebtoonEpisodesContent from './WebtoonEpisodesContent';
import WebtoonCutsContent from './WebtoonCutsContent';

type MenuKey =
  | 'webtoon-works'
  | 'webtoon-episodes'
  | 'webtoon-cuts'
  | 'image-create'
  | 'image-history';

// 사이드바 메뉴 그룹 정의
const MENU_GROUPS = [
  {
    label: '웹툰만들기',
    items: [
      { key: 'webtoon-works' as MenuKey,    label: '웹툰 작품' },
      { key: 'webtoon-episodes' as MenuKey, label: '웹툰 에피소드(회차)' },
      { key: 'webtoon-cuts' as MenuKey,     label: '웹툰 컷(개별 패널)' },
    ],
  },
  {
    label: '이미지생성',
    items: [
      { key: 'image-create' as MenuKey,  label: 'AI 이미지 만들기' },
      { key: 'image-history' as MenuKey, label: 'AI 이미지 생성 이력' },
    ],
  },
];

// 각 메뉴별 빈 상태(Empty State) 설정
const EMPTY_STATES: Record<Exclude<MenuKey, 'image-create'>, {
  title: string;
  desc: string;
  btnLabel?: string;
}> = {
  'webtoon-works': {
    title: '웹툰 작품',
    desc: '아직 등록된 웹툰 작품이 없습니다.\n새 웹툰을 만들어 보세요.',
    btnLabel: '+ 새 웹툰 만들기',
  },
  'webtoon-episodes': {
    title: '웹툰 에피소드(회차)',
    desc: '등록된 에피소드가 없습니다.\n웹툰 작품을 먼저 선택하거나 에피소드를 추가해 보세요.',
    btnLabel: '+ 에피소드 추가',
  },
  'webtoon-cuts': {
    title: '웹툰 컷(개별 패널)',
    desc: '등록된 컷이 없습니다.\nAI로 이미지를 생성하거나 에피소드를 먼저 선택해 주세요.',
    btnLabel: '+ 컷 추가',
  },
  'image-history': {
    title: 'AI 이미지 생성 이력',
    desc: '아직 생성된 이미지가 없습니다.\nAI 이미지 만들기에서 첫 이미지를 생성해 보세요.',
  },
};

// 전체 레이아웃: 상단 GNB + (사이드바 + 콘텐츠)
export default function DashboardLayout() {
  const [activeMenu, setActiveMenu] = useState<MenuKey>('image-create');

  return (
    <div
      className="flex flex-col h-screen"
      style={{ backgroundColor: 'var(--dash-bg)', color: 'var(--dash-text)' }}
    >

      {/* ── 상단 GNB ── */}
      <header
        className="flex items-center justify-between px-6 h-14 flex-shrink-0"
        style={{
          backgroundColor: 'var(--dash-panel)',
          borderBottom: '1px solid var(--dash-border)',
          zIndex: 10,
        }}
      >
        <Link
          href="/dashboard"
          className="text-lg font-black tracking-tight transition-opacity hover:opacity-70"
          style={{ color: 'var(--dash-text)', textDecoration: 'none' }}
        >
          ToonCraft
        </Link>
        <div className="flex items-center gap-3">
          <button
            className="flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg transition-opacity hover:opacity-70"
            style={{
              color: 'var(--dash-text-sub)',
              backgroundColor: 'var(--dash-surface)',
              border: '1px solid var(--dash-border)',
            }}
          >
            한국어
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <UserMenu />
        </div>
      </header>

      {/* ── 본문: 사이드바 + 콘텐츠 ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── 사이드바 네비게이션 (200px) ── */}
        <nav
          className="flex-shrink-0 flex flex-col py-6 overflow-y-auto scrollbar-hidden"
          style={{
            width: '200px',
            backgroundColor: 'var(--dash-panel)',
            borderRight: '1px solid var(--dash-border)',
          }}
        >
          {MENU_GROUPS.map((group) => (
            <div key={group.label} className="mb-7">
              {/* 그룹 헤더 */}
              <p
                className="px-5 mb-2 text-xs font-bold uppercase tracking-widest"
                style={{ color: 'var(--dash-text-muted)' }}
              >
                {group.label}
              </p>

              {/* 메뉴 아이템 */}
              {group.items.map((item) => {
                const isActive = activeMenu === item.key;
                return (
                  <button
                    key={item.key}
                    onClick={() => setActiveMenu(item.key)}
                    className="w-full text-left px-5 py-2.5 text-sm transition-all"
                    style={{
                      color: isActive ? '#00C73C' : 'var(--dash-text-sub)',
                      backgroundColor: isActive ? 'rgba(0, 199, 60, 0.08)' : 'transparent',
                      borderLeft: isActive ? '2px solid #00C73C' : '2px solid transparent',
                      fontWeight: isActive ? 600 : 400,
                    }}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        {/* ── 콘텐츠 영역 ── */}
        {activeMenu === 'image-create' ? (
          /* AI 이미지 만들기: 컨트롤 패널 + 프리뷰 패널 */
          <>
            <aside
              className="flex flex-col flex-shrink-0 p-4 overflow-y-auto scrollbar-hidden"
              style={{
                width: '346px',
                backgroundColor: 'var(--dash-panel)',
                borderRight: '1px solid var(--dash-border)',
              }}
            >
              <Link
                href="/dashboard"
                className="flex items-center gap-1 text-sm mb-5 w-fit transition-opacity hover:opacity-70"
                style={{ color: 'var(--dash-text-sub)', textDecoration: 'none' }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                바로 시작하기
              </Link>
              <StyleSelector />
              <PromptInput />
              <RatioSelector />
              <ImageUpload />
              <ActionButtons />
            </aside>

            <main
              className="flex-1 p-6 overflow-y-auto scrollbar-hidden"
              style={{ backgroundColor: 'var(--dash-bg)' }}
            >
              <WarningBanner />
              <FeatureTabs />
              <div className="mt-4">
                <ImagePreview />
              </div>
            </main>
          </>
        ) : activeMenu === 'webtoon-works' ? (
          <WebtoonWorksContent />
        ) : activeMenu === 'webtoon-episodes' ? (
          <WebtoonEpisodesContent />
        ) : activeMenu === 'webtoon-cuts' ? (
          <WebtoonCutsContent />
        ) : (
          /* image-history: 빈 상태 화면 */
          <ContentPlaceholder menuKey="image-history" />
        )}

      </div>
    </div>
  );
}

// 빈 상태(Empty State) 플레이스홀더 컴포넌트
function ContentPlaceholder({ menuKey }: { menuKey: Exclude<MenuKey, 'image-create'> }) {
  const state = EMPTY_STATES[menuKey];

  return (
    <main
      className="flex-1 flex flex-col overflow-y-auto scrollbar-hidden"
      style={{ backgroundColor: 'var(--dash-bg)' }}
    >
      {/* 섹션 헤더 */}
      <div className="px-8 py-6" style={{ borderBottom: '1px solid var(--dash-border)' }}>
        <h1 className="text-xl font-bold" style={{ color: 'var(--dash-text)' }}>
          {state.title}
        </h1>
      </div>

      {/* 빈 상태 */}
      <div className="flex-1 flex flex-col items-center justify-center gap-4 pb-20">
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center"
          style={{ backgroundColor: 'var(--dash-surface)' }}
        >
          <svg
            className="w-8 h-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            style={{ color: 'var(--dash-text-muted)' }}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>

        <p
          className="text-sm text-center whitespace-pre-line"
          style={{ color: 'var(--dash-text-sub)', lineHeight: 1.8 }}
        >
          {state.desc}
        </p>

        {state.btnLabel && (
          <button
            className="mt-2 px-5 py-2.5 text-sm font-bold rounded-lg transition-opacity hover:opacity-80"
            style={{ backgroundColor: '#00C73C', color: '#FFFFFF' }}
          >
            {state.btnLabel}
          </button>
        )}
      </div>
    </main>
  );
}
