'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Activity,
  Clock,
  LogOut,
  Menu,
  MessageSquare,
  Settings,
  Shield,
  Upload,
  Users,
  X,
  Sparkles,
} from 'lucide-react';
import { useAppStore } from '@/store';
import { authService } from '@/lib/auth-service';

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, setUser } = useAppStore();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch {
      // Token is cleared locally even if the network request fails.
    } finally {
      setUser(null);
      router.push('/login');
    }
  };

  const isActive = (path: string) => pathname === path;

  const navItems = [
    { href: '/', label: 'Dashboard', icon: Shield },
    { href: '/scans', label: 'Scans', icon: Activity },
    { href: '/upload', label: 'Upload', icon: Upload },
    { href: '/teams', label: 'Teams', icon: Users },
    { href: '/schedules', label: 'Schedules', icon: Clock },
    { href: '/chat', label: 'AI Assistant', icon: MessageSquare },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-sky-200/70 bg-white/85 shadow-[0_14px_40px_rgba(14,165,233,0.12)] backdrop-blur-2xl">
      <div className="h-1 bg-gradient-to-r from-cyan-300 via-emerald-300 via-amber-300 to-rose-300" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link href="/" className="flex min-w-0 items-center gap-3 group">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 via-emerald-400 to-amber-300 shadow-lg shadow-cyan-500/20 transition-all duration-300 group-hover:shadow-emerald-400/30">
              <Shield className="text-[#ffffff]" size={22} />
            </div>
            <div className="min-w-0">
              <span className="block truncate text-lg font-bold tracking-tight gradient-text sm:text-xl">
                CodeGuard AI
              </span>
              <span className="hidden items-center gap-1 text-xs font-medium text-slate-600 sm:flex">
                <Sparkles size={10} />
                Modern Security
              </span>
            </div>
          </Link>

          {user ? (
            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-1 rounded-2xl border border-sky-200/70 bg-white/75 p-1 shadow-inner shadow-sky-100/80 md:flex">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-200 ${
                        isActive(item.href)
                          ? 'border border-sky-200 bg-gradient-to-r from-sky-100 via-emerald-100 to-amber-100 text-sky-950 shadow-lg shadow-sky-500/10'
                          : 'text-slate-700 hover:bg-sky-50 hover:text-sky-900 hover:shadow-md hover:shadow-sky-500/10'
                      }`}
                    >
                      <Icon size={16} />
                      <span className={item.href === '/schedules' ? 'hidden xl:inline' : ''}>{item.label}</span>
                    </Link>
                  );
                })}
              </div>

              <div className="hidden items-center gap-3 border-l border-cyan-200/20 pl-4 md:flex">
                <div className="text-right">
                  <div className="text-sm font-semibold text-slate-950">{user.full_name}</div>
                  <div className="text-xs font-medium text-slate-600">Security Expert</div>
                </div>
                <Link
                  href="/settings"
                  className={`rounded-xl p-2 transition-all duration-200 btn-glow ${
                    isActive('/settings') ? 'bg-amber-100 text-amber-800' : 'text-slate-600 hover:bg-sky-50 hover:text-sky-900'
                  }`}
                  title="Settings"
                >
                  <Settings size={18} />
                </Link>
                <button
                  onClick={handleLogout}
                  className="rounded-xl p-2 text-slate-600 transition-all duration-200 hover:bg-red-50 hover:text-red-700"
                  title="Logout"
                >
                  <LogOut size={18} />
                </button>
              </div>

              <button
                onClick={() => setMobileOpen((open) => !open)}
                className="rounded-xl border border-sky-200/70 bg-white/80 p-2 text-slate-800 shadow-sm transition-all duration-200 hover:bg-sky-50 md:hidden"
                aria-label="Toggle menu"
              >
                {mobileOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link href="/login" className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-700 transition-all duration-200 hover:bg-sky-50 hover:text-sky-900">
                Login
              </Link>
              <Link
                href="/signup"
                className="rounded-xl bg-gradient-to-r from-cyan-400 via-emerald-400 to-amber-300 px-4 py-2 text-sm font-semibold text-slate-950 transition-all duration-200 hover:shadow-lg hover:shadow-cyan-500/25"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
        {user && mobileOpen && (
          <div className="border-t border-sky-200/70 pb-4 pt-3 md:hidden">
            <div className="grid grid-cols-2 gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-2 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-200 ${
                      isActive(item.href)
                        ? 'border border-sky-200 bg-gradient-to-r from-sky-100 via-emerald-100 to-amber-100 text-sky-950 shadow-sm'
                        : 'border border-sky-100 bg-white/70 text-slate-700 hover:bg-sky-50 hover:text-sky-900'
                    }`}
                  >
                    <Icon size={16} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
            <div className="mt-3 flex items-center justify-between rounded-xl border border-sky-200/70 bg-white/75 px-3 py-2 shadow-sm">
              <div>
                <div className="text-sm font-semibold text-slate-950">{user.full_name}</div>
                <div className="text-xs font-medium text-slate-600">Security Expert</div>
              </div>
              <div className="flex items-center gap-1">
                <Link href="/settings" onClick={() => setMobileOpen(false)} className="rounded-lg p-2 text-slate-600 hover:bg-sky-50 hover:text-sky-900">
                  <Settings size={18} />
                </Link>
                <button onClick={handleLogout} className="rounded-lg p-2 text-slate-600 hover:bg-red-50 hover:text-red-700">
                  <LogOut size={18} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
