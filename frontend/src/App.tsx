import { useState, useEffect } from 'react';
import { useTelemetry } from './hooks/useTelemetry';
import { DevTelemetryOverlay } from './components/DevTelemetryOverlay';
import { CognitiveDashboard } from './components/CognitiveDashboard';
import { FeedbackPopup } from './components/FeedbackPopup';
import { GatewayHealth } from './components/GatewayHealth';
import { BenchmarkMetrics } from './components/BenchmarkMetrics';
import { SessionSummaryCard } from './components/SessionSummaryCard';
import { FeatureImportance } from './components/FeatureImportance';
import { DemoControlPanel } from './components/DemoControlPanel';
import { BrainCircuit, LogOut, BarChart3, Activity } from 'lucide-react';
import { useAuthStore } from './store/useAuthStore';
import { useCognitiveStore } from './store/useCognitiveStore';
import { Login } from './components/Auth/Login';
import { Register } from './components/Auth/Register';
import { HistoricalAnalytics } from './components/HistoricalAnalytics';

function App() {
  const [initializing, setInitializing] = useState(true);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [activeTab, setActiveTab] = useState<'live' | 'history'>('live');
  const { isAuthenticated, logout } = useAuthStore();
  const { isDeepWorkMode } = useCognitiveStore();
  
  // Initialize the telemetry tracker hook only if authenticated
  useTelemetry();

  // Dark Startup Animation
  useEffect(() => {
    const timer = setTimeout(() => setInitializing(false), 1800);
    return () => clearTimeout(timer);
  }, []);

  if (!isAuthenticated) {
    if (authMode === 'login') {
      return <Login onSwitch={() => setAuthMode('register')} />;
    }
    return <Register onSwitch={() => setAuthMode('login')} />;
  }

  if (initializing) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center text-white select-none">
        <BrainCircuit className="w-12 h-12 text-emerald-400 animate-pulse mb-8" />
        <h2 className="text-sm font-medium tracking-[0.2em] text-gray-400 uppercase">
          Initializing Behavioral Signal Engine...
        </h2>
      </div>
    );
  }

  return (
    <div className={`min-h-screen flex flex-col p-6 md:p-8 font-sans transition-all duration-1000 ${isDeepWorkMode ? 'bg-[#fcfdfd] text-gray-500' : 'bg-[#f8f9fa] text-gray-900'}`}>
      
      {/* Deep Work Ambient Banner */}
      {isDeepWorkMode && (
        <div className="fixed top-0 left-0 w-full h-1 bg-emerald-400 opacity-50 z-50"></div>
      )}

      {/* Top Bar */}
      <header className={`w-full flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8 transition-opacity duration-1000 ${isDeepWorkMode ? 'opacity-30' : 'opacity-100'}`}>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <BrainCircuit className={`w-7 h-7 ${isDeepWorkMode ? 'text-gray-400' : 'text-indigo-600'}`} />
            <h1 className="text-xl font-bold tracking-tight">
              Cognitive Load AI
              {isDeepWorkMode && <span className="ml-3 text-xs font-normal uppercase tracking-widest text-emerald-500">Deep Work Active</span>}
            </h1>
          </div>
          
          {/* Navigation Tabs */}
          {!isDeepWorkMode && (
            <div className="flex bg-gray-100 p-1 rounded-lg">
              <button onClick={() => setActiveTab('live')} className={`px-4 py-1.5 text-sm font-medium rounded-md flex items-center gap-2 transition-all ${activeTab === 'live' ? 'bg-white shadow-sm text-gray-800' : 'text-gray-500 hover:text-gray-700'}`}>
                <Activity className="w-4 h-4" /> Live
              </button>
              <button onClick={() => setActiveTab('history')} className={`px-4 py-1.5 text-sm font-medium rounded-md flex items-center gap-2 transition-all ${activeTab === 'history' ? 'bg-white shadow-sm text-gray-800' : 'text-gray-500 hover:text-gray-700'}`}>
                <BarChart3 className="w-4 h-4" /> History
              </button>
            </div>
          )}
          
          <button onClick={logout} className="text-xs text-gray-400 hover:text-red-500 flex items-center gap-1 transition-colors">
            <LogOut className="w-3 h-3" /> Disconnect
          </button>
        </div>
        
        {!isDeepWorkMode && (
          <div className="flex flex-col sm:flex-row items-end sm:items-center gap-6">
            <BenchmarkMetrics />
            <GatewayHealth />
          </div>
        )}
      </header>

      {/* Main Command Center Layout */}
      <div className={`flex-1 flex flex-col xl:flex-row gap-6 w-full mx-auto transition-all duration-1000 ${isDeepWorkMode ? 'max-w-[1000px]' : 'max-w-[1600px]'}`}>
        
        {activeTab === 'live' ? (
          <>
            {/* Center: Intelligence Pipeline */}
            <div className={`flex-1 flex flex-col gap-6 min-w-0 transition-all duration-1000 ${isDeepWorkMode ? 'scale-[1.02]' : 'scale-100'}`}>
              <CognitiveDashboard />
              
              {!isDeepWorkMode && (
                <div className="w-full bg-white rounded-xl shadow-sm border border-gray-100 p-6 mt-auto">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Manual Telemetry Generation Area</h3>
                  <textarea 
                    className="w-full h-32 p-4 border border-gray-100 bg-gray-50 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:bg-white focus:border-transparent outline-none transition-all resize-none font-mono text-sm text-gray-600"
                    placeholder="Start typing here to generate manual keyboard telemetry events, or use the Demo Control Panel for orchestrated scenarios..."
                  />
                </div>
              )}
            </div>

            {/* Side Panel: Context & Control */}
            <div className={`w-full xl:w-[320px] shrink-0 flex flex-col gap-6 transition-all duration-1000 ${isDeepWorkMode ? 'opacity-0 w-0 overflow-hidden hidden' : 'opacity-100'}`}>
              <DemoControlPanel />
              <SessionSummaryCard />
              <FeatureImportance />
            </div>
          </>
        ) : (
          <HistoricalAnalytics />
        )}
        
      </div>

      {/* Dev Tools & Modals */}
      <DevTelemetryOverlay />
      <FeedbackPopup />
    </div>
  );
}

export default App;
