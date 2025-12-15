
import React from 'react';

export const VideoFeed: React.FC = () => {
    // API URL - Hardcoded for now or use env var
    const VIDEO_URL = "http://localhost:8000/video_feed";

    return (
        <div className="relative w-full aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl border border-slate-700 group">
            <img 
                src={VIDEO_URL} 
                alt="Live Surveillance Feed" 
                className="w-full h-full object-cover" 
            />
            
            {/* Overlay Gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
            
            {/* Status Badge */}
            <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-white text-xs font-medium tracking-wide">LIVE</span>
            </div>
            
            <div className="absolute bottom-4 left-4 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                 <p className="text-sm font-semibold">Main Camera Feed</p>
                 <p className="text-xs text-slate-300">Res: 1000px (Display) / 640px (Process)</p>
            </div>
        </div>
    );
};
