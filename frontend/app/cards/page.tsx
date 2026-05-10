'use client';

import { useEffect, useState, useRef, Suspense } from 'react';
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
  const [timer, setTimer]       = useState(60);
  const [loading, setLoading]   = useState(true);
  const wsRef = useRef<ReturnType<typeof resetWsClient> | null>(null);

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

        // Find waiting game at this stake or create one
        const games = await api.listGames('waiting') as any[];
        let g = games.find((x: any) => x.entry_fee === stake);

        if (!g) {
          // Also check countdown games
          const cGames = await api.listGames('countdown') as any[];
          g = cGames.find((x: any) => x.entry_fee === stake);
        }

        if (!g) {
          g = await api.createGame('beginner', stake);
        }
        setGame(g);
        sessionStorage.setItem('currentGame', JSON.stringify(g));

        // Load card statuses
        const cardsData = await api.getAvailableCards(g.game_id) as any;
        setTaken(cardsData.taken_cards || {});

        setLoading(false);

        // Connect WebSocket for real-time card updates + timer
        const ws = resetWsClient();
        wsRef.current = ws;
        try {
          await ws.connect(g.game_id, u.id);
        } catch {}

        ws.on('card_selected', (d: any) => {
          setTaken(prev => ({ ...prev, [d.card_number]: d.user_id }));
        });
        ws.on('card_available', (d: any) => {
          setTaken(prev => { const n = { ...prev }; delete n[d.card_number]; return n; });
        });
        ws.on('timer_update', (d: any) => {
          setTimer(d.seconds);
        });
        ws.on('game_started', () => {
          autoJoin(g.game_id, u);
        });
        ws.on('initial_state', (d: any) => {
          if (d.taken_cards) setTaken(d.taken_cards);
          if (d.game_state?.timer) setTimer(d.game_state.timer);
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
    if (loading || timer <= 0) return;
    const t = setTimeout(() => setTimer(p => Math.max(0, p - 1)), 1000);
    return () => clearTimeout(t);
  }, [timer, loading]);

  useEffect(() => {
    if (timer === 0 && game && user) autoJoin(game.game_id, user);
  }, [timer]);

  /* ── Auto-join ───────────────────────────────────────────────────── */
  const autoJoin = async (gameId: string, u: any) => {
    let card = selected;
    if (!card) {
      const avail = Array.from({ length: 600 }, (_, i) => i + 1).filter(n => !taken[n]);
      if (!avail.length) { alert('No cards available'); router.push('/'); return; }
      card = avail[Math.floor(Math.random() * avail.length)];
    }
    try {
      const tg = (window as any).Telegram?.WebApp;
      const initData = tg?.initData || '';
      await api.joinGame(gameId, card, initData || undefined);
    } catch {}
    sessionStorage.setItem('myCard', String(card));
    sessionStorage.setItem('myUserId', String(u?.id ?? 0));
    router.push(`/game?game=${gameId}&card=${card}`);
  };

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
    <div className="h-screen flex flex-col" style={{ background: '#0f0b1e' }}>

      {/* ── Top bar ── */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/10 flex-shrink-0">
        {/* Back */}
        <button onClick={() => router.push('/')}
          className="flex items-center gap-1 text-white/70 hover:text-white bg-white/10 rounded-lg px-2 py-1.5 text-xs transition-all">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/>
          </svg>
          Back
        </button>

        {/* Wallets */}
        <div className="flex items-center gap-2 flex-1 justify-center">
          <div className="bg-white/5 rounded-lg px-2 py-1 text-center border border-white/10">
            <p className="text-white/40 text-[9px]">Main wallet</p>
            <p className="text-white font-bold text-xs">{mainBalance}</p>
          </div>
          <div className="bg-white/5 rounded-lg px-2 py-1 text-center border border-white/10">
            <p className="text-white/40 text-[9px]">Play wallet</p>
            <p className="text-green-400 font-bold text-xs">{playBalance}</p>
          </div>
          <div className="bg-white/5 rounded-lg px-2 py-1 text-center border border-white/10">
            <p className="text-white/40 text-[9px]">Stake</p>
            <p className="text-yellow-400 font-bold text-xs">{stake}</p>
          </div>
        </div>

        {/* Timer */}
        <div className="flex items-center gap-1.5 bg-gray-800 rounded-lg px-2 py-1.5 border border-white/10">
          <div className="text-center">
            <p className="text-white/50 text-[9px]">Starts in</p>
            <p className={`font-black text-xs ${timerClass}`}>{timer}s</p>
          </div>
        </div>
      </div>

      {/* ── Game info row ── */}
      <div className="flex gap-2 px-3 py-2 flex-shrink-0">
        {[
          { label: 'Game ID', value: game?.game_id?.slice(-8).toUpperCase() ?? '—' },
          { label: 'Players', value: game?.total_players ?? 0 },
          { label: 'Derash',  value: derash },
        ].map(({ label, value }) => (
          <div key={label} className="info-tile">
            <div className="info-tile-label">{label}</div>
            <div className="info-tile-value">{value}</div>
          </div>
        ))}
      </div>

      {/* ── Hint ── */}
      <div className="px-3 flex-shrink-0">
        <p className="text-white/40 text-xs text-center py-1">
          🟢 Yours &nbsp;|&nbsp; 🔴 Taken &nbsp;|&nbsp; Select a card (1–600)
          {timer > 0 && timer <= 10 && (
            <span className="text-red-400 font-bold animate-pulse"> — Hurry! {timer}s</span>
          )}
        </p>
      </div>

      {/* ── Card grid ── */}
      <div className="flex-1 overflow-y-auto px-3 pb-20">
        <div className="card-grid-8">
          {Array.from({ length: 600 }, (_, i) => i + 1).map(n => (
            <button key={n} className={cardClass(n)}
              disabled={!!(taken[n] && taken[n] !== user?.id) || timer === 0}
              onClick={() => handleCardClick(n)}>
              {n}
            </button>
          ))}
        </div>
      </div>

      {/* ── Selected card bottom bar ── */}
      {selected && timer > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-black/90 border-t border-green-500/40 px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-white/60 text-xs">Selected Card</p>
            <p className="text-yellow-400 font-black text-xl">#{selected}</p>
          </div>
          <button onClick={() => autoJoin(game.game_id, user)}
            className="bg-green-500 hover:bg-green-600 text-white font-bold px-6 py-3 rounded-xl text-sm transition-all active:scale-95">
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
