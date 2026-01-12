
import React from 'react';
import { Palette, Wand2, RotateCcw, Sun, Thermometer, Droplets, Contrast as ContrastIcon } from 'lucide-react';
import { Clip, VideoProject } from '../types';

interface ColorInspectorProps {
  clip: Clip | null;
  filterApplied: boolean;
  setFilterApplied: (val: boolean) => void;
  project: VideoProject | null;
  onUpdateProject?: (project: VideoProject) => void;
}

const FILTERS = [
  { name: 'None', label: 'No Filter', color: 'bg-gray-700' },
  { name: 'Cinematic', label: 'Cinematic', color: 'bg-teal-700' },
  { name: 'Teal & Orange', label: 'Teal & Orange', color: 'bg-orange-500' },
  { name: 'Vintage', label: 'Vintage', color: 'bg-yellow-700' },
  { name: 'Noir', label: 'Noir', color: 'bg-black border border-white/20' },
  { name: 'Vivid', label: 'Vivid', color: 'bg-red-500' },
  { name: 'Vivid Warm', label: 'Vivid Warm', color: 'bg-orange-600' },
  { name: 'Vivid Cool', label: 'Vivid Cool', color: 'bg-blue-500' },
  { name: 'Dramatic', label: 'Dramatic', color: 'bg-indigo-900' },
  { name: 'Silvertone', label: 'Silvertone', color: 'bg-gray-200' },
  { name: 'Mono', label: 'Mono', color: 'bg-gray-400' },
];



const AdjustmentSlider = ({
  label,
  value,
  displayValue,
  min,
  max,
  step = 1,
  onChange,
  icon: Icon,
  iconColor,
  gradient,
  trackBg = "bg-white/10"
}: {
  label: string,
  value: number,
  displayValue: string,
  min: number,
  max: number,
  step?: number,
  onChange: (val: number) => void,
  icon: any,
  iconColor: string,
  gradient?: string,
  trackBg?: string
}) => {
  const trackRef = React.useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const track = trackRef.current;
    if (!track) return;

    const updateValue = (clientX: number) => {
      const rect = track.getBoundingClientRect();
      const percentage = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      const newValue = min + percentage * (max - min);
      // Snap to step
      const steppedValue = Math.round(newValue / step) * step;
      onChange(Math.max(min, Math.min(max, steppedValue)));
    };

    updateValue(e.clientX);

    const handleMouseMove = (mv: MouseEvent) => updateValue(mv.clientX);
    const handleMouseUp = () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center text-[9px]">
        <div className="flex items-center gap-2 text-gray-400">
          <Icon size={10} className={iconColor} />
          {label}
        </div>
        <span className="font-mono text-gray-500">{displayValue}</span>
      </div>
      <div
        ref={trackRef}
        onMouseDown={handleMouseDown}
        className={`h-1 w-full ${gradient ? gradient : trackBg} rounded-full border border-[#2A2A2A] relative group cursor-ew-resize`}
      >
        <div
          style={{ left: `${percentage}%` }}
          className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-white rounded-full border border-black shadow shadow-black/50 pointer-events-none"
        />
      </div>
    </div>
  );
};

