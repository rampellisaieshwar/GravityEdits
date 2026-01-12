import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Download, CheckCircle2, Cpu, FileVideo } from 'lucide-react';
import { VideoProject } from '../types';
import { API_BASE_URL } from '../constants';

interface ExportOverlayProps {
  onClose: () => void;
  project: VideoProject | null;
  initialExportTarget?: number;
}

const ExportOverlay: React.FC<ExportOverlayProps> = ({ onClose, project, initialExportTarget }) => {
  const [status, setStatus] = useState<'idle' | 'processing' | 'finished'>('idle');
  const [progress, setProgress] = useState(0);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [exportTarget, setExportTarget] = useState<number>(initialExportTarget !== undefined ? initialExportTarget : -1);

  const projectName = project?.name || "Untitled_Edit";

  // Polling for progress
  useEffect(() => {
    if (status !== 'processing' || !jobId) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/export-status/${jobId}`);
        if (!response.ok) return;

        const data = await response.json();

        if (data.progress) setProgress(data.progress);
        if (data.message) {
          setLogs(prev => {
            const last = prev[prev.length - 1];
            if (last !== data.message) return [...prev, data.message].slice(-5);
            return prev;
          });
        }

        if (data.status === 'completed' && data.url) {
          setDownloadUrl(`${API_BASE_URL}${data.url}`);
          setStatus('finished');
          setProgress(100);
          setJobId(null);
        } else if (data.status === 'failed') {
          alert("Render failed: " + data.message);
          setStatus('idle');
          setJobId(null);
        }
      } catch (e) {
        console.error("Polling error", e);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [status, jobId]);

  const handleStartRender = async () => {
    if (!project) return;
    setStatus('processing');
    setProgress(0);
    setLogs(["Starting render job..."]);

    try {
      // Determine clips based on selection
      let clipsToRender = project.edl;
      let renderName = projectName;

      if (exportTarget !== -1 && project.viralShorts[exportTarget]) {
        const short = project.viralShorts[exportTarget];
        // Filter clips that match the short's IDs
        // We create a new list where 'keep' is forced to true for these clips
        clipsToRender = project.edl
          .filter(c => short.clipIds.includes(c.id))
          .map(c => ({ ...c, keep: true }));

        renderName = `${projectName}_${short.title.replace(/\s+/g, '_')}`;

        if (clipsToRender.length === 0) {
          alert("The clips for this short are not available in the current timeline.");
          setStatus('idle');
          return;
        }
      }

      // Prepare payload
      const payload = {
        project: {
          name: renderName,
          renderMode: (exportTarget !== -1) ? 'portrait' : 'landscape',
          // Pass full global settings including colorGrading
          globalSettings: project.globalSettings,
          // Legacy filter key for backward comp just in case, though renderer checks globalSettings now
          filter: project.globalSettings.filterSuggestion,
          clips: clipsToRender.map(c => ({
            id: c.id,
            source: c.source,
            keep: c.keep,
            start: c.start || 0,
            end: c.end || 0,
            // Pass clip-specific color grading
            colorGrading: c.colorGrading
          })),
          // Include Background Music and Secondary Audio Chips
          bgMusic: project.bgMusic,
          audioClips: project.audioClips
        }
      };

      const response = await fetch(`${API_BASE_URL}/export-video/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();

      if (response.ok && data.job_id) {
        setJobId(data.job_id);
        // Status remains 'processing', polling effect takes over
      } else {
        alert("Render start failed: " + (data.detail || data.error || "Unknown error"));
        setStatus('idle');
      }
    } catch (e) {
      console.error("Export failed", e);
      alert("Failed to start render. Check console.");
      setStatus('idle');
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${projectName}_final.mp4`;
      link.target = '_blank'; // Force new tab behavior just in case
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleSaveProject = () => {
    if (!project) return;
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${projectName}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Calculate stats based on SELECTION, not generic project
  // Actually, standard stats are better for generic, but maybe we assume 'approved' for shorts?
  const totalClips = project?.edl.length || 0;
  const approvedClips = project?.edl.filter(c => c.keep).length || 0;
  const skippedClips = totalClips - approvedClips;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-black/90 backdrop-blur-xl flex items-center justify-center p-6"
    >
      <div className="max-w-xl w-full flex flex-col items-center">

        {/* IDLE STATE */}
        {status === 'idle' && (
          <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className="flex flex-col items-center gap-6 text-center w-full">
            <div className="w-24 h-24 rounded-full bg-blue-600/10 flex items-center justify-center border-2 border-dashed border-blue-500/50">
              <FileVideo size={40} className="text-blue-500" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Ready to Render</h2>
              <p className="text-gray-400 text-sm">Convert your timeline into a final MP4 video.</p>

              {/* Stats Badge */}
              <div className="flex gap-4 justify-center mt-4">
                <div className="px-3 py-1 rounded-full bg-green-500/10 border border-green-500/30 text-green-400 text-xs font-bold">
                  {approvedClips} Clips Approved
                </div>
                {skippedClips > 0 && (
                  <div className="px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold">
                    {skippedClips} Clips Skipped
                  </div>
                )}
              </div>
            </div>

            {/* Target Selector */}
            {project && project.viralShorts && project.viralShorts.length > 0 && (
              <div className="w-full text-left bg-white/5 p-4 rounded-xl border border-white/10">
                <label className="text-[10px] uppercase font-bold text-gray-500 block mb-2">Export Target</label>
                <select
                  value={exportTarget}
                  onChange={(e) => setExportTarget(Number(e.target.value))}
                  className="w-full bg-[#111] border border-[#333] rounded-lg px-3 py-3 text-xs text-white focus:outline-none focus:border-blue-500 transition-colors cursor-pointer"
                >
                  <option value={-1}>Current Timeline ({projectName})</option>
                  {project.viralShorts.map((short, i) => (
                    <option key={i} value={i}>Short: {short.title}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="w-full grid grid-cols-2 gap-4">
              <button onClick={onClose} className="p-4 rounded-xl bg-[#222] hover:bg-[#333] text-gray-400 font-bold text-xs uppercase transition-colors">Cancel</button>
              <button onClick={handleStartRender} className="p-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs uppercase transition-colors shadow-lg shadow-blue-900/40 flex items-center justify-center gap-2">
                <Cpu size={16} /> Start Render
              </button>
            </div>
          </motion.div>
        )}

        {/* PROCESSING STATE */}
        {status === 'processing' && (
          <div className="w-full space-y-12">
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                  className="w-32 h-32 rounded-full border-t-2 border-blue-500 border-r-2 border-transparent"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-3xl font-black text-white">{Math.floor(progress)}%</span>
                </div>
                <div className="absolute -top-4 -right-4 bg-blue-600 text-white p-2 rounded-lg shadow-lg">
                  <Cpu size={20} />
                </div>
              </div>
              <div className="text-center">
                <h2 className="text-xl font-bold tracking-widest text-white uppercase">Rendering Media</h2>
                <p className="text-xs text-gray-500 font-mono mt-1">{projectName}.mp4</p>
              </div>
            </div>

            <div className="bg-[#0A0A0A] border border-[#2A2A2A] rounded-xl p-4 font-mono text-[10px] space-y-1 h-32 overflow-hidden shadow-inner">
              {logs.map((log, i) => (
                <motion.div
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  key={i}
                  className="flex gap-2 items-center text-blue-400"
                >
                  <span className="text-gray-600">[{new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]</span>
                  <span className={i === logs.length - 1 ? "text-white" : "text-blue-900"}>{log}</span>
                </motion.div>
              ))}
              <div className="animate-pulse w-1 h-3 bg-blue-500 inline-block" />
            </div>

            <div className="space-y-2">
              <div className="h-1.5 w-full bg-[#1A1A1A] rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.8)]"
                  animate={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* FINISHED STATE */}
        {status === 'finished' && (
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="flex flex-col items-center gap-6 text-center"
          >
            <div className="w-24 h-24 rounded-full bg-green-500/20 border border-green-500/50 flex items-center justify-center shadow-[0_0_40px_rgba(34,197,94,0.2)]">
              <CheckCircle2 size={48} className="text-green-500" />
            </div>

            <div className="space-y-1">
              <h2 className="text-2xl font-black text-white uppercase tracking-tight">Export Successful</h2>
              <p className="text-gray-400 text-sm max-w-xs mx-auto">Your project "{projectName}" is encoded and ready for distribution.</p>
            </div>

            <div className="grid grid-cols-2 gap-4 w-full">
              <button
                onClick={handleDownload}
                className="flex flex-col items-center gap-2 p-4 bg-[#1A1A1A] hover:bg-[#222] border border-[#2A2A2A] rounded-xl transition-all group"
              >
                <Download className="text-blue-500 group-hover:scale-110 transition-transform" />
                <span className="text-[10px] font-bold uppercase text-gray-400">Download .MP4</span>
              </button>

              <button
                onClick={handleSaveProject}
                className="flex flex-col items-center gap-2 p-4 bg-[#1A1A1A] hover:bg-[#222] border border-[#2A2A2A] rounded-xl transition-all group"
              >
                <li className="list-none"><FileVideo className="text-purple-500 group-hover:scale-110 transition-transform" /></li>
                <span className="text-[10px] font-bold uppercase text-gray-400">Save Project JSON</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="mt-4 text-xs font-bold text-gray-500 hover:text-white transition-colors underline underline-offset-4"
            >
              Back to Editor
            </button>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default ExportOverlay;
