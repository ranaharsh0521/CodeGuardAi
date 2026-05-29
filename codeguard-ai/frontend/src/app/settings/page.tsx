'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LogOut, Mail, Calendar } from 'lucide-react';
import { authService, User } from '@/lib/auth-service';
import { useAppStore } from '@/store';

export default function SettingsPage() {
  const router = useRouter();
  const { setUser } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    const loadUser = async () => {
      try {
        if (!authService.isAuthenticated()) {
          router.push('/login');
          return;
        }

        const userData = await authService.getCurrentUser();
        setCurrentUser(userData);
      } catch {
        await authService.logout();
        setUser(null);
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, [router, setUser]);

  const handleLogout = async () => {
    await authService.logout();
    setUser(null);
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <header className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
          <h1 className="text-4xl font-bold">Settings</h1>
          <p className="mt-2 text-slate-400">Manage account profile and workspace settings.</p>
        </header>

        <div className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
          <h2 className="mb-6 text-2xl font-bold">Profile Information</h2>

          <div className="space-y-6">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-400">Full Name</label>
              <p className="text-lg text-white">{currentUser?.full_name}</p>
            </div>

            <div>
              <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-400">
                <Mail size={16} />
                <span>Email Address</span>
              </label>
              <p className="text-lg text-white">{currentUser?.email}</p>
            </div>

            <div>
              <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-400">
                <Calendar size={16} />
                <span>Member Since</span>
              </label>
              <p className="text-lg text-white">
                {currentUser?.created_at && new Date(currentUser.created_at).toLocaleDateString()}
              </p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-400">Account Status</label>
              <span
                className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${
                  currentUser?.is_active
                    ? 'border border-emerald-300/30 bg-emerald-300/10 text-emerald-100'
                    : 'border border-red-400/30 bg-red-500/10 text-red-100'
                }`}
              >
                {currentUser?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>

        <div className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
          <h2 className="mb-6 text-2xl font-bold">API Settings</h2>
          <p className="mb-4 text-slate-400">Coming soon: API key management for integrations</p>
        </div>

        <div className="rounded-3xl border border-red-400/30 bg-red-500/10 p-5 sm:p-8">
          <h2 className="mb-6 text-2xl font-bold text-red-100">Danger Zone</h2>

          <button
            onClick={handleLogout}
            className="flex w-full items-center justify-between rounded-2xl border border-red-400/30 bg-red-500/10 px-6 py-3 font-medium text-red-100 transition hover:bg-red-500/15"
          >
            <div className="flex items-center gap-2">
              <LogOut size={20} />
              <span>Logout</span>
            </div>
            <span>Exit</span>
          </button>
        </div>
      </div>
    </div>
  );
}
