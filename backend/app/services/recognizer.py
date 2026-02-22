"""
Speech recognition service using OpenAI Whisper.
Transcribes user audio to text so we can extract actual spoken phonemes.
"""

import whisper


class RecognizerService:
    def __init__(self, model_name: str = "tiny"):
        """
        Initialize Whisper model.
        Model sizes: tiny (~75MB), base (~140MB), small (~460MB)
        'base' is a good balance of speed and accuracy for short phrases.
        """
        print(f"[Recognizer] Loading Whisper '{model_name}' model...")
        self.model = whisper.load_model(model_name)
        print(f"[Recognizer] Whisper model loaded.")

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe an audio file to text.
        Loads audio using librosa to avoid ffmpeg dependency.
        Returns the recognized text (lowercased, stripped).
        """
        import librosa
        print(f"[Recognizer] Loading audio with librosa: {audio_path}")
        # Whisper expects 16,000Hz mono audio
        audio, _ = librosa.load(audio_path, sr=16000)
        
        print(f"[Recognizer] Transcribing with Whisper...")
        result = self.model.transcribe(
            audio,
            language="en",
            fp16=False,
        )
        text = result["text"].strip()
        print(f"[Recognizer] Transcription: '{text}'")
        return text
