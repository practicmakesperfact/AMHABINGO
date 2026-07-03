"use client";

import { useEffect } from "react";

export default function RegistrationRequired() {
  useEffect(() => {
    // Try to open Telegram bot
    if (typeof window !== "undefined" && window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp;
      const botUsername = "amhabingo_bot"; // Update with your actual bot username
      
      // Show alert
      tg.showAlert(
        "📋 Registration Required\n\nPlease register via the bot first by clicking 'Register 📋' and sharing your contact.",
        () => {
          // After alert, try to open the bot
          tg.openTelegramLink(`https://t.me/${botUsername}`);
        }
      );
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 flex items-center justify-center p-4">
      <div className="bg-white/10 backdrop-blur-md rounded-3xl p-8 max-w-md text-center border border-white/20">
        <div className="text-6xl mb-6">📋</div>
        
        <h1 className="text-3xl font-bold text-white mb-4">
          Registration Required
        </h1>
        
        <p className="text-white/90 mb-6 leading-relaxed">
          To play AMHABINGO, you need to complete registration via the Telegram bot first.
        </p>
        
        <div className="bg-purple-600/30 rounded-2xl p-6 mb-6 text-left">
          <h2 className="text-white font-bold mb-3 text-lg">How to Register:</h2>
          <ol className="text-white/90 space-y-2 text-sm">
            <li>1️⃣ Open the AMHABINGO bot</li>
            <li>2️⃣ Click <span className="font-bold">"Register 📋"</span></li>
            <li>3️⃣ Share your contact when prompted</li>
            <li>4️⃣ Get <span className="font-bold text-yellow-300">10 ETB</span> welcome bonus!</li>
            <li>5️⃣ Return here and play</li>
          </ol>
        </div>
        
        <a
          href="https://t.me/amhabingo_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-4 rounded-xl font-bold text-lg hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 shadow-lg"
        >
          Open Bot to Register
        </a>
        
        <p className="text-white/60 text-sm mt-4">
          Already registered? Refresh this page after completing bot registration.
        </p>
      </div>
    </div>
  );
}
