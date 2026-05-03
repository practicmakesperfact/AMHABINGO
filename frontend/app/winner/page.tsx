'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useGameStore } from '@/store/gameStore';
import { useTelegram } from '@/hooks/useTelegram';

export default function WinnerPage() {
  const router = useRouter();
  const { currentGame, currentPlayer, user } = useGameStore();
  const { hapticFeedback } = useTelegram();

  useEffect(() => {
    if (!currentGame || !currentPlayer) {
      router.push('/');
      return;
    }

    if (currentPlayer.has_won) {
      hapticFeedback('success');
    }
  }, [currentGame, currentPlayer, router, hapticFeedback]);

  const handleBackHome = () => {
    router.push('/');
  };

  if (!currentGame || !currentPlayer) {
    return null;
  }

  const isWinner = currentPlayer.has_won;
  const prizePerWinner = currentGame.winner_ids.length > 0
    ? currentGame.prize_pool / currentGame.winner_ids.length
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {isWinner ? (
          // Winner View
          <div className="text-center">
            <div className="text-8xl mb-6 animate-bounce">🎉</div>
            <h1 className="text-5xl font-bold text-yellow-400 mb-4">
              BINGO!
            </h1>
            <p className="text-2xl mb-8">Congratulations, you won!</p>

            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 mb-8">
              <div className="text-sm text-gray-400 mb-2">Your Prize</div>
              <div className="text-5xl font-bold text-green-400 mb-4">
                {prizePerWinner.toFixed(2)} ETB
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-400">Card Number</div>
                  <div className="font-bold">#{currentPlayer.card_number}</div>
                </div>
                <div>
                  <div className="text-gray-400">Pattern</div>
                  <div className="font-bold capitalize">
                    {currentPlayer.winning_pattern?.replace('_', ' ')}
                  </div>
                </div>
                <div>
                  <div className="text-gray-400">Game ID</div>
                  <div className="font-bold text-xs">{currentGame.game_id}</div>
                </div>
                <div>
                  <div className="text-gray-400">Total Winners</div>
                  <div className="font-bold">{currentGame.winner_ids.length}</div>
                </div>
              </div>
            </div>

            <button
              onClick={handleBackHome}
              className="w-full bg-gradient-to-r from-yellow-400 to-yellow-600 text-gray-900 font-bold py-4 rounded-2xl hover:scale-105 transition-transform"
            >
              Play Again
            </button>
          </div>
        ) : (
          // Non-Winner View
          <div className="text-center">
            <div className="text-6xl mb-6">😔</div>
            <h1 className="text-3xl font-bold mb-4">Better Luck Next Time!</h1>
            <p className="text-gray-400 mb-8">
              The game has ended. Keep playing to win!
            </p>

            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 mb-8">
              <div className="text-sm text-gray-400 mb-2">Game Stats</div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-400">Your Card</div>
                  <div className="font-bold">#{currentPlayer.card_number}</div>
                </div>
                <div>
                  <div className="text-gray-400">Numbers Marked</div>
                  <div className="font-bold">{currentPlayer.marked_numbers.length}</div>
                </div>
                <div>
                  <div className="text-gray-400">Winners</div>
                  <div className="font-bold">{currentGame.winner_ids.length}</div>
                </div>
                <div>
                  <div className="text-gray-400">Prize Pool</div>
                  <div className="font-bold">{currentGame.prize_pool.toFixed(2)} ETB</div>
                </div>
              </div>
            </div>

            <button
              onClick={handleBackHome}
              className="w-full bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-4 rounded-2xl hover:scale-105 transition-transform"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
