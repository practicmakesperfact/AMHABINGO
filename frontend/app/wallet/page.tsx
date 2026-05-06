'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface Transaction {
  id: number;
  amount: number;
  type: string;
  status: string;
  created_at: string;
  description: string;
}

export default function WalletPage() {
  const router = useRouter();
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadWallet = async () => {
      try {
        // Fetch user data
        const user = await api.getCurrentUser();
        setBalance(user.balance);

        // Fetch transactions
        const txs = await api.getTransactions();
        setTransactions(txs);
        
        setLoading(false);
      } catch (error) {
        console.error('Failed to load wallet:', error);
        setLoading(false);
      }
    };

    loadWallet();
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
        <h1 className="text-white font-bold text-xl">Wallet</h1>
        <div className="w-16"></div>
      </div>

      {/* Balance Card */}
      <div className="p-4">
        <div className="bg-gradient-to-br from-yellow-500 to-orange-500 rounded-3xl p-6 mb-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-white/80 text-sm">Available Balance</span>
            <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4z"/>
            </svg>
          </div>
          <div className="text-4xl font-bold text-white mb-6">
            {loading ? '...' : `${balance.toFixed(2)} ETB`}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <button className="bg-white/20 backdrop-blur-sm text-white py-3 rounded-xl font-semibold hover:bg-white/30 transition-all">
              Deposit
            </button>
            <button className="bg-white/20 backdrop-blur-sm text-white py-3 rounded-xl font-semibold hover:bg-white/30 transition-all">
              Withdraw
            </button>
          </div>
        </div>

        {/* Transactions */}
        <div className="mb-4">
          <h2 className="text-white font-semibold text-lg mb-3">Recent Transactions</h2>
          
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-yellow-400 mx-auto"></div>
            </div>
          ) : transactions.length === 0 ? (
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-8 text-center">
              <div className="text-4xl mb-3">💳</div>
              <p className="text-white/60">No transactions yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {transactions.map((tx) => (
                <div
                  key={tx.id}
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          tx.type === 'deposit'
                            ? 'bg-green-500/20'
                            : tx.type === 'withdrawal'
                            ? 'bg-red-500/20'
                            : 'bg-blue-500/20'
                        }`}
                      >
                        <span className="text-xl">
                          {tx.type === 'deposit' ? '↓' : tx.type === 'withdrawal' ? '↑' : '🎮'}
                        </span>
                      </div>
                      <div>
                        <p className="text-white font-semibold">{tx.description || tx.type}</p>
                        <p className="text-white/60 text-xs">
                          {new Date(tx.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p
                        className={`font-bold ${
                          tx.type === 'deposit' ? 'text-green-400' : 'text-red-400'
                        }`}
                      >
                        {tx.type === 'deposit' ? '+' : '-'}
                        {Math.abs(tx.amount).toFixed(2)} ETB
                      </p>
                      <p
                        className={`text-xs ${
                          tx.status === 'completed'
                            ? 'text-green-400'
                            : tx.status === 'pending'
                            ? 'text-yellow-400'
                            : 'text-red-400'
                        }`}
                      >
                        {tx.status}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
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
            className="flex flex-col items-center gap-1 py-3 text-blue-400"
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
