'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Lock, ArrowRight, Eye, EyeOff, GitBranch } from 'lucide-react';
import { authService } from '@/lib/auth-service';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/store';

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
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-800 p-8 rounded-2xl shadow-xl w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 mb-2">
            Welcome Back
          </h1>
          <p className="text-gray-400 text-sm">Sign in to your CodeGuard AI account</p>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500 text-red-200 px-4 py-3 rounded-lg mb-6">
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
            className="w-full flex items-center justify-center gap-2 bg-gray-950 hover:bg-gray-800 text-gray-100 border border-gray-700 py-3 rounded-lg font-medium transition disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="flex h-5 w-5 items-center justify-center rounded-full border border-gray-500 text-sm font-bold text-gray-100">
              G
            </span>
            {googleLoading ? 'Redirecting...' : googleEnabled ? 'Continue with Google' : 'Google not configured'}
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
            className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 border border-gray-600 py-3 rounded-lg font-medium transition disabled:cursor-not-allowed disabled:opacity-60"
          >
            <GitBranch size={20} />
            {githubLoading ? 'Redirecting...' : githubEnabled ? 'Continue with GitHub' : 'GitHub not configured'}
          </button>
        </div>

        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-700" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-gray-900 text-gray-500">or email</span>
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                <Mail size={18} />
              </div>
              <input
                type="email"
                required
                className="w-full bg-gray-950 border border-gray-700 rounded-lg pl-10 pr-4 py-3 text-white focus:outline-none focus:border-blue-500 transition"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                <Lock size={18} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                className="w-full bg-gray-950 border border-gray-700 rounded-lg pl-10 pr-14 py-3 text-white focus:outline-none focus:border-blue-500 transition"
                placeholder="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-3 flex items-center text-gray-400 hover:text-white transition"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition flex items-center justify-center group"
          >
            {loading ? 'Signing in...' : 'Sign In'}
            {!loading && <ArrowRight size={18} className="ml-2 group-hover:translate-x-1 transition-transform" />}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-gray-400">
          Don&apos;t have an account?{' '}
          <Link href="/signup" className="text-emerald-400 hover:text-emerald-300 transition font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
