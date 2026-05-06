'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  balance: number;
  wins: number;
  games_played: number;
}

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load profile:', error);
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400 mx-auto"></div>
          <p className="text-white mt-4">Loading profile...</p>
        </div>
      </div>
    );
  }

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
        <h1 className="text-white font-bold text-xl">Profile</h1>
        <div className="w-16"></div>
      </div>

      {/* Profile Content */}
      <div className="p-4">
        {/* Profile Card */}
        <div className="bg-white/10 backdrop-blur-sm rounded-3xl p-6 mb-6 border border-white/20">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-20 h-20 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center text-white text-3xl font-bold">
              {user?.first_name?.[0] || user?.username?.[0] || 'U'}
            </div>
            <div>
              <h2 className="text-white text-2xl font-bold">
                {user?.first_name || user?.username || 'Player'}
              </h2>
              <p className="text-white/60">@{user?.username || 'user'}</p>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white/5 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-white mb-1">{user?.games_played || 0}</div>
              <div className="text-white/60 text-xs">Games</div>
            </div>
            <div className="bg-white/5 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-yellow-400 mb-1">{user?.wins || 0}</div>
              <div className="text-white/60 text-xs">Wins</div>
            </div>
            <div className="bg-white/5 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-green-400 mb-1">
                {user?.games_played ? ((user.wins / user.games_played) * 100).toFixed(0) : 0}%
              </div>
              <div className="text-white/60 text-xs">Win Rate</div>
            </div>
          </div>

          {/* Balance */}
          <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 rounded-xl p-4 border border-green-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white/60 text-sm mb-1">Current Balance</p>
                <p className="text-white text-2xl font-bold">{user?.balance.toFixed(2)} ETB</p>
              </div>
              <button
                onClick={() => router.push('/wallet')}
                className="bg-white/20 text-white px-4 py-2 rounded-lg hover:bg-white/30 transition-all"
              >
                View Wallet
              </button>
            </div>
          </div>
        </div>

        {/* Menu Items */}
        <div className="space-y-3">
          <button
            onClick={() => router.push('/history')}
            className="w-full bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 flex items-center justify-between hover:bg-white/20 transition-all"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9V7h2v6z"/>
                </svg>
              </div>
              <span className="text-white font-semibold">Game History</span>
            </div>
            <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button
            onClick={() => router.push('/rules')}
            className="w-full bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 flex items-center justify-between hover:bg-white/20 transition-all"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
                </svg>
              </div>
              <span className="text-white font-semibold">Game Rules</span>
            </div>
            <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button className="w-full bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 flex items-center justify-between hover:bg-white/20 transition-all">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z"/>
                  <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z"/>
                </svg>
              </div>
              <span className="text-white font-semibold">Support</span>
            </div>
            <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
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
            className="flex flex-col items-center gap-1 py-3 text-blue-400"
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
