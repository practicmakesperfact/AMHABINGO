const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async authenticateUser(initData?: string) {
    const headers: Record<string, string> = {};
    if (initData) {
      headers['X-Telegram-Init-Data'] = initData;
    }
    return this.request('/api/users/auth', {
      method: 'POST',
      headers,
    });
  }

  async getPlatformStats() {
    return this.request('/api/users/stats/platform');
  }

  async getTransactions(initData?: string) {
    const headers: Record<string, string> = {};
    if (initData) {
      headers['X-Telegram-Init-Data'] = initData;
    }
    return this.request('/api/payment/transactions', { headers });
  }

  async getUserHistory(initData?: string) {
    const headers: Record<string, string> = {};
    if (initData) {
      headers['X-Telegram-Init-Data'] = initData;
    }
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

  async getAvailableCards(gameId: string) {
    return this.request(`/api/games/${gameId}/available-cards`);
  }

  async joinGame(gameId: string, cardNumber: number, initData?: string) {
    const headers: Record<string, string> = {};
    if (initData) {
      headers['X-Telegram-Init-Data'] = initData;
    }
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
