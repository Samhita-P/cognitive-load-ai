import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface PrivacyState {
  telemetryConsent: boolean;
  privacyMode: boolean;
  consentVersion: string;
  hasAnsweredConsent: boolean;
  setTelemetryConsent: (consent: boolean) => void;
  setPrivacyMode: (mode: boolean) => void;
  setHasAnsweredConsent: (answered: boolean) => void;
}

export const usePrivacyStore = create<PrivacyState>()(
  persist(
    (set) => ({
      telemetryConsent: false,
      privacyMode: false,
      consentVersion: '1.0',
      hasAnsweredConsent: false,
      setTelemetryConsent: (consent) => set({ telemetryConsent: consent }),
      setPrivacyMode: (mode) => set({ privacyMode: mode }),
      setHasAnsweredConsent: (answered) => set({ hasAnsweredConsent: answered }),
    }),
    {
      name: 'privacy-storage',
    }
  )
);
