import React from 'react';
import { Shield, AlertTriangle, User, Clock, Package, Eye } from 'lucide-react';

export interface LiveObject {
    id: number;
    category: string;
    details: string;
    status: 'Normal' | 'WARNING' | 'CRITICAL';
}

interface LiveEventsTableProps {
    objects: LiveObject[];
}

export const LiveEventsTable: React.FC<LiveEventsTableProps> = ({ objects }) => {
    return (
        <div className="h-full flex flex-col relative group">
            {/* Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-tr from-orange-500/5 via-transparent to-amber-500/5 pointer-events-none" />
            
            {/* Header */}
            <div className="p-4 border-b border-white/5 bg-white/5 z-10 flex justify-between items-center backdrop-blur-md">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-orange-500/10 rounded-lg">
                        <Eye className="w-4 h-4 text-orange-400" />
                    </div>
                    <div>
                        <h2 className="text-sm font-black text-white tracking-widest uppercase">Live Targets</h2>
                    </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-black/40 rounded-full border border-green-500/20 shadow-[0_0_10px_rgba(34,197,94,0.1)]">
                    <span className="flex h-1.5 w-1.5 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500"></span>
                    </span>
                    <span className="text-[10px] font-mono text-green-400 font-bold tracking-widest">ACTIVE FEED</span>
                </div>
            </div>
            
            {/* Content */}
            <div className="flex-1 overflow-auto p-0 custom-scrollbar z-10">
                {objects.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-2">
                        <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center animate-pulse border border-white/5">
                            <Shield className="w-5 h-5 opacity-20" />
                        </div>
                        <p className="text-xs font-mono uppercase tracking-widest opacity-50">Scanning Area...</p>
                    </div>
                ) : (
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-[10px] text-slate-500 uppercase tracking-widest border-b border-white/5 bg-white/2 sticky top-0 backdrop-blur-md">
                                <th className="py-2 pl-4 font-bold">Target ID</th>
                                <th className="py-2">Classification</th>
                                <th className="py-2">Details / Conf</th>
                                <th className="py-2 text-right pr-4">Threat Lvl</th>
                            </tr>
                        </thead>
                        <tbody className="text-xs font-medium">
                            {objects.map((obj) => (
                                <tr key={obj.id} className="border-b border-white/5 hover:bg-orange-500/10 transition-colors group">
                                    <td className="py-2.5 pl-4 font-mono text-slate-400 group-hover:text-orange-200 transition-colors">
                                        <span className="opacity-50">#</span>{obj.id}
                                    </td>
                                    
                                    <td className="py-2.5">
                                        <div className="flex items-center gap-2">
                                            {obj.category.includes('person') && <User size={12} className="text-blue-400" />}
                                            {obj.category.includes('suitcase') && <Package size={12} className="text-yellow-400" />}
                                            {['gun', 'knife', 'bat'].some(w => obj.category.includes(w)) && <AlertTriangle size={12} className="text-red-400 animate-pulse" />}
                                            <span className="capitalize text-slate-200">{obj.category}</span>
                                        </div>
                                    </td>
                                    
                                    <td className="py-2.5 font-mono text-slate-400">
                                        {obj.details}
                                    </td>
                                    
                                    <td className="py-2.5 text-right pr-4">
                                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider border backdrop-blur-md ${
                                            obj.status === 'CRITICAL' ? 'bg-red-500/10 border-red-500/20 text-red-200 shadow-[0_0_15px_rgba(239,68,68,0.2)] animate-pulse' :
                                            obj.status === 'WARNING' ? 'bg-orange-500/10 border-orange-500/20 text-orange-200' :
                                            'bg-blue-500/5 border-blue-500/10 text-blue-300 opacity-60'
                                        }`}>
                                            {obj.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};
