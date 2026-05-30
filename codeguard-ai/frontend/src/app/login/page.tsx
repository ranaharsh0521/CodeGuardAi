'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Lock, ArrowRight, Eye, EyeOff, Loader2 } from 'lucide-react';
import { authService } from '@/lib/auth-service';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/store';
import { GitHubLogo, GoogleLogo } from '@/components/ui/provider-icons';

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useAppStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [githubLoading, setGithubLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [githubEnabled, setGithubEnabled] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);

  useEffect(() => {
    let mounted = true;
    const loadProviders = async () => {
      const features = await authService.getOAuthFeatures();
      if (mounted) {
        setGithubEnabled(features.github);
        setGoogleEnabled(features.google);
      }
    };
    loadProviders();
    return () => {
      mounted = false;
    };
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { access_token } = await authService.login({ email, password });
      apiClient.setToken(access_token);
      const user = await authService.getCurrentUser();
      setUser(user);
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="glass w-full max-w-md rounded-2xl border border-cyan-200/20 p-8 shadow-2xl shadow-cyan-950/30">
        <div className="text-center mb-8">
          <div className="mx-auto mb-4 h-1.5 w-28 rounded-full bg-gradient-to-r from-cyan-300 via-emerald-300 to-rose-300" />
          <h1 className="mb-2 bg-gradient-to-r from-sky-700 via-emerald-600 to-rose-600 bg-clip-text text-3xl font-bold text-transparent">
            Welcome Back
          </h1>
          <p className="text-sm text-slate-300">Sign in to your CodeGuard AI account</p>
        </div>

        {error && (
          <div className="mb-6 rounded-lg border border-red-400/40 bg-red-500/10 px-4 py-3 text-red-100">
            {error}
          </div>
        )}

        <div className="space-y-3 mb-6">
          <button
            type="button"
            disabled={!googleEnabled || googleLoading || githubLoading}
            onClick={async () => {
              setGoogleLoading(true);
              setError('');
              try {
                await authService.loginWithGoogle();
              } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Google login unavailable');
                setGoogleLoading(false);
              }
            }}
            title={googleEnabled ? 'Continue with Google' : 'Add Google OAuth credentials in backend/.env'}
            className="group flex w-full items-center justify-between rounded-2xl border border-slate-200/80 bg-white/80 px-4 py-3.5 font-semibold text-slate-900 shadow-sm shadow-slate-200/70 transition hover:-translate-y-0.5 hover:border-sky-200 hover:bg-white hover:shadow-xl hover:shadow-sky-100/80 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white shadow-inner">
                <GoogleLogo className="h-5 w-5" />
              </span>
              <span>{googleLoading ? 'Redirecting...' : googleEnabled ? 'Continue with Google' : 'Google not configured'}</span>
            </span>
            {googleLoading ? (
              <Loader2 className="animate-spin text-sky-600" size={18} />
            ) : (
              <ArrowRight className="text-slate-400 transition group-hover:translate-x-1 group-hover:text-sky-600" size={18} />
            )}
          </button>

          <button
            type="button"
            disabled={!githubEnabled || githubLoading || googleLoading}
            onClick={async () => {
              setGithubLoading(true);
              setError('');
              try {
                await authService.loginWithGithub();
              } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'GitHub login unavailable');
                setGithubLoading(false);
              }
            }}
            title={githubEnabled ? 'Continue with GitHub' : 'Add GitHub OAuth credentials in backend/.env'}
            className="group flex w-full items-center justify-between rounded-2xl border border-slate-900/10 bg-[#111827] px-4 py-3.5 font-semibold text-[#ffffff] shadow-lg shadow-slate-300/60 transition hover:-translate-y-0.5 hover:bg-[#0f172a] hover:shadow-xl hover:shadow-slate-300/80 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/10 text-[#ffffff]">
                <GitHubLogo className="h-5 w-5" />
              </span>
              <span>{githubLoading ? 'Redirecting...' : githubEnabled ? 'Continue with GitHub' : 'GitHub not configured'}</span>
            </span>
            {githubLoading ? (
              <Loader2 className="animate-spin text-[#ffffff]" size={18} />
            ) : (
              <ArrowRight className="text-slate-400 transition group-hover:translate-x-1 group-hover:text-[#ffffff]" size={18} />
            )}
          </button>
        </div>

        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/10" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="rounded-full border border-white/10 bg-slate-950/80 px-3 py-1 text-slate-400">or email</span>
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-200">Email Address</label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-cyan-200/70">
                <Mail size={18} />
              </div>
              <input
                type="email"
                required
                className="w-full rounded-lg border border-white/10 bg-slate-950/65 py-3 pl-10 pr-4 text-white transition placeholder:text-slate-500 focus:border-cyan-300/60 focus:outline-none"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-200">Password</label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-cyan-200/70">
                <Lock size={18} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                className="w-full rounded-lg border border-white/10 bg-slate-950/65 py-3 pl-10 pr-14 text-white transition placeholder:text-slate-500 focus:border-cyan-300/60 focus:outline-none"
                placeholder="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-3 flex items-center text-slate-400 transition hover:text-white"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="group flex w-full items-center justify-center rounded-lg bg-gradient-to-r from-sky-400 via-emerald-300 to-amber-300 py-3 font-semibold text-slate-950 transition hover:shadow-lg hover:shadow-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
            {!loading && <ArrowRight size={18} className="ml-2 group-hover:translate-x-1 transition-transform" />}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-slate-400">
          Don&apos;t have an account?{' '}
          <Link href="/signup" className="font-medium text-emerald-300 transition hover:text-amber-200">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
