import React from 'react';
import { motion } from 'motion/react';

export const Hero: React.FC = () => {
    const title = "FANFICTION";
    const subtitle = "LEGEND";

    // Animation variants for letters
    const letterVariants = {
        initial: { y: 100, opacity: 0 },
        animate: { y: 0, opacity: 1 },
        hover: { 
            scale: 1.1,
            color: "#0033ff",
            textShadow: "4px 4px 0px #ff0033",
            transition: { type: "spring", stiffness: 400, damping: 10 }
        }
    };

    const containerVariants = {
        animate: {
            transition: {
                staggerChildren: 0.05
            }
        }
    };

    return (
        <div className="relative w-full h-screen overflow-hidden bg-brutal-black select-none">
            {/* Video Background */}
            <video
                data-testid="hero-video"
                autoPlay
                loop
                muted
                playsInline
                className="absolute inset-0 w-full h-full object-cover opacity-40 grayscale contrast-125"
            >
                <source src="/hero-bg.mp4" type="video/mp4" />
            </video>

            {/* Scanning Line Effect */}
            <div className="absolute inset-0 z-20 pointer-events-none bg-gradient-to-b from-transparent via-brutal-blue/5 to-transparent h-20 w-full animate-[scan_4s_linear_infinite]"></div>

            {/* Overlay Pattern (Dot Grid) */}
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>

            {/* Content */}
            <div className="relative z-30 flex flex-col items-center justify-center h-full px-4 text-center">
                <motion.div 
                    variants={containerVariants}
                    initial="initial"
                    animate="animate"
                    className="cursor-default"
                >
                    <h1 className="font-display font-black text-7xl md:text-[12rem] leading-[0.8] tracking-tighter text-brutal-white drop-shadow-[8px_8px_0_rgba(0,0,0,1)]">
                        <div className="flex overflow-hidden">
                            {title.split("").map((char, i) => (
                                <motion.span 
                                    key={i} 
                                    variants={letterVariants}
                                    whileHover="hover"
                                    className="inline-block"
                                >
                                    {char}
                                </motion.span>
                            ))}
                        </div>
                        <div className="flex justify-center overflow-hidden">
                            {subtitle.split("").map((char, i) => (
                                <motion.span 
                                    key={i} 
                                    variants={letterVariants}
                                    whileHover="hover"
                                    className="inline-block text-brutal-blue"
                                >
                                    {char}
                                </motion.span>
                            ))}
                        </div>
                    </h1>
                </motion.div>
                
                <motion.p 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1 }}
                    className="mt-8 font-mono text-lg md:text-xl text-brutal-white bg-brutal-blue/20 px-4 py-2 border-l-4 border-brutal-blue"
                >
                    &gt; [SYSTEM STATUS: READY_]
                </motion.p>

                <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.2 }}
                    className="mt-12 flex flex-col md:flex-row gap-6 w-full max-w-md md:max-w-none"
                >
                    <button className="group relative px-10 py-5 bg-brutal-blue text-white font-mono font-black text-xl shadow-brutal hover:shadow-none hover:translate-x-1 hover:translate-y-1 active:scale-95 transition-all w-full md:w-auto">
                        INITIALIZE_CONVERSION
                        <span className="absolute -top-2 -right-2 bg-brutal-red text-[10px] px-1 animate-pulse">NEW</span>
                    </button>
                    <button className="px-10 py-5 bg-transparent text-white border-4 border-brutal-white font-mono font-black text-xl hover:bg-brutal-white hover:text-brutal-black active:scale-95 transition-all w-full md:w-auto">
                        ARCHIVE_LOGS
                    </button>
                </motion.div>
            </div>
            
            {/* Visual Metadata Footer */}
            <div className="absolute bottom-10 left-10 right-10 flex justify-between items-end font-mono text-[10px] text-brutal-white/40 z-30 hidden md:flex">
                <div>
                    LATENCY: 14MS<br/>
                    BUFFER: 1024KB<br/>
                    ID: {Math.random().toString(36).substring(7).toUpperCase()}
                </div>
                <div className="text-right">
                    © 2026 FANFICTION LEGEND<br/>
                    BRUTALIST_ENGINE_V4.0
                </div>
            </div>

            {/* Decorative Vignette */}
            <div className="absolute inset-0 pointer-events-none shadow-[inset_0_0_150px_rgba(0,0,0,0.8)]"></div>
        </div>
    );
};