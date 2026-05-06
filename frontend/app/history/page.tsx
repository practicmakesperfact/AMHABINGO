'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface GameHistory {
  id: number;
  game_id: string;
  status: string;
  entry_fee: number;
  prize_pool: number;
  created_at: string;
  has_won: boolean;
}

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<GameHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        // Fetch user's game history
        const games = await api.listGames();
        setHistory(games);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load history:', error);
        setLoading(false);
      }
    };

    loadHistory();
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-white/80 hover:text-white"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span>Back</span>
        </button>
        <h1 className="text-white font-bold text-xl">Game History</h1>
        <div className="w-16"></div>
      </div>

      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-yellow-400 mx-auto"></div>
            <p className="text-white mt-4">Loading history...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎮</div>
            <p className="text-white/60">No games played yet</p>
            <button
              onClick={() => router.push('/')}
              className="mt-6 bg-gradient-to-r from-purple-500 to-blue-500 text-white px-6 py-3 rounded-xl"
            >
              Play Your First Game
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((game) => (
              <div
                key={game.id}
                className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-semibold">
                    Game #{game.game_id.slice(-8)}
                  </span>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      game.status === 'finished'
                        ? 'bg-gray-500/30 text-gray-300'
                        : game.status === 'active'
                        ? 'bg-green-500/30 text-green-300'
                        : 'bg-yellow-500/30 text-yellow-300'
                    }`}
                  >
                    {game.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-white/60">Entry Fee:</span>
                    <span className="text-white ml-2">{game.entry_fee} ETB</span>
                  </div>
                  <div>
                    <span className="text-white/60">Prize Pool:</span>
                    <span className="text-white ml-2">{game.prize_pool} ETB</span>
                  </div>
                </div>
                {game.has_won && (
                  <div className="mt-2 bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-2 text-center">
                    <span className="text-yellow-400 font-bold">🏆 Winner!</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-white/10">
        <div className="grid grid-cols-4 gap-1 p-2">
          <button
            onClick={() => router.push('/')}
            className="flex flex-col items-center gap-1 py-3 text-white/60 hover:text-white"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 3.5L2 9.5v8h5v-5h6v5h5v-8l-8-6z"/>
            </svg>
            <span className="text-xs">Game</span>
          </button>
          
          <button
            onClick={() => router.push('/history')}
            className="flex flex-col items-center gap-1 py-3 text-blue-400"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9V7h2v6z"/>
            </svg>
            <span className="text-xs">History</span>
          </button>
          
          <button
            onClick={() => router.push('/wallet')}
            className="flex flex-col items-center gap-1 py-3 text-white/60 hover:text-white"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4z"/>
            </svg>
            <span className="text-xs">Wallet</span>
          </button>
          
          <button
            onClick={() => router.push('/profile')}
            className="flex flex-col items-center gap-1 py-3 text-white/60 hover:text-white"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2a4 4 0 100 8 4 4 0 000-8zm0 10c-4.42 0-8 1.79-8 4v2h16v-2c0-2.21-3.58-4-8-4z"/>
            </svg>
            <span className="text-xs">Profile</span>
          </button>
        </div>
      </div>
    </main>
  );
}
