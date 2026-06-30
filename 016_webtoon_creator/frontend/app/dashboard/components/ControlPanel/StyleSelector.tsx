'use client';

import { useState, useRef } from 'react';

const STYLES = [
  { id: 1, label: '애니메이션' },
  { id: 2, label: '자유롭게' },
  { id: 3, label: '짧은컷 연출' },
  { id: 4, label: '수채화' },
  { id: 5, label: '웹툰' },
  { id: 6, label: '스케치' },
];

// 스타일 선택 썸네일 카드 (드래그 가로 스크롤)
export default function StyleSelector() {
  const [selected, setSelected] = useState(1);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 드래그 상태
  const isDragging = useRef(false);
  const startX = useRef(0);
  const scrollLeft = useRef(0);
  const dragMoved = useRef(false); // 드래그 이동 여부 (클릭과 구분)

  const onMouseDown = (e: React.MouseEvent) => {
    if (!scrollRef.current) return;
    isDragging.current = true;
    dragMoved.current = false;
    startX.current = e.pageX - scrollRef.current.offsetLeft;
    scrollLeft.current = scrollRef.current.scrollLeft;
    scrollRef.current.style.cursor = 'grabbing';
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current || !scrollRef.current) return;
    e.preventDefault();
    const x = e.pageX - scrollRef.current.offsetLeft;
    const walk = (x - startX.current) * 1.2;
    if (Math.abs(walk) > 3) dragMoved.current = true;
    scrollRef.current.scrollLeft = scrollLeft.current - walk;
  };

  const onMouseUp = () => {
    isDragging.current = false;
    if (scrollRef.current) scrollRef.current.style.cursor = 'grab';
  };

  const onMouseLeave = () => {
    isDragging.current = false;
    if (scrollRef.current) scrollRef.current.style.cursor = 'grab';
  };

  const handleClick = (id: number) => {
    // 드래그 이동이 있었으면 클릭 무시
    if (!dragMoved.current) setSelected(id);
  };

  return (
    <div className="mb-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold" style={{ color: 'var(--dash-text)' }}>스타일</span>
        <button className="text-xs transition-opacity hover:opacity-70" style={{ color: 'var(--dash-text-sub)' }}>
          122개 전체보기
        </button>
      </div>

      {/* 드래그 스크롤 컨테이너 */}
      <div
        ref={scrollRef}
        className="flex gap-2 pb-1 scrollbar-hidden select-none"
        style={{ overflowX: 'auto', cursor: 'grab' }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseLeave}
      >
        {STYLES.map((style) => (
          <button
            key={style.id}
            onClick={() => handleClick(style.id)}
            className="flex-shrink-0 flex flex-col items-center gap-1"
            draggable={false}
          >
            <div
              className="w-14 h-14 rounded-lg transition-all"
              style={{
                backgroundColor: 'var(--dash-surface)',
                border: `2px solid ${selected === style.id ? 'var(--dash-text)' : 'var(--dash-border)'}`,
              }}
            />
            <span
              className="text-xs whitespace-nowrap"
              style={{ color: selected === style.id ? 'var(--dash-text)' : 'var(--dash-text-sub)' }}
            >
              {style.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
