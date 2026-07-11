import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { SessionProvider } from "@/components/providers/SessionProvider";

export default async function AdminRootLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect("/login");

  return (
    <SessionProvider session={session}>
      <div className="min-h-screen bg-neutral-50">
        <header className="border-b border-neutral-200 bg-white px-4 py-3 flex items-center justify-between">
          <p className="font-bold">🏟️ SportsOS Admin</p>
          <a href="/home" className="text-sm text-neutral-500 hover:text-neutral-800">
            ← Back to player app
          </a>
        </header>
        <main className="max-w-3xl mx-auto w-full p-4 md:p-8">{children}</main>
      </div>
    </SessionProvider>
  );
}
