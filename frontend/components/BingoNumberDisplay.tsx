'use client';

import { useEffect, useState } from 'react';

interface BingoNumberDisplayProps {
  currentNumber: number | null;
  calledNumbers: number[];
  isMuted?: boolean;
  onMuteToggle?: () => void;
}

// Convert number to Bingo label (B:1-15, I:16-30, N:31-45, G:46-60, O:61-75)
export const getBingoLabel = (number: number): { letter: string; num: number; color: string } => {
  if (number >= 1 && number <= 15) {
    return { letter: 'B', num: number, color: 'blue' };
  } else if (number >= 16 && number <= 30) {
    return { letter: 'I', num: number, color: 'indigo' };
  } else if (number >= 31 && number <= 45) {
    return { letter: 'N', num: number, color: 'purple' };
  } else if (number >= 46 && number <= 60) {
    return { letter: 'G', num: number, color: 'green' };
  } else if (number >= 61 && number <= 75) {
    return { letter: 'O', num: number, color: 'orange' };
  }
  return { letter: '', num: number, color: 'gray' };
};

// Get Tailwind color classes based on letter
const getColorClasses = (color: string) => {
  const colors: Record<string, { bg: string; text: string; glow: string }> = {
    blue: {
      bg: 'bg-blue-500',
      text: 'text-blue-500',
      glow: 'shadow-blue-500/50',
    },
    indigo: {
      bg: 'bg-indigo-500',
      text: 'text-indigo-500',
      glow: 'shadow-indigo-500/50',
    },
    purple: {
      bg: 'bg-purple-500',
      text: 'text-purple-500',
      glow: 'shadow-purple-500/50',
    },
    green: {
      bg: 'bg-green-500',
      text: 'text-green-500',
      glow: 'shadow-green-500/50',
    },
    orange: {
      bg: 'bg-orange-500',
      text: 'text-orange-500',
      glow: 'shadow-orange-500/50',
    },
  };
  return colors[color] || colors.blue;
};

export default function BingoNumberDisplay({
  currentNumber,
  calledNumbers,
  isMuted = false,
  onMuteToggle,
}: BingoNumberDisplayProps) {
  const [isAnimating, setIsAnimating] = useState(false);

  // Trigger animation when current number changes
  useEffect(() => {
    if (currentNumber) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 500);
      return () => clearTimeout(timer);
    }
  }, [currentNumber]);

  // Get last 10 called numbers (excluding current)
  const historyNumbers = calledNumbers
    .filter((num) => num !== currentNumber)
    .slice(-10)
    .reverse();

  const currentLabel = currentNumber ? getBingoLabel(currentNumber) : null;
  const currentColors = currentLabel ? getColorClasses(currentLabel.color) : null;

  return (
    <div className="w-full space-y-4">
      {/* History Row - Last 10 Numbers (Orange/Red for previous) */}
      <div className="bg-purple-800/60 backdrop-blur-sm rounded-2xl p-4 border border-purple-600/30">
        <div className="flex items-center gap-3 overflow-x-auto scrollbar-hide">
          {historyNumbers.length > 0 ? (
            historyNumbers.map((num, idx) => {
              const label = getBingoLabel(num);
              return (
                <div
                  key={`${num}-${idx}`}
                  className="bg-orange-500 rounded-full px-4 py-2 flex-shrink-0 shadow-lg transform transition-all duration-300 hover:scale-110"
                  style={{
                    animation: `slideIn 0.3s ease-out ${idx * 0.05}s both`,
                  }}
                >
                  <span className="text-white font-bold text-sm whitespace-nowrap">
                    {label.letter}-{label.num}
                  </span>
                </div>
              );
            })
          ) : (
            <div className="text-white/40 text-sm">Waiting for numbers...</div>
          )}

          {/* Mute Button */}
          {onMuteToggle && (
            <button
              onClick={onMuteToggle}
              className="ml-auto text-white/80 hover:text-white transition-colors flex-shrink-0"
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? (
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12.293 7.293a1 1 0 011.414 0L15 8.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Current Number - Large Circle with Letter Color */}
      {currentNumber && currentLabel && currentColors ? (
        <div className="flex items-center justify-center py-8">
          <div
            className={`
              relative w-48 h-48 sm:w-56 sm:h-56 md:w-64 md:h-64
              rounded-full 
              bg-gradient-to-br from-yellow-400 via-orange-400 to-orange-500
              flex items-center justify-center
              shadow-2xl ${currentColors.glow}
              transform transition-all duration-500
              ${isAnimating ? 'scale-110 rotate-12' : 'scale-100 rotate-0'}
            `}
            style={{
              animation: isAnimating ? 'pulse 0.5s ease-in-out' : 'none',
            }}
          >
            {/* Glow effect */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-yellow-300/50 to-orange-500/50 blur-xl animate-pulse" />
            
            {/* Number display with letter color */}
            <div className="relative z-10 text-center">
              <div className={`${currentColors.text} font-black text-6xl sm:text-7xl md:text-8xl drop-shadow-2xl`}>
                {currentLabel.letter}
              </div>
              <div className={`${currentColors.text} font-black text-5xl sm:text-6xl md:text-7xl drop-shadow-2xl -mt-2`}>
                {currentLabel.num}
              </div>
            </div>

            {/* Rotating ring */}
            <div
              className="absolute inset-0 rounded-full border-4 border-white/30"
              style={{
                animation: isAnimating ? 'spin 1s linear' : 'none',
              }}
            />
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="text-6xl mb-4">🎮</div>
            <h2 className="text-white text-2xl font-bold mb-2">Waiting for Game</h2>
            <p className="text-white/60">Numbers will appear here</p>
          </div>
        </div>
      )}

      {/* Custom animations */}
      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes pulse {
          0%, 100% {
            transform: scale(1) rotate(0deg);
          }
          50% {
            transform: scale(1.1) rotate(12deg);
          }
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }

        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
