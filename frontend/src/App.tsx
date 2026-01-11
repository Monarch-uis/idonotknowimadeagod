import { useState, useEffect } from 'react';
import { Hero } from './components/Hero';
import { Dashboard } from './components/Dashboard';
import { LogConsole } from './components/LogConsole';
import type { Project } from './components/Dashboard';
import { fetchProjects } from './api/client';
import { AnimatePresence } from 'motion/react';

function App() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

    useEffect(() => {
        const loadProjects = async () => {
            try {
                const data = await fetchProjects();
                // Combine active and archived for now, or just show active
                setProjects([...data.active, ...data.archived]);
            } catch (err) {
                console.error(err);
                setError('Failed to load projects.');
            } finally {
                setLoading(false);
            }
        };

        loadProjects();
    }, []);

    return (
        <div className="min-h-screen bg-brutal-black">
            <Hero />
            
            {loading ? (
                <div className="p-10 text-center text-brutal-white font-mono">
                    LOADING SYSTEM...
                </div>
            ) : error ? (
                <div className="p-10 text-center text-brutal-red font-mono border-2 border-brutal-red m-10">
                    ERROR: {error}
                </div>
            ) : (
                <Dashboard 
                    projects={projects} 
                    onSelectProject={(id) => setSelectedProjectId(id)} 
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