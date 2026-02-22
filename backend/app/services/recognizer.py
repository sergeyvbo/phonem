"""
Phonetic recognition service using Allosaurus.
Transcribes user audio directly into phonetic sounds (phones/phonemes).
"""

from allosaurus.app import read_recognizer


class RecognizerService:
    def __init__(self, model_name: str = "eng2102"):
        """
        Initialize Allosaurus recognizer.
        Default model 'eng2102' is optimized for English.
        """
        print(f"[Recognizer] Loading Allosaurus '{model_name}' model...")
        self.model = read_recognizer(model_name)
        print(f"[Recognizer] Allosaurus model loaded.")

    def transcribe(self, audio_path: str) -> list[str]:
        """
        Transcribe an audio file directly to phonemes.
        Returns a list of IPA phonemes.
        """
        print(f"[Recognizer] Recognizing phones in: {audio_path}")
        
        # recognize returns phones separated by spaces
        # e.g., "h e l o u"
        phones_str = self.model.recognize(audio_path)
        
        # Clean up and convert to list
        # Allosaurus uses its own internal phone set which is close to IPA
        phones = phones_str.strip().split()
        
        print(f"[Recognizer] Recognized phones: {phones}")
        return phones
