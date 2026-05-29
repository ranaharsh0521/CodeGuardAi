import { useState, useEffect, useCallback, useRef } from 'react';
import { scanService, ScanStatus } from '@/lib/scan-service';

export function useScanStatus(scanId: number | null, pollingInterval: number = 2500) {
  const [status, setStatus] = useState<ScanStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const statusRef = useRef<string | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!scanId) return;

    try {
      setLoading(true);
      const statusData = await scanService.getScanStatus(scanId);
      setStatus(statusData);
      statusRef.current = statusData.status;
      setError(null);
      return statusData;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch scan status');
      return null;
    } finally {
      setLoading(false);
    }
  }, [scanId]);

  useEffect(() => {
    if (!scanId) return;

    fetchStatus();

    const interval = setInterval(async () => {
      const current = statusRef.current;
      if (current === 'completed' || current === 'failed') return;
      await fetchStatus();
    }, pollingInterval);

    return () => clearInterval(interval);
  }, [scanId, fetchStatus, pollingInterval]);

  return {
    status,
    loading,
    error,
    refetch: fetchStatus,
    isComplete: status?.status === 'completed' || status?.status === 'failed',
  };
}
