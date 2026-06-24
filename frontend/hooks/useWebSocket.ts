import { useEffect, useCallback } from 'react';
import { wsClient, WSMessageType, WSEventHandler } from '@/lib/websocket';
import { useGameStore } from '@/store/gameStore';

export function useWebSocket(gameId: string | null, userId: number | null) {
  const {
    addTakenCard,
    removeTakenCard,
    setTimer,
    addCalledNumber,
    setCurrentNumber,
    setCurrentGame,
    currentGame,
  } = useGameStore();

  useEffect(() => {
    if (!gameId || !userId) return;

    // Connect to WebSocket
    wsClient.connect(gameId, userId);

    // Handle initial state
    wsClient.on('initial_state', (data) => {
      console.log('Initial state:', data);
      if (data.taken_cards) {
        Object.entries(data.taken_cards).forEach(([cardNum, userId]) => {
          addTakenCard(Number(cardNum), userId as number);
        });
      }
    });

    // Handle card selected
    wsClient.on('card_selected', (data) => {
      console.log('Card selected:', data);
      addTakenCard(data.card_number, data.user_id);
    });

    // Handle card available
    wsClient.on('card_available', (data) => {
      console.log('Card available:', data);
      removeTakenCard(data.card_number);
    });

    // Handle timer update
    wsClient.on('timer_update', (data) => {
      console.log('Timer update:', data);
      setTimer(data.seconds);
    });

    // Handle game started
    wsClient.on('game_started', (data) => {
      console.log('Game started:', data);
      if (currentGame) {
        setCurrentGame({ ...currentGame, status: 'active' });
      }
    });

    // Handle number called
    wsClient.on('number_called', (data) => {
      console.log('Number called:', data);
      addCalledNumber(data.number);
      setCurrentNumber(data.number);
    });

    // Handle player won
    wsClient.on('player_won', (data) => {
      console.log('Player won:', data);
      // Handle winner announcement
    });

    // Handle errors
    wsClient.on('error', (data) => {
      console.error('WebSocket error:', data);
    });

    // Cleanup
    return () => {
      wsClient.disconnect();
    };
  }, [gameId, userId]);

  const selectCard = useCallback((cardNumber: number) => {
    wsClient.selectCard(cardNumber);
  }, []);

  const unselectCard = useCallback((cardNumber: number) => {
    wsClient.unselectCard(cardNumber);
  }, []);

  const claimWin = useCallback(() => {
    wsClient.claimWin();
  }, []);

  return {
    selectCard,
    unselectCard,
    claimWin,
    isConnected: wsClient.isConnected(),
  };
}
