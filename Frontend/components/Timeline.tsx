import React, { useState, useRef, useEffect } from 'react';
import { VideoProject, Clip, TextOverlay } from '../types';
import { Scissors, MousePointer2, Film, Volume2, Music, Type, Plus } from 'lucide-react';
import { Reorder, motion } from 'framer-motion';
import { formatDuration } from '../utils/format';

interface TimelineProps {
  project: VideoProject | null;
  selectedClipId: string | null;
  currentTime: number;
  onSelectClip: (id: string) => void;
  onToggleStatus: (id: string) => void;
  onDeleteClip?: (id: string) => void;
  onReorder: (newClips: Clip[]) => void;
  onSeek: (time: number) => void;
  onScrubStart?: () => void;
  onScrubEnd?: () => void;
  onSplitClip: (id: string, offset: number) => void;
  onOpenAudioTab: () => void;
  onAddAudioClip: (source: string, time: number, track: number) => void;
  onAddTrack: () => void;
  onRemoveTrack: (id: number) => void;
  onVolumeChange: (track: string, volume: number) => void;
  onUpdateOverlay: (id: string, updates: Partial<TextOverlay>) => void;
  onAddOverlay: (start: number) => void;
  onSelectOverlay?: (id: string) => void;
  selectedOverlayId?: string | null;
  onDeleteOverlay?: (id: string) => void;
  onUpdateBgMusic: (updates: { start?: number, duration?: number }) => void;
  onUpdateAudioClip?: (id: string, updates: Partial<any>) => void;
  onDeleteAudioClip?: (id: string) => void;
  onSplitAudioClip?: (id: string, offset: number) => void;
  onSplitBgMusic?: (offset: number) => void;
}

