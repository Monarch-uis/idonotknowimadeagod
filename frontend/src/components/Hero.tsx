import React from 'react';

export const Hero: React.FC = () => {
    return (
        <div className="relative w-full h-screen overflow-hidden bg-brutal-black">
            {/* Video Background */}
            <video
                data-testid="hero-video"
                autoPlay
                loop
                muted
                className="absolute inset-0 w-full h-full object-cover opacity-50 grayscale"
            >
                {/* Placeholder for now, can be replaced with a real asset later */}
                <source src="/hero-bg.mp4" type="video/mp4" />
            </video>

            {/* Overlay Pattern (Dot Grid) */}
            <div className="absolute inset-0 bg-[url('/dot-grid.png')] opacity-20"></div>

            {/* Content */}
            <div className="relative z-10 flex flex-col items-center justify-center h-full px-4 text-center">
                <h1 className="font-display font-black text-6xl md:text-9xl tracking-tighter text-brutal-white drop-shadow-[4px_4px_0_rgba(0,0,0,1)] selection:bg-brutal-blue selection:text-white">
                    FANFICTION
                    <span className="block text-brutal-blue">LEGEND</span>
                </h1>
                
                <p className="mt-6 font-mono text-lg md:text-xl text-brutal-white/80 max-w-2xl bg-black/80 p-2 border border-white/20">
                    // AUTOMATED EPUB TO AUDIOBOOK PIPELINE_
                </p>

                <div className="mt-10 flex gap-4">
                    <button className="px-8 py-4 bg-brutal-blue text-white font-mono font-bold text-lg border-2 border-transparent hover:border-white shadow-brutal hover:shadow-brutal-lg hover:-translate-y-1 transition-all duration-200">
                        START PROJECT
                    </button>
                    <button className="px-8 py-4 bg-brutal-gray text-white font-mono font-bold text-lg border-2 border-transparent hover:border-white shadow-brutal hover:shadow-brutal-lg hover:-translate-y-1 transition-all duration-200">
                        VIEW DOCS
                    </button>
                </div>
            </div>
            
            {/* Decorative bottom border */}
            <div className="absolute bottom-0 left-0 w-full h-4 bg-brutal-blue"></div>
        </div>
    );
};
