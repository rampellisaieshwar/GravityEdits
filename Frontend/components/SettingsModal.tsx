
import React, { useState, useEffect } from "react";
import { X, Key, Shield, AlertTriangle, Save } from "lucide-react";
import { motion } from "framer-motion";

interface SettingsModalProps {
    onClose: () => void;
    isOpen: boolean;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose, isOpen }) => {
    const [apiKey, setApiKey] = useState("");
    const [provider, setProvider] = useState("gemini");
    const [userName, setUserName] = useState("");
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Load from Local Storage on mount
        const savedKey = localStorage.getItem("gravity_api_key");
        const savedProvider = localStorage.getItem("gravity_llm_provider");
        const savedName = localStorage.getItem("gravity_user_name");

        if (savedKey) setApiKey(savedKey);
        if (savedProvider) setProvider(savedProvider);
        if (savedName) setUserName(savedName);
    }, [isOpen]);

    const handleSave = () => {
        if (apiKey.trim()) {
            localStorage.setItem("gravity_api_key", apiKey.trim());
            localStorage.setItem("gravity_llm_provider", provider);
            localStorage.setItem("gravity_user_name", userName.trim() || "Editor"); // Default if empty

            // Dispatch event to update UI immediately
            window.dispatchEvent(new Event("profileUpdated"));

            alert("Settings Saved!");
            onClose();
        } else {
            localStorage.removeItem("gravity_api_key"); // Allow clearing
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="bg-[#111] border border-white/10 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl"
            >
                {/* Header */}
                <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-white/5">
                    <div className="flex items-center gap-2 text-white">
                        <Key size={18} className="text-yellow-500" />
                        <span className="font-bold tracking-wide">User Profile</span>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6">

                    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 flex gap-3 text-sm text-blue-200">
                        <Shield size={20} className="shrink-0 text-blue-400 mt-0.5" />
                        <div>
                            <p className="font-bold text-blue-100 mb-1">Privacy First</p>
                            <p className="leading-relaxed opacity-80">
                                Your keys and data are stored <strong>locally</strong>.
                                We do not track your credentials.
                            </p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block">Display Name</label>
                            <input
                                type="text"
                                value={userName}
                                onChange={(e) => setUserName(e.target.value)}
                                placeholder="e.g. Director Dave"
                                className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors text-sm"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block">AI Provider</label>
                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={() => setProvider("gemini")}
                                    className={`px-4 py-3 rounded-lg border text-sm font-bold transition-all ${provider === 'gemini' ? 'bg-blue-600 border-blue-400 text-white' : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'}`}
                                >
                                    Google Gemini
                                </button>
                                <button
                                    onClick={() => setProvider("openai")}
                                    className={`px-4 py-3 rounded-lg border text-sm font-bold transition-all ${provider === 'openai' ? 'bg-green-600 border-green-400 text-white' : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'}`}
                                >
                                    OpenAI GPT-4
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block">API Key</label>
                            <div className="relative">
                                <input
                                    type={isVisible ? "text" : "password"}
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                    placeholder={`Enter your ${provider === 'gemini' ? 'Gemini' : 'OpenAI'} API Key`}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors font-mono text-sm"
                                />
                                <button
                                    onClick={() => setIsVisible(!isVisible)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-white font-bold"
                                >
                                    {isVisible ? "HIDE" : "SHOW"}
                                </button>
                            </div>
                            <p className="text-[10px] text-gray-500 flex items-center gap-1">
                                <AlertTriangle size={10} />
                                {provider === 'gemini' ? "Requires a Google AI Studio Key." : "Requires an OpenAI Platform Key."}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 bg-white/5 flex justify-end">
                    <button
                        onClick={handleSave}
                        className="bg-white text-black px-6 py-2 rounded-lg font-bold hover:bg-gray-200 transition-colors flex items-center gap-2"
                    >
                        <Save size={16} /> Save Settings
                    </button>
                </div>

            </motion.div>
        </div>
    );
};

export default SettingsModal;
