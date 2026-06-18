import React from 'react';

const MAP: Record<string, { cls: string; label: string }> = {
  pending:    { cls: 'b-draft', label: '대기 중' },
  processing: { cls: 'b-draft', label: '처리 중' },
  done:       { cls: 'b-ok',    label: '완료' },
};

export default function StatusBadge({ status }: { status: string }) {
  const { cls, label } = MAP[status] ?? { cls: 'b-neu', label: status };
  return <span className={`badge ${cls}`}>{label}</span>;
}
