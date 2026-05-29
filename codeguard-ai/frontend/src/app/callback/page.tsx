'use client';

import { Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

function CallbackRedirectInner() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const query = params.toString();
    router.replace(`/auth/oauth/callback${query ? `?${query}` : ''}`);
  }, [params, router]);

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-400">
      Completing sign in...
    </div>
  );
}

export default function CallbackRedirectPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-400">Loading...</div>}>
      <CallbackRedirectInner />
    </Suspense>
  );
}
