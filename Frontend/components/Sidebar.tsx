import React, { useState, useEffect, useRef } from 'react';
import { LayoutGrid, List, Film, Zap, Search, MoreVertical, Sparkles, Send, Loader2, Plus, Trash2, Download, Music, Volume2, Settings } from 'lucide-react';
import { VideoProject, Clip } from '../types';
import { formatDuration } from '../utils/format';
import { API_BASE_URL } from '../constants';

interface SidebarProps {
  project: VideoProject | null;
  tab: 'media' | 'viral' | 'audio';
  setTab: (tab: 'media' | 'viral' | 'audio') => void;
  onSelectClip: (id: string) => void;
  onUpdateProject: (project: VideoProject) => void;
  selectedId: string | null;
  onOpenUpload: () => void;
  onBack: () => void;
  onLoadShort: (shortId: number) => void;
  onExportShort: (shortId: number) => void;
  onAddAudioClip?: (source: string, time: number, track: number) => void;
  onOpenSettings: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ project, tab, setTab, onSelectClip, onUpdateProject, selectedId, onOpenUpload, onBack, onLoadShort, onExportShort, onAddAudioClip, onOpenSettings }) => {
  const [audioFiles, setAudioFiles] = useState<{ name: string; path: string }[]>([]);
  const audioInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (tab === 'audio') {
      fetchAudioFiles();
    }
  }, [tab]);

  const fetchAudioFiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/uploaded-audio/${project?.name ? `?project_name=${project.name}` : ''}`);
      if (response.ok) {
        const data = await response.json();
        setAudioFiles(data.files || []);
      }
    } catch (error) {
      console.error("Failed to fetch audio files", error);
    }
  };

  const handleAudioUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    if (project?.name) {
      formData.append('project_name', project.name);
    }

    try {
      const res = await fetch(`${API_BASE_URL}/upload-batch/`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        fetchAudioFiles();
      }
    } catch (err) {
      console.error("Audio upload failed", err);
    }
  };

  const handleDeleteClip = (e: React.MouseEvent, clipId: string) => {
    e.stopPropagation(); // Prevent selecting the clip when deleting
    if (!project) return;

    // Remove clip from EDL
    const updatedEdl = project.edl.filter(c => c.id !== clipId);

    // Also remove any viral shorts associated with this clip
    const updatedShorts = project.viralShorts.filter(s => s.originalClipId !== clipId);

    onUpdateProject({
      ...project,
      edl: updatedEdl,
      viralShorts: updatedShorts
    });
  };

  const handleSetBgMusic = (file: { name: string; path: string }) => {
    if (!project) return;
    onUpdateProject({
      ...project,
      bgMusic: {
        source: file.name, // Just filename for backend resolution or path
        volume: 0.5,
        loop: true
      }
    });
  };

  const handleRemoveBgMusic = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!project) return;
    const { bgMusic, ...rest } = project;
    onUpdateProject(rest as VideoProject);
  };



  return (
    <div className="w-full h-full bg-black/40 backdrop-blur-md flex flex-col border-r border-white/5">
      <div className="p-3 flex items-center justify-between border-b border-white/5 shrink-0">
        <div className="flex gap-1 items-center">
          <button
            onClick={() => {
              if (window.confirm("Are you sure you want to go back? Your unsaved edits regarding the project state in memory will be lost unless you saved the JSON.")) {
                onBack();
              }
            }}
            title="Back to Dashboard"
            className="mr-2 p-1 text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
          >
            <LayoutGrid size={14} />
          </button>

          <button
            onClick={() => setTab('media')}
            className={`px-3 py-1 text-[10px] uppercase font-bold tracking-wider rounded transition-colors ${tab === 'media' ? 'bg-[#333] text-white' : 'text-gray-500 hover:text-gray-300'
              }`}
          >
            Media
          </button>
          <button
            onClick={() => setTab('viral')}
            className={`px-3 py-1 text-[10px] uppercase font-bold tracking-wider rounded transition-colors flex items-center gap-1 ${tab === 'viral' ? 'bg-[#333] text-amber-500' : 'text-gray-500 hover:text-gray-300'
              }`}
          >
            <Zap size={10} className={tab === 'viral' ? 'fill-amber-500' : ''} />
            Viral
          </button>
          <button
            onClick={() => setTab('audio')}
            className={`px-3 py-1 text-[10px] uppercase font-bold tracking-wider rounded transition-colors flex items-center gap-1 ${tab === 'audio' ? 'bg-[#333] text-purple-500' : 'text-gray-500 hover:text-gray-300'
              }`}
          >
            <Music size={10} />
            Audio
          </button>
        </div>

        {tab === 'media' && (
          <button
            onClick={onOpenUpload}
            className="p-1.5 ml-2 bg-blue-600 hover:bg-blue-500 rounded-full text-white transition-colors shadow-lg"
            title="Import Media"
          >
            <Plus size={14} strokeWidth={3} />
          </button>
        )}
        {tab === 'audio' && (
          <>
            <button
              onClick={() => audioInputRef.current?.click()}
              className="p-1.5 ml-2 bg-purple-600 hover:bg-purple-500 rounded-full text-white transition-colors shadow-lg"
              title="Import Audio"
            >
              <Plus size={14} strokeWidth={3} />
            </button>
            <input ref={audioInputRef} type="file" accept=".mp3, .wav, .m4a, .aac, .ogg, audio/*" multiple onChange={handleAudioUpload} className="hidden" />
          </>
        )}
      </div>

      <div className="p-2 border-b border-[#2A2A2A] shrink-0">
        <div className="relative">
          <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search assets..."
            className="w-full bg-white/5 border border-white/10 rounded py-1 pl-7 pr-2 text-[11px] focus:outline-none focus:border-blue-500 text-gray-300 placeholder:text-gray-600"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {tab === 'media' ? (
          <div className="p-2 grid grid-cols-1 gap-1">
            {project?.edl.map((clip) => (
              <div
                key={clip.id}
                onClick={() => onSelectClip(clip.id)}
                className={`group flex items-center gap-2 p-2 rounded cursor-pointer transition-all border relative pr-8 ${selectedId === clip.id
                  ? 'bg-blue-600/20 border-blue-500/50 shadow-[0_0_15px_rgba(37,99,235,0.2)]'
                  : 'bg-white/5 border-transparent hover:border-white/10 hover:bg-white/10'
                  }`}
              >
                <div className="w-10 h-7 bg-gray-800 rounded flex items-center justify-center relative overflow-hidden shrink-0">
                  <Film size={12} className="text-gray-600" />
                  {!clip.keep && (
                    <div className="absolute inset-0 bg-red-900/40" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] font-medium truncate text-gray-300">
                    {clip.source}
                  </div>
                  <div className="text-[8px] text-gray-500 truncate">
                    {formatDuration(clip.duration || 0)} • {clip.keep ? 'Approved' : 'Rejected'}
                  </div>
                </div>

                {/* Delete Button */}
                <button
                  onClick={(e) => handleDeleteClip(e, clip.id)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded-md opacity-0 group-hover:opacity-100 transition-all"
                  title="Remove clip"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        ) : tab === 'viral' ? (
          <div className="p-2 flex flex-col gap-2">
            {project?.viralShorts.map((short, idx) => (
              <div
                key={idx}
                onClick={() => onLoadShort(idx)}
                className="bg-[#121212] border border-amber-900/30 rounded p-3 hover:border-amber-500 transition-colors cursor-pointer group relative overflow-hidden"
              >
                <div className="flex justify-between items-start mb-1">
                  <h3 className="text-amber-500 font-bold text-xs truncate pr-4">{short.title || `Short #${idx + 1}`}</h3>
                  <div className="flex gap-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); onExportShort(idx); }}
                      className="p-1 hover:bg-amber-500/20 rounded text-gray-500 hover:text-amber-500 transition-colors"
                      title="Export Short"
                    >
                      <Download size={12} />
                    </button>
                    <Zap size={12} className="text-amber-500 shrink-0 mt-1" />
                  </div>
                </div>
                <p className="text-[10px] text-gray-400 leading-snug mb-2 line-clamp-2">
                  {short.description}
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded border border-amber-500/20">
                    {short.clipIds.length} Clips
                  </span>
                  <span className="text-[9px] text-gray-600 uppercase font-bold tracking-wider group-hover:text-amber-400 transition-colors">
                    Click to Load
                  </span>
                </div>
              </div>
            ))}
            {(!project?.viralShorts || project.viralShorts.length === 0) && (
              <div className="text-center p-4 text-gray-500 text-xs italic">
                No viral shorts identified yet.
              </div>
            )}
          </div>
        ) : (
          <div className="p-2 flex flex-col gap-1 h-full">
            {audioFiles.length > 0 ? (
              // Existing List
              audioFiles.map((file, idx) => (
                <div
                  key={idx}
                  draggable={true}
                  onDragStart={(e) => {
                    // Use text/plain for better compatibility
                    const payload = JSON.stringify({ type: 'audio', name: file.name, path: file.path });
                    e.dataTransfer.setData('text/plain', payload);
                    e.dataTransfer.effectAllowed = 'copy';
                  }}
                  onClick={() => handleSetBgMusic(file)}
                  className={`group flex items-center gap-2 p-2 rounded cursor-pointer transition-all border relative pr-8 ${project?.bgMusic?.source === file.name
                    ? 'bg-purple-900/20 border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.2)]'
                    : 'bg-white/5 border-transparent hover:border-white/10 hover:bg-white/10'
                    } active:cursor-grabbing hover:cursor-grab`}
                >
                  <div className="absolute right-8 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); onAddAudioClip?.(file.name, 0, 2); }} // Add to A2 at 0s
                      className="p-1 bg-teal-600 hover:bg-teal-500 rounded text-white"
                      title="Add to Track A2"
                    >
                      <Plus size={10} />
                    </button>
                  </div>
                  <div className="w-10 h-7 bg-gray-800 rounded flex items-center justify-center shrink-0">
                    <Volume2 size={12} className={project?.bgMusic?.source === file.name ? "text-purple-400" : "text-gray-600"} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[10px] font-medium truncate text-gray-300">
                      {file.name}
                    </div>
                  </div>
                  {project?.bgMusic?.source === file.name && (
                    <button
                      onClick={handleRemoveBgMusic}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-purple-400 hover:text-red-500 hover:bg-red-500/10 rounded-md transition-all"
                      title="Remove Music"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              ))
            ) : (
              // Empty State
              <div className="flex flex-col items-center justify-center h-40 border border-dashed border-white/10 rounded m-2 text-center gap-2">
                <Music size={24} className="text-gray-600 mb-2" />
                <p className="text-[10px] text-gray-500">No audio files found.</p>
                <button
                  onClick={() => audioInputRef.current?.click()}
                  className="text-[10px] bg-[#333] hover:bg-purple-600 hover:text-white text-gray-300 px-3 py-1.5 rounded transition-all mt-1"
                >
                  Upload Music
                </button>
              </div>
            )}
          </div>
        )}
      </div>


    </div >
  );
};

export default React.memo(Sidebar);
