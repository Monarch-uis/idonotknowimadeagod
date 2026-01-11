import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface LogConsoleProps {
    projectId: string;
    onClose?: () => void;
}

export const LogConsole: React.FC<LogConsoleProps> = ({ projectId, onClose }) => {
    const [logs, setLogs] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/projects/${projectId}/logs`);
                if (response.ok) {
                    const data = await response.json();
                    setLogs(data.logs);
                }
            } catch (err) {
                console.error("Failed to fetch logs:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchLogs();
        const interval = setInterval(fetchLogs, 5000); // Poll every 5 seconds
        return () => clearInterval(interval);
    }, [projectId]);

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-0 right-0 w-full md:w-[600px] h-[400px] bg-brutal-black border-l-4 border-t-4 border-brutal-white z-50 flex flex-col shadow-brutal-lg"
        >
            <div className="flex justify-between items-center bg-brutal-white px-4 py-2">
                <span className="font-mono text-xs font-black text-brutal-black uppercase tracking-widest">
                    SYSTEM_LOGS // {projectId}
                </span>
                <button 
                    onClick={onClose}
                    className="text-brutal-black hover:bg-brutal-red hover:text-white px-2 transition-colors font-bold"
                >
                    [X]
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-1 scrollbar-thin scrollbar-thumb-brutal-gray">
                {loading ? (
                    <div className="text-brutal-blue animate-pulse">ESTABLISHING CONNECTION...</div>
                ) : logs.length === 0 ? (
                    <div className="text-brutal-gray italic">&gt; NO SYSTEM LOGS FOUND IN CURRENT BUFFER.</div>
                ) : (
                    logs.map((log, i) => (
                        <div key={i} className="flex gap-2">
                            <span className="text-brutal-blue">[{i.toString().padStart(3, '0')}]</span>
                            <span className={log.toLowerCase().includes('error') ? 'text-brutal-red' : 'text-brutal-white'}>
                                {log}
                            </span>
                        </div>
                    ))
                )}
            </div>

            <div className="bg-brutal-gray/20 px-4 py-1 font-mono text-[10px] text-brutal-white/40 border-t border-brutal-white/10">
                REAL-TIME_LOGGING_ACTIVE // ADDR: 0x{Math.random().toString(16).substring(2, 10).toUpperCase()}
            </div>
        </motion.div>
    );
};
