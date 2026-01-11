import React from 'react';

export interface Project {
    id: string;
    title: string;
    author?: string;
    status: 'active' | 'archived';
    last_updated?: string;
    path?: string;
}

interface DashboardProps {
    projects: Project[];
    onSelectProject?: (id: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ projects, onSelectProject }) => {
    if (projects.length === 0) {
        return (
            <div className="w-full min-h-[50vh] flex flex-col items-center justify-center border-t-2 border-brutal-gray bg-brutal-black p-10 text-center">
                <p className="font-mono text-xl text-brutal-gray mb-4">// DATABASE EMPTY_</p>
                <h2 className="font-display text-4xl text-brutal-white">NO ACTIVE PROJECTS</h2>
                <button className="mt-8 px-6 py-3 border-2 border-brutal-white text-brutal-white font-mono hover:bg-brutal-white hover:text-brutal-black transition-colors">
                    + INITIALIZE NEW
                </button>
            </div>
        );
    }

    return (
        <div className="w-full bg-brutal-black p-4 md:p-10 border-t-2 border-brutal-white">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-end mb-10 border-b-4 border-brutal-white pb-4">
                    <h2 className="font-display text-5xl md:text-7xl text-brutal-white">
                        PROJECTS <span className="text-brutal-blue text-2xl align-top">[{projects.length}]</span>
                    </h2>
                    <div className="hidden md:block font-mono text-right text-brutal-gray">
                        STATUS: ONLINE<br/>
                        SYS.READY
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {projects.map((project, index) => (
                        <div 
                            key={project.id}
                            className={`
                                group relative bg-brutal-gray p-6 border-2 border-transparent 
                                hover:border-brutal-white hover:bg-brutal-black transition-all duration-300
                                ${index % 3 === 0 ? 'lg:col-span-2' : ''} 
                            `}
                        >
                            {/* Hover shadow effect */}
                            <div className="absolute inset-0 border-2 border-transparent group-hover:translate-x-2 group-hover:translate-y-2 group-hover:border-brutal-blue pointer-events-none transition-all duration-300"></div>
                            
                            <div className="relative z-10">
                                <div className="flex justify-between items-start mb-4">
                                    <span className="font-mono text-xs bg-brutal-blue text-white px-2 py-1">
                                        ID: {project.id.substring(0, 6)}
                                    </span>
                                    <span className="font-mono text-xs text-brutal-white/50">
                                        {project.last_updated || 'UNKNOWN'}
                                    </span>
                                </div>
                                
                                <h3 className="font-display text-3xl text-brutal-white mb-2 leading-tight group-hover:text-brutal-blue transition-colors">
                                    {project.title}
                                </h3>
                                
                                <p className="font-mono text-brutal-white/70 text-sm mb-6">
                                    BY {project.author || 'UNKNOWN'}
                                </p>

                                <div className="flex justify-between items-center border-t border-brutal-white/20 pt-4 mt-auto">
                                    <span className={`font-mono text-xs uppercase ${project.status === 'active' ? 'text-green-500' : 'text-gray-500'}`}>
                                        ● {project.status}
                                    </span>
                                    <button 
                                        onClick={() => onSelectProject?.(project.id)}
                                        className="text-brutal-white font-mono text-sm hover:underline"
                                    >
                                        ACCESS &gt;&gt;
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
