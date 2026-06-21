import React from 'react';

export default function Stars({ rating }: { rating: number }) {
  return (
    <span className="text-sm">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n <= rating ? 'text-yellow-400' : 'text-divider'}>★</span>
      ))}
    </span>
  );
}
