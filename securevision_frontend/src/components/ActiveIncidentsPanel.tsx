import React from 'react';
import type { AgenticIncident } from './AgenticAlertCard';
import { Radar, TimerReset } from 'lucide-react';

interface ActiveIncidentsPanelProps {
    incidents: AgenticIncident[];
    onSelectIncident?: (incident: AgenticIncident) => void;
}

export const ActiveIncidentsPanel: React.FC<ActiveIncidentsPanelProps> = ({ incidents, onSelectIncident }) => {
    return (
        <div className="border-t border-white/5 bg-black/20 p-4">
            <div className="mb-3 flex items-center gap-2">
                <div className="rounded-lg bg-orange-500/10 p-1.5">
                    <Radar className="h-4 w-4 text-orange-400" />
                </div>
                <div>
                    <h3 className="text-xs font-black uppercase tracking-widest text-white">Active Incidents</h3>
                    <p className="text-[10px] text-slate-500">Grouped incident windows from the agent layer</p>
                </div>
            </div>

            {incidents.length === 0 ? (
                <div className="rounded-xl border border-white/5 bg-white/5 px-3 py-4 text-center text-[11px] text-slate-500">
                    No active incidents yet.
                </div>
            ) : (
                <div className="max-h-64 overflow-y-auto pr-1 custom-scrollbar">
                    <div className="grid gap-2">
                    {incidents.map((incident) => (
                        <button
                            key={incident.incident_id}
                            type="button"
                            onClick={() => onSelectIncident?.(incident)}
                            className="rounded-xl border border-white/5 bg-white/5 px-3 py-3 text-left transition-all duration-200 hover:border-orange-500/30 hover:bg-orange-500/10 focus:outline-none focus:ring-2 focus:ring-orange-400/40"
                        >
                            <div className="flex items-start justify-between gap-3">
                                <div>
                                    <p className="text-xs font-bold text-white">{incident.incident_title}</p>
                                    <p className="mt-1 text-[11px] leading-relaxed text-slate-400">{incident.timeline_summary}</p>
                                </div>
                                <div className="text-right text-[10px] font-mono text-orange-300">
                                    <div>{incident.detections_count} detections</div>
                                    <div>{incident.evidence_count} evidence</div>
                                </div>
                            </div>
                            <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-500">
                                <TimerReset className="h-3 w-3" />
                                {incident.camera_name || 'Camera'} / {incident.sector || 'Unknown Sector'} / {incident.area || 'Unknown Area'}
                            </div>
                        </button>
                    ))}
                    </div>
                </div>
            )}
        </div>
    );
};
