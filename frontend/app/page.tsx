'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({ activePlayers: 0, gamesPlayed: 0, winnersDaily: 0 });

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        
        // Check cache first
        const cachedUser = sessionStorage.getItem('user');
        if (cachedUser) {
          const userData = JSON.parse(cachedUser);
          setUser(userData);
          setLoading(false);
          
          // Load stats in background (non-blocking)
          api.getPlatformStats().then(setStats).catch(() => {});
          
          // Check for active game and redirect if needed
          await checkActiveGame(userData);
          return;
        }

        // No cache, authenticate
        const tg = (window as any).Telegram?.WebApp;
        const initData = tg?.initData || '';
        const userData = await api.authenticateUser(initData || undefined);
        setUser(userData);
        sessionStorage.setItem('user', JSON.stringify(userData));

        // Load stats in parallel (non-blocking)
        api.getPlatformStats().then(setStats).catch(() => {});
        
        // Check for active game and redirect if needed
        await checkActiveGame(userData);
        
        setLoading(false);
      } catch (e: any) {
        setError(e.message || 'Cannot connect to backend');
        setLoading(false);
      }
    };
    init();
  }, []);

  // Check if user has an active game and redirect accordingly
  const checkActiveGame = async (userData: any) => {
    try {
      const currentGame = sessionStorage.getItem('currentGame');
      const myCard = sessionStorage.getItem('myCard');
      
      if (!currentGame) return;
      
      const gameData = JSON.parse(currentGame);
      const gameId = gameData.game_id;
      
      // Fetch latest game state
      const game = await api.getGame(gameId);
      
      // If game is WAITING or COUNTDOWN, redirect to card selection
      if (game.status === 'waiting' || game.status === 'countdown') {
        router.push(`/cards?stake=${game.entry_fee}`);
        return;
      }
      
      // If game is ACTIVE, redirect to game page
      if (game.status === 'active') {
        if (myCard) {
          // User joined - show their card
          router.push(`/game?game=${gameId}&card=${myCard}`);
        } else {
          // User didn't join - show watching mode
          router.push(`/game?game=${gameId}`);
        }
        return;
      }
      
      // If game is FINISHED, clear session and stay on home
      if (game.status === 'finished') {
        sessionStorage.removeItem('currentGame');
        sessionStorage.removeItem('myCard');
      }
    } catch (e) {
      // Game not found or error - clear session
      sessionStorage.removeItem('currentGame');
      sessionStorage.removeItem('myCard');
    }
  };

  const handleStake = (stake: number) => {
    // Clear old game data when starting new game
    sessionStorage.removeItem('currentGame');
    sessionStorage.removeItem('myCard');
    sessionStorage.removeItem('myUserId');
    // Immediate navigation without waiting
    router.push(`/cards?stake=${stake}`);
  };

  // Show UI immediately if we have cached user data
  if (loading && !user) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #1a0533 0%, #0f0b1e 50%, #0d1b3e 100%)' }}>
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin mx-auto" />
        <p className="text-white/60 mt-4 text-sm">Loading AMHABINGO…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: '#0f0b1e' }}>
      <div className="bg-red-900/30 border border-red-500/40 rounded-2xl p-6 max-w-sm w-full text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <h2 className="text-white font-bold text-lg mb-2">Backend Offline</h2>
        <p className="text-white/60 text-sm mb-4">{error}</p>
        <code className="block bg-black/40 rounded-lg p-3 text-green-400 text-xs text-left mb-4">
          cd backend<br />
          python -m uvicorn app.main:app --reload
        </code>
        <button onClick={() => window.location.reload()}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 rounded-xl transition-all">
          Retry
        </button>
      </div>
    </div>
  );

  const mainBalance = user?.balance?.toFixed(0) ?? '0';
  const playBalance = user?.play_balance?.toFixed(0) ?? '0';
  const coins = user?.coins ?? 0;
  const displayName = user?.first_name || user?.username || 'Player';

  return (
    <main className="min-h-screen pb-20" style={{ background: 'linear-gradient(135deg, #6B21A8 0%, #1E293B 50%, #0F172A 100%)' }}>

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center font-black text-xl text-purple-700">A</div>
          <span className="text-white font-bold text-xl tracking-wide">AMHABINGO</span>
        </div>
        <button onClick={() => router.push('/rules')}
          className="flex items-center gap-2 text-white/90 hover:text-white bg-white/10 backdrop-blur-sm rounded-lg px-4 py-2 text-sm transition-all border border-white/20">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          Rules
        </button>
      </div>

      {/* Welcome */}
      <div className="text-center pt-16 pb-12 px-4">
        <h1 className="text-4xl font-black text-white mb-2">
          Welcome to <span className="text-yellow-400">AMHABINGO</span>
        </h1>
      </div>

      {/* Stake Selection Box */}
      <div className="px-6 mb-12">
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-sm rounded-3xl p-6 border-2 border-yellow-600/40 shadow-2xl">
          <div className="flex items-center justify-center gap-2 mb-6">
            <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6.3 2.84A1.5 1.5 0 004 4.11V15.9a1.5 1.5 0 002.3 1.27l9.344-5.891a1.5 1.5 0 000-2.538L6.3 2.841z"/>
            </svg>
            <span className="text-white font-bold text-lg">Choose Your Stake</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <button onClick={() => handleStake(10)}
              className="bg-gradient-to-r from-emerald-500 to-green-600 text-white font-bold py-5 rounded-2xl flex items-center justify-center gap-2 text-xl hover:scale-105 active:scale-95 transition-transform shadow-xl">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.84A1.5 1.5 0 004 4.11V15.9a1.5 1.5 0 002.3 1.27l9.344-5.891a1.5 1.5 0 000-2.538L6.3 2.841z"/>
              </svg>
              Play 10
            </button>
            <button onClick={() => handleStake(20)}
              className="bg-gradient-to-r from-blue-500 to-blue-700 text-white font-bold py-5 rounded-2xl flex items-center justify-center gap-2 text-xl hover:scale-105 active:scale-95 transition-transform shadow-xl">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.84A1.5 1.5 0 004 4.11V15.9a1.5 1.5 0 002.3 1.27l9.344-5.891a1.5 1.5 0 000-2.538L6.3 2.841z"/>
              </svg>
              Play 20
            </button>
            <button onClick={() => handleStake(50)}
              className="bg-gradient-to-r from-purple-500 to-purple-700 text-white font-bold py-5 rounded-2xl flex items-center justify-center gap-2 text-xl hover:scale-105 active:scale-95 transition-transform shadow-xl">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.84A1.5 1.5 0 004 4.11V15.9a1.5 1.5 0 002.3 1.27l9.344-5.891a1.5 1.5 0 000-2.538L6.3 2.841z"/>
              </svg>
              Play 50
            </button>
            <button onClick={() => handleStake(100)}
              className="bg-gradient-to-r from-orange-500 to-orange-700 text-white font-bold py-5 rounded-2xl flex items-center justify-center gap-2 text-xl hover:scale-105 active:scale-95 transition-transform shadow-xl">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.84A1.5 1.5 0 004 4.11V15.9a1.5 1.5 0 002.3 1.27l9.344-5.891a1.5 1.5 0 000-2.538L6.3 2.841z"/>
              </svg>
              Play 100
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="px-6 mb-8">
        <div className="bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-sm rounded-3xl p-8 border border-white/10">
          <div className="grid grid-cols-3 gap-6 text-center">
            {[
              { label: 'Active Players', value: stats.activePlayers },
              { label: 'Games Played',   value: stats.gamesPlayed },
              { label: 'Winners Daily',  value: stats.winnersDaily },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="text-3xl font-black text-white mb-1">{value.toLocaleString()}+</div>
                <div className="text-white/60 text-xs">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-md border-t border-white/10 px-2 py-3 grid grid-cols-4 gap-1">
        {[
          { label: 'Game',    icon: 'M10 3.5L2 9.5v8h5v-5h6v5h5v-8l-8-6z',               path: '/' },
          { label: 'History', icon: 'M10 2a8 8 0 100 16A8 8 0 0010 2zm1 11H9V7h2v6z',     path: '/history' },
          { label: 'Wallet',  icon: 'M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4z', path: '/wallet' },
          { label: 'Profile', icon: 'M10 2a4 4 0 100 8 4 4 0 000-8zm0 10c-4.42 0-8 1.79-8 4v2h16v-2c0-2.21-3.58-4-8-4z', path: '/profile' },
        ].map(({ label, icon, path }) => (
          <button key={label} onClick={() => router.push(path)}
            className={`flex flex-col items-center gap-1 py-2 rounded-lg transition-all ${
              path === '/' 
                ? 'text-blue-400' 
                : 'text-white/50 hover:text-white/80'
            }`}>
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path d={icon}/></svg>
            <span className="text-xs font-medium">{label}</span>
          </button>
        ))}
      </nav>
    </main>
  );
}
