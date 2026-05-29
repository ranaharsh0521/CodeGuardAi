import { useEffect, useState, useCallback } from 'react';

export interface ScanProgressEvent {
  scan_id: number;
  status: string;
  progress: number;
  message: string;
  risk_score?: number;
  findings_count?: number;
}

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function useScanWebSocket(scanId: number | null) {
  const [event, setEvent] = useState<ScanProgressEvent | null>(null);
  const [connected, setConnected] = useState(false);

  const disconnect = useCallback(() => setConnected(false), []);

  useEffect(() => {
    if (!scanId) return;

    let ws: WebSocket | null = null;
    let disposed = false;

    const connectTimer = window.setTimeout(() => {
      if (disposed) return;

      ws = new WebSocket(`${WS_BASE}/ws/scan-progress?scan_id=${scanId}`);

      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as ScanProgressEvent;
          setEvent(data);
        } catch {
          /* ignore */
        }
      };
    }, 100);

    return () => {
      disposed = true;
      window.clearTimeout(connectTimer);
      if (ws && ws.readyState !== WebSocket.CLOSED) {
        ws.close();
      }
    };
  }, [scanId]);

  return { event, connected, disconnect };
}
