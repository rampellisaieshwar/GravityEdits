
import React from 'react';
import { CheckCircle2, XCircle, BrainCircuit, Zap, MessageSquare, Download, Info, Type } from 'lucide-react';
import { Clip, ViralShort, TextOverlay } from '../types';

interface InspectorProps {
  clip: Clip | null;
  overlay?: TextOverlay | null;
  onUpdateOverlay?: (updates: Partial<TextOverlay>) => void;
  onToggleStatus: () => void;
  onExport: () => void;
  associatedShort?: ViralShort;
}

const Inspector: React.FC<InspectorProps> = ({ clip, overlay, onUpdateOverlay, onToggleStatus, onExport, associatedShort }) => {
  if (overlay) {
    return (
      <div className="w-full h-full bg-black/40 backdrop-blur-md border-l border-white/5 flex flex-col overflow-y-auto">
        <div className="p-4 border-b border-white/5 bg-white/5 sticky top-0 z-10 shrink-0">
          <div className="flex items-center gap-2 mb-1">
            <Type className="text-purple-500" size={16} />
            <h2 className="text-[10px] font-bold tracking-widest uppercase text-white">Text Inspector</h2>
          </div>
          <div className="text-[9px] text-gray-500 font-mono truncate">{overlay.id}</div>
        </div>

        <div className="p-4 space-y-6 flex-1 overflow-y-auto">
          {/* Text Content */}
          <section>
            <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-2 block">Content</label>
            <textarea
              value={overlay.content}
              onChange={(e) => onUpdateOverlay?.({ content: e.target.value })}
              className="w-full bg-[#121212] border border-[#333] rounded p-2 text-xs text-white focus:border-purple-500 outline-none min-h-[80px]"
              placeholder="Enter text..."
            />
          </section>

          {/* Style Selector */}
          <section>
            <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-2 block">Animation Style</label>
            <div className="grid grid-cols-2 gap-2">
              {['pop', 'slide_up', 'fade', 'typewriter'].map(style => (
                <button
                  key={style}
                  onClick={() => onUpdateOverlay?.({ style: style })}
                  className={`px-3 py-2 rounded text-[10px] font-bold uppercase transition-all border ${overlay.style === style
                    ? 'bg-purple-600 border-purple-400 text-white shadow-lg'
                    : 'bg-[#1a1a1a] border-[#333] text-gray-400 hover:border-gray-500'
                    }`}
                >
                  {style.replace('_', ' ')}
                </button>
              ))}
            </div>
          </section>

          {/* Duration Control */}
          <section>
            <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-2 block">Duration (s)</label>
            <input
              type="number"
              step="0.1"
              value={overlay.duration}
              onChange={(e) => onUpdateOverlay?.({ duration: parseFloat(e.target.value) })}
              className="w-full bg-[#121212] border border-[#333] rounded p-2 text-xs text-white focus:border-purple-500 outline-none"
            />
          </section>

          {/* Color & Font Control */}
          <section className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-2 block">Color</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={overlay.textColor || '#ffffff'}
                  onChange={(e) => onUpdateOverlay?.({ textColor: e.target.value })}
                  className="bg-transparent border-none w-8 h-8 cursor-pointer"
                />
                <span className="text-[10px] text-gray-400 font-mono">{overlay.textColor || '#ffffff'}</span>
              </div>
            </div>
            <div>
              <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-2 block">Font</label>
              <select
                value={overlay.fontFamily || 'Arial-Bold'}
                onChange={(e) => onUpdateOverlay?.({ fontFamily: e.target.value })}
                className="w-full bg-[#121212] border border-[#333] rounded p-1 text-xs text-white focus:border-purple-500 outline-none"
              >
                <option value="Arial-Bold">Arial (Bold)</option>
                <option value="Helvetica-Bold">Helvetica</option>
                <option value="Impact">Impact</option>
                <option value="Courier-Bold">Courier</option>
                <option value="Times-Bold">Times New Roman</option>
                <option value="Verdana-Bold">Verdana</option>
                <option value="Georgia-Bold">Georgia</option>
              </select>
            </div>
          </section>

          {/* Size Control */}
          <section>
            <div className="flex justify-between items-center mb-2">
              <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block">Size</label>
              <span className="text-[9px] text-gray-400">{overlay.fontSize || 4}</span>
            </div>
            <input
              type="range"
              min="1" max="20" step="0.5"
              value={overlay.fontSize || 4}
              onChange={(e) => onUpdateOverlay?.({ fontSize: parseFloat(e.target.value) })}
              className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
          </section>

          {/* Position Control */}
          <section>
            <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-2 block">Position (X / Y)</label>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-gray-500 w-4">X</span>
                <input
                  type="range"
                  min="0" max="100"
                  value={overlay.positionX !== undefined ? overlay.positionX : 50}
                  onChange={(e) => onUpdateOverlay?.({ positionX: parseFloat(e.target.value) })}
                  className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-[9px] text-gray-400 w-6 text-right">{overlay.positionX !== undefined ? overlay.positionX : 50}%</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-gray-500 w-4">Y</span>
                <input
                  type="range"
                  min="0" max="100"
                  value={overlay.positionY !== undefined ? overlay.positionY : 50}
                  onChange={(e) => onUpdateOverlay?.({ positionY: parseFloat(e.target.value) })}
                  className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-[9px] text-gray-400 w-6 text-right">{overlay.positionY !== undefined ? overlay.positionY : 50}%</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    );
  }

  if (!clip) {
    return (
      <div className="w-full h-full bg-black/40 backdrop-blur-md border-l border-white/5 flex flex-col">
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center gap-4">
          <div className="w-16 h-16 rounded-full bg-[#121212] flex items-center justify-center border border-[#2A2A2A]">
            <Info className="text-gray-600" size={32} />
          </div>
          <div className="text-gray-500 text-[10px] font-medium uppercase tracking-widest">
            Select a clip to inspect AI
          </div>
        </div>
        <div className="p-4 border-t border-[#2A2A2A] bg-[#1a1a1a] shrink-0">
          <button
            onClick={onExport}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded text-[10px] font-bold transition-all shadow-lg shadow-blue-900/20"
          >
            <Download size={12} /> EXPORT PROJECT
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-black/40 backdrop-blur-md border-l border-white/5 flex flex-col overflow-y-auto">
      <div className="p-4 border-b border-white/5 bg-white/5 sticky top-0 z-10 shrink-0">
        <div className="flex items-center gap-2 mb-1">
          <BrainCircuit className="text-blue-500" size={16} />
          <h2 className="text-[10px] font-bold tracking-widest uppercase text-white">AI Inspector</h2>
        </div>
        <div className="text-[9px] text-gray-500 font-mono truncate">{clip.source}</div>
      </div>

      <div className="p-4 space-y-6 flex-1 overflow-y-auto">
        <section>
          <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-3 block">Status</label>
          <div className="flex items-center justify-between p-2 bg-white/5 rounded border border-white/10">
            <div className="flex items-center gap-2">
              {clip.keep ? <CheckCircle2 size={14} className="text-blue-500" /> : <XCircle size={14} className="text-red-500" />}
              <span className={`text-[10px] font-bold ${clip.keep ? 'text-blue-400' : 'text-red-400'}`}>
                {clip.keep ? 'APPROVED' : 'REJECTED'}
              </span>
            </div>
            <button onClick={onToggleStatus} className="text-[9px] font-bold bg-[#2A2A2A] hover:bg-[#333] px-2 py-1 rounded transition-colors">FLIP</button>
          </div>
        </section>

        <section>
          <label className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-2 block flex items-center gap-2">
            <MessageSquare size={10} /> Reasoning
          </label>
          <div className="p-3 bg-blue-900/10 rounded border border-blue-900/30">
            <p className="text-[10px] text-gray-300 leading-relaxed italic">"{clip.reason || "No specific reasoning provided."}"</p>
          </div>
        </section>

        {/* Viral Suggestion Section */}
        {associatedShort ? (
          <section className="bg-amber-900/10 p-3 rounded-lg border border-amber-900/30 ring-1 ring-amber-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Zap size={14} className="text-amber-500 fill-amber-500/20" />
              <h3 className="text-[10px] font-bold text-amber-500 uppercase tracking-wide">Featured in Viral Short</h3>
            </div>
            <div className="bg-[#121212] rounded p-2 mb-2">
              <div className="text-[9px] font-bold text-amber-400 mb-0.5">{associatedShort.title}</div>
              <p className="text-[9px] text-gray-400 leading-tight italic">"{associatedShort.description}"</p>
            </div>
            <p className="text-[9px] text-gray-500 leading-tight">
              This clip was specifically selected by AI for this short-form compilation.
            </p>
          </section>
        ) : (clip.reason?.toLowerCase().includes('viral') || clip.reason?.toLowerCase().includes('high energy') || clip.reason?.toLowerCase().includes('hook')) && (
          <section className="bg-amber-900/10 p-3 rounded-lg border border-amber-900/30">
            <div className="flex items-center gap-2 mb-1">
              <Zap size={12} className="text-amber-500" />
              <h3 className="text-[9px] font-bold text-amber-500 uppercase">Viral Potential</h3>
            </div>
            <p className="text-[9px] text-gray-400 leading-tight">
              AI detected characteristics suitable for short-form content.
            </p>
          </section>
        )}
      </div>

      <div className="p-4 border-t border-[#2A2A2A] bg-[#1a1a1a] shrink-0">
        <button
          onClick={onExport}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded text-[10px] font-bold transition-all shadow-lg shadow-blue-900/20"
        >
          <Download size={12} /> EXPORT PROJECT
        </button>
      </div>
    </div>
  );
};

export default React.memo(Inspector);
