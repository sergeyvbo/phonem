---
title: Phonem
emoji: 🗣️
colorFrom: indigo
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# Pronunciation Trainer

A full-stack application for practicing English pronunciation with real-time feedback using IPA phonemes and OpenAI Whisper.

## Features

- **Text-to-Speech (TTS)**: Generate reference audio using Microsoft Edge TTS.
- **IPA Phonemes**: Displays pronunciation guides in the International Phonetic Alphabet.
- **Accurate Scoring**: Uses **OpenAI Whisper (tiny)** to transcribe user recordings and compare them against the reference.
- **Real-time Feedback**: Color-coded phoneme display showing matches, substitutions, and insertions.
- **In-Browser WAV Encoding**: Encodes audio to standard PCM WAV in the browser for maximum compatibility.

## Tech Stack

- **Backend**: FastAPI, OpenAI Whisper, g2p_en, librosa.
- **Frontend**: React (Vite), Tailwind CSS, Lucide Icons.

## Setup Instructions

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## License

MIT
