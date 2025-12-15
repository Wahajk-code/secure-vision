import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { User, Shield, LogOut, Trash2, ArrowLeft } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';

export const Settings = () => {
    const { user, logout, token } = useAuth();
    const navigate = useNavigate();

    const handleDeleteAccount = async () => {
        if (!window.confirm("ARE YOU SURE? This action cannot be undone.")) return;
        
        try {
            const res = await fetch('http://localhost:8001/users/me', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (res.ok) {
                logout();
                navigate('/login');
            } else {
                alert("Failed to delete account");
            }
        } catch (e) {
            console.error(e);
            alert("Error deleting account");
        }
    };

    return (
        <div className="flex h-screen bg-[#050505] text-slate-100 font-sans overflow-hidden relative">
             <div className="absolute inset-0 bg-gradient-to-br from-orange-900/10 via-black to-[#0a0a0a] z-0" />
             <div className="absolute top-0 left-0 w-full h-full bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-30 z-0 pointer-events-none mix-blend-overlay" />
            
             {/* Sidebar */}
            <div className="relative z-10 h-full border-r border-orange-500/10 bg-black/40 backdrop-blur-xl">
                <Sidebar activeTab="settings" onSwitch={(tab) => navigate(tab === 'dashboard' ? '/' : '/settings')} />
            </div>

            <main className="flex-1 p-8 relative z-10 overflow-y-auto">
                <div className="max-w-4xl mx-auto">
                    <header className="mb-8 flex items-center gap-4">
                        <button onClick={() => navigate('/')} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                            <ArrowLeft />
                        </button>
                        <div>
                            <h1 className="text-3xl font-black text-white tracking-tight">SYSTEM SETTINGS</h1>
                            <p className="text-orange-400 font-mono text-xs uppercase tracking-widest">User Profile & Configuration</p>
                        </div>
                    </header>

                    <div className="grid gap-6">
                        {/* Profile Card */}
                        <div className="p-6 rounded-3xl bg-white/5 border border-white/5 backdrop-blur-xl">
                            <div className="flex items-center gap-6">
                                <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-orange-500 to-amber-600 p-[2px]">
                                    <div className="w-full h-full rounded-[14px] bg-black flex items-center justify-center">
                                        <User size={32} className="text-orange-400" />
                                    </div>
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-white">{user?.username}</h2>
                                    <div className="flex items-center gap-2 mt-1">
                                        <Shield size={14} className="text-green-400" />
                                        <span className="text-sm font-mono text-slate-400 uppercase">{user?.role} Access</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <button 
                                onClick={logout}
                                className="p-6 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group text-left"
                            >
                                <LogOut className="w-8 h-8 text-slate-400 group-hover:text-white mb-4 transition-colors" />
                                <h3 className="text-lg font-bold text-white">Disconnect Session</h3>
                                <p className="text-sm text-slate-500 mt-1">Safe logout from current terminal</p>
                            </button>

                            <button 
                                onClick={handleDeleteAccount}
                                className="p-6 rounded-2xl bg-red-500/5 border border-red-500/10 hover:bg-red-500/10 transition-all group text-left"
                            >
                                <Trash2 className="w-8 h-8 text-red-500/60 group-hover:text-red-500 mb-4 transition-colors" />
                                <h3 className="text-lg font-bold text-red-400 group-hover:text-red-300">Terminate Protocol</h3>
                                <p className="text-sm text-red-500/60 mt-1">Permanently delete user account</p>
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};
