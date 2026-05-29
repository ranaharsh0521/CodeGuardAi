'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  Activity,
  ArrowLeft,
  CheckCircle,
  GitCompare,
  Play,
  Save,
  ShieldAlert,
  Trash2,
} from 'lucide-react';
import { authService } from '@/lib/auth-service';
import { projectService, Project } from '@/lib/project-service';
import { scanService, Scan, ScanComparison } from '@/lib/scan-service';
import { teamService, Team } from '@/lib/team-service';
import { ScanCard } from '@/components/ui/scan-card';

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Number(params.id);

  const [project, setProject] = useState<Project | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [comparison, setComparison] = useState<ScanComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [startingScan, setStartingScan] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const [formName, setFormName] = useState('');
  const [formUrl, setFormUrl] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formTeamId, setFormTeamId] = useState('');

  const loadProject = useCallback(async () => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }

    if (!Number.isFinite(projectId)) {
      setError('Invalid project id');
      return;
    }

    const [projectData, scanData, teamData] = await Promise.all([
      projectService.getById(projectId),
      scanService.getScans(projectId),
      teamService.list(),
    ]);

    setProject(projectData);
    setScans(scanData);
    setTeams(
      teamData.filter(
        (team) => team.role === 'owner' || team.role === 'admin' || team.id === projectData.team_id,
      ),
    );
    setFormName(projectData.name);
    setFormUrl(projectData.repository_url || '');
    setFormDescription(projectData.description || '');
    setFormTeamId(projectData.team_id ? String(projectData.team_id) : '');

    const latestCompleted = scanData.find((scan) => scan.status === 'completed');
    if (latestCompleted) {
      try {
        setComparison(await scanService.compareScan(latestCompleted.id));
      } catch {
        setComparison(null);
      }
    } else {
      setComparison(null);
    }
  }, [projectId, router]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadProject()
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : 'Failed to load project');
        })
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadProject]);

  const completedScans = useMemo(() => scans.filter((scan) => scan.status === 'completed'), [scans]);
  const latestScan = scans[0];
  const trendScans = completedScans.slice(0, 8).reverse();
  const averageRisk =
    completedScans.length > 0
      ? Math.round(completedScans.reduce((sum, scan) => sum + scan.risk_score, 0) / completedScans.length)
      : 0;

  const openFindingsEstimate = scans.reduce((sum, scan) => sum + (scan.findings_count || 0), 0);

  const handleSave = async () => {
    if (!formName.trim() || !project) return;
    setSaving(true);
    setError('');
    setMessage('');

    try {
      const updated = await projectService.update(project.id, {
        name: formName.trim(),
        repository_url: formUrl.trim() || undefined,
        description: formDescription.trim() || undefined,
        team_id: formTeamId ? Number(formTeamId) : undefined,
      });
      setProject(updated);
      setMessage('Project updated');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update project');
    } finally {
      setSaving(false);
    }
  };

  const handleStartScan = async () => {
    if (!project) return;
    setStartingScan(true);
    setError('');
    try {
      const scan = await scanService.triggerScan({ project_id: project.id });
      router.push(`/results/${scan.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to start scan');
      setStartingScan(false);
    }
  };

  const handleDelete = async () => {
    if (!project || !confirm(`Delete "${project.name}" permanently?`)) return;
    try {
      await projectService.delete(project.id);
      router.push('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete project');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <Link href="/" className="mb-8 inline-flex items-center gap-2 text-cyan-200 hover:text-cyan-100">
            <ArrowLeft size={20} />
            Dashboard
          </Link>
          <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-6 py-4 text-red-100">
            {error || 'Project not found'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-cyan-200 hover:text-cyan-100">
          <ArrowLeft size={20} />
          Dashboard
        </Link>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-red-100">
            {error}
          </div>
        )}
        {message && (
          <div className="mb-6 rounded-2xl border border-emerald-300/30 bg-emerald-300/10 px-4 py-3 text-emerald-100">
            {message}
          </div>
        )}

        <header className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <p className="mb-2 text-sm text-slate-400">Project #{project.id}</p>
              <h1 className="truncate text-3xl font-bold sm:text-5xl">{project.name}</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
                {project.description || 'No description added yet.'}
              </p>
              {project.repository_url && (
                <p className="mt-3 truncate text-xs text-cyan-200">{project.repository_url}</p>
              )}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                onClick={handleStartScan}
                disabled={startingScan}
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-4 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Play size={18} />
                {startingScan ? 'Starting...' : 'Scan Now'}
              </button>
              <button
                onClick={handleDelete}
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm font-semibold text-red-100 transition hover:bg-red-500/15"
              >
                <Trash2 size={18} />
                Delete
              </button>
            </div>
          </div>
        </header>

        <div className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {[
            { label: 'Total Scans', value: scans.length, icon: Activity, tone: 'text-cyan-200' },
            { label: 'Completed', value: completedScans.length, icon: CheckCircle, tone: 'text-emerald-200' },
            { label: 'Avg Risk', value: averageRisk, icon: ShieldAlert, tone: 'text-amber-200' },
            { label: 'Tracked Findings', value: openFindingsEstimate, icon: GitCompare, tone: 'text-red-200' },
          ].map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs text-slate-400">{stat.label}</p>
                    <p className="mt-2 text-3xl font-bold">{stat.value}</p>
                  </div>
                  <Icon className={stat.tone} size={26} />
                </div>
              </div>
            );
          })}
        </div>

        <div className="mb-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
            <h2 className="mb-4 text-xl font-bold">Project Settings</h2>
            <div className="space-y-3">
              <input
                value={formName}
                onChange={(event) => setFormName(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none focus:border-cyan-300/60"
                placeholder="Project name"
              />
              <input
                value={formUrl}
                onChange={(event) => setFormUrl(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none focus:border-cyan-300/60"
                placeholder="Repository URL"
              />
              <textarea
                value={formDescription}
                onChange={(event) => setFormDescription(event.target.value)}
                className="h-28 w-full resize-none rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none focus:border-cyan-300/60"
                placeholder="Description"
              />
              {teams.length > 0 && (
                <select
                  value={formTeamId}
                  onChange={(event) => setFormTeamId(event.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none focus:border-cyan-300/60"
                >
                  <option value="">Personal project</option>
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name}
                    </option>
                  ))}
                </select>
              )}
              <button
                onClick={handleSave}
                disabled={saving || !formName.trim()}
                className="inline-flex items-center gap-2 rounded-2xl border border-emerald-300/30 bg-emerald-300/10 px-5 py-3 font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Save size={18} />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
            <h2 className="mb-4 text-xl font-bold">Risk Trend</h2>
            {trendScans.length > 0 ? (
              <div className="flex h-48 items-end gap-3 rounded-2xl bg-slate-950/50 p-4">
                {trendScans.map((scan) => (
                  <Link
                    key={scan.id}
                    href={`/results/${scan.id}`}
                    className="flex h-full flex-1 flex-col justify-end gap-2"
                    title={`Scan #${scan.id}: ${scan.risk_score}/100`}
                  >
                    <div
                      className={`min-h-2 rounded-t-xl transition hover:opacity-80 ${
                        scan.risk_score < 30
                          ? 'bg-emerald-400/70'
                          : scan.risk_score < 70
                          ? 'bg-amber-400/70'
                          : 'bg-red-400/70'
                      }`}
                      style={{ height: `${Math.max(8, scan.risk_score)}%` }}
                    />
                    <span className="text-center text-xs text-slate-500">#{scan.id}</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-white/15 bg-slate-950/40 p-8 text-center text-slate-400">
                Complete a scan to build a risk trend.
              </div>
            )}
          </section>
        </div>

        <section className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
          <div className="mb-4 flex items-center gap-2">
            <GitCompare className="text-cyan-200" size={20} />
            <h2 className="text-xl font-bold">Latest Comparison</h2>
          </div>
          {comparison?.base_scan_id ? (
            <div className="grid gap-3 md:grid-cols-4">
              <div className="rounded-2xl bg-slate-950/50 p-4">
                <p className="text-xs text-slate-400">Compared Scans</p>
                <p className="mt-2 font-semibold">
                  #{comparison.base_scan_id} to #{comparison.current_scan_id}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-950/50 p-4">
                <p className="text-xs text-slate-400">Risk Delta</p>
                <p className={`mt-2 text-2xl font-bold ${(comparison.risk_delta || 0) <= 0 ? 'text-emerald-200' : 'text-red-200'}`}>
                  {(comparison.risk_delta || 0) > 0 ? '+' : ''}
                  {comparison.risk_delta}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-950/50 p-4">
                <p className="text-xs text-slate-400">New Findings</p>
                <p className="mt-2 text-2xl font-bold text-red-200">{comparison.new_findings_count}</p>
              </div>
              <div className="rounded-2xl bg-slate-950/50 p-4">
                <p className="text-xs text-slate-400">Resolved</p>
                <p className="mt-2 text-2xl font-bold text-emerald-200">{comparison.resolved_findings_count}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400">
              {latestScan ? 'One completed scan exists. Run another scan to compare changes.' : 'No scans have been started for this project yet.'}
            </p>
          )}
        </section>

        <section>
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold">Scan History</h2>
              <p className="mt-1 text-sm text-slate-400">Open results, review findings, and track progress over time.</p>
            </div>
            <button
              onClick={handleStartScan}
              disabled={startingScan}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-4 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Play size={18} />
              Scan Now
            </button>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {scans.length > 0 ? (
              scans.map((scan) => (
                <ScanCard
                  key={scan.id}
                  id={scan.id}
                  status={scan.status}
                  risk_score={scan.risk_score}
                  findings_count={scan.findings_count ?? scan.findings?.length ?? 0}
                  project_name={project.name}
                  created_at={scan.created_at}
                  onClick={() => router.push(`/results/${scan.id}`)}
                />
              ))
            ) : (
              <div className="rounded-3xl border border-dashed border-white/15 bg-white/[0.03] p-8 text-center text-slate-400 lg:col-span-2">
                No scans yet. Start a scan to create the first baseline.
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
