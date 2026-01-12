import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Film, Settings, Palette } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { MOCK_XML_EDL, API_BASE_URL } from './constants';
import { parseEDLXml } from './utils/xmlParser';
import { VideoProject, Clip, AudioClip, TextOverlay } from './types';

// Components
import Sidebar from './components/Sidebar';
import ProgramMonitor from './components/ProgramMonitor';
import Timeline from './components/Timeline';
import Inspector from './components/Inspector';
import ColorInspector from './components/ColorInspector';
import UploadModal from './components/UploadModal';
import ExportOverlay from './components/ExportOverlay';
import LandingPage from './components/LandingPage';
import SettingsModal from './components/SettingsModal';

const SpaceBackground = () => (
  <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-[#050505] to-[#050505]" />
    {[...Array(30)].map((_, i) => (
      <motion.div
        key={i}
        className="absolute bg-white rounded-full opacity-10"
        initial={{
          x: Math.random() * window.innerWidth,
          y: Math.random() * window.innerHeight,
          scale: Math.random() * 0.5 + 0.5,
        }}
        animate={{
          y: [null, Math.random() * window.innerHeight],
          opacity: [0.1, 0.3, 0.1],
        }}
        transition={{
          duration: Math.random() * 20 + 30,
          repeat: Infinity,
          ease: "linear",
        }}
        style={{
          width: Math.random() * 2 + 'px',
          height: Math.random() * 2 + 'px',
        }}
      />
    ))}
  </div>
);

const App: React.FC = () => {
  const [appMode, setAppMode] = useState<'landing' | 'editor'>('landing');
  const [project, setProject] = useState<VideoProject | null>(null);
  const [currentProjectName, setCurrentProjectName] = useState<string | null>(null);
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null);
  const [selectedOverlayId, setSelectedOverlayId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [filterApplied, setFilterApplied] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<'media' | 'viral' | 'audio'>('media');
  const [view, setView] = useState<'edit' | 'color'>('edit');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [userInitials, setUserInitials] = useState("JS");

  const updateProfile = () => {
    if (typeof window === 'undefined') return;
    const name = localStorage.getItem("gravity_user_name") || "Editor";
    const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    setUserInitials(initials || "ED");
  }

  useEffect(() => {
    updateProfile();
    window.addEventListener('profileUpdated', updateProfile);
    return () => window.removeEventListener('profileUpdated', updateProfile);
  }, []);

  // Playback State
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playGreenOnly, setPlayGreenOnly] = useState(false);

  // Session Persistence
  useEffect(() => {
    const savedName = localStorage.getItem('gravity_recent_project');
    if (savedName) {
      setCurrentProjectName(savedName);
      // Attempt to load
      fetch(`${API_BASE_URL}/api/projects/${savedName}/edl`)
        .then(res => {
          if (res.ok) return res.text();
          throw new Error('No EDL');
        })
        .then(xml => {
          const proj = parseEDLXml(xml);
          if (proj) {
            // Fetch metadata to complete the project object if needed
            fetch(`${API_BASE_URL}/api/projects/${savedName}/analysis`)
              .then(r => r.json())
              .then(meta => {
                // Merge? For now just use EDL
                // We need to ensure project name is set from folder or XML
                proj.name = savedName;
                setProject(proj);
                setAppMode('editor');
              })
              .catch(() => {
                proj.name = savedName;
                setProject(proj);
                setAppMode('editor');
              });
          }
        })
        .catch(() => {
          // Failed to restore, stay on landing
          console.log("Session restore failed, staying on landing.");
        });
    }
  }, []);

  useEffect(() => {
    if (currentProjectName) {
      localStorage.setItem('gravity_recent_project', currentProjectName);
    } else {
      localStorage.removeItem('gravity_recent_project');
    }
  }, [currentProjectName]);

  // Listen for Settings Open Event (from Landing Page)
  useEffect(() => {
    const handleOpenSettings = () => setIsSettingsOpen(true);
    window.addEventListener('openAPISettings', handleOpenSettings);
    return () => window.removeEventListener('openAPISettings', handleOpenSettings);
  }, []);

  // -- LANDING PAGE HANDLERS --
  const handleProjectLoaded = (loadedProject: VideoProject, name?: string, shouldSwitchMode = true) => {
    setProject(loadedProject);
    if (name) setCurrentProjectName(name);
    // If loaded from XML, name is inside project usually, but we might want explicit folder name
    else setCurrentProjectName(loadedProject.name);

    if (shouldSwitchMode) setAppMode('editor');
  };

  const handleStartUpload = (projectName?: string) => {
    if (projectName) setCurrentProjectName(projectName);
    setIsUploading(true);
  };

  const handleBackToDashboard = () => {
    setAppMode('landing');
    setProject(null);
    setCurrentProjectName(null);
    setIsPlaying(false);
    setIsUploading(false);
  };

  const handleUploadComplete = () => {
    setIsUploading(false);
    if (project) {
      setAppMode('editor');
    }
  };

  const totalDuration = useMemo(() => {
    return project?.edl.reduce((acc, clip) => acc + (clip.duration || 0), 0) || 0;
  }, [project]);

  const keptDuration = useMemo(() => {
    return project?.edl.reduce((acc, clip) => acc + (clip.keep ? (clip.duration || 0) : 0), 0) || 0;
  }, [project]);

  useEffect(() => {
    let animationFrameId: number;
    let lastTimestamp: number | null = null;

    const animate = (timestamp: number) => {
      if (!lastTimestamp) lastTimestamp = timestamp;
      const deltaTime = (timestamp - lastTimestamp) / 1000; // In seconds
      lastTimestamp = timestamp;

      // Limit max step to avoid huge jumps if tab was backgrounded
      const safeDelta = Math.min(deltaTime, 0.1);

      setCurrentTime(prev => {
        let nextTime = prev + safeDelta;

        // Logic to skip non-kept (red) clips if playGreenOnly is enabled
        if (playGreenOnly && project) {
          let potentialTime = nextTime;
          let timeAccumulator = 0;

          for (const clip of project.edl) {
            const clipStart = timeAccumulator;
            const clipEnd = clipStart + (clip.duration || 0);

            if (potentialTime >= clipEnd) {
              timeAccumulator = clipEnd;
              continue;
            }

            // We are in this clip
            if (!clip.keep) {
              // Skip to end
              potentialTime = clipEnd + 0.001;
              timeAccumulator = clipEnd;
              continue;
            } else {
              break;
            }
          }
          nextTime = potentialTime;
        }

        if (nextTime >= totalDuration) {
          setIsPlaying(false);
          return 0;
        }
        return nextTime;
      });

      if (isPlaying) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    if (isPlaying) {
      animationFrameId = requestAnimationFrame(animate);
    } else {
      lastTimestamp = null;
    }

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, [isPlaying, totalDuration, playGreenOnly, project]);

  const togglePlay = () => setIsPlaying(!isPlaying);
  const handleSeek = (time: number) => {
    setCurrentTime(Math.max(0, Math.min(time, totalDuration)));
  };

  // Layout State for Resizability
  const [sidebarWidth, setSidebarWidth] = useState(320);
  const [inspectorWidth, setInspectorWidth] = useState(320);
  const [timelineHeight, setTimelineHeight] = useState(256);
  const [isResizing, setIsResizing] = useState<string | null>(null);

  // Note: Removed auto-load useEffect to support Landing Page flow


  const selectedClip = useMemo(() => {
    if (!project || !selectedClipId) return null;
    return project.edl.find(c => c.id === selectedClipId) || null;

  }, [project, selectedClipId]);

  const selectedOverlay = useMemo(() => {
    if (!project || !selectedOverlayId) return null;
    return project.overlays?.find(o => o.id === selectedOverlayId) || null;
  }, [project, selectedOverlayId]);

  const toggleClipStatus = (id: string) => {
    if (!project) return;
    const updatedEdl = project.edl.map(clip =>
      clip.id === id ? { ...clip, keep: !clip.keep } : clip
    );
    setProject({ ...project, edl: updatedEdl });
  };

  const reorderClips = (newClips: Clip[]) => {
    if (!project) return;
    setProject({ ...project, edl: newClips });
  };

  const handleSplitClip = (clipId: string, splitOffset: number) => {
    if (!project) return;

    const clipIndex = project.edl.findIndex(c => c.id === clipId);
    if (clipIndex === -1) return;

    const originalClip = project.edl[clipIndex];
    // Safety check: Don't split if too close to edges (e.g. < 0.1s)
    if (splitOffset < 0.1 || splitOffset > (originalClip.duration || 0) - 0.1) return;

    // Calculate source times
    const originalStart = originalClip.start || 0;
    const splitSourceTime = originalStart + splitOffset;

    // Create Clip 1 (Left) - Modifying original
    const clip1: Clip = {
      ...originalClip,
      end: splitSourceTime,
      duration: splitOffset,
      // Ensure ID is unique if we want, or keep it. keeping it is usually fine for react keys if we are careful, 
      // but let's make sure we don't have dupes if we split multiple times. 
      // Actually, let's generate a new ID for the second part only.
    };

    // Create Clip 2 (Right) - New segment
    const clip2: Clip = {
      ...originalClip,
      id: `${originalClip.id}_split_${Math.floor(Math.random() * 1000)}`,
      start: splitSourceTime, // continue from split
      duration: (originalClip.duration || 0) - splitOffset,
      // end inherits from original or we calculate it? 
      // If original had 'end', clip2 keeps it. If it didn't (implicit), we might need to be careful.
      // But usually 'end' is derived or explicit. Let's assume explicit 'end' or we assume duration handles it.
      // To be safe, let's ensure we carry over 'end' if it exists.
    };

    // Insert into EDL
    const newEdl = [...project.edl];
    // Replace original with these two
    newEdl.splice(clipIndex, 1, clip1, clip2);

    setProject({ ...project, edl: newEdl });
  };

  const [originalProject, setOriginalProject] = useState<VideoProject | null>(null);
  const [initialExportTarget, setInitialExportTarget] = useState<number>(-1);

  const handleUpdateProject = (updatedProject: VideoProject) => {
    // Auto-expand timeline if bgMusic is added
    if (updatedProject.bgMusic && !project?.bgMusic) {
      setTimelineHeight(prev => Math.min(600, prev + 48));
    }
    setProject(updatedProject);

    // Also update title if changed
    if (updatedProject.name !== project?.name) {
      setCurrentProjectName(updatedProject.name);
    }
  };

  const handleExportShort = (shortIndex: number) => {
    setInitialExportTarget(shortIndex);
    setIsExporting(true);
  };

  const handleLoadShort = (shortIndex: number) => {
    if (!project) return;

    // Save original if not saved yet
    const baseProject = originalProject || project;
    if (!originalProject) setOriginalProject(project);

    const short = baseProject.viralShorts[shortIndex];
    if (!short) return;

    // Build short timeline
    const shortClips = short.clipIds.map(id => {
      // Look in base project because current project might already be a short
      const found = baseProject.edl.find(c => c.id === id);
      return found ? { ...found, keep: true } : null;
    }).filter((c): c is Clip => !!c); // Type guard

    if (shortClips.length === 0) {
      alert("Could not find clips for this short.");
      return;
    }

    setProject({
      ...baseProject,
      name: `${baseProject.name} [${short.title}]`,
      edl: shortClips,
      overlays: [], // Clear main video overlays for the short
      audioClips: [], // Optionally clear secondary audio if not relevant
      bgMusic: undefined // Optionally clear Bg music or keep it? varied choice, usually shorts need new music. Let's clear for clean slate.
    });

    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleExitShortMode = () => {
    if (originalProject) {
      setProject(originalProject);
      setOriginalProject(null);
      setCurrentProjectName(originalProject.name);
      setIsPlaying(false);
      setCurrentTime(0);
    }
  };

  // Resize Handlers
  const startResizing = (direction: string) => (e: React.MouseEvent) => {
    setIsResizing(direction);
    e.preventDefault();
  };

  const stopResizing = useCallback(() => {
    setIsResizing(null);
  }, []);

  const resize = useCallback((e: MouseEvent) => {
    if (isResizing === 'sidebar') {
      const newWidth = e.clientX;
      if (newWidth > 180 && newWidth < 500) setSidebarWidth(newWidth);
    } else if (isResizing === 'inspector') {
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth > 240 && newWidth < 600) setInspectorWidth(newWidth);
    } else if (isResizing === 'timeline') {
      const newHeight = window.innerHeight - e.clientY;
      if (newHeight > 120 && newHeight < 600) setTimelineHeight(newHeight);
    }
  }, [isResizing]);

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize);
      window.addEventListener('mouseup', stopResizing);
      document.body.style.cursor = isResizing.includes('sidebar') || isResizing.includes('inspector') ? 'col-resize' : 'row-resize';
      document.body.style.userSelect = 'none';
    } else {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    }
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  const handleAddAudioClip = (source: string, time: number, track: number) => {
    if (!project) return;
    const newClip: AudioClip = {
      id: `audio-${Date.now()}`,
      source,
      start: time,
      duration: 60.0, // Default duration extended per user request (was 15s)
      track
    };
    const updatedAudioClips = [...(project.audioClips || []), newClip];

    // Auto-expand if adding to a high track number that might be hidden?
    // Not strictly needed if we assume standard height, but good for polish.
    // If track > 2, ensure we have space. 
    // Actually, the main request is handled in handleAddTrack.

    setProject({ ...project, audioClips: updatedAudioClips });
  };

  const handleUpdateBgMusic = (updates: { start?: number, duration?: number }) => {
    setProject(prev => {
      if (!prev || !prev.bgMusic) return prev;
      return {
        ...prev,
        bgMusic: { ...prev.bgMusic, ...updates }
      };
    });
  };

  const handleUpdateAudioClip = (id: string, updates: Partial<any>) => {
    setProject(prev => {
      if (!prev || !prev.audioClips) return prev;
      return {
        ...prev,
        audioClips: prev.audioClips.map(c => c.id === id ? { ...c, ...updates } : c)
      };
    });
  };

  const handleSplitAudioClip = (id: string, offset: number) => {
    // Offset is relative to clip start
    if (!project || !project.audioClips) return;

    const clip = project.audioClips.find(c => c.id === id);
    if (!clip) return;

    const splitPoint = offset;

    if (splitPoint <= 0 || splitPoint >= clip.duration) return;

    // Create two new clips
    const firstPart = {
      ...clip,
      id: `audio-${Date.now()}-1`,
      duration: splitPoint
    };

    const secondPart = {
      ...clip,
      id: `audio-${Date.now()}-2`,
      start: clip.start + splitPoint,
      duration: clip.duration - splitPoint
    };

    setProject(prev => ({
      ...prev!,
      audioClips: (prev!.audioClips || [])
        .filter(c => c.id !== id)
        .concat([firstPart, secondPart])
    }));
  };

  const handleSplitBgMusic = (offset: number) => {
    if (!project || !project.bgMusic) return;

    // Convert current BG Music into Audio Clips
    const music = project.bgMusic;
    const currentStart = music.start || 0;
    const currentDuration = music.duration || 60; // Approximate if not set

    // Calculate split
    const splitRelTime = offset - currentStart; // Music might start later

    // If click is NOT on the music bar (should have been checked by UI, but double check)
    // Actually, offset passed is absolute Timeline Time from UI
    // So splitRelTime is correct offset into the clip.
    // Wait, let's verify Timeline logic. 
    // Timeline passes `offsetTime` derived from `offsetX` relative to PAGE/SCROLL?
    // No, `offsetX = e.clientX - rect.left`. This is relative to the element (BgMusic div).
    // The BgMusic div IS rendered at `start` time.
    // So `offsetX / zoom` IS the relative time into the clip.
    // So `splitRelTime` should actually just be `offset` if "offset" meant "relative offset".

    // Let's re-read Timeline.tsx click handler:
    // const rect = e.currentTarget.getBoundingClientRect();
    // const offsetX = e.clientX - rect.left;
    // const offsetTime = offsetX / zoom;
    // props.onSplitBgMusic(offsetTime);

    // YES, offsetTime IS relative to the clip start.

    const splitPoint = offset; // Clarifying naming

    if (splitPoint <= 0 || splitPoint >= currentDuration) return;

    // Create Clips
    // Part 1: Start -> splitPoint
    const part1 = {
      id: `music-migrated-1-${Date.now()}`,
      source: music.source,
      start: currentStart,
      duration: splitPoint,
      track: 99 // Dedicated Music Track ID
    };

    // Part 2: splitPoint -> End
    // Start of part 2 is currentStart + splitPoint
    const part2 = {
      id: `music-migrated-2-${Date.now()}`,
      source: music.source,
      start: currentStart + splitPoint,
      duration: currentDuration - splitPoint,
      track: 99
    };

    // Update Project
    setProject(prev => {
      if (!prev) return null;
      // Check if track 99 exists, if not add it
      const currentTracks = new Set(prev.audioTracks || [2]);
      currentTracks.add(99);

      return {
        ...prev,
        bgMusic: undefined, // Remove legacy field
        audioClips: [...(prev.audioClips || []), part1, part2],
        audioTracks: Array.from(currentTracks).sort((a, b) => a - b)
      };
    });
  };

  const handleTrackVolumeChange = (track: string, volume: number) => {
    if (!project) return;
    const newVolumes = {
      ...(project.trackVolumes || { a1: 1, a2: 1, music: 1 }),
      [track]: volume
    };
    setProject({ ...project, trackVolumes: newVolumes });
  };

  const handleAddTrack = () => {
    if (!project) return;
    const currentTracks = project.audioTracks || [2];
    const maxTrack = Math.max(1, ...currentTracks); // 1 is base, usually starts at 2
    const newTrackId = maxTrack + 1;

    // Auto-adjust timeline height
    setTimelineHeight(prev => Math.min(600, prev + 48));

    setProject({
      ...project,
      audioTracks: [...currentTracks, newTrackId]
    });
  };

  const handleRemoveTrack = (trackId: number) => {
    if (!project) return;
    const currentTracks = project.audioTracks || [2];
    // Remove track from list
    const newTracks = currentTracks.filter(t => t !== trackId);
    // Optional: Remove clips associated with this track? For now, we keep them but they won't render.
    // Better to remove them or they will become orphaned.
    // Let's remove them to keep state clean.
    const newAudioClips = (project.audioClips || []).filter(c => c.track !== trackId);

    // Auto-adjust timeline height (optional, but requested behavior implies responsiveness)
    setTimelineHeight(prev => Math.max(250, prev - 48));

    setProject({
      ...project,
      audioTracks: newTracks,
      audioClips: newAudioClips
    });
  };

  const handleUpdateOverlay = (overlayId: string, updates: Partial<TextOverlay>) => {
    if (!project) return;
    const newOverlays = (project.overlays || []).map(o =>
      o.id === overlayId ? { ...o, ...updates } : o
    );
    setProject({ ...project, overlays: newOverlays });
  };

  const handleAddOverlay = (start: number) => {
    if (!project) return;
    const newOverlay: TextOverlay = {
      id: `text-${Date.now()}`,
      content: "DOUBLE CLICK ME",
      start: start,
      duration: 3.0,
      style: 'pop',
      origin: 'manual'
    };
    setProject({ ...project, overlays: [...(project.overlays || []), newOverlay] });
  };

  if (appMode === 'landing') {
    return (
      <>
        <LandingPage onProjectLoaded={handleProjectLoaded} onStartUpload={handleStartUpload} />
        {/* Allow UploadModal to overlay LandingPage if triggered */}
        <AnimatePresence>
          {isUploading && (
            <UploadModal
              onComplete={handleUploadComplete}
              setProject={(p) => handleProjectLoaded(p, currentProjectName || undefined, false)}
              projectName={currentProjectName}
            />
          )}
          {isSettingsOpen && <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />}
        </AnimatePresence>
      </>
    );
  }

  return (
    <div className="relative flex flex-col h-screen bg-[#050505] text-[#E0E0E0] overflow-hidden select-none font-sans">
      <SpaceBackground />
      {/* Dynamic Main Header */}
      <header className="h-12 border-b border-white/5 flex items-center justify-between px-4 bg-black/40 backdrop-blur-md z-20 shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-blue-500 font-bold tracking-tight">
            <Film size={20} className="fill-blue-500/20" />
            <span className="text-sm tracking-widest uppercase">GRAVITY EDIT PRO</span>
          </div>
          <div className="h-4 w-[1px] bg-[#2A2A2A]" />
          <nav className="flex items-center gap-1 text-[11px] font-semibold">
            <button onClick={() => setView('edit')} className={`px-3 py-1 rounded transition-all ${view === 'edit' ? 'text-white bg-[#333]' : 'text-gray-500 hover:text-gray-200'}`}>Edit</button>
            <button onClick={() => setView('color')} className={`px-3 py-1 rounded flex items-center gap-1.5 transition-all ${view === 'color' ? 'text-blue-400 bg-[#333]' : 'text-gray-500 hover:text-gray-200'}`}><Palette size={12} />Color</button>
          </nav>
        </div>

        {/* Center: Back Button when in Short Mode */}
        {originalProject && (
          <div className="absolute left-1/2 -translate-x-1/2">
            <button
              onClick={handleExitShortMode}
              className="bg-yellow-500/10 border border-yellow-500/50 text-yellow-500 px-4 py-1 rounded-full text-xs font-bold uppercase hover:bg-yellow-500/20 transition-all flex items-center gap-2 animate-pulse"
            >
              <span>Editing Viral Short</span>
              <span className="bg-yellow-500 text-black px-1.5 rounded-sm">EXIT</span>
            </button>
          </div>
        )}

        <div className="flex items-center gap-3">
          {/* Status Indicator */}
          <div
            className={`hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full border text-[10px] font-bold uppercase tracking-wider transition-all ${(typeof window !== 'undefined' && localStorage.getItem("gravity_api_key"))
              ? "bg-green-500/10 border-green-500/30 text-green-500"
              : "bg-red-500/10 border-red-500/30 text-red-500 animate-pulse"
              }`}
          >
            <div className={`w-1.5 h-1.5 rounded-full ${(typeof window !== 'undefined' && localStorage.getItem("gravity_api_key")) ? "bg-green-500" : "bg-red-500"}`} />
            {(typeof window !== 'undefined' && localStorage.getItem("gravity_api_key")) ? "System Active" : "No API Key"}
          </div>

          <button
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center gap-2 bg-[#2A2A2A] hover:bg-[#333] px-3 py-1 rounded text-[10px] font-bold uppercase transition-colors"
          >
            <Settings size={12} /> Project Configuration
          </button>
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-[10px] font-black border border-blue-400/50 shadow-inner">{userInitials}</div>
        </div>
      </header>

      {/* Main Resizable Body */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex-1 flex min-h-0">
          {/* Sidebar */}
          <div style={{ width: sidebarWidth }} className="shrink-0 flex flex-col overflow-hidden z-10 relative">
            <Sidebar
              project={project}
              tab={sidebarTab}
              setTab={setSidebarTab}
              onSelectClip={setSelectedClipId}
              onUpdateProject={handleUpdateProject}
              selectedId={selectedClipId}
              onOpenUpload={() => setIsUploading(true)}
              onBack={handleBackToDashboard}
              onLoadShort={handleLoadShort}
              onExportShort={handleExportShort}
              onAddAudioClip={handleAddAudioClip}
            />
          </div>

          {/* Divider */}
          <div onMouseDown={startResizing('sidebar')} className={`w-[4px] cursor-col-resize transition-all z-10 hover:bg-blue-500/40 ${isResizing === 'sidebar' ? 'bg-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.4)]' : 'bg-transparent'}`} />

          {/* Monitor */}
          <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden bg-black/20 backdrop-blur-sm relative">
            <ProgramMonitor
              project={project}
              selectedClip={selectedClip}
              filterApplied={filterApplied}
              setFilterApplied={setFilterApplied}
              currentTime={currentTime}
              duration={totalDuration}
              effectiveDuration={keptDuration}
              isPlaying={isPlaying}
              onTogglePlay={togglePlay}
              originalProjectName={originalProject?.name}
              onSeek={handleSeek}
              playGreenOnly={playGreenOnly}
              setPlayGreenOnly={setPlayGreenOnly}
              isShortMode={!!originalProject}
            />
          </div>

          {/* Divider */}
          <div onMouseDown={startResizing('inspector')} className={`w-[4px] cursor-col-resize transition-all z-10 hover:bg-blue-500/40 ${isResizing === 'inspector' ? 'bg-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.4)]' : 'bg-transparent'}`} />

          {/* Inspector */}
          <div style={{ width: inspectorWidth }} className="shrink-0 flex flex-col overflow-hidden">
            <AnimatePresence mode="wait">
              {view === 'edit' ? (
                <motion.div key="inspector" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <Inspector
                    clip={selectedClip}
                    overlay={selectedOverlay}
                    onUpdateOverlay={(updates) => selectedOverlayId && handleUpdateOverlay(selectedOverlayId, updates)}
                    onToggleStatus={() => selectedClip && toggleClipStatus(selectedClip.id)}
                    onExport={() => setIsExporting(true)}
                    associatedShort={project?.viralShorts.find(s => selectedClip && s.clipIds.includes(selectedClip.id))}
                  />
                </motion.div>
              ) : (
                <motion.div key="color" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <ColorInspector clip={selectedClip} filterApplied={filterApplied} setFilterApplied={setFilterApplied} project={project} onUpdateProject={handleUpdateProject} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Horizontal Divider */}
        <div onMouseDown={startResizing('timeline')} className={`h-[4px] cursor-row-resize transition-all z-10 hover:bg-blue-500/40 ${isResizing === 'timeline' ? 'bg-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.4)]' : 'bg-transparent'}`} />

        {/* Timeline */}
        <div style={{ height: timelineHeight }} className="shrink-0 flex flex-col overflow-hidden bg-black/60 backdrop-blur-md border-t border-white/5">
          <Timeline
            project={project}
            selectedClipId={selectedClipId}
            selectedOverlayId={selectedOverlayId}
            onSelectClip={(id) => { setSelectedClipId(id); setSelectedOverlayId(null); }}
            onSelectOverlay={(id) => { setSelectedOverlayId(id); setSelectedClipId(null); }}
            onToggleStatus={toggleClipStatus}
            onReorder={reorderClips}
            currentTime={currentTime}
            onSeek={handleSeek}
            onScrubStart={() => setIsPlaying(false)}
            onSplitClip={handleSplitClip}
            onOpenAudioTab={() => setSidebarTab('audio')}
            onAddAudioClip={handleAddAudioClip}
            onVolumeChange={handleTrackVolumeChange}
            onAddTrack={handleAddTrack}
            onRemoveTrack={handleRemoveTrack}
            onUpdateOverlay={handleUpdateOverlay}
            onAddOverlay={handleAddOverlay}
            onUpdateBgMusic={handleUpdateBgMusic}
            onUpdateAudioClip={handleUpdateAudioClip}
            onSplitAudioClip={handleSplitAudioClip}
            onSplitBgMusic={handleSplitBgMusic}
          />

        </div>
      </div>

      {/* Global Modals */}
      <AnimatePresence>
        {isUploading && (
          <UploadModal
            onComplete={handleUploadComplete}
            setProject={(p) => handleProjectLoaded(p, currentProjectName || undefined, false)}
            projectName={currentProjectName}
          />
        )}
        {isExporting && <ExportOverlay onClose={() => setIsExporting(false)} project={project} initialExportTarget={initialExportTarget} />}
        {isSettingsOpen && <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />}
      </AnimatePresence>
    </div>
  );
};

export default App;
