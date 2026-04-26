import React from 'react';
import { ClipboardList, CornerDownRight } from 'lucide-react';

interface OperatorActionCardProps {
    actions: string[];
    note: string;
    escalationHint: string;
}

export const OperatorActionCard: React.FC<OperatorActionCardProps> = ({ actions, note, escalationHint }) => {
    return (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md">
            <div className="flex items-center gap-2">
                <div className="rounded-lg border border-orange-500/20 bg-orange-500/10 p-1.5">
                    <ClipboardList className="h-4 w-4 text-orange-300" />
                </div>
                <div>
                    <h3 className="text-xs font-black uppercase tracking-widest text-white">Operator Actions</h3>
                    <p className="text-[10px] text-slate-500">System-approved steps with agent wording</p>
                </div>
            </div>

            <div className="mt-3 grid gap-2">
                {actions.map((action, index) => (
                    <div key={`${action}-${index}`} className="flex items-start gap-2 rounded-xl bg-black/30 px-3 py-2 text-xs text-slate-200">
                        <CornerDownRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-orange-300" />
                        <span>{action}</span>
                    </div>
                ))}
            </div>

            <div className="mt-3 rounded-xl bg-black/30 p-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Operator Note</p>
                <p className="mt-1 text-xs text-slate-300">{note}</p>
                <p className="mt-2 text-[11px] text-orange-200">{escalationHint}</p>
            </div>
        </div>
    );
};
