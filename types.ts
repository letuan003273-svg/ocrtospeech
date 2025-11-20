export enum VoiceName {
  Kore = 'Kore',
  Puck = 'Puck',
  Charon = 'Charon',
  Fenrir = 'Fenrir',
  Zephyr = 'Zephyr',
}

export interface ExtractedContent {
  text: string;
  confidence?: number;
}

export interface AudioState {
  isPlaying: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface OCRState {
  isExtracting: boolean;
  error: string | null;
  originalImage: string | null; // Base64
  fileName?: string;
}
