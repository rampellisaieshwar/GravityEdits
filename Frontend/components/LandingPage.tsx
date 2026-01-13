import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Upload, FileJson, Video, Music, Folder, Clock, Film, Trash2 } from 'lucide-react';
import { VideoProject } from '../types';
import { parseEDLXml } from '../utils/xmlParser';
import { API_BASE_URL } from '../constants';

interface LandingPageProps {
    onProjectLoaded: (project: VideoProject, name: string) => void;
    onStartUpload: (projectName: string) => void;
}

interface ProjectMeta {
    name: string;
    created_at?: string;
    thumbnail?: string;
    clip_count: number;
}

const LandingPage: React.FC<LandingPageProps> = ({ onProjectLoaded, onStartUpload }) => {
    const [showNewProjectModal, setShowNewProjectModal] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [projects, setProjects] = useState<ProjectMeta[]>([]);
    const [newProjectName, setNewProjectName] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [userInitials, setUserInitials] = useState("?");

    const updateProfile = () => {
        if (typeof window === 'undefined') return;
        const name = localStorage.getItem("gravity_user_name");
        if (name) {
            const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
            setUserInitials(initials);
        } else {
            setUserInitials("?");
        }
    }

    useEffect(() => {
        updateProfile();
        window.addEventListener('profileUpdated', updateProfile);
        return () => window.removeEventListener('profileUpdated', updateProfile);
    }, []);

    useEffect(() => {
        // Auto-play ambient sound
        const audio = audioRef.current;
        if (audio) {
            audio.volume = 0.5;
            const playPromise = audio.play();
            if (playPromise !== undefined) {
                playPromise.then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
            }
        }

        // Fetch Projects
        fetchProjects();

        return () => {
            if (audio) {
                audio.pause();
                audio.currentTime = 0;
            }
        };
    }, []);

    const fetchProjects = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/projects`);
            if (res.ok) {
                const data = await res.json();
                setProjects(data);
            }
        } catch (e) {
            console.error("Failed to load projects", e);
        }
    };

    const toggleSound = () => {
        if (!audioRef.current) return;
        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
        } else {
            audioRef.current.play();
            setIsPlaying(true);
        }
    };

    const handleCreateProject = async () => {
        if (!newProjectName.trim()) return;
        setIsLoading(true);

        try {
            const res = await fetch(`${API_BASE_URL}/api/projects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newProjectName })
            });

            if (res.ok) {
                onStartUpload(newProjectName);
            } else {
                const errData = await res.json().catch(() => ({}));
                alert(`Failed to create project: ${errData.detail || "Name might exist or server error"}`);
            }
        } catch (e) {
            console.error(e);
            alert("Error creating project");
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteProject = async (e: React.MouseEvent, p: ProjectMeta) => {
        e.stopPropagation(); // Prevent opening the project
        if (!confirm(`Are you sure you want to permanently delete '${p.name}'?`)) return;

        try {
            const res = await fetch(`${API_BASE_URL}/api/projects/${p.name}`, {
                method: 'DELETE',
            });
            if (res.ok) {
                setProjects(projects.filter(proj => proj.name !== p.name));
            } else {
                alert("Failed to delete project");
            }
        } catch (error) {
            console.error(error);
            alert("Error deleting project");
        }
    };

    const openProject = async (p: ProjectMeta) => {
        // Try to load EDL
        try {
            const res = await fetch(`${API_BASE_URL}/api/projects/${p.name}/edl`);
            if (res.ok) {
                const xmlText = await res.text();

                // Try analysis meta
                let meta = null;
                try {
                    const mRes = await fetch(`${API_BASE_URL}/api/projects/${p.name}/analysis`);
                    if (mRes.ok) meta = await mRes.json();
                } catch { }

                const project = parseEDLXml(xmlText, meta);
                // Inject name if missing
                project.name = p.name;
                onProjectLoaded(project, p.name);
            } else {
                // Project exists but no analysis/EDL yet?
                // Mabe just open editor in empty state or trigger uploads?
                // For now, let's assume if it exists in list but no EDL, it's an unfinished project.
                // We'll prompt to upload.
                if (confirm(`Project '${p.name}' has no timeline yet. Upload media?`)) {
                    onStartUpload(p.name);
                }
            }
        } catch (e) {
            alert("Failed to open project: " + e);
        }
    };

    return (
        <div className="relative h-screen w-full bg-[#050505] overflow-hidden flex flex-col items-center justify-center text-white selection:bg-blue-500/30">
            {/* Background Animation (Stars/Space) */}
            <div className="absolute inset-0 z-0">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-[#050505] to-[#050505]" />
                {[...Array(50)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute bg-white rounded-full opacity-20"
                        initial={{
                            x: Math.random() * window.innerWidth,
                            y: Math.random() * window.innerHeight,
                            scale: Math.random() * 0.5 + 0.5,
                        }}
                        animate={{
                            y: [null, Math.random() * window.innerHeight],
                            opacity: [0.2, 0.5, 0.2],
                        }}
                        transition={{
                            duration: Math.random() * 10 + 20,
                            repeat: Infinity,
                            ease: "linear",
                        }}
                        style={{
                            width: Math.random() * 3 + 1 + 'px',
                            height: Math.random() * 3 + 1 + 'px',
                        }}
                    />
                ))}
            </div>

            {/* Ambient Sound */}
            <audio ref={audioRef} loop src="/Interstellar.mp3" />

            <div className="z-10 flex flex-col items-center gap-12 w-full max-w-6xl px-8">
                {/* Branding */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1 }}
                    className="text-center space-y-4"
                >
                    <div className="flex items-center justify-center gap-3 mb-2">
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                            className="w-12 h-12 rounded-full border-2 border-blue-500/50 border-t-white"
                        />
                    </div>
                    <h1 className="text-6xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-white to-gray-600">
                        GRAVITY EDIT
                    </h1>
                    <p className="text-blue-400 tracking-[0.5em] text-sm font-bold uppercase">Pro AI Workspace</p>
                </motion.div>

                <div className="w-full flex flex-wrap justify-center gap-6 max-w-7xl">
                    {/* Create New Card */}
                    <motion.div
                        layout
                        whileHover={{ scale: 1.05 }}
                        className="w-72 h-48 bg-[#111] border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-blue-500/50 hover:bg-[#151515] transition-all group shadow-2xl shadow-black/50"
                        onClick={() => setShowNewProjectModal(true)}
                    >
                        <div className="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/40 group-hover:scale-110 transition-transform">
                            <Plus size={32} />
                        </div>
                        <span className="font-bold tracking-widest uppercase text-sm">Create New Project</span>
                    </motion.div>

                    {/* Project List */}
                    <AnimatePresence>
                        {projects.map((p) => (
                            <motion.div
                                layout
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                                key={p.name}
                                whileHover={{ y: -5 }}
                                className="w-72 h-48 bg-[#1A1A1A] border border-white/5 rounded-2xl p-6 cursor-pointer hover:border-white/20 group relative overflow-hidden shadow-xl"
                                onClick={() => openProject(p)}
                            >
                                <div className="absolute top-0 right-0 p-2 opacity-50 z-0">
                                    <Folder size={80} className="text-[#222] -rotate-12 translate-x-4 -translate-y-4" />
                                </div>
                                <div className="relative z-10 flex flex-col h-full justify-between">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="font-bold text-lg truncate pr-4 text-white max-w-[150px]" title={p.name}>{p.name}</h3>
                                            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                                                <span className="flex items-center gap-1"><Film size={12} /> {p.clip_count} clips</span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={(e) => handleDeleteProject(e, p)}
                                            className="text-gray-600 hover:text-red-500 transition-colors p-1 rounded-full hover:bg-white/10"
                                            title="Delete Project"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>

                                    <div className="flex items-end justify-between border-t border-white/5 pt-4">
                                        <span className="flex items-center gap-1 text-[10px] text-gray-600 font-mono">
                                            <Clock size={10} /> {p.created_at ? new Date(p.created_at).toLocaleDateString() : 'N/A'}
                                        </span>
                                        <span className="text-xs text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity uppercase font-bold tracking-wider">Open &rarr;</span>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>

                {/* Sound Toggle */}
                <button
                    onClick={toggleSound}
                    className="fixed bottom-8 right-8 text-gray-600 hover:text-white transition-colors flex items-center gap-2 text-xs font-mono uppercase"
                >
                    <Music size={14} className={isPlaying ? "animate-pulse text-blue-500" : ""} />
                    {isPlaying ? "Sound On" : "Sound Off"}
                </button>

                {/* Profile / Settings Button */}
                <button
                    onClick={() => window.dispatchEvent(new Event('openAPISettings'))}
                    className="fixed top-8 right-8 flex items-center gap-3 bg-[#111] hover:bg-[#1A1A1A] border border-white/10 hover:border-white/30 pl-1 pr-4 py-1.5 rounded-full transition-all group z-50 cursor-pointer"
                >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-black border border-white/10 ${typeof window !== 'undefined' && localStorage.getItem('gravity_api_key') ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-900/50' : 'bg-gray-800 text-gray-400'}`}>
                        {userInitials}
                    </div>
                    <div className="text-left">
                        <span className="block text-[10px] uppercase font-bold text-gray-400 group-hover:text-blue-400 transition-colors tracking-wider">
                            {typeof window !== 'undefined' && localStorage.getItem('gravity_api_key') ? 'Profile Active' : 'Setup Profile'}
                        </span>
                        <span className="block text-[9px] text-gray-600">
                            {typeof window !== 'undefined' && localStorage.getItem('gravity_llm_provider') === 'openai' ? 'OpenAI GPT-4' : 'Google Gemini'}
                        </span>
                    </div>
                </button>
            </div>

            {/* New Project Modal */}
            <AnimatePresence>
                {showNewProjectModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4" onClick={() => setShowNewProjectModal(false)}>
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-[#151515] border border-[#333] p-8 rounded-2xl max-w-md w-full shadow-2xl space-y-6"
                        >
                            <h2 className="text-2xl font-bold text-center text-white">Name Your Project</h2>

                            <div className="space-y-2">
                                <input
                                    autoFocus
                                    type="text"
                                    className="w-full bg-[#0A0A0A] border border-[#333] p-4 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500 text-center text-xl font-bold"
                                    placeholder="My Awesome Video"
                                    value={newProjectName}
                                    onChange={e => setNewProjectName(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleCreateProject()}
                                />
                            </div>

                            <div className="flex gap-4">
                                <button
                                    onClick={() => setShowNewProjectModal(false)}
                                    className="flex-1 py-3 text-gray-500 hover:text-white font-bold transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleCreateProject}
                                    disabled={isLoading}
                                    className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-900/40 flex items-center justify-center gap-2"
                                >
                                    {isLoading ? <Clock size={18} className="animate-spin" /> : <Plus size={18} />}
                                    Create Project
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default LandingPage;
