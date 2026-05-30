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
    <nav className="sticky top-0 z-50 glass border-b border-cyan-200/20">
      <div className="h-1 bg-gradient-to-r from-cyan-300 via-emerald-300 via-amber-300 to-rose-300" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link href="/" className="flex min-w-0 items-center gap-3 group">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 via-emerald-400 to-amber-300 shadow-lg shadow-cyan-500/20 transition-all duration-300 group-hover:shadow-emerald-400/30">
              <Shield className="text-white" size={22} />
            </div>
            <div className="min-w-0">
              <span className="block truncate text-lg font-bold tracking-tight gradient-text sm:text-xl">
                CodeGuard AI
              </span>
              <span className="hidden items-center gap-1 text-xs text-cyan-100/70 sm:flex">
                <Sparkles size={10} />
                Modern Security
              </span>
            </div>
          </Link>

          {user ? (
            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-1 rounded-2xl border border-white/10 bg-slate-950/40 p-1 shadow-inner shadow-white/5 md:flex">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-200 ${
                        isActive(item.href)
                          ? 'border border-cyan-200/30 bg-gradient-to-r from-cyan-400/20 via-emerald-300/15 to-amber-300/20 text-white shadow-lg shadow-cyan-500/10'
                          : 'text-slate-300 hover:bg-white/10 hover:text-white hover:shadow-md hover:shadow-cyan-500/10'
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
                  <div className="text-sm font-medium text-white">{user.full_name}</div>
                  <div className="text-xs text-emerald-200/70">Security Expert</div>
                </div>
                <Link
                  href="/settings"
                  className={`rounded-xl p-2 transition-all duration-200 btn-glow ${
                    isActive('/settings') ? 'bg-amber-300/15 text-amber-200' : 'text-slate-400 hover:bg-white/10 hover:text-white'
                  }`}
                  title="Settings"
                >
                  <Settings size={18} />
                </Link>
                <button
                  onClick={handleLogout}
                  className="rounded-xl p-2 text-slate-400 transition-all duration-200 hover:bg-red-500/20 hover:text-red-300"
                  title="Logout"
                >
                  <LogOut size={18} />
                </button>
              </div>

              <button
                onClick={() => setMobileOpen((open) => !open)}
                className="rounded-xl border border-cyan-200/20 bg-slate-950/50 p-2 text-slate-200 transition-all duration-200 hover:bg-white/10 md:hidden"
                aria-label="Toggle menu"
              >
                {mobileOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link href="/login" className="rounded-xl px-4 py-2 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white">
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
          <div className="border-t border-cyan-200/20 pb-4 pt-3 md:hidden">
            <div className="grid grid-cols-2 gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-2 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-200 ${
                      isActive(item.href) ? 'bg-gradient-to-r from-cyan-400/20 via-emerald-300/15 to-amber-300/20 text-white' : 'glass text-slate-300 hover:bg-white/10'
                    }`}
                  >
                    <Icon size={16} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
            <div className="mt-3 flex items-center justify-between glass rounded-xl px-3 py-2">
              <div>
                <div className="text-sm font-medium text-white">{user.full_name}</div>
                <div className="text-xs text-slate-400">Security Expert</div>
              </div>
              <div className="flex items-center gap-1">
                <Link href="/settings" onClick={() => setMobileOpen(false)} className="rounded-lg p-2 text-slate-300 hover:text-white">
                  <Settings size={18} />
                </Link>
                <button onClick={handleLogout} className="rounded-lg p-2 text-slate-300 hover:text-red-300">
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
