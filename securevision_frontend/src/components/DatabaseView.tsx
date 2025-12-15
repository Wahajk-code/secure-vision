
import React, { useState, useMemo } from 'react';
import { Database, Clock, Search, Filter } from 'lucide-react';

export interface DBEvent {
    id: number;
    event: string;
    time: string;
    loc: string;
    status: 'PENDING' | 'RESOLVED' | 'FALSE_ALARM';
}

interface DatabaseViewProps {
    events: DBEvent[];
}



export const DatabaseView: React.FC<DatabaseViewProps> = ({ events }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('ALL');

    const filteredEvents = useMemo(() => {
        return events.filter(ev => {
            const matchesSearch = 
                ev.event.toLowerCase().includes(searchTerm.toLowerCase()) ||
                ev.loc.toLowerCase().includes(searchTerm.toLowerCase()) ||
                ev.id.toString().includes(searchTerm);
            
            const matchesStatus = statusFilter === 'ALL' || ev.status === statusFilter;
            
            return matchesSearch && matchesStatus;
        });
    }, [events, searchTerm, statusFilter]);

    return (
        <div className="h-full bg-black/40 backdrop-blur-xl rounded-3xl border border-white/5 shadow-2xl overflow-hidden flex flex-col relative group hover:border-orange-500/20 transition-all duration-500">
            <div className="absolute inset-0 bg-gradient-to-br from-orange-900/5 to-transparent pointer-events-none -z-10" />

            {/* Header / Toolbar */}
            <div className="p-4 border-b border-white/5 flex flex-col gap-3">
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-orange-500/10 rounded-lg">
                            <Database className="w-4 h-4 text-orange-400" />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold text-slate-200 tracking-wide uppercase">Event Logs</h2>
                        </div>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                        <input 
                            type="text" 
                            placeholder="Search Logs..." 
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-black/40 border border-white/5 rounded-lg py-1.5 pl-9 pr-3 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-orange-500/30 transition-colors"
                        />
                    </div>
                    
                    <div className="relative">
                        <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                        <select 
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="bg-black/40 border border-white/5 rounded-lg py-1.5 pl-8 pr-6 text-xs text-slate-300 focus:outline-none focus:border-orange-500/30 appearance-none cursor-pointer"
                        >
                            <option value="ALL">Status: All</option>
                            <option value="PENDING">Pending</option>
                            <option value="RESOLVED">Resolved</option>
                            <option value="FALSE_ALARM">False Alarm</option>
                        </select>
                    </div>
                </div>
            </div>
            
            {/* Table */}
            <div className="flex-1 overflow-auto p-0 custom-scrollbar">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="text-[10px] text-slate-500 uppercase tracking-wider border-b border-white/5 bg-white/2">
                            <th className="py-2 pl-4 font-bold">ID</th>
                            <th className="py-2">Type</th>
                            <th className="py-2">Time</th>
                            <th className="py-2 text-right pr-4">State</th>
                        </tr>
                    </thead>
                    <tbody className="text-xs">
                        {filteredEvents.length > 0 ? (
                            filteredEvents.map((row) => (
                                <tr key={row.id} className="border-b border-white/5 hover:bg-orange-500/5 transition-colors group">
                                    <td className="py-2.5 pl-4 font-mono text-slate-500 group-hover:text-orange-200 transition-colors">
                                        #{row.id}
                                    </td>
                                    <td className="py-2.5 font-bold text-slate-200">
                                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[9px] font-black border backdrop-blur-md ${
                                            row.event.includes('WEAPON') ? 'bg-red-500/10 border-red-500/10 text-red-300' :
                                            row.event.includes('FIGHT') ? 'bg-orange-500/10 border-orange-500/10 text-orange-300' :
                                            'bg-yellow-500/10 border-yellow-500/10 text-yellow-300'
                                        }`}>
                                            {row.event}
                                        </span>
                                    </td>
                                    <td className="py-2.5 text-slate-500 flex items-center gap-1.5">
                                        <Clock size={10} className="text-slate-600" /> {row.time}
                                    </td>
                                    <td className="py-2.5 text-right pr-4">
                                        <span className={`text-[9px] font-black uppercase tracking-wider ${
                                            row.status === 'RESOLVED' ? 'text-green-500/80' :
                                            row.status === 'PENDING' ? 'text-red-500 animate-pulse' :
                                            'text-slate-600'
                                        }`}>
                                            {row.status}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={4} className="py-8 text-center text-slate-600 text-xs italic">
                                    No records found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
