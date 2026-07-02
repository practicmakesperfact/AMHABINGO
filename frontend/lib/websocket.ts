// Derive WS URL: explicit env var > auto-convert API URL > localhost fallback
function getWsUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) return process.env.NEXT_PUBLIC_WS_URL;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
  if (apiUrl) {
    // Convert https://host → wss://host, http://host → ws://host
    return apiUrl.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
  }
  return 'ws://127.0.0.1:8000';
}
const WS_URL = getWsUrl();

export type WSMessageType =
  | 'initial_state'
  | 'card_selected'
  | 'card_available'
  | 'timer_update'
  | 'countdown_started'
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
  private maxReconnectAttempts = 8;
  private _manualDisconnect = false;
  private _connectResolver: (() => void) | null = null;
  private _connectRejecter: ((e: Error) => void) | null = null;

  async connect(gameId: string, userId: number): Promise<void> {
    this.gameId = gameId;
    this.userId = userId;
    this._manualDisconnect = false;
    this.reconnectAttempts = 0;

    return this._openConnection();
  }

  private _openConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.gameId || !this.userId) {
        reject(new Error('No gameId/userId'));
        return;
      }

      try {
        const url = `${WS_URL}/api/games/ws/${this.gameId}?user_id=${this.userId}`;
        console.log(`🔌 WebSocket connecting to: ${url}`);
        this.ws = new WebSocket(url);
        this._connectResolver = resolve;
        this._connectRejecter = reject;

        // Connection timeout — if no open event in 10s, fail
        const timeoutId = setTimeout(() => {
          if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
            this.ws.close();
            reject(new Error('WebSocket connection timed out'));
          }
        }, 10_000);

        this.ws.onopen = () => {
          clearTimeout(timeoutId);
          console.log('✅ WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
          this._connectResolver = null;
          this._connectRejecter = null;
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this._handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = () => {
          clearTimeout(timeoutId);
          // onerror is always followed by onclose — let onclose drive reconnect
          if (this._connectRejecter) {
            this._connectRejecter(new Error('WebSocket connection failed'));
            this._connectResolver = null;
            this._connectRejecter = null;
          }
        };

        this.ws.onclose = (event) => {
          clearTimeout(timeoutId);
          console.log(`WebSocket closed: code=${event.code} reason=${event.reason || 'none'}`);
          if (!this._manualDisconnect) {
            this._scheduleReconnect();
          }
        };
      } catch (error: any) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  private _scheduleReconnect(): void {
    if (
      this._manualDisconnect ||
      this.reconnectAttempts >= this.maxReconnectAttempts ||
      !this.gameId ||
      !this.userId
    ) {
      return;
    }

    this.reconnectAttempts++;
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s … capped at 30s
    const delay = Math.min(1000 * 2 ** (this.reconnectAttempts - 1), 30_000);
    console.log(`⏳ WebSocket reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    setTimeout(() => {
      if (!this._manualDisconnect) {
        this._openConnection().catch(() => {
          // If still failing, _scheduleReconnect() will be called again by onclose
        });
      }
    }, delay);
  }

  private _handleMessage(message: any): void {
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
    this.handlers.get(event)?.delete(handler);
  }

  send(type: string, data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    } else {
      console.warn('⚠️ WebSocket not connected — message dropped:', type);
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
    this._manualDisconnect = true;
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

// Singleton instance for pages that share state
export const wsClient = new WebSocketClient();

// Per-page instance management
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
