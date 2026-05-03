'use client';

import { useEffect } from 'react';
import { useTelegram } from '@/hooks/useTelegram';

interface Winner {
  user_id: number;
  username: string;
  card_number: number;
  winning_pattern: string;
  prize: number;
}

interface WinnerModalProps {
  winners: Winner[];
  isOpen: boolean;
  onClose: () => void;
}

export default function WinnerModal({ winners, isOpen, onClose }: WinnerModalProps) {
  const { hapticFeedback } = useTelegram();

  useEffect(() => {
    if (isOpen && winners.length > 0) {
      hapticFeedback('success');
    }
  }, [isOpen, winners, hapticFeedback]);

  if (!isOpen) return null;

  const formatPattern = (pattern: string) => {
    if (pattern.startsWith('row_')) return `Row ${parseInt(pattern.split('_')[1]) + 1}`;
    if (pattern.startsWith('col_')) return `Column ${parseInt(pattern.split('_')[1]) + 1}`;
    if (pattern === 'diagonal_lr') return 'Diagonal ↘';
    if (pattern === 'diagonal_rl') return 'Diagonal ↙';
    return pattern;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-gradient-to-br from-purple-900 to-blue-900 rounded-3xl p-8 max-w-md w-full shadow-2xl">
        {/* Confetti Animation */}
        <div className="text-center mb-6">
          <div className="text-6xl mb-4 animate-bounce">🎉</div>
          <h2 className="text-3xl font-bold text-yellow-400 mb-2">
            {winners.length === 1 ? 'WINNER!' : 'WINNERS!'}
          </h2>
          <p className="text-white/80">
            {winners.length === 1 
              ? 'Congratulations to the winner!' 
              : `${winners.length} players won!`
            }
          </p>
        </div>

        {/* Winners List */}
        <div className="space-y-4 mb-6">
          {winners.map((winner, idx) => (
            <div
              key={idx}
              className="bg-white/10 backdrop-blur-sm rounded-2xl p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="text-white font-bold text-lg">
                    {winner.username || `Player ${winner.user_id}`}
                  </div>
                  <div className="text-gray-400 text-sm">
                    Card #{winner.card_number}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-yellow-400 font-bold text-xl">
                    {winner.prize.toFixed(2)} ETB
                  </div>
                  <div className="text-gray-400 text-sm">
                    {formatPattern(winner.winning_pattern)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="w-full bg-gradient-to-r from-yellow-400 to-yellow-600 text-gray-900 font-bold py-4 rounded-2xl hover:scale-105 transition-transform"
        >
          Back to Home
        </button>
      </div>
    </div>
  );
}
