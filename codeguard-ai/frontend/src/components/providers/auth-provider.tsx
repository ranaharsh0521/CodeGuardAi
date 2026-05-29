'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useAppStore } from '@/store';
import { authService } from '@/lib/auth-service';

/**
 * Hydrates user state from JWT on every page load so the navbar stays in sync.
 *
 * IMPORTANT: We skip hydration on /auth/oauth/callback because at that point the
 * token has been received in the URL but not yet saved to localStorage. Calling
 * /users/me before the callback page's useEffect runs would result in a 401 or
 * the browser reporting a CORS error on top of the real 401/500 response.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser } = useAppStore();
  const pathname = usePathname();

  useEffect(() => {
    // Skip hydration on the OAuth callback page — the callback page saves the token
    // and fetches the user itself after storing it.
    if (pathname.startsWith('/auth/oauth/callback')) {
      return;
    }

    const hydrate = async () => {
      if (!authService.isAuthenticated()) return;
      try {
        const user = await authService.getCurrentUser();
        setUser(user);
      } catch {
        await authService.logout();
        setUser(null);
      }
    };

    hydrate();
  }, [pathname, setUser]);

  return <>{children}</>;
}
