import { useEffect, useState } from 'react';
import { telegram, TelegramWebApp } from '@/lib/telegram';

export function useTelegram() {
  const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const app = telegram.getWebApp();
    setWebApp(app);
    setUser(telegram.getUser());
  }, []);

  return {
    webApp,
    user,
    userId: telegram.getUserId(),
    username: telegram.getUsername(),
    firstName: telegram.getFirstName(),
    isAvailable: telegram.isAvailable(),
    showBackButton: telegram.showBackButton.bind(telegram),
    hideBackButton: telegram.hideBackButton.bind(telegram),
    showMainButton: telegram.showMainButton.bind(telegram),
    hideMainButton: telegram.hideMainButton.bind(telegram),
    hapticFeedback: telegram.haptic.bind(telegram),
    hapticNotification: telegram.notify.bind(telegram),
    showAlert: telegram.showAlert.bind(telegram),
    showConfirm: telegram.showConfirm.bind(telegram),
    close: telegram.close.bind(telegram),
    openLink: telegram.openLink.bind(telegram),
  };
}
