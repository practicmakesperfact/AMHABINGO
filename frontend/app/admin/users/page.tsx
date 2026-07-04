"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

interface User {
  id: number;
  telegram_id: number;
  username: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  balance: number;
  play_balance: number;
  coins: number;
  wins: number;
  games_played: number;
  created_at: string;
}

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<"balance" | "wins" | "created">("balance");

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      // In production, create /api/users/all endpoint for admin
      // For now, we'll use leaderboard as proxy
      const res = await fetch(`${API_BASE_URL}/api/users/leaderboard?limit=100`);
      const data = await res.json();
      
      // Transform leaderboard data to user format
      // In production, fetch full user details
      setUsers(data.map((item: any) => ({
        id: item.user_id,
        telegram_id: 0,
        username: item.username,
        balance: item.total_earnings || 0,
        wins: item.total_wins || 0,
        games_played: 0,
        coins: 0,
        play_balance: 0,
        created_at: new Date().toISOString(),
      })));
    } catch (error) {
      console.error("Failed to load users:", error);
      alert("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users
    .filter((user) => {
      const search = searchTerm.toLowerCase();
      return (
        user.username?.toLowerCase().includes(search) ||
        user.first_name?.toLowerCase().includes(search) ||
        user.telegram_id?.toString().includes(search)
      );
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "balance":
          return b.balance - a.balance;
        case "wins":
          return b.wins - a.wins;
        case "created":
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        default:
          return 0;
      }
    });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">👥 Users</h2>
          <p className="text-white/70">Manage users and view statistics</p>
        </div>
        <button
          onClick={loadUsers}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Users" value={users.length} icon="👥" />
        <StatCard
          title="Total Balance"
          value={`${users.reduce((sum, u) => sum + u.balance, 0).toFixed(0)} ETB`}
          icon="💰"
        />
        <StatCard
          title="Total Wins"
          value={users.reduce((sum, u) => sum + u.wins, 0)}
          icon="🏆"
        />
        <StatCard
          title="Total Games"
          value={users.reduce((sum, u) => sum + u.games_played, 0)}
          icon="🎮"
        />
      </div>

      {/* Search and Sort */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="🔍 Search by username, name, or telegram ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
            />
          </div>
          <div className="flex gap-2">
            <SortButton
              active={sortBy === "balance"}
              onClick={() => setSortBy("balance")}
            >
              💰 Balance
            </SortButton>
            <SortButton active={sortBy === "wins"} onClick={() => setSortBy("wins")}>
              🏆 Wins
            </SortButton>
            <SortButton
              active={sortBy === "created"}
              onClick={() => setSortBy("created")}
            >
              📅 Newest
            </SortButton>
          </div>
        </div>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="text-center text-white py-10">Loading users...</div>
      ) : filteredUsers.length === 0 ? (
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-10 text-center border border-white/20">
          <p className="text-white/70 text-lg">No users found</p>
        </div>
      ) : (
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl border border-white/20 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-black/30">
                <tr>
                  <th className="px-4 py-3 text-left text-white/70 text-sm font-medium">
                    User
                  </th>
                  <th className="px-4 py-3 text-left text-white/70 text-sm font-medium">
                    Balance
                  </th>
                  <th className="px-4 py-3 text-left text-white/70 text-sm font-medium">
                    Play Balance
                  </th>
                  <th className="px-4 py-3 text-left text-white/70 text-sm font-medium">
                    Coins
                  </th>
                  <th className="px-4 py-3 text-left text-white/70 text-sm font-medium">
                    Stats
                  </th>
                  <th className="px-4 py-3 text-left text-white/70 text-sm font-medium">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {filteredUsers.map((user) => (
                  <UserRow key={user.id} user={user} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination Info */}
      <div className="text-center text-white/70 text-sm">
        Showing {filteredUsers.length} of {users.length} users
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string | number;
  icon: string;
}) {
  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
      <div className="flex items-center justify-between mb-2">
        <p className="text-white/70 text-sm">{title}</p>
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

function SortButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap text-sm ${
        active
          ? "bg-white/20 text-white"
          : "bg-white/5 text-white/70 hover:bg-white/10"
      }`}
    >
      {children}
    </button>
  );
}

function UserRow({ user }: { user: User }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <>
      <tr className="hover:bg-white/5 transition-colors">
        <td className="px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
              {user.username?.[0]?.toUpperCase() || user.first_name?.[0]?.toUpperCase() || "U"}
            </div>
            <div>
              <p className="text-white font-medium">
                {user.first_name || "Unknown"} {user.last_name || ""}
              </p>
              <p className="text-white/50 text-sm">@{user.username || "N/A"}</p>
              {user.telegram_id > 0 && (
                <p className="text-white/30 text-xs">ID: {user.telegram_id}</p>
              )}
            </div>
          </div>
        </td>
        <td className="px-4 py-3">
          <p className="text-white font-mono">{user.balance.toFixed(2)} ETB</p>
        </td>
        <td className="px-4 py-3">
          <p className="text-white/70 font-mono">{user.play_balance?.toFixed(2) || "0.00"} ETB</p>
        </td>
        <td className="px-4 py-3">
          <p className="text-yellow-400 font-mono">{user.coins || 0} 🪙</p>
        </td>
        <td className="px-4 py-3">
          <div className="text-sm">
            <p className="text-white">
              🏆 {user.wins} wins
            </p>
            <p className="text-white/70">
              🎮 {user.games_played} games
            </p>
          </div>
        </td>
        <td className="px-4 py-3">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm transition-colors"
          >
            {showDetails ? "Hide" : "Details"}
          </button>
        </td>
      </tr>
      {showDetails && (
        <tr>
          <td colSpan={6} className="px-4 py-3 bg-black/20">
            <div className="space-y-2 text-sm">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-white/50">Phone</p>
                  <p className="text-white">{user.phone_number || "N/A"}</p>
                </div>
                <div>
                  <p className="text-white/50">Telegram ID</p>
                  <p className="text-white font-mono">{user.telegram_id || "N/A"}</p>
                </div>
                <div>
                  <p className="text-white/50">Win Rate</p>
                  <p className="text-white">
                    {user.games_played > 0
                      ? ((user.wins / user.games_played) * 100).toFixed(1)
                      : 0}
                    %
                  </p>
                </div>
                <div>
                  <p className="text-white/50">Joined</p>
                  <p className="text-white">
                    {new Date(user.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button className="px-3 py-1 bg-blue-500 hover:bg-blue-600 rounded text-white text-sm">
                  View Transactions
                </button>
                <button className="px-3 py-1 bg-green-500 hover:bg-green-600 rounded text-white text-sm">
                  View Games
                </button>
                <button className="px-3 py-1 bg-purple-500 hover:bg-purple-600 rounded text-white text-sm">
                  Send Notification
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
