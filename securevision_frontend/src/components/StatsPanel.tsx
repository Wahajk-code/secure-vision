import React, { useState, useMemo } from 'react';
import { Camera, Maximize2, Minimize2, AlertTriangle, Shield, Cpu, Tag, Clock, Filter, Calendar } from 'lucide-react';
import { AgenticAlertCard, type AgenticAlertPayload } from './AgenticAlertCard';
import { OperatorActionCard } from './OperatorActionCard';

interface LogEntry {
    type: 'INFO' | 'WARNING' | 'CRITICAL';
    message: string;
    timestamp: string;
}

export interface CriticalImage {
    id: number;
    url: string;
    description: string;
    timestamp: string;
    capturedAtMs?: number;
    metadata?: {
        camera_id?: string;
        camera_name?: string;
        sector?: string;
        area?: string;
        stream_id?: string;
    };
}

interface StatsPanelProps {
    logs: LogEntry[]; // kept for compatibility, maybe unused visually
    fps: number;
    criticalImages?: CriticalImage[];
    latestAgenticAlert?: AgenticAlertPayload | null;
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ fps, criticalImages = [], latestAgenticAlert = null }) => {
    const [expandedImageId, setExpandedImageId] = useState<number | null>(null);
    const [selectedSession, setSelectedSession] = useState<'All' | 'Current Shift' | 'Previous Shift'>('All');
    const [selectedTimeline, setSelectedTimeline] = useState<'Anytime' | 'Last Hour' | 'Last 24h'>('Anytime');

    // Filter Logic
    const filteredImages = useMemo(() => {
        const now = Date.now();
        const currentShift = Math.floor(now / (8 * 60 * 60 * 1000));

        return criticalImages.filter((img) => {
            const capturedAt = img.capturedAtMs ?? now;
            const ageMs = now - capturedAt;
            const imageShift = Math.floor(capturedAt / (8 * 60 * 60 * 1000));

            const sessionMatches =
                selectedSession === 'All' ||
                (selectedSession === 'Current Shift' && imageShift === currentShift) ||
                (selectedSession === 'Previous Shift' && imageShift === currentShift - 1);

            const timelineMatches =
                selectedTimeline === 'Anytime' ||
                (selectedTimeline === 'Last Hour' && ageMs <= 60 * 60 * 1000) ||
                (selectedTimeline === 'Last 24h' && ageMs <= 24 * 60 * 60 * 1000);

            return sessionMatches && timelineMatches;
        });
    }, [criticalImages, selectedSession, selectedTimeline]);

    const expandedImage = filteredImages.find(img => img.id === expandedImageId) || criticalImages.find(img => img.id === expandedImageId) || null;

    return (
        <div className="flex flex-col h-full bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl relative group overflow-hidden">
             {/* Gradient Overlay */}
             <div className="absolute inset-0 bg-gradient-to-bl from-red-500/5 via-transparent to-orange-500/5 pointer-events-none" />

            {/* Header & Filters */}
            <div className="flex flex-col border-b border-white/5 bg-black/40 backdrop-blur-md z-10 shrink-0">
                <div className="p-3 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <div className="p-1 rounded bg-red-500/10 border border-red-500/20">
                            <Camera className="w-4 h-4 text-red-400" />
                        </div>
                        <h2 className="text-xs font-black tracking-widest text-white uppercase">Incident Evidence</h2>
                    </div>
                    <div className="flex items-center gap-2">
                        <Cpu size={12} className="text-slate-500" />
                        <span className="text-[10px] font-mono text-slate-400">FPS: <span className="text-white font-bold">{fps.toFixed(1)}</span></span>
                    </div>
                </div>
                
                {/* Filter Bar */}
                <div className="px-3 pb-3 flex gap-4 border-t border-white/5 pt-2">
                    {/* Session Filter */}
                    <div className="flex gap-1.5 items-center">
                        <Filter size={10} className="text-slate-500" />
                        {['All', 'Current Shift', 'Previous Shift'].map(session => (
                            <button 
                                key={session}
                                onClick={() => setSelectedSession(session as any)}
                                className={`text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded-md transition-colors ${selectedSession === session ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' : 'bg-white/5 text-slate-400 hover:bg-white/10'}`}
                            >
                                {session}
                            </button>
                        ))}
                    </div>

                    <div className="w-px bg-white/10 h-4 self-center" />

                    {/* Timeline Filter */}
                    <div className="flex gap-1.5 items-center">
                        <Calendar size={10} className="text-slate-500" />
                        {['Anytime', 'Last Hour', 'Last 24h'].map(time => (
                            <button 
                                key={time}
                                onClick={() => setSelectedTimeline(time as any)}
                                className={`text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded-md transition-colors ${selectedTimeline === time ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' : 'bg-white/5 text-slate-400 hover:bg-white/10'}`}
                            >
                                {time}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar z-10">
                <div className="grid gap-4 p-4">
                    {latestAgenticAlert && latestAgenticAlert.original_event?.severity === 'CRITICAL' && (
                        <>
                            <AgenticAlertCard alert={latestAgenticAlert} />
                            <OperatorActionCard
                                actions={latestAgenticAlert.actions.action_plan || []}
                                note={latestAgenticAlert.actions.operator_note || ''}
                                escalationHint={latestAgenticAlert.actions.escalation_hint || ''}
                            />
                        </>
                    )}

                    <div className={`${filteredImages.length > 0 ? 'grid grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 content-start gap-4 auto-rows-max' : 'flex flex-col'}`}>
                {filteredImages.length === 0 && (
                    <div className="text-center text-slate-500 py-10 flex flex-col items-center gap-2 opacity-50 h-full justify-center w-full col-span-2">
                        <Camera size={24} />
                        <span className="font-mono text-[10px]">No Critical Captures Yet...</span>
                    </div>
                )}
                {filteredImages.map((img) => (
                    <div 
                        key={img.id} 
                        className="flex flex-col rounded-xl overflow-hidden border border-white/5 bg-white/5 hover:border-red-500/30 hover:bg-white/10 transition-all duration-300"
                    >
                        {/* Image Container */}
                        <div 
                            className="relative cursor-pointer transition-all duration-500 h-24 group/img"
                            onClick={() => setExpandedImageId(img.id)}
                        >
                            <img 
                                src={img.url} 
                                alt="Critical Capture" 
                                className="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-500"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                            
                            <button className="absolute top-2 right-2 p-1.5 rounded-md bg-black/50 text-white/70 hover:text-white hover:bg-black/80 transition-colors backdrop-blur-sm opacity-0 group-hover/img:opacity-100">
                                <Maximize2 size={12} />
                            </button>
                        </div>
                        
                        {/* Metadata */}
                        <div className="p-2 flex flex-col gap-1 relative bg-black/20">
                            <div className="absolute -top-2 right-2 w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
                            
                            <div className="flex items-center gap-1.5">
                                <AlertTriangle size={10} className="text-red-400 shrink-0" />
                                <h3 className="text-[10px] font-bold text-white capitalize truncate">{img.description}</h3>
                            </div>
                                    <div className="flex items-center gap-1 text-slate-400 shrink-0">
                                        <Clock size={10} />
                                        <span className="text-[9px] font-mono">{img.timestamp}</span>
                                    </div>
                            <div className="flex items-center gap-1 text-slate-500 shrink-0">
                                <Camera size={10} />
                                <span className="text-[9px] font-mono truncate">
                                    {img.metadata?.camera_name || img.metadata?.camera_id || 'Unknown Camera'}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
                    </div>
                </div>
            </div>

            {/* FULL SCREEN MODAL */}
            {expandedImageId !== null && (
                <div 
                    className="fixed inset-0 z-[99999] bg-black/95 backdrop-blur-2xl flex items-center justify-center p-8"
                    onClick={() => setExpandedImageId(null)}
                >
                    <div 
                        className="relative w-full max-w-6xl max-h-full flex flex-col bg-[#0a0a0a] rounded-3xl border border-white/10 shadow-[0_0_50px_rgba(239,68,68,0.15)] overflow-hidden"
                        onClick={(e) => e.stopPropagation()} // Prevent clicking inner modal from closing it
                    >
                        {/* Modal Header */}
                        <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex justify-between items-center">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20">
                                    <AlertTriangle className="w-5 h-5 text-red-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-black text-white capitalize">
                                        {expandedImage?.description}
                                    </h2>
                                    <span className="text-xs text-slate-400 font-mono flex items-center gap-2">
                                        <Clock size={12} /> {expandedImage?.timestamp}
                                    </span>
                                </div>
                            </div>
                            <button 
                                onClick={() => setExpandedImageId(null)}
                                className="p-2 rounded-xl bg-white/5 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                            >
                                <Minimize2 size={20} />
                            </button>
                        </div>
                        
                        {/* Modal Image */}
                        <div className="flex-1 min-h-0 bg-black/50 overflow-hidden flex items-center justify-center p-4">
                            <img 
                                src={expandedImage?.url} 
                                alt="Expanded Evidence" 
                                className="max-w-full max-h-[70vh] object-contain rounded-xl shadow-2xl ring-1 ring-white/10"
                            />
                        </div>

                        {/* Modal Footer / Details */}
                        <div className="px-6 py-4 border-t border-white/5 bg-black/40 grid grid-cols-3 gap-4">
                            <div className="bg-white/5 rounded-xl p-3 flex items-center gap-3">
                                <Tag size={16} className="text-slate-500" />
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase font-black tracking-wider">Event Type</div>
                                    <div className="text-sm text-slate-300 capitalize">{expandedImage?.description}</div>
                                </div>
                            </div>
                            <div className="bg-white/5 rounded-xl p-3 flex items-center gap-3">
                                <Shield size={16} className="text-slate-500" />
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase font-black tracking-wider">Threat Level</div>
                                    <div className="text-sm text-red-500 font-black tracking-widest">CRITICAL</div>
                                </div>
                            </div>
                            <div className="bg-white/5 rounded-xl p-3 flex items-center gap-3">
                                <Camera size={16} className="text-slate-500" />
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase font-black tracking-wider">Source</div>
                                    <div className="text-sm text-slate-300">
                                        {expandedImage?.metadata?.camera_name || expandedImage?.metadata?.camera_id || 'Unknown Camera'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">
                                        {[expandedImage?.metadata?.sector, expandedImage?.metadata?.area].filter(Boolean).join(' / ') || 'Location unavailable'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
