from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from app.services.tts import TTSService
from app.services.aligner import AlignerService
from app.services.scorer import ScorerService
from app.services.recognizer import RecognizerService
from app.services.phoneme_converter import convert_phonemes
import shutil
import os
import uuid
import json
import traceback
import sys
from app.core.config import settings
from g2p_en import G2p
from pydantic import BaseModel

class DeleteAudioRequest(BaseModel):
    audio_url: str

router = APIRouter()
aligner_service = AlignerService()
scorer_service = ScorerService()
recognizer_service = RecognizerService()

AVAILABLE_VOICES = [
    {"id": "en-US-AriaNeural", "label": "Aria (US Female)"},
    {"id": "en-US-GuyNeural", "label": "Guy (US Male)"},
    {"id": "en-US-JennyNeural", "label": "Jenny (US Female)"},
    {"id": "en-GB-SoniaNeural", "label": "Sonia (UK Female)"},
    {"id": "en-GB-RyanNeural", "label": "Ryan (UK Male)"},
    {"id": "en-AU-NatashaNeural", "label": "Natasha (AU Female)"},
    {"id": "en-AU-WilliamNeural", "label": "William (AU Male)"},
]

print("Loading G2P model...")
try:
    g2p_model = G2p()
    print("G2P model loaded.")
except Exception as e:
    print(f"Failed to initialize G2P model: {e}")
    traceback.print_exc()
    g2p_model = None

@router.get("/voices")
def get_voices():
    """Returns the list of available TTS voices."""
    return JSONResponse(AVAILABLE_VOICES)

@router.post("/audio/delete")
async def delete_audio(request: DeleteAudioRequest):
    """
    Deletes an audio file from the output directory based on its URL.
    """
    try:
        # Extract filename from URL (e.g., /static/filename.mp3)
        filename = os.path.basename(request.audio_url)
        file_path = settings.OUTPUT_DIR / filename
        
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[API] Deleted reference audio: {file_path}")
            return {"status": "deleted"}
        else:
            print(f"[API] File not found for deletion: {file_path}")
            return {"status": "not_found"}
    except Exception as e:
        print(f"[API] Error deleting audio: {e}")
        return {"status": "error", "detail": str(e)}

@router.post("/practice/init")
async def init_practice(
    text: str = Form(...),
    voice: str = Form("en-US-AriaNeural"),
    rate: str = Form("-25%"),
):
    """
    Generates reference audio and phonemes for the given text.
    """
    print(f"[API] Received init request for text: {text}, voice: {voice}, rate: {rate}")
    try:
        # 1. Generate TTS audio
        print("[API] Calling TTS Service...")
        tts_service = TTSService(voice=voice, rate=rate)
        audio_path = await tts_service.generate_audio(text)
        print(f"[API] TTS Audio generated at: {audio_path}")
        
        # 2. Generate Reference Phonemes
        print("[API] Generating phonemes...")
        global g2p_model
        if not g2p_model:
             print("[API] Initializing G2P model just in time...")
             g2p_model = G2p()
             
        phonemes_arpa = g2p_model(text)
        # Clean phonemes
        phonemes_arpa = [p for p in phonemes_arpa if p.strip() and p not in ["'", ",", ".", " ", "?", "!"]]
        print(f"[API] ARPAbet phonemes: {phonemes_arpa}")
        
        # Convert to IPA for display
        phonemes_ipa = convert_phonemes(phonemes_arpa)
        print(f"[API] IPA phonemes: {phonemes_ipa}")
        
        # Return relative path for frontend to access (we need to serve static files)
        filename = os.path.basename(audio_path)
        audio_url = f"/static/{filename}"
        
        response_data = {
            "audio_url": audio_url,
            "phonemes": phonemes_ipa,
            "phonemes_arpa": phonemes_arpa,
            "text": text
        }
        print(f"[API] Returning response: {response_data}")
        return JSONResponse(response_data)
        
    except Exception as e:
        print(f"[API] Error in init_practice: {e}")
        traceback.print_exc()
        # Explicitly print to stderr for backup
        print(traceback.format_exc(), file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/practice/score")
def score_practice(audio: UploadFile = File(...), text: str = Form(...), ref_phonemes: str = Form(...)):
    """
    Scores the user's pronunciation against the reference.
    Uses Whisper to transcribe the user's actual audio, then compares phonemes.
    """
    print(f"[API] Received score request for text: {text}")
    try:
        # 1. Save user audio
        filename = f"user_{uuid.uuid4()}.wav"
        user_audio_path = settings.INPUT_DIR / filename
        os.makedirs(settings.INPUT_DIR, exist_ok=True)
        
        print(f"[API] Saving user audio to {user_audio_path}")
        with open(user_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        # 2. Transcribe user audio with Whisper (actual speech recognition)
        print("[API] Transcribing user audio with Whisper...")
        transcribed_text = recognizer_service.transcribe(str(user_audio_path))
        print(f"[API] User said: '{transcribed_text}'")
        
        # 3. Generate phonemes from what the user actually said
        global g2p_model
        if not g2p_model:
            g2p_model = G2p()
        
        user_phonemes_arpa = g2p_model(transcribed_text)
        user_phonemes_arpa = [p for p in user_phonemes_arpa if p.strip() and p not in ["'", ",", ".", " ", "?", "!"]]
        user_phonemes_ipa = convert_phonemes(user_phonemes_arpa)
        print(f"[API] User phonemes (IPA): {user_phonemes_ipa}")
        
        # 4. Get reference phonemes (re-generate from text to ensure consistency)
        ref_phonemes_arpa = g2p_model(text)
        ref_phonemes_arpa = [p for p in ref_phonemes_arpa if p.strip() and p not in ["'", ",", ".", " ", "?", "!"]]
        ref_phonemes_ipa = convert_phonemes(ref_phonemes_arpa)
        print(f"[API] Reference phonemes (IPA): {ref_phonemes_ipa}")
            
        # 5. Compare IPA phonemes
        print("[API] Scoring comparison...")
        score_result = scorer_service.compare_phonemes(ref_phonemes_ipa, user_phonemes_ipa)
        score_result["transcribed_text"] = transcribed_text
        print(f"[API] Score: {score_result['score']}")
        
        # 6. Delete user audio immediately (Save space!)
        try:
            if os.path.exists(user_audio_path):
                os.remove(user_audio_path)
                print(f"[API] Deleted user audio: {user_audio_path}")
        except Exception as e:
            print(f"[API] Failed to delete user audio: {e}")
            
        return JSONResponse(score_result)
        
    except Exception as e:
        print(f"[API] Error in score_practice: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
