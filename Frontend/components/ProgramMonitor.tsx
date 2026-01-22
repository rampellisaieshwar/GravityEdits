
import React from 'react';
import { Play, Pause, SkipBack, SkipForward, Maximize2, Volume2, Wand2, Layers } from 'lucide-react';
import { VideoProject, Clip, TextOverlay } from '../types';
import { API_BASE_URL } from '../constants';
import { useRef, useEffect, useState, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface ProgramMonitorProps {
  project: VideoProject | null;
  selectedClip: Clip | null;
  filterApplied: boolean;
  setFilterApplied: (val: boolean) => void;
  currentTime: number;
  duration: number;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onSeek: (time: number) => void;
  playGreenOnly?: boolean;
  setPlayGreenOnly?: (val: boolean) => void;
  effectiveDuration?: number;
  originalProjectName?: string;
  isShortMode?: boolean;
}

const getFilterStyle = (filterName: string): React.CSSProperties => {
  if (!filterName) return {};

  switch (filterName) {
    case 'Cinematic':
      return { filter: 'contrast(1.2) brightness(0.95) saturate(0.9)' };
    case 'Teal & Orange':
      // Approximate CSS for Teal/Orange using hue-rotate and contrast
      return { filter: 'contrast(1.2) saturate(1.4) hue-rotate(-10deg) sepia(0.2)' };
    case 'Vintage':
      return { filter: 'sepia(0.5) contrast(0.9) brightness(1.1) saturate(0.7)' };
    case 'Noir':
      return { filter: 'grayscale(1) contrast(1.5) brightness(0.9)' };
    case 'Vivid':
      return { filter: 'saturate(1.5) contrast(1.1)' };
    case 'Vivid Warm':
      return { filter: 'saturate(1.3) sepia(0.2) contrast(1.1)' };
    case 'Vivid Cool':
      return { filter: 'saturate(1.2) hue-rotate(-20deg) contrast(1.1)' };
    case 'Dramatic':
      return { filter: 'contrast(1.4) brightness(0.9) saturate(0.8)' };
    case 'Mono':
      return { filter: 'grayscale(1)' };
    case 'Silvertone':
      return { filter: 'grayscale(1) contrast(1.2) brightness(1.2)' };
    default:
      return {};
  }
};

const ProgramMonitor: React.FC<ProgramMonitorProps> = ({
  project,
  selectedClip,
  filterApplied,
  setFilterApplied,
  currentTime,
  duration,
  isPlaying,
  onTogglePlay,
  onSeek,
  playGreenOnly = false,
  setPlayGreenOnly,
  effectiveDuration,
  originalProjectName,
  isShortMode = false
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [volume, setVolume] = useState(1);

  const activeClip = React.useMemo(() => {
    if (!project) return null;

    let timeAccumulator = 0;
    let found = null;

    for (const clip of project.edl) {
      const clipDuration = clip.duration || 5; // Fallback
      if (currentTime >= timeAccumulator && currentTime < timeAccumulator + clipDuration) {
        found = { clip, startTime: timeAccumulator };
        break;
      }
      timeAccumulator += clipDuration;
    }
    return found;
  }, [currentTime, project]);

  useEffect(() => {
    if (videoRef.current) {
      // Apply Master Volume to Video Ref immediately when it changes
      // (Actual mix volume is applied in the sync effect below)
      // This is just a fallback or generic sync
    }
  }, [volume]);

  // 1. Volume Sync Effect - Runs only when volume changes
  useEffect(() => {
    if (videoRef.current) {
      const a1Vol = project?.trackVolumes?.a1 ?? 1;
      const safeVolume = Number.isFinite(volume * a1Vol) ? Math.min(Math.max(volume * a1Vol, 0), 1) : 1;
      videoRef.current.volume = safeVolume;
      videoRef.current.muted = false;
    }
  }, [volume, project?.trackVolumes, activeClip]);

  // 2. Play/Pause Sync Effect - Runs only when isPlaying changes
  useEffect(() => {
    if (videoRef.current) {
      if (isPlaying) {
        const playPromise = videoRef.current.play();
        if (playPromise !== undefined) {
          playPromise.catch(error => {
            console.log("Auto-play was prevented:", error);
          });
        }
      } else {
        videoRef.current.pause();
      }
    }
  }, [isPlaying, activeClip]);

  // 3. Time Sync Effect - Runs frequently (on currentTime)
  useEffect(() => {
    if (videoRef.current && activeClip) {
      // Calculate relative time into the clip on the timeline
      const relativeTime = currentTime - activeClip.startTime;
      const clipStart = activeClip.clip.start || 0;
      const localTime = clipStart + relativeTime;

      // Only update if difference is significant to avoid stutter (seeking kills audio)
      // When playing, we allow more drift (0.8s) because the video clock and react clock drift slightly.
      // When paused, we want precise sync (0.1s).
      const threshold = isPlaying ? 0.8 : 0.1;
      const diff = Math.abs(videoRef.current.currentTime - localTime);

      if (diff > threshold) {
        videoRef.current.currentTime = localTime;
      }
    }
  }, [activeClip, currentTime, isPlaying]); // Removed volume/trackVolumes dependencies from this loop

  const formatTime = (time: number) => {
    return new Date(time * 1000).toISOString().substr(11, 8);
  };

  const handleScrub = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    onSeek(percentage * duration);
  };

  const combinedStyle = React.useMemo(() => {
    // 1. Base Named Filter (Global)
    const baseStyle = getFilterStyle(project?.globalSettings.filterSuggestion || 'None');
    let filterString = String(baseStyle.filter || '');

    // 2. Manual Grading (Clip > Global > Defaults)
    const clipGrading = activeClip?.clip.colorGrading;
    const globalGrading = project?.globalSettings.colorGrading;

    // Use Clip specific if available, else Global, else defaults
    const exposure = clipGrading?.exposure ?? globalGrading?.exposure ?? 0;
    const contrast = clipGrading?.contrast ?? globalGrading?.contrast ?? 0;
    const saturation = clipGrading?.saturation ?? globalGrading?.saturation ?? 100;
    const temperature = clipGrading?.temperature ?? globalGrading?.temperature ?? 5600;

    // Calculate CSS values
    const bVal = Math.max(0, 1 + (exposure / 2));
    const cVal = Math.max(0, 1 + (contrast / 100));
    const sVal = Math.max(0, saturation / 100);

    // Append manual adjustments
    filterString += ` brightness(${bVal}) contrast(${cVal}) saturate(${sVal})`;

    // Simple Temperature Hack
    if (temperature > 5600) {
      const sepiaVal = Math.min(0.3, (temperature - 5600) / 10000);
      filterString += ` sepia(${sepiaVal})`;
    }

    return { filter: filterString.trim() };
  }, [project, activeClip]);

  // Helper to construct media URLs correctly based on project context
  const getMediaUrl = (source: string) => {
    if (source.startsWith('http') || source.startsWith('/')) return source;
    // If we are in a project context, files are likely in the project folder
    const pName = originalProjectName || (project?.name ? project.name.split(' [')[0] : null);
    if (pName) {
      return `${API_BASE_URL}/projects/${encodeURIComponent(pName)}/source_media/${encodeURIComponent(source)}`;
    }
    // Fallback to generic uploads
    return `${API_BASE_URL}/uploads/${encodeURIComponent(source)}`;
  };

  const bgMusicRef = useRef<HTMLAudioElement>(null);

  // Sync Audio Elements
  useEffect(() => {
    // BG Music Sync
    if (bgMusicRef.current && project?.bgMusic) {
      const el = bgMusicRef.current;

      // Calculate effective volume
      const musicVol = project?.trackVolumes?.music ?? (project.bgMusic.volume ?? 1);
      el.volume = musicVol * volume;

      if (isPlaying) {
        if (el.paused) el.play().catch(() => { });
      } else {
        if (!el.paused) el.pause();
      }

      // Time Sync
      if (el.duration) {
        const targetTime = currentTime % el.duration;
        if (Math.abs(el.currentTime - targetTime) > 0.3) {
          el.currentTime = targetTime;
        }
      }
    }
  }, [
    isPlaying,
    currentTime,
    volume,
    project?.bgMusic,
    project?.trackVolumes
  ]);

  const activeOverlays = useMemo(() => {
    if (!project?.overlays) return [];
    const active = project.overlays.filter(o =>
      currentTime >= o.start && currentTime < (o.start + o.duration)
    );
    // Debug: Log overlay values
    if (active.length > 0) {
      active.forEach(o => console.log(`📝 Overlay "${o.content}": posX=${o.positionX}, posY=${o.positionY}, fontSize=${o.fontSize}, CSS: left=${(o.positionX || 0.5) * 100}%, top=${(o.positionY || 0.8) * 100}%`));
    }
    return active;
  }, [project?.overlays, currentTime]);

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full bg-[#0A0A0A]">
      {/* ... header ... */}

      {/* Hidden Audio for BG Music */}
      {project?.bgMusic && (
        <audio
          ref={bgMusicRef}
          src={getMediaUrl(project.bgMusic.source)}
          loop
        />
      )}
      <div className="flex items-center justify-between p-2 border-b border-[#2A2A2A] bg-[#1E1E1E]">
        <div className="text-xs font-semibold text-gray-400 truncate min-w-0 flex-1">
          Program Monitor: <span className="text-white">{project?.name || 'Untitled'}</span>
        </div>
        {project?.globalSettings.filterSuggestion && (
          <button
            onClick={() => setFilterApplied(!filterApplied)}
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-bold transition-all ${filterApplied
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
              : 'bg-[#2A2A2A] text-blue-400 hover:bg-[#333]'
              }`}
          >
            <Wand2 size={12} />
            {filterApplied ? `Applied: ${project.globalSettings.filterSuggestion}` : `Apply ${project.globalSettings.filterSuggestion}`}
          </button>
        )}
      </div>

      <div className="flex-1 relative flex flex-col items-center justify-center overflow-hidden bg-black min-h-0">
        {/* CRITICAL: aspect-ratio: 16/9 locks preview to video proportions */}
        <div className="w-full h-full relative overflow-hidden flex items-center justify-center bg-black" style={{ containerType: 'size', aspectRatio: '16/9', maxHeight: '100%', maxWidth: '100%' }}>
          {activeClip ? (
            <video
              key={activeClip.clip.source}
              ref={videoRef}
              src={getMediaUrl(activeClip.clip.source)}
              className={isShortMode ? "h-full aspect-[9/16] object-cover bg-black ring-1 ring-white/10" : "w-full h-full object-contain"}
              style={combinedStyle}
              playsInline
              preload="auto"
              onLoadedMetadata={(e) => {
                const el = e.currentTarget;
                el.muted = false; // Force unmute on load
                // Ensure we seek to the correct start time immediately upon loading
                if (activeClip) {
                  const relativeTime = currentTime - activeClip.startTime;
                  const clipStart = activeClip.clip.start || 0;
                  el.currentTime = clipStart + relativeTime;
                }
              }}
            />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <div className="text-gray-700 font-mono text-3xl">{formatTime(currentTime)}:00</div>
              <div className="text-gray-500 text-xs font-medium uppercase tracking-[0.2em]">
                {isPlaying ? 'Ending...' : 'No media at playhead'}
              </div>
            </div>
          )}

          {/* Simulated filter overlays for complex tones */}
          {filterApplied && (project?.globalSettings.filterSuggestion === 'Cinematic' || project?.globalSettings.filterSuggestion === 'Dramatic') && (
            <div className="absolute inset-0 pointer-events-none mix-blend-overlay opacity-30 bg-gradient-to-tr from-cyan-900 via-transparent to-orange-900" />
          )}

          {/* Timecode Overlay */}
          {/* Debug Overlay */}
          <div className="absolute top-12 left-4 text-[9px] bg-red-900/80 text-white p-1 rounded pointer-events-none z-50">
            Clip: {activeClip ? activeClip.clip.source : "None"} <br />
            Src Start: {activeClip?.clip.start.toFixed(2)} | Dur: {activeClip?.clip.duration.toFixed(2)}<br />
            Time: {currentTime.toFixed(2)} | Rel: {activeClip && (currentTime - activeClip.startTime).toFixed(2)}<br />
          </div>

          <div className="absolute top-4 left-4 font-mono text-[10px] bg-black/60 px-2 py-1 rounded text-white border border-white/10 z-10">
            {formatTime(currentTime)}:00
          </div>
          <div className="absolute bottom-4 right-4 font-mono text-[10px] bg-black/60 px-2 py-1 rounded text-white border border-white/10 z-10 flex gap-2">
            <span className={playGreenOnly ? "opacity-50" : ""}>
              {Math.floor(duration / 3600)}:{Math.floor((duration % 3600) / 60)}:{Math.floor(duration % 60)}:00
            </span>
            {playGreenOnly && effectiveDuration !== undefined && (
              <span className="text-green-400 font-bold">
                (Est: {Math.floor(effectiveDuration / 60)}:{Math.floor(effectiveDuration % 60)})
              </span>
            )}
          </div>

          {/* MOVED INSIDE 16:9 CONTAINER FOR ACCURATE RELATIVE POSITIONING */}
          {/* Text Overlays Layer */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 50 }}>
            <AnimatePresence>
              {activeOverlays.map(overlay => (
                <motion.div
                  key={overlay.id}
                  initial={
                    overlay.style === 'slide_up' ? { y: 100, opacity: 0 } :
                      overlay.style === 'fade' ? { opacity: 0 } :
                        { scale: 0.5, opacity: 0 }
                  }
                  animate={
                    overlay.style === 'slide_up' ? { y: 0, opacity: 1 } :
                      overlay.style === 'fade' ? { opacity: 1 } :
                        { scale: 1, opacity: 1 }
                  }
                  exit={
                    overlay.style === 'slide_up' ? { y: -50, opacity: 0 } :
                      overlay.style === 'fade' ? { opacity: 0 } :
                        { scale: 1.2, opacity: 0 }
                  }
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className={`text-white font-bold drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] text-center px-4 whitespace-normal`}
                  style={{
                    position: 'absolute',
                    zIndex: 20,

                    // 1. CONVERT TO PERCENTAGE
                    left: (() => {
                      const x = overlay.positionX ?? 0.5;
                      return x > 1 ? `${x}%` : `${x * 100}%`;
                    })(),
                    top: (() => {
                      const y = overlay.positionY ?? 0.5;
                      return y > 1 ? `${y}%` : `${y * 100}%`;
                    })(),

                    // 2. CENTER ANCHOR
                    transform: 'translate(-50%, -50%)',

                    // 3. SCALE FONT (Using 2.0x boosted cqh logic, fallback to rem if needed)
                    // Note: Since we are now inside container-type: size, 'cqh' is perfect.
                    fontSize: (overlay.fontSize || 0.08) > 1
                      ? `${overlay.fontSize}cqw`
                      : `${(overlay.fontSize || 0.08) * 100 * 2.0}cqh`,

                    color: overlay.textColor || '#ffffff',
                    fontFamily: overlay.fontFamily ? overlay.fontFamily.split('-')[0] : 'Arial',
                    textShadow: '2px 2px 0px black, -1px -1px 0 black, 1px -1px 0 black, -1px 1px 0 black, 1px 1px 0 black',
                    maxWidth: '90%',
                    overflowWrap: 'break-word',
                    width: 'auto',
                    pointerEvents: 'none'
                  }}
                >
                  {overlay.content}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Multi-Track Audio Layer - Robust Sync */}
      {(() => {
        // Find ALL active clips across ALL tracks
        const activeAudioClips = project?.audioClips?.filter(c =>
          currentTime >= c.start && currentTime < (c.start + c.duration)
        );

        if (!activeAudioClips || activeAudioClips.length === 0) return null;

        return activeAudioClips.map((clip) => (
          <audio
            key={`track-${clip.track}-clip-${clip.id}`}
            src={getMediaUrl(clip.source)}
            autoPlay={isPlaying}
            ref={(el) => {
              if (el) {
                // Dynamic Track Volume Control
                const trackKey = `a${clip.track}`;
                const trackVol = project?.trackVolumes?.[trackKey] ?? 1;
                el.volume = trackVol * volume;

                // Immediate sync on mount/update
                const relTime = currentTime - clip.start;
                if (Math.abs(el.currentTime - relTime) > 0.3) el.currentTime = relTime;

                if (isPlaying && el.paused) el.play().catch(() => { });
                if (!isPlaying && !el.paused) el.pause();
              }
            }}
          />
        ));
      })()}

      {/* Playback Controls */}
      <div className="bg-[#1E1E1E] border-t border-[#2A2A2A] p-2 flex flex-col gap-2 shrink-0 z-20">
        <div
          className="h-1 bg-[#121212] w-full rounded-full relative overflow-hidden group cursor-pointer"
          onClick={handleScrub}
        >
          <div
            className="absolute top-0 left-0 h-full bg-blue-600 transition-all duration-100 ease-linear"
            style={{ width: `${(currentTime / Math.max(duration, 1)) * 100}%` }}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <button className="p-2 text-gray-400 hover:text-white transition-colors" onClick={() => onSeek(0)}>
              <SkipBack size={18} fill="currentColor" />
            </button>
            <button
              className="p-3 text-white bg-blue-600 rounded-full hover:bg-blue-500 transition-colors mx-2"
              onClick={onTogglePlay}
            >
              {isPlaying ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" />}
            </button>
            <button className="p-2 text-gray-400 hover:text-white transition-colors" onClick={() => onSeek(duration)}>
              <SkipForward size={18} fill="currentColor" />
            </button>
          </div>

          <div className="flex items-center gap-4">
            {setPlayGreenOnly && (
              <button
                onClick={() => setPlayGreenOnly(!playGreenOnly)}
                className={`flex items-center gap-2 text-[10px] font-bold uppercase transition-colors px-2 py-1 rounded border border-transparent hover:border-white/10 ${playGreenOnly ? 'text-green-400 bg-green-500/10' : 'text-gray-500 hover:text-gray-300'}`}
                title={playGreenOnly ? "Playing Only Green Clips" : "Playing All Clips"}
              >
                <Layers size={14} />
                {playGreenOnly ? "Keep Only" : "All Clips"}
              </button>
            )}
            <div className="flex items-center gap-2 group relative">
              <button onClick={() => setVolume(v => v === 0 ? 1 : 0)}>
                {volume === 0 ? <Volume2 size={14} className="text-red-500" /> : <Volume2 size={14} className="text-gray-500 group-hover:text-white" />}
              </button>
              <div
                className="w-16 h-1 bg-[#2A2A2A] rounded-full overflow-hidden cursor-pointer relative"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const x = e.clientX - rect.left;
                  setVolume(Math.max(0, Math.min(1, x / rect.width)));
                }}
              >
                <div
                  className="h-full bg-gray-500 group-hover:bg-blue-500 transition-colors"
                  style={{ width: `${volume * 100}%` }}
                />
              </div>
            </div>
            <Maximize2 size={16} className="text-gray-500 hover:text-white cursor-pointer" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgramMonitor;
