'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useTelegram } from '@/hooks/useTelegram';
import { useGameStore } from '@/store/gameStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { api } from '@/lib/api';

export default function CardsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const gameId = searchParams.get('game');
  
  const { showBackButton, hideBackButton, hapticFeedback, userId } = useTelegram();
  const {
    currentGame,
    setCurrentGame,
    selectedCardNumber,
    setSelectedCardNumber,
    takenCards,
    setTakenCards,
    timer,
    user,
  } = useGameStore();

  const { selectCard, unselectCard } = useWebSocket(gameId, userId);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    showBackButton(() => router.push('/stake'));
    return () => hideBackButton();
  }, []);

  useEffect(() => {
    const loadGame = async () => {
      if (!gameId) {
        router.push('/');
        return;
      }

      try {
        // Load game data
        const game = await api.getGame(gameId);
        setCurrentGame(game);

        // Load available cards
        const cardsData = await api.getAvailableCards(gameId);
        setTakenCards(cardsData.taken_cards);

        setLoading(false);
      } catch (error) {
        console.error('Failed to load game:', error);
        router.push('/');
      }
    };

    loadGame();
  }, [gameId]);

  const handleCardClick = (cardNumber: number) => {
    if (!userId) return;

    const takenBy = takenCards[cardNumber];

    // If card is taken by someone else, do nothing
    if (takenBy && takenBy !== userId) {
      hapticFeedback('heavy');
      return;
    }

    // If this card is selected by current user, unselect it
    if (selectedCardNumber === cardNumber) {
      unselectCard(cardNumber);
      setSelectedCardNumber(null);
      hapticFeedback('light');
      return;
    }

    // If another card was selected, unselect it first
    if (selectedCardNumber) {
      unselectCard(selectedCardNumber);
    }

    // Select this card
    selectCard(cardNumber);
    setSelectedCardNumber(cardNumber);
    hapticFeedback('medium');
  };

  const handleContinue = async () => {
    if (!selectedCardNumber || !gameId) return;

    try {
      hapticFeedback('medium');
      
      // Initialize payment
      const payment = await api.initializePayment(gameId, selectedCardNumber);
      
      // Open payment URL
      window.open(payment.checkout_url, '_blank');
      
      // Navigate to game page (will wait for payment verification)
      router.push(`/game?game=${gameId}&tx_ref=${payment.tx_ref}`);
    } catch (error) {
      console.error('Payment failed:', error);
      hapticFeedback('heavy');
      alert('Payment initialization failed. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400 mx-auto"></div>
          <p className="text-white mt-4">Loading cards...</p>
        </div>
      </div>
    );
  }

  const getCardStyle = (cardNumber: number) => {
    const takenBy = takenCards[cardNumber];
    
    if (selectedCardNumber === cardNumber) {
      return 'card-button-selected';
    }
    
    if (takenBy) {
      return takenBy === userId ? 'card-button-selected' : 'card-button-taken';
    }
    
    return 'card-button-available';
  };

  return (
    <main className="min-h-screen p-4 pb-24">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white font-semibold">Game #{currentGame?.game_id}</p>
            <p className="text-gray-300 text-sm">
              Entry: {currentGame?.entry_fee} ETB
            </p>
          </div>
          <div className="text-right">
            <p className="text-yellow-400 font-bold text-2xl">
              {timer > 0 ? `${timer}s` : '0s'}
            </p>
            <p className="text-gray-300 text-sm">Time left</p>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-blue-500/20 backdrop-blur-lg rounded-xl p-3 mb-4">
        <p className="text-white text-sm text-center">
          💡 Select a card number (1-600). Green = yours, Red = taken
        </p>
      </div>

      {/* Card Grid */}
      <div className="card-grid mb-4">
        {Array.from({ length: 600 }, (_, i) => i + 1).map((cardNumber) => (
          <button
            key={cardNumber}
            onClick={() => handleCardClick(cardNumber)}
            className={`card-button ${getCardStyle(cardNumber)}`}
            disabled={takenCards[cardNumber] && takenCards[cardNumber] !== userId}
          >
            {cardNumber}
          </button>
        ))}
      </div>

      {/* Fixed Bottom Bar */}
      {selectedCardNumber && (
        <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4">
          <div className="max-w-md mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 mb-3">
              <p className="text-white text-center">
                Selected Card: <span className="font-bold text-yellow-400">#{selectedCardNumber}</span>
              </p>
            </div>
            <button
              onClick={handleContinue}
              className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white font-bold py-4 rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 active:scale-95"
            >
              Continue to Payment →
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
