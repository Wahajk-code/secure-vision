
import React from 'react';
import { LayoutDashboard, Settings, ShieldCheck, Activity } from 'lucide-react';

interface SidebarProps {
    activeTab: 'dashboard' | 'analytics' | 'settings';
    onSwitch: (tab: 'dashboard' | 'analytics' | 'settings') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSwitch }) => {
    return (
        <div className="w-64 h-full flex flex-col pt-2">
            {/* Logo */}
            <div className="p-4 px-6 flex items-center gap-3 mb-2">
                <div className="w-24 h-24 rounded-xl flex items-center justify-center border border-white/5 shadow-[0_0_15px_rgba(249,115,22,0.1)]">
                    <img src="/fyp_logo.png" alt="Logo" className="w-full h-full object-contain drop-shadow-[0_0_5px_rgba(249,115,22,0.5)]" />
                </div>
                <div>
                    <h1 className="text-lg font-black tracking-tight text-white">
                        SECURE<span className="text-orange-400">VISION</span>
                    </h1>
                    <span className="text-[9px] font-bold tracking-[0.2em] text-slate-500 uppercase">AI Surveillance</span>
                </div>
            </div>

            {/* Nav Items */}
            <nav className="flex-1 px-3 py-2 space-y-1">
                <NavItem 
                    icon={<LayoutDashboard />} 
                    label="Command Center" 
                    active={activeTab === 'dashboard'} 
                    onClick={() => onSwitch('dashboard')}
                />
                <NavItem 
                    icon={<Activity />} 
                    label="Analytics Core" 
                    active={activeTab === 'analytics'} 
                    onClick={() => onSwitch('analytics')}
                />
            </nav>

            {/* Bottom */}
            <div className="p-3 border-t border-white/5 mt-auto bg-black/20">
                <NavItem 
                    icon={<Settings />} 
                    label="System Config" 
                    active={activeTab === 'settings'}
                    onClick={() => onSwitch('settings')}
                />
                <div className="mt-3 p-2.5 bg-white/5 rounded-xl border border-white/5 hover:bg-white/10 transition-colors cursor-pointer group">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-orange-500/20 border border-orange-500/30 flex items-center justify-center text-xs font-black text-orange-400 group-hover:text-white transition-colors">
                            AD
                        </div>
                        <div>
                            <p className="text-xs text-white font-bold group-hover:text-orange-200 transition-colors">Admin Commander</p>
                            <p className="text-[10px] text-slate-500 font-mono">ID: OM-8832</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const NavItem: React.FC<{icon: React.ReactNode, label: string, active?: boolean, badge?: number, onClick?: () => void}> = ({icon, label, active, badge, onClick}) => (
    <button 
        onClick={onClick}
        className={`w-full flex items-center justify-between p-2.5 rounded-xl transition-all duration-300 group relative overflow-hidden ${
        active 
        ? 'bg-orange-500/10 text-orange-100 border border-orange-500/20 shadow-[0_0_15px_rgba(249,115,22,0.1)]' 
        : 'text-slate-400 hover:bg-white/5 hover:text-white border border-transparent'
    }`}>
        {active && <div className="absolute inset-0 bg-gradient-to-r from-orange-500/10 to-transparent opacity-50" />}
        <div className="flex items-center gap-3 relative z-10">
            <span className={active ? 'text-orange-400' : 'group-hover:text-white transition-colors'}>
                {React.cloneElement(icon as React.ReactElement, { size: 18 })}
            </span>
            <span className="font-bold text-xs tracking-wide">{label}</span>
        </div>
        {badge && (
            <span className="bg-red-500 text-white text-[9px] font-black px-1.5 py-0.5 rounded-md shadow-lg shadow-red-500/20">
                {badge}
            </span>
        )}
    </button>
);
