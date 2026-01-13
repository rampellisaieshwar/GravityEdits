import React, { useState, useEffect } from 'react';
import { Sparkles, Send, Loader2 } from 'lucide-react';
import { VideoProject, ChatMessage } from '../types';
import { API_BASE_URL } from '../constants';

interface AIChatPanelProps {
    project: VideoProject | null;
    onProjectUpdate?: (newProject: VideoProject) => void;
    onUndo?: () => void;
    chatHistory?: ChatMessage[];
    setChatHistory?: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
}

const AIChatPanel: React.FC<AIChatPanelProps> = ({ project, onProjectUpdate, onUndo, chatHistory: externalHistory, setChatHistory: setExternalHistory }) => {
    const [aiCommand, setAiCommand] = useState('');
    const [isAiProcessing, setIsAiProcessing] = useState(false);

    // Internal state fallback if not provided by parent
    const [localHistory, setLocalHistory] = useState<ChatMessage[]>([]);

    const chatHistory = externalHistory || localHistory;
    const setChatHistory = setExternalHistory || setLocalHistory;

    const handleAiCommand = async () => {
        if (!aiCommand.trim()) return;

        // Optimistic Update
        const userMsg = { role: 'user' as const, content: aiCommand };
        setChatHistory(prev => [...prev, userMsg]);
        setAiCommand('');
        setIsAiProcessing(true);

        try {
            const apiKey = localStorage.getItem("gravity_api_key");
            const response = await fetch(`${API_BASE_URL}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: userMsg.content,
                    project_name: project?.name || null,
                    api_key: apiKey,
                    current_state: project
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();
            const aiResponse = data.response || "I couldn't generate a response.";

            // --- TOOL EXECUTION LOGIC ---
            if (aiResponse.includes("```tool_code")) {
                const codeBlock = aiResponse.split("```tool_code")[1].split("```")[0].trim();
                let successMessage = "";
                let failureMessage = "";

                const newProject = { ...project };

                // 1. EDIT TRANSCRIPT
                // gravity_ai.edit_transcript(clip_id="1", new_transcript="foo")
                const editMatch = codeBlock.match(/edit_transcript\(clip_id=['"]?(\w+)['"]?,\s*new_transcript=['"](.*)['"]\)/);
                if (editMatch) {
                    const id = editMatch[1];
                    const text = editMatch[2];
                    const clip = newProject.edl.find(c => c.id.toString() === id.toString());
                    if (clip) {
                        clip.text = text;
                        successMessage = `✅ Updated transcript for Clip ${id}.`;
                    } else failureMessage = `❌ Clip ${id} not found.`;
                }

                // 2. CUT CLIP (Reject)
                // gravity_ai.cut_clip(clip_id="1")
                const cutMatch = codeBlock.match(/cut_clip\(clip_id=['"]?(\w+)['"]?\)/);
                if (cutMatch) {
                    const id = cutMatch[1];
                    const clip = newProject.edl.find(c => c.id.toString() === id.toString());
                    if (clip) {
                        clip.keep = false;
                        successMessage = `✂️ Cut Clip ${id} (Rejected).`;
                    } else failureMessage = `❌ Clip ${id} not found.`;
                }

                // 3. KEEP CLIP (Restore)
                // gravity_ai.keep_clip(clip_id="1")
                const keepMatch = codeBlock.match(/keep_clip\(clip_id=['"]?(\w+)['"]?\)/);
                if (keepMatch) {
                    const id = keepMatch[1];
                    const clip = newProject.edl.find(c => c.id.toString() === id.toString());
                    if (clip) {
                        clip.keep = true;
                        successMessage = `✅ Restored Clip ${id} (Kept).`;
                    } else failureMessage = `❌ Clip ${id} not found.`;
                }

                // 4. ADD TEXT OVERLAY
                if (codeBlock.includes('add_text(')) {
                    const contentMatch = codeBlock.match(/content\s*=\s*['"](.*?)['"]/);
                    const startMatch = codeBlock.match(/start_time\s*=\s*([\d.]+)/);
                    const durationMatch = codeBlock.match(/duration\s*=\s*([\d.]+)/);
                    const styleMatch = codeBlock.match(/style\s*=\s*['"]?(\w+)['"]?/);

                    if (contentMatch) {
                        const content = contentMatch[1];
                        const start = startMatch ? parseFloat(startMatch[1]) : 0;
                        const duration = durationMatch ? parseFloat(durationMatch[1]) : 3.0;
                        const style = (styleMatch ? styleMatch[1] : 'pop') as 'pop' | 'typewriter' | 'slide_up';

                        const newOverlay = {
                            id: `ai-text-${Date.now()}`,
                            content,
                            start,
                            duration,
                            style,
                            origin: 'ai-chat' as const
                        };

                        if (!newProject.overlays) newProject.overlays = [];
                        newProject.overlays.push(newOverlay);
                        successMessage = `✨ Added text "${content}" at ${start}s.`;
                    }
                }

                // 5. SPLIT CLIP (Precision Cut)
                // gravity_ai.split_clip(clip_id="1", time=15.5)
                const splitMatch = codeBlock.match(/split_clip\(clip_id=['"]?(\w+)['"]?,\s*time=([\d.]+)\)/);
                if (splitMatch) {
                    const id = splitMatch[1];
                    const absoluteTime = parseFloat(splitMatch[2]);

                    const clipIndex = newProject.edl.findIndex(c => c.id.toString() === id.toString());
                    if (clipIndex !== -1) {
                        const originalClip = newProject.edl[clipIndex];
                        const offset = absoluteTime - (originalClip.start || 0);

                        // Validate Split (Relaxed for AI surgery)
                        if (offset > 0.01 && offset < (originalClip.duration || 0) - 0.01) {
                            // --- REPLICATE SPLIT LOGIC FROM APP.TSX ---
                            const splitSourceTime = (originalClip.start || 0) + offset;

                            const clip1 = {
                                ...originalClip,
                                end: splitSourceTime,
                                duration: offset
                            };

                            const clip2 = {
                                ...originalClip,
                                id: `${originalClip.id}_split_${Math.floor(Math.random() * 1000)}`,
                                start: splitSourceTime,
                                duration: (originalClip.duration || 0) - offset
                            };

                            newProject.edl.splice(clipIndex, 1, clip1, clip2);
                            successMessage = `🔪 Split Clip ${id} at ${absoluteTime}s.`;
                        } else {
                            failureMessage = `⚠️ Split point ${absoluteTime}s is invalid (too close to edge).`;
                        }
                    } else failureMessage = `❌ Clip ${id} not found.`;
                }

                // 6. REMOVE SEGMENT (Manual Surgery)
                const segMatch = codeBlock.match(/remove_segment\(clip_id=['"]?(\w+)['"]?,\s*start=([\d.]+),\s*end=([\d.]+)\)/);
                if (segMatch) {
                    const id = segMatch[1];
                    const cutStart = parseFloat(segMatch[2]);
                    const cutEnd = parseFloat(segMatch[3]);
                    handleRemoveSegment(id, cutStart, cutEnd);
                }

                // 7. REMOVE WORD (Auto Surgery)
                // gravity_ai.remove_word(clip_id="1", word="banana")
                const wordMatch = codeBlock.match(/remove_word\(clip_id=['"]?(\w+)['"]?,\s*word=['"](.*?)['"]\)/);
                if (wordMatch) {
                    const id = wordMatch[1];
                    const targetWord = wordMatch[2].toLowerCase().trim();

                    const clip = newProject.edl.find(c => c.id.toString() === id.toString());

                    // Helper to clean punctuation
                    const clean = (s: string) => s.toLowerCase().replace(/[.,!?]/g, '');

                    if (clip && clip.words) {
                        // Find the word occurrence
                        const foundWord = clip.words.find(w =>
                            clean(w.word) === clean(targetWord) ||
                            clean(w.word).includes(clean(targetWord))
                        );

                        if (foundWord) {
                            handleRemoveSegment(id, foundWord.start, foundWord.end);
                            successMessage = `✂️ Found "${foundWord.word}" at ${foundWord.start}s and removed it.`;
                        } else {
                            // Backup: Try finding in main text if words missing
                            failureMessage = `❌ Cloud not find word "${targetWord}" in clip ${id} data.`;
                        }
                    } else {
                        failureMessage = clip ? `❌ No detailed word data available for Clip ${id}.` : `❌ Clip ${id} not found.`;
                    }
                }

                // Helper for the surgery logic
                function handleRemoveSegment(id: string, cutStart: number, cutEnd: number) {
                    const clipIndex = newProject.edl.findIndex(c => c.id.toString() === id.toString());
                    if (clipIndex !== -1) {
                        const originalClip = newProject.edl[clipIndex];
                        const clipStart = originalClip.start || 0;
                        const clipEnd = clipStart + (originalClip.duration || 0);

                        // Validate Range (Relaxed)
                        if (cutStart >= clipStart && cutEnd <= clipEnd && cutEnd > cutStart) {
                            const replacements: any[] = [];
                            // 1. Pre
                            if (cutStart > clipStart + 0.02) {
                                replacements.push({
                                    ...originalClip,
                                    id: `${originalClip.id}_pre_${Date.now()}`,
                                    end: cutStart,
                                    duration: cutStart - clipStart
                                });
                            }
                            // 2. Cut
                            replacements.push({
                                ...originalClip,
                                id: `${originalClip.id}_cut_${Date.now()}`,
                                start: cutStart,
                                end: cutEnd,
                                duration: cutEnd - cutStart,
                                keep: false,
                                reason: "AI Removed Segment"
                            });
                            // 3. Post
                            if (cutEnd < clipEnd - 0.02) {
                                replacements.push({
                                    ...originalClip,
                                    id: `${originalClip.id}_post_${Date.now()}`,
                                    start: cutEnd,
                                    end: clipEnd,
                                    duration: clipEnd - cutEnd
                                });
                            }

                            newProject.edl.splice(clipIndex, 1, ...replacements);
                            if (!successMessage) successMessage = `✂️ Surgically removed segment ${cutStart}s - ${cutEnd}s.`;
                        } else {
                            failureMessage = `⚠️ Cut range ${cutStart}-${cutEnd} is outside clip bounds (${clipStart}-${clipEnd}).`;
                        }
                    } else failureMessage = `❌ Clip ${id} not found.`;
                }

                // 8. UNDO (Time Travel)
                if (codeBlock.includes('undo_action()')) {
                    if (onUndo) {
                        onUndo();
                        successMessage = "↺ Undoing last action...";
                    } else {
                        failureMessage = "❌ Undo is not available.";
                    }
                }

                if (successMessage && onProjectUpdate) {
                    // Update state ONLY if not undoing (undo handles its own state)
                    if (!codeBlock.includes('undo_action()')) {
                        onProjectUpdate(newProject);
                    }
                    setChatHistory(prev => [...prev, { role: 'assistant', content: successMessage! }]);
                } else if (failureMessage) {
                    setChatHistory(prev => [...prev, { role: 'assistant', content: failureMessage }]);
                } else {
                    // No recognized command matched
                    setChatHistory(prev => [...prev, { role: 'assistant', content: aiResponse }]);
                }
            } else {
                setChatHistory(prev => [...prev, { role: 'assistant', content: aiResponse }]);
            }

        } catch (error) {
            console.error("AI Assistant failed:", error);
            setChatHistory(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error connecting to the AI brain." }]);
        } finally {
            setIsAiProcessing(false);
        }
    };

    return (
        <div className="w-full h-full bg-black/40 backdrop-blur-md border-l border-white/5 flex flex-col">
            <div className="p-4 border-b border-white/5 bg-white/5 sticky top-0 z-10 shrink-0">
                <div className="flex items-center gap-2 mb-1">
                    <Sparkles className="text-blue-500" size={16} />
                    <h2 className="text-[10px] font-bold tracking-widest uppercase text-white">AI Chat</h2>
                </div>
                <div className="text-[9px] text-gray-500 font-mono truncate">{project?.name || "No Project"}</div>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin min-h-[100px]">
                {/* Welcome Message */}
                <div className="flex flex-col items-start gap-1">
                    <div className="flex items-center gap-2">
                        <Sparkles size={10} className="text-blue-400" />
                        <span className="text-[10px] font-bold text-gray-400">Gravity AI</span>
                    </div>
                    <div className="bg-[#2A2A2A] rounded-lg rounded-tl-none p-2 text-[10px] text-gray-300 max-w-[90%]">
                        {project ? "I've analyzed your footage. Ask me anything or tell me how to edit!" : "Ready to assist. Import a project to get started."}
                    </div>
                </div>

                {/* Dynamic History */}
                {chatHistory.map((msg, i) => (
                    <div key={i} className={`flex flex-col gap-1 w-full ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                        <div className={`relative group rounded-lg p-2 text-[10px] max-w-[90%] break-words whitespace-pre-wrap ${msg.role === 'user' ? 'bg-blue-600/20 text-blue-100 rounded-tr-none' : 'bg-[#2A2A2A] text-gray-300 rounded-tl-none'}`}>
                            {msg.content}
                            <button
                                onClick={() => navigator.clipboard.writeText(msg.content)}
                                className="absolute -top-3 right-0 opacity-0 group-hover:opacity-100 bg-black/60 text-white text-[9px] px-1 rounded transition-opacity"
                            >
                                Copy
                            </button>
                        </div>
                    </div>
                ))}

                {isAiProcessing && (
                    <div className="flex flex-col items-start gap-1">
                        <div className="bg-[#2A2A2A] rounded-lg rounded-tl-none p-2 text-[10px] text-gray-300 flex items-center gap-2">
                            <Loader2 size={10} className="animate-spin text-gray-500" /> Thinking...
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-3 border-t border-[#2A2A2A] bg-[#1a1a1a]">
                <div className="relative">
                    <textarea
                        value={aiCommand}
                        onChange={(e) => setAiCommand(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleAiCommand();
                            }
                        }}
                        disabled={isAiProcessing}
                        placeholder={project ? "e.g. 'Show me the drone shots'..." : "Waiting for project..."}
                        className="w-full bg-[#121212] border border-[#2A2A2A] rounded-lg p-2 text-[10px] min-h-[40px] max-h-[100px] resize-none focus:outline-none focus:border-blue-500 pr-8 text-gray-300 placeholder:text-gray-600 disabled:opacity-50"
                    />
                    <button
                        onClick={handleAiCommand}
                        disabled={isAiProcessing || !aiCommand.trim()}
                        className="absolute bottom-2 right-2 p-1.5 text-blue-500 hover:bg-blue-500/10 rounded-md disabled:opacity-30 disabled:text-gray-700 transition-all"
                    >
                        {isAiProcessing ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AIChatPanel;
