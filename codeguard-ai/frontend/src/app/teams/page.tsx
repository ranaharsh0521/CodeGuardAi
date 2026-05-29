'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Users, Plus, Mail } from 'lucide-react';
import { teamService, Team, TeamMember } from '@/lib/team-service';
import { authService } from '@/lib/auth-service';

export default function TeamsPage() {
  const router = useRouter();
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [newTeamName, setNewTeamName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    teamService.list().then(setTeams).finally(() => setLoading(false));
  }, [router]);

  const loadMembers = async (team: Team) => {
    setSelectedTeam(team);
    const m = await teamService.members(team.id);
    setMembers(m);
  };

  const handleCreate = async () => {
    if (!newTeamName.trim()) return;
    const team = await teamService.create(newTeamName.trim());
    setTeams((prev) => [...prev, team]);
    setNewTeamName('');
    setMessage(`Team "${team.name}" created`);
  };

  const handleInvite = async () => {
    if (!selectedTeam || !inviteEmail.trim()) return;
    const res = await teamService.invite(selectedTeam.id, inviteEmail.trim());
    setMessage(res.message);
    setInviteEmail('');
    await loadMembers(selectedTeam);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300" />
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-4 py-6 text-white sm:px-6 lg:px-8">
      <header className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
        <h1 className="flex items-center gap-3 text-3xl font-bold">
          <Users className="text-cyan-200" />
          Teams
        </h1>
        <p className="mt-2 text-slate-400">Collaborate on security scans with your team</p>
      </header>

      {message && (
        <div className="mb-6 rounded-2xl border border-emerald-300/30 bg-emerald-300/10 px-4 py-3 text-emerald-100">
          {message}
        </div>
      )}

      <div className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
        <h2 className="mb-4 font-semibold">Create Team</h2>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            value={newTeamName}
            onChange={(e) => setNewTeamName(e.target.value)}
            placeholder="Team name"
            className="flex-1 rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 outline-none placeholder:text-slate-500 focus:border-cyan-300/60"
          />
          <button
            onClick={handleCreate}
            className="flex items-center justify-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-4 py-3 font-semibold text-cyan-100 hover:bg-cyan-300/15"
          >
            <Plus size={18} /> Create
          </button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-3">
          <h2 className="font-semibold text-slate-300">Your Teams</h2>
          {teams.length === 0 ? (
            <p className="text-slate-500">No teams yet. Create one above.</p>
          ) : (
            teams.map((team) => (
              <button
                key={team.id}
                onClick={() => loadMembers(team)}
                className={`w-full rounded-3xl border p-4 text-left transition ${
                  selectedTeam?.id === team.id
                    ? 'border-cyan-300/50 bg-cyan-300/10'
                    : 'border-white/10 bg-white/[0.04] hover:border-white/20'
                }`}
              >
                <p className="font-medium">{team.name}</p>
                <p className="text-sm text-slate-500">
                  {team.member_count} members - {team.role}
                </p>
              </button>
            ))
          )}
        </div>

        {selectedTeam && (
          <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
            <h2 className="mb-4 font-semibold">{selectedTeam.name} - Members</h2>
            <ul className="mb-6 space-y-2">
              {members.map((m) => (
                <li key={m.user_id} className="flex justify-between rounded-2xl border border-white/10 bg-slate-950/60 p-3 text-sm">
                  <span>{m.full_name || m.email}</span>
                  <span className="text-slate-500">{m.role}</span>
                </li>
              ))}
            </ul>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="flex-1 rounded-2xl border border-white/10 bg-slate-950/70 px-3 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-300/60"
              />
              <button
                onClick={handleInvite}
                className="flex items-center justify-center gap-1 rounded-2xl border border-emerald-300/30 bg-emerald-300/10 px-4 py-3 text-sm font-semibold text-emerald-100 hover:bg-emerald-300/15"
              >
                <Mail size={16} /> Invite
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
