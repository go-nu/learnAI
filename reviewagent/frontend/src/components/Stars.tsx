import React from 'react';

export default function Stars({ rating }: { rating: number }) {
  return (
    <span className="stars">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n > rating ? 'off' : ''}>★</span>
      ))}
    </span>
  );
}
