'use client';

import { useEffect, useState, useRef, Suspense, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { resetWsClient } from '@/lib/websocket';

/* ── helpers ─────────────────────────────────────────────────────────── */
function calcDerash(players: number, bet: number) {
  return Math.floor(players * bet * 0.8); // 20% house commission
}

/* ── Inner component (needs Suspense for useSearchParams) ─────────────── */
function CardsInner() {
  const router = useRouter();
  const params = useSearchParams();
  const stake = Number(params.get('stake') || '10');

  const [user, setUser]         = useState<any>(null);
  const [game, setGame]         = useState<any>(null);
  const [taken, setTaken]       = useState<Record<number, number>>({});
  const [selected, setSelected] = useState<number | null>(null);
  const [timer, setTimer]       = useState<number>(60);
  const [loading, setLoading]   = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<ReturnType<typeof resetWsClient> | null>(null);

  /* ── Auto-join function (defined early so it can be used in useEffects) ── */
  const autoJoin = useCallback(async (gameId: string, u: any) => {
    console.log('Auto-joining game:', gameId);
    let card = selected;
    if (!card) {
      const avail = Array.from({ length: 600 }, (_, i) => i + 1).filter(n => !taken[n]);
      if (!avail.length) { 
        console.log('No cards available');
        alert('No cards available'); 
        router.push('/'); 
        return; 
      }
      card = avail[Math.floor(Math.random() * avail.length)];
      console.log('Auto-selected random card:', card);
    }
    try {
      const tg = (window as any).Telegram?.WebApp;
      const initData = tg?.initData || '';
      console.log('Joining game with card:', card);
      await api.joinGame(gameId, card, initData || undefined);
      console.log('Successfully joined game');
    } catch (e) {
      console.error('Failed to join game:', e);
    }
    sessionStorage.setItem('myCard', String(card));
    sessionStorage.setItem('myUserId', String(u?.id ?? 0));
    console.log('Redirecting to game page...');
    router.push(`/game?game=${gameId}&card=${card}`);
  }, [selected, taken, router]);

  /* ── Init ───────────────────────────────────────────────────────── */
  useEffect(() => {
    const init = async () => {
      try {
        // Get or create user
        const tg = (window as any).Telegram?.WebApp;
        const initData = tg?.initData || '';
        const u = await api.authenticateUser(initData || undefined);
        setUser(u);
        sessionStorage.setItem('user', JSON.stringify(u));

        // For testing: Always create a fresh game
        console.log('Creating new game with stake:', stake);
        const g = await api.createGame('beginner', stake);
        console.log('New game created:', g.game_id, 'countdown:', g.countdown_seconds);
        
        setGame(g);
        sessionStorage.setItem('currentGame', JSON.stringify(g));
        
        // Set initial timer - use countdown_seconds from game or default to 60
        const initialTimer = g.countdown_seconds || 60;
        console.log('Setting initial timer to:', initialTimer);
        setTimer(initialTimer);

        // Load card statuses
        const cardsData = await api.getAvailableCards(g.game_id) as any;
        setTaken(cardsData.taken_cards || {});

        setLoading(false);

        // Connect WebSocket for real-time card updates + timer
        const ws = resetWsClient();
        wsRef.current = ws;
        try {
          console.log('Connecting to WebSocket...');
          await ws.connect(g.game_id, u.id);
          console.log('WebSocket connected successfully');
          setWsConnected(true);
        } catch (e) {
          console.error('WebSocket connection failed:', e);
        }

        ws.on('card_selected', (d: any) => {
          console.log('Card selected:', d.card_number);
          setTaken(prev => ({ ...prev, [d.card_number]: d.user_id }));
        });
        ws.on('card_available', (d: any) => {
          console.log('Card available:', d.card_number);
          setTaken(prev => { const n = { ...prev }; delete n[d.card_number]; return n; });
        });
        ws.on('timer_update', (d: any) => {
          console.log('Timer update from WebSocket:', d.seconds);
          setTimer(d.seconds);
        });
        ws.on('game_started', () => {
          console.log('Game started event received');
          autoJoin(g.game_id, u);
        });
        ws.on('initial_state', (d: any) => {
          console.log('Initial state received:', d);
          if (d.taken_cards) setTaken(d.taken_cards);
          if (d.game_state?.timer !== undefined) {
            console.log('Setting timer from initial state:', d.game_state.timer);
            setTimer(d.game_state.timer);
          }
        });

      } catch (e: any) {
        alert('Failed to load: ' + e.message);
        router.push('/');
      }
    };
    init();
    return () => wsRef.current?.disconnect();
  }, [stake]);

  /* ── Local countdown (fallback if WS not connected) ─────────────── */
  useEffect(() => {
    // Only run local countdown if WebSocket is not connected
    if (loading || timer <= 0 || wsConnected) return;
    const t = setTimeout(() => setTimer(p => Math.max(0, p - 1)), 1000);
    return () => clearTimeout(t);
  }, [timer, loading, wsConnected]);

  /* ── Auto-join when timer reaches 0 ─────────────────────────────── */
  useEffect(() => {
    if (timer === 0 && game && user && !loading) {
      console.log('Timer reached 0, auto-joining game...');
      autoJoin(game.game_id, user);
    }
  }, [timer, game, user, loading, autoJoin]);

  const handleCardClick = (n: number) => {
    if (timer === 0) return;
    if (taken[n] && taken[n] !== user?.id) return;
    if (selected === n) { setSelected(null); return; }
    setSelected(n);
    // Optimistically broadcast via WS
    wsRef.current?.send('select_card', { card_number: n });
  };

  /* ── Card color ──────────────────────────────────────────────────── */
  const cardClass = (n: number) => {
    if (n === selected) return 'card-btn selected';
    if (taken[n])       return 'card-btn taken';
    return 'card-btn available';
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#0f0b1e' }}>
      <div className="text-center">
        <div className="w-14 h-14 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin mx-auto" />
        <p className="text-white/60 mt-3 text-sm">Loading cards…</p>
      </div>
    </div>
  );

  const derash  = calcDerash(game?.total_players ?? 0, stake);
  const mainBalance = (user?.balance ?? 0).toFixed(0);
  const playBalance = (user?.play_balance ?? 0).toFixed(0);
  const timerClass = timer <= 10 ? 'timer-urgent' : 'timer-normal';

  return (
    <div className="h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #6B21A8 0%, #1E293B 50%, #0F172A 100%)' }}>

      {/* ── Top bar ── */}
      <div className="flex items-center justify-between gap-3 px-4 py-3 flex-shrink-0">
        {/* Back */}
        <button onClick={() => router.push('/')}
          className="flex items-center gap-2 text-white/90 hover:text-white bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2 text-sm transition-all border border-white/20">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/>
          </svg>
          Back
        </button>

        {/* Wallets */}
        <div className="flex items-center gap-2">
          <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-3 py-2 flex items-center gap-2 border border-white/10">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4z"/></svg>
            </div>
            <div>
              <p className="text-white/50 text-[10px] leading-tight">Main Wallet</p>
              <p className="text-white font-bold text-sm leading-tight">{mainBalance}</p>
            </div>
          </div>
          <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-3 py-2 flex items-center gap-2 border border-white/10">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a8 8 0 100 16A8 8 0 0010 2zm1 6.5V7a1 1 0 10-2 0v2H7a1 1 0 000 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2z"/></svg>
            </div>
            <div>
              <p className="text-white/50 text-[10px] leading-tight">Play Wallet</p>
              <p className="text-green-400 font-bold text-sm leading-tight">{playBalance}</p>
            </div>
          </div>
          <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-3 py-2 flex items-center gap-2 border border-purple-500/30">
            <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-black">$</span>
            </div>
            <div>
              <p className="text-white/50 text-[10px] leading-tight">Stake</p>
              <p className="text-purple-300 font-bold text-sm leading-tight">{stake}</p>
            </div>
          </div>
        </div>

        {/* Timer & Refresh */}
        <div className="flex items-center gap-2">
          <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-4 py-2 border border-yellow-500/30">
            <p className={`font-black text-2xl ${timerClass}`}>{timer || 0}s</p>
          </div>
          <button onClick={() => window.location.reload()}
            className="flex items-center gap-2 text-white/90 hover:text-white bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2 text-sm transition-all border border-white/20">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* ── Hint ── */}
      <div className="px-4 py-2 flex-shrink-0">
        <p className="text-white/50 text-xs text-center">
          🟢 Yours &nbsp;|&nbsp; 🔴 Taken &nbsp;|&nbsp; Select a card (1–600)
        </p>
      </div>

      {/* ── Card grid ── */}
      <div className="flex-1 overflow-y-auto px-4 pb-24">
        {/* Card container with border */}
        <div className="bg-slate-800/20 backdrop-blur-sm rounded-3xl p-5 border border-slate-700/40">
          <div className="grid grid-cols-8 gap-2.5">
            {Array.from({ length: 600 }, (_, i) => i + 1).map(n => {
              const isTaken = taken[n] && taken[n] !== user?.id;
              const isSelected = n === selected;
              
              return (
                <button key={n}
                  disabled={isTaken || timer === 0}
                  onClick={() => handleCardClick(n)}
                  style={{
                    background: isSelected 
                      ? '#22c55e' 
                      : isTaken 
                      ? '#ea580c' 
                      : 'rgba(71, 85, 105, 0.5)',
                    border: isSelected
                      ? '2px solid #22c55e'
                      : isTaken
                      ? '2px solid #ea580c'
                      : '1.5px solid rgba(100, 116, 139, 0.4)',
                    color: '#fff',
                    borderRadius: '12px',
                    aspectRatio: '1',
                    fontSize: '15px',
                    fontWeight: '700',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: isTaken ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s',
                    transform: isSelected ? 'scale(1.05)' : 'scale(1)',
                    boxShadow: isSelected ? '0 0 20px rgba(34, 197, 94, 0.5)' : 'none',
                  }}
                  onMouseEnter={(e) => {
                    if (!isTaken && !isSelected) {
                      e.currentTarget.style.background = 'rgba(100, 116, 139, 0.6)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isTaken && !isSelected) {
                      e.currentTarget.style.background = 'rgba(71, 85, 105, 0.5)';
                    }
                  }}>
                  {n}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Selected card bottom bar ── */}
      {selected && timer > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-md border-t border-white/10 px-4 py-4 flex items-center justify-between">
          <div>
            <p className="text-white/60 text-xs">Selected Card</p>
            <p className="text-green-400 font-black text-2xl">#{selected}</p>
          </div>
          <button onClick={() => autoJoin(game.game_id, user)}
            className="bg-green-500 hover:bg-green-600 text-white font-bold px-8 py-3 rounded-xl text-base transition-all active:scale-95 shadow-lg">
            Join Now →
          </button>
        </div>
      )}
    </div>
  );
}

export default function CardsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0f0b1e' }}>
        <div className="w-14 h-14 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin" />
      </div>
    }>
      <CardsInner />
    </Suspense>
  );
}
