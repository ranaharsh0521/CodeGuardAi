'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import { scanService, Scan } from '@/lib/scan-service';
import { authService } from '@/lib/auth-service';
import { ScanCard } from '@/components/ui/scan-card';

export default function ScansPage() {
  const router = useRouter();
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadScans = async () => {
      try {
        if (!authService.isAuthenticated()) {
          router.push('/login');
          return;
        }

        const allScans = await scanService.getScans();
        setScans(allScans);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load scans');
      } finally {
        setLoading(false);
      }
    };

    loadScans();
  }, [router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
          <h1 className="mb-2 text-3xl font-bold sm:text-4xl">Scan History</h1>
          <p className="text-slate-400">View all your previous security scans</p>
        </div>

        {error && (
          <div className="mb-8 rounded-2xl border border-red-400/30 bg-red-500/10 px-6 py-4 text-red-100">
            {error}
          </div>
        )}

        {scans.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {scans.map((scan) => (
              <ScanCard
                key={scan.id}
                id={scan.id}
                status={scan.status}
                risk_score={scan.risk_score}
                findings_count={scan.findings_count ?? scan.findings?.length ?? 0}
                project_name={scan.project_name || `Project ${scan.project_id}`}
                created_at={scan.created_at}
                onClick={() => router.push(`/results/${scan.id}`)}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-white/15 bg-white/[0.03] p-8 text-center sm:p-12">
            <h3 className="mb-2 text-xl font-semibold text-slate-200">No scans yet</h3>
            <p className="mb-6 text-slate-400">Start by creating a project and triggering a security scan.</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-6 py-3 font-semibold text-cyan-100 transition hover:bg-cyan-300/15"
            >
              <span>Go to Dashboard</span>
              <ChevronRight size={20} />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
