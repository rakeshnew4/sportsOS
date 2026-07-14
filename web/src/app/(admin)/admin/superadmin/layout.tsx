import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { SuperadminNav } from "@/components/layout/SuperadminNav";

export default async function SuperadminLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect("/admin-login");
  if (!session.is_superadmin) redirect("/admin");

  return (
    <div>
      <SuperadminNav />
      {children}
    </div>
  );
}
