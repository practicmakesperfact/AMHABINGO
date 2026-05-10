'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

/* ── shared nav ───────────────────────────────────────────────── */
function BottomNav({ active }: { active: string }) {
  const router = useRouter();
  const items = [
    { label: 'Game',    icon: 'M10 3.5L2 9.5v8h5v-5h6v5h5v-8l-8-6z',               path: '/' },
    { label: 'History', icon: 'M10 2a8 8 0 100 16A8 8 0 0010 2zm1 11H9V7h2v6z',     path: '/history' },
    { label: 'Wallet',  icon: 'M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4z', path: '/wallet' },
    { label: 'Profile', icon: 'M10 2a4 4 0 100 8 4 4 0 000-8zm0 10c-4.42 0-8 1.79-8 4v2h16v-2c0-2.21-3.58-4-8-4z', path: '/profile' },
  ];
  return (
    <nav className="bottom-nav">
      {items.map(({ label, icon, path }) => (
        <button key={label} onClick={() => router.push(path)}
          className={`nav-btn ${path === active ? 'active' : ''}`}>
          <svg fill="currentColor" viewBox="0 0 20 20"><path d={icon}/></svg>
          {label}
        </button>
      ))}
    </nav>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser]     = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const tg       = (window as any).Telegram?.WebApp;
        const initData = tg?.initData || '';
        // Reuse cached user from sessionStorage for speed
        const cached = sessionStorage.getItem('user');
        if (cached) { setUser(JSON.parse(cached)); }
        // Always refresh from server to get latest balances
        const fresh = await api.authenticateUser(initData || undefined);
        setUser(fresh);
        sessionStorage.setItem('user', JSON.stringify(fresh));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const initials   = (user?.first_name?.[0] || user?.username?.[0] || 'A').toUpperCase();
  const displayName = user?.first_name || user?.username || 'Player';
  const winRate     = user?.games_played
    ? ((user.wins / user.games_played) * 100).toFixed(0)
    : '0';

  return (
    <main className="min-h-screen pb-24" style={{ background: 'linear-gradient(160deg, #2d0b5a 0%, #0f0b1e 45%, #0d1b3e 100%)' }}>

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <button onClick={() => router.back()}
          className="flex items-center gap-1.5 text-white/70 hover:text-white text-sm">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/>
          </svg>
          Back
        </button>
        <h1 className="text-white font-bold text-lg">Profile</h1>
        <div className="w-12"/>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin"/>
        </div>
      ) : (
        <div className="px-4 pt-6 space-y-5">

          {/* ── Avatar + name ── */}
          <div className="flex flex-col items-center gap-3 py-4">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center text-3xl font-black text-white shadow-lg shadow-purple-900/50">
              {initials}
            </div>
            <div className="text-center">
              <p className="text-white font-black text-xl">{displayName}</p>
              {user?.username && <p className="text-white/50 text-sm">@{user.username}</p>}
              {user?.phone_number
                ? <p className="text-green-400 text-xs mt-1">✅ {user.phone_number}</p>
                : (
                  <div className="mt-2 bg-yellow-500/20 border border-yellow-500/40 rounded-lg px-3 py-1.5 text-center">
                    <p className="text-yellow-400 text-xs font-semibold">
                      📋 Register via bot to get 10 ETB bonus!
                    </p>
                  </div>
                )
              }
            </div>
          </div>

          {/* ── Wallet cards ── */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/5 rounded-2xl p-4 border border-white/10 text-center">
              <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4z"/>
                </svg>
              </div>
              <p className="text-white/50 text-xs mb-1">Main Wallet</p>
              <p className="text-white font-black text-xl">{(user?.balance ?? 0).toFixed(2)}</p>
              <p className="text-white/40 text-xs">ETB</p>
            </div>
            <div className="bg-white/5 rounded-2xl p-4 border border-green-500/20 text-center">
              <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"/>
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd"/>
                </svg>
              </div>
              <p className="text-white/50 text-xs mb-1">Play Wallet</p>
              <p className="text-green-400 font-black text-xl">{(user?.play_balance ?? 0).toFixed(2)}</p>
              <p className="text-white/40 text-xs">ETB</p>
            </div>
          </div>

          {/* ── Stats ── */}
          <div className="bg-white/5 rounded-2xl p-4 border border-white/10">
            <p className="text-white/50 text-xs uppercase tracking-widest mb-3">Statistics</p>
            <div className="grid grid-cols-3 gap-3 text-center">
              {[
                { label: 'Games',    value: user?.games_played ?? 0, color: 'text-white' },
                { label: 'Wins',     value: user?.wins ?? 0,          color: 'text-yellow-400' },
                { label: 'Win Rate', value: `${winRate}%`,             color: 'text-green-400' },
              ].map(({ label, value, color }) => (
                <div key={label}>
                  <p className={`text-2xl font-black ${color}`}>{value}</p>
                  <p className="text-white/50 text-xs mt-0.5">{label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ── Menu items ── */}
          <div className="space-y-2">
            {[
              { label: 'Game History',  icon: '🕐', path: '/history', color: 'bg-blue-500/20' },
              { label: 'Wallet',        icon: '💰', path: '/wallet',  color: 'bg-green-500/20' },
              { label: 'Game Rules',    icon: '📖', path: '/rules',   color: 'bg-purple-500/20' },
            ].map(({ label, icon, path, color }) => (
              <button key={label} onClick={() => router.push(path)}
                className="w-full bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl p-4 flex items-center justify-between transition-all">
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 ${color} rounded-lg flex items-center justify-center text-lg`}>{icon}</div>
                  <span className="text-white font-semibold text-sm">{label}</span>
                </div>
                <svg className="w-4 h-4 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/>
                </svg>
              </button>
            ))}
          </div>

          <div className="text-center text-white/20 text-xs py-2">@amhabingo_bot</div>
        </div>
      )}

      <BottomNav active="/profile"/>
    </main>
  );
}
