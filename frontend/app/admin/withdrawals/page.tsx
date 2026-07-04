"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

interface Withdrawal {
  id: number;
  user_id: number;
  amount: number;
  status: string;
  tx_ref: string;
  phone_number: string;
  payment_method: string;
  payment_proof: string;
  admin_notes: string;
  created_at: string;
  reviewed_at: string;
  completed_at: string;
  user: {
    telegram_id: number;
    username: string;
    first_name: string;
    phone_number: string;
    balance: number;
  };
}

export default function AdminWithdrawals() {
  const [withdrawals, setWithdrawals] = useState<Withdrawal[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"pending" | "approved" | "rejected" | "completed" | "all">("pending");
  const [processing, setProcessing] = useState<number | null>(null);

  useEffect(() => {
    loadWithdrawals();
  }, [filter]);

  const loadWithdrawals = async () => {
    setLoading(true);
    try {
      const url = filter === "all" 
        ? `${API_BASE_URL}/api/withdrawals/pending`
        : `${API_BASE_URL}/api/withdrawals/pending?status=${filter}`;
      
      const res = await fetch(url);
      const data = await res.json();
      setWithdrawals(data);
    } catch (error) {
      console.error("Failed to load withdrawals:", error);
      alert("Failed to load withdrawals");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (withdrawalId: number) => {
    if (!confirm("Approve this withdrawal? Make sure you've sent the money via Telebirr.")) return;

    const notes = prompt("Add notes (optional - e.g., Telebirr TX ID):");

    setProcessing(withdrawalId);
    try {
      const WebApp = (window as any).Telegram?.WebApp;
      const adminTelegramId = WebApp?.initDataUnsafe?.user?.id || 909425014;

      const res = await fetch(`${API_BASE_URL}/api/withdrawals/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          withdrawal_id: withdrawalId,
          admin_telegram_id: adminTelegramId,
          notes: notes || "Approved via admin panel"
        }),
      });

      if (!res.ok) throw new Error("Approval failed");

      alert("✅ Withdrawal approved! Remember to mark as completed after sending money.");
      loadWithdrawals();
    } catch (error) {
      console.error("Approval error:", error);
      alert("❌ Failed to approve withdrawal");
    } finally {
      setProcessing(null);
    }
  };

  const handleComplete = async (withdrawalId: number) => {
    const paymentProof = prompt("Enter Telebirr transaction ID or proof:");
    if (!paymentProof) return;

    setProcessing(withdrawalId);
    try {
      const WebApp = (window as any).Telegram?.WebApp;
      const adminTelegramId = WebApp?.initDataUnsafe?.user?.id || 909425014;

      const res = await fetch(`${API_BASE_URL}/api/withdrawals/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          withdrawal_id: withdrawalId,
          admin_telegram_id: adminTelegramId,
          payment_proof: paymentProof
        }),
      });

      if (!res.ok) throw new Error("Completion failed");

      alert("✅ Withdrawal marked as completed!");
      loadWithdrawals();
    } catch (error) {
      console.error("Completion error:", error);
      alert("❌ Failed to complete withdrawal");
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async (withdrawalId: number) => {
    const reason = prompt("Reason for rejection (user will be refunded):");
    if (!reason) return;

    setProcessing(withdrawalId);
    try {
      const WebApp = (window as any).Telegram?.WebApp;
      const adminTelegramId = WebApp?.initDataUnsafe?.user?.id || 909425014;

      const res = await fetch(`${API_BASE_URL}/api/withdrawals/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          withdrawal_id: withdrawalId,
          admin_telegram_id: adminTelegramId,
          reason
        }),
      });

      if (!res.ok) throw new Error("Rejection failed");

      alert("✅ Withdrawal rejected! User balance has been refunded.");
      loadWithdrawals();
    } catch (error) {
      console.error("Rejection error:", error);
      alert("❌ Failed to reject withdrawal");
    } finally {
      setProcessing(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">🤑 Withdrawals</h2>
          <p className="text-white/70">Process withdrawal requests</p>
        </div>
        <button
          onClick={loadWithdrawals}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 overflow-x-auto">
        <FilterTab active={filter === "pending"} onClick={() => setFilter("pending")}>
          ⏳ Pending ({withdrawals.filter((w) => w.status === "pending").length})
        </FilterTab>
        <FilterTab active={filter === "approved"} onClick={() => setFilter("approved")}>
          ✅ Approved
        </FilterTab>
        <FilterTab active={filter === "completed"} onClick={() => setFilter("completed")}>
          🎉 Completed
        </FilterTab>
        <FilterTab active={filter === "rejected"} onClick={() => setFilter("rejected")}>
          ❌ Rejected
        </FilterTab>
        <FilterTab active={filter === "all"} onClick={() => setFilter("all")}>
          📋 All
        </FilterTab>
      </div>

      {/* Withdrawals Table */}
      {loading ? (
        <div className="text-center text-white py-10">Loading withdrawals...</div>
      ) : withdrawals.length === 0 ? (
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-10 text-center border border-white/20">
          <p className="text-white/70 text-lg">No withdrawals found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {withdrawals.map((withdrawal) => (
            <WithdrawalCard
              key={withdrawal.id}
              withdrawal={withdrawal}
              onApprove={() => handleApprove(withdrawal.id)}
              onComplete={() => handleComplete(withdrawal.id)}
              onReject={() => handleReject(withdrawal.id)}
              processing={processing === withdrawal.id}
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

function WithdrawalCard({
  withdrawal,
  onApprove,
  onComplete,
  onReject,
  processing,
}: {
  withdrawal: Withdrawal;
  onApprove: () => void;
  onComplete: () => void;
  onReject: () => void;
  processing: boolean;
}) {
  const statusColors = {
    pending: "bg-yellow-500/20 text-yellow-300",
    approved: "bg-green-500/20 text-green-300",
    rejected: "bg-red-500/20 text-red-300",
    completed: "bg-blue-500/20 text-blue-300",
  };

  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Left: Withdrawal Info */}
        <div className="space-y-3 flex-1">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🤑</span>
            <div>
              <p className="text-2xl font-bold text-white">{withdrawal.amount} ETB</p>
              <p className="text-white/70 text-sm">Ref: {withdrawal.tx_ref}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-white/50">User</p>
              <p className="text-white">
                {withdrawal.user?.first_name || "Unknown"} (@{withdrawal.user?.username || "N/A"})
              </p>
              <p className="text-white/70 text-xs">ID: {withdrawal.user?.telegram_id}</p>
            </div>
            <div>
              <p className="text-white/50">User Balance</p>
              <p className="text-white">{withdrawal.user?.balance?.toFixed(2) || "N/A"} ETB</p>
              <p className="text-white/70 text-xs">
                ⚠️ Balance already deducted (held)
              </p>
            </div>
            <div>
              <p className="text-white/50">Withdrawal Phone</p>
              <p className="text-white font-mono">{withdrawal.phone_number}</p>
            </div>
            <div>
              <p className="text-white/50">Method</p>
              <p className="text-white capitalize">{withdrawal.payment_method}</p>
            </div>
            <div>
              <p className="text-white/50">Requested</p>
              <p className="text-white">{new Date(withdrawal.created_at).toLocaleString()}</p>
            </div>
            {withdrawal.reviewed_at && (
              <div>
                <p className="text-white/50">Reviewed</p>
                <p className="text-white">{new Date(withdrawal.reviewed_at).toLocaleString()}</p>
              </div>
            )}
          </div>

          {/* Admin Notes */}
          {withdrawal.admin_notes && (
            <div className="bg-black/20 rounded-lg p-3">
              <p className="text-white/50 text-xs mb-1">Admin Notes:</p>
              <p className="text-white text-sm">{withdrawal.admin_notes}</p>
            </div>
          )}

          {/* Payment Proof */}
          {withdrawal.payment_proof && (
            <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/30">
              <p className="text-green-300 text-xs mb-1">Payment Proof:</p>
              <p className="text-white text-sm font-mono">{withdrawal.payment_proof}</p>
            </div>
          )}

          {/* Instructions */}
          {withdrawal.status === "pending" && (
            <div className="bg-yellow-500/10 rounded-lg p-3 border border-yellow-500/30">
              <p className="text-yellow-300 text-sm font-medium mb-2">
                📋 Instructions:
              </p>
              <ol className="text-white/70 text-xs space-y-1 list-decimal list-inside">
                <li>Open Telebirr app</li>
                <li>Send {withdrawal.amount} ETB to {withdrawal.phone_number}</li>
                <li>Click "Approve" and enter the Telebirr TX ID</li>
                <li>After confirming money sent, click "Complete"</li>
              </ol>
            </div>
          )}
        </div>

        {/* Right: Status & Actions */}
        <div className="flex flex-col items-end gap-3">
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              statusColors[withdrawal.status as keyof typeof statusColors]
            }`}
          >
            {withdrawal.status.toUpperCase()}
          </span>

          {withdrawal.status === "pending" && (
            <div className="flex flex-col gap-2">
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
                {processing ? "⏳" : "❌"} Reject & Refund
              </button>
            </div>
          )}

          {withdrawal.status === "approved" && (
            <button
              onClick={onComplete}
              disabled={processing}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 text-white rounded-lg font-medium transition-colors"
            >
              {processing ? "⏳" : "🎉"} Mark Completed
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
