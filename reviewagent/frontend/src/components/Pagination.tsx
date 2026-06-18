import React from 'react';

interface Props {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}

const GROUP = 5;

export default function Pagination({ page, totalPages, onChange }: Props) {
  if (totalPages <= 1) return null;

  const group = Math.ceil(page / GROUP);
  const start = (group - 1) * GROUP + 1;
  const end = Math.min(group * GROUP, totalPages);
  const pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  const prevGroup = Math.max(1, start - GROUP);
  const nextGroup = Math.min(totalPages, end + 1);

  return (
    <div className="pager">
      <button className="pg" disabled={page === 1} onClick={() => onChange(1)}>«</button>
      <button className="pg" disabled={start === 1} onClick={() => onChange(prevGroup)}>‹</button>
      {pages.map((p) => (
        <button key={p} className={`pg${page === p ? ' on' : ''}`} onClick={() => onChange(p)}>{p}</button>
      ))}
      <button className="pg" disabled={end === totalPages} onClick={() => onChange(nextGroup)}>›</button>
      <button className="pg" disabled={page === totalPages} onClick={() => onChange(totalPages)}>»</button>
    </div>
  );
}
