import React, { useState } from 'react';
import { useAuthStore } from '../../store/useAuthStore';
import { BrainCircuit } from 'lucide-react';
import { apiUrl } from '../../config/env';

export const Login: React.FC<{ onSwitch: () => void }> = ({ onSwitch }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const setToken = useAuthStore((state) => state.setToken);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(apiUrl('/api/auth/login/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) throw new Error('Invalid credentials');
      const data = await res.json();
      setToken(data.access);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-200">
      <div className="flex items-center gap-3 mb-8">
        <BrainCircuit className="w-8 h-8 text-blue-500" />
        <h1 className="text-2xl font-semibold tracking-tight">Cognitive Load AI</h1>
      </div>
      <form onSubmit={handleSubmit} className="w-full max-w-sm p-6 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl">
        <h2 className="text-lg font-medium mb-6 text-slate-300">System Authentication</h2>
        {error && <div className="mb-4 text-sm text-red-400 bg-red-950/30 p-2 rounded">{error}</div>}
        <div className="space-y-4">
          <div>
            <label className="block text-xs uppercase text-slate-500 mb-1 tracking-wider">Operator ID</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors" placeholder="Enter username" />
          </div>
          <div>
            <label className="block text-xs uppercase text-slate-500 mb-1 tracking-wider">Passcode</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors" placeholder="••••••••" />
          </div>
          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded py-2 text-sm font-medium transition-colors mt-2">
            Initialize Session
          </button>
        </div>
        <div className="mt-6 text-center text-xs text-slate-500">
          Unregistered Operator? <button type="button" onClick={onSwitch} className="text-blue-400 hover:text-blue-300 ml-1">Register Identity</button>
        </div>
      </form>
    </div>
  );
};
