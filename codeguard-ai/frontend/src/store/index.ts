'use client';

import { create } from 'zustand'


export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

interface ScanResult {
  id: number;
  project_id: number;
  status: string;
  risk_score: number;
  findings?: unknown[];
  created_at: string;
  completed_at?: string;
}

interface AppState {
  user: User | null;
  setUser: (user: User | null) => void;
  currentScan: ScanResult | null;
  setCurrentScan: (scan: ScanResult | null) => void;
  isScanning: boolean;
  setIsScanning: (isScanning: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  currentScan: null,
  setCurrentScan: (scan) => set({ currentScan: scan }),
  isScanning: false,
  setIsScanning: (isScanning) => set({ isScanning }),
}))
