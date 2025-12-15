import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '../components/Sidebar';
import { StatsPanel } from '../components/StatsPanel';
import { AnalyticsPanel } from '../components/AnalyticsPanel';
import { DatabaseView } from '../components/DatabaseView';
import type { DBEvent } from '../components/DatabaseView';
import { LiveEventsTable } from '../components/LiveEventsTable';
import type { LiveObject } from '../components/LiveEventsTable';
import { ToastContainer } from '../components/Toast';
import type { ToastMessage } from '../components/Toast';
import { Bell, Search, User, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

interface LogEntry {
    type: 'INFO' | 'WARNING' | 'CRITICAL';
    message: string;
    timestamp: string;
}

interface ChartDataPoint {
    name: string;
    weapons: number;
    fights: number;
    luggage: number;
}

export const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  // Navigation State
  const [activeTab, setActiveTab] = useState<'dashboard' | 'analytics'>('dashboard');

  const handleTabSwitch = (tab: 'dashboard' | 'analytics' | 'settings') => {
      if (tab === 'settings') {
          navigate('/settings');
      } else {
          setActiveTab(tab);
      }
  };

  // Application State
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [fps, setFps] = useState<number>(0);
  const [liveObjects, setLiveObjects] = useState<LiveObject[]>([]);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  
  // Notification State
  const [notifications, setNotifications] = useState<LogEntry[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  
  // Charts & DB State (Analytics Tab)
  const [chartData, setChartData] = useState<ChartDataPoint[]>(() => {
      const data = [];
      const now = new Date();
      for (let i = 6; i >= 0; i--) {
          const t = new Date(now.getTime() - i * 5 * 60000);
          data.push({ name: t.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}), weapons: 0, fights: 0, luggage: 0 });
      }
      return data;
  });

  // Dynamic Chart Update
  useEffect(() => {
      const interval = setInterval(() => {
          setChartData(prev => {
              const newData = [...prev.slice(1)]; 
              const lastTime = new Date();
              newData.push({ 
                  name: lastTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}), 
                  weapons: 0, 
                  fights: 0,
                  luggage: 0
              });
              return newData;
          });
      }, 60000);
      return () => clearInterval(interval);
  }, []);
  
  const [events, setEvents] = useState<DBEvent[]>([
       { id: 1024, event: 'SYSTEM_START', time: new Date().toLocaleTimeString(), loc: 'Server', status: 'RESOLVED' }
  ]);
  
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Toast Helper
  const addToast = useCallback((type: 'success' | 'warning' | 'error' | 'info', title: string, message: string) => {
      setToasts(prev => {
          // Anti-Spam: Check if identical toast exists
          const exists = prev.some(t => t.message === message && t.title === title);
          if (exists) return prev;
          return [...prev, { id: Date.now(), type, title, message }];
      });
  }, []);
  const removeToast = useCallback((id: number) => {
      setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const connectWebSocket = () => {
        if (ws?.readyState === WebSocket.OPEN) return;

        const socket = new WebSocket("ws://localhost:8001/ws/stats");
        setWs(socket);

        socket.onopen = () => {
             setIsConnected(true);
             addToast('success', 'System Connected', 'Successfully established connection to SecureVision Backend.');
             setLogs(prev => [{type: 'INFO', message: 'System Connected to Backend', timestamp: new Date().toLocaleTimeString()}, ...prev]);
        };
        
        socket.onclose = (e) => {
             console.log("WS Closed", e.code);
             setIsConnected(false);
             setFps(0);
             setTimeout(connectWebSocket, 3000); // Reconnect
        };

        socket.onmessage = (event) => {
            try {
                 const data = JSON.parse(event.data);
                 
                 // 1. LIVE FEED
                 if (data.type === 'LIVE_FEED' && data.objects) {
                     setLiveObjects(data.objects);
                     return;
                 }

                 // 2. FPS
                 if (data.fps) {
                     setFps(data.fps);
                 }
                 
                 // 3. Logs & Alerts
                 if (data.log) {
                     const newLog = data.log;
                     setLogs(prev => [newLog, ...prev].slice(0, 50));
                     
                     if (newLog.type === 'CRITICAL' || newLog.type === 'WARNING') {
                         handleCriticalEvent(newLog);
                         // Add to Notifications if Critical
                         if (newLog.type === 'CRITICAL') {
                             setNotifications(prev => [newLog, ...prev].slice(0, 10));
                         }
                     }
                 } else if (data.type === 'CRITICAL') {
                     const logEntry: LogEntry = {
                         type: 'CRITICAL',
                         message: data.message,
                         timestamp: data.timestamp
                     };
                     setLogs(prev => [logEntry, ...prev].slice(0, 50));
                     handleCriticalEvent(logEntry);
                     setNotifications(prev => [logEntry, ...prev].slice(0, 10));
                 }
                 
            } catch (e) {
                console.error("WS Parse Error", e);
            }
        };
  };

  useEffect(() => {
        connectWebSocket();
        return () => {
            ws?.close();
        };
  }, []);

  const handleCriticalEvent = (log: LogEntry) => {
      const time = new Date().toLocaleTimeString();
      let eventType = 'UNKNOWN';
      let title = 'Alert';
      
      if (log.message.includes('Weapon')) { eventType = 'WEAPON_DETECTED'; title = 'Weapon Detected'; }
      else if (log.message.includes('Fight')) { eventType = 'FIGHT_DETECTED'; title = 'Fight Active'; }
      else if (log.message.includes('Abandoned')) { eventType = 'LUGGAGE_ABANDONED'; title = 'Abandoned Object'; }
      
      if (eventType !== 'UNKNOWN') {
           addToast('error', title, log.message);
      }
      
      const newEvent: DBEvent = {
          id: Math.floor(Math.random() * 10000),
          event: eventType,
          time: log.timestamp || time,
          loc: 'Cam 01',
          status: 'PENDING'
      };
      
      setEvents(prev => [newEvent, ...prev].slice(0, 20));
      
      setChartData(prev => {
          const newData = [...prev];
          const lastIndex = newData.length - 1;
          // CPM: Create a shallow copy of the object to avoid mutating state directly
          if (lastIndex >= 0) {
              const lastPoint = { ...newData[lastIndex] };
              if (eventType === 'WEAPON_DETECTED') lastPoint.weapons += 1;
              if (eventType === 'FIGHT_DETECTED') lastPoint.fights += 1;
              if (eventType === 'LUGGAGE_ABANDONED') lastPoint.luggage += 1;
              newData[lastIndex] = lastPoint;
          }
          return newData;
      });
  };
  
  const handleLogout = () => {
      logout();
      navigate('/login');
  };

  return (
    <div className="flex h-screen bg-[#050505] text-slate-100 font-sans selection:bg-orange-500/30 overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-br from-orange-900/10 via-black to-[#0a0a0a] z-0" />
      <div className="absolute top-0 left-0 w-full h-full bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-30 z-0 pointer-events-none mix-blend-overlay" />
      
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      
      {/* Sidebar */}
      <div className="relative z-10 h-full border-r border-orange-500/10 bg-black/40 backdrop-blur-xl">
        <Sidebar activeTab={activeTab} onSwitch={handleTabSwitch} />
      </div>
      
      {/* Main Content */}
      <main className="flex-1 overflow-hidden flex flex-col gap-4 relative z-10 w-full">
        {/* Header with Notifications */}
        <div className="relative z-50 flex justify-between items-center shrink-0 py-2 border-b border-white/5 bg-black/20 backdrop-blur-md rounded-b-2xl px-6">
            <div className="flex flex-col">
                <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-orange-100 to-orange-200 tracking-tighter drop-shadow-sm">
                    {activeTab === 'dashboard' ? 'LIVE COMMAND' : 'ANALYTICS CORE'}
                </h2>
                <p className="text-[10px] text-orange-400/80 font-bold uppercase tracking-[0.2em]">
                    {activeTab === 'dashboard' ? 'Real-time Surveillance Grid' : 'Historical Threat Analysis'}
                </p>
            </div>
            
            <div className="flex gap-4 items-center">
                 {/* Connection Status */}
                 <div className="flex items-center gap-2">
                     <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-red-500 animate-pulse'}`} />
                     <span className="text-[10px] font-mono text-slate-400">{isConnected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}</span>
                 </div>
                 
                 {/* Notifications */}
                 <div className="relative">
                     <button 
                        onClick={() => setShowNotifications(!showNotifications)}
                        className="p-2 rounded-xl bg-white/5 hover:bg-orange-500/20 text-slate-400 hover:text-orange-400 transition-colors relative"
                     >
                         <Bell size={18} />
                         {notifications.length > 0 && (
                             <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-ping" />
                         )}
                     </button>
                     
                     {showNotifications && (
                         <div className="absolute right-0 top-full mt-2 w-80 bg-[#0a0a0a]/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl flex flex-col max-h-96 overflow-hidden z-[9999]">
                             <div className="p-3 border-b border-white/5 bg-white/5">
                                 <h4 className="text-xs font-bold text-white uppercase tracking-wider">Latest Alerts</h4>
                             </div>
                             <div className="flex-1 overflow-y-auto custom-scrollbar">
                                 {notifications.length === 0 ? (
                                     <div className="p-6 text-center text-slate-500 text-xs italic">No new notifications</div>
                                 ) : (
                                     notifications.map((n, i) => (
                                         <div key={i} className="p-3 border-b border-white/5 hover:bg-white/5 transition-colors flex gap-3">
                                             <div className="w-1 bg-red-500 rounded-full" />
                                             <div className="flex-1">
                                                 <p className="text-xs text-slate-300 leading-tight">{n.message}</p>
                                                 <span className="text-[9px] text-slate-500 font-mono mt-1 block">{n.timestamp}</span>
                                             </div>
                                         </div>
                                     ))
                                 )}
                             </div>
                         </div>
                     )}
                 </div>
                 
                 {/* User Profile / Logout */}
                 <div className="flex items-center gap-3 pl-4 border-l border-white/5">
                     <div className="text-right hidden md:block">
                         <p className="text-sm font-bold text-white leading-none">{user?.username || 'Admin'}</p>
                         <p className="text-[10px] text-orange-400 uppercase tracking-wider">{user?.role || 'Operator'}</p>
                     </div>
                     <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-orange-500 to-amber-600 p-[1px]">
                         <div className="w-full h-full rounded-full bg-black flex items-center justify-center">
                             <User size={16} className="text-orange-400" />
                         </div>
                     </div>
                     <button onClick={handleLogout} className="p-2 text-slate-500 hover:text-red-400 transition-colors">
                         <LogOut size={18} />
                     </button>
                 </div>
            </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 min-h-0 flex gap-4">
            {activeTab === 'dashboard' ? (
                <div className="flex-1 grid grid-cols-2 gap-4 h-full p-4 overflow-hidden">
                    {/* Left: Live Events */}
                    <div className="bg-black/20 border border-white/5 rounded-3xl backdrop-blur-sm overflow-hidden shadow-2xl">
                        <LiveEventsTable objects={liveObjects} />
                    </div>
                    
                    {/* Right: Stats Panel */}
                    <div className="bg-black/20 border border-white/5 rounded-3xl backdrop-blur-sm overflow-hidden shadow-2xl p-1">
                            <StatsPanel logs={logs} fps={fps} />
                    </div>
                </div>
            ) : (
                <div className="flex-1 grid grid-cols-2 gap-4 h-full p-4 overflow-hidden">
                    <div className="col-span-1 h-full bg-black/20 border border-white/5 rounded-3xl backdrop-blur-sm overflow-hidden shadow-2xl p-4">
                        <AnalyticsPanel data={chartData} />
                    </div>
                    <div className="col-span-1 h-full bg-black/20 border border-white/5 rounded-3xl backdrop-blur-sm overflow-hidden shadow-2xl">
                        <DatabaseView events={events} />
                    </div>
                </div>
            )}
        </div>
      </main>
    </div>
  );
};
