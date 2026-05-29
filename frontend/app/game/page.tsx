'use client';

import { useEffect, useState, useRef, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { getWsClient } from '@/lib/websocket';

/* ── types ── */
interface Winner {
  user_id: number;
  username?: string;
  card_number: number;
  card_data: number[][];
  winning_pattern: string;
  prize_amount: number;
}

/* ── helpers ── */
const BINGO = ['B', 'I', 'N', 'G', 'O'];
const LETTER_COLORS: Record<string, string> = {
  B: 'badge-b', I: 'badge-i', N: 'badge-n', G: 'badge-g', O: 'badge-o',
};
const HEADER_COLORS: Record<string, string> = {
  B: 'bg-blue-500', I: 'bg-purple-500', N: 'bg-purple-700', G: 'bg-green-500', O: 'bg-orange-500',
};

function getLetter(n: number) {
  if (n >= 1  && n <= 15) return 'B';
  if (n >= 16 && n <= 30) return 'I';
  if (n >= 31 && n <= 45) return 'N';
  if (n >= 46 && n <= 60) return 'G';
  return 'O';
}

function speak(text: string) {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.9;
    window.speechSynthesis.speak(u);
  }
}

function calcDerash(players: number, bet: number) {
  return Math.floor(players * bet * 0.8);
}

/* ── winning rows/cols/diags ── */
function getWinningCells(card: number[][], pattern: string): Set<string> {
  const s = new Set<string>();
  if (!card || !pattern) return s;
  if (pattern.startsWith('row_')) {
    const r = parseInt(pattern.split('_')[1]);
    for (let c = 0; c < 5; c++) s.add(`${r}-${c}`);
  } else if (pattern.startsWith('col_')) {
    const col = parseInt(pattern.split('_')[1]);
    for (let r = 0; r < 5; r++) s.add(`${r}-${col}`);
  } else if (pattern === 'diagonal_lr') {
    for (let i = 0; i < 5; i++) s.add(`${i}-${i}`);
  } else if (pattern === 'diagonal_rl') {
    for (let i = 0; i < 5; i++) s.add(`${i}-${4 - i}`);
  }
  return s;
}

