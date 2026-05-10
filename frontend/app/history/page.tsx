'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

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

interface GameRecord {
  game_id: string; status: string; entry_fee: number;
  prize_pool: number; total_players: number; card_number: number;
  has_won: boolean; winning_pattern: string | null; joined_at: string | null;
}

function statusBadge(s: string) {
  if (s === 'finished') return 'bg-gray-700/60 text-gray-300';
  if (s === 'active')   return 'bg-green-500/30 text-green-300';
  return 'bg-yellow-500/30 text-yellow-300';
}

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<GameRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');

  useEffect(() => {
    (async () => {
      try {
        const tg = (window as any).Telegram?.WebApp;
        const data = await api.getUserHistory(tg?.initData || undefined) as GameRecord[];
        setHistory(data);
      } catch (e: any) { setError(e.message); }
      finally { setLoading(false); }
    })();
  }, []);

  return (
    <main className="min-h-screen pb-24" style={{ background: 'linear-gradient(160deg,#2d0b5a 0%,#0f0b1e 45%,#0d1b3e 100%)' }}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-white/70 hover:text-white text-sm">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/>
          </svg>Back
        </button>
        <h1 className="text-white font-bold text-lg">Game History</h1>
        <div className="w-12"/>
      </div>

      <div className="px-4 pt-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-12 h-12 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin"/>
          </div>
        ) : error ? (
          <div className="bg-red-900/30 border border-red-500/40 rounded-2xl p-6 text-center mt-8">
            <p className="text-4xl mb-2">⚠️</p><p className="text-red-400 text-sm">{error}</p>
          </div>
        ) : history.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <div className="text-6xl mb-4">🎮</div>
            <p className="text-white font-bold text-lg mb-1">No games yet</p>
            <p className="text-white/50 text-sm mb-6">ጨዋታ ጀምረው ታሪክዎ ይታያል</p>
            <button onClick={() => router.push('/')} className="bg-purple-600 hover:bg-purple-700 text-white font-bold px-8 py-3 rounded-xl transition-all">Play Now 🎮</button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-white/40 text-xs uppercase tracking-widest mb-2">{history.length} games played</p>
            {history.map((g, i) => (
              <div key={i} className={`rounded-xl p-4 border ${g.has_won ? 'bg-yellow-500/10 border-yellow-500/30' : 'bg-white/5 border-white/10'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-bold text-sm">#{g.game_id.slice(-8).toUpperCase()}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${statusBadge(g.status)}`}>{g.status}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center mb-2">
                  {[{l:'Stake',v:`${g.entry_fee} ETB`},{l:'Players',v:g.total_players},{l:'Cartela',v:`#${g.card_number}`}].map(({l,v})=>(
                    <div key={l} className="bg-white/5 rounded-lg py-1.5">
                      <p className="text-white/40 text-[10px]">{l}</p>
                      <p className="text-white font-bold text-xs">{v}</p>
                    </div>
                  ))}
                </div>
                {g.has_won
                  ? <div className="bg-yellow-500/20 border border-yellow-500/40 rounded-lg px-3 py-1.5 flex items-center justify-between"><span className="text-yellow-400 font-bold text-sm">🏆 Winner!</span><span className="text-yellow-300 text-xs">{(g.prize_pool*0.8).toFixed(0)} ETB</span></div>
                  : <div className="bg-white/5 rounded-lg px-3 py-1.5 text-center"><span className="text-white/40 text-xs">No win this round</span></div>
                }
                {g.joined_at && <p className="text-white/25 text-[10px] mt-1.5 text-right">{new Date(g.joined_at).toLocaleDateString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
      <BottomNav active="/history"/>
    </main>
  );
}
