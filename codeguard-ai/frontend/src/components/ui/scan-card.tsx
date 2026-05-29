import React from 'react';
import { AlertTriangle, AlertCircle, AlertOctagon, CheckCircle } from 'lucide-react';

interface Finding {
  tool: string;
  rule_id: string;
  message: string;
  file_path: string;
  line_number: number;
  severity: string;
  code_snippet?: string;
  ai_fix_suggestion?: string;
  ai_explanation?: string;
}

interface ScanCardProps {
  id: number;
  status: string;
  risk_score: number;
  findings_count: number;
  project_name: string;
  created_at: string;
  onClick: () => void;
}

export function ScanCard({
  id,
  status,
  risk_score,
  findings_count,
  project_name,
  created_at,
  onClick,
}: ScanCardProps) {
  const getRiskColor = () => {
    if (risk_score < 20) return 'text-emerald-200 bg-emerald-400/10';
    if (risk_score < 50) return 'text-amber-200 bg-amber-400/10';
    return 'text-red-200 bg-red-400/10';
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'completed':
        return <div className="rounded-full bg-emerald-400/10 px-3 py-1 text-sm text-emerald-200">Completed</div>;
      case 'running':
        return <div className="animate-pulse rounded-full bg-cyan-400/10 px-3 py-1 text-sm text-cyan-200">Running</div>;
      case 'pending':
        return <div className="rounded-full bg-white/[0.06] px-3 py-1 text-sm text-slate-300">Pending</div>;
      default:
        return <div className="rounded-full bg-red-400/10 px-3 py-1 text-sm text-red-200">Failed</div>;
    }
  };

  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-3xl border border-white/10 bg-white/[0.04] p-5 transition hover:border-cyan-300/30 hover:bg-white/[0.06] sm:p-6"
    >
      <div className="mb-5 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold text-white">{project_name}</h3>
          <p className="text-sm text-slate-500">Scan #{id}</p>
        </div>
        {getStatusBadge()}
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-2xl bg-white/[0.04] p-3">
          <p className="text-xs text-slate-400">Risk Score</p>
          <p className={`mt-1 rounded-xl px-2 py-1 text-lg font-bold ${getRiskColor()}`}>{risk_score}/100</p>
        </div>
        <div className="rounded-2xl bg-white/[0.04] p-3">
          <p className="text-xs text-slate-400">Findings</p>
          <p className="mt-1 text-2xl font-bold text-cyan-200">{findings_count}</p>
        </div>
        <div className="rounded-2xl bg-white/[0.04] p-3">
          <p className="text-xs text-slate-400">Date</p>
          <p className="mt-2 text-sm text-slate-300">{new Date(created_at).toLocaleDateString()}</p>
        </div>
      </div>
    </div>
  );
}

export function FindingItem({ finding }: { finding: Finding }) {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertOctagon className="text-red-500" size={20} />;
      case 'error':
        return <AlertTriangle className="text-red-400" size={20} />;
      case 'warning':
        return <AlertCircle className="text-yellow-400" size={20} />;
      default:
        return <CheckCircle className="text-blue-400" size={20} />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-l-4 border-red-500';
      case 'error':
        return 'border-l-4 border-red-400';
      case 'warning':
        return 'border-l-4 border-yellow-400';
      default:
        return 'border-l-4 border-blue-400';
    }
  };

  return (
    <div className={`mb-3 rounded-2xl bg-white/[0.04] p-4 ${getSeverityColor(finding.severity)}`}>
      <div className="flex items-start space-x-3">
        {getSeverityIcon(finding.severity)}
        <div className="flex-1">
          <div className="flex justify-between items-start">
            <div>
              <h4 className="text-white font-semibold">{finding.message}</h4>
              <p className="text-sm text-gray-400">
                {finding.file_path}:{finding.line_number}
              </p>
            </div>
            <span className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded">
              {finding.rule_id}
            </span>
          </div>

          {finding.code_snippet && (
            <pre className="mt-2 bg-gray-800 p-2 rounded text-xs text-gray-300 overflow-auto">
              {finding.code_snippet}
            </pre>
          )}

          {finding.ai_explanation && (
            <div className="mt-2 bg-gray-800/80 border-l-2 border-gray-500 p-2 rounded">
              <p className="text-xs text-gray-400 font-semibold">Explanation:</p>
              <p className="text-xs text-gray-300 mt-1">{finding.ai_explanation}</p>
            </div>
          )}

          {finding.ai_fix_suggestion && (
            <div className="mt-2 bg-blue-900/20 border-l-2 border-blue-500 p-2 rounded">
              <p className="text-xs text-blue-300 font-semibold">AI Fix:</p>
              <p className="text-xs text-gray-300 mt-1 whitespace-pre-wrap">{finding.ai_fix_suggestion}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
