"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function SignupPage() {
  const router = useRouter();
  const [role, setRole] = useState<"player" | "owner">("player");
  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role, display_name: displayName, phone }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Could not create your account");
      }
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-neutral-200 p-6 shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex rounded-lg border border-neutral-300 p-1 text-sm">
          <button
            type="button"
            onClick={() => setRole("player")}
            className={`flex-1 rounded-md py-1.5 font-medium transition-colors ${
              role === "player" ? "bg-emerald-600 text-white" : "text-neutral-600"
            }`}
          >
            🎽 Player
          </button>
          <button
            type="button"
            onClick={() => setRole("owner")}
            className={`flex-1 rounded-md py-1.5 font-medium transition-colors ${
              role === "owner" ? "bg-emerald-600 text-white" : "text-neutral-600"
            }`}
          >
            🏢 Venue owner
          </button>
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Display name</label>
          <input
            type="text"
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded-lg border border-neutral-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Phone number</label>
          <input
            type="tel"
            required
            placeholder="+91 90000 00000"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-lg border border-neutral-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="text-sm text-neutral-500 text-center mt-4">
        Already have an account?{" "}
        <Link href="/login" className="text-emerald-600 font-medium">
          Log in
        </Link>
      </p>
    </div>
  );
}
