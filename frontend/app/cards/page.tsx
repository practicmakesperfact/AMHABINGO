'use client';

import { useEffect, useState, useRef, Suspense, useCallback, memo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { resetWsClient } from '@/lib/websocket';

/* ── helpers ─────────────────────────────────────────────────────────────── */
function calcDerash(players: number, bet: number) {
  return Math.floor(players * bet * 0.8); // 20 % house commission
}

/* ── Waking-up overlay ───────────────────────────────────────────────────── */
function WakeUpScreen({ seconds }: { seconds: number }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6" style={{ background: '#0f0b1e' }}>
      <div className="w-16 h-16 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin" />
      <div className="text-center px-8">
        <p className="text-white font-bold text-lg mb-1">🚀 Server is waking up…</p>
        <p className="text-white/50 text-sm">Render free plan sleeps when idle.</p>
        <p className="text-white/40 text-xs mt-1">This takes up to 30–60 seconds.</p>
      </div>
      <div className="bg-white/5 rounded-xl px-6 py-3 border border-white/10">
        <p className="text-purple-300 font-black text-3xl text-center">{seconds}s</p>
        <p className="text-white/40 text-xs text-center mt-1">elapsed</p>
      </div>
    </div>
  );
}

/* ── Error / offline overlay ─────────────────────────────────────────────── */
function ErrorScreen({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 px-8" style={{ background: '#0f0b1e' }}>
      <div className="bg-red-900/40 border border-red-500/30 rounded-2xl p-8 max-w-sm w-full text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <p className="text-white font-bold text-lg mb-2">Connection Failed</p>
        <p className="text-white/60 text-sm mb-6">{message}</p>
        <button
          onClick={onRetry}
          className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded-xl transition-all active:scale-95"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

/* ── Memoized Card Button ────────────────────────────────────────────────── */
const BingoCardButton = memo(function BingoCardButton({
  n,
  isTaken,
  isMyCard,
  isSelected,
  isDisabled,
  onClick
}: {
  n: number;
  isTaken: boolean;
  isMyCard: boolean;
  isSelected: boolean;
  isDisabled: boolean;
  onClick: (n: number) => void;
}) {
  return (
    <button
      disabled={isDisabled}
      onClick={() => onClick(n)}
      style={{
        background: isSelected
          ? '#22c55e'
          : isMyCard
          ? '#16a34a'
          : isTaken
          ? '#ea580c'
          : 'rgba(71,85,105,0.5)',
        border: isSelected
          ? '2px solid #22c55e'
          : isMyCard
          ? '2px solid #16a34a'
          : isTaken
          ? '2px solid #ea580c'
          : '1.5px solid rgba(100,116,139,0.4)',
        color: '#fff',
        borderRadius: '10px',
        aspectRatio: '1',
        fontSize: '13px',
        fontWeight: '700',
        cursor: isTaken ? 'not-allowed' : 'pointer',
        transition: 'background 0.1s, transform 0.1s',
        transform: isSelected ? 'scale(1.08)' : 'scale(1)',
        opacity: isTaken ? 0.6 : 1,
      }}
    >
      {n}
    </button>
  );
});

/* ── Inner component (needs Suspense for useSearchParams) ─────────────────── */
function CardsInner() {
  const router  = useRouter();
  const params  = useSearchParams();
  const stake   = Number(params.get('stake') || '10');

  const [user,        setUser]        = useState<any>(null);
  const [game,        setGame]        = useState<any>(null);
  const [taken,       setTaken]       = useState<Record<number, number>>({});
  const [selected,    setSelected]    = useState<number | null>(null);
  const [timer,       setTimer]       = useState<number>(60);
  const [loading,     setLoading]     = useState(true);
  const [wakeUpSecs,  setWakeUpSecs]  = useState<number | null>(null); // null = not waking
  const [error,       setError]       = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  const wsRef   = useRef<ReturnType<typeof resetWsClient> | null>(null);
  const initRef = useRef(false);
  const joiningRef = useRef(false); // Prevent double autoJoin

  /* ── Auto-join ────────────────────────────────────────────────────────── */
  const autoJoin = useCallback(async (gameId: string, u: any) => {
    // Guard: prevent double-join from timer=0 AND game_started firing simultaneously
    if (joiningRef.current) return;
    joiningRef.current = true;

    let card = selected;
    if (!card) {
      const avail = Array.from({ length: 600 }, (_, i) => i + 1).filter(n => !taken[n]);
      if (!avail.length) {
        alert('No cards available — all 600 cartelas are taken!');
        router.push('/');
        joiningRef.current = false;
        return;
      }
      card = avail[Math.floor(Math.random() * avail.length)];
    }

    setLoading(true);
    try {
      const tg       = (window as any).Telegram?.WebApp;
      const initData = tg?.initData || '';
      await api.joinGame(gameId, card, initData || undefined);

      sessionStorage.setItem('myCard',   String(card));
      sessionStorage.setItem('myUserId', String(u?.id ?? 0));
      
      // ⚠️ Clear ALL websocket handlers BEFORE navigating so they
      // cannot fire on the shared singleton in the game page.
      wsRef.current?.disconnect();
      wsRef.current = null;
      
      router.push(`/game?game=${gameId}&card=${card}`);
    } catch (e: any) {
      joiningRef.current = false;
      const msg = e.message || 'Unknown error';
      if (msg.includes('already finished')) {
        // Game is done — go back to lobby
        setLoading(false);
        alert('This game has already finished. Waiting for the next game…');
      } else if (msg.includes('already started')) {
        // Game just started — navigate to game page as spectator (no card)
        wsRef.current?.disconnect();
        wsRef.current = null;
        router.push(`/game?game=${gameId}`);
      } else {
        alert(`Failed to join: ${msg}`);
        setLoading(false);
      }
    }
  }, [selected, taken, router]);

  /* ── Initialization ───────────────────────────────────────────────────── */
  const init = useCallback(async () => {
    setError(null);
    setLoading(true);
    setWakeUpSecs(null);

    try {
      /* ── 1. Wake-up detection ─────────────────────────────────────────── */
      // Quick probe first — if it fails immediately, start wake-up UI
      const alive = await api.ping();
      if (!alive) {
        setLoading(false);
        setWakeUpSecs(0);
        const ok = await api.waitForBackend(
          (secs) => setWakeUpSecs(secs),
          90_000, // wait up to 90s
        );
        if (!ok) {
          setWakeUpSecs(null);
          setError('Backend did not wake up in time. Please try again in a minute.');
          return;
        }
        setWakeUpSecs(null);
        setLoading(true);
      }

      /* ── 2. Auth ──────────────────────────────────────────────────────── */
      let u: any = null;
      const cachedUser = sessionStorage.getItem('user');
      if (cachedUser) {
        u = JSON.parse(cachedUser);
      } else {
        const tg       = (window as any).Telegram?.WebApp;
        const initData = tg?.initData || '';
        u = await api.authenticateUser(initData || undefined);
        sessionStorage.setItem('user', JSON.stringify(u));
      }
      setUser(u);

      /* ── 3. Find / create game ────────────────────────────────────────── */
      const g: any = await api.createGame('beginner', stake);
      sessionStorage.setItem('currentGame', JSON.stringify(g));
      setGame(g);
      setTimer(g.countdown_seconds || 60);

      /* ── 4. Load card statuses + connect WS in parallel ─────────────── */
      const [statusData] = await Promise.all([
        // Use the lightweight endpoint — only returns taken cards
        api.getCardsStatus(g.game_id),
        (async () => {
          if (wsRef.current?.isConnected()) return wsRef.current;
          const ws = resetWsClient();
          wsRef.current = ws;
          try {
            await ws.connect(g.game_id, u.id);
            setWsConnected(true);
          } catch {
            console.warn('⚠️ WebSocket failed — continuing without real-time updates');
          }
          return ws;
        })(),
      ]);

      setTaken((statusData as any).taken_cards || {});
      setLoading(false);

      /* ── 5. WebSocket event handlers ─────────────────────────────────── */
      const ws = wsRef.current;
      if (ws) {
        ws.on('card_selected',    (d: any) => setTaken(prev => ({ ...prev, [d.card_number]: d.user_id })));
        ws.on('card_available',   (d: any) => setTaken(prev => { const n = { ...prev }; delete n[d.card_number]; return n; }));
        ws.on('timer_update',     (d: any) => setTimer(d.seconds));
        ws.on('countdown_started', (d: any) => {
          // Use starts_at (server epoch) to compute true remaining seconds
          if (d.starts_at) {
            const remaining = Math.max(0, Math.round(d.starts_at - Date.now() / 1000));
            setTimer(remaining > 0 ? remaining : d.seconds);
          } else {
            setTimer(d.seconds);
          }
        });
        ws.on('error', (d: any) => {
          setSelected(null);
          alert(d.message || 'An error occurred');
        });
        ws.on('game_state_update', (d: any) => {
          setGame((prev: any) => ({
            ...prev,
            total_players: d.total_players ?? prev?.total_players,
            prize_pool:    d.prize_pool    ?? prev?.prize_pool,
          }));
        });
        ws.on('game_started', () => {
          // Game has started — update status. Timer=0 effect handles autoJoin.
          setGame((prev: any) => prev ? { ...prev, status: 'active' } : prev);
          // Force timer to 0 to trigger autoJoin if countdown hasn't done so yet
          setTimer(0);
        });
        ws.on('initial_state', (d: any) => {
          if (d.taken_cards) setTaken(d.taken_cards);
          // If the game has already started, force timer to 0 to trigger autoJoin immediately
          if (d.game_state?.status === 'active' || d.game_state?.status === 'finished') {
            setTimer(0);
          } else if (d.timer_remaining != null && d.timer_remaining > 0) {
            setTimer(d.timer_remaining);
          }
        });
        ws.on('next_game', (d: any) => {
          if (d.entry_fee === stake) {
            window.location.href = `/cards?stake=${stake}`;
          }
        });
      }

    } catch (e: any) {
      console.error('Init error:', e);
      setLoading(false);
      setWakeUpSecs(null);
      setError(e.message || 'Failed to connect');
    }
  }, [stake, autoJoin]);

  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;
    init();
    return () => {
      wsRef.current?.disconnect();
      initRef.current = false;
    };
  }, [stake]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Local countdown — ref-based so clearInterval never uses a stale ID ── */
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (loading) return;
    // Clear any existing interval before starting a new one
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      setTimer(prev => {
        if (prev <= 1) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [loading]);

  /* ── Auto-join on timer=0 (fires even if still loading from a prior join attempt) */
  const gameRef = useRef<any>(null);
  const userRef = useRef<any>(null);
  gameRef.current = game;
  userRef.current = user;
  useEffect(() => {
    if (timer === 0 && game && user) {
      autoJoin(game.game_id, user);
    }
  }, [timer]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Card click ───────────────────────────────────────────────────────── */
  const handleCardClick = (n: number) => {
    if (timer === 0) return;
    if (taken[n] && taken[n] !== user?.id) return;
    if (selected === n) { setSelected(null); return; }
    setSelected(n);
    wsRef.current?.send('select_card', { card_number: n });
  };

  /* ── Render states ───────────────────────────────────────────────────── */
  if (wakeUpSecs !== null) return <WakeUpScreen seconds={wakeUpSecs} />;

  if (error) return (
    <ErrorScreen
      message={error}
      onRetry={() => { initRef.current = false; init(); }}
    />
  );

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#0f0b1e' }}>
      <div className="text-center">
        <div className="w-14 h-14 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin mx-auto" />
        <p className="text-white/60 mt-3 text-sm">Loading cards…</p>
      </div>
    </div>
  );

  const derash      = calcDerash(game?.total_players ?? 0, stake);
  const mainBalance = (user?.balance    ?? 0).toFixed(0);
  const playBalance = (user?.play_balance ?? 0).toFixed(0);
  const timerUrgent = timer <= 10;

  return (
    <div className="h-screen flex flex-col" style={{ background: 'linear-gradient(135deg,#6B21A8 0%,#1E293B 50%,#0F172A 100%)' }}>

      {/* ── Top bar ────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3 px-4 py-3 flex-shrink-0">
        {/* Back */}
        <button
          onClick={() => {
            sessionStorage.removeItem('currentGame');
            sessionStorage.removeItem('myCard');
            router.push('/');
          }}
          className="flex items-center gap-2 text-white/90 hover:text-white bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2 text-sm transition-all border border-white/20"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>

        {/* Balances */}
        <div className="flex items-center gap-2">
          <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-3 py-2 flex items-center gap-2 border border-white/10">
            <div className="w-7 h-7 bg-green-500 rounded-full flex items-center justify-center">
              <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4z" />
              </svg>
            </div>
            <div>
              <p className="text-white/50 text-[9px] leading-tight">Main</p>
              <p className="text-white font-bold text-sm leading-tight">{mainBalance}</p>
            </div>
          </div>

          <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-3 py-2 flex items-center gap-2 border border-white/10">
            <div className="w-7 h-7 bg-green-500 rounded-full flex items-center justify-center">
              <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a8 8 0 100 16A8 8 0 0010 2zm1 6.5V7a1 1 0 10-2 0v2H7a1 1 0 000 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2z" />
              </svg>
            </div>
            <div>
              <p className="text-white/50 text-[9px] leading-tight">Play</p>
              <p className="text-green-400 font-bold text-sm leading-tight">{playBalance}</p>
            </div>
          </div>

          <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl px-3 py-2 flex items-center gap-2 border border-purple-500/30">
            <div className="w-7 h-7 bg-purple-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-black">$</span>
            </div>
            <div>
              <p className="text-white/50 text-[9px] leading-tight">Stake</p>
              <p className="text-purple-300 font-bold text-sm leading-tight">{stake}</p>
            </div>
          </div>
        </div>

        {/* Timer + WS indicator */}
        <div className="flex items-center gap-2">
          <div className={`backdrop-blur-sm rounded-xl px-4 py-2 border ${timerUrgent ? 'border-red-500/50 bg-red-900/30' : 'border-yellow-500/30 bg-slate-800/60'}`}>
            <p className={`font-black text-2xl ${timerUrgent ? 'text-red-400 animate-pulse' : 'text-yellow-300'}`}>
              {timer || 0}s
            </p>
          </div>
          {/* WebSocket connection dot */}
          <div
            title={wsConnected ? 'Real-time connected' : 'Real-time disconnected'}
            className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`}
          />
        </div>
      </div>

      {/* ── Stats bar ──────────────────────────────────────────────────── */}
      <div className="flex items-center gap-4 px-4 pb-2 flex-shrink-0">
        <span className="text-white/40 text-xs">
          👥 {game?.total_players ?? 0} players
        </span>
        <span className="text-white/40 text-xs">
          💰 Derash: {derash} ETB
        </span>
        <span className="text-white/40 text-xs">
          🃏 {Object.keys(taken).length}/600 joined
        </span>
        {selected && (
          <span className="text-green-400 text-xs font-bold">
            ✅ #{selected} selected
          </span>
        )}
      </div>

      {/* ── 600-card grid ──────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 pb-28">
        <div className="bg-slate-800/20 backdrop-blur-sm rounded-3xl p-4 border border-slate-700/40">
          <div className="grid grid-cols-8 gap-2">
            {Array.from({ length: 600 }, (_, i) => i + 1).map(n => {
              const isTaken     = Boolean(taken[n] && taken[n] !== user?.id);
              const isMyCard    = taken[n] === user?.id;
              const isSelected  = n === selected;

              return (
                <BingoCardButton
                  key={n}
                  n={n}
                  isTaken={isTaken}
                  isMyCard={isMyCard}
                  isSelected={isSelected}
                  isDisabled={isTaken || timer === 0}
                  onClick={handleCardClick}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Bottom: selected card + join button ──────────────────────────── */}
      {selected && timer > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-md border-t border-white/10 px-4 py-4 flex items-center justify-between">
          <div>
            <p className="text-white/60 text-xs">Selected Card</p>
            <p className="text-green-400 font-black text-2xl">#{selected}</p>
          </div>
          <button
            onClick={() => autoJoin(game.game_id, user)}
            className="bg-green-500 hover:bg-green-400 text-white font-bold px-8 py-3 rounded-xl text-base transition-all active:scale-95 shadow-lg"
          >
            Join Now →
          </button>
        </div>
      )}
    </div>
  );
}

export default function CardsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center" style={{ background: '#0f0b1e' }}>
          <div className="w-14 h-14 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin" />
        </div>
      }
    >
      <CardsInner />
    </Suspense>
  );
}
