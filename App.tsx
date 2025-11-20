import React, { useState, useRef, useCallback, useEffect } from 'react';
import { 
  Upload, 
  Image as ImageIcon, 
  FileText, 
  Play, 
  Square, 
  Volume2, 
  Loader2, 
  Wand2,
  X,
  File as FileIcon,
  Download,
  Copy,
  Check
} from 'lucide-react';
import { VoiceName, OCRState, AudioState } from './types';
import { extractTextFromImage, generateSpeech } from './services/geminiService';
import { decodeBase64, decodeAudioData, playAudioBuffer, pcmToWavBlob } from './utils/audioHelper';

// Main App Component
const App: React.FC = () => {
  // --- State ---
  const [ocrState, setOcrState] = useState<OCRState>({
    isExtracting: false,
    error: null,
    originalImage: null, // This acts as the source file data URL
    fileName: undefined
  });
  
  const [fileType, setFileType] = useState<string>(''); // To track if it's PDF or Image
  const [extractedText, setExtractedText] = useState<string>("");
  const [copied, setCopied] = useState(false);
  
  const [audioState, setAudioState] = useState<AudioState>({
    isPlaying: false,
    isLoading: false,
    error: null,
  });

  const [selectedVoice, setSelectedVoice] = useState<VoiceName>(VoiceName.Kore);

  // --- Refs ---
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const rawAudioBytesRef = useRef<Uint8Array | null>(null); // Store raw bytes for download

  // Initialize Audio Context lazily (browsers require user interaction)
  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      audioContextRef.current = new AudioContextClass({ sampleRate: 24000 });
    }
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
    return audioContextRef.current;
  }, []);

  // --- Handlers ---

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const isImage = file.type.startsWith('image/');
    const isPdf = file.type === 'application/pdf';

    if (!isImage && !isPdf) {
      setOcrState(prev => ({ ...prev, error: 'Please upload a valid image or PDF file.' }));
      return;
    }

    // Size validation: Gemini inline data limit is ~20MB.
    const MAX_SIZE_MB = 19;
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
       setOcrState(prev => ({ ...prev, error: `File size exceeds ${MAX_SIZE_MB}MB limit.` }));
       return;
    }

    // Reset previous states
    setExtractedText("");
    setAudioState({ isPlaying: false, isLoading: false, error: null });
    stopAudio();
    rawAudioBytesRef.current = null;
    setFileType(file.type);

    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64 = e.target?.result as string;
      
      setOcrState({
        isExtracting: true,
        error: null,
        originalImage: base64,
        fileName: file.name
      });

      try {
        const text = await extractTextFromImage(base64, file.type);
        setExtractedText(text);
        setOcrState(prev => ({ ...prev, isExtracting: false }));
      } catch (err) {
        setOcrState(prev => ({ 
          ...prev, 
          isExtracting: false, 
          error: err instanceof Error ? err.message : 'Failed to read text.' 
        }));
      }
    };
    reader.readAsDataURL(file);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setExtractedText(e.target.value);
  };

  const stopAudio = useCallback(() => {
    if (audioSourceRef.current) {
      try {
        audioSourceRef.current.stop();
      } catch (e) {
        // Ignore errors if already stopped
      }
      audioSourceRef.current = null;
    }
    setAudioState(prev => ({ ...prev, isPlaying: false }));
  }, []);

  const handlePlayAudio = async () => {
    if (!extractedText.trim()) return;

    // If already playing, stop it.
    if (audioState.isPlaying) {
      stopAudio();
      return;
    }

    setAudioState({ isPlaying: false, isLoading: true, error: null });

    try {
      const ctx = getAudioContext();
      
      // 1. Check if we already have the audio for the CURRENT text? 
      // For simplicity, we regenerate if user clicks play to ensure voice/text matches.
      // Optimization: In a real app, check if text/voice changed before regenerating.
      
      const base64Audio = await generateSpeech(extractedText, selectedVoice);

      // 2. Decode Base64 to raw bytes
      const audioBytes = decodeBase64(base64Audio);
      rawAudioBytesRef.current = audioBytes; // Store for download

      // 3. Decode raw PCM to AudioBuffer
      const audioBuffer = await decodeAudioData(audioBytes, ctx, 24000, 1);

      // 4. Play
      setAudioState({ isPlaying: true, isLoading: false, error: null });
      
      audioSourceRef.current = playAudioBuffer(ctx, audioBuffer, () => {
        setAudioState(prev => ({ ...prev, isPlaying: false }));
        audioSourceRef.current = null;
      });

    } catch (err) {
      setAudioState({ 
        isPlaying: false, 
        isLoading: false, 
        error: err instanceof Error ? err.message : 'Failed to generate speech.' 
      });
    }
  };

  const handleDownloadAudio = () => {
    if (!rawAudioBytesRef.current) return;
    const blob = pcmToWavBlob(rawAudioBytesRef.current, 24000, 1);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `visionvoice-${Date.now()}.wav`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyText = async () => {
    if (!extractedText) return;
    try {
      await navigator.clipboard.writeText(extractedText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text", err);
    }
  };

  const handleDownloadText = () => {
    if (!extractedText) return;
    const blob = new Blob([extractedText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extracted-text-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Clean up audio context on unmount
  useEffect(() => {
    return () => {
      stopAudio();
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [stopAudio]);

  // --- Render ---
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-10 px-4 sm:px-6 lg:px-8">
      <header className="mb-10 text-center">
        <div className="flex items-center justify-center space-x-3 mb-3">
          <div className="p-3 bg-indigo-600 rounded-xl shadow-lg">
            <Wand2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">VisionVoice</h1>
        </div>
        <p className="text-slate-500 max-w-lg mx-auto">
          Upload an image or PDF to extract text and listen to it with lifelike AI speech.
        </p>
      </header>

      <main className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Column: File Input */}
        <section className="flex flex-col space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h2 className="font-semibold text-slate-700 flex items-center">
                <ImageIcon className="w-4 h-4 mr-2 text-indigo-500" />
                Source File
              </h2>
              {ocrState.originalImage && (
                <button 
                  onClick={() => {
                     setOcrState({ isExtracting: false, error: null, originalImage: null, fileName: undefined });
                     setExtractedText("");
                     setFileType("");
                     stopAudio();
                     rawAudioBytesRef.current = null;
                  }}
                  className="text-xs text-slate-400 hover:text-red-500 transition-colors"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="p-6">
              {!ocrState.originalImage ? (
                <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-slate-300 border-dashed rounded-xl cursor-pointer bg-slate-50 hover:bg-indigo-50/30 hover:border-indigo-300 transition-all group">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <div className="p-4 bg-white rounded-full shadow-sm mb-3 group-hover:scale-110 transition-transform duration-300">
                        <Upload className="w-8 h-8 text-indigo-500" />
                    </div>
                    <p className="mb-1 text-sm text-slate-700 font-medium">Click to upload</p>
                    <p className="text-xs text-slate-400">Image (JPG, PNG) or PDF</p>
                  </div>
                  <input 
                    type="file" 
                    className="hidden" 
                    accept="image/*,application/pdf"
                    onChange={handleFileUpload}
                  />
                </label>
              ) : (
                <div className="relative rounded-xl overflow-hidden bg-slate-100 border border-slate-200 group h-80 flex items-center justify-center">
                   {fileType === 'application/pdf' ? (
                     <div className="text-center p-6 w-full px-8">
                       <FileIcon className="w-20 h-20 text-red-500 mx-auto mb-3" />
                       <p className="text-slate-700 font-medium truncate text-ellipsis">{ocrState.fileName || 'PDF Document'}</p>
                       <p className="text-xs text-slate-400 mt-1">Ready to extract text</p>
                     </div>
                   ) : (
                     <img 
                       src={ocrState.originalImage} 
                       alt="Uploaded content" 
                       className="w-full h-full object-contain mx-auto"
                     />
                   )}
                   
                   <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
                     <label className="cursor-pointer opacity-0 group-hover:opacity-100 bg-white/90 hover:bg-white text-slate-800 px-4 py-2 rounded-lg shadow-lg font-medium text-sm transition-all transform translate-y-2 group-hover:translate-y-0">
                        Change File
                        <input 
                          type="file" 
                          className="hidden" 
                          accept="image/*,application/pdf"
                          onChange={handleFileUpload}
                        />
                     </label>
                   </div>
                </div>
              )}
              
              {ocrState.error && (
                <div className="mt-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg flex items-start">
                  <X className="w-4 h-4 mr-2 mt-0.5 shrink-0" />
                  {ocrState.error}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Right Column: Text & Audio */}
        <section className="flex flex-col space-y-6 h-full">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 flex flex-col h-full min-h-[400px]">
             <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h2 className="font-semibold text-slate-700 flex items-center">
                <FileText className="w-4 h-4 mr-2 text-indigo-500" />
                Content
              </h2>
              <div className="flex items-center space-x-1">
                {extractedText && !ocrState.isExtracting && (
                  <>
                    <button 
                      onClick={handleCopyText}
                      className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                      title="Copy Text"
                    >
                      {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                    </button>
                    <button 
                      onClick={handleDownloadText}
                      className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                      title="Download Text"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <div className="h-4 w-px bg-slate-300 mx-1"></div>
                  </>
                )}
                <span className="text-xs px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full font-medium">
                  {ocrState.isExtracting ? "Scanning..." : "Editable"}
                </span>
              </div>
            </div>

            <div className="flex-grow relative p-0">
              {ocrState.isExtracting ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 z-10 backdrop-blur-sm">
                   <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mb-3" />
                   <p className="text-slate-600 font-medium animate-pulse">Analyzing content...</p>
                </div>
              ) : null}
              
              <textarea 
                className="w-full h-full p-6 resize-none focus:outline-none text-slate-700 text-lg leading-relaxed bg-transparent placeholder-slate-300"
                placeholder={ocrState.originalImage ? "Text will appear here..." : "Upload a file to start extraction..."}
                value={extractedText}
                onChange={handleTextChange}
                disabled={ocrState.isExtracting}
              />
            </div>

            {/* Audio Controls Toolbar */}
            <div className="p-4 bg-slate-50 border-t border-slate-200 rounded-b-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
               <div className="flex items-center space-x-3 w-full sm:w-auto">
                 <div className="relative">
                    <select 
                      value={selectedVoice}
                      onChange={(e) => setSelectedVoice(e.target.value as VoiceName)}
                      className="appearance-none bg-white border border-slate-300 text-slate-700 py-2 pl-3 pr-8 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-medium min-w-[120px]"
                    >
                      {Object.values(VoiceName).map(voice => (
                        <option key={voice} value={voice}>{voice}</option>
                      ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
                      <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                    </div>
                 </div>
               </div>

               <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
                 {audioState.error && (
                    <span className="text-xs text-red-500 mr-2">{audioState.error}</span>
                 )}

                 {/* Audio Download Button */}
                 {rawAudioBytesRef.current && !audioState.isLoading && !audioState.isPlaying && (
                    <button
                      onClick={handleDownloadAudio}
                      className="p-2.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-100 hover:text-indigo-600 transition-colors"
                      title="Download Audio (WAV)"
                    >
                       <Download className="w-5 h-5" />
                    </button>
                 )}
                 
                 <button
                    onClick={handlePlayAudio}
                    disabled={!extractedText.trim() || audioState.isLoading || ocrState.isExtracting}
                    className={`
                      flex items-center justify-center px-5 py-2.5 rounded-lg font-semibold text-white transition-all shadow-md
                      ${audioState.isPlaying 
                        ? 'bg-rose-500 hover:bg-rose-600 ring-rose-200' 
                        : 'bg-indigo-600 hover:bg-indigo-700 ring-indigo-200'
                      }
                      focus:ring-4 focus:outline-none
                      disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
                    `}
                 >
                    {audioState.isLoading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : audioState.isPlaying ? (
                      <>
                         <Square className="w-5 h-5 mr-2 fill-current" />
                         Stop
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-5 h-5 mr-2" />
                        Read Aloud
                      </>
                    )}
                 </button>
               </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="mt-12 text-slate-400 text-sm">
        Powered by Gemini 2.5 Flash & TTS
      </footer>
    </div>
  );
};

export default App;
