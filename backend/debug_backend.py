import os
import traceback

def test_tts():
    print("Testing TTS...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        output_path = "test_tts.wav"
        engine.save_to_file("Hello world", output_path)
        engine.runAndWait()
        print(f"TTS Success: {output_path} created.")
    except Exception:
        traceback.print_exc()

def test_g2p():
    print("Testing G2P...")
    try:
        from g2p_en import G2p
        g2p = G2p()
        phonemes = g2p("Hello world")
        print(f"G2P Success: {phonemes}")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    test_tts()
    test_g2p()
