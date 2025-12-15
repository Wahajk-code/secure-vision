import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';
import { TrendingUp, Activity, AlertTriangle, Shield, Package } from 'lucide-react';

interface ChartDataPoint {
    name: string;
    weapons: number;
    fights: number;
    luggage: number;
}

interface AnalyticsPanelProps {
    data: ChartDataPoint[];
}

export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({ data }) => {
    // Calculate total stats for cards
    const totalWeapons = data.reduce((acc, curr) => acc + curr.weapons, 0);
    const totalFights = data.reduce((acc, curr) => acc + curr.fights, 0);
    const totalLuggage = data.reduce((acc, curr) => acc + curr.luggage, 0);
    const riskLevel = totalWeapons > 0 ? 'CRITICAL' : (totalFights > 0 || totalLuggage > 2) ? 'HIGH' : 'LOW';

    return (
        <div className="h-full flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar">
            
            {/* Top Stats Row */}
            <div className="grid grid-cols-4 gap-4 shrink-0">
                <StatCard 
                    label="Threat Level" 
                    value={riskLevel} 
                    icon={<AlertTriangle className={riskLevel === 'CRITICAL' ? 'text-red-400' : 'text-orange-400'} />}
                    color={riskLevel === 'CRITICAL' ? 'red' : 'orange'}
                />
                <StatCard 
                    label="Weapons" 
                    value={totalWeapons.toString()} 
                    icon={<Shield className="text-red-400" />}
                    color="red"
                />
                <StatCard 
                    label="Violence" 
                    value={totalFights.toString()} 
                    icon={<Activity className="text-orange-400" />}
                    color="orange"
                />
                <StatCard 
                    label="Abandoned" 
                    value={totalLuggage.toString()} 
                    icon={<Package className="text-yellow-400" />}
                    color="yellow"
                />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-[200px]">
                
                {/* Area Chart: Trends */}
                <div className="bg-black/40 backdrop-blur-xl p-5 rounded-3xl border border-white/5 shadow-2xl flex flex-col relative overflow-hidden group hover:border-orange-500/20 transition-all">
                    <div className="absolute inset-0 bg-gradient-to-tr from-orange-900/10 to-transparent pointer-events-none" />
                    <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2 z-10 uppercase tracking-widest opacity-80">
                        <TrendingUp size={14} className="text-orange-400" />
                        Threat Timeline
                    </h3>
                    <div className="flex-1 w-full min-h-0 z-10">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorWeapons" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="colorFights" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#f97316" stopOpacity={0.8}/>
                                        <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="colorLuggage" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#eab308" stopOpacity={0.8}/>
                                        <stop offset="95%" stopColor="#eab308" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} dy={5} />
                                <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                                <Tooltip 
                                    contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px', backdropFilter: 'blur(10px)', fontSize: '12px' }}
                                    itemStyle={{ padding: 0 }}
                                />
                                <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', paddingTop: '10px', opacity: 0.7 }} />
                                <Area type="monotone" name="Weapons" dataKey="weapons" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorWeapons)" />
                                <Area type="monotone" name="Violence" dataKey="fights" stroke="#f97316" strokeWidth={2} fillOpacity={1} fill="url(#colorFights)" />
                                <Area type="monotone" name="Luggage" dataKey="luggage" stroke="#eab308" strokeWidth={2} fillOpacity={1} fill="url(#colorLuggage)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Bar Chart: Comparisons */}
                <div className="bg-black/40 backdrop-blur-xl p-5 rounded-3xl border border-white/5 shadow-2xl flex flex-col relative overflow-hidden group hover:border-orange-500/20 transition-all">
                    <div className="absolute inset-0 bg-gradient-to-tr from-amber-900/10 to-transparent pointer-events-none" />
                    <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2 z-10 uppercase tracking-widest opacity-80">
                        <Activity size={14} className="text-amber-400" />
                        Category Distribution
                    </h3>
                    <div className="flex-1 w-full min-h-0 z-10">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} dy={5} />
                                <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                                <Tooltip 
                                    cursor={{fill: 'rgba(255,255,255,0.05)'}}
                                    contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px', backdropFilter: 'blur(10px)', fontSize: '12px' }}
                                />
                                <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', paddingTop: '10px', opacity: 0.7 }} />
                                <Bar name="Weapons" dataKey="weapons" fill="#ef4444" radius={[2, 2, 0, 0]} barSize={8} />
                                <Bar name="Violence" dataKey="fights" fill="#f97316" radius={[2, 2, 0, 0]} barSize={8} />
                                <Bar name="Luggage" dataKey="luggage" fill="#eab308" radius={[2, 2, 0, 0]} barSize={8} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

            </div>
        </div>
    );
};

const StatCard = ({ label, value, icon, color }: { label: string, value: string, icon: React.ReactNode, color: string }) => {
    const colorStyles = {
        red: 'bg-red-500/5 border-red-500/10 text-red-100 hover:bg-red-500/10',
        orange: 'bg-orange-500/5 border-orange-500/10 text-orange-100 hover:bg-orange-500/10',
        yellow: 'bg-yellow-500/5 border-yellow-500/10 text-yellow-100 hover:bg-yellow-500/10',
        blue: 'bg-blue-500/5 border-blue-500/10 text-blue-100 hover:bg-blue-500/10',
        green: 'bg-green-500/5 border-green-500/10 text-green-100 hover:bg-green-500/10',
    } as any;

    return (
        <div className={`p-4 rounded-2xl border backdrop-blur-md flex flex-col gap-1 shadow-lg transition-all duration-300 group ${colorStyles[color] || colorStyles.blue}`}>
            <div className="flex justify-between items-start mb-1">
                <span className="text-[10px] font-bold uppercase tracking-widest opacity-50 group-hover:opacity-80 transition-opacity">{label}</span>
                <div className={`p-1.5 rounded-lg bg-black/20 ${color === 'red' ? 'text-red-400' : color === 'orange' ? 'text-orange-400' : color === 'yellow' ? 'text-yellow-400' : 'text-blue-400'}`}>
                    {React.cloneElement(icon as React.ReactElement, { size: 14 })}
                </div>
            </div>
            <span className="text-2xl font-black tracking-tighter tabular-nums">{value}</span>
        </div>
    );
};
