"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

interface PaymentAccount {
  id: number;
  account_name: string;
  account_holder: string;
  phone_number: string;
  payment_method: string;
  is_active: boolean;
  priority: number;
  daily_limit: number;
  notes: string;
}

export default function AdminPaymentAccounts() {
  const [accounts, setAccounts] = useState<PaymentAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/payment-accounts?active_only=false`);
      const data = await res.json();
      setAccounts(data);
    } catch (error) {
      console.error("Failed to load accounts:", error);
      alert("Failed to load payment accounts");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (accountId: number, currentStatus: boolean) => {
    try {
      const WebApp = (window as any).Telegram?.WebApp;
      const adminTelegramId = WebApp?.initDataUnsafe?.user?.id || 909425014;

      const res = await fetch(
        `${API_BASE_URL}/api/payment-accounts/${accountId}?admin_telegram_id=${adminTelegramId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            is_active: !currentStatus,
          }),
        }
      );

      if (!res.ok) throw new Error("Update failed");

      alert(currentStatus ? "❌ Account deactivated" : "✅ Account activated");
      loadAccounts();
    } catch (error) {
      console.error("Toggle error:", error);
      alert("Failed to update account status");
    }
  };

  const handleDelete = async (accountId: number) => {
    if (!confirm("Delete this payment account? This cannot be undone.")) return;

    try {
      const WebApp = (window as any).Telegram?.WebApp;
      const adminTelegramId = WebApp?.initDataUnsafe?.user?.id || 909425014;

      const res = await fetch(
        `${API_BASE_URL}/api/payment-accounts/${accountId}?admin_telegram_id=${adminTelegramId}`,
        {
          method: "DELETE",
        }
      );

      if (!res.ok) throw new Error("Delete failed");

      alert("✅ Account deleted");
      loadAccounts();
    } catch (error) {
      console.error("Delete error:", error);
      alert("Failed to delete account");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">🏦 Payment Accounts</h2>
          <p className="text-white/70">Manage Telebirr accounts for deposits</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadAccounts}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg text-white font-medium transition-colors"
          >
            {showAddForm ? "✕ Cancel" : "+ Add Account"}
          </button>
        </div>
      </div>

      {/* Add Account Form */}
      {showAddForm && (
        <AddAccountForm
          onSuccess={() => {
            setShowAddForm(false);
            loadAccounts();
          }}
        />
      )}

      {/* Accounts List */}
      {loading ? (
        <div className="text-center text-white py-10">Loading accounts...</div>
      ) : accounts.length === 0 ? (
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-10 text-center border border-white/20">
          <p className="text-white/70 text-lg">No payment accounts found</p>
          <p className="text-white/50 text-sm mt-2">Add your first account to start accepting deposits</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {accounts.map((account) => (
            <AccountCard
              key={account.id}
              account={account}
              onToggleActive={() => handleToggleActive(account.id, account.is_active)}
              onDelete={() => handleDelete(account.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function AccountCard({
  account,
  onToggleActive,
  onDelete,
}: {
  account: PaymentAccount;
  onToggleActive: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      className={`bg-white/10 backdrop-blur-sm rounded-2xl p-6 border transition-all ${
        account.is_active
          ? "border-green-500/30 shadow-lg shadow-green-500/10"
          : "border-white/20 opacity-60"
      }`}
    >
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Left: Account Info */}
        <div className="space-y-3 flex-1">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🏦</span>
            <div>
              <h3 className="text-xl font-bold text-white">{account.account_name}</h3>
              <p className="text-white/70 text-sm">{account.account_holder}</p>
            </div>
            {account.is_active && (
              <span className="ml-2 px-2 py-1 bg-green-500/20 text-green-300 rounded-full text-xs font-medium">
                Active
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div>
              <p className="text-white/50">Phone Number</p>
              <p className="text-white font-mono text-lg">{account.phone_number}</p>
            </div>
            <div>
              <p className="text-white/50">Payment Method</p>
              <p className="text-white capitalize">{account.payment_method}</p>
            </div>
            <div>
              <p className="text-white/50">Daily Limit</p>
              <p className="text-white">
                {account.daily_limit ? `${account.daily_limit.toLocaleString()} ETB` : "Unlimited"}
              </p>
            </div>
          </div>

          {account.notes && (
            <div className="bg-black/20 rounded-lg p-3">
              <p className="text-white/50 text-xs mb-1">Notes:</p>
              <p className="text-white text-sm">{account.notes}</p>
            </div>
          )}

          <div className="flex items-center gap-4 text-xs text-white/50">
            <span>Priority: {account.priority}</span>
            <span>ID: {account.id}</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex flex-col gap-2">
          <button
            onClick={onToggleActive}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              account.is_active
                ? "bg-yellow-500 hover:bg-yellow-600 text-white"
                : "bg-green-500 hover:bg-green-600 text-white"
            }`}
          >
            {account.is_active ? "🔴 Deactivate" : "🟢 Activate"}
          </button>
          <button
            onClick={onDelete}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg text-white font-medium transition-colors"
          >
            🗑️ Delete
          </button>
        </div>
      </div>
    </div>
  );
}

function AddAccountForm({ onSuccess }: { onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    account_name: "",
    account_holder: "",
    phone_number: "",
    payment_method: "telebirr",
    priority: 1,
    daily_limit: 100000,
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const WebApp = (window as any).Telegram?.WebApp;
      const adminTelegramId = WebApp?.initDataUnsafe?.user?.id || 909425014;

      const res = await fetch(
        `${API_BASE_URL}/api/payment-accounts?admin_telegram_id=${adminTelegramId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...formData,
            is_active: true,
          }),
        }
      );

      if (!res.ok) throw new Error("Failed to create account");

      alert("✅ Payment account created successfully!");
      onSuccess();
    } catch (error) {
      console.error("Create error:", error);
      alert("❌ Failed to create payment account");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 space-y-4"
    >
      <h3 className="text-xl font-bold text-white mb-4">➕ Add New Payment Account</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-white/70 text-sm mb-2">Account Name *</label>
          <input
            type="text"
            required
            value={formData.account_name}
            onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
            placeholder="e.g., AMHABINGO Official"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
          />
        </div>

        <div>
          <label className="block text-white/70 text-sm mb-2">Account Holder *</label>
          <input
            type="text"
            required
            value={formData.account_holder}
            onChange={(e) => setFormData({ ...formData, account_holder: e.target.value })}
            placeholder="e.g., Abebe Kebede"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
          />
        </div>

        <div>
          <label className="block text-white/70 text-sm mb-2">Phone Number *</label>
          <input
            type="tel"
            required
            value={formData.phone_number}
            onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
            placeholder="+251912345678 or 0912345678"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
          />
        </div>

        <div>
          <label className="block text-white/70 text-sm mb-2">Payment Method</label>
          <select
            value={formData.payment_method}
            onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-white/30"
          >
            <option value="telebirr">Telebirr</option>
            <option value="cbe_birr">CBE Birr</option>
            <option value="mpesa">M-Pesa</option>
          </select>
        </div>

        <div>
          <label className="block text-white/70 text-sm mb-2">Priority (1 = highest)</label>
          <input
            type="number"
            min="1"
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-white/30"
          />
        </div>

        <div>
          <label className="block text-white/70 text-sm mb-2">Daily Limit (ETB)</label>
          <input
            type="number"
            min="0"
            value={formData.daily_limit}
            onChange={(e) => setFormData({ ...formData, daily_limit: parseInt(e.target.value) })}
            placeholder="100000"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
          />
        </div>
      </div>

      <div>
        <label className="block text-white/70 text-sm mb-2">Notes (optional)</label>
        <textarea
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          placeholder="Add any notes about this account..."
          rows={3}
          className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
        />
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={submitting}
          className="px-6 py-2 bg-green-500 hover:bg-green-600 disabled:bg-green-500/50 rounded-lg text-white font-medium transition-colors"
        >
          {submitting ? "Creating..." : "✅ Create Account"}
        </button>
      </div>
    </form>
  );
}
