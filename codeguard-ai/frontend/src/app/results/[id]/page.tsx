'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, CheckCircle, Download, Trash2, Loader2, GitCompare, ShieldCheck } from 'lucide-react';
import { scanService, FindingWorkflowUpdate, ScanComparison, ScanResults } from '@/lib/scan-service';
import { authService } from '@/lib/auth-service';
import { reportService } from '@/lib/report-service';
import { useScanStatus } from '@/lib/hooks/use-scan-status';
import { useScanWebSocket } from '@/lib/hooks/use-scan-websocket';
import { FindingItem } from '@/components/ui/scan-card';

export default function ScanResultsPage() {
  const router = useRouter();
  const params = useParams();
  const scanId = parseInt(params.id as string);

  const [scanResults, setScanResults] = useState<ScanResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [downloading, setDownloading] = useState<'pdf' | 'json' | null>(null);
  const [comparison, setComparison] = useState<ScanComparison | null>(null);
  const [workflowSaving, setWorkflowSaving] = useState<number | null>(null);

  const { status: liveStatus, isComplete } = useScanStatus(scanId);
  const { event: wsEvent, connected: wsConnected } = useScanWebSocket(scanId);

  const loadResults = useCallback(async () => {
    const results = await scanService.getScanResult(scanId);
    setScanResults(results);
    if (results.status === 'completed') {
      try {
        const comparisonData = await scanService.compareScan(scanId);
        setComparison(comparisonData);
      } catch {
        setComparison(null);
      }
    } else {
      setComparison(null);
    }
    return results;
  }, [scanId]);

  useEffect(() => {
    const init = async () => {
      try {
        if (!authService.isAuthenticated()) {
          router.push('/login');
          return;
        }
        await loadResults();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load scan results');
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [scanId, router, loadResults]);

  // Refresh full results when scan completes (polling or WebSocket)
  useEffect(() => {
    if (isComplete || wsEvent?.status === 'completed' || wsEvent?.status === 'failed') {
      const timer = window.setTimeout(() => {
        loadResults().catch(() => {});
      }, 0);
      return () => window.clearTimeout(timer);
    }
  }, [isComplete, wsEvent?.status, loadResults]);

  const handleDelete = async () => {
    if (!confirm('Delete this scan permanently?')) return;
    try {
      await scanService.deleteScan(scanId);
      router.push('/scans');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete scan');
    }
  };

  const handleDownload = async (type: 'pdf' | 'json') => {
    setDownloading(type);
    try {
      if (type === 'pdf') await reportService.downloadPdf(scanId);
      else await reportService.downloadJson(scanId);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setDownloading(null);
    }
  };

  const handleWorkflowUpdate = async (findingIndex: number, data: FindingWorkflowUpdate) => {
    setWorkflowSaving(findingIndex);
    try {
      const response = await scanService.updateFindingWorkflow(scanId, findingIndex, data);
      setScanResults((current) => {
        if (!current) return current;
        const nextFindings = [...current.findings];
        nextFindings[findingIndex] = response.finding;
        return { ...current, findings: nextFindings };
      });
      setError('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update finding status');
    } finally {
      setWorkflowSaving(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300"></div>
      </div>
    );
  }

  if (error && !scanResults) {
    return (
      <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <button
            onClick={() => router.back()}
            className="mb-8 flex items-center gap-2 text-cyan-200 transition hover:text-cyan-100"
          >
            <ArrowLeft size={20} />
            <span>Back</span>
          </button>
          <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-6 py-4 text-red-100">
            {error}
          </div>
        </div>
      </div>
    );
  }

  if (!scanResults) return null;

  const displayStatus = liveStatus?.status || scanResults.status;
  const displayRisk = liveStatus?.risk_score ?? scanResults.risk_score;
  const displayError = liveStatus?.error_message || scanResults.error_message;
  const isRunning = displayStatus === 'running' || displayStatus === 'pending';
  const findings = scanResults.findings || [];

  const severityCounts = {
    critical: findings.filter((f) => f.severity === 'critical').length,
    error: findings.filter((f) => f.severity === 'error').length,
    warning: findings.filter((f) => f.severity === 'warning').length,
    info: findings.filter((f) => f.severity === 'info').length,
  };

  const filteredFindings =
    filterSeverity === 'all'
      ? findings.map((finding, index) => ({ finding, index }))
      : findings.map((finding, index) => ({ finding, index })).filter((item) => item.finding.severity === filterSeverity);

  const workflowCounts = {
    open: findings.filter((finding) => !finding.workflow_status || finding.workflow_status === 'open').length,
    resolved: findings.filter((finding) => finding.workflow_status === 'resolved').length,
    ignored: findings.filter((finding) => finding.workflow_status === 'ignored').length,
    falsePositive: findings.filter((finding) => finding.workflow_status === 'false_positive').length,
  };

  const getRiskLevel = (score: number) => {
    if (score < 20) return 'Low Risk';
    if (score < 50) return 'Medium Risk';
    if (score < 80) return 'High Risk';
    return 'Critical Risk';
  };

  return (
    <div className="min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <button
          onClick={() => router.back()}
          className="mb-8 flex items-center gap-2 text-cyan-200 transition hover:text-cyan-100"
        >
          <ArrowLeft size={20} />
          <span>Back</span>
        </button>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-red-100">
            {error}
          </div>
        )}

        <div className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
          <div className="flex flex-wrap justify-between items-start gap-4 mb-8">
            <div>
              <h1 className="text-4xl font-bold mb-2">Scan Results</h1>
              <p className="text-slate-400">Scan #{scanResults.id}</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <span
                className={`px-4 py-2 rounded-full font-semibold capitalize flex items-center gap-2 ${
                  displayStatus === 'completed'
                    ? 'border border-emerald-300/30 bg-emerald-300/10 text-emerald-100'
                    : displayStatus === 'running' || displayStatus === 'pending'
                    ? 'border border-cyan-300/30 bg-cyan-300/10 text-cyan-100'
                    : 'border border-white/10 bg-white/[0.06] text-slate-300'
                }`}
              >
                {isRunning && <Loader2 className="animate-spin" size={16} />}
                {displayStatus}
              </span>
              {displayStatus === 'completed' && (
                <>
                  <button
                    onClick={() => handleDownload('pdf')}
                    disabled={!!downloading}
                    className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-950/60 px-4 py-2 text-sm transition hover:bg-white/[0.08]"
                  >
                    <Download size={16} />
                    PDF
                  </button>
                  <button
                    onClick={() => handleDownload('json')}
                    disabled={!!downloading}
                    className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-950/60 px-4 py-2 text-sm transition hover:bg-white/[0.08]"
                  >
                    <Download size={16} />
                    JSON
                  </button>
                </>
              )}
              <button
                onClick={handleDelete}
                className="flex items-center gap-2 rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-2 text-sm text-red-100 transition hover:bg-red-500/15"
              >
                <Trash2 size={16} />
                Delete
              </button>
            </div>
          </div>

          {isRunning && (
            <div className="mb-6 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 p-4 text-sm text-cyan-100">
              <div className="flex justify-between items-center mb-2">
                <span>Scan in progress…</span>
                {wsConnected && <span className="text-xs text-emerald-400">Live</span>}
              </div>
              {wsEvent && (
                <div className="mt-2">
                  <div className="mb-1 h-2 w-full rounded-full bg-slate-950/70">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${wsEvent.progress || 0}%` }}
                    />
                  </div>
                  <p>{wsEvent.message} ({wsEvent.progress}%)</p>
                </div>
              )}
              {!wsEvent && liveStatus && (
                <p className="mt-1">{liveStatus.findings_count} findings so far (polling)</p>
              )}
            </div>
          )}

          {displayStatus === 'failed' && (
            <div className="mb-6 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">
              <p className="font-semibold mb-1">Scan failed</p>
              <p>{displayError || 'The scan could not be completed. Start a new scan after checking the repository URL or uploaded files.'}</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-2xl bg-slate-950/50 p-4">
              <p className="mb-2 text-sm text-slate-400">Risk Score</p>
              <p className="text-4xl font-bold">{displayRisk}/100</p>
              <p className="text-sm mt-2 text-yellow-400">{getRiskLevel(displayRisk)}</p>
            </div>
            <div className="rounded-2xl bg-slate-950/50 p-4">
              <p className="mb-2 text-sm text-slate-400">Total Findings</p>
              <p className="text-4xl font-bold">{findings.length}</p>
            </div>
            <div className="rounded-2xl bg-slate-950/50 p-4">
              <p className="mb-2 text-sm text-slate-400">Scan Date</p>
              <p className="text-lg">{new Date(scanResults.created_at).toLocaleString()}</p>
            </div>
          </div>

          {scanResults.quality_gate_result && (
            <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/50 p-4">
              <div className="mb-3 flex items-center gap-2">
                <ShieldCheck size={18} className={scanResults.quality_gate_result.passed ? 'text-emerald-300' : 'text-amber-300'} />
                <h2 className="font-semibold">Quality Gate</h2>
              </div>
              <p className="text-sm text-slate-300">{scanResults.quality_gate_result.summary || 'Quality gate result saved for this scan.'}</p>
            </div>
          )}
        </div>

        {!isRunning && displayStatus !== 'failed' && (
          <>
            {comparison && (
              <div className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
                <div className="mb-4 flex items-center gap-2">
                  <GitCompare className="text-cyan-200" size={20} />
                  <h2 className="text-xl font-bold">Scan Comparison</h2>
                </div>
                {comparison.base_scan_id ? (
                  <div className="grid gap-3 md:grid-cols-4">
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
                    <div className="rounded-2xl bg-slate-950/50 p-4">
                      <p className="text-xs text-slate-400">Unchanged</p>
                      <p className="mt-2 text-2xl font-bold text-slate-200">{comparison.unchanged_findings_count}</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No previous completed scan is available yet.</p>
                )}
              </div>
            )}

            <div className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-4">
              {(['all', 'critical', 'error', 'warning'] as const).map((sev) => (
                <button
                  key={sev}
                  onClick={() => setFilterSeverity(sev)}
                  className={`rounded-2xl border p-4 text-left transition ${
                    filterSeverity === sev
                      ? 'border-cyan-300/50 bg-cyan-300/10'
                      : 'border-white/10 bg-white/[0.04] hover:border-white/20'
                  }`}
                >
                  <p className="text-sm capitalize text-slate-400">{sev}</p>
                  <p className="text-2xl font-bold">
                    {sev === 'all' ? findings.length : severityCounts[sev as keyof typeof severityCounts]}
                  </p>
                </button>
              ))}
            </div>

            <div className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-4">
              {[
                { label: 'Open', value: workflowCounts.open, tone: 'text-red-200' },
                { label: 'Resolved', value: workflowCounts.resolved, tone: 'text-emerald-200' },
                { label: 'Ignored', value: workflowCounts.ignored, tone: 'text-slate-300' },
                { label: 'False Positive', value: workflowCounts.falsePositive, tone: 'text-blue-200' },
              ].map((item) => (
                <div key={item.label} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                  <p className="text-sm text-slate-400">{item.label}</p>
                  <p className={`mt-2 text-2xl font-bold ${item.tone}`}>{item.value}</p>
                </div>
              ))}
            </div>

            <div>
              <h2 className="text-2xl font-bold mb-6">Findings</h2>
              {filteredFindings.length > 0 ? (
                <div className="space-y-3">
                  {filteredFindings.map(({ finding, index }) => (
                    <FindingItem
                      key={`${finding.rule_id}-${finding.file_path}-${finding.line_number}-${index}`}
                      finding={finding}
                      index={index}
                      saving={workflowSaving === index}
                      onWorkflowUpdate={handleWorkflowUpdate}
                    />
                  ))}
                </div>
              ) : (
                <div className="rounded-3xl border border-emerald-300/30 bg-emerald-300/10 p-8 text-center">
                  <CheckCircle className="mx-auto mb-4 text-emerald-400" size={48} />
                  <h3 className="text-xl font-semibold text-emerald-400 mb-2">No findings</h3>
                  <p className="text-emerald-300">No security issues found in this scan.</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
