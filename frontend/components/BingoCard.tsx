'use client';

import { useMemo } from 'react';

interface BingoCardProps {
  card: number[][];
  markedNumbers: number[];
  currentNumber: number | null;
  onCellClick?: (row: number, col: number) => void;
}

export default function BingoCard({ 
  card, 
  markedNumbers, 
  currentNumber,
  onCellClick 
}: BingoCardProps) {
  // Convert flat indices to 2D coordinates
  const markedCoords = useMemo(() => {
    const coords = new Set<string>();
    markedNumbers.forEach(idx => {
      const row = Math.floor(idx / 5);
      const col = idx % 5;
      coords.add(`${row}-${col}`);
    });
    // Center is always marked (FREE)
    coords.add('2-2');
    return coords;
  }, [markedNumbers]);

  const getCellColor = (row: number, col: number, value: number) => {
    const isMarked = markedCoords.has(`${row}-${col}`);
    const isCurrent = value === currentNumber;
    const isFree = row === 2 && col === 2;

    if (isFree) return 'bg-yellow-400 text-gray-900';
    if (isCurrent) return 'bg-green-500 text-white animate-pulse';
    if (isMarked) return 'bg-red-500 text-white';
    return 'bg-white/10 text-white hover:bg-white/20';
  };

  const headers = ['B', 'I', 'N', 'G', 'O'];

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Header */}
      <div className="grid grid-cols-5 gap-1 mb-2">
        {headers.map((letter, idx) => (
          <div
            key={letter}
            className={`
              text-center font-bold text-2xl py-2 rounded-lg
              ${idx === 0 ? 'bg-indigo-600' : ''}
              ${idx === 1 ? 'bg-cyan-600' : ''}
              ${idx === 2 ? 'bg-green-600' : ''}
              ${idx === 3 ? 'bg-amber-600' : ''}
              ${idx === 4 ? 'bg-red-600' : ''}
            `}
          >
            {letter}
          </div>
        ))}
      </div>

      {/* Card Grid */}
      <div className="grid grid-cols-5 gap-1">
        {card.map((row, rowIdx) =>
          row.map((value, colIdx) => {
            const isFree = rowIdx === 2 && colIdx === 2;
            return (
              <button
                key={`${rowIdx}-${colIdx}`}
                onClick={() => onCellClick?.(rowIdx, colIdx)}
                className={`
                  aspect-square rounded-lg font-bold text-lg
                  transition-all duration-200
                  ${getCellColor(rowIdx, colIdx, value)}
                  ${onCellClick ? 'cursor-pointer' : 'cursor-default'}
                `}
              >
                {isFree ? 'FREE' : value}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
