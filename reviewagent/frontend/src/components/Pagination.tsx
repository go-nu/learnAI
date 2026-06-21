import React from 'react';

interface Props {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}

const GROUP = 5;

const baseBtn = 'w-8 h-8 flex items-center justify-center rounded-lg text-sm transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed';
const inactiveBtn = `${baseBtn} text-ink2 hover:bg-hover-bg`;
const activeBtn   = `${baseBtn} bg-primary text-white font-semibold`;

export default function Pagination({ page, totalPages, onChange }: Props) {
  if (totalPages <= 1) return null;

  const group = Math.ceil(page / GROUP);
  const start = (group - 1) * GROUP + 1;
  const end = Math.min(group * GROUP, totalPages);
  const pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  const prevGroup = Math.max(1, start - GROUP);
  const nextGroup = Math.min(totalPages, end + 1);

  return (
    <div className="flex justify-center gap-1.5 mt-6">
      <button className={inactiveBtn} disabled={page === 1} onClick={() => onChange(1)}>«</button>
      <button className={inactiveBtn} disabled={start === 1} onClick={() => onChange(prevGroup)}>‹</button>
      {pages.map((p) => (
        <button key={p} className={page === p ? activeBtn : inactiveBtn} onClick={() => onChange(p)}>
          {p}
        </button>
      ))}
      <button className={inactiveBtn} disabled={end === totalPages} onClick={() => onChange(nextGroup)}>›</button>
      <button className={inactiveBtn} disabled={page === totalPages} onClick={() => onChange(totalPages)}>»</button>
    </div>
  );
}