const ColorInspector: React.FC<ColorInspectorProps> = ({ clip, filterApplied, setFilterApplied, project, onUpdateProject }) => {
  const activeFilter = project?.globalSettings.filterSuggestion || 'None';

  const handleFilterSelect = (filterName: string) => {
    setFilterApplied(filterName !== 'None');
    if (project && onUpdateProject) {
      const updatedProject = {
        ...project,
        globalSettings: {
          ...project.globalSettings,
          filterSuggestion: filterName
        }
      };
      onUpdateProject(updatedProject);
    }
  };

  // if (!clip) check removed to allow global editing
  const targetLabel = clip ? clip.source : "Project Global";

  const defaultColorSettings = {
    temperature: 5600,
    exposure: 0,
    contrast: 0,
    saturation: 100,
    filterStrength: 100
  };

  const currentSettings = (clip ? clip.colorGrading : project?.globalSettings.colorGrading) || defaultColorSettings;

  const updateColorSetting = (key: keyof typeof defaultColorSettings, value: number) => {
    const newSettings = { ...currentSettings, [key]: value };

    if (clip && project && onUpdateProject) {
      // Update clip specific settings
      const updatedEdl = project.edl.map(c =>
        c.id === clip.id ? { ...c, colorGrading: newSettings } : c
      );
      onUpdateProject({ ...project, edl: updatedEdl });
    } else if (project && onUpdateProject) {
      // Update global settings
      onUpdateProject({
        ...project,
        globalSettings: {
          ...project.globalSettings,
          colorGrading: newSettings
        }
      });
    }
  };

  return (
    <div className="w-full h-full bg-black/40 backdrop-blur-md border-l border-white/5 flex flex-col overflow-y-auto">
      <div className="p-4 border-b border-white/5 bg-white/5 sticky top-0 z-10 flex justify-between items-center shrink-0">
        <div className="flex items-center gap-2">
          <Palette className="text-blue-500" size={16} />
          <div>
            <h2 className="text-[10px] font-bold tracking-widest uppercase text-white">Color Board</h2>
            <div className="text-[9px] text-gray-500 font-mono truncate max-w-[150px]">{targetLabel}</div>
          </div>
        </div>
        <button className="text-gray-500 hover:text-white transition-colors">
          <RotateCcw size={14} />
        </button>
      </div>

      <div className="p-4 space-y-6 flex-1">


        <section className="space-y-4 pt-4 border-t border-[#2A2A2A]">
          <div className="space-y-3">
            <AdjustmentSlider
              label="Temp"
              value={currentSettings.temperature}
              displayValue={`${Math.round(currentSettings.temperature)}K`}
              min={2000} max={10000} step={50}
              onChange={(v) => updateColorSetting('temperature', v)}
              icon={Thermometer} iconColor="text-orange-400"
              gradient="bg-gradient-to-r from-blue-600 via-gray-400 to-orange-400"
            />
            <AdjustmentSlider
              label="Exposure"
              value={currentSettings.exposure}
              displayValue={`${currentSettings.exposure > 0 ? '+' : ''}${currentSettings.exposure.toFixed(1)} ev`}
              min={-5} max={5} step={0.1}
              onChange={(v) => updateColorSetting('exposure', v)}
              icon={Sun} iconColor="text-yellow-400"
            />
            <AdjustmentSlider
              label="Contrast"
              value={currentSettings.contrast}
              displayValue={`${Math.round(currentSettings.contrast)}`}
              min={-100} max={100}
              onChange={(v) => updateColorSetting('contrast', v)}
              icon={ContrastIcon} iconColor="text-gray-400"
            />
            <AdjustmentSlider
              label="Sat"
              value={currentSettings.saturation}
              displayValue={`${Math.round(currentSettings.saturation)}%`}
              min={0} max={200}
              onChange={(v) => updateColorSetting('saturation', v)}
              icon={Droplets} iconColor="text-purple-400"
              gradient="bg-gradient-to-r from-gray-600 to-purple-600"
            />
            {/* New Global Filter Slider - Visual Only for now */}
            <div className="pt-2 border-t border-[#2A2A2A]/50">
              <AdjustmentSlider
                label="Filter Strength"
                value={currentSettings.filterStrength}
                displayValue={`${Math.round(currentSettings.filterStrength)}%`}
                min={0} max={100}
                onChange={(v) => updateColorSetting('filterStrength', v)}
                icon={Wand2} iconColor="text-pink-400"
                gradient="bg-gradient-to-r from-pink-900 to-pink-500"
              />
            </div>
          </div>
        </section>

        <section className="bg-white/5 rounded border border-white/10 p-3 space-y-3">
          <div className="flex items-center gap-2">
            <Wand2 size={12} className="text-blue-500" />
            <h3 className="text-[9px] font-bold text-white uppercase">AI Grades</h3>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {FILTERS.map(f => (
              <button
                key={f.name}
                onClick={() => handleFilterSelect(f.name)}
                className={`text-left p-2 rounded text-[10px] transition-all border flex items-center gap-2 ${activeFilter === f.name
                  ? 'bg-blue-600/20 border-blue-500 text-white'
                  : 'bg-[#121212] border-transparent text-gray-400 hover:text-white hover:bg-[#222]'
                  }`}
              >
                <div className={`w-3 h-3 rounded-full ${f.color} shadow-sm`} />
                {f.label}
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="p-4 bg-[#1a1a1a] border-t border-[#2A2A2A] shrink-0">
        <button className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded text-[10px] font-bold uppercase tracking-widest transition-all">
          Save Preset
        </button>
      </div>
    </div>
  );
};

export default ColorInspector;
