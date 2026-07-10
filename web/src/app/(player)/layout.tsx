import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { SessionProvider } from "@/components/providers/SessionProvider";
import { PlayerNav } from "@/components/layout/PlayerNav";

export default async function PlayerLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect("/login");

  return (
    <SessionProvider session={session}>
      <div className="flex min-h-screen flex-col md:flex-row">
        <PlayerNav />
        <main className="flex-1 p-4 pb-20 md:pb-8 md:p-8 lg:p-10 max-w-5xl mx-auto w-full">{children}</main>
      </div>
    </SessionProvider>
  );
}
