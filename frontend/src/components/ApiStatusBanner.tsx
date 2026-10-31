import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';

export const ApiStatusBanner: React.FC = () => {
  const [status, setStatus] = useState<'checking' | 'connected' | 'waking' | 'offline'>('checking');
  const [show, setShow] = useState(false);

  const checkStatus = async () => {
    try {
      const res = await api.checkHealth();
      if (res && (res.status === 'ok' || res.status === 'healthy')) {
        setStatus('connected');
        setTimeout(() => setShow(false), 2500);
      } else {
        setStatus('offline');
        setShow(true);
      }
    } catch {
      setStatus('waking');
      setShow(true);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!show && status === 'connected') return null;

  return (
    <div
      className={`w-full px-4 py-2 text-xs font-medium transition-all duration-300 flex items-center justify-between ${
        status === 'waking'
          ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-b border-amber-500/20'
          : status === 'offline'
          ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-b border-rose-500/20'
          : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-b border-emerald-500/20'
      }`}
    >
      <div className="flex items-center space-x-2 mx-auto">
        {status === 'waking' && (
          <>
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span>Connecting to CIT Backend Engine (waking up if sleeping on free tier)...</span>
          </>
        )}
        {status === 'offline' && (
          <>
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Backend engine unreachable. Ensure server is running on port 8000.</span>
            <button
              onClick={checkStatus}
              className="ml-2 underline hover:opacity-80 font-bold"
            >
              Retry
            </button>
          </>
        )}
        {status === 'connected' && (
          <>
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>CIT Core Engine connected & healthy (CP-SAT Solver Ready)</span>
          </>
        )}
      </div>
    </div>
  );
};