// Memoized Track Component to prevent re-rendering on 60fps time updates
const TimelineTracks = React.memo(({
  project,
  zoom,
  selectedClipId,
  onReorder,
  onSelectClip,
  onToggleStatus,
  onDeleteClip,
  activeTool,
  onSplit,
  onAddAudioClip,
  onVolumeChange,
  onUpdateOverlay,
  onDeleteOverlay,
  onSelectOverlay,
  selectedOverlayId,
  onUpdateBgMusic,
  onUpdateAudioClip,
  onDeleteAudioClip,
  onSplitAudioClip,
  onSplitBgMusic
  // Note: onVolumeChange was missing in previous destructuring but present in type
}: {
  project: VideoProject;
  zoom: number;
  selectedClipId: string | null;
  selectedOverlayId?: string | null;
  onSelectOverlay?: (id: string) => void;
  onReorder: (newClips: Clip[]) => void;
  onSelectClip: (id: string) => void;
  onToggleStatus: (id: string) => void;
  onDeleteClip?: (id: string) => void;
  activeTool: 'select' | 'razor';
  onSplit: (id: string, offset: number) => void;
  onAddAudioClip: (source: string, time: number, track: number) => void;
  onVolumeChange: (track: string, volume: number) => void;
  onUpdateOverlay: (id: string, updates: Partial<TextOverlay>) => void;
  onDeleteOverlay?: (id: string) => void;
  onUpdateBgMusic: (updates: { start?: number, duration?: number }) => void;
  onUpdateAudioClip?: (id: string, updates: Partial<any>) => void;
  onDeleteAudioClip?: (id: string) => void;
  onSplitAudioClip?: (id: string, offset: number) => void;
  onSplitBgMusic?: (offset: number) => void;
}) => {
  const audioTracks = project.audioTracks || [2]; // Default to just track 2 if undefined
  const overlays = project.overlays || [];

  // Create a local object for easier access in callbacks where simple access is needed
  const props = { onUpdateAudioClip, onSplitAudioClip, onSplitBgMusic, onDeleteAudioClip };

  return (
    <div className="p-4 flex flex-col gap-1 w-max min-w-full">
      {/* Overlay Track (Above Video) */}
      <div className="relative flex items-stretch gap-[2px] h-12 min-w-full border-b border-white/5 mb-1 bg-purple-900/10">
        {overlays.map(overlay => (
          <motion.div
            key={overlay.id}
            onClick={(e) => {
              e.stopPropagation();
              onSelectOverlay?.(overlay.id);
            }}
            drag="x"
            dragMomentum={false}
            dragConstraints={{ left: 0, right: 10000 }} // Ideally constrained to timeline width
            onDragEnd={(_, info) => {
              // This is rough because "info.point.x" is screen coords. 
              // Better to rely on state or use a ref. 
              // Simplifying: Just let user drag and we calculated delta?
              // actually, motion drag changes visual only unless we bind it.
              // For precise editing, we need to know the new 'start' time.
              // Let's rely on standard mouse drag for precision if framer motion is tricky without refs.
              // But wait, let's try a simple approach: 
              // We render it at 'left'. Drag changes visual 'x'. onDragEnd we read the computed style or 'x' value?
              // Actually, let's use a simpler onMouseDown approach if possible, but framer is easier for "feel".
              // Let's try to calculate based on offset.
              const changeX = info.offset.x;
              const changeTime = changeX / zoom;
              const newStart = Math.max(0, overlay.start + changeTime);
              onUpdateOverlay(overlay.id, { start: newStart });
            }}
            onDoubleClick={(e) => {
              e.stopPropagation();
              const newText = prompt("Edit Text Content:", overlay.content);
              if (newText !== null) onUpdateOverlay(overlay.id, { content: newText });
            }}
            // Initial position
            style={{
              x: overlay.start * zoom, // We use x transform instead of left for framer motion drag to work naturally? 
              // No, better to set 'left' and let drag add transform.
              left: 0,
              position: 'absolute',
              width: `${overlay.duration * zoom}px`
            }}
            className={`absolute top-1 bottom-1 border rounded px-2 overflow-hidden text-xs text-white flex items-center shadow-lg cursor-grab active:cursor-grabbing z-20 group transition-all ${selectedOverlayId === overlay.id
              ? 'bg-purple-600 border-white ring-2 ring-white/50'
              : 'bg-purple-600/80 border-purple-400'
              }`}
          >
            <div className="font-bold truncate pointer-events-none">{overlay.content}</div>

            {/* Delete Button */}
            {onDeleteOverlay && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm(`Delete text overlay "${overlay.content}"?`)) {
                    onDeleteOverlay(overlay.id);
                  }
                }}
                className="absolute top-0 right-0 w-5 h-5 bg-red-500/80 hover:bg-red-600 rounded-bl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-bold z-30"
                title="Delete overlay"
              >
                ×
              </button>
            )}

            {/* Resize Handle (Right) - Simplified */}
            <div
              className="absolute right-0 top-0 bottom-0 w-2 cursor-e-resize hover:bg-white/20"
              onMouseDown={(e) => {
                e.stopPropagation();
                // Prevent drag
              }}
            // We'd need resize logic here. For now, just drag & double click.
            />
          </motion.div>
        ))}
        {overlays.length === 0 && (
          <div className="w-full h-full flex items-center justify-center text-[10px] text-purple-300/30">
            Overlay Track (Click '+' to add text)
          </div>
        )}
      </div>

      {/* Video Track 1 - Now Reorderable */}
      <Reorder.Group
        axis="x"
        values={project.edl}
        onReorder={activeTool === 'select' ? onReorder : () => { }}
        className={`flex items-stretch gap-[2px] h-24 min-w-full ${activeTool === 'razor' ? 'cursor-crosshair' : ''}`}
      >
        {project.edl.map((clip) => (
          <Reorder.Item
            key={clip.id}
            value={clip}
            dragListener={activeTool === 'select'}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation();
              if (activeTool === 'razor') {
                // Calculate relative click position in Seconds
                const itemRect = e.currentTarget.getBoundingClientRect();
                const clickX = e.clientX - itemRect.left;
                const offsetTime = clickX / zoom;
                onSplit(clip.id, offsetTime);
              } else {
                onSelectClip(clip.id);
              }
            }}
            onDoubleClick={(e) => { e.stopPropagation(); onToggleStatus(clip.id); }}
            style={{ width: `${(clip.duration || 5) * zoom}px` }}
            className={`relative shrink-0 flex flex-col justify-between p-2 transition-shadow border-y border-x border-transparent group ${activeTool === 'select' ? 'cursor-grab active:cursor-grabbing' : 'cursor-crosshair'} ${selectedClipId === clip.id ? 'ring-2 ring-white z-10' : ''
              } ${clip.keep
                ? 'bg-blue-600/80 hover:bg-blue-500 border-blue-400'
                : 'bg-red-900/20 hover:bg-red-900/30 opacity-60 border-red-900/30'
              }`}
          >
            <div className="flex justify-between items-start pointer-events-none">
              <span className="text-[10px] font-bold text-white truncate drop-shadow-md">
                {clip.source}
              </span>
              {clip.keep ? (
                <div className="w-2 h-2 rounded-full bg-blue-300 shadow-[0_0_5px_rgba(255,255,255,0.8)]" />
              ) : (
                <div className="w-2 h-2 rounded-full bg-red-500/50" />
              )}
            </div>

            <div className="text-[8px] text-white/50 truncate pointer-events-none">
              {formatDuration(clip.duration || 0)}
            </div>

            {/* Delete Button for Video Clips */}
            {onDeleteClip && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm(`Delete clip "${clip.source}"?`)) {
                    onDeleteClip(clip.id);
                  }
                }}
                className="absolute top-0 right-0 w-5 h-5 bg-red-500/80 hover:bg-red-600 rounded-bl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-bold z-30"
                title="Delete clip"
              >
                ×
              </button>
            )}

            {/* Selection handle indicator */}
            {selectedClipId === clip.id && (
              <motion.div layoutId="selector-left" className="absolute top-0 left-0 w-1 h-full bg-white pointer-events-none" />
            )}
            {selectedClipId === clip.id && (
              <motion.div layoutId="selector-right" className="absolute top-0 right-0 w-1 h-full bg-white pointer-events-none" />
            )}

            {/* Razor Line on Hover (CSS based or simple div) */}
            {activeTool === 'razor' && (
              <div className="absolute top-0 bottom-0 w-[1px] bg-red-400 opacity-0 hover:opacity-100 pointer-events-none" style={{ left: 'var(--mouse-x)' }} />
            )}
          </Reorder.Item>
        ))}
      </Reorder.Group>

      {/* Audio Track 1 - Syncs with Visual Order */}
      <div className="flex items-stretch gap-[2px] h-12 min-w-full">
        {project.edl.map((clip) => (
          <div
            key={`audio-${clip.id}`}
            style={{ width: `${(clip.duration || 5) * zoom}px` }}
            className={`bg-teal-900/30 border-t border-teal-500/20 relative overflow-hidden transition-all duration-300 shrink-0 ${clip.keep ? 'opacity-100' : 'opacity-20 grayscale'
              }`}
          >
            <div className="absolute bottom-0 left-0 w-full h-full flex items-end justify-around gap-[1px] px-1">
              {Array.from({ length: 15 }).map((_, j) => (
                <div key={j} style={{ height: `${20 + Math.random() * 60}%` }} className="w-[1px] bg-teal-400/40 rounded-t" />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Dynamic Secondary Audio Tracks */}
      {audioTracks.map(trackId => (
        <div
          key={trackId}
          className="flex items-stretch gap-[2px] h-12 min-w-full border-t border-white/5 relative bg-[#0e0e0e] transition-colors hover:bg-teal-900/10"
          onDragOver={(e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            e.currentTarget.style.backgroundColor = 'rgba(20, 184, 166, 0.1)';
          }}
          onDragLeave={(e) => {
            e.currentTarget.style.backgroundColor = '';
          }}
          onDrop={(e) => {
            e.preventDefault();
            e.currentTarget.style.backgroundColor = '';
            const data = e.dataTransfer.getData('text/plain') || e.dataTransfer.getData('application/json');

            if (data) {
              try {
                const { type, name } = JSON.parse(data);
                if (type === 'audio') {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const offsetX = e.clientX - rect.left;
                  const time = Math.max(0, offsetX / zoom);
                  onAddAudioClip(name, time, trackId);
                }
              } catch (err) {
                console.error("Drop Parse Error", err);
              }
            }
          }}
        >
          {/* Render Audio Clips for this Track */}
          {project.audioClips?.map(clip => (
            clip.track === trackId && (
              <motion.div
                key={clip.id}
                drag="x"
                dragMomentum={false}
                dragConstraints={{ left: 0, right: 10000 }}
                onDragEnd={(_, info) => {
                  // Update start time based on drag
                  // We need a way to update specific audio clip
                  // passing a new callback "onUpdateAudioClip"
                  const changeX = info.offset.x;
                  const changeTime = changeX / zoom;
                  const newStart = Math.max(0, clip.start + changeTime);
                  // We need to expose this action
                  // For now, we'll assume a prop 'onUpdateAudioClip' exists or we add it
                  // calling onVolumeChange is wrong.
                  // Let's rely on new prop
                  /* @ts-ignore */
                  if (props.onUpdateAudioClip) props.onUpdateAudioClip(clip.id, { start: newStart });
                }}
                className="absolute top-1 bottom-1 bg-teal-800/60 border border-teal-500/50 rounded px-2 overflow-hidden text-[9px] text-teal-100 flex items-center shadow-lg cursor-pointer hover:bg-teal-700/80 active:cursor-grabbing group"
                style={{
                  x: clip.start * zoom,
                  width: `${Math.max(20, clip.duration * zoom)}px`,
                  position: 'absolute',
                  left: 0
                }}
                title={`${clip.source} (${formatDuration(clip.duration)})`}
                onMouseDown={(e) => e.stopPropagation()} // Prevent seek
                onClick={(e) => {
                  e.stopPropagation();
                  if (activeTool === 'razor') {
                    // Split Audio Logic
                    const rect = e.currentTarget.getBoundingClientRect();
                    const clickX = e.clientX - rect.left;
                    const offsetTime = clickX / zoom;
                    // Split relative to clip start
                    /* @ts-ignore */
                    if (props.onSplitAudioClip) props.onSplitAudioClip(clip.id, offsetTime);
                  }
                }}
              >
                <span className="truncate pointer-events-none">{clip.source}</span>

                {/* Delete Button for Audio Clips */}
                {onDeleteAudioClip && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete audio clip "${clip.source}"?`)) {
                        onDeleteAudioClip(clip.id);
                      }
                    }}
                    className="absolute top-0 right-0 w-5 h-5 bg-red-500/80 hover:bg-red-600 rounded-bl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-bold z-30"
                    title="Delete audio clip"
                  >
                    ×
                  </button>
                )}
              </motion.div>
            )
          ))}

          {(!project.audioClips || !project.audioClips.some(c => c.track === trackId)) && (
            <div className="w-full h-full flex items-center justify-center text-[10px] text-gray-700 pointer-events-none">
              <span className="opacity-20">Audio Track A{trackId} (Drag & Drop)</span>
            </div>
          )}
        </div>
      ))}

      {/* Background Music Track */}
      {project.bgMusic && (
        <div className="relative flex items-stretch h-12 min-w-full mt-1 border-t border-white/5 bg-transparent">
          <motion.div
            drag="x"
            dragMomentum={false}
            dragConstraints={{ left: 0, right: 10000 }} // Infinite right
            onDragEnd={(_, info) => {
              // Calculate new start time based on drag offset
              const currentStart = project.bgMusic?.start || 0;
              const changeTime = info.offset.x / zoom;
              const newStart = Math.max(0, currentStart + changeTime);
              onUpdateBgMusic({ start: newStart });
            }}
            style={{
              x: (project.bgMusic.start || 0) * zoom,
              width: `${(project.bgMusic.duration || project.edl.reduce((acc, c) => acc + (c.duration || 0), 0)) * zoom}px`,
              minWidth: '100px', // Minimum visual width
              position: 'absolute',
              left: 0
            }}
            className="bg-purple-900/30 border border-purple-500/20 relative overflow-hidden shrink-0 cursor-grab active:cursor-grabbing hover:bg-purple-900/40 transition-colors rounded-sm h-full"
            title={`${project.bgMusic.source}`}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation();
              if (activeTool === 'razor') {
                const rect = e.currentTarget.getBoundingClientRect();
                const offsetX = e.clientX - rect.left;
                const offsetTime = offsetX / zoom;
                /* @ts-ignore */
                if (props.onSplitBgMusic) props.onSplitBgMusic(offsetTime);
              }
            }}
          >
            <div className="sticky left-2 top-2 text-[10px] text-purple-300 font-bold z-10 flex items-center gap-1 pointer-events-none">
              <span className="opacity-50">♫</span> {project.bgMusic.source}
            </div>
            <div className="absolute bottom-0 left-0 w-full h-full flex items-end justify-between gap-[1px] px-1 opacity-40 pointer-events-none">
              {/* Simplified Waveform Pattern */}
              {Array.from({ length: 100 }).map((_, j) => (
                <div key={j} style={{ height: `${30 + Math.random() * 40}%`, width: '1%' }} className="bg-purple-400/40 rounded-t" />
              ))}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
});

const Timeline: React.FC<TimelineProps> = ({
  project,
  selectedClipId,
  selectedOverlayId,
  currentTime,
  onSelectClip,
  onSelectOverlay,
  onToggleStatus,
  onDeleteClip,
  onReorder,
  onSeek,
  onScrubStart,
  onScrubEnd,
  onSplitClip,
  onOpenAudioTab,
  onAddAudioClip,
  onAddTrack,
  onRemoveTrack,
  onVolumeChange,
  onUpdateOverlay,
  onAddOverlay,
  onDeleteOverlay,
  onUpdateBgMusic,
  onUpdateAudioClip,
  onDeleteAudioClip,
  onSplitAudioClip,
  onSplitBgMusic
}) => {
  if (!project) return null;

  // 1 second = 20 pixels
  // Zoom Level State (Pixels Per Second)
  const [zoom, setZoom] = useState(20);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isScrubbing, setIsScrubbing] = useState(false);
  const [activeTool, setActiveTool] = useState<'select' | 'razor'>('select');
  const [showApprovedOnly, setShowApprovedOnly] = useState(false);

  const displayProject = React.useMemo(() => {
    if (!showApprovedOnly) return project;
    return { ...project, edl: project.edl.filter(c => c.keep) };
  }, [project, showApprovedOnly]);

  const calculateTimeFromEvent = (e: React.MouseEvent | MouseEvent) => {
    if (!scrollContainerRef.current) return 0;
    const rect = scrollContainerRef.current.getBoundingClientRect();
    // Adjust for scroll and start position
    const x = e.clientX - rect.left + scrollContainerRef.current.scrollLeft;
    return Math.max(0, x / zoom);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsScrubbing(true);
    onScrubStart?.();
    onSeek(calculateTimeFromEvent(e));
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isScrubbing) {
      onSeek(calculateTimeFromEvent(e));
    }
  };

  // Attach global mouse listeners for scrubbing dragging
  useEffect(() => {
    if (isScrubbing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isScrubbing]); // Depend on isScrubbing to add/remove listeners

  // Note: we need handleMouseUp to be stable or defined outside if we want to remove it correctly,
  // but useEffect cleanup handles it.
  // Wait, handleMouseUp is not defined inside useEffect but used.
  // It needs to be defined in component scope.

  const handleMouseUp = () => {
    if (isScrubbing) {
      setIsScrubbing(false);
      onScrubEnd?.();
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    // Zoom if Ctrl, Cmd, or Alt is pressed (standard editor behavior)
    if (e.ctrlKey || e.metaKey || e.altKey) {
      e.preventDefault();
      const delta = -e.deltaY * 0.1;
      setZoom(prev => Math.max(1, Math.min(200, prev + delta)));
    }
  };

  const handleRulerWheel = (e: React.WheelEvent) => {
    // Always zoom when wheeling specifically on the ruler (gesture)
    e.preventDefault();
    e.stopPropagation();
    const delta = -e.deltaY * 0.1;
    setZoom(prev => Math.max(1, Math.min(200, prev + delta)));
  };

  // Adaptive Grid Logic
  const getGridInterval = (zoomLevel: number) => {
    if (zoomLevel > 100) return 1;    // Every second
    if (zoomLevel > 40) return 5;     // Every 5 seconds
    if (zoomLevel > 10) return 10;    // Every 10 seconds
    if (zoomLevel > 5) return 30;     // Every 30 seconds
    return 60;                        // Every minute
  };

  const gridInterval = getGridInterval(zoom);
  const totalDuration = project.edl.reduce((acc, c) => acc + (c.duration || 0), 0);
  const totalWidth = totalDuration * zoom + 500; // Extra space


  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-white/5">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 bg-[#121212] p-1 rounded border border-[#2A2A2A]">
            <button
              onClick={() => setActiveTool('razor')}
              className={`p-1 rounded transition-colors ${activeTool === 'razor' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:text-white'}`}
              title="Razor Tool (Click clip to split)"
            >
              <Scissors size={14} />
            </button>
            <button
              onClick={() => setActiveTool('select')}
              className={`p-1 rounded transition-colors ${activeTool === 'select' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:text-white'}`}
              title="Selection Tool"
            >
              <MousePointer2 size={14} />
            </button>
          </div>
          <div className="text-[10px] font-mono text-blue-500 w-20">
            {new Date(currentTime * 1000).toISOString().substr(11, 8)}:00
          </div>
        </div>
        <div className="flex gap-2 items-center">
          <button
            onClick={() => setShowApprovedOnly(!showApprovedOnly)}
            className={`text-[10px] px-2 py-1 rounded border transition-colors ${showApprovedOnly ? 'bg-green-900/40 text-green-300 border-green-500/50' : 'bg-[#2A2A2A] text-gray-400 border-transparent hover:text-white'}`}
            title="Toggle showing only approved clips"
          >
            {showApprovedOnly ? 'Approved Only' : 'All Clips'}
          </button>
          <div className="w-[1px] h-4 bg-[#333] mx-1"></div>
          <button className="text-[10px] text-gray-400 hover:text-white bg-[#2A2A2A] px-2 py-1 rounded">V1</button>
          <button className="text-[10px] text-gray-400 hover:text-white bg-[#2A2A2A] px-2 py-1 rounded">A1</button>
          <button
            onClick={onOpenAudioTab}
            className={`text-[10px] px-2 py-1 rounded flex items-center gap-1 transition-colors ${project.bgMusic ? 'bg-purple-900/40 text-purple-300 border border-purple-500/30' : 'bg-[#2A2A2A] text-gray-400 hover:text-white'}`}
          >
            {project.bgMusic ? 'Music' : '+ Music'}
          </button>
        </div>
      </div>

      <div className="flex-1 flex min-h-0 bg-[#0A0A0A] relative">
        {/* Track Headers (Left Sidebar for Tracks) */}
        <div className="w-10 min-w-[40px] border-r border-[#2A2A2A] bg-[#121212] flex flex-col pt-10 pb-4 z-20 shrink-0 select-none">
          {/* Overlays Header */}
          <div className="h-12 flex flex-col items-center justify-center gap-1 border-b border-[#222] bg-purple-900/10 mb-1 group relative">
            <Type size={14} className="text-purple-400" />
            <span className="text-[9px] font-bold text-gray-500">Overlay</span>
            <button
              onClick={() => onAddOverlay ? onAddOverlay(currentTime) : null}
              className="absolute inset-0 flex items-center justify-center bg-purple-600/80 opacity-0 group-hover:opacity-100 transition-opacity text-white font-bold"
              title="Add Text at Playhead"
            >
              <Plus size={16} />
            </button>
          </div>

          {/* V1 Header */}
          <div className="h-24 flex flex-col items-center justify-center gap-1 border-b border-[#222]">
            <Film size={14} className="text-blue-400" />
            <span className="text-[9px] font-bold text-gray-500">V1</span>
          </div>

          <div className="h-[2px]"></div>{/* Spacing alignment */}

          {/* A1 Header */}
          <div className="h-12 flex flex-col items-center justify-center gap-1 border-b border-[#222] bg-teal-900/10 group relative">
            <Volume2 size={12} className="text-teal-400 group-hover:hidden" />
            <span className="text-[9px] font-bold text-gray-500 group-hover:hidden">A1</span>
            {/* Volume Slider on Hover */}
            <div className="hidden group-hover:flex flex-col items-center w-full h-full justify-center">
              <input
                type="range"
                min="0" max="1" step="0.1"
                value={project.trackVolumes?.a1 ?? 1}
                onChange={(e) => onVolumeChange('a1', parseFloat(e.target.value))}
                className="w-8 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                title={`A1 Volume: ${Math.round((project.trackVolumes?.a1 ?? 1) * 100)}%`}
              />
            </div>
          </div>

          {/* Dynamic Secondary Audio Headers */}
          {(project.audioTracks || [2]).map(trackId => (
            <div key={`track-${trackId}`} className="h-12 flex flex-col items-center justify-center gap-1 border-b border-[#222] bg-teal-900/10 group relative">
              {/* Delete Button (Only visible on hover) */}
              <button
                onClick={() => onRemoveTrack(trackId)}
                className="absolute top-0 right-0 p-[2px] text-gray-500 hover:text-red-500 hidden group-hover:block z-20"
                title="Remove Track"
              >
                <div className="text-[8px]">✕</div>
              </button>

              <Volume2 size={12} className="text-teal-400 group-hover:hidden" />
              <span className="text-[9px] font-bold text-gray-500 group-hover:hidden">A{trackId}</span>
              <div className="hidden group-hover:flex flex-col items-center w-full h-full justify-center">
                <input
                  type="range"
                  min="0" max="1" step="0.1"
                  value={project.trackVolumes?.[`a${trackId}`] ?? 1}
                  onChange={(e) => onVolumeChange(`a${trackId}`, parseFloat(e.target.value))}
                  className="w-8 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                  title={`A${trackId} Volume`}
                />
              </div>
            </div>
          ))}

          {/* Add Track Button */}
          <button
            onClick={onAddTrack}
            className="h-6 flex items-center justify-center border-b border-[#222] hover:bg-[#222] text-gray-500 hover:text-white transition-colors"
            title="Add Audio Track"
          >
            <span className="text-sm font-bold">+</span>
          </button>

          {/* Music Header */}
          {project.bgMusic && (
            <div className="h-12 flex flex-col items-center justify-center gap-1 mt-1 border-b border-[#222] bg-purple-900/10 group relative">
              <Music size={12} className="text-purple-400 group-hover:hidden" />
              <span className="text-[9px] font-bold text-gray-500 group-hover:hidden">Music</span>
              <div className="hidden group-hover:flex flex-col items-center w-full h-full justify-center">
                <input
                  type="range"
                  min="0" max="1" step="0.1"
                  value={project.trackVolumes?.music ?? (project.bgMusic.volume ?? 1)} // Sync with legacy bgMusic volume initially
                  onChange={(e) => onVolumeChange('music', parseFloat(e.target.value))}
                  className="w-8 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                  title={`Music Volume: ${Math.round((project.trackVolumes?.music ?? project.bgMusic.volume ?? 1) * 100)}%`}
                />
              </div>
            </div>
          )}
        </div>

        {/* Scrollable Timeline Area */}
        <div
          ref={scrollContainerRef}
          className="flex-1 overflow-x-auto relative bg-transparent scrollbar-thin overflow-hidden"
          onMouseDown={handleMouseDown}
          onWheel={handleWheel}
          style={{ cursor: activeTool === 'razor' ? 'crosshair' : 'default', paddingLeft: '0px' }}
        >
          {/* Playhead - Moving based on currentTime */}
          <div
            className="absolute top-0 h-full w-[2px] bg-red-500 z-30 pointer-events-none transition-none will-change-transform"
            style={{ transform: `translateX(${currentTime * zoom}px)` }}
          >
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-red-500 rotate-45 -mt-1.5" />
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1px] h-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
          </div>

          {/* Timeline Header (Ruler) */}
          <div
            className="h-6 min-w-full border-b border-[#2A2A2A] flex items-end relative cursor-ew-resize hover:bg-white/5 transition-colors"
            style={{ width: `${totalWidth}px` }}
            onWheel={handleRulerWheel}
          >
            {Array.from({ length: Math.ceil(totalDuration / gridInterval) + 2 }).map((_, i) => (
              <div key={i} className="absolute bottom-0 h-2 border-l border-[#444] text-[8px] text-gray-500 pl-1 select-none pointer-events-none" style={{ left: `${i * gridInterval * zoom}px` }}>
                {formatDuration(i * gridInterval)}
              </div>
            ))}
          </div>

          <TimelineTracks
            project={displayProject}
            zoom={zoom}
            selectedClipId={selectedClipId}
            selectedOverlayId={selectedOverlayId}
            onReorder={onReorder}
            onSelectClip={onSelectClip}
            onSelectOverlay={onSelectOverlay}
            onToggleStatus={onToggleStatus}
            onDeleteClip={onDeleteClip}
            activeTool={activeTool}
            onSplit={onSplitClip}
            onUpdateOverlay={onUpdateOverlay}
            onDeleteOverlay={onDeleteOverlay}
            onUpdateBgMusic={onUpdateBgMusic}
            onUpdateAudioClip={onUpdateAudioClip}
            onDeleteAudioClip={onDeleteAudioClip}
            onSplitAudioClip={onSplitAudioClip}
            onSplitBgMusic={onSplitBgMusic}
          />
        </div>
      </div>
    </div>
  );
};

export default Timeline;
