'use client';

import { useEffect, useState, useRef, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { resetWsClient } from '@/lib/websocket';

/* types */
interface Winner {
  user_id: number;
  username?: string;
  card_number: number;
  card_data: number[][];
  winning_pattern: string;
  prize_amount: number;
}

/* helpers */
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
    u.rate = 0.85;
    u.pitch = 1.0;
    u.volume = 1.0;
    u.lang = 'en-US';
    window.speechSynthesis.speak(u);
  }
}

function formatPattern(pattern: string): string {
  if (!pattern) return 'Unknown';
  
  // Convert backend pattern names to user-friendly format
  if (pattern.startsWith('row_')) {
    const rowNum = parseInt(pattern.split('_')[1]) + 1;
    return `Row ${rowNum}`;
  }
  if (pattern.startsWith('col_')) {
    const colNum = parseInt(pattern.split('_')[1]) + 1;
    return `Column ${colNum}`;
  }
  if (pattern === 'diagonal_lr') return 'Diagonal ↘';
  if (pattern === 'diagonal_rl') return 'Diagonal ↙';
  if (pattern === 'four_corner') return 'Four Corners';
  if (pattern === 'blackout') return 'Blackout (Full Card)';
  
  return pattern;
}

function calcDerash(players: number, bet: number) {
  return Math.floor(players * bet * 0.8);
}

/* winning rows/cols/diags/patterns */
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
  } else if (pattern === 'four_corner') {
    s.add('0-0'); s.add('0-4'); s.add('4-0'); s.add('4-4');
  } else if (pattern === 'blackout') {
    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 5; c++) s.add(`${r}-${c}`);
    }
  }
  return s;
}

