import { create } from 'zustand';

interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  balance: number;
  wins: number;
  games_played: number;
}

interface Game {
  id: number;
  game_id: string;
  status: 'waiting' | 'countdown' | 'active' | 'finished';
  room: string;
  entry_fee: number;
  prize_pool: number;
  total_players: number;
  max_players: number;
  called_numbers: number[];
  current_number: number | null;
  winner_ids: number[];
  countdown_seconds: number;
}

interface Player {
  id: number;
  user_id: number;
  game_id: number;
  card_number: number;
  card_data: number[][];
  marked_numbers: number[];
  has_won: boolean;
  winning_pattern: string | null;
}

interface GameStore {
  // User state
  user: User | null;
  setUser: (user: User | null) => void;

  // Game state
  currentGame: Game | null;
  setCurrentGame: (game: Game | null) => void;

  // Player state
  currentPlayer: Player | null;
  setCurrentPlayer: (player: Player | null) => void;

  // Card selection state
  selectedCardNumber: number | null;
  setSelectedCardNumber: (cardNumber: number | null) => void;
  takenCards: Record<number, number>; // cardNumber -> userId
  setTakenCards: (cards: Record<number, number>) => void;
  addTakenCard: (cardNumber: number, userId: number) => void;
  removeTakenCard: (cardNumber: number) => void;

  // Game play state
  timer: number;
  setTimer: (seconds: number) => void;
  calledNumbers: number[];
  setCalledNumbers: (numbers: number[]) => void;
  addCalledNumber: (number: number) => void;
  currentNumber: number | null;
  setCurrentNumber: (number: number | null) => void;

  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;

  // Actions
  reset: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  // Initial state
  user: null,
  currentGame: null,
  currentPlayer: null,
  selectedCardNumber: null,
  takenCards: {},
  timer: 0,
  calledNumbers: [],
  currentNumber: null,
  isLoading: false,
  error: null,

  // Setters
  setUser: (user) => set({ user }),
  setCurrentGame: (currentGame) => set({ currentGame }),
  setCurrentPlayer: (currentPlayer) => set({ currentPlayer }),
  setSelectedCardNumber: (selectedCardNumber) => set({ selectedCardNumber }),
  setTakenCards: (takenCards) => set({ takenCards }),
  addTakenCard: (cardNumber, userId) =>
    set((state) => ({
      takenCards: { ...state.takenCards, [cardNumber]: userId },
    })),
  removeTakenCard: (cardNumber) =>
    set((state) => {
      const newTakenCards = { ...state.takenCards };
      delete newTakenCards[cardNumber];
      return { takenCards: newTakenCards };
    }),
  setTimer: (timer) => set({ timer }),
  setCalledNumbers: (calledNumbers) => set({ calledNumbers }),
  addCalledNumber: (number) =>
    set((state) => ({
      calledNumbers: [...state.calledNumbers, number],
    })),
  setCurrentNumber: (currentNumber) => set({ currentNumber }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  // Reset
  reset: () =>
    set({
      currentGame: null,
      currentPlayer: null,
      selectedCardNumber: null,
      takenCards: {},
      timer: 0,
      calledNumbers: [],
      currentNumber: null,
      isLoading: false,
      error: null,
    }),
}));
