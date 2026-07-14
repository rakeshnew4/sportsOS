import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { AdminNav } from "@/components/layout/AdminNav";

export default async function TenantAdminLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = await params;
  const session = await getSession();
  if (!session) redirect("/admin-login");
  if (!session.owner_of.includes(tenantId) && !session.staff_of.includes(tenantId)) {
    redirect("/admin");
  }

  return (
    <div>
      <AdminNav tenantId={tenantId} />
      {children}
    </div>
  );
}
