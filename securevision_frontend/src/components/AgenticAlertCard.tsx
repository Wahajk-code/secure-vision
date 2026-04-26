import React from 'react';
import { AlertTriangle, BrainCircuit, ShieldAlert } from 'lucide-react';

export interface AgenticIncident {
    incident_id: string;
    incident_title: string;
    timeline_summary: string;
    recommended_next_step: string;
    detections_count: number;
    evidence_count: number;
    max_confidence?: number;
    camera_name?: string;
    sector?: string;
    area?: string;
}

export interface AgenticAlertPayload {
    type: 'AGENTIC_ALERT';
    triage: {
        dashboard_title: string;
        operator_summary: string;
        risk_explanation: string;
        recommended_priority: string;
        tts_message: string;
        requires_operator_review: boolean;
        severity?: string;
    };
    incident: AgenticIncident;
    actions: {
        action_plan: string[];
        operator_note: string;
        escalation_hint: string;
    };
    original_event: {
        event_type: string;
        severity: string;
        risk_level: string;
        risk_score: number;
        camera_name?: string;
        camera_id?: string;
        sector?: string;
        area?: string;
    };
}

interface AgenticAlertCardProps {
    alert: AgenticAlertPayload;
}

export const AgenticAlertCard: React.FC<AgenticAlertCardProps> = ({ alert }) => {
    const location = [
        alert.original_event.camera_name || alert.original_event.camera_id,
        alert.original_event.sector,
        alert.original_event.area,
    ].filter(Boolean).join(' / ');

    return (
        <div className="rounded-2xl border border-orange-500/20 bg-orange-500/5 p-4 backdrop-blur-md">
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                    <div className="mt-0.5 rounded-xl border border-orange-500/20 bg-orange-500/10 p-2">
                        <BrainCircuit className="h-4 w-4 text-orange-300" />
                    </div>
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-[0.25em] text-orange-300/80">Agentic Alert</p>
                        <h3 className="mt-1 text-sm font-black text-white">{alert.triage.dashboard_title}</h3>
                        <p className="mt-1 text-xs leading-relaxed text-slate-300">{alert.triage.operator_summary}</p>
                    </div>
                </div>
                <span className="rounded-full border border-red-500/20 bg-red-500/10 px-2 py-1 text-[10px] font-black uppercase tracking-widest text-red-200">
                    {alert.original_event.severity}
                </span>
            </div>

            <div className="mt-3 grid gap-3 lg:grid-cols-2">
                <div className="rounded-xl bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-wider text-slate-400">
                        <ShieldAlert className="h-3.5 w-3.5 text-orange-300" />
                        Risk Context
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-slate-300">{alert.triage.risk_explanation}</p>
                    <p className="mt-2 text-[11px] font-mono text-orange-200">
                        Priority: {alert.triage.recommended_priority} | Score: {alert.original_event.risk_score}
                    </p>
                </div>

                <div className="rounded-xl bg-black/30 p-3">
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-wider text-slate-400">
                        <AlertTriangle className="h-3.5 w-3.5 text-orange-300" />
                        Incident Context
                    </div>
                    <p className="mt-2 text-xs text-slate-300">{alert.incident.timeline_summary}</p>
                    <p className="mt-2 text-[11px] font-mono text-slate-400">{location || 'Location unavailable'}</p>
                </div>
            </div>
        </div>
    );
};
