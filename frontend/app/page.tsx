'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    activePlayers: 45000,
    gamesPlayed: 60000,
    winnersDaily: 500,
  });

  useEffect(() => {
    const initUser = async () => {
      try {
        // Authenticate with backend
        const userData = await api.authenticateUser();
        console.log('✅ User authenticated:', userData);
        
        // Fetch platform stats (if endpoint exists)
        try {
          const statsData = await api.getPlatformStats();
          setStats(statsData);
        } catch (e) {
          console.log('Using default stats');
        }
        
        setLoading(false);
      } catch (error) {
        console.error('❌ Failed to authenticate:', error);
        setLoading(false);
      }
    };

    setTimeout(initUser, 100);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400 mx-auto"></div>
          <p className="text-white mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
            <span className="text-purple-900 font-bold text-xl">A</span>
          </div>
          <span className="text-white font-bold text-xl">AMHABINGO</span>
        </div>
        <button 
          onClick={() => router.push('/rules')}
          className="text-white/80 hover:text-white px-4 py-2 rounded-lg border border-white/20"
        >
          Rules
        </button>
      </div>

      {/* Welcome Section */}
      <div className="text-center py-12 px-4">
        <h1 className="text-4xl font-bold text-white mb-2">
          Welcome to <span className="text-yellow-400">AMHABINGO</span>
        </h1>
      </div>

      {/* Stake Selection */}
      <div className="px-4 mb-8">
        <div className="max-w-2xl mx-auto bg-white/5 backdrop-blur-sm rounded-3xl p-6 border-2 border-yellow-500/50">
          <div className="flex items-center gap-2 mb-6">
            <div className="text-yellow-400 text-xl">▶</div>
            <h2 className="text-white text-xl font-semibold">Choose Your Stake</h2>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => router.push('/cards?stake=10')}
              className="bg-gradient-to-r from-green-500 to-green-600 text-white font-bold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95 flex items-center justify-center gap-2"
            >
              <span className="text-2xl">▶</span>
              <span className="text-xl">Play 10</span>
            </button>
            
            <button
              onClick={() => router.push('/cards?stake=20')}
              className="bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95 flex items-center justify-center gap-2"
            >
              <span className="text-2xl">▶</span>
              <span className="text-xl">Play 20</span>
            </button>

            <button
              onClick={() => router.push('/cards?stake=50')}
              className="bg-gradient-to-r from-purple-500 to-purple-600 text-white font-bold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95 flex items-center justify-center gap-2"
            >
              <span className="text-2xl">▶</span>
              <span className="text-xl">Play 50</span>
            </button>

            <button
              onClick={() => router.push('/cards?stake=100')}
              className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white font-bold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95 flex items-center justify-center gap-2"
            >
              <span className="text-2xl">▶</span>
              <span className="text-xl">Play 100</span>
            </button>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="px-4 mb-20">
        <div className="max-w-2xl mx-auto bg-white/5 backdrop-blur-sm rounded-3xl p-6">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-3xl font-bold text-white mb-1">
                {stats.activePlayers.toLocaleString()}+
              </div>
              <div className="text-white/60 text-sm">Active Players</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white mb-1">
                {stats.gamesPlayed.toLocaleString()}+
              </div>
              <div className="text-white/60 text-sm">Games Played</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white mb-1">
                {stats.winnersDaily.toLocaleString()}+
              </div>
              <div className="text-white/60 text-sm">Winners Daily</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-white/10">
        <div className="grid grid-cols-4 gap-1 p-2">
          <button
            onClick={() => router.push('/')}
            className="flex flex-col items-center gap-1 py-3 text-blue-400"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 3.5L2 9.5v8h5v-5h6v5h5v-8l-8-6z"/>
            </svg>
            <span className="text-xs">Game</span>
          </button>
          
          <button
            onClick={() => router.push('/history')}
            className="flex flex-col items-center gap-1 py-3 text-white/60 hover:text-white"
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