/* ── Inner component ── */
function GameInner() {
  const router = useRouter();
  const params = useSearchParams();
  const gameId   = params.get('game') || '';
  const cardNum  = parseInt(params.get('card') || '0');

  const [game,          setGame]          = useState<any>(null);
  const [calledNums,    setCalledNums]    = useState<number[]>([]);
  const [currentNum,    setCurrentNum]    = useState<number | null>(null);
  const [recentNums,    setRecentNums]    = useState<number[]>([]);
  const [playerCard,    setPlayerCard]    = useState<number[][] | null>(null);
  const [muted,         setMuted]         = useState(false);
  const [automatic,     setAutomatic]     = useState(true);
  const [loading,       setLoading]       = useState(true);
  const [winner,        setWinner]        = useState<Winner[] | null>(null);
  const [nextGameTimer, setNextGameTimer] = useState<number | null>(null);
  const [userId,        setUserId]        = useState(0);
  const [wsConnected,   setWsConnected]   = useState(false);

  const mutableMuted = useRef(false);
  mutableMuted.current = muted;

  /* ── Init ── */
  useEffect(() => {
    if (!gameId) { router.push('/'); return; }

    const init = async () => {
      try {
        // Get user
        const storedUser = sessionStorage.getItem('user');
        let u = storedUser ? JSON.parse(storedUser) : null;
        if (!u) {
          const tg = (window as any).Telegram?.WebApp;
          u = await api.authenticateUser(tg?.initData || undefined);
          sessionStorage.setItem('user', JSON.stringify(u));
        }
        setUserId(u?.id ?? 0);

        // Get game data
        const g = await api.getGame(gameId);
        setGame(g);
        setCalledNums((g as any).called_numbers || []);
        setCurrentNum((g as any).current_number ?? null);

        // Get player card
        if (cardNum && u?.id) {
          try {
            const pc = await api.getPlayerCard(gameId, u.id) as any;
            setPlayerCard(pc.card_data);
            sessionStorage.setItem('myCard', String(pc.card_number));
          } catch {}
        }

        setLoading(false);

        // Connect WebSocket
        const ws = getWsClient();
        try {
          await ws.connect(gameId, u?.id ?? 0);
          setWsConnected(true);
        } catch {}

        ws.on('number_called', (d: any) => {
          const num = d.number;
          setCurrentNum(num);
          setCalledNums(prev => [...prev, num]);
          setRecentNums(prev => [num, ...prev].slice(0, 5));
          if (!mutableMuted.current) speak(`${getLetter(num)} ${num}`);
        });

        ws.on('player_won', (d: any) => {
          const winners: Winner[] = d.winners || [];
          setWinner(winners);
          if (winners.length && !mutableMuted.current) speak('Bingo!');
          // Start next-game countdown
          let count = 8;
          setNextGameTimer(count);
          const t = setInterval(() => {
            count--;
            setNextGameTimer(count);
            if (count <= 0) {
              clearInterval(t);
              router.push('/');
            }
          }, 1000);
        });

        ws.on('timer_update', (d: any) => {
          setGame((prev: any) => prev ? { ...prev, _timer: d.seconds } : prev);
        });

        ws.on('game_started', () => {
          setGame((prev: any) => prev ? { ...prev, status: 'active' } : prev);
        });

        ws.on('next_game', (d: any) => {
          // Auto-redirect to new game's card selection after 3s
          setTimeout(() => router.push(`/cards?stake=${game?.entry_fee ?? 10}`), 3000);
        });

        // Refresh game info every 5s
        const interval = setInterval(async () => {
          try {
            const gUpdated = await api.getGame(gameId) as any;
            setGame(gUpdated);
            setCalledNums(gUpdated.called_numbers || []);
            setCurrentNum(gUpdated.current_number ?? null);
          } catch {}
        }, 5000);
        return () => clearInterval(interval);

      } catch (e: any) {
        console.error(e);
        setLoading(false);
      }
    };

    init();
    return () => { getWsClient().disconnect(); };
  }, [gameId]);

  /* ── Render ── */
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#0f0b1e' }}>
      <div className="text-center">
        <div className="w-14 h-14 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin mx-auto" />
        <p className="text-white/50 mt-3 text-sm">Loading game…</p>
      </div>
    </div>
  );

  const players  = game?.total_players ?? 0;
  const bet      = game?.entry_fee ?? 10;
  const derash   = calcDerash(players, bet);

  // Build 75-number columns
  const numColumns = BINGO.map((_, ci) =>
    Array.from({ length: 15 }, (_, i) => ci * 15 + i + 1)
  );

  const isWinner = (winner || []).some(w => w.user_id === userId);

  return (
    <div className="h-screen flex flex-col" style={{ background: '#0f0b1e' }}>

      {/* ── Top header ── */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/10 flex-shrink-0">
        <h1 className="text-white font-black text-base tracking-widest">AMHABINGO</h1>
        <div className="flex gap-2">
          <button onClick={() => setMuted(m => !m)}
            className="text-white/60 hover:text-white transition-colors">
            {muted
              ? <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12.293 7.293a1 1 0 011.414 0L15 8.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 010-1.414z" clipRule="evenodd"/>
                </svg>
              : <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd"/>
                </svg>
            }
          </button>
          <button onClick={() => router.push('/')} className="text-white/60 hover:text-white">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      {/* ── Info bar ── */}
      <div className="flex gap-1.5 px-2 py-1.5 flex-shrink-0">
        {[
          { label: 'Game ID', value: game?.game_id?.slice(-8).toUpperCase() ?? '—' },
          { label: 'Players', value: players },
          { label: 'Bet',     value: bet },
          { label: 'Derash',  value: derash },
          { label: 'Called',  value: calledNums.length },
        ].map(({ label, value }) => (
          <div key={label} className="info-tile text-center">
            <div className="info-tile-label">{label}</div>
            <div className="info-tile-value text-sm">{value}</div>
          </div>
        ))}
      </div>

      {/* ── Main body ── */}
      <div className="flex-1 flex gap-3 px-3 pb-2 overflow-hidden min-h-0">

        {/* Left: 75-number BINGO grid - ALL 15 ROWS VISIBLE */}
        <div className="flex flex-col bg-slate-800/40 rounded-2xl flex-shrink-0 border border-slate-700/50 p-2" style={{ width: '240px' }}>
          {/* B I N G O headers */}
          <div className="grid grid-cols-5 gap-1.5 mb-2 flex-shrink-0">
            {BINGO.map(l => (
              <div key={l} className={`${HEADER_COLORS[l]} text-white font-black text-center py-1.5 rounded-lg text-sm`}>{l}</div>
            ))}
          </div>
          {/* Numbers - ALL 15 ROWS, calculated height */}
          <div className="grid grid-cols-5 gap-1.5 flex-1">
            {numColumns.map((col, ci) => (
              <div key={ci} className="flex flex-col gap-1.5">
                {col.map(n => (
                  <div key={n}
                    className={`flex items-center justify-center text-xs font-bold rounded-lg transition-all ${
                      calledNums.includes(n)
                        ? 'bg-orange-600 text-white'
                        : 'bg-slate-700/70 text-white/80'
                    }`}
                    style={{ height: 'calc((100% - 56px) / 15)' }}>
                    {n}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Right panel */}
        <div className="flex-1 flex flex-col gap-3 overflow-hidden min-w-0">

          {/* Recent numbers row */}
          <div className="flex items-center gap-2 bg-slate-800/40 rounded-2xl px-4 py-3 flex-shrink-0 border border-slate-700/50">
            <div className="flex gap-2 overflow-x-auto flex-1">
              {recentNums.length === 0 && (
                <span className="text-white/30 text-xs">Waiting for numbers…</span>
              )}
              {recentNums.map((n, i) => {
                const l = getLetter(n);
                return (
                  <div key={i} className={`num-badge ${LETTER_COLORS[l]} text-white font-black text-sm px-4 py-2 rounded-xl whitespace-nowrap`}>
                    {l}-{n}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Current number */}
          <div className="flex-1 bg-slate-800/40 rounded-2xl p-4 flex flex-col items-center justify-center gap-4 overflow-hidden border border-slate-700/50">
            {currentNum ? (
              <div className="current-number-circle">
                <span className="current-number-letter">{getLetter(currentNum)}</span>
                <span className="current-number-num">{currentNum}</span>
              </div>
            ) : (
              <div className="flex gap-2">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-3 h-3 bg-purple-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 150}ms` }} />
                ))}
              </div>
            )}

            {/* Automatic toggle */}
            <div className="w-full bg-slate-700/60 rounded-xl px-5 py-3 flex items-center justify-between">
              <span className="text-white/70 text-base font-semibold">Automatic</span>
              <button onClick={() => setAutomatic(a => !a)}
                className={`relative w-14 h-7 rounded-full transition-colors ${automatic ? 'bg-green-500' : 'bg-gray-600'}`}>
                <div className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${automatic ? 'translate-x-7' : ''}`} />
              </button>
            </div>

            {/* Player card OR watching */}
            {playerCard ? (
              <div className="w-full">
                <p className="text-white/50 text-xs text-center mb-2">Your Card — #{cardNum}</p>
                {/* 5×5 bingo card */}
                <div className="grid grid-cols-5 gap-2">
                  {BINGO.map(l => (
                    <div key={l} className={`${HEADER_COLORS[l]} text-white font-black text-center py-1.5 rounded text-sm`}>{l}</div>
                  ))}
                  {Array.from({ length: 5 }, (_, row) =>
                    Array.from({ length: 5 }, (_, col) => {
                      const val = playerCard[col]?.[row] ?? 0;
                      const isFree = (row === 2 && col === 2) || val === 0;
                      const isMarked = !isFree && calledNums.includes(val);
                      return (
                        <div key={`${row}-${col}`}
                          className={`bingo-cell text-sm ${isFree ? 'free' : isMarked ? 'marked' : 'unmarked'}`}>
                          {isFree ? '✦' : val}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            ) : (
              <div className="w-full bg-slate-700/60 rounded-xl p-5 text-center">
                <h3 className="text-white font-bold text-lg mb-2">Watching Only</h3>
                <p className="text-white/50 text-sm leading-relaxed">
                  የዚህ ዙር ጨዋታ ተጫዋች አይደሉም።<br />
                  አዲስ ዙር እስኪጀምር እዚሁ ይቆዩ።
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Bottom buttons ── */}
      <div className="grid grid-cols-3 gap-2 px-2 pb-2 flex-shrink-0">
        <button onClick={() => router.push('/')}
          className="bg-red-500 hover:bg-red-600 text-white font-bold py-3 rounded-xl text-sm transition-all active:scale-95">
          Leave
        </button>
        <button onClick={() => window.location.reload()}
          className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-1.5 transition-all active:scale-95">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          Refresh
        </button>
        <button className={`font-bold py-3 rounded-xl text-sm transition-all ${
          automatic ? 'bg-yellow-600 hover:bg-yellow-500 text-white' : 'bg-gray-700 text-white/50'
        }`} onClick={() => setAutomatic(a => !a)}>
          Automatic
        </button>
      </div>

      {/* ── Footer ── */}
      <div className="text-center text-white/20 text-[10px] pb-1">@amhabingo_bot</div>

      {/* ── Winner Overlay ── */}
      {winner && (
        <div className="winner-overlay" onClick={() => { if (nextGameTimer === 0) router.push('/'); }}>
          <div className="winner-card">
            {/* Crown */}
            <div className="w-16 h-16 bg-yellow-500 rounded-full flex items-center justify-center mx-auto mb-3 shadow-lg">
              <svg className="w-9 h-9 text-yellow-900" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 4a1 1 0 011-1h8a1 1 0 011 1v1l2 2-2 3H5L3 7l2-2V4z"/>
                <path fillRule="evenodd" d="M4 10h12v1a2 2 0 01-2 2H6a2 2 0 01-2-2v-1z" clipRule="evenodd"/>
              </svg>
            </div>

            <h2 className="text-yellow-400 font-black text-3xl mb-1">BINGO!</h2>

            {winner.map((w, i) => (
              <p key={i} className="text-white font-bold text-lg mb-1">
                🎉 {w.username || `Player ${w.user_id}`} WON! 🎉
              </p>
            ))}

            {winner[0] && (
              <>
                <div className="bg-gray-800/60 rounded-xl p-3 my-3">
                  <p className="text-white/60 text-xs mb-2">🏆 Winning Cartela : {winner[0].card_number}</p>
                  {winner[0].card_data && (() => {
                    const winCells = getWinningCells(winner[0].card_data, winner[0].winning_pattern);
                    return (
                      <>
                        <div className="grid grid-cols-5 gap-1 mb-1">
                          {BINGO.map(l => (
                            <div key={l} className={`${HEADER_COLORS[l]} text-white font-black text-center py-1 rounded text-xs`}>{l}</div>
                          ))}
                        </div>
                        <div className="grid grid-cols-5 gap-1">
                          {Array.from({ length: 5 }, (_, row) =>
                            Array.from({ length: 5 }, (_, col) => {
                              const val = winner[0].card_data[col]?.[row] ?? 0;
                              const isFree = row === 2 && col === 2;
                              const isWin  = winCells.has(`${row}-${col}`);
                              const isMark = !isFree && calledNums.includes(val);
                              return (
                                <div key={`${row}-${col}`}
                                  className={`bingo-cell text-xs ${
                                    isFree ? 'free' : isWin ? 'winning' : isMark ? 'marked' : 'unmarked'
                                  }`}>
                                  {isFree ? '✦' : val}
                                </div>
                              );
                            })
                          )}
                        </div>
                      </>
                    );
                  })()}
                </div>
                <p className="text-yellow-400 font-bold text-lg">
                  Prize: {winner[0].prize_amount?.toFixed(0)} ETB
                  {winner.length > 1 && ` (÷${winner.length})`}
                </p>
              </>
            )}

            {isWinner && (
              <div className="mt-2 bg-green-500/20 border border-green-500/40 rounded-lg px-3 py-2">
                <p className="text-green-400 font-bold text-sm">🎊 You won! Prize added to your wallet.</p>
              </div>
            )}

            {nextGameTimer !== null && nextGameTimer > 0 && (
              <div className="mt-3 flex items-center justify-center gap-2 text-white/50 text-xs">
                <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                Auto-starting next game in {nextGameTimer}s
              </div>
            )}

            <button onClick={() => router.push('/')}
              className="mt-4 w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 rounded-xl text-sm transition-all">
              Back to Home
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function GamePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0f0b1e' }}>
        <div className="w-14 h-14 border-4 border-t-purple-500 border-white/10 rounded-full animate-spin" />
      </div>
    }>
      <GameInner />
    </Suspense>
  );
}
