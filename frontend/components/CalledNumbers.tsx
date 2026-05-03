'use client';

import { useMemo } from 'react';

interface CalledNumbersProps {
  calledNumbers: number[];
  currentNumber: number | null;
}

export default function CalledNumbers({ calledNumbers, currentNumber }: CalledNumbersProps) {
  // Group numbers by category
  const groupedNumbers = useMemo(() => {
    const groups = {
      B: [] as number[],
      I: [] as number[],
      N: [] as number[],
      G: [] as number[],
      O: [] as number[],
    };

    calledNumbers.forEach(num => {
      if (num >= 1 && num <= 15) groups.B.push(num);
      else if (num >= 16 && num <= 30) groups.I.push(num);
      else if (num >= 31 && num <= 45) groups.N.push(num);
      else if (num >= 46 && num <= 60) groups.G.push(num);
      else if (num >= 61 && num <= 75) groups.O.push(num);
    });

    // Sort each group
    Object.keys(groups).forEach(key => {
      groups[key as keyof typeof groups].sort((a, b) => a - b);
    });

    return groups;
  }, [calledNumbers]);

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'B': return 'bg-indigo-600';
      case 'I': return 'bg-cyan-600';
      case 'N': return 'bg-green-600';
      case 'G': return 'bg-amber-600';
      case 'O': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="w-full space-y-2">
      {/* Current Number Display */}
      {currentNumber && (
        <div className="text-center mb-4">
          <div className="text-sm text-gray-400 mb-1">Current Number</div>
          <div className="inline-block bg-green-500 text-white text-5xl font-bold px-8 py-4 rounded-2xl animate-pulse">
            {currentNumber}
          </div>
        </div>
      )}

      {/* Called Numbers by Category */}
      <div className="space-y-2">
        {Object.entries(groupedNumbers).map(([category, numbers]) => (
          <div key={category} className="flex items-center gap-2">
            <div className={`${getCategoryColor(category)} text-white font-bold text-xl w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0`}>
              {category}
            </div>
            <div className="flex-1 flex flex-wrap gap-1">
              {numbers.length === 0 ? (
                <span className="text-gray-500 text-sm">No numbers called</span>
              ) : (
                numbers.map(num => (
                  <span
                    key={num}
                    className={`
                      px-2 py-1 rounded text-sm font-semibold
                      ${num === currentNumber 
                        ? 'bg-green-500 text-white' 
                        : 'bg-white/10 text-white'
                      }
                    `}
                  >
                    {num}
                  </span>
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Total Count */}
      <div className="text-center text-sm text-gray-400 mt-4">
        {calledNumbers.length} / 75 numbers called
      </div>
    </div>
  );
}
