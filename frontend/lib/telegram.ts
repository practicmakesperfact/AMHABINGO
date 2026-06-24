

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
      language_code?: string;
      is_premium?: boolean;
    };
    start_param?: string;
  };
  version: string;
  platform: string;
  colorScheme: 'light' | 'dark';
  themeParams: Record<string, string>;
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  headerColor: string;
  backgroundColor: string;

  BackButton: {
    show: () => void;
    hide: () => void;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
  };

  MainButton: {
    text: string;
    color: string;
    textColor: string;
    isVisible: boolean;
    isActive: boolean;

    setText: (text: string) => void;
    show: () => void;
    hide: () => void;
    enable: () => void;
    disable: () => void;

    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;

    showProgress: (leaveActive?: boolean) => void;
    hideProgress: () => void;

    setParams: (params: Record<string, any>) => void;
  };

  HapticFeedback: {
    impactOccurred: (
      style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'
    ) => void;
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
    selectionChanged: () => void;
  };

  close: () => void;
  ready: () => void;
  expand: () => void;

  showAlert: (message: string, callback?: () => void) => void;
  showConfirm: (
    message: string,
    callback?: (confirmed: boolean) => void
  ) => void;

  openLink: (url: string) => void;
  openTelegramLink: (url: string) => void;

  sendData: (data: string) => void;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

class TelegramHelper {
  public getWebApp(): TelegramWebApp | null {
    if (typeof window === 'undefined') return null;
    return window.Telegram?.WebApp || null;
  }

  isAvailable(): boolean {
    return typeof window !== 'undefined' && !!window.Telegram?.WebApp;
  }

  isTelegram(): boolean {
    return this.isAvailable();
  }

  // ---------------- USER ----------------

  getUser() {
    return this.getWebApp()?.initDataUnsafe?.user || null;
  }

  getUserId(): number | null {
    return this.getUser()?.id || null;
  }

  getUsername(): string | null {
    return this.getUser()?.username || null;
  }

  getFirstName(): string | null {
    return this.getUser()?.first_name || null;
  }

  // ---------------- LIFECYCLE ----------------

  ready() {
    this.getWebApp()?.ready();
  }

  expand() {
    this.getWebApp()?.expand();
  }

  close() {
    this.getWebApp()?.close();
  }

  // ---------------- BACK BUTTON ----------------

  showBackButton(callback?: () => void) {
    const webApp = this.getWebApp();
    if (!webApp?.BackButton) return;

    webApp.BackButton.show();

    if (callback) {
      webApp.BackButton.onClick(callback);
    }
  }

  hideBackButton() {
    this.getWebApp()?.BackButton?.hide();
  }

  // ---------------- MAIN BUTTON ----------------

  showMainButton(text: string, callback: () => void) {
    const webApp = this.getWebApp();
    if (!webApp?.MainButton) return;

    webApp.MainButton.setText(text);
    webApp.MainButton.show();

    // prevent duplicate stacking by clearing old listeners safely
    if (webApp.MainButton.offClick) {
      webApp.MainButton.offClick(() => {});
    }

    webApp.MainButton.onClick(callback);
  }

  hideMainButton() {
    this.getWebApp()?.MainButton?.hide();
  }

  enableMainButton() {
    this.getWebApp()?.MainButton?.enable();
  }

  disableMainButton() {
    this.getWebApp()?.MainButton?.disable();
  }

  setMainButtonLoading(loading: boolean) {
    const btn = this.getWebApp()?.MainButton;
    if (!btn) return;

    if (loading) btn.showProgress();
    else btn.hideProgress();
  }

  // ---------------- HAPTIC FEEDBACK ----------------

  haptic(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') {
    this.getWebApp()?.HapticFeedback?.impactOccurred(style);
  }

  notify(type: 'error' | 'success' | 'warning') {
    this.getWebApp()?.HapticFeedback?.notificationOccurred(type);
  }

  selectionChanged() {
    this.getWebApp()?.HapticFeedback?.selectionChanged();
  }

  // ---------------- DIALOGS ----------------

  showAlert(message: string, callback?: () => void) {
    this.getWebApp()?.showAlert(message, callback);
  }

  showConfirm(message: string, callback?: (confirmed: boolean) => void) {
    this.getWebApp()?.showConfirm(message, callback);
  }

  // ---------------- LINKS ----------------

  openLink(url: string) {
    this.getWebApp()?.openLink(url);
  }

  openTelegramLink(url: string) {
    this.getWebApp()?.openTelegramLink(url);
  }

  // ---------------- DATA ----------------

  sendData(data: string) {
    this.getWebApp()?.sendData(data);
  }

  // ---------------- THEME ----------------

  getTheme() {
    const webApp = this.getWebApp();
    return {
      colorScheme: webApp?.colorScheme,
      themeParams: webApp?.themeParams,
      backgroundColor: webApp?.backgroundColor,
      headerColor: webApp?.headerColor,
    };
  }
}

export const telegram = new TelegramHelper();