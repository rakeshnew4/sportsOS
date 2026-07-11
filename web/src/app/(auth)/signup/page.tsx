"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Building2, User } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

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
      router.push("/home");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-1 rounded-2xl bg-surface-muted p-1">
          {(
            [
              { key: "player", label: "Player", icon: User },
              { key: "owner", label: "Venue owner", icon: Building2 },
            ] as const
          ).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setRole(key)}
              className={`flex-1 flex items-center justify-center gap-1.5 rounded-xl py-2.5 text-sm font-semibold transition-colors ${
                role === key
                  ? "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20"
                  : "text-ink-muted"
              }`}
            >
              <Icon size={15} strokeWidth={2.25} />
              {label}
            </button>
          ))}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1.5">Display name</label>
          <input
            type="text"
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded-full border border-border bg-surface px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1.5">Phone number</label>
          <input
            type="tel"
            required
            placeholder="+91 90000 00000"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-full border border-border bg-surface px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" variant="gradient" pill disabled={loading} className="w-full">
          {loading ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="text-sm text-ink-muted text-center mt-4">
        Already have an account?{" "}
        <Link href="/login" className="text-brand-from font-medium">
          Log in
        </Link>
      </p>
    </Card>
  );
}
