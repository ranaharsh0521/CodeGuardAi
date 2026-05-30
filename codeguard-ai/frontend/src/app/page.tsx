'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Activity,
  ArrowRight,
  CheckCircle,
  FolderGit2,
  GitBranch,
  Plus,
  ShieldAlert,
  Sparkles,
  Upload,
} from 'lucide-react';
import { GitHubRepository, projectService, Project } from '@/lib/project-service';
import { scanService, Scan } from '@/lib/scan-service';
import { authService } from '@/lib/auth-service';
import { APIRequestError } from '@/lib/api-client';
import { teamService, Team } from '@/lib/team-service';
import { useAppStore } from '@/store';
import { ScanCard } from '@/components/ui/scan-card';

type DashboardScan = Scan & { project_id: number; created_at: string; status: string; risk_score: number };
type LoadGitHubReposOptions = {
  skipConnectRedirect?: boolean;
};

export default function Dashboard() {
  const router = useRouter();
  const { setUser, setCurrentScan } = useAppStore();

  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [recentScans, setRecentScans] = useState<DashboardScan[]>([]);
  const [totalScans, setTotalScans] = useState(0);
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectUrl, setNewProjectUrl] = useState('');
  const [newProjectTeamId, setNewProjectTeamId] = useState('');
  const [showNewProject, setShowNewProject] = useState(false);
  const [githubRepos, setGithubRepos] = useState<GitHubRepository[]>([]);
  const [githubReposLoading, setGithubReposLoading] = useState(false);
  const [selectedRepoId, setSelectedRepoId] = useState('');
  const [repoSearch, setRepoSearch] = useState('');

  const loadGitHubRepos = useCallback(async (options: LoadGitHubReposOptions = {}) => {
    setErrorMsg('');
    setGithubReposLoading(true);
    try {
      const repos = await projectService.getGitHubRepositories();
      setGithubRepos(repos);
      setGithubReposLoading(false);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unable to load GitHub repositories. Connect GitHub first.';
      const shouldConnectGitHub =
        message.toLowerCase().includes('github') &&
        (message.toLowerCase().includes('connect') ||
          message.toLowerCase().includes('expired') ||
          err instanceof APIRequestError);

      if (shouldConnectGitHub && !options.skipConnectRedirect) {
        setErrorMsg('Connecting GitHub...');
        localStorage.setItem('oauth_return_to', '/dashboard?loadGithubRepos=1&githubConnected=1');
        try {
          await authService.loginWithGithub();
        } catch (loginErr: unknown) {
          setErrorMsg(loginErr instanceof Error ? loginErr.message : message);
          setGithubReposLoading(false);
        }
        return;
      }

      setErrorMsg(message);
      setGithubReposLoading(false);
    }
  }, []);

  useEffect(() => {
    const initDashboard = async () => {
      try {
        if (!authService.isAuthenticated()) {
          router.push('/login');
          return;
        }

        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);

        const userProjects = await projectService.getAll();
        setProjects(userProjects);
        const userTeams = await teamService.list();
        setTeams(userTeams.filter((team) => team.role === 'owner' || team.role === 'admin'));

        const scans = await scanService.getScans();
        setTotalScans(scans.length);
        setRecentScans(scans.slice(0, 6));
      } catch {
        await authService.logout();
        setUser(null);
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    initDashboard();
  }, [router, setUser]);

  useEffect(() => {
    if (loading) return;

    const params = new URLSearchParams(window.location.search);
    if (params.get('loadGithubRepos') !== '1') return;

    setShowNewProject(true);
    window.history.replaceState({}, document.title, window.location.pathname);
    void loadGitHubRepos({ skipConnectRedirect: params.get('githubConnected') === '1' });
  }, [loadGitHubRepos, loading]);

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    setErrorMsg('');

    try {
      const newProject = await projectService.create({
        name: newProjectName,
        description: newProjectDesc || undefined,
        repository_url: newProjectUrl || undefined,
        team_id: newProjectTeamId ? parseInt(newProjectTeamId) : undefined,
      });
      setProjects((prev) => [...prev, newProject]);
      setNewProjectName('');
      setNewProjectUrl('');
      setNewProjectDesc('');
      setNewProjectTeamId('');
      setShowNewProject(false);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to create project. Please try again.');
    }
  };

  const handleSelectGitHubRepo = (repoId: string) => {
    setSelectedRepoId(repoId);
    const repo = githubRepos.find((item) => String(item.id) === repoId);
    if (!repo) return;
    setNewProjectName(repo.full_name);
    setNewProjectUrl(repo.clone_url || repo.html_url);
    setNewProjectDesc(repo.description || `Imported from GitHub (${repo.default_branch || 'default branch'})`);
  };

  const handleCreateAndScan = async () => {
    if (!newProjectName.trim()) return;
    setErrorMsg('');
    try {
      const newProject = await projectService.create({
        name: newProjectName,
        description: newProjectDesc || undefined,
        repository_url: newProjectUrl || undefined,
        team_id: newProjectTeamId ? parseInt(newProjectTeamId) : undefined,
      });
      setProjects((prev) => [...prev, newProject]);
      const scan = await scanService.triggerScan({ project_id: newProject.id });
      setCurrentScan(scan);
      router.push(`/results/${scan.id}`);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to create project and start scan.');
    }
  };

  const handleTriggerScan = async (projectId: number) => {
    setErrorMsg('');
    try {
      const scan = await scanService.triggerScan({ project_id: projectId });
      setCurrentScan(scan);
      router.push(`/results/${scan.id}`);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to start scan. Check backend is running.');
    }
  };

  const averageRisk =
    recentScans.length > 0
      ? Math.round(recentScans.reduce((sum, scan) => sum + scan.risk_score, 0) / recentScans.length)
      : 0;

  const filteredGitHubRepos = githubRepos.filter((repo) => {
    const query = repoSearch.trim().toLowerCase();
    if (!query) return true;
    return repo.full_name.toLowerCase().includes(query) || (repo.description || '').toLowerCase().includes(query);
  });

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 overflow-hidden rounded-3xl border border-white/70 bg-gradient-to-br from-white/85 via-sky-50/80 to-rose-50/80 p-5 shadow-2xl shadow-sky-200/40 sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-200/30 bg-emerald-300/10 px-3 py-1 text-xs font-semibold text-emerald-100">
                <Sparkles size={14} />
                AI powered code security
              </div>
              <h1 className="max-w-3xl bg-gradient-to-r from-slate-950 via-sky-700 to-rose-700 bg-clip-text text-3xl font-bold tracking-normal text-transparent sm:text-5xl">
                Secure your codebase with a cleaner command center.
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400 sm:text-base">
                Track projects, run scans, and review risk signals from one responsive workspace.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Link
                href="/upload"
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-amber-200/20 bg-amber-300/10 px-4 py-3 text-sm font-semibold text-amber-100 transition hover:bg-amber-300/15"
              >
                <Upload size={18} />
                Upload Files
              </Link>
              <button
                onClick={() => setShowNewProject(true)}
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-4 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/15 hover:shadow-lg hover:shadow-cyan-500/10"
              >
                <Plus size={18} />
                New Project
              </button>
            </div>
          </div>
        </header>

        {errorMsg && (
          <div className="mb-6 flex items-center justify-between rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-red-100">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg('')} className="ml-4 text-lg leading-none text-red-200 hover:text-white">
              &times;
            </button>
          </div>
        )}

        <div className="mb-10 grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-5">
          {[
            {
              label: 'Total Projects',
              value: projects.length,
              icon: FolderGit2,
              tone: 'text-cyan-200',
              panel: 'from-cyan-400/15 to-blue-400/5',
            },
            {
              label: 'Total Scans',
              value: totalScans,
              icon: Activity,
              tone: 'text-emerald-200',
              panel: 'from-emerald-400/15 to-teal-400/5',
            },
            {
              label: 'Avg Risk Score',
              value: averageRisk,
              icon: ShieldAlert,
              tone: 'text-amber-200',
              panel: 'from-amber-400/15 to-orange-400/5',
            },
            {
              label: 'Secure Scans',
              value: recentScans.filter((scan) => scan.risk_score < 30).length,
              icon: CheckCircle,
              tone: 'text-rose-200',
              panel: 'from-rose-400/15 to-fuchsia-400/5',
            },
          ].map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className={`card-hover rounded-2xl border border-white/10 bg-gradient-to-br ${stat.panel} p-4 sm:p-5`}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium text-slate-400 sm:text-sm">{stat.label}</p>
                    <p className="mt-2 text-3xl font-bold">{stat.value}</p>
                  </div>
                  <Icon className={`${stat.tone} opacity-80`} size={28} />
                </div>
              </div>
            );
          })}
        </div>

        <section className="mb-10">
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold">Projects</h2>
              <p className="mt-1 text-sm text-slate-400">Create repositories and launch security scans.</p>
            </div>
            <button
              onClick={() => setShowNewProject(!showNewProject)}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-4 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/15 hover:shadow-lg hover:shadow-cyan-500/10"
            >
              <Plus size={20} />
              New Project
            </button>
          </div>

          {showNewProject && (
            <div className="mb-6 rounded-3xl border border-cyan-200/20 bg-slate-950/70 p-5 shadow-2xl shadow-cyan-950/20 sm:p-6">
              <h3 className="mb-4 text-lg font-semibold">Create New Project</h3>
              <div className="mb-4 rounded-2xl border border-emerald-200/20 bg-emerald-300/5 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-semibold text-slate-100">Import from GitHub</p>
                    <p className="text-sm text-slate-500">Select a connected GitHub repository or paste a URL below.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void loadGitHubRepos()}
                    disabled={githubReposLoading}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-4 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <GitBranch size={18} />
                    {githubReposLoading ? 'Loading...' : 'Load Repos'}
                  </button>
                </div>

                {githubRepos.length > 0 && (
                  <div className="mt-4 grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
                    <input
                      type="search"
                      placeholder="Search repositories"
                      value={repoSearch}
                      onChange={(event) => setRepoSearch(event.target.value)}
                      className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-cyan-300/60"
                    />
                    <select
                      value={selectedRepoId}
                      onChange={(event) => handleSelectGitHubRepo(event.target.value)}
                      className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none focus:border-cyan-300/60"
                    >
                      <option value="">Select GitHub repository</option>
                      {filteredGitHubRepos.map((repo) => (
                        <option key={repo.id} value={repo.id}>
                          {repo.full_name} {repo.private ? '(private)' : '(public)'}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <input
                type="text"
                placeholder="Project Name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                className="mb-3 w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60"
              />
              <input
                type="url"
                placeholder="Repository URL (optional)"
                value={newProjectUrl}
                onChange={(e) => setNewProjectUrl(e.target.value)}
                className="mb-3 w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60"
              />
              <textarea
                placeholder="Project Description (optional)"
                value={newProjectDesc}
                onChange={(e) => setNewProjectDesc(e.target.value)}
                className="mb-3 h-24 w-full resize-none rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60"
              />
              {teams.length > 0 && (
                <select
                  value={newProjectTeamId}
                  onChange={(e) => setNewProjectTeamId(e.target.value)}
                  className="mb-4 w-full rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-cyan-300/60"
                >
                  <option value="">Personal project</option>
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name}
                    </option>
                  ))}
                </select>
              )}
              <div className="flex flex-col gap-3 sm:flex-row">
                <button
                  onClick={handleCreateProject}
                  disabled={!newProjectName.trim()}
                  className="rounded-2xl border border-emerald-300/30 bg-emerald-300/10 px-6 py-3 font-semibold text-emerald-100 transition hover:bg-emerald-300/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Create
                </button>
                <button
                  onClick={handleCreateAndScan}
                  disabled={!newProjectName.trim()}
                  className="rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-6 py-3 font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Create & Scan
                </button>
                <button
                  onClick={() => setShowNewProject(false)}
                  className="rounded-2xl border border-white/10 bg-white/[0.04] px-6 py-3 font-semibold text-slate-200 transition hover:bg-white/[0.08]"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {projects.map((project) => (
              <div
                key={project.id}
                className="card-hover relative overflow-hidden rounded-3xl border border-sky-200/80 bg-white/80 p-5 shadow-[0_0_0_1px_rgba(14,165,233,0.14),0_18px_48px_rgba(14,165,233,0.16)] ring-1 ring-white/80 transition hover:border-sky-300 hover:shadow-[0_0_0_2px_rgba(14,165,233,0.22),0_24px_70px_rgba(14,165,233,0.22)] sm:p-6"
              >
                <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-sky-400 via-emerald-300 to-rose-300" />
                <div className="absolute -right-12 -top-12 h-28 w-28 rounded-full bg-sky-200/50 blur-2xl" />
                <div className="absolute -bottom-10 left-8 h-24 w-24 rounded-full bg-emerald-200/45 blur-2xl" />

                <div className="relative mb-5 flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="truncate text-xl font-bold tracking-normal text-slate-950">{project.name}</h3>
                    {project.repository_url && (
                      <p className="mt-2 truncate text-sm font-medium text-sky-700">{project.repository_url}</p>
                    )}
                  </div>
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-sky-200 bg-gradient-to-br from-sky-100 via-cyan-50 to-emerald-100 text-sky-700 shadow-inner">
                    <FolderGit2 size={22} />
                  </div>
                </div>
                {project.description && (
                  <p className="relative mb-5 line-clamp-2 rounded-2xl border border-slate-200/80 bg-white/65 px-4 py-3 text-sm font-medium leading-6 text-slate-700">
                    {project.description}
                  </p>
                )}
                <div className="relative grid gap-3 sm:grid-cols-2">
                  <Link
                    href={`/projects/${project.id}`}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 font-bold text-slate-900 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-lg hover:shadow-sky-100"
                  >
                    Details
                    <ArrowRight size={18} />
                  </Link>
                  <button
                    onClick={() => handleTriggerScan(project.id)}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-sky-200 bg-gradient-to-r from-sky-100 via-cyan-100 to-emerald-100 px-4 py-3 font-bold text-sky-800 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-cyan-100"
                  >
                    Scan Now
                    <ArrowRight size={18} />
                  </button>
                </div>
              </div>
            ))}
            {projects.length === 0 && (
              <div className="rounded-3xl border border-dashed border-white/15 bg-white/[0.03] p-8 text-center lg:col-span-2">
                <p className="text-slate-300">No projects yet. Create your first project to start scanning.</p>
              </div>
            )}
          </div>
        </section>

        <section>
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold">Recent Scans</h2>
              <p className="mt-1 text-sm text-slate-400">Review your latest security activity.</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-emerald-200 transition hover:bg-white/[0.06]"
              >
                Upload Files
                <ArrowRight size={15} />
              </Link>
              <Link
                href="/scans"
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-cyan-200 transition hover:bg-white/[0.06]"
              >
                View All
                <ArrowRight size={15} />
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {recentScans.length > 0 ? (
              recentScans.map((scan) => (
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
              ))
            ) : (
              <div className="rounded-3xl border border-dashed border-white/15 bg-white/[0.03] py-12 text-center lg:col-span-2">
                <p className="text-slate-400">No scans yet. Start by creating a project and triggering a scan.</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