/* Inner component */
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
  const [fullCard,      setFullCard]      = useState<number[][] | null>(null); // Store full 5x5 card
  const [muted,         setMuted]         = useState(false);
  const [loading,       setLoading]       = useState(true);
  const [gameStarting,  setGameStarting]  = useState(false); // grace period countdown
  const [startingIn,    setStartingIn]    = useState(0);     // seconds until game starts
  const automatic = true; // Always ON, not changeable

  const mutableMuted = useRef(false);
  mutableMuted.current = muted;
  const [winner,        setWinner]        = useState<Winner[] | null>(null);
  const [nextGameTimer, setNextGameTimer] = useState<number | null>(null);
  const [userId,        setUserId]        = useState(0);
  const [wsConnected,   setWsConnected]   = useState(false);
  const initRef = useRef(false); // Prevent double initialization

  /* Init */
  useEffect(() => {
    if (!gameId) { router.push('/'); return; }
    if (initRef.current) return; // Prevent double initialization
    initRef.current = true;

    const init = async () => {
      try {
        setLoading(true);
        
        // Get user from cache first
        let u = null;
        const storedUser = sessionStorage.getItem('user');
        if (storedUser) {
          u = JSON.parse(storedUser);
        } else {
          const tg = (window as any).Telegram?.WebApp;
          u = await api.authenticateUser(tg?.initData || undefined);
          sessionStorage.setItem('user', JSON.stringify(u));
        }
        setUserId(u?.id ?? 0);

        // Fetch game data and player card in parallel
        const [g, pcData] = await Promise.all([
          api.getGame(gameId),
          cardNum && u?.id ? api.getPlayerCard(gameId, u.id).catch(() => null) : Promise.resolve(null)
        ]);

        setGame(g);
        
        // NOTE: called_numbers are now Redis-only (not in DB).
        // They are delivered via the WebSocket 'initial_state' event below.
        // Initialize to empty here; WS will populate them.
        setCalledNums([]);
        setCurrentNum(null);
        setRecentNums([]);

        if (pcData) {
          // Store full 5x5 card
          const fullCardData = (pcData as any).card_data;
          setFullCard(fullCardData);
          setPlayerCard(fullCardData); // Use full card
          sessionStorage.setItem('myCard', String((pcData as any).card_number));
        }

        setLoading(false);

        // Connect WebSocket — use resetWsClient to get a CLEAN client
        // with no stale handlers from the cards page.
        const ws = resetWsClient();
        try {
          await ws.connect(gameId, u?.id ?? 0);
          setWsConnected(true);
        } catch (e) {
          console.error('WebSocket failed:', e);
        }

        ws.on('number_called', (d: any) => {
          const num = d.number;
          const letter = getLetter(num);
          
          // Update current number
          setCurrentNum(num);
          
          // Add to called numbers (keep all called numbers)
          setCalledNums(prev => {
            if (prev.includes(num)) return prev;
            return [...prev, num];
          });
          
          // Update recent numbers - keep last 8 for display at top
          setRecentNums(prev => {
            const updated = [num, ...prev.filter(n => n !== num)].slice(0, 8);
            return updated;
          });
          
          // Announce with voice
          if (!mutableMuted.current) {
            speak(`${letter} ${num}`);
          }
        });

        ws.on('player_won', (d: any) => {
          const winners: Winner[] = d.winners || [];
          console.log('🎉 BINGO! Winners:', winners);
          setWinner(winners);
          
          // Announce winner
          if (winners.length && !mutableMuted.current) {
            speak('Bingo!');
          }
          
          // Start next-game countdown
          let count = 5;
          setNextGameTimer(count);
          const t = setInterval(() => {
            count--;
            setNextGameTimer(count);
            if (count <= 0) {
              clearInterval(t);
              // Redirect to card selection with same stake (not home page)
              const stake = (g as any)?.entry_fee ?? 10;
              router.push(`/cards?stake=${stake}`);
            }
          }, 1000);
        });

        ws.on('timer_update', (d: any) => {
          setGame((prev: any) => prev ? { ...prev, _timer: d.seconds } : prev);
          // When timer hits 0 on game page, show grace period countdown (8s)
          // Use functional check via setCurrentNum to avoid stale closure
          if (d.seconds === 0) {
            setCurrentNum(prev => {
              if (!prev) {
                setGameStarting(true);
                setStartingIn(8);
                const t = setInterval(() => {
                  setStartingIn(p => {
                    if (p <= 1) { clearInterval(t); setGameStarting(false); return 0; }
                    return p - 1;
                  });
                }, 1000);
              }
              return prev;
            });
          }
        });

        ws.on('game_started', () => {
          setGame((prev: any) => prev ? { ...prev, status: 'active' } : prev);
          setGameStarting(false);
        });
        
        // Listen for game state updates (players, prize pool, etc.)
        ws.on('game_state_update', (d: any) => {
          setGame((prev: any) => ({
            ...prev,
            total_players: d.total_players ?? prev?.total_players,
            prize_pool: d.prize_pool ?? prev?.prize_pool,
          }));
        });
        
        ws.on('initial_state', (d: any) => {
          // If game already finished, redirect to card selection for next round
          if (d.game_state?.status === 'finished') {
            console.log('Game already finished, redirecting...');
            const stake = g?.entry_fee ?? 10;
            router.push(`/cards?stake=${stake}`);
            return;
          }
          // Restore game info from Redis
          if (d.game_state) {
            setGame((prev: any) => ({
              ...prev,
              status: d.game_state.status ?? prev?.status,
              total_players: d.game_state.total_players ?? prev?.total_players,
              prize_pool: d.game_state.prize_pool ?? prev?.prize_pool,
            }));
          }
          // Restore called numbers history if server sends them
          if (d.called_numbers && Array.isArray(d.called_numbers)) {
            setCalledNums(d.called_numbers);
            setCurrentNum(d.called_numbers[d.called_numbers.length - 1] ?? null);
            setRecentNums([...d.called_numbers].reverse().slice(0, 8));
          }
        });

        // Removed: next_game redirect - handled by player_won event

      } catch (e: any) {
        console.error(e);
        setLoading(false);
      }
    };

    init();
    return () => { 
      resetWsClient();
      initRef.current = false;
    };
  }, [gameId]);

  /* Stuck-game recovery: poll the game status every 15s.
     If the game has finished but we never got the WS event
     (e.g. Render cold start, WS dropped), redirect to next round. */
  useEffect(() => {
    if (!gameId || winner) return; // no need if we already have a winner
    const interval = setInterval(async () => {
      try {
        const g = await api.getGame(gameId);
        if (g && (g as any).status === 'finished') {
          console.log('Stuck-game recovery: game is finished, redirecting...');
          clearInterval(interval);
          const stake = (g as any).entry_fee ?? game?.entry_fee ?? 10;
          router.push(`/cards?stake=${stake}`);
        }
      } catch {
        // Backend unreachable — skip this check
      }
    }, 15_000);
    return () => clearInterval(interval);
  }, [gameId, winner]);

  /* Render */
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

      {/* Top header */}
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
          <button onClick={() => {
            // Clear session when user closes
            sessionStorage.removeItem('currentGame');
            sessionStorage.removeItem('myCard');
            router.push('/');
          }} className="text-white/60 hover:text-white">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Info bar - COMPACT */}
      <div className="flex gap-1 px-2 py-1 flex-shrink-0">
        {[
          { label: 'Game ID', value: game?.game_id?.slice(-8).toUpperCase() ?? '—' },
          { label: 'Players', value: players },
          { label: 'Bet',     value: bet },
          { label: 'Derash',  value: derash },
          { label: 'Called',  value: calledNums.length },
        ].map(({ label, value }) => (
          <div key={label} className="info-tile text-center">
            <div className="info-tile-label text-[9px]">{label}</div>
            <div className="info-tile-value text-xs">{value}</div>
          </div>
        ))}
      </div>

      {/* Main body - NO SCROLLING */}
      <div className="flex-1 flex gap-2 px-2 pb-2 min-h-0">

        {/* Left: 75-number BINGO grid */}
        <div className="flex flex-col bg-slate-800/40 rounded-xl flex-shrink-0 border border-slate-700/50 p-2" style={{ width: '200px' }}>
          {/* B I N G O headers */}
          <div className="grid grid-cols-5 gap-1 mb-1 flex-shrink-0">
            {BINGO.map(l => (
              <div key={l} className={`${HEADER_COLORS[l]} text-white font-black text-center py-1 rounded text-xs`}>{l}</div>
            ))}
          </div>
          {/* Numbers - ALL 15 ROWS */}
          <div className="grid grid-cols-5 gap-1 flex-1">
            {numColumns.map((col, ci) => (
              <div key={ci} className="flex flex-col gap-1">
                {col.map(n => {
                  const isCalled = calledNums.includes(n);
                  const isCurrent = n === currentNum;
                  return (
                    <div key={n}
                      className={`flex items-center justify-center text-[10px] font-bold rounded transition-all ${
                        isCurrent
                          ? 'bg-green-500 text-white scale-110'
                          : isCalled
                          ? 'bg-orange-600 text-white'
                          : 'bg-slate-700/70 text-white/80'
                      }`}
                      style={{ height: 'calc((100% - 14px) / 15)' }}>
                      {n}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Right panel - FIXED HEIGHT */}
        <div className="flex-1 flex flex-col gap-2 min-w-0">

          {/* Recent numbers (no sound button) */}
          <div className="flex items-center gap-2 bg-slate-800/40 rounded-xl px-3 py-1.5 flex-shrink-0 border border-slate-700/50">
            <div className="flex gap-1 overflow-x-auto flex-1">
              {recentNums.length === 0 && (
                <span className="text-white/30 text-[10px]">
                  {gameStarting ? `🚀 Starting in ${startingIn}s…` : 'Waiting for game to start…'}
                </span>
              )}
              {recentNums.map((n, i) => {
                const l = getLetter(n);
                return (
                  <div key={`${n}-${i}`} 
                    className={`${HEADER_COLORS[l]} text-white font-bold text-[10px] px-2 py-1 rounded-full whitespace-nowrap min-w-[40px] text-center`}>
                    {l}-{n}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Current number - SMALL (or GAME OVER banner) */}
          {winner ? (
            <div className="bg-red-600 rounded-xl p-3 flex items-center justify-center flex-shrink-0 border-2 border-yellow-400">
              <div className="text-center">
                <div className="text-yellow-400 font-black text-xl">🏆 GAME OVER 🏆</div>
                <div className="text-white font-bold text-sm mt-1">WINNER FOUND!</div>
              </div>
            </div>
          ) : (
            <div className="bg-slate-800/40 rounded-xl p-2 flex items-center justify-center flex-shrink-0 border border-slate-700/50">
              {currentNum ? (
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center shadow-lg border-2 border-yellow-300">
                  <div className="text-purple-700 font-black text-xl leading-none">
                    {getLetter(currentNum)}-{currentNum}
                  </div>
                </div>
              ) : (
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <div key={i} className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Automatic toggle - DISABLED (always ON) */}
          <div className="bg-slate-800/40 rounded-xl px-3 py-1.5 flex items-center justify-between flex-shrink-0 border border-slate-700/50 opacity-60 blur-[0.3px]">
            <span className="text-xs font-semibold text-white/50">Automatic</span>
            <button 
              disabled
              className="relative w-10 h-5 rounded-full bg-green-500 cursor-not-allowed">
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full translate-x-5" />
            </button>
          </div>

          {/* Player's bingo card - FITS REMAINING SPACE (gold border if winner) */}
          {playerCard && fullCard ? (
            <div className={`bg-slate-800/40 rounded-xl p-2 flex-1 flex flex-col min-h-0 ${
              isWinner ? 'border-4 border-yellow-400 shadow-2xl shadow-yellow-400/50' : 'border border-slate-700/50'
            }`}>
              {/* BINGO headers */}
              <div className="grid grid-cols-5 gap-1 mb-1 flex-shrink-0">
                {BINGO.map(l => (
                  <div key={l} className={`${HEADER_COLORS[l]} text-white font-black text-center py-1 rounded text-xs`}>{l}</div>
                ))}
              </div>
              {/* 5x5 grid - PROPER GRID LAYOUT */}
              <div className="grid grid-cols-5 grid-rows-5 gap-1 flex-1">
                {Array.from({ length: 5 }, (_, row) =>
                  Array.from({ length: 5 }, (_, col) => {
                    const val = fullCard[col]?.[row] ?? 0;
                    const isFree = row === 2 && col === 2;
                    const isMarked = !isFree && calledNums.includes(val);
                    
                    return (
                      <div key={`${row}-${col}`}
                        className={`${
                          isFree ? 'bg-purple-600' : isMarked ? 'bg-green-500' : 'bg-white'
                        } ${
                          isFree || isMarked ? 'text-white' : 'text-purple-700'
                        } font-bold text-center flex items-center justify-center rounded text-xs transition-all`}>
                        {isFree ? '✦' : val}
                      </div>
                    );
                  })
                ).flat()}
              </div>
              <div className={`mt-1 text-center rounded py-1 flex-shrink-0 ${
                isWinner ? 'bg-yellow-400' : 'bg-yellow-600/90'
              }`}>
                <span className={`font-bold text-[10px] ${isWinner ? 'text-purple-900' : 'text-white'}`}>
                  {isWinner ? '🏆 WINNER! ' : ''}Cartela No: {cardNum}
                </span>
              </div>
            </div>
          ) : (
            <div className="bg-slate-800/40 rounded-xl p-4 text-center flex-1 flex items-center justify-center border border-slate-700/50">
              <div>
                <div className="text-4xl mb-3">👀</div>
                <h3 className="text-white font-bold text-lg mb-2">Watching Only</h3>
                <p className="text-white/70 text-sm leading-relaxed mb-1">
                  You are not playing this round.
                </p>
                <p className="text-white/50 text-xs leading-relaxed">
                  የዚህ ዙር ጨዋታ ተጫዋች አይደሉም።<br />
                  አዲስ ዙር እስኪጀምር እዚሁ ይቆዩ።
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom buttons */}
      <div className="grid grid-cols-3 gap-2 px-2 pb-2 flex-shrink-0">
        <button onClick={() => {
          // Clear session when user explicitly leaves
          sessionStorage.removeItem('currentGame');
          sessionStorage.removeItem('myCard');
          router.push('/');
        }}
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
        <button 
          disabled
          className="font-bold py-3 rounded-xl text-sm bg-green-500 text-white cursor-not-allowed opacity-60 blur-[0.3px]">
          Automatic
        </button>
      </div>

      {/* Footer */}
      <div className="text-center text-white/20 text-[10px] pb-1">@amhabingo_bot</div>

      {/* Winner Overlay */}
      {winner && (
        <div className="winner-overlay" onClick={() => { 
          if (nextGameTimer === 0) {
            const stake = game?.entry_fee ?? 10;
            router.push(`/cards?stake=${stake}`);
          }
        }}>
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
              <div key={i} className="mb-2">
                <p className="text-white font-bold text-lg mb-1">
                  🎉 {w.username || `Player ${w.user_id}`} WON! 🎉
                </p>
                <p className="text-yellow-300 font-semibold text-sm">
                  Pattern: {formatPattern(w.winning_pattern)}
                </p>
              </div>
            ))}

            {winner[0] && (
              <>
                <div className="bg-gray-800/60 rounded-xl p-3 my-3">
                  <p className="text-white/60 text-xs mb-2">🏆 Winning Cartela: {winner[0].card_number}</p>
                  {winner[0].card_data && (() => {
                    const winCells = getWinningCells(winner[0].card_data, winner[0].winning_pattern);
                    return (
                      <>
                        <div className="grid grid-cols-5 gap-1.5 mb-1.5">
                          {BINGO.map(l => (
                            <div key={l} className={`${HEADER_COLORS[l]} text-white font-black text-center py-1.5 rounded text-xs`}>{l}</div>
                          ))}
                        </div>
                        <div className="grid grid-cols-5 gap-1.5">
                          {Array.from({ length: 5 }, (_, row) =>
                            Array.from({ length: 5 }, (_, col) => {
                              const val = winner[0].card_data[col]?.[row] ?? 0;
                              const isFree = row === 2 && col === 2;
                              const isWinningCell = winCells.has(`${row}-${col}`);
                              const isCalled = !isFree && calledNums.includes(val);
                              
                              return (
                                <div key={`${row}-${col}`}
                                  className={`bingo-cell text-xs ${
                                    isFree 
                                      ? 'free' 
                                      : isWinningCell 
                                      ? 'winning' 
                                      : isCalled 
                                      ? 'marked' 
                                      : 'unmarked'
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

            <button onClick={() => {
              const stake = game?.entry_fee ?? 10;
              router.push(`/cards?stake=${stake}`);
            }}
              className="mt-4 w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 rounded-xl text-sm transition-all">
              Next Game →
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
