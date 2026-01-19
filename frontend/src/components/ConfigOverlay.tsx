import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { fetchSystemOptions, SystemOptions } from '../api/client';

interface ConfigOverlayProps {
    projectId: string;
    onClose: () => void;
    onConfirm: (settings: any) => void;
}

export const ConfigOverlay: React.FC<ConfigOverlayProps> = ({ projectId, onClose, onConfirm }) => {
    const [options, setOptions] = useState<SystemOptions | null>(null);
    const [loading, setLoading] = useState(true);
    
    // Selection state
    const [engine, setEngine] = useState('edge-tts');
    const [voice, setVoice] = useState('');
    const [speed, setSpeed] = useState('+0%');
    const [quality, setQuality] = useState('Balanced');

    useEffect(() => {
        const loadOptions = async () => {
            try {
                const data = await fetchSystemOptions();
                setOptions(data);
                if (data.voices['edge-tts']) {
                    setVoice(data.voices['edge-tts'][0]);
                }
            } catch (err) {
                console.error("Failed to load options", err);
            } finally {
                setLoading(false);
            }
        };
        loadOptions();
    }, []);

    const handleEngineChange = (newEngine: string) => {
        setEngine(newEngine);
        if (options && options.voices[newEngine]) {
            setVoice(options.voices[newEngine][0]);
        }
    };

    if (loading) return null;

    return (
        <div className="fixed inset-0 z-[120] flex items-center justify-center p-4">
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="absolute inset-0 bg-brutal-black/90 backdrop-blur-md"
            />
            
            <motion.div 
                initial={{ scale: 0.9, y: 20, opacity: 0 }}
                animate={{ scale: 1, y: 0, opacity: 1 }}
                exit={{ scale: 0.9, y: 20, opacity: 0 }}
                className="relative w-full max-w-2xl bg-brutal-black border-4 border-brutal-white p-8 shadow-brutal-lg"
            >
                <div className="flex justify-between items-start mb-8 border-b-2 border-brutal-white pb-4">
                    <div>
                        <h2 className="font-display text-4xl text-brutal-white uppercase">PROCESS_CONFIG</h2>
                        <p className="font-mono text-xs text-brutal-blue">TARGET_ID: {projectId}</p>
                    </div>
                    <button onClick={onClose} className="text-brutal-white hover:text-brutal-red font-black text-2xl">[X]</button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Engine Selection */}
                    <div className="space-y-4">
                        <label className="block font-mono text-xs text-brutal-white/60 uppercase">01 // TTS_ENGINE</label>
                        <div className="flex flex-col gap-2">
                            {options?.engines.map(e => (
                                <button 
                                    key={e}
                                    onClick={() => handleEngineChange(e)}
                                    className={`px-4 py-2 font-mono text-left text-sm border-2 transition-all ${engine === e ? 'bg-brutal-blue border-white text-white' : 'border-brutal-gray text-brutal-gray hover:border-brutal-white'}`}
                                >
                                    {e.toUpperCase()}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Voice Selection */}
                    <div className="space-y-4">
                        <label className="block font-mono text-xs text-brutal-white/60 uppercase">02 // VOICE_PROFILE</label>
                        <select 
                            value={voice}
                            onChange={(e) => setVoice(e.target.value)}
                            className="w-full bg-brutal-gray border-2 border-brutal-white p-2 font-mono text-sm text-white outline-none focus:bg-brutal-blue"
                        >
                            {options?.voices[engine]?.map(v => (
                                <option key={v} value={v}>{v}</option>
                            ))}
                        </select>
                    </div>

                    {/* Speed Selection */}
                    <div className="space-y-4">
                        <label className="block font-mono text-xs text-brutal-white/60 uppercase">03 // SYNTH_SPEED</label>
                        <div className="grid grid-cols-3 gap-2">
                            {options?.speeds.map(s => (
                                <button 
                                    key={s}
                                    onClick={() => setSpeed(s)}
                                    className={`p-2 font-mono text-xs border-2 transition-all ${speed === s ? 'bg-brutal-blue border-white text-white' : 'border-brutal-gray text-brutal-gray hover:border-brutal-white'}`}
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Quality Selection */}
                    <div className="space-y-4">
                        <label className="block font-mono text-xs text-brutal-white/60 uppercase">04 // RENDER_QUALITY</label>
                        <div className="flex flex-col gap-2">
                            {options?.quality_presets.map(q => (
                                <button 
                                    key={q}
                                    onClick={() => setQuality(q)}
                                    className={`px-4 py-2 font-mono text-left text-sm border-2 transition-all ${quality === q ? 'bg-brutal-blue border-white text-white' : 'border-brutal-gray text-brutal-gray hover:border-brutal-white'}`}
                                >
                                    {q.toUpperCase()}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="mt-10 pt-6 border-t-2 border-brutal-white flex justify-end gap-4">
                    <button 
                        onClick={onClose}
                        className="px-6 py-3 font-mono text-sm text-brutal-white hover:text-brutal-red"
                    >
                        ABORT_MISSION
                    </button>
                    <button 
                        onClick={() => onConfirm({ engine, voice, speed, quality })}
                        className="px-10 py-3 bg-brutal-blue text-white font-mono font-black text-lg border-2 border-transparent hover:border-white shadow-brutal active:translate-x-1 active:translate-y-1 active:shadow-none transition-all"
                    >
                        CONFIRM_&_INITIALIZE &gt;&gt;
                    </button>
                </div>
            </motion.div>
        </div>
    );
};
