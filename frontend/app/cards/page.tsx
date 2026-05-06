'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

export default function CardsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const stake = searchParams.get('stake');
  
  const [gameId, setGameId] = useState<string | null>(null);
  const [selectedCardNumber, setSelectedCardNumber] = useState<number | null>(null);
  const [takenCards, setTakenCards] = useState<Record<number, number>>({});
  const [timer, setTimer] = useState(60);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initGame = async () => {
      console.log('🎴 Cards page loaded, stake:', stake);
      
      if (!stake) {
        console.log('❌ No stake provided, redirecting to home');
        router.push('/');
        return;
      }

      try {
        // Create or find a waiting game with this stake
        const games = await api.listGames('waiting', 'beginner');
        let game;
        
        if (games.length > 0) {
          // Join existing waiting game
          game = games[0];
          console.log('✅ Found existing game:', game.game_id);
        } else {
          // Create new game
          game = await api.createGame('beginner', parseFloat(stake));
          console.log('✅ Created new game:', game.game_id);
        }
        
        setGameId(game.game_id);
        
        // Fetch available cards
        const cardsData = await api.getAvailableCards(game.game_id);
        setTakenCards(cardsData.taken_cards || {});
        console.log('✅ Loaded cards, taken:', Object.keys(cardsData.taken_cards || {}).length);
        
        setLoading(false);
      } catch (error) {
        console.error('❌ Failed to initialize game:', error);
        alert('Failed to load game. Please try again.');
        router.push('/');
      }
    };

    initGame();
  }, [stake, router]);

  // Countdown timer
  useEffect(() => {
    if (timer <= 0) return;
    
    const interval = setInterval(() => {
      setTimer((prev) => Math.max(0, prev - 1));
    }, 1000);
    
    return () => clearInterval(interval);
  }, [timer]);

  const handleCardClick = (cardNumber: number) => {
    console.log('🎴 Card clicked:', cardNumber);
    
    const takenBy = takenCards[cardNumber];

    // If card is taken by someone else, do nothing
    if (takenBy) {
      alert('This card is already taken!');
      return;
    }

    // If this card is selected by current user, unselect it
    if (selectedCardNumber === cardNumber) {
      setSelectedCardNumber(null);
      console.log('❌ Card unselected');
      return;
    }

    // Select this card
    setSelectedCardNumber(cardNumber);
    console.log('✅ Card selected:', cardNumber);
  };

  const handleContinue = async () => {
    if (!selectedCardNumber || !gameId) return;

    console.log('🎮 Joining game with card:', selectedCardNumber);
    
    try {
      setLoading(true);
      
      // Join the game with selected card
      await api.joinGame(gameId, selectedCardNumber);
      console.log('✅ Successfully joined game');
      
      // Navigate to game page
      router.push(`/game?game=${gameId}&card=${selectedCardNumber}`);
    } catch (error: any) {
      console.error('❌ Failed to join game:', error);
      alert(error.response?.data?.detail || 'Failed to join game. Please try again.');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
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
      return 'card-button-taken';
    }
    
    return 'card-button-available';
  };

  return (
    <main className="min-h-screen p-4 pb-24 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white font-semibold">Game #{gameId?.slice(-8)}</p>
            <p className="text-gray-300 text-sm">
              Select your card
            </p>
          </div>
          <div className="text-right">
            <p className="text-yellow-400 font-bold text-2xl">
              {timer}s
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
            disabled={!!takenCards[cardNumber]}
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
              Continue to Game →
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
