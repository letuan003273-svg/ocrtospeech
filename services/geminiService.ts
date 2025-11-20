import { GoogleGenAI, Modality } from "@google/genai";
import { VoiceName } from "../types";

// Initialize the client.
// NOTE: process.env.API_KEY is injected by the environment.
const getClient = () => new GoogleGenAI({ apiKey: process.env.API_KEY });

/**
 * Extracts text from an image or PDF using gemini-2.5-flash
 */
export const extractTextFromImage = async (
  base64Data: string,
  mimeType: string
): Promise<string> => {
  const ai = getClient();
  
  // Remove the data URL prefix if present (e.g., "data:image/png;base64,")
  const rawBase64 = base64Data.split(',')[1] || base64Data;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: {
        parts: [
          {
            inlineData: {
              mimeType: mimeType,
              data: rawBase64
            }
          },
          {
            text: "Extract all text from this document. If it is a multi-page PDF, process all pages in order. Preserve the original structure, paragraphs, and lists. Return ONLY the extracted text. Do not include markdown code blocks (```) or any introductory/concluding remarks."
          }
        ]
      }
    });

    const text = response.text;
    if (!text) {
      throw new Error("No text extracted.");
    }
    return text.trim();
  } catch (error) {
    console.error("OCR Error:", error);
    throw new Error("Failed to extract text. Ensure the file is legible and under 20MB.");
  }
};

/**
 * Generates speech from text using gemini-2.5-flash-preview-tts
 */
export const generateSpeech = async (
  text: string,
  voice: VoiceName
): Promise<string> => {
  const ai = getClient();

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-preview-tts",
      contents: [{ parts: [{ text: text }] }],
      config: {
        responseModalities: [Modality.AUDIO],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: { voiceName: voice },
          },
        },
      },
    });

    const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    
    if (!base64Audio) {
      throw new Error("No audio data received from Gemini.");
    }

    return base64Audio;
  } catch (error) {
    console.error("TTS Error:", error);
    throw new Error("Failed to generate speech.");
  }
};
