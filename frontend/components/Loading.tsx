'use client';

export default function Loading({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-white/20 border-t-white mb-4"></div>
        <p className="text-white text-lg">{message}</p>
      </div>
    </div>
  );
}
