export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-neutral-900">🏟️ SportsOS</h1>
          <p className="text-neutral-500 text-sm mt-1">Book a court. Join a match. Play.</p>
        </div>
        {children}
      </div>
    </div>
  );
}
