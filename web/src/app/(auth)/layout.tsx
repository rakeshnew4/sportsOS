import Image from "next/image";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-background">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Image src="/brand/logo-mark.png" alt="" width={48} height={48} className="h-12 w-12 mx-auto mb-2" priority />
          <h1 className="text-xl font-bold">SportsOS</h1>
          <p className="text-ink-muted text-sm mt-1">Book a court. Join a match. Play.</p>
        </div>
        {children}
      </div>
    </div>
  );
}
