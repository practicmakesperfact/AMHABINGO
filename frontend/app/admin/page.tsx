"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

interface DashboardStats {
  totalUsers: number;
  activeGames: number;
  pendingDeposits: number;
  pendingWithdrawals: number;
  totalDepositsToday: number;
  totalWithdrawalsToday: number;
  revenueToday: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
    // Refresh every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      // For now, load individual stats
      // In production, create a dedicated /api/admin/stats endpoint
      
      const [depositsRes, withdrawalsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/deposits/pending`),
        fetch(`${API_BASE_URL}/api/withdrawals/pending`),
      ]);

      const deposits = await depositsRes.json();
      const withdrawals = await withdrawalsRes.json();

      setStats({
        totalUsers: 0, // TODO: Add endpoint
        activeGames: 0, // TODO: Add endpoint
        pendingDeposits: deposits.length || 0,
        pendingWithdrawals: withdrawals.length || 0,
        totalDepositsToday: 0, // TODO: Calculate
        totalWithdrawalsToday: 0, // TODO: Calculate
        revenueToday: 0, // TODO: Calculate
      });
    } catch (error) {
      console.error("Failed to load stats:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-white text-xl">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white mb-2">Dashboard</h2>
        <p className="text-white/70">Welcome to AMHABINGO Admin Panel</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Pending Deposits"
          value={stats?.pendingDeposits || 0}
          icon="💰"
          color="yellow"
          link="/admin/deposits"
        />
        <StatCard
          title="Pending Withdrawals"
          value={stats?.pendingWithdrawals || 0}
          icon="🤑"
          color="green"
          link="/admin/withdrawals"
        />
        <StatCard
          title="Total Users"
          value={stats?.totalUsers || 0}
          icon="👥"
          color="blue"
          link="/admin/users"
        />
        <StatCard
          title="Active Games"
          value={stats?.activeGames || 0}
          icon="🎮"
          color="purple"
        />
      </div>

      {/* Today's Activity */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4">📅 Today's Activity</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-white/70 text-sm">Deposits</p>
            <p className="text-2xl font-bold text-green-400">
              {stats?.totalDepositsToday || 0} ETB
            </p>
          </div>
          <div>
            <p className="text-white/70 text-sm">Withdrawals</p>
            <p className="text-2xl font-bold text-red-400">
              {stats?.totalWithdrawalsToday || 0} ETB
            </p>
          </div>
          <div>
            <p className="text-white/70 text-sm">Revenue (20%)</p>
            <p className="text-2xl font-bold text-yellow-400">
              {stats?.revenueToday || 0} ETB
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4">⚡ Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <QuickActionButton href="/admin/deposits" icon="💰" label="Review Deposits" />
          <QuickActionButton href="/admin/withdrawals" icon="🤑" label="Process Withdrawals" />
          <QuickActionButton href="/admin/users" icon="👥" label="Manage Users" />
          <QuickActionButton href="/admin/accounts" icon="🏦" label="Payment Accounts" />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4">📋 Recent Activity</h3>
        <div className="space-y-2 text-white/70 text-sm">
          <p>🕐 System started successfully</p>
          <p>✅ All services operational</p>
          <p>📊 Monitoring active</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
  link,
}: {
  title: string;
  value: number;
  icon: string;
  color: string;
  link?: string;
}) {
  const colorClasses = {
    yellow: "from-yellow-500/20 to-orange-500/20 border-yellow-500/30",
    green: "from-green-500/20 to-emerald-500/20 border-green-500/30",
    blue: "from-blue-500/20 to-cyan-500/20 border-blue-500/30",
    purple: "from-purple-500/20 to-pink-500/20 border-purple-500/30",
  }[color];

  const content = (
    <div
      className={`bg-gradient-to-br ${colorClasses} backdrop-blur-sm rounded-2xl p-6 border ${
        link ? "cursor-pointer hover:scale-105" : ""
      } transition-transform`}
    >
      <div className="flex items-center justify-between mb-2">
        <p className="text-white/70 text-sm">{title}</p>
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );

  if (link) {
    return (
      <a href={link}>
        {content}
      </a>
    );
  }

  return content;
}

function QuickActionButton({
  href,
  icon,
  label,
}: {
  href: string;
  icon: string;
  label: string;
}) {
  return (
    <a
      href={href}
      className="flex items-center space-x-3 px-4 py-3 bg-white/10 hover:bg-white/20 rounded-xl border border-white/20 transition-colors"
    >
      <span className="text-2xl">{icon}</span>
      <span className="text-white font-medium">{label}</span>
    </a>
  );
}
