'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTelegram } from '@/hooks/useTelegram';
import { useGameStore } from '@/store/gameStore';
import { api } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const { user: tgUser, isAvailable, hapticFeedback } = useTelegram();
  const { user, setUser } = useGameStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initUser = async () => {
      try {
        if (!isAvailable) {
          console.warn('Telegram WebApp not available');
          setLoading(false);
          return;
        }

        // Authenticate user
        const userData = await api.authenticateUser();
        setUser(userData);
        setLoading(false);
      } catch (error) {
        console.error('Failed to authenticate:', error);
        setLoading(false);
      }
    };

    initUser();
  }, [isAvailable, setUser]);

  const handlePlayClick = () => {
    hapticFeedback('medium');
    router.push('/stake');
  };

  const handleBalanceClick = () => {
    hapticFeedback('light');
    // Show balance modal or navigate to balance page
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400 mx-auto"></div>
          <p className="text-white mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6">
      {/* Logo */}
      <div className="text-center mb-12">
        <h1 className="text-6xl font-bold text-yellow-400 mb-2">
          AMHABINGO
        </h1>
        <p className="text-white text-lg">Real-time Bingo Game</p>
      </div>

      {/* User Info */}
      {user && (
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 mb-8 w-full max-w-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-semibold">
                👋 {tgUser?.first_name || 'Player'}
              </p>
              <p className="text-gray-300 text-sm">
                @{tgUser?.username || 'anonymous'}
              </p>
            </div>
            <div className="text-right">
              <p className="text-yellow-400 font-bold text-xl">
                {user.balance.toFixed(2)} ETB
              </p>
              <p className="text-gray-300 text-sm">
                {user.wins} wins
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Menu Buttons */}
      <div className="grid grid-cols-2 gap-4 w-full max-w-md">
        <button
          onClick={handlePlayClick}
          className="bg-gradient-to-r from-green-500 to-green-600 text-white font-bold py-6 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95"
        >
          <div className="text-4xl mb-2">🎮</div>
          <div>Play</div>
        </button>

        <button
          onClick={handleBalanceClick}
          className="bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold py-6 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95"
        >
          <div className="text-4xl mb-2">💰</div>
          <div>Balance</div>
        </button>

        <button
          onClick={() => {
            hapticFeedback('light');
            // Navigate to leaderboard
          }}
          className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white font-bold py-6 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95"
        >
          <div className="text-4xl mb-2">🏆</div>
          <div>Leaderboard</div>
        </button>

        <button
          onClick={() => {
            hapticFeedback('light');
            // Navigate to history
          }}
          className="bg-gradient-to-r from-purple-500 to-purple-600 text-white font-bold py-6 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95"
        >
          <div className="text-4xl mb-2">📊</div>
          <div>History</div>
        </button>
      </div>

      {/* Stats */}
      <div className="mt-8 text-center text-white/60 text-sm">
        <p>Games Played: {user?.games_played || 0}</p>
      </div>
    </main>
  );
}
