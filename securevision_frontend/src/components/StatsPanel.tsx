
import React from 'react';
import { Activity, AlertTriangle, Shield, Terminal, Cpu } from 'lucide-react';

interface LogEntry {
    type: 'INFO' | 'WARNING' | 'CRITICAL';
    message: string;
    timestamp: string;
}

interface StatsPanelProps {
    logs: LogEntry[];
    fps: number;
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ logs, fps }) => {

    return (
        <div className="flex flex-col h-full bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl relative group overflow-hidden">
             {/* Gradient Overlay */}
             <div className="absolute inset-0 bg-gradient-to-bl from-orange-500/5 via-transparent to-blue-500/5 pointer-events-none" />

            {/* Header */}
            <div className="p-3 border-b border-white/5 bg-white/5 flex justify-between items-center backdrop-blur-md z-10">
                <div className="flex items-center gap-2">
                    <div className="p-1 rounded bg-orange-500/10">
                        <Terminal className="w-3.5 h-3.5 text-orange-400" />
                    </div>
                    <h2 className="text-xs font-black tracking-widest text-white uppercase">System Logs</h2>
                </div>
                <div className="flex items-center gap-2">
                    <Cpu size={12} className="text-slate-500" />
                    <span className="text-[10px] font-mono text-slate-400">FPS: <span className="text-white font-bold">{fps.toFixed(1)}</span></span>
                </div>
            </div>

            {/* Log Feed */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar z-10 text-xs">
                {logs.length === 0 && (
                    <div className="text-center text-slate-500 py-10 flex flex-col items-center gap-2 opacity-50">
                        <Terminal size={24} />
                        <span className="font-mono text-[10px]">Awaiting Events...</span>
                    </div>
                )}
                {logs.map((log, idx) => (
                    <div key={idx} className="flex gap-2.5 items-start animate-fade-in group/log p-2 rounded-lg hover:bg-white/5 transition-colors border border-transparent hover:border-white/5">
                        <div className={`mt-0.5 p-1 rounded-md shrink-0 ${
                            log.type === 'CRITICAL' ? 'bg-red-500/10 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.2)]' :
                            log.type === 'WARNING' ? 'bg-orange-500/10 text-orange-400' :
                            'bg-blue-500/10 text-blue-400'
                        }`}>
                            {log.type === 'CRITICAL' && <AlertTriangle size={12} />}
                            {log.type === 'WARNING' && <Shield size={12} />}
                            {log.type === 'INFO' && <Activity size={12} />}
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-baseline mb-0.5">
                                <span className={`text-[9px] font-black uppercase tracking-wider ${
                                    log.type === 'CRITICAL' ? 'text-red-400' : 
                                    log.type === 'WARNING' ? 'text-orange-400' : 'text-blue-400'
                                }`}>
                                    {log.type}
                                </span>
                                <span className="text-[9px] text-slate-600 font-mono">{log.timestamp}</span>
                            </div>
                            <p className="text-slate-300 font-medium leading-tight truncate group-hover/log:whitespace-normal group-hover/log:break-words transition-all duration-300">
                                {log.message}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
