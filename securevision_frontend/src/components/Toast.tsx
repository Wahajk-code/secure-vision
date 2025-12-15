import React, { useEffect } from 'react';
import { X, CheckCircle, AlertTriangle, AlertOctagon, Info } from 'lucide-react';

export interface ToastMessage {
    id: number;
    type: 'success' | 'warning' | 'error' | 'info';
    title: string;
    message: string;
}

interface ToastContainerProps {
    toasts: ToastMessage[];
    removeToast: (id: number) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = React.memo(({ toasts, removeToast }) => {
    return (
        <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
            ))}
        </div>
    );
});

const ToastItem: React.FC<{ toast: ToastMessage, onClose: () => void }> = ({ toast, onClose }) => {
    
    // Use Ref to hold latest onClose callback without resetting timer on prop change
    const onCloseRef = React.useRef(onClose);
    
    React.useEffect(() => {
        onCloseRef.current = onClose;
    }, [onClose]);

    useEffect(() => {
        const timer = setTimeout(() => {
            onCloseRef.current();
        }, 3000);
        return () => clearTimeout(timer);
    }, []); // Empty dependency = Timer starts ONCE on mount using ref

    const styles = {
        success: 'bg-green-500/10 border-green-500/20 text-green-200',
        warning: 'bg-orange-500/10 border-orange-500/20 text-orange-200',
        error: 'bg-red-500/10 border-red-500/20 text-red-200',
        info:   'bg-blue-500/10 border-blue-500/20 text-blue-200',
    };
    
    const icon = {
        success: <CheckCircle className="text-green-400" size={18} />,
        warning: <AlertTriangle className="text-orange-400" size={18} />,
        error:   <AlertOctagon className="text-red-400" size={18} />,
        info:    <Info className="text-blue-400" size={18} />,
    };

    return (
        <div className={`pointer-events-auto min-w-[320px] max-w-sm rounded-xl p-4 border backdrop-blur-xl shadow-2xl flex items-start gap-3 animate-slide-in relative overflow-hidden ${styles[toast.type]}`}>
            {/* Glossy sheen */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
            
            <div className="mt-0.5 relative z-10">{icon[toast.type]}</div>
            <div className="flex-1 relative z-10">
                <h4 className="font-bold text-sm tracking-wide">{toast.title}</h4>
                <p className="text-xs opacity-80 mt-1 leading-relaxed">{toast.message}</p>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg transition-colors relative z-10">
                <X size={14} />
            </button>
        </div>
    );
};
