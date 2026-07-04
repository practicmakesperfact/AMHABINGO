"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

interface Deposit {
  id: number;
  user_id: number;
  amount: number;
  status: string;
  tx_ref: string;
  payment_method: string;
  receipt_data: any;
  receipt_message: string;
  created_at: string;
  user: {
    telegram_id: number;
    username: string;
    first_name: string;
    phone_number: string;
  };
}

export default function AdminDeposits() {
  const [deposits, setDeposits] = useState<Deposit[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "pending" | "verified" | "approved" | "rejected">("verified");
  const [processing, setProcessing] = useState<number | null>(null);

  useEffect(() => {
    loadDeposits();
  }, [filter]);

  const loadDeposits = async () => {
    setLoading(true);
    try {
      const url = filter === "all" 
        ? `${API_BASE_URL}/api/deposits/pending`
        : `${API_BASE_URL}/api/deposits/pending?status=${filter}`;
      
      const res = await fetch(url);
      const data = await res.json();
      setDeposits(data);
    } catch (error) {
      console.error("Failed to load deposits:", error);
      alert("Failed to load deposits");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (depositId: number) => {
    if (!confirm("Approve this deposit?")) return;

    setProcessing(depositId);
    try {
      const WebApp = (window as any).Telegram?.WebApp;
      const adminTelegramId = WebApp?.initDataUnsafe?.user?.id || 909425014;

      const res = await fetch(`${API_BASE_URL}/api/deposits/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deposit_id: depositId,
          admin_telegram_id: adminTelegramId,
          notes: "Approved via admin panel"
        }),
      });

      if (!res.ok) throw new Error("Approval failed");

      alert("✅ Deposit approved!");
      loadDeposits();
    } catch (error) {
      console.error("Approval error:", error);
      alert("❌ Failed to approve deposit");
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async (depositId: number) => {
    const reason = prompt("Reason for rejection:");
    if (!reason) return;

    setProcessing(depositId);
    try {
      const WebApp = (window as any).Telegram?.WebApp;
      const adminTelegramId = WebApp?.initDataUnsafe?.user?.id || 909425014;

      const res = await fetch(`${API_BASE_URL}/api/deposits/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deposit_id: depositId,
          admin_telegram_id: adminTelegramId,
          reason
        }),
      });

      if (!res.ok) throw new Error("Rejection failed");

      alert("✅ Deposit rejected!");
      loadDeposits();
    } catch (error) {
      console.error("Rejection error:", error);
      alert("❌ Failed to reject deposit");
    } finally {
      setProcessing(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">💰 Deposits</h2>
          <p className="text-white/70">Review and approve deposit requests</p>
        </div>
        <button
          onClick={loadDeposits}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 overflow-x-auto">
        <FilterTab active={filter === "verified"} onClick={() => setFilter("verified")}>
          🔍 Verified ({deposits.filter((d) => d.status === "verified").length})
        </FilterTab>
        <FilterTab active={filter === "pending"} onClick={() => setFilter("pending")}>
          ⏳ Pending
        </FilterTab>
        <FilterTab active={filter === "approved"} onClick={() => setFilter("approved")}>
          ✅ Approved
        </FilterTab>
        <FilterTab active={filter === "rejected"} onClick={() => setFilter("rejected")}>
          ❌ Rejected
        </FilterTab>
        <FilterTab active={filter === "all"} onClick={() => setFilter("all")}>
          📋 All
        </FilterTab>
      </div>

      {/* Deposits Table */}
      {loading ? (
        <div className="text-center text-white py-10">Loading deposits...</div>
      ) : deposits.length === 0 ? (
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-10 text-center border border-white/20">
          <p className="text-white/70 text-lg">No deposits found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {deposits.map((deposit) => (
            <DepositCard
              key={deposit.id}
              deposit={deposit}
              onApprove={() => handleApprove(deposit.id)}
              onReject={() => handleReject(deposit.id)}
              processing={processing === deposit.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function FilterTab({
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
      className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
        active
          ? "bg-white/20 text-white"
          : "bg-white/5 text-white/70 hover:bg-white/10"
      }`}
    >
      {children}
    </button>
  );
}

function DepositCard({
  deposit,
  onApprove,
  onReject,
  processing,
}: {
  deposit: Deposit;
  onApprove: () => void;
  onReject: () => void;
  processing: boolean;
}) {
  const statusColors = {
    pending: "bg-gray-500/20 text-gray-300",
    verified: "bg-yellow-500/20 text-yellow-300",
    approved: "bg-green-500/20 text-green-300",
    rejected: "bg-red-500/20 text-red-300",
  };

  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Left: Deposit Info */}
        <div className="space-y-3 flex-1">
          <div className="flex items-center gap-3">
            <span className="text-2xl">💰</span>
            <div>
              <p className="text-2xl font-bold text-white">{deposit.amount} ETB</p>
              <p className="text-white/70 text-sm">Ref: {deposit.tx_ref}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-white/50">User</p>
              <p className="text-white">
                {deposit.user?.first_name || "Unknown"} (@{deposit.user?.username || "N/A"})
              </p>
              <p className="text-white/70 text-xs">ID: {deposit.user?.telegram_id}</p>
            </div>
            <div>
              <p className="text-white/50">Phone</p>
              <p className="text-white">{deposit.user?.phone_number || "N/A"}</p>
            </div>
            <div>
              <p className="text-white/50">Method</p>
              <p className="text-white capitalize">{deposit.payment_method}</p>
            </div>
            <div>
              <p className="text-white/50">Date</p>
              <p className="text-white">{new Date(deposit.created_at).toLocaleString()}</p>
            </div>
          </div>

          {/* Receipt Data */}
          {deposit.receipt_data && (
            <details className="bg-black/20 rounded-lg p-3">
              <summary className="text-white/70 cursor-pointer text-sm">
                📄 View Receipt Data
              </summary>
              <pre className="text-xs text-white/70 mt-2 overflow-x-auto">
                {JSON.stringify(deposit.receipt_data, null, 2)}
              </pre>
            </details>
          )}

          {deposit.receipt_message && (
            <div className="bg-black/20 rounded-lg p-3">
              <p className="text-white/50 text-xs mb-1">Receipt Message:</p>
              <p className="text-white text-sm">{deposit.receipt_message}</p>
            </div>
          )}
        </div>

        {/* Right: Status & Actions */}
        <div className="flex flex-col items-end gap-3">
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              statusColors[deposit.status as keyof typeof statusColors]
            }`}
          >
            {deposit.status.toUpperCase()}
          </span>

          {deposit.status === "verified" && (
            <div className="flex gap-2">
              <button
                onClick={onApprove}
                disabled={processing}
                className="px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-green-500/50 text-white rounded-lg font-medium transition-colors"
              >
                {processing ? "⏳" : "✅"} Approve
              </button>
              <button
                onClick={onReject}
                disabled={processing}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-red-500/50 text-white rounded-lg font-medium transition-colors"
              >
                {processing ? "⏳" : "❌"} Reject
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
