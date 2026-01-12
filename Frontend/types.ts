
export interface Clip {
  id: string;
  source: string;
  keep: boolean;
  reason: string;
  emotionScore?: number;
  duration?: number;
  start?: number;
  end?: number;
  colorGrading?: {
    temperature: number;
    exposure: number;
    contrast: number;
    saturation: number;
    filterStrength: number;
  };
}

export interface ViralShort {
  title: string;
  description: string;
  clipIds: string[];
}

export interface ProjectSettings {
  filterSuggestion: string;
  colorGrading?: {
    temperature: number;
    exposure: number;
    contrast: number;
    saturation: number;
    filterStrength: number;
  };
}

export interface AudioClip {
  id: string;
  source: string; // Filename
  start: number; // Timeline start time in seconds
  duration: number; // Duration in seconds
  track: number; // Track index (e.g. 2 for A2)
}

export interface VideoProject {
  name: string;
  globalSettings: ProjectSettings;
  edl: Clip[];
  bgMusic?: {
    source: string;
    volume: number;
    loop: boolean;
  };
  audioClips?: AudioClip[]; // Secondary audio clips
  audioTracks?: number[];   // Active secondary audio tracks (e.g. [2, 3])
  trackVolumes?: Record<string, number>; // Volume levels for tracks ('a1', 'a2', 'music', 'a3'...)
  viralShorts: ViralShort[];
  overlays: TextOverlay[];
}

export interface TextOverlay {
  id: string;
  content: string;
  start: number;
  duration: number;
  style: string; // 'pop', 'slide_up'
  origin: 'ai' | 'manual';
  fontSize?: number; // Percentage relative to container width (default ~4)
  positionX?: number; // Percentage 0-100 (default 50)
  positionY?: number; // Percentage 0-100 (default 50)
  textColor?: string;
  fontFamily?: string;
}
