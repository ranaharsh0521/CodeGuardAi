'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Clock, Trash2, Pause, Play } from 'lucide-react';
import { scheduleService, ScheduledScan } from '@/lib/schedule-service';
import { projectService, Project } from '@/lib/project-service';
import { authService } from '@/lib/auth-service';

export default function SchedulesPage() {
  const router = useRouter();
  const [schedules, setSchedules] = useState<ScheduledScan[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState('');
  const [intervalHours, setIntervalHours] = useState(24);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    const [s, p] = await Promise.all([scheduleService.list(), projectService.getAll()]);
    setSchedules(s);
    setProjects(p);
    if (p.length && !projectId) setProjectId(String(p[0].id));
  };

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    load().finally(() => setLoading(false));
  }, [router]);

  const handleCreate = async () => {
    if (!projectId) return;
    await scheduleService.create(parseInt(projectId), intervalHours);
    await load();
  };

  const handleToggle = async (id: number) => {
    await scheduleService.toggle(id);
    await load();
  };

  const handleDelete = async (id: number) => {
    await scheduleService.delete(id);
    await load();
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300" />
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-6 text-white sm:px-6 lg:px-8">
      <header className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
        <h1 className="flex items-center gap-3 text-3xl font-bold">
          <Clock className="text-amber-200" />
          Scheduled Scans
        </h1>
        <p className="mt-2 text-slate-400">Automatically re-scan projects on a schedule.</p>
      </header>

      <div className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
        <h2 className="mb-4 font-semibold">New Schedule</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 outline-none focus:border-cyan-300/60"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input
            type="number"
            min={1}
            value={intervalHours}
            onChange={(e) => setIntervalHours(parseInt(e.target.value) || 24)}
            className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 outline-none focus:border-cyan-300/60"
            placeholder="Interval (hours)"
          />
          <button
            onClick={handleCreate}
            className="rounded-2xl border border-cyan-300/30 bg-cyan-300/10 py-3 font-semibold text-cyan-100 hover:bg-cyan-300/15"
          >
            Add Schedule
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {schedules.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-white/15 bg-white/[0.03] p-8 text-center text-slate-400">
            No scheduled scans yet.
          </div>
        ) : (
          schedules.map((s) => (
            <div
              key={s.id}
              className="flex flex-col gap-4 rounded-3xl border border-white/10 bg-white/[0.04] p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="font-medium">Project #{s.project_id}</p>
                <p className="text-sm text-slate-500">
                  Every {s.interval_hours}h - {s.enabled ? 'Active' : 'Paused'}
                  {s.next_run_at && ` - Next: ${new Date(s.next_run_at).toLocaleString()}`}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleToggle(s.id)}
                  className="rounded-xl border border-white/10 bg-slate-950/60 p-2 text-slate-200 hover:bg-white/[0.08]"
                  title={s.enabled ? 'Pause' : 'Resume'}
                >
                  {s.enabled ? <Pause size={18} /> : <Play size={18} />}
                </button>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="rounded-xl border border-red-400/30 bg-red-500/10 p-2 text-red-200 hover:bg-red-500/15"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
