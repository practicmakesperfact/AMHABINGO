const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// How long to wait for a single request before giving up (ms)
const REQUEST_TIMEOUT_MS = 15_000;

// Max number of retry attempts for failed requests
const MAX_RETRIES = 3;

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Core request method with:
   * - Configurable timeout (AbortController)
   * - Exponential-backoff retry for network errors / 5xx
   * - Clear error messages for wake-up UX
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries = MAX_RETRIES,
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    for (let attempt = 0; attempt <= retries; attempt++) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

      try {
        const response = await fetch(url, {
          ...options,
          headers,
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: 'Request failed' }));
          // 4xx errors are client errors — don't retry
          if (response.status >= 400 && response.status < 500) {
            throw new Error(error.detail || `HTTP ${response.status}`);
          }
          // 5xx — retryable
          if (attempt < retries) {
            await this._sleep(500 * 2 ** attempt); // 500ms, 1s, 2s
            continue;
          }
          throw new Error(error.detail || `Server error ${response.status}`);
        }

        return response.json();
      } catch (err: any) {
        clearTimeout(timeoutId);

        // Abort = timeout
        if (err.name === 'AbortError') {
          if (attempt < retries) {
            console.warn(`⏱ Request timed out (attempt ${attempt + 1}/${retries + 1}), retrying...`);
            await this._sleep(1000 * 2 ** attempt);
            continue;
          }
          throw new Error('Backend is starting up — please wait a moment and retry.');
        }

        // Network error (Failed to fetch / CORS blocked / server asleep)
        if (err instanceof TypeError && err.message.includes('fetch')) {
          if (attempt < retries) {
            console.warn(`🌐 Network error (attempt ${attempt + 1}/${retries + 1}), retrying...`);
            await this._sleep(1500 * 2 ** attempt);
            continue;
          }
          throw new Error(
            'Cannot reach the server. It may be waking up from sleep — please wait 30 seconds and try again.',
          );
        }

        // Known errors (4xx) — rethrow immediately
        throw err;
      }
    }

    throw new Error('Request failed after retries');
  }

  private _sleep(ms: number): Promise<void> {
    return new Promise((r) => setTimeout(r, ms));
  }

  /**
   * Lightweight health probe — used to detect when Render has woken up.
   * Returns true if the server is reachable, false otherwise (never throws).
   */
  ping = async (): Promise<boolean> => {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(`${this.baseUrl}/ping`, { signal: controller.signal });
      clearTimeout(id);
      return res.ok;
    } catch {
      return false;
    }
  }

  /**
   * Wait for the backend to wake up (Render free plan can sleep 15+ min).
   * Polls /ping every 3 seconds for up to 60 seconds.
   * Calls onWaiting(seconds) each poll so the UI can show a countdown.
   */
  waitForBackend = async (
    onWaiting?: (secondsElapsed: number) => void,
    timeoutMs = 60_000,
  ): Promise<boolean> => {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const ok = await this.ping();
      if (ok) return true;
      onWaiting?.(Math.round((Date.now() - start) / 1000));
      await this._sleep(3000);
    }
    return false;
  }

  async authenticateUser(initData?: string) {
    const headers: Record<string, string> = {};
    if (initData) headers['X-Telegram-Init-Data'] = initData;
    
    try {
      return await this.request('/api/users/auth', { method: 'POST', headers });
    } catch (error: any) {
      // Check if it's a registration required error
      if (error.message?.includes('registration_required')) {
        throw new Error('REGISTRATION_REQUIRED');
      }
      throw error;
    }
  }

  async getPlatformStats() {
    return this.request('/api/users/stats/platform');
  }

  async getTransactions(initData?: string) {
    const headers: Record<string, string> = {};
    if (initData) headers['X-Telegram-Init-Data'] = initData;
    return this.request('/api/payment/transactions', { headers });
  }

  async getUserHistory(initData?: string) {
    const headers: Record<string, string> = {};
    if (initData) headers['X-Telegram-Init-Data'] = initData;
    return this.request('/api/users/history', { headers });
  }

  async listGames(status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request(`/api/games/${params}`);
  }

  async createGame(difficulty: string, entryFee: number) {
    return this.request('/api/games/', {
      method: 'POST',
      body: JSON.stringify({ room: difficulty, entry_fee: entryFee }),
    });
  }

  async getGame(gameId: string) {
    return this.request(`/api/games/${gameId}`);
  }

  /** Lightweight — only returns taken card IDs */
  async getCardsStatus(gameId: string) {
    return this.request(`/api/games/${gameId}/cards-status`);
  }

  /** Full list — use getCardsStatus() for performance */
  async getAvailableCards(gameId: string) {
    return this.request(`/api/games/${gameId}/available-cards`);
  }

  async joinGame(gameId: string, cardNumber: number, initData?: string) {
    const headers: Record<string, string> = {};
    if (initData) headers['X-Telegram-Init-Data'] = initData;
    return this.request(`/api/games/${gameId}/join`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ card_number: cardNumber }),
    });
  }

  async getPlayerCard(gameId: string, userId: number) {
    return this.request(`/api/games/${gameId}/player/${userId}/card`);
  }
}

export const api = new ApiClient(API_URL);
