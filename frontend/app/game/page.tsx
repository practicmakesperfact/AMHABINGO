'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useGameStore } from '@/store/gameStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useTelegram } from '@/hooks/useTelegram';
import { audioManager } from '@/lib/audio';
import BingoCard from '@/components/BingoCard';
import CalledNumbers from '@/components/CalledNumbers';
import Timer from '@/components/Timer';
import WinnerModal from '@/components/WinnerModal';
import Loading from '@/components/Loading';

interface Winner {
  user_id: number;
  username: string;
  card_number: number;
  winning_pattern: string;
  prize: number;
}

export default function GamePage() {
  const router = useRouter();
  const { user, currentGame, currentPlayer, timer, calledNumbers, currentNumber } = useGameStore();
  const { isConnected } = useWebSocket();
  const { hapticFeedback, showAlert } = useTelegram();
  
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [winners, setWinners] = useState<Winner[]>([]);
  const [showWinnerModal, setShowWinnerModal] = useState(false);

  // Redirect if no game
  useEffect(() => {
    if (!currentGame || !currentPlayer) {
      router.push('/');
    }
  }, [currentGame, currentPlayer, router]);

  // Handle audio announcements
  useEffect(() => {
    if (currentNumber && audioEnabled) {
      audioManager.announceNumber(currentNumber);
      hapticFeedback('light');
    }
  }, [currentNumber, audioEnabled, hapticFeedback]);

  // Handle game start
  useEffect(() => {
    if (currentGame?.status === 'active' && audioEnabled) {
      audioManager.announceGameStart();
    }
  }, [currentGame?.status, audioEnabled]);

  // Handle winners
  useEffect(() => {
    if (currentGame?.winner_ids && currentGame.winner_ids.length > 0 && !showWinnerModal) {
      // Fetch winner details (in real app, this would come from WebSocket)
      const winnerData: Winner[] = currentGame.winner_ids.map((id, idx) => ({
        user_id: id,
        username: `Player ${id}`,
        card_number: idx + 1,
        winning_pattern: 'row_0',
        prize: currentGame.prize_pool / currentGame.winner_ids.length,
      }));
      
      setWinners(winnerData);
      setShowWinnerModal(true);
      
      if (audioEnabled) {
        audioManager.announceWinner();
      }
      hapticFeedback('success');
    }
  }, [currentGame?.winner_ids, showWinnerModal, currentGame?.prize_pool, audioEnabled, hapticFeedback]);

  const toggleAudio = () => {
    const newState = !audioEnabled;
    setAudioEnabled(newState);
    audioManager.setEnabled(newState);
    hapticFeedback('light');
  };

  const handleClaimWin = () => {
    if (!currentGame || !currentPlayer) return;
    
    // Check if player has won
    const hasWon = currentPlayer.has_won;
    
    if (hasWon) {
      showAlert('You already claimed your win!');
    } else {
      showAlert('No winning pattern detected yet. Keep playing!');
    }
    hapticFeedback('light');
  };

  const handleWinnerModalClose = () => {
    setShowWinnerModal(false);
    router.push('/');
  };

  if (!currentGame || !currentPlayer) {
    return <Loading message="Loading game..." />;
  }

  const getStatusMessage = () => {
    switch (currentGame.status) {
      case 'waiting':
        return 'Waiting for players...';
      case 'countdown':
        return 'Game starting soon!';
      case 'active':
        return 'Game in progress';
      case 'finished':
        return 'Game finished';
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white p-4 pb-20">
      {/* Header */}
      <div className="max-w-6xl mx-auto mb-6">
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="text-sm text-gray-400">Game ID</div>
              <div className="font-bold">{currentGame.game_id}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-400">Status</div>
              <div className="font-bold text-yellow-400">{getStatusMessage()}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400">Prize Pool</div>
              <div className="font-bold text-green-400">{currentGame.prize_pool.toFixed(2)} ETB</div>
            </div>
          </div>
          
          <div className="flex items-center justify-between text-sm">
            <div>
              <span className="text-gray-400">Players:</span>{' '}
              <span className="font-semibold">{currentGame.total_players}/{currentGame.max_players}</span>
            </div>
            <div>
              <span className="text-gray-400">Your Card:</span>{' '}
              <span className="font-semibold">#{currentPlayer.card_number}</span>
            </div>
            <div>
              <span className="text-gray-400">Room:</span>{' '}
              <span className="font-semibold capitalize">{currentGame.room}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Timer */}
      {currentGame.status === 'countdown' && (
        <div className="max-w-6xl mx-auto mb-6">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
            <Timer 
              seconds={timer} 
              label="Game starts in"
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-6">
        {/* Left: Bingo Card */}
        <div>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Your Card</h2>
              <div className="flex gap-2">
                <button
                  onClick={toggleAudio}
                  className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition-colors"
                >
                  {audioEnabled ? '🔊' : '🔇'}
                </button>
                <button
                  onClick={handleClaimWin}
                  className="bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-bold px-4 py-2 rounded-lg transition-colors"
                >
                  Claim Win
                </button>
              </div>
            </div>
            
            <BingoCard
              card={currentPlayer.card_data}
              markedNumbers={currentPlayer.marked_numbers}
              currentNumber={currentNumber}
            />

            <div className="mt-4 text-center text-sm text-gray-400">
              {currentPlayer.marked_numbers.length} numbers marked
            </div>
          </div>
        </div>

        {/* Right: Called Numbers */}
        <div>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
            <h2 className="text-xl font-bold mb-4">Called Numbers</h2>
            <CalledNumbers
              calledNumbers={calledNumbers}
              currentNumber={currentNumber}
            />
          </div>
        </div>
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <div className="fixed bottom-4 left-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg text-center">
          ⚠️ Disconnected - Reconnecting...
        </div>
      )}

      {/* Winner Modal */}
      <WinnerModal
        winners={winners}
        isOpen={showWinnerModal}
        onClose={handleWinnerModalClose}
      />
    </div>
  );
}
