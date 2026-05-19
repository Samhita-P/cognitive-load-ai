import React, { useState, useEffect } from 'react';
import { usePrivacyStore } from '../store/usePrivacyStore';
import { useAuthStore } from '../store/useAuthStore';
import { apiUrl } from '../config/env';

export const PrivacyControls: React.FC = () => {
  const { 
    telemetryConsent, 
    privacyMode, 
    hasAnsweredConsent, 
    setTelemetryConsent, 
    setPrivacyMode, 
    setHasAnsweredConsent 
  } = usePrivacyStore();
  
  const token = useAuthStore((s) => s.token);
  const [showModal, setShowModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteSuccess, setDeleteSuccess] = useState(false);

  useEffect(() => {
    if (token) {
      fetch(apiUrl('/api/privacy/consent/'), {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        // Only set if they haven't explicitly answered locally yet?
        // Actually, always sync from server to avoid local storage state mismatch
        if (data.telemetry_consent !== undefined) {
          setTelemetryConsent(data.telemetry_consent);
          setPrivacyMode(data.privacy_mode);
          setHasAnsweredConsent(true);
        }
      })
      .catch(console.error);
    }
  }, [token, setTelemetryConsent, setPrivacyMode, setHasAnsweredConsent]);

  useEffect(() => {
    if (!hasAnsweredConsent && token) {
      setShowModal(true);
    }
  }, [hasAnsweredConsent, token]);

  const saveConsent = async (consent: boolean, mode: boolean = false) => {
    setTelemetryConsent(consent);
    setPrivacyMode(mode);
    setHasAnsweredConsent(true);
    setShowModal(false);

    try {
      await fetch(apiUrl('/api/privacy/consent/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          telemetry_consent: consent,
          privacy_mode: mode
        })
      });
    } catch (error) {
      console.error('Failed to save privacy settings', error);
    }
  };

  const handleHardDelete = async () => {
    if (!window.confirm("Are you sure? This will hard delete ALL your telemetry, predictions, and feedback from our servers. This action is irreversible.")) {
      return;
    }
    
    setIsDeleting(true);
    try {
      const res = await fetch(apiUrl('/api/privacy/telemetry/'), {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setDeleteSuccess(true);
        // Also revoke consent as a safety measure
        await saveConsent(false, true);
        setTimeout(() => setDeleteSuccess(false), 5000);
      }
    } catch (error) {
      console.error('Failed to delete telemetry', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <svg className="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
        Privacy & Governance
      </h3>
      
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-700">Privacy Mode</h4>
            <p className="text-sm text-gray-500">When enabled, no telemetry data leaves your browser.</p>
          </div>
          <button
            onClick={() => saveConsent(telemetryConsent, !privacyMode)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${privacyMode ? 'bg-indigo-600' : 'bg-gray-200'}`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${privacyMode ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        <div className="pt-4 border-t border-gray-100">
          <h4 className="font-medium text-gray-700 mb-2">Data Collection Declaration</h4>
          <div className="bg-gray-50 p-3 rounded text-sm text-gray-600">
            <p className="mb-2"><strong>We collect:</strong> ✅ interaction timing, ✅ mouse movement metrics, ✅ idle activity patterns.</p>
            <p><strong>We do NOT collect:</strong> ❌ actual keystroke content, ❌ passwords, ❌ clipboard contents, ❌ screen contents.</p>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-100">
          <h4 className="font-medium text-gray-700 mb-2">Right to be Forgotten</h4>
          <p className="text-sm text-gray-500 mb-3">
            You can request a hard deletion of all your identifiable telemetry, predictions, and feedback at any time.
          </p>
          <button
            onClick={handleHardDelete}
            disabled={isDeleting}
            className="px-4 py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded text-sm font-medium transition-colors"
          >
            {isDeleting ? 'Deleting...' : 'Delete My Telemetry'}
          </button>
          {deleteSuccess && <p className="text-green-600 text-sm mt-2">Data successfully deleted.</p>}
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 m-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-indigo-100 mb-4 mx-auto">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            </div>
            <h2 className="text-xl font-bold text-center text-gray-800 mb-2">Your Privacy Matters</h2>
            <p className="text-gray-600 text-sm text-center mb-4">
              Cognitive Load AI relies on behavioral telemetry (mouse movements, typing cadence, and idle time) to predict focus and fatigue. 
              We never record your actual keystrokes, passwords, or screen contents.
            </p>
            <p className="text-gray-600 text-sm text-center mb-6 font-medium">
              Do you consent to sharing your behavioral telemetry to enable AI predictions?
            </p>
            <div className="flex space-x-3">
              <button 
                onClick={() => saveConsent(false, true)}
                className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
              >
                Decline
              </button>
              <button 
                onClick={() => saveConsent(true, false)}
                className="flex-1 py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium transition-colors"
              >
                I Consent
              </button>
            </div>
            <p className="text-xs text-gray-400 text-center mt-4">
              You can change this anytime from the Privacy Governance settings.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
