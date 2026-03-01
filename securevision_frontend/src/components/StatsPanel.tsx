import React, { useState } from 'react';
import { Camera, Maximize2, Minimize2, AlertTriangle, Shield, Cpu, Tag, Clock } from 'lucide-react';

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
}

interface StatsPanelProps {
    logs: LogEntry[]; // kept for compatibility, maybe unused visually
    fps: number;
    criticalImages?: CriticalImage[];
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ fps, criticalImages = [] }) => {
    const [expandedImageId, setExpandedImageId] = useState<number | null>(null);

    return (
        <div className="flex flex-col h-full bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl relative group overflow-hidden">
             {/* Gradient Overlay */}
             <div className="absolute inset-0 bg-gradient-to-bl from-red-500/5 via-transparent to-orange-500/5 pointer-events-none" />

            {/* Header */}
            <div className="p-3 border-b border-white/5 bg-white/5 flex justify-between items-center backdrop-blur-md z-10 shrink-0">
                <div className="flex items-center gap-2">
                    <div className="p-1 rounded bg-red-500/10">
                        <Camera className="w-3.5 h-3.5 text-red-400" />
                    </div>
                    <h2 className="text-xs font-black tracking-widest text-white uppercase">Critical Captures</h2>
                </div>
                <div className="flex items-center gap-2">
                    <Cpu size={12} className="text-slate-500" />
                    <span className="text-[10px] font-mono text-slate-400">FPS: <span className="text-white font-bold">{fps.toFixed(1)}</span></span>
                </div>
            </div>

            {/* Image Feed Grid */}
            <div className={`flex-1 overflow-y-auto p-4 custom-scrollbar z-10 ${criticalImages.length > 0 ? 'grid grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 content-start gap-4 auto-rows-max' : 'flex flex-col'}`}>
                {criticalImages.length === 0 && (
                    <div className="text-center text-slate-500 py-10 flex flex-col items-center gap-2 opacity-50 h-full justify-center w-full col-span-2">
                        <Camera size={24} />
                        <span className="font-mono text-[10px]">No Critical Captures Yet...</span>
                    </div>
                )}
                {criticalImages.map((img) => (
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
                        </div>
                    </div>
                ))}
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
                                        {criticalImages.find(img => img.id === expandedImageId)?.description}
                                    </h2>
                                    <span className="text-xs text-slate-400 font-mono flex items-center gap-2">
                                        <Clock size={12} /> {criticalImages.find(img => img.id === expandedImageId)?.timestamp}
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
                                src={criticalImages.find(img => img.id === expandedImageId)?.url} 
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
                                    <div className="text-sm text-slate-300 capitalize">{criticalImages.find(img => img.id === expandedImageId)?.description}</div>
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
                                    <div className="text-sm text-slate-300">Cam 01 (Main Node)</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
