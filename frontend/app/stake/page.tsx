'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTelegram } from '@/hooks/useTelegram';
import { useGameStore } from '@/store/gameStore';
import { api } from '@/lib/api';

const STAKE_OPTIONS = [
  { amount: 10, label: '10 ETB', color: 'from-green-500 to-green-600' },
  { amount: 20, label: '20 ETB', color: 'from-blue-500 to-blue-600' },
  { amount: 50, label: '50 ETB', color: 'from-purple-500 to-purple-600' },
  { amount: 100, label: '100 ETB', color: 'from-yellow-500 to-yellow-600' },
];

export default function StakePage() {
  const router = useRouter();
  const { showBackButton, hideBackButton, hapticFeedback } = useTelegram();
  const { user, setCurrentGame, setIsLoading } = useGameStore();
  const [selectedStake, setSelectedStake] = useState<number | null>(null);

  useState(() => {
    showBackButton(() => router.push('/'));
    return () => hideBackButton();
  });

  const handleStakeSelect = async (amount: number) => {
    if (!user) return;

    if (user.balance < amount) {
      hapticFeedback('heavy');
      alert('Insufficient balance! Please deposit first.');
      return;
    }

    setSelectedStake(amount);
    hapticFeedback('medium');

    try {
      setIsLoading(true);

      // Find or create game with this stake
      const games = await api.listGames('waiting', 'beginner');
      let game = games.find((g: any) => g.entry_fee === amount);

      if (!game) {
        // Create new game
        game = await api.createGame('beginner', amount);
      }

      setCurrentGame(game);
      setIsLoading(false);

      // Navigate to card selection
      router.push(`/cards?game=${game.game_id}`);
    } catch (error) {
      console.error('Failed to create/join game:', error);
      setIsLoading(false);
      hapticFeedback('heavy');
      alert('Failed to start game. Please try again.');
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-yellow-400 mb-2">
          Choose Your Stake
        </h1>
        <p className="text-white/80">
          Select entry fee to start playing
        </p>
      </div>

      {/* Balance Display */}
      {user && (
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 mb-8 w-full max-w-md">
          <div className="text-center">
            <p className="text-white/60 text-sm mb-1">Your Balance</p>
            <p className="text-yellow-400 font-bold text-3xl">
              {user.balance.toFixed(2)} ETB
            </p>
          </div>
        </div>
      )}

      {/* Stake Options */}
      <div className="grid grid-cols-2 gap-4 w-full max-w-md">
        {STAKE_OPTIONS.map((option) => {
          const canAfford = user && user.balance >= option.amount;
          
          return (
            <button
              key={option.amount}
              onClick={() => handleStakeSelect(option.amount)}
              disabled={!canAfford}
              className={`
                bg-gradient-to-r ${option.color}
                text-white font-bold py-8 px-6 rounded-2xl shadow-lg
                transform transition-all duration-200
                ${canAfford 
                  ? 'hover:shadow-xl hover:scale-105 active:scale-95' 
                  : 'opacity-50 cursor-not-allowed'
                }
                ${selectedStake === option.amount ? 'ring-4 ring-white' : ''}
              `}
            >
              <div className="text-3xl mb-2">💰</div>
              <div className="text-2xl font-bold">{option.label}</div>
              {!canAfford && (
                <div className="text-xs mt-2 opacity-75">Insufficient balance</div>
              )}
            </button>
          );
        })}
      </div>

      {/* Info */}
      <div className="mt-8 text-center text-white/60 text-sm max-w-md">
        <p>
          💡 Entry fee is collected upfront. Winner takes the prize pool minus 10% commission.
        </p>
      </div>
    </main>
  );
}
