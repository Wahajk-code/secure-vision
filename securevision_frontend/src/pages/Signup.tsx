import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, Lock, User, ArrowRight, UserPlus } from 'lucide-react';

export const Signup = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const res = await fetch('http://localhost:8001/auth/signup', {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Signup failed');
            }

            const data = await res.json();
            login(data.access_token);
            navigate('/');
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center relative overflow-hidden">
             {/* Background Effects */}
            <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-orange-600/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/5 blur-[100px] rounded-full pointer-events-none" />
            
            <div className="w-full max-w-md p-8 bg-white/5 backdrop-blur-xl rounded-3xl border border-white/5 shadow-2xl relative z-10">
                <div className="flex flex-col items-center mb-8">
                    <div className="w-28 h-28 bg-gradient-to-tr from-orange-500/20 to-amber-500/20 rounded-full flex items-center justify-center border border-white/5 shadow-[0_0_20px_rgba(249,115,22,0.1)] mb-6">
                        <img src="/fyp_logo.png" alt="Logo" className="w-28 h-28 object-contain drop-shadow-[0_0_10px_rgba(249,115,22,0.5)]" />
                    </div>
                    <h1 className="text-2xl font-black text-white tracking-tight">NEW OPERATOR</h1>
                    <p className="text-slate-500 text-xs font-bold tracking-[0.2em] uppercase mt-1">Register for Access</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-200 text-xs font-bold text-center animate-pulse">
                            {error}
                        </div>
                    )}
                    
                    <div className="space-y-1">
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider ml-1">Username</label>
                        <div className="relative group">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-orange-400 transition-colors" />
                            <input 
                                type="text" 
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-black/40 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-orange-500/50 transition-colors"
                                placeholder="Choose ID"
                            />
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider ml-1">Password</label>
                        <div className="relative group">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-orange-400 transition-colors" />
                            <input 
                                type="password" 
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-black/40 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-orange-500/50 transition-colors"
                                placeholder="Create Password"
                            />
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        className="w-full bg-white/10 text-white font-bold py-3 rounded-xl border border-white/5 hover:bg-white/20 transition-all duration-300 flex items-center justify-center gap-2 mt-4"
                    >
                        REGISTER
                        <UserPlus size={16} />
                    </button>
                    
                    <div className="text-center mt-6">
                        <Link to="/login" className="text-xs text-slate-500 hover:text-orange-400 transition-colors font-bold tracking-wide">
                            ALREADY HAVE AN ACCOUNT? LOGIN
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
};
