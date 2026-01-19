import { useState, useEffect, useCallback } from 'react';
import { Hero } from './components/Hero';
import { Dashboard } from './components/Dashboard';
import { LogConsole } from './components/LogConsole';
import { ConfigOverlay } from './components/ConfigOverlay';
import type { Project } from './components/Dashboard';
import { fetchProjects, uploadProject, startProjectProcessing } from './api/client';
import { AnimatePresence, motion } from 'motion/react';

function App() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [processing, setProcessing] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
    const [configProjectId, setConfigProjectId] = useState<string | null>(null);

    const loadProjects = useCallback(async (isSilent = false) => {
        if (!isSilent) setLoading(true);
        try {
            const data = await fetchProjects();
            setProjects([...data.active, ...data.archived]);
        } catch (err) {
            console.error(err);
            if (!isSilent) setError('Failed to connect to backend system.');
        } finally {
            if (!isSilent) setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadProjects();
        const interval = setInterval(() => loadProjects(true), 10000);
        return () => clearInterval(interval);
    }, [loadProjects]);

    const handleUpload = async (file: File) => {
        setUploading(true);
        setError(null);
        try {
            await uploadProject(file);
            setSuccess(`UPLOAD_SUCCESS: ${file.name} initialized.`);
            await loadProjects();
        } catch (err: any) {
            setError(`UPLOAD_FAILURE: ${err.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleProcessClick = (id: string) => {
        setConfigProjectId(id);
    };

    const handleConfirmProcess = async (settings: any) => {
        const id = configProjectId;
        if (!id) return;
        
        setConfigProjectId(null);
        setProcessing(id);
        setError(null);
        try {
            await startProjectProcessing(id, settings);
            setSuccess(`SYSTEM_NOTICE: Project ${id} added to queue.`);
            await loadProjects(true);
            setSelectedProjectId(id);
        } catch (err: any) {
            setError(`PROCESS_FAILURE: ${err.message}`);
        } finally {
            setProcessing(null);
        }
    };

    return (
        <div className="min-h-screen bg-brutal-black">
            <Hero onUpload={handleUpload} />
            
            <AnimatePresence>
                {error && (
                    <motion.div 
                        initial={{ opacity: 0, x: 100 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 100 }}
                        className="fixed top-10 right-10 z-[150] bg-brutal-red text-white p-6 border-4 border-white shadow-brutal-lg max-w-md"
                    >
                        <div className="flex justify-between items-start mb-2">
                            <span className="font-mono font-black text-xl">SYSTEM_ALERT</span>
                            <button onClick={() => setError(null)} className="font-bold">[X]</button>
                        </div>
                        <p className="font-mono text-sm break-words">{error}</p>
                    </motion.div>
                )}

                {success && (
                    <motion.div 
                        initial={{ opacity: 0, x: 100 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 100 }}
                        className="fixed top-10 right-10 z-[150] bg-brutal-blue text-white p-6 border-4 border-white shadow-brutal-lg max-w-md"
                    >
                        <div className="flex justify-between items-start mb-2">
                            <span className="font-mono font-black text-xl">SYSTEM_CONFIRM</span>
                            <button onClick={() => setSuccess(null)} className="font-bold">[X]</button>
                        </div>
                        <p className="font-mono text-sm break-words">{success}</p>
                    </motion.div>
                )}

                {configProjectId && (
                    <ConfigOverlay 
                        projectId={configProjectId} 
                        onClose={() => setConfigProjectId(null)}
                        onConfirm={handleConfirmProcess}
                    />
                )}
            </AnimatePresence>

            {uploading && (
                <div className="fixed inset-0 z-[100] bg-brutal-black/80 flex items-center justify-center backdrop-blur-sm">
                    <div className="bg-brutal-blue text-white p-10 font-mono text-2xl border-4 border-white animate-pulse">
                        UPLOADING_CORE_DATA...
                    </div>
                </div>
            )}

            {processing && (
                <div className="fixed inset-0 z-[100] bg-brutal-black/80 flex items-center justify-center backdrop-blur-sm">
                    <div className="bg-brutal-blue text-white p-10 font-mono text-2xl border-4 border-white animate-pulse">
                        INITIALIZING_PROCESSOR...
                    </div>
                </div>
            )}

            {loading ? (
                <div className="p-20 text-center text-brutal-white font-mono text-xl">
                    <span className="animate-pulse">LOADING_DATA_STREAM...</span>
                </div>
            ) : (
                <Dashboard 
                    projects={projects} 
                    onSelectProject={(id) => setSelectedProjectId(id)} 
                    onProcessProject={handleProcessClick}
                />
            )}

            <AnimatePresence>
                {selectedProjectId && (
                    <LogConsole 
                        projectId={selectedProjectId} 
                        onClose={() => setSelectedProjectId(null)} 
                    />
                )}
            </AnimatePresence>
        </div>
    );
}

export default App;