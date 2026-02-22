import React, { useState, useEffect, useRef } from 'react';
import { initPractice, scorePractice, getVoices } from './api';
import AudioRecorder from './components/AudioRecorder';
import PhonemeDisplay from './components/PhonemeDisplay';
import { Play, Square, RotateCcw, RefreshCcw } from 'lucide-react';

function App() {
  const [text, setText] = useState("Hello world");
  const [screen, setScreen] = useState('input'); // input, practice, result
  const [audioUrl, setAudioUrl] = useState(null);
  const [refPhonemes, setRefPhonemes] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('en-US-AriaNeural');
  const [speed, setSpeed] = useState(75); // percentage: 75 means 0.75x
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    getVoices().then(setVoices).catch(() => {});
  }, []);

  // Convert speed slider value (e.g. 75) to edge-tts rate string (e.g. "-25%")
  const speedToRate = (s) => {
    const delta = s - 100;
    return delta >= 0 ? `+${delta}%` : `${delta}%`;
  };

  const handleInit = async () => {
    // Stop any playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
    setLoading(true);
    try {
      const data = await initPractice(text, selectedVoice, speedToRate(speed));
      setAudioUrl(`http://localhost:8000${data.audio_url}`);
      setRefPhonemes(data.phonemes);
      setScreen('practice');
    } catch (err) {
      alert("Failed to initialize practice");
    } finally {
      setLoading(false);
    }
  };

  const handleRecordingComplete = async (blob) => {
    setLoading(true);
    try {
      const data = await scorePractice(blob, text, refPhonemes);
      setResult(data);
      setScreen('result');
    } catch (err) {
      alert("Failed to score practice");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
    setScreen('input');
    setResult(null);
    setAudioUrl(null);
    setRefPhonemes([]);
  };

  const handleRetry = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
    setResult(null);
    setScreen('practice');
  };

  const toggleReferenceAudio = () => {
    if (isPlaying) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    } else {
      if (!audioRef.current || audioRef.current.src !== audioUrl) {
        audioRef.current = new Audio(audioUrl);
        audioRef.current.onended = () => setIsPlaying(false);
      }
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4 font-sans">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6 text-center text-indigo-600">Pronunciation Trainer</h1>

        {screen === 'input' && (
          <div className="flex flex-col gap-4">
            <label className="text-gray-700 font-medium">Enter text to practice:</label>
            <textarea
              className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none resize-none bg-gray-50"
              rows={3}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type something..."
            />

            {/* Voice selector */}
            <div>
              <label className="text-sm text-gray-600 mb-1 block">Voice</label>
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="w-full p-2.5 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-indigo-500 outline-none text-gray-700"
              >
                {voices.map((v) => (
                  <option key={v.id} value={v.id}>{v.label}</option>
                ))}
              </select>
            </div>

            {/* Speed slider */}
            <div>
              <label className="text-sm text-gray-600 mb-1 block">
                Speed: <span className="font-semibold text-indigo-600">{(speed / 100).toFixed(2)}x</span>
              </label>
              <input
                type="range"
                min={25}
                max={200}
                step={5}
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
                className="w-full accent-indigo-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                <span>0.25x</span>
                <span>1.0x</span>
                <span>2.0x</span>
              </div>
            </div>

            <button
              onClick={handleInit}
              disabled={loading}
              className="w-full py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {loading ? "Generating..." : "Start Practice"}
            </button>
          </div>
        )}

        {screen === 'practice' && (
          <div className="flex flex-col items-center gap-6">
            <p className="text-xl font-medium text-center text-gray-800">"{text}"</p>
            
            {audioUrl && (
              <button 
                onClick={toggleReferenceAudio}
                className={`flex items-center gap-2 px-4 py-2 rounded-full transition ${
                  isPlaying 
                    ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                    : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                }`}
              >
                {isPlaying ? (
                  <>
                    <Square size={20} fill="currentColor" />
                    Stop Listening
                  </>
                ) : (
                  <>
                    <Play size={20} fill="currentColor" />
                    Listen to Reference
                  </>
                )}
              </button>
            )}

            <div className="w-full border-t border-gray-200 my-2"></div>

            <p className="text-sm text-gray-500">Record your pronunciation:</p>
            <AudioRecorder onRecordingComplete={handleRecordingComplete} />
            
            {loading && <p className="text-sm text-indigo-600 animate-pulse">Analyzing...</p>}
            
             <button
              onClick={() => setScreen('input')}
              className="text-sm text-gray-400 hover:text-gray-600 underline mt-4"
            >
              Cancel
            </button>
          </div>
        )}

        {screen === 'result' && result && (
          <div className="flex flex-col items-center gap-6">
            <div className="text-center">
              <span className="text-gray-500 uppercase text-xs tracking-wider">Score</span>
              <div className="text-5xl font-bold text-indigo-600">{result.score}%</div>
            </div>

            <div className="w-full flex flex-col gap-3">
              <div className="text-center w-full px-4 py-3 bg-indigo-50 rounded-lg border border-indigo-100">
                <span className="text-xs text-indigo-400 uppercase tracking-wider font-semibold">Expected</span>
                <p className="text-lg text-indigo-900 font-medium">"{text}"</p>
              </div>

              {result.transcribed_text && (
                <div className="text-center w-full px-4 py-3 bg-gray-50 rounded-lg border border-gray-100">
                  <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold">We heard</span>
                  <p className="text-lg text-gray-700 font-medium">"{result.transcribed_text}"</p>
                </div>
              )}
            </div>

            <PhonemeDisplay diffs={result.details} />

            <div className="flex gap-3 mt-4">
              <button
                onClick={handleRetry}
                className="flex items-center gap-2 px-6 py-3 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition"
              >
                <RefreshCcw size={20} />
                Retry
              </button>
              
              <button
                onClick={reset}
                className="flex items-center gap-2 px-6 py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition"
              >
                <RotateCcw size={20} />
                Try Another
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
