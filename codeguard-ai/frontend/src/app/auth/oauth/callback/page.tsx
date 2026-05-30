'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { authService } from '@/lib/auth-service';
import { useAppStore } from '@/store';

function OAuthCallbackInner() {
  const router = useRouter();
  const { setUser } = useAppStore();
  const [status, setStatus] = useState<'loading' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    // Read params from window.location.search directly — this is always reliable
    // even in Next.js Turbopack where useSearchParams() can return empty on first render.
    const searchParams = new URLSearchParams(window.location.search);
    const token = searchParams.get('token');
    const provider = searchParams.get('provider') || 'OAuth';
    const providerError = searchParams.get('error');

    if (!token) {
      const timer = window.setTimeout(() => {
        setStatus('error');
        setErrorMessage(providerError || `No token received from ${provider}. Please try logging in again.`);
      }, 0);
      return () => window.clearTimeout(timer);
    }

    let cancelled = false;

    const finish = async () => {
      try {
        // Step 1: Save token to localStorage FIRST before any API call
        apiClient.setToken(token);

        // Step 2: Clean token from URL so it's not in browser history
        window.history.replaceState({}, document.title, window.location.pathname);

        // Step 3: Fetch user — token is now saved, Authorization header will be sent
        const user = await authService.getCurrentUser();

        if (!cancelled) {
          setUser(user);
          const returnTo = localStorage.getItem('oauth_return_to') || '/dashboard';
          localStorage.removeItem('oauth_return_to');
          // Step 4: Go back to the workflow that started OAuth
          router.replace(returnTo);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          apiClient.clearToken();
          const message = err instanceof Error ? err.message : `${provider} sign-in failed`;
          setStatus('error');
          setErrorMessage(message);
        }
      }
    };

    finish();
    return () => {
      cancelled = true;
    };
  }, [router, setUser]);

  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center gap-4 text-white px-4">
        <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-6 max-w-md w-full text-center">
          <div className="text-4xl mb-3">⚠️</div>
          <h2 className="text-lg font-semibold text-red-300 mb-2">Sign-in Failed</h2>
          <p className="text-gray-400 text-sm mb-4">{errorMessage}</p>
          <button
            onClick={() => router.replace('/login')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center gap-4 text-white">
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Completing sign-in&hellip;</p>
      </div>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-950 flex items-center justify-center">
          <div className="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        </div>
      }
    >
      <OAuthCallbackInner />
    </Suspense>
  );
}
