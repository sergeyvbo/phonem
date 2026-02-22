import axios from 'axios';

const rawEnvUrl = import.meta.env.VITE_API_URL;
console.log('[DEBUG] VITE_API_URL from environment:', rawEnvUrl);

const API_BASE_URL = rawEnvUrl ? rawEnvUrl.replace(/\/api$/, '') : 'http://localhost:8000';
const API_URL = `${API_BASE_URL}/api`;

console.log('[DEBUG] Resolved API_BASE_URL:', API_BASE_URL);
console.log('[DEBUG] Resolved API_URL:', API_URL);

export { API_BASE_URL };

export const getVoices = async () => {
    const response = await axios.get(`${API_URL}/voices`);
    return response.data;
};

export const initPractice = async (text, voice, rate) => {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('voice', voice);
    formData.append('rate', rate);
    try {
        const response = await axios.post(`${API_URL}/practice/init`, formData);
        return response.data;
    } catch (error) {
        console.error("Error initializing practice:", error);
        throw error;
    }
};

export const scorePractice = async (audioBlob, text, refPhonemes) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    formData.append('text', text);
    formData.append('ref_phonemes', JSON.stringify(refPhonemes)); // Send as JSON string

    try {
        const response = await axios.post(`${API_URL}/practice/score`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error("Error scoring practice:", error);
        throw error;
    }
};

export const deleteAudio = async (audioUrl) => {
    try {
        await axios.post(`${API_URL}/audio/delete`, { audio_url: audioUrl });
    } catch (error) {
        console.error("Error deleting audio:", error);
    }
};
