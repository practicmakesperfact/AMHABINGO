'use client';

import { useEffect, useState, useRef, Suspense, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { resetWsClient } from '@/lib/websocket';

/* helpers */
function calcDerash(players: number, bet: number) {
  return Math.floor(players * bet * 0.8); // 20% house commission
}

/* Inner component (needs Suspense for useSearchParams) */
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
  const initRef = useRef(false); // Prevent double initialization

  /* Auto-join function (defined early so it can be used in useEffects) */
  const autoJoin = useCallback(async (gameId: string, u: any) => {
    console.log('Auto-joining game:', gameId);
    
    // Use refs to get current values without causing re-renders
    let card = selected;
    if (!card) {
      const currentTaken = taken;
      const avail = Array.from({ length: 600 }, (_, i) => i + 1).filter(n => !currentTaken[n]);
      if (!avail.length) { 
        console.log('No cards available');
        alert('No cards available - all 600 cartelas are taken!'); 
        router.push('/'); 
        return; 
      }
      card = avail[Math.floor(Math.random() * avail.length)];
      console.log('Auto-selected random cartela:', card);
    }
    
    // Show loading state
    setLoading(true);
    
    try {
      const tg = (window as any).Telegram?.WebApp;
      const initData = tg?.initData || '';
      console.log('Joining game with cartela:', card);
      await api.joinGame(gameId, card, initData || undefined);
      console.log('Successfully joined game');
      
      sessionStorage.setItem('myCard', String(card));
      sessionStorage.setItem('myUserId', String(u?.id ?? 0));
      console.log('Redirecting to game page...');
      router.push(`/game?game=${gameId}&card=${card}`);
    } catch (e: any) {
      console.error('Failed to join game:', e);
      const errorMsg = e.message || 'Unknown error';
      
      // Handle specific error cases
      if (errorMsg.includes('already finished') || errorMsg.includes('already started')) {
        console.log('Game not joinable, waiting for next game...');
        alert('This game is no longer joinable. Waiting for next game...');
        setLoading(false);
        // Don't redirect, wait for next_game WebSocket event
      } else {
        alert(`Failed to join game: ${errorMsg}`);
        setLoading(false);
      }
    }
  }, [selected, taken, router]);

  /* Init */
  useEffect(() => {
    // Prevent double initialization in React StrictMode
    if (initRef.current) return;
    initRef.current = true;

    const init = async () => {
      try {
        setLoading(true);
        
        // Get or create user (from cache if available)
        let u = null;
        const cachedUser = sessionStorage.getItem('user');
        if (cachedUser) {
          u = JSON.parse(cachedUser);
        } else {
          const tg = (window as any).Telegram?.WebApp;
          const initData = tg?.initData || '';
          u = await api.authenticateUser(initData || undefined);
          sessionStorage.setItem('user', JSON.stringify(u));
        }
        setUser(u);

        // Find or create a game for this stake amount (backend will reuse existing ones)
        console.log('Finding/creating game for stake:', stake);
        const g = await api.createGame('beginner', stake);
        sessionStorage.setItem('currentGame', JSON.stringify(g));
        
        setGame(g);
        
        // Set initial timer
        const initialTimer = (g as any).countdown_seconds || 60;
        setTimer(initialTimer);

        // Load card statuses and connect WebSocket in parallel
        const [cardsData] = await Promise.all([
          api.getAvailableCards((g as any).game_id),
          // WebSocket connection starts in parallel (non-blocking)
          (async () => {
            // Only create WebSocket if not already connected
            if (wsRef.current?.isConnected()) {
              console.log('WebSocket already connected, reusing...');
              return wsRef.current;
            }
            
            const ws = resetWsClient();
            wsRef.current = ws;
            try {
              console.log('Connecting WebSocket for game:', (g as any).game_id);
              await ws.connect((g as any).game_id, u.id);
              setWsConnected(true);
              console.log('✅ WebSocket connected');
            } catch (e) {
              console.warn('⚠️ WebSocket failed - continuing without real-time updates');
              // Don't block the UI if WebSocket fails
            }
            return ws;
          })()
        ]);

        setTaken((cardsData as any).taken_cards || {});
        setLoading(false);

        // Setup WebSocket event handlers (only once)
        const ws = wsRef.current;
        if (ws) {
          ws.on('card_selected', (d: any) => {
            setTaken(prev => ({ ...prev, [d.card_number]: d.user_id }));
          });
          ws.on('card_available', (d: any) => {
            setTaken(prev => { const n = { ...prev }; delete n[d.card_number]; return n; });
          });
          ws.on('timer_update', (d: any) => {
            setTimer(d.seconds);
          });
          ws.on('game_state_update', (d: any) => {
            // Update game state when players join
            setGame((prev: any) => ({
              ...prev,
              total_players: d.total_players ?? prev?.total_players,
              prize_pool: d.prize_pool ?? prev?.prize_pool,
            }));
          });
          ws.on('game_started', () => {
            // Capture current values at the time of event
            const currentGame = g;
            const currentUser = u;
            autoJoin((currentGame as any).game_id, currentUser);
          });
          ws.on('initial_state', (d: any) => {
            if (d.taken_cards) setTaken(d.taken_cards);
            if (d.game_state?.timer !== undefined) {
              setTimer(d.game_state.timer);
            }
            if (d.game_state) {
              setGame((prev: any) => ({
                ...prev,
                total_players: d.game_state.total_players ?? prev?.total_players,
                prize_pool: d.game_state.prize_pool ?? prev?.prize_pool,
              }));
            }
          });
          ws.on('next_game', (d: any) => {
            console.log('Next game created:', d.game_id);
            // Only reload if it's for the same stake amount
            if (d.entry_fee === stake) {
              window.location.href = `/cards?stake=${stake}`;
            }
          });
        }

      } catch (e: any) {
        alert('Failed to load: ' + e.message);
        router.push('/');
      }
    };
    init();
    
    return () => {
      wsRef.current?.disconnect();
      initRef.current = false;
    };
  }, [stake, router]); // Removed autoJoin from dependencies

  /* Local countdown (fallback if WS not connected) */
  useEffect(() => {
    // Only run local countdown if WebSocket is not connected
    if (loading || timer <= 0 || wsConnected) return;
    const t = setTimeout(() => setTimer(p => Math.max(0, p - 1)), 1000);
    return () => clearTimeout(t);
  }, [timer, loading, wsConnected]);

  /* Auto-join when timer reaches 0  */
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

  /* Card color  */
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

  // Prevent blinking by using stable references
  const stableGame = game;
  const stableUser = user;

  return (
    <div className="h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #6B21A8 0%, #1E293B 50%, #0F172A 100%)' }}>

      {/* Top bar */}
      <div className="flex items-center justify-between gap-3 px-4 py-3 flex-shrink-0">
        {/* Back */}
        <button onClick={() => {
          // Clear session when user explicitly goes back
          sessionStorage.removeItem('currentGame');
          sessionStorage.removeItem('myCard');
          router.push('/');
        }}
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

      {/* Hint */}
     

      {/* Card grid */}
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

      {/* Selected card bottom bar */}
      {selected && timer > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-md border-t border-white/10 px-4 py-4 flex items-center justify-between">
          <div>
            <p className="text-white/60 text-xs">Selected Card</p>
            <p className="text-green-400 font-black text-2xl">#{selected}</p>
          </div>
          <button onClick={() => autoJoin(stableGame.game_id, stableUser)}
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
