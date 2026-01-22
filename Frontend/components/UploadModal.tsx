
import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, Check, Loader2, FileVideo, Film, BrainCircuit, AlertCircle, PlayCircle, CheckCircle, X } from 'lucide-react';
import { VideoProject } from '../types';
import { parseEDLXml } from '../utils/xmlParser';
import { API_BASE_URL } from '../constants';

interface UploadModalProps {
  onComplete: () => void;
  setProject: (project: VideoProject) => void;
  projectName?: string | null;
}

const UploadModal: React.FC<UploadModalProps> = ({ onComplete, setProject, projectName }) => {
  const [stage, setStage] = useState<'selection' | 'upload' | 'uploaded' | 'processing' | 'finishing'>('selection');
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; duration: number }[]>([]);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [analysisJobId, setAnalysisJobId] = useState<string | null>(null);
  const [description, setDescription] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const xmlInputRef = useRef<HTMLInputElement>(null);

  const effectiveProjectName = projectName || "Project_Default";

  const checkAnalysisStatus = async () => {
    if (!analysisJobId) return false;

    try {
      const statusRes = await fetch(`${API_BASE_URL}/analysis-status/${analysisJobId}`);
      if (!statusRes.ok) {
        if (statusRes.status === 404) {
          setError("Analysis process died (Backend restarted or crashed).");
          return true;
        }
        return false;
      }

      const statusData = await statusRes.json();

      if (typeof statusData.progress === 'number') {
        setProgress(statusData.progress);
      }

      if (statusData.status === 'failed') {
        setError(statusData.message || "Analysis failed");
        return true;
      }

      if (statusData.status === 'completed') {
        // Fetch EDL from Project-specific Endpoint
        const response = await fetch(`${API_BASE_URL}/api/projects/${effectiveProjectName}/edl`);
        if (response.ok) {
          const xmlText = await response.text();

          let metadata = null;
          try {
            const metaRes = await fetch(`${API_BASE_URL}/api/projects/${effectiveProjectName}/analysis`);
            if (metaRes.ok) {
              metadata = await metaRes.json();
            }
          } catch (e) {
            console.warn("Could not load analysis metadata", e);
          }

          const parsedProject = parseEDLXml(xmlText, metadata);
          setProject(parsedProject);
          setProgress(100);
          setTimeout(() => setStage('finishing'), 800);
          return true;
        }
      }

      return false;
    } catch (e) {
      console.error("Polling check failed", e);
      return false;
    }
  };

  const startPolling = () => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;

      // Real progress comes from backend now
      // setProgress(prev => ...);

      const done = await checkAnalysisStatus();
      if (done) {
        clearInterval(interval);
      }

      if (attempts > 300) { // 10 minutes timeout
        clearInterval(interval);
        setError("Processing timed out.");
        setStage('upload');
      }
    }, 2000);
  };

  const handleXmlSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const project = parseEDLXml(text, null); // Manual XML import might not have analysis meta
      project.name = effectiveProjectName;
      setProject(project);
      onComplete();
    } catch (e: any) {
      setError("Failed to parse XML: " + e.message);
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setStage('processing');
    setProgress(5);
    setError(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    // Pass Project Name
    formData.append('project_name', effectiveProjectName);

    try {
      const uploadRes = await fetch(`${API_BASE_URL}/upload-batch/?trigger_ai=false`, {
        method: 'POST',
        body: formData
      });

      if (!uploadRes.ok) {
        const errorData = await uploadRes.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const data = await uploadRes.json();
      setUploadedFiles(data.files || []);
      setStage('uploaded');

    } catch (err: any) {
      console.error("Upload failed:", err);
      setError(err.message || "Failed to upload files. Ensure backend is running.");
      setStage('upload');
    }
  };

  const handleAnalyze = async () => {
    const apiKey = localStorage.getItem("gravity_api_key");
    if (!apiKey) {
      // Trigger global settings modal
      window.dispatchEvent(new Event("openAPISettings"));
      alert("Please provide an API Key in Settings to proceed with AI Analysis.");
      return;
    }

    setStage('processing');
    setProgress(5);
    try {
      const res = await fetch(`${API_BASE_URL}/analyze/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: effectiveProjectName,
          file_names: uploadedFiles.map(f => f.name),
          description: description,
          api_key: apiKey // Pass the key!
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.job_id) {
          setAnalysisJobId(data.job_id);
        }
      }
    } catch (e) {
      console.error("Analysis trigger failed", e);
      setError("Failed to start analysis.");
      setStage('uploaded');
    }
  };

  // Use Effect to start polling when job ID is set
  React.useEffect(() => {
    if (analysisJobId && stage === 'processing') {
      startPolling();
    }
  }, [analysisJobId]);

  const handleManual = () => {
    // Determine default duration scheme if backend returned 0
    const defaultDuration = 10;

    const manualClips = uploadedFiles.map((file, idx) => ({
      id: `manual-${idx}-${Date.now()}`,
      source: file.name,
      keep: true,
      reason: 'Manual Import',
      // Manual clips usually play the whole file, so start=0, end=duration
      start: 0,
      end: file.duration || defaultDuration,
      duration: file.duration || defaultDuration,
      emotionScore: 50,
      visual_data: { brightness: "normal" } // Mock visual data for safety
    }));

    const manualProject: VideoProject = {
      name: effectiveProjectName,
      globalSettings: { filterSuggestion: 'None' },
      edl: manualClips,
      viralShorts: [],
      overlays: [],
      // Initialize optional audio fields to prevent undefined crashes in Timeline
      audioTracks: [2],
      trackVolumes: { a1: 1, a2: 1, music: 1 },
      audioClips: [],
      bgMusic: undefined
    };

    console.log("Initializing Manual Project:", manualProject);
    setProject(manualProject);

    // Slight delay to ensure state propagates before unmounting? 
    // No, App handles sync. But let's be safe.
    onComplete();
  };

  const handleClose = () => {
    // Just close the modal without loading anything
    onComplete();
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  const processingMessages = [
    "Uploading footage...",
    "Transcribing audio...",
    "Analyzing visual flow...",
    "Gravity is deciding cuts...",
    "Building your EDL..."
  ];

  const currentMessageIndex = Math.min(
    Math.floor((progress / 100) * processingMessages.length),
    processingMessages.length - 1
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="bg-[#1E1E1E] border border-[#2A2A2A] w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden"
      >
        <div className="p-8 relative">
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors p-2"
          >
            <X size={20} />
          </button>

          {stage === 'selection' && (
            <div className="flex flex-col items-center gap-8 py-4">
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-white">Project Setup</h2>
                <p className="text-gray-400">Choose how to initialize your workspace.</p>
              </div>

              <div className="grid grid-cols-2 gap-4 w-full">
                <div
                  onClick={() => setStage('upload')}
                  className="bg-[#121212] border border-[#333] hover:border-blue-500 rounded-xl p-6 cursor-pointer group transition-all flex flex-col items-center gap-4 text-center"
                >
                  <div className="w-16 h-16 rounded-full bg-blue-900/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Upload size={32} className="text-blue-500" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white mb-1">Upload Media</h3>
                    <p className="text-xs text-gray-500">Upload raw footage. Choose AI Analysis or Manual editing later.</p>
                  </div>
                </div>

                <div
                  onClick={() => xmlInputRef.current?.click()}
                  className="bg-[#121212] border border-[#333] hover:border-purple-500 rounded-xl p-6 cursor-pointer group transition-all flex flex-col items-center gap-4 text-center"
                >
                  <input type="file" accept=".xml" ref={xmlInputRef} onChange={handleXmlSelect} className="hidden" />
                  <div className="w-16 h-16 rounded-full bg-purple-900/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <FileVideo size={32} className="text-purple-500" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white mb-1">Import XML</h3>
                    <p className="text-xs text-gray-500">Load an existing timeline from a Premiere/Final Cut XML file.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {stage === 'upload' && (
            <div className="flex flex-col items-center gap-6">
              <input
                type="file"
                multiple
                accept="video/*"
                className="hidden"
                ref={fileInputRef}
                onChange={handleFileSelect}
              />

              <div className="w-24 h-24 rounded-full bg-blue-600/10 flex items-center justify-center border-2 border-dashed border-blue-500/50">
                <Upload size={32} className="text-blue-500" />
              </div>
              <div className="text-center">
                <h2 className="text-xl font-bold text-white mb-2">Import Media for AI Analysis</h2>
                <p className="text-gray-400 text-sm max-w-sm">
                  Upload your raw video files. The AI will analyze them, prune bad takes, and structure your edit automatically.
                </p>
              </div>

              {error && (
                <div className="w-full bg-red-900/20 border border-red-500/50 p-3 rounded-lg flex items-center gap-3 text-red-400 text-xs">
                  <AlertCircle size={14} />
                  {error}
                </div>
              )}

              <div
                className="w-full h-48 border-2 border-dashed border-[#2A2A2A] hover:border-blue-500/50 transition-colors rounded-xl flex flex-col items-center justify-center gap-3 cursor-pointer group"
                onClick={triggerFileSelect}
              >
                <div className="flex gap-2">
                  <FileVideo className="text-gray-600 group-hover:text-blue-500 transition-colors" />
                  <Film className="text-gray-600 group-hover:text-blue-500 transition-colors" />
                </div>
                <span className="text-xs font-medium text-gray-500 group-hover:text-gray-300">
                  Click to select files
                </span>
              </div>

              <div className="w-full flex gap-4 pt-4">
                <button
                  onClick={triggerFileSelect}
                  className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl text-sm transition-all shadow-lg shadow-blue-900/40 flex items-center justify-center gap-2"
                >
                  <BrainCircuit size={18} />
                  Select Files & Analyze
                </button>
              </div>
            </div>
          )}

          {stage === 'uploaded' && (
            <div className="flex flex-col items-center gap-6 py-4">
              <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/30">
                <CheckCircle size={32} className="text-blue-500" />
              </div>
              <div className="text-center">
                <h2 className="text-xl font-bold text-white mb-2">Upload Complete</h2>
                <p className="text-gray-400 text-sm max-w-sm">
                  {uploadedFiles.length} file{uploadedFiles.length !== 1 ? 's' : ''} ready.
                </p>
              </div>

              {/* Description Input */}
              <div className="w-full max-w-md space-y-2">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest pl-1">
                  Describe your vision (Optional)
                </label>
                <textarea
                  className="w-full bg-[#121212] border border-[#333] rounded-xl p-4 text-white text-sm focus:border-blue-500 focus:outline-none min-h-[100px] resize-none placeholder:text-gray-700"
                  placeholder="e.g. 'Make a dynamic vlog with fast cuts', or 'Focus on the nature shots and keep it slow paced'..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="flex gap-4 w-full pt-2">
                <button
                  onClick={handleManual}
                  className="flex-1 bg-[#2A2A2A] hover:bg-[#333] text-gray-200 font-bold py-4 rounded-xl text-sm transition-all border border-gray-700 hover:border-gray-500 flex flex-col items-center gap-2 group"
                >
                  <PlayCircle size={24} className="text-gray-400 group-hover:text-white transition-colors" />
                  <span>Manual Editor</span>
                </button>

                <button
                  onClick={handleAnalyze}
                  className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl text-sm transition-all shadow-lg shadow-blue-900/40 flex flex-col items-center gap-2 group border border-blue-400/50"
                >
                  <BrainCircuit size={24} className="text-blue-100 group-hover:scale-110 transition-transform" />
                  <span>AI Analysis</span>
                </button>
              </div>
            </div>
          )}

          {stage === 'processing' && (
            <div className="flex flex-col items-center gap-8 py-12">
              <div className="relative">
                <Loader2 className="animate-spin text-blue-500" size={64} />
                <BrainCircuit className="absolute inset-0 m-auto text-blue-300" size={32} />
              </div>

              <div className="w-full space-y-4">
                <div className="flex justify-between items-end">
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest">Processing Project</h3>
                    <p className="text-xs text-blue-400 animate-pulse">{processingMessages[currentMessageIndex]}</p>
                  </div>
                  <span className="text-2xl font-black text-white">{Math.round(progress)}%</span>
                </div>

                <div className="h-3 w-full bg-[#121212] rounded-full overflow-hidden border border-[#2A2A2A]">
                  <motion.div
                    className="h-full bg-blue-600 shadow-[0_0_20px_rgba(37,99,235,0.6)]"
                    animate={{ width: `${progress}%` }}
                    transition={{ type: "spring", stiffness: 50 }}
                  />
                </div>
              </div>
            </div>
          )}

          {stage === 'finishing' && (
            <div className="flex flex-col items-center gap-6 py-6 text-center">
              <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center border border-green-500/50">
                <Check size={40} className="text-green-500" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">AI Analysis Complete!</h2>
                <p className="text-gray-400 text-sm max-w-sm mx-auto">
                  Gravity has finished pruning your takes. Your workspace is configured and ready.
                </p>
              </div>
              <button
                onClick={onComplete}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black py-4 rounded-xl text-sm tracking-widest uppercase transition-all shadow-xl shadow-blue-900/40"
              >
                OPEN WORKSPACE
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default UploadModal;
