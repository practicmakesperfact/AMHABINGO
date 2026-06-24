const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000';

export type WSMessageType =
  | 'initial_state'
  | 'card_selected'
  | 'card_available'
  | 'timer_update'
  | 'game_started'
  | 'game_state_update'
  | 'number_called'
  | 'player_won'
  | 'next_game'
  | 'error';

export type WSEventHandler = (data: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private gameId: string | null = null;
  private userId: number | null = null;
  private handlers: Map<WSMessageType, Set<WSEventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;

  async connect(gameId: string, userId: number): Promise<void> {
    this.gameId = gameId;
    this.userId = userId;

    return new Promise((resolve, reject) => {
      try {
        const url = `${WS_URL}/api/games/ws/${gameId}?user_id=${userId}`;
        console.log('Attempting WebSocket connection to:', url);
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected successfully');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error - Backend may not be running on port 8000');
          reject(new Error('WebSocket connection failed'));
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.attemptReconnect();
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  private attemptReconnect(): void {
    if (
      this.reconnectAttempts < this.maxReconnectAttempts &&
      this.gameId &&
      this.userId
    ) {
      this.reconnectAttempts++;
      console.log(
        `⚠️ WebSocket failed - continuing without real-time updates`
      );
      // Don't auto-reconnect to avoid console spam and page blinking
      // User can refresh page to retry connection
    }
  }

  private handleMessage(message: any): void {
    const { type, data } = message;
    const handlers = this.handlers.get(type as WSMessageType);
    if (handlers) {
      handlers.forEach((handler) => handler(data || {}));
    }
  }

  on(event: WSMessageType, handler: WSEventHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
  }

  off(event: WSMessageType, handler: WSEventHandler): void {
    const handlers = this.handlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  send(type: string, data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  selectCard(cardNumber: number): void {
    this.send('select_card', { card_number: cardNumber });
  }

  unselectCard(cardNumber: number): void {
    this.send('unselect_card', { card_number: cardNumber });
  }

  claimWin(): void {
    this.send('claim_win', {});
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.handlers.clear();
    this.gameId = null;
    this.userId = null;
    this.reconnectAttempts = 0;
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const wsClient = new WebSocketClient();

// Helper functions for game pages that need a fresh instance
let gameWsClient: WebSocketClient | null = null;

export function getWsClient(): WebSocketClient {
  if (!gameWsClient) {
    gameWsClient = new WebSocketClient();
  }
  return gameWsClient;
}

export function resetWsClient(): WebSocketClient {
  if (gameWsClient) {
    gameWsClient.disconnect();
  }
  gameWsClient = new WebSocketClient();
  return gameWsClient;
}
