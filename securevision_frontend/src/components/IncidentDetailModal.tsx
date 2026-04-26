import React from 'react';
import type { AgenticIncident } from './AgenticAlertCard';
import { X, MapPin, Activity, FileText, ShieldAlert } from 'lucide-react';

interface IncidentDetailModalProps {
    incident: AgenticIncident | null;
    onClose: () => void;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({ incident, onClose }) => {
    if (!incident) {
        return null;
    }

    const location = [
        incident.camera_name || 'Camera',
        incident.sector || 'Unknown Sector',
        incident.area || 'Unknown Area',
    ].join(' / ');

    return (
        <div className="fixed inset-0 z-[100000] flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl" onClick={onClose}>
            <div
                className="w-full max-w-3xl overflow-hidden rounded-3xl border border-white/10 bg-[#0a0a0a] shadow-[0_0_50px_rgba(249,115,22,0.12)]"
                onClick={(event) => event.stopPropagation()}
            >
                <div className="flex items-start justify-between gap-4 border-b border-white/5 bg-white/5 px-6 py-5">
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-[0.25em] text-orange-300/80">Incident Detail</p>
                        <h2 className="mt-1 text-xl font-black text-white">{incident.incident_title}</h2>
                        <p className="mt-2 text-sm text-slate-400">{location}</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="rounded-xl bg-white/5 p-2 text-slate-400 transition-colors hover:bg-orange-500/20 hover:text-orange-200"
                    >
                        <X size={18} />
                    </button>
                </div>

                <div className="grid gap-4 p-6 md:grid-cols-3">
                    <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-500">
                            <Activity size={14} className="text-orange-300" />
                            Detection Count
                        </div>
                        <p className="mt-3 text-3xl font-black tracking-tight text-white">{incident.detections_count}</p>
                        <p className="mt-1 text-xs text-slate-500">Grouped detections in the current incident window.</p>
                    </div>

                    <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-500">
                            <ShieldAlert size={14} className="text-orange-300" />
                            Evidence Count
                        </div>
                        <p className="mt-3 text-3xl font-black tracking-tight text-white">{incident.evidence_count}</p>
                        <p className="mt-1 text-xs text-slate-500">Critical evidence captures linked to this incident.</p>
                    </div>

                    <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-500">
                            <MapPin size={14} className="text-orange-300" />
                            Max Confidence
                        </div>
                        <p className="mt-3 text-3xl font-black tracking-tight text-white">
                            {typeof incident.max_confidence === 'number' ? incident.max_confidence.toFixed(2) : '0.00'}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">Highest confidence observed in this incident group.</p>
                    </div>
                </div>

                <div className="grid gap-4 border-t border-white/5 bg-black/20 p-6 md:grid-cols-2">
                    <div className="rounded-2xl bg-white/5 p-4">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-500">
                            <FileText size={14} className="text-orange-300" />
                            Timeline Summary
                        </div>
                        <p className="mt-3 text-sm leading-relaxed text-slate-300">{incident.timeline_summary}</p>
                    </div>

                    <div className="rounded-2xl bg-white/5 p-4">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-500">
                            <ShieldAlert size={14} className="text-orange-300" />
                            Recommended Next Step
                        </div>
                        <p className="mt-3 text-sm leading-relaxed text-slate-300">{incident.recommended_next_step}</p>
                    </div>
                </div>
            </div>
        </div>
    );
};
