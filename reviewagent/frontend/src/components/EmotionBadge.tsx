import React from 'react';

const MAP: Record<string, { cls: string; label: string }> = {
  good:   { cls: 'b-pos', label: '긍정' },
  normal: { cls: 'b-neu', label: '중립' },
  bad:    { cls: 'b-neg', label: '부정' },
};

export default function EmotionBadge({ emotion }: { emotion: string | null }) {
  if (!emotion) return <span className="badge b-neu">미분류</span>;
  const { cls, label } = MAP[emotion] ?? { cls: 'b-neu', label: emotion };
  return <span className={`badge ${cls}`}>{label}</span>;
}
