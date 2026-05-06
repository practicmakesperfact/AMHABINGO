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
        console.log('📡 Fetching waiting games...');
        const games = await api.listGames('waiting', 'beginner');
        console.log('📡 Games response:', games);
        let game;
        
        if (games.length > 0) {
          // Join existing waiting game
          game = games[0];
          console.log('✅ Found existing game:', game.game_id);
        } else {
          // Create new game
          console.log('📡 Creating new game with stake:', stake);
          game = await api.createGame('beginner', parseFloat(stake));
          console.log('✅ Created new game:', game.game_id);
        }
        
        setGameId(game.game_id);
        
        // Fetch available cards
        console.log('📡 Fetching available cards...');
        const cardsData = await api.getAvailableCards(game.game_id);
        console.log('📡 Cards data:', cardsData);
        setTakenCards(cardsData.taken_cards || {});
        console.log('✅ Loaded cards, taken:', Object.keys(cardsData.taken_cards || {}).length);
        
        setLoading(false);
      } catch (error: any) {
        console.error('❌ Failed to initialize game:', error);
        console.error('❌ Error details:', error.response?.data);
        console.error('❌ Error status:', error.response?.status);
        alert(`Failed to load game: ${error.response?.data?.detail || error.message || 'Unknown error'}`);
        router.push('/');
      }
    };

    initGame();
  }, [stake, router]);

  // Countdown timer with auto-redirect
  useEffect(() => {
    if (timer <= 0) {
      // Timer reached 0, auto-select random card and join game
      handleAutoJoinGame();
      return;
    }
    
    const interval = setInterval(() => {
      setTimer((prev) => Math.max(0, prev - 1));
    }, 1000);
    
    return () => clearInterval(interval);
  }, [timer]);

  const handleAutoJoinGame = async () => {
    if (!gameId) return;

    try {
      // If no card selected, pick a random available card
      let cardToJoin = selectedCardNumber;
      
      if (!cardToJoin) {
        const availableCards = Array.from({ length: 600 }, (_, i) => i + 1)
          .filter(num => !takenCards[num]);
        
        if (availableCards.length === 0) {
          alert('No cards available!');
          router.push('/');
          return;
        }
        
        // Pick random card
        cardToJoin = availableCards[Math.floor(Math.random() * availableCards.length)];
        console.log('🎲 Auto-selected random card:', cardToJoin);
      }

      console.log('🎮 Auto-joining game with card:', cardToJoin);
      
      // Try to join the game, but continue even if it fails
      try {
        await api.joinGame(gameId, cardToJoin);
        console.log('✅ Successfully joined game');
      } catch (joinError) {
        console.warn('⚠️ Failed to join game via API, continuing anyway:', joinError);
      }
      
      // Navigate to game page regardless
      router.push(`/game?game=${gameId}&card=${cardToJoin}`);
    } catch (error: any) {
      console.error('❌ Failed to auto-join game:', error);
      // Still try to navigate to game page
      const cardToUse = selectedCardNumber || Math.floor(Math.random() * 600) + 1;
      router.push(`/game?game=${gameId}&card=${cardToUse}`);
    }
  };

  const handleCardClick = (cardNumber: number) => {
    // Don't allow selection if timer is 0
    if (timer === 0) return;
    
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
          {timer > 0 && timer <= 10 && (
            <span className="block mt-1 text-yellow-400 font-bold animate-pulse">
              ⏰ Hurry! Game starts in {timer}s
            </span>
          )}
          {timer === 0 && (
            <span className="block mt-1 text-green-400 font-bold">
              🎮 Starting game...
            </span>
          )}
        </p>
      </div>

      {/* Card Grid */}
      <div className="card-grid mb-4">
        {Array.from({ length: 600 }, (_, i) => i + 1).map((cardNumber) => (
          <button
            key={cardNumber}
            onClick={() => handleCardClick(cardNumber)}
            className={`card-button ${getCardStyle(cardNumber)}`}
            disabled={!!takenCards[cardNumber] || timer === 0}
          >
            {cardNumber}
          </button>
        ))}
      </div>

      {/* Selected Card Indicator (Fixed at bottom, no button) */}
      {selectedCardNumber && timer > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4">
          <div className="max-w-md mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border-2 border-green-500/50">
              <p className="text-white text-center">
                Selected Card: <span className="font-bold text-yellow-400 text-xl">#{selectedCardNumber}</span>
              </p>
              <p className="text-white/60 text-sm text-center mt-2">
                Game will start automatically in {timer}s
              </p>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
