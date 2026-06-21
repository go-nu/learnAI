import React from 'react';

const MAP: Record<string, { cls: string; label: string }> = {
  pending:    { cls: 'bg-yellow-100 text-yellow-700', label: '대기 중' },
  processing: { cls: 'bg-blue-100 text-blue-700',    label: '처리 중' },
  done:       { cls: 'bg-green-100 text-green-700',  label: '완료' },
};

export default function StatusBadge({ status }: { status: string }) {
  const { cls, label } = MAP[status] ?? { cls: 'bg-gray-100 text-gray-600', label: status };
  return (
    <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${cls}`}>
      {label}
    </span>
  );
}
