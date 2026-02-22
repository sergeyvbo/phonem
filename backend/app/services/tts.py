import edge_tts
import os
import uuid
from app.core.config import settings


class TTSService:
    DEFAULT_VOICE = "en-US-AriaNeural"
    DEFAULT_RATE = "-65%"  # 0.5x speed

    def __init__(self, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE):
        self.voice = voice
        self.rate = rate

    async def generate_audio(self, text: str) -> str:
        """
        Generates audio from text using edge-tts and saves it to a file.
        Returns the absolute path to the audio file.
        """
        print(f"[TTS] Generating audio for: '{text}' with voice '{self.voice}', rate '{self.rate}'")
        filename = f"{uuid.uuid4()}.mp3"
        output_path = settings.OUTPUT_DIR / filename

        # Ensure directory exists
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

        try:
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
            await communicate.save(str(output_path))
            print(f"[TTS] Generation complete: {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"[TTS] Error generating audio: {e}")
            raise e
