from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from app.services.tts import TTSService
from app.services.aligner import AlignerService
from app.services.scorer import ScorerService
from app.services.recognizer import RecognizerService
from app.services.phoneme_converter import convert_phonemes, normalize_ipa_sequence
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

# Global instances for lazy loading
_aligner_service = None
_scorer_service = None
_recognizer_service = None
_g2p_model = None

def get_aligner():
    global _aligner_service
    if _aligner_service is None:
        _aligner_service = AlignerService()
    return _aligner_service

def get_scorer():
    global _scorer_service
    if _scorer_service is None:
        _scorer_service = ScorerService()
    return _scorer_service

def get_recognizer():
    global _recognizer_service
    if _recognizer_service is None:
        try:
            _recognizer_service = RecognizerService()
        except Exception as e:
            print(f"[API] ERROR: Failed to load Allosaurus: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Failed to load recognition engine")
    return _recognizer_service

def get_g2p():
    global _g2p_model
    if _g2p_model is None:
        from g2p_en import G2p
        print("[API] Loading G2P model...")
        _g2p_model = G2p()
        print("[API] G2P model loaded.")
    return _g2p_model

AVAILABLE_VOICES = [
    {"id": "en-US-AriaNeural", "label": "Aria (US Female)"},
    {"id": "en-US-GuyNeural", "label": "Guy (US Male)"},
    {"id": "en-US-JennyNeural", "label": "Jenny (US Female)"},
    {"id": "en-GB-SoniaNeural", "label": "Sonia (UK Female)"},
    {"id": "en-GB-RyanNeural", "label": "Ryan (UK Male)"},
    {"id": "en-AU-NatashaNeural", "label": "Natasha (AU Female)"},
    {"id": "en-AU-WilliamNeural", "label": "William (AU Male)"},
]

# Removed global g2p loading from module level

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
        g2p = get_g2p()
        phonemes_arpa = g2p(text)
        # Clean phonemes
        phonemes_arpa = [p for p in phonemes_arpa if p.strip() and p not in ["'", ",", ".", " ", "?", "!"]]
        print(f"[API] ARPAbet phonemes: {phonemes_arpa}")
        
        # Convert to IPA for display
        phonemes_ipa_list = convert_phonemes(phonemes_arpa)
        
        # Flatten and clean IPA symbols using centralized normalizer
        phonemes_ipa = normalize_ipa_sequence(phonemes_ipa_list)
        
        print(f"[API] IPA phonemes (flattened): {phonemes_ipa}")
        
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
            
        # 2. Recognize phones with Allosaurus (direct phonetic recognition)
        print("[API] Recognizing phones with Allosaurus...")
        recognizer = get_recognizer()
        user_phonemes_ipa = recognizer.transcribe(str(user_audio_path))
        print(f"[API] User sounds: {user_phonemes_ipa}")
        
        # 3. Get reference phonemes (re-generate from text to ensure consistency)
        g2p = get_g2p()
        ref_phonemes_arpa = g2p(text)
        ref_phonemes_arpa = [p for p in ref_phonemes_arpa if p.strip() and p not in ["'", ",", ".", " ", "?", "!"]]
        ref_phonemes_ipa_list = convert_phonemes(ref_phonemes_arpa)
        
        # Consistent flattening for scoring using centralized normalizer
        ref_phonemes_ipa = normalize_ipa_sequence(ref_phonemes_ipa_list)
        
        print(f"[API] Reference phonemes (IPA flattened): {ref_phonemes_ipa}")
            
        # 4. Compare IPA phonemes
        print("[API] Scoring comparison...")
        scorer = get_scorer()
        score_result = scorer.compare_phonemes(ref_phonemes_ipa, user_phonemes_ipa)
        
        # We'll use the 'transcribed_text' field to show the recognized sounds to the user
        # Since user_phonemes_ipa is now a flat list of characters, we might want to space them out 
        # but the logic for 'transcribed_text' should probably stay readable.
        score_result["transcribed_text"] = "/ " + "".join(user_phonemes_ipa) + " /"
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
