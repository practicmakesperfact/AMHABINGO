'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import BingoNumberDisplay from '@/components/BingoNumberDisplay';
import WinnerModal from '@/components/WinnerModal';

export default function GamePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const gameId = searchParams.get('game');
  const cardNumber = searchParams.get('card');

  const [game, setGame] = useState<any>(null);
  const [player, setPlayer] = useState<any>(null);
  const [calledNumbers, setCalledNumbers] = useState<number[]>([]);
  const [currentNumber, setCurrentNumber] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAutomatic, setIsAutomatic] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [hasWon, setHasWon] = useState(false);
  const [winningPattern, setWinningPattern] = useState<string | null>(null);
  const [isWaitingForNumber, setIsWaitingForNumber] = useState(true);

  useEffect(() => {
    const initGame = async () => {
      if (!gameId || !cardNumber) {
        router.push('/');
        return;
      }

      try {
        const gameData = await api.getGame(gameId);
        setGame(gameData);
        const cardData = generateBingoCard();
        setPlayer({
          card_number: parseInt(cardNumber),
          card_data: cardData,
          marked_numbers: [],
        });
        setLoading(false);
        
        // Start game after 3 seconds
        setTimeout(() => {
          setIsWaitingForNumber(false);
          simulateNumberCalling();
        }, 3000);
      } catch (error) {
        console.error('Failed to load game:', error);
        setGame({
          game_id: gameId,
          total_players: 350,
          entry_fee: 10,
          prize_pool: 2800,
          status: 'active',
        });
        const cardData = generateBingoCard();
        setPlayer({
          card_number: parseInt(cardNumber),
          card_data: cardData,
          marked_numbers: [],
        });
        setLoading(false);
        
        setTimeout(() => {
          setIsWaitingForNumber(false);
          simulateNumberCalling();
        }, 3000);
      }
    };

    initGame();
  }, [gameId, cardNumber, router]);

  useEffect(() => {
    if (player && calledNumbers.length > 0) {
      checkForWin();
    }
  }, [calledNumbers, player]);

  const checkForWin = () => {
    if (!player?.card_data || hasWon) return;

    const card = player.card_data;
    
    // Check rows
    for (let row = 0; row < 5; row++) {
      let rowComplete = true;
      for (let col = 0; col < 5; col++) {
        const num = card[col][row];
        if (num !== 0 && !calledNumbers.includes(num)) {
          rowComplete = false;
          break;
        }
      }
      if (rowComplete) {
        setHasWon(true);
        setWinningPattern(`Row ${row + 1}`);
        announceWin();
        return;
      }
    }

    // Check columns
    for (let col = 0; col < 5; col++) {
      let colComplete = true;
      for (let row = 0; row < 5; row++) {
        const num = card[col][row];
        if (num !== 0 && !calledNumbers.includes(num)) {
          colComplete = false;
          break;
        }
      }
      if (colComplete) {
        setHasWon(true);
        setWinningPattern(`Column ${getBingoLetter(col)}`);
        announceWin();
        return;
      }
    }

    // Check diagonals
    let diag1Complete = true;
    for (let i = 0; i < 5; i++) {
      const num = card[i][i];
      if (num !== 0 && !calledNumbers.includes(num)) {
        diag1Complete = false;
        break;
      }
    }
    if (diag1Complete) {
      setHasWon(true);
      setWinningPattern('Diagonal \\');
      announceWin();
      return;
    }

    let diag2Complete = true;
    for (let i = 0; i < 5; i++) {
      const num = card[4 - i][i];
      if (num !== 0 && !calledNumbers.includes(num)) {
        diag2Complete = false;
        break;
      }
    }
    if (diag2Complete) {
      setHasWon(true);
      setWinningPattern('Diagonal /');
      announceWin();
      return;
    }
  };

  const announceWin = () => {
    if (!isMuted) {
      speakText('Bingo! You won!');
    }
  };

  const simulateNumberCalling = () => {
    const numbers = Array.from({ length: 75 }, (_, i) => i + 1);
    const shuffled = numbers.sort(() => Math.random() - 0.5);
    
    let index = 0;
    const interval = setInterval(() => {
      if (index < shuffled.length) {
        const num = shuffled[index];
        setCurrentNumber(num);
        setCalledNumbers(prev => [...prev, num]);
        
        const letter = getBingoLetter(Math.floor((num - 1) / 15));
        announceNumber(letter, num);
        
        index++;
      } else {
        clearInterval(interval);
      }
    }, 3000);
  };

  const announceNumber = (letter: string, num: number) => {
    if (!isMuted) {
      speakText(`${letter} ${num}`);
    }
  };

  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;
      window.speechSynthesis.speak(utterance);
    }
  };

  const generateBingoCard = () => {
    const card: number[][] = [];
    const ranges = [
      [1, 15],   // B
      [16, 30],  // I
      [31, 45],  // N
      [46, 60],  // G
      [61, 75],  // O
    ];

    for (let col = 0; col < 5; col++) {
      const column: number[] = [];
      const [min, max] = ranges[col];
      const available = Array.from({ length: max - min + 1 }, (_, i) => min + i);

      for (let row = 0; row < 5; row++) {
        if (col === 2 && row === 2) {
          column.push(0);
        } else {
          const randomIndex = Math.floor(Math.random() * available.length);
          column.push(available.splice(randomIndex, 1)[0]);
        }
      }
      card.push(column);
    }

    return card;
  };

  const getBingoLetter = (col: number) => {
    return ['B', 'I', 'N', 'G', 'O'][col];
  };

  const getNumberColor = (num: number) => {
    if (num >= 1 && num <= 15) return 'bg-blue-500';
    if (num >= 16 && num <= 30) return 'bg-indigo-500';
    if (num >= 31 && num <= 45) return 'bg-purple-500';
    if (num >= 46 && num <= 60) return 'bg-green-500';
    if (num >= 61 && num <= 75) return 'bg-orange-500';
    return 'bg-gray-500';
  };

  const isNumberMarked = (num: number) => {
    return calledNumbers.includes(num);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400 mx-auto"></div>
          <p className="text-white mt-4">Loading game...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 bg-white/10 backdrop-blur-sm rounded-t-2xl p-4">
        <h1 className="text-gray-800 text-xl font-bold">Beteseb Bingo</h1>
        <div className="flex gap-2">
          <button className="text-gray-600 hover:text-gray-800">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
            </svg>
          </button>
          <button onClick={() => router.push('/')} className="text-gray-600 hover:text-gray-800">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Game Info Bar */}
      <div className="grid grid-cols-5 gap-2 mb-4">
        <div className="bg-purple-700/80 backdrop-blur-sm rounded-lg p-3 text-center border border-purple-500/30">
          <div className="text-white/70 text-xs mb-1">Game ID</div>
          <div className="text-white font-bold text-sm">{game?.game_id?.slice(-8).toUpperCase() || 'BBE7RJNS'}</div>
        </div>
        <div className="bg-purple-700/80 backdrop-blur-sm rounded-lg p-3 text-center border border-purple-500/30">
          <div className="text-white/70 text-xs mb-1">Players</div>
          <div className="text-white font-bold text-lg">{game?.total_players || 350}</div>
        </div>
        <div className="bg-purple-700/80 backdrop-blur-sm rounded-lg p-3 text-center border border-purple-500/30">
          <div className="text-white/70 text-xs mb-1">Bet</div>
          <div className="text-white font-bold text-lg">{game?.entry_fee || 10}</div>
        </div>
        <div className="bg-purple-700/80 backdrop-blur-sm rounded-lg p-3 text-center border border-purple-500/30">
          <div className="text-white/70 text-xs mb-1">Derash</div>
          <div className="text-white font-bold text-lg">{game?.prize_pool || 2800}</div>
        </div>
        <div className="bg-purple-700/80 backdrop-blur-sm rounded-lg p-3 text-center border border-purple-500/30">
          <div className="text-white/70 text-xs mb-1">Called</div>
          <div className="text-white font-bold text-lg">{calledNumbers.length}</div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-4 mb-4">
        {/* All 75 Numbers Grid (B:1-15, I:16-30, N:31-45, G:46-60, O:61-75) */}
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-3 border border-purple-600/30">
          <div className="grid grid-cols-5 gap-1 mb-2">
            {['B', 'I', 'N', 'G', 'O'].map((letter, idx) => (
              <div
                key={letter}
                className={`${getNumberColor((idx * 15) + 1)} text-white font-bold text-center py-2 rounded-lg shadow-lg text-sm`}
              >
                {letter}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-5 gap-1 max-h-[600px] overflow-y-auto">
            {/* B Column: 1-15 */}
            {Array.from({ length: 15 }, (_, i) => i + 1).map((num) => (
              <button
                key={`b-${num}`}
                className={`aspect-square rounded-lg font-bold text-sm transition-all shadow-md flex items-center justify-center ${
                  isNumberMarked(num)
                    ? 'bg-orange-500 text-white ring-2 ring-orange-300'
                    : 'bg-gray-700/70 text-white hover:bg-gray-600/70'
                }`}
              >
                {num}
              </button>
            ))}
            
            {/* I Column: 16-30 */}
            {Array.from({ length: 15 }, (_, i) => i + 16).map((num) => (
              <button
                key={`i-${num}`}
                className={`aspect-square rounded-lg font-bold text-sm transition-all shadow-md flex items-center justify-center ${
                  isNumberMarked(num)
                    ? 'bg-orange-500 text-white ring-2 ring-orange-300'
                    : 'bg-gray-700/70 text-white hover:bg-gray-600/70'
                }`}
              >
                {num}
              </button>
            ))}
            
            {/* N Column: 31-45 */}
            {Array.from({ length: 15 }, (_, i) => i + 31).map((num) => (
              <button
                key={`n-${num}`}
                className={`aspect-square rounded-lg font-bold text-sm transition-all shadow-md flex items-center justify-center ${
                  isNumberMarked(num)
                    ? 'bg-orange-500 text-white ring-2 ring-orange-300'
                    : 'bg-gray-700/70 text-white hover:bg-gray-600/70'
                }`}
              >
                {num}
              </button>
            ))}
            
            {/* G Column: 46-60 */}
            {Array.from({ length: 15 }, (_, i) => i + 46).map((num) => (
              <button
                key={`g-${num}`}
                className={`aspect-square rounded-lg font-bold text-sm transition-all shadow-md flex items-center justify-center ${
                  isNumberMarked(num)
                    ? 'bg-orange-500 text-white ring-2 ring-orange-300'
                    : 'bg-gray-700/70 text-white hover:bg-gray-600/70'
                }`}
              >
                {num}
              </button>
            ))}
            
            {/* O Column: 61-75 */}
            {Array.from({ length: 15 }, (_, i) => i + 61).map((num) => (
              <button
                key={`o-${num}`}
                className={`aspect-square rounded-lg font-bold text-sm transition-all shadow-md flex items-center justify-center ${
                  isNumberMarked(num)
                    ? 'bg-orange-500 text-white ring-2 ring-orange-300'
                    : 'bg-gray-700/70 text-white hover:bg-gray-600/70'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Right Side - Number Display */}
        <div className="space-y-4">
          {/* Called Numbers History with Mute */}
          <BingoNumberDisplay
            currentNumber={isWaitingForNumber ? null : currentNumber}
            calledNumbers={calledNumbers}
            isMuted={isMuted}
            onMuteToggle={() => setIsMuted(!isMuted)}
          />

          {/* Waiting/Playing State */}
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-600/30">
            {isWaitingForNumber ? (
              <div className="text-center py-8">
                <div className="flex justify-center gap-2 mb-6">
                  <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <h2 className="text-white text-2xl font-bold mb-4">Get ready for the next number!</h2>
                <div className="w-full bg-gray-700/50 rounded-full h-2 mb-6">
                  <div className="bg-purple-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                </div>
                <div className="flex items-center justify-center gap-3">
                  <span className="text-white/80">Automatic</span>
                  <button
                    onClick={() => setIsAutomatic(!isAutomatic)}
                    className={`relative w-14 h-7 rounded-full transition-colors ${
                      isAutomatic ? 'bg-green-500' : 'bg-gray-600'
                    }`}
                  >
                    <div
                      className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${
                        isAutomatic ? 'translate-x-7' : ''
                      }`}
                    />
                  </button>
                </div>
              </div>
            ) : !hasWon ? (
              <div className="text-center py-8">
                <h2 className="text-white text-2xl font-bold mb-4">Watching Only</h2>
                <p className="text-white/60 text-center leading-relaxed">
                  የዚህ ዙር ጨዋታ ተጫዋች አይደሉም። እዚህ ዙር
                  <br />
                  እስኪጀምር እስኪሁ ይመልከቱ።
                </p>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Winner Modal */}
      <WinnerModal
        isOpen={hasWon}
        cartelaNumber={player?.card_number || 0}
        winningCard={player?.card_data || []}
        calledNumbers={calledNumbers}
        onClose={() => {
          setHasWon(false);
          router.push('/');
        }}
      />

      {/* Bottom Buttons */}
      <div className="grid grid-cols-3 gap-3">
        <button
          onClick={() => router.push('/')}
          className="bg-red-500 hover:bg-red-600 text-white font-bold py-4 rounded-xl transition-all shadow-lg"
        >
          Leave
        </button>
        <button 
          onClick={() => window.location.reload()}
          className="bg-red-800/60 hover:bg-red-800/80 text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
        <button
          className={`font-bold py-4 rounded-xl transition-all shadow-lg ${
            isAutomatic
              ? 'bg-gradient-to-r from-yellow-600 to-orange-600 text-white'
              : 'bg-gray-600 text-white/60'
          }`}
        >
          Automatic
        </button>
      </div>

      {/* Footer */}
      <div className="text-center mt-6 text-white/40 text-sm">
        @beteseb bingo_bot
      </div>
    </main>
  );
}
