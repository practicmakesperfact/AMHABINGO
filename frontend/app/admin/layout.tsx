"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is admin
    const checkAdmin = async () => {
      try {
        // Get telegram user
        const WebApp = (window as any).Telegram?.WebApp;
        if (!WebApp) {
          // Not in Telegram - redirect
          router.push("/");
          return;
        }

        const user = WebApp.initDataUnsafe?.user;
        if (!user) {
          router.push("/");
          return;
        }

        // Check if user is admin (you can add more admin IDs in config)
        const adminIds = [
          909425014, // Your telegram ID
          // Add more admin IDs here
        ];

        if (!adminIds.includes(user.id)) {
          alert("❌ Admin access required!");
          router.push("/");
          return;
        }

        setIsAuthorized(true);
      } catch (error) {
        console.error("Admin check error:", error);
        router.push("/");
      } finally {
        setIsLoading(false);
      }
    };

    checkAdmin();
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">🔐 Checking admin access...</div>
      </div>
    );
  }

  if (!isAuthorized) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Admin Header */}
      <header className="bg-black/30 backdrop-blur-sm border-b border-white/10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">
              🛡️ Admin Panel
            </h1>
            <Link
              href="/"
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
            >
              ← Back to Game
            </Link>
          </div>
        </div>
      </header>

      {/* Admin Navigation */}
      <nav className="bg-black/20 backdrop-blur-sm border-b border-white/10">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1 overflow-x-auto">
            <NavLink href="/admin">📊 Dashboard</NavLink>
            <NavLink href="/admin/deposits">💰 Deposits</NavLink>
            <NavLink href="/admin/withdrawals">🤑 Withdrawals</NavLink>
            <NavLink href="/admin/users">👥 Users</NavLink>
            <NavLink href="/admin/accounts">🏦 Payment Accounts</NavLink>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="container mx-auto px-4 py-6">{children}</main>
    </div>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-4 py-3 text-white/70 hover:text-white hover:bg-white/10 transition-colors whitespace-nowrap"
    >
      {children}
    </Link>
  );
}
