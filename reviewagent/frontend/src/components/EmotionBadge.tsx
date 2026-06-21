import React from 'react';

const MAP: Record<string, { dot: string; label: string }> = {
  good:   { dot: 'bg-success', label: '긍정' },
  normal: { dot: 'bg-ink2',    label: '중립' },
  bad:    { dot: 'bg-danger',  label: '부정' },
};

export default function EmotionBadge({ emotion }: { emotion: string | null }) {
  if (!emotion) {
    return (
      <span className="flex items-center gap-1.5 text-xs font-semibold">
        <span className="w-2 h-2 rounded-full inline-block bg-ink2" />
        미분류
      </span>
    );
  }
  const { dot, label } = MAP[emotion] ?? { dot: 'bg-ink2', label: emotion };
  return (
    <span className="flex items-center gap-1.5 text-xs font-semibold">
      <span className={`w-2 h-2 rounded-full inline-block ${dot}`} />
      {label}
    </span>
  );
}
