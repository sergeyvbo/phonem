"""
Phonetic recognition service using Wav2Vec2 (Transformer).
Transcribes user audio directly into phonetic sounds (IPA).
More robust than Allosaurus for noisy environments.
"""

class RecognizerService:
    def __init__(self, model_name: str = "speech31/wav2vec2-large-english-phoneme-v2"):
        """
        Initialize Wav2Vec2 recognizer.
        Optimized for English IPA phoneme recognition.
        """
        print(f"[Recognizer] Initializing Wav2Vec2 with model: {model_name}")
        from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
        print(f"[Recognizer] Wav2Vec2 model loaded.")

    def transcribe(self, audio_path: str) -> list[str]:
        """
        Transcribe an audio file directly to IPA phonemes.
        Returns a flat list of IPA characters for robust alignment.
        """
        import torch
        import librosa
        from app.services.phoneme_converter import normalize_ipa_sequence
        
        print(f"[Recognizer] Recognizing phones in: {audio_path}")
        
        # 1. Load audio (Wav2Vec2 expects 16kHz)
        audio, _ = librosa.load(audio_path, sr=16000)
        
        # 2. Process audio
        input_values = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_values
        
        # 3. Inference
        with torch.no_grad():
            logits = self.model(input_values).logits
        
        # 4. Decode
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        print(f"[Recognizer] Raw transcription: '{transcription}'")
        
        # 5. Clean and Flatten to individual IPA units using centralized normalizer
        phones = normalize_ipa_sequence([transcription])
        
        print(f"[Recognizer] Flattened phones: {phones}")
        return phones
