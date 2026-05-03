import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AMHABINGO - Telegram Bingo Game",
  description: "Real-time multiplayer bingo game on Telegram",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
      </head>
      <body className="bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 min-h-screen">
        {children}
      </body>
    </html>
  );
}
