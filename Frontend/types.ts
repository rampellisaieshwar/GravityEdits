
export interface Clip {
  id: string;
  source: string;
  keep: boolean;
  reason: string;
  emotionScore?: number;
  duration?: number;
  start?: number;
  end?: number;
  text?: string;
  colorGrading?: {
    temperature: number;
    exposure: number;
    contrast: number;
    saturation: number;
    filterStrength: number;
  };
  words?: {
    word: string;
    start: number;
    end: number;
    probability: number;
  }[];
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
    start?: number; // Timeline start time
    duration?: number; // Optional duration override
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
  // NORMALIZED COORDINATES (0.0 to 1.0)
  // This is the "Universal Coordinate" protocol:
  // - 0.0 = left/top edge
  // - 0.5 = center
  // - 1.0 = right/bottom edge
  fontSize?: number;   // % of VIDEO HEIGHT (e.g., 0.05 = 5% of height)
  positionX?: number;  // 0.0-1.0 (center of text, horizontally)
  positionY?: number;  // 0.0-1.0 (center of text, vertically)
  textColor?: string;
  fontFamily?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}
