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

interface TxItem {
  id: number; amount: number; type: string;
  status: string; tx_ref: string; created_at: string;
}

const TX_LABELS: Record<string, string> = {
  entry_fee: 'Game Entry',
  payout:    'Prize Won 🏆',
  deposit:   'Deposit',
  withdrawal:'Withdrawal',
};
const TX_ICONS: Record<string, string> = {
  entry_fee: '🎮', payout: '🏆', deposit: '💰', withdrawal: '🏧',
};

export default function WalletPage() {
  const router = useRouter();
  const [user,   setUser]   = useState<any>(null);
  const [txList, setTxList] = useState<TxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab,    setTab]    = useState<'main' | 'play'>('main');

  useEffect(() => {
    (async () => {
      try {
        const tg       = (window as any).Telegram?.WebApp;
        const initData = tg?.initData || '';
        const [u, txs] = await Promise.all([
          api.authenticateUser(initData || undefined),
          api.getTransactions(initData || undefined).catch(() => []),
        ]);
        setUser(u);
        setTxList(txs as TxItem[]);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  const mainBal  = (user?.balance      ?? 0).toFixed(2);
  const playBal  = (user?.play_balance ?? 0).toFixed(2);

  return (
    <main className="min-h-screen pb-24" style={{ background: 'linear-gradient(160deg,#2d0b5a 0%,#0f0b1e 45%,#0d1b3e 100%)' }}>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-white/70 hover:text-white text-sm">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/>
          </svg>Back
        </button>
        <h1 className="text-white font-bold text-lg">Wallet</h1>
        <div className="w-12"/>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin"/>
        </div>
      ) : (
        <div className="px-4 pt-4 space-y-4">

          {/* Wallet tab switcher */}
          <div className="flex gap-2 bg-white/5 rounded-xl p-1">
            {(['main','play'] as const).map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${tab === t ? 'bg-purple-600 text-white' : 'text-white/50 hover:text-white'}`}>
                {t === 'main' ? 'Main Wallet' : 'Play Wallet'}
              </button>
            ))}
          </div>

          {/* Balance card */}
          <div className={`rounded-2xl p-6 border shadow-xl ${
            tab === 'main'
              ? 'bg-gradient-to-br from-purple-700 to-indigo-800 border-purple-500/30'
              : 'bg-gradient-to-br from-green-700 to-emerald-800 border-green-500/30'
          }`}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl ${tab === 'main' ? 'bg-purple-500/30' : 'bg-green-500/30'}`}>
                {tab === 'main' ? '🏦' : '🎮'}
              </div>
              <div>
                <p className="text-white/70 text-sm">{tab === 'main' ? 'Main Wallet' : 'Play Wallet'}</p>
                <p className="text-white font-black text-3xl">{tab === 'main' ? mainBal : playBal} <span className="text-lg font-medium">ETB</span></p>
              </div>
            </div>

            {tab === 'main' ? (
              <div className="grid grid-cols-2 gap-3">
                <button className="bg-white/20 hover:bg-white/30 text-white py-3 rounded-xl font-semibold text-sm transition-all active:scale-95"
                  onClick={() => alert('Bot ላይ Deposit 💰 ይጫኑ')}>
                  💰 Deposit
                </button>
                <button className="bg-white/20 hover:bg-white/30 text-white py-3 rounded-xl font-semibold text-sm transition-all active:scale-95"
                  onClick={() => alert('Bot ላይ Withdraw 🤑 ይጫኑ')}>
                  🤑 Withdraw
                </button>
              </div>
            ) : (
              <div className="bg-green-900/30 rounded-xl p-3 text-center">
                <p className="text-green-200 text-xs">🎁 Play balance ለጨዋታ ብቻ ነው። ለ deposit ወደ Main Wallet ይቀልዑ።</p>
              </div>
            )}
          </div>

          {/* Transactions */}
          <div>
            <p className="text-white/50 text-xs uppercase tracking-widest mb-3">Recent Transactions</p>
            {txList.length === 0 ? (
              <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
                <p className="text-4xl mb-3">💳</p>
                <p className="text-white/60 text-sm">No transactions yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {txList.slice(0, 20).map((tx) => {
                  const isCredit = tx.type === 'payout' || tx.type === 'deposit';
                  return (
                    <div key={tx.id} className="bg-white/5 border border-white/10 rounded-xl p-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-9 h-9 rounded-full flex items-center justify-center text-lg ${isCredit ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                          {TX_ICONS[tx.type] || '💲'}
                        </div>
                        <div>
                          <p className="text-white font-semibold text-sm">{TX_LABELS[tx.type] || tx.type}</p>
                          <p className="text-white/40 text-xs">
                            {tx.created_at ? new Date(tx.created_at).toLocaleDateString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}) : ''}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-bold text-sm ${isCredit ? 'text-green-400' : 'text-red-400'}`}>
                          {isCredit ? '+' : '-'}{Math.abs(tx.amount).toFixed(2)} ETB
                        </p>
                        <p className={`text-xs ${tx.status === 'success' ? 'text-green-400' : tx.status === 'pending' ? 'text-yellow-400' : 'text-red-400'}`}>
                          {tx.status}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="text-center text-white/20 text-xs py-2">@amhabingo_bot</div>
        </div>
      )}

      <BottomNav active="/wallet"/>
    </main>
  );
}
