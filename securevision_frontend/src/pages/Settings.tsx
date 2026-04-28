import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { User, Shield, LogOut, Trash2, ArrowLeft, Camera, Save } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';
import { ToastContainer } from '../components/Toast';
import type { ToastMessage } from '../components/Toast';

interface CameraConfig {
    id: string;
    name: string;
    sector: string;
    area: string;
    is_active: boolean;
}

export const Settings = () => {
    const { user, logout, token } = useAuth();
    const navigate = useNavigate();
    const [activeSettingsTab, setActiveSettingsTab] = useState<'profile' | 'cameras'>('cameras');
    const [cameras, setCameras] = useState<CameraConfig[]>([]);
    const [cameraStatus, setCameraStatus] = useState<string>('');
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const addToast = (type: ToastMessage['type'], title: string, message: string) => {
        setToasts(prev => {
            const exists = prev.some(toast => toast.title === title && toast.message === message);
            if (exists) return prev;
            return [...prev, { id: Date.now(), type, title, message }];
        });
    };

    const removeToast = (id: number) => {
        setToasts(prev => prev.filter(toast => toast.id !== id));
    };

    useEffect(() => {
        const fetchCameras = async () => {
            try {
                const res = await fetch('http://localhost:8001/api/cameras', {
                    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
                });
                if (res.ok) {
                    const data = await res.json();
                    setCameras(data.cameras || []);
                }
            } catch (e) {
                console.error(e);
                setCameraStatus('Camera area service unavailable');
                addToast('error', 'Camera Areas Offline', 'Backend camera configuration could not be loaded.');
            }
        };
        fetchCameras();
    }, [token]);

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

    const updateCamera = (id: string, field: keyof CameraConfig, value: string | boolean) => {
        setCameras(prev => prev.map(camera => (
            camera.id === id ? { ...camera, [field]: value } : camera
        )));
    };

    const handleSaveCameras = async () => {
        setCameraStatus('Saving camera areas...');
        try {
            const res = await fetch('http://localhost:8001/api/cameras', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ cameras })
            });
            if (res.ok) {
                const data = await res.json();
                setCameras(data.cameras || cameras);
                setCameraStatus('Camera areas saved. New alerts will use these names.');
                addToast('success', 'Camera Areas Saved', 'New alerts will use the updated camera, sector, and area names.');
            } else {
                setCameraStatus('Failed to save camera areas');
                addToast('error', 'Save Failed', 'Camera area assignments were not saved.');
            }
        } catch (e) {
            console.error(e);
            setCameraStatus('Failed to reach backend');
            addToast('error', 'Backend Unavailable', 'Could not reach the camera configuration service.');
        }
    };

    return (
        <div className="flex h-screen bg-[#050505] text-slate-100 font-sans overflow-hidden relative">
             <div className="absolute inset-0 bg-gradient-to-br from-orange-900/10 via-black to-[#0a0a0a] z-0" />
             <div className="absolute top-0 left-0 w-full h-full bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-30 z-0 pointer-events-none mix-blend-overlay" />
             <ToastContainer toasts={toasts} removeToast={removeToast} />
            
             {/* Sidebar */}
            <div className="relative z-10 h-full border-r border-orange-500/10 bg-black/40 backdrop-blur-xl">
                <Sidebar activeTab="settings" onSwitch={(tab) => {
                    if (tab === 'dashboard') navigate('/');
                    else if (tab === 'settings') navigate('/settings');
                    else navigate('/');
                }} />
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

                    <div className="flex gap-2 mb-6">
                        <button
                            onClick={() => setActiveSettingsTab('cameras')}
                            className={`px-4 py-2 rounded-xl border text-xs font-black uppercase tracking-wider transition-colors ${activeSettingsTab === 'cameras' ? 'bg-orange-500/15 border-orange-500/30 text-orange-200' : 'bg-white/5 border-white/5 text-slate-400 hover:text-white'}`}
                        >
                            Camera Areas
                        </button>
                        <button
                            onClick={() => setActiveSettingsTab('profile')}
                            className={`px-4 py-2 rounded-xl border text-xs font-black uppercase tracking-wider transition-colors ${activeSettingsTab === 'profile' ? 'bg-orange-500/15 border-orange-500/30 text-orange-200' : 'bg-white/5 border-white/5 text-slate-400 hover:text-white'}`}
                        >
                            Profile
                        </button>
                    </div>

                    {activeSettingsTab === 'cameras' ? (
                        <div className="grid gap-6">
                            <div className="p-6 rounded-3xl bg-white/5 border border-white/5 backdrop-blur-xl">
                                <div className="flex items-center justify-between gap-4 mb-6">
                                    <div>
                                        <h2 className="text-xl font-black text-white flex items-center gap-2">
                                            <Camera className="text-orange-400" size={22} />
                                            Camera Area Assignment
                                        </h2>
                                        <p className="text-xs text-slate-500 mt-1">
                                            The OpenCV window currently runs as Camera 1. Alerts will speak and display the assigned sector and area name.
                                        </p>
                                    </div>
                                    <button
                                        onClick={handleSaveCameras}
                                        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-orange-500/20 border border-orange-500/30 text-orange-100 hover:bg-orange-500/30 transition-colors text-xs font-black uppercase tracking-wider"
                                    >
                                        <Save size={14} />
                                        Save Areas
                                    </button>
                                </div>

                                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                                    {cameras.map((camera, index) => (
                                        <div key={camera.id} className="rounded-2xl bg-black/30 border border-white/5 p-4">
                                            <div className="flex items-center justify-between mb-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-300 font-black">
                                                        {index + 1}
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-bold text-white">{camera.name}</p>
                                                        <p className="text-[10px] text-slate-500 font-mono uppercase">{camera.id}</p>
                                                    </div>
                                                </div>
                                                <label className="flex items-center gap-2 text-[10px] text-slate-400 uppercase font-bold">
                                                    <input
                                                        type="checkbox"
                                                        checked={camera.is_active}
                                                        onChange={(e) => updateCamera(camera.id, 'is_active', e.target.checked)}
                                                        className="accent-orange-500"
                                                    />
                                                    Active
                                                </label>
                                            </div>

                                            <div className="grid gap-3">
                                                <label className="grid gap-1">
                                                    <span className="text-[10px] text-slate-500 uppercase font-black tracking-wider">Camera Name</span>
                                                    <input
                                                        value={camera.name}
                                                        onChange={(e) => updateCamera(camera.id, 'name', e.target.value)}
                                                        className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/40"
                                                    />
                                                </label>
                                                <label className="grid gap-1">
                                                    <span className="text-[10px] text-slate-500 uppercase font-black tracking-wider">Sector</span>
                                                    <input
                                                        value={camera.sector}
                                                        onChange={(e) => updateCamera(camera.id, 'sector', e.target.value)}
                                                        className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/40"
                                                    />
                                                </label>
                                                <label className="grid gap-1">
                                                    <span className="text-[10px] text-slate-500 uppercase font-black tracking-wider">Area / Location</span>
                                                    <input
                                                        value={camera.area}
                                                        onChange={(e) => updateCamera(camera.id, 'area', e.target.value)}
                                                        className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/40"
                                                    />
                                                </label>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {cameraStatus && (
                                    <p className="mt-4 text-xs text-orange-300 font-mono">{cameraStatus}</p>
                                )}
                            </div>
                        </div>
                    ) : (
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
                    )}
                </div>
            </main>
        </div>
    );
};
