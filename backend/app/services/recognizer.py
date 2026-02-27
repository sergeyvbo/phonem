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
        
        # 1. Ensure model is in eval mode to disable dropout
        self.model.eval()
        
        self.blank_id = self.processor.tokenizer.pad_token_id
        # Build a mapping from IPA char to token ID for biasing
        self.vocab = self.processor.tokenizer.get_vocab()
        print(f"[Recognizer] Wav2Vec2 model loaded. Blank ID: {self.blank_id}")

    def transcribe(self, 
                  audio_path: str, 
                  expected_phonemes: list[str] = None, 
                  sensitivity: float = 2.0, 
                  phoneme_boost: float = 1.0,
                  temperature: float = 1.3,
                  confidence_threshold: float = 0.6,
                  beam_width: int = 10,
                  min_duration_ms: int = 30) -> list[dict]:
        """
        Transcribe audio using advanced CTC beam search alignment.
        
        Algorithmic Improvements:
        - Manual CTC beam search (torch-based, tracking frame metadata)
        - Dynamic frame duration calculation
        - Median-based robust confidence aggregation
        - Probabilistic blank suppression
        - Top-K constrained expected phoneme biasing
        """
        import torch
        import librosa
        import numpy as np
        from app.services.phoneme_converter import normalize_ipa_sequence
        from collections import defaultdict

        # 1. Load Audio
        audio, sample_rate = librosa.load(audio_path, sr=16000)
        
        # 2. Pre-processing
        rms = np.sqrt(np.mean(audio**2))
        if rms > 1e-8:
            audio = audio / rms
            
        non_silent_intervals = librosa.effects.split(audio, top_db=30)
        orig_start_idx = 0
        if len(non_silent_intervals) > 0:
            orig_start_idx = non_silent_intervals[0][0]
            end_idx = non_silent_intervals[-1][1]
            audio = audio[orig_start_idx:end_idx]

        # 3. Model Inference
        input_values = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_values
        with torch.no_grad():
            logits = self.model(input_values).logits # [1, T, V]
            
        # 4. Temperature Scaling and Log-Space correctness
        # We operate in log-space (log_softmax) for numerical stability and beam search
        log_probs = torch.log_softmax(logits / temperature, dim=-1)[0] # [T, V]
        num_frames, vocab_size = log_probs.shape
        
        # 5. Dynamic Frame Calculation
        # Computed from actual waveform length and logits count
        ms_per_frame = (len(audio) / sample_rate) / num_frames * 1000
        offset_ms = (orig_start_idx / sample_rate) * 1000

        # 6. Probabilistic Biasing & Suppression
        # We modify log_probs in-place (or on a clone)
        refined_log_probs = log_probs.clone()
        
        for t in range(num_frames):
            frame_log_probs = refined_log_probs[t]
            
            # Get current top-k for contextual modifications
            top_k_vals, top_k_indices = torch.topk(frame_log_probs, k=5)
            max_prob = torch.exp(top_k_vals[0])
            
            # --- probabilistic blank suppression ---
            if max_prob < confidence_threshold:
                # Restrict candidates to top-2 + blank if the model is uncertain
                # This prevents "searching" for sounds in noise
                mask = torch.ones(vocab_size, dtype=torch.bool, device=log_probs.device)
                mask[top_k_indices[:2]] = False
                mask[self.blank_id] = False
                frame_log_probs[mask] = -float('inf')
                # Renormalize
                refined_log_probs[t] = torch.log_softmax(frame_log_probs, dim=-1)

            # --- top-k constrained expected phoneme biasing ---
            if expected_phonemes:
                for p in expected_phonemes:
                    token_id = self.vocab.get(p)
                    if token_id is not None and token_id in top_k_indices[:3]:
                        # Only boost if it was already acoustically plausible (in top-3)
                        refined_log_probs[t][token_id] += phoneme_boost

        # 7. Lightweight CTC Beam Search
        # Implementation: Simple beam search that tracks (prefix, last_token)
        # We track frame alignments by storing segments in the beam state.
        # Beam state: { (prefix_tuple): { "log_prob_blank": -, "log_prob_non_blank": -, "segments": [] } }
        
        # Initial beam: Empty prefix
        # We store log_probs for prefixes ending in blank and non-blank separately (CTC logic)
        beam = {
            (): {
                "b": 0.0,            # log_prob ending in blank
                "nb": -float('inf'),  # log_prob ending in non-blank
                "segs": []           # list of [{"p": id, "frames": [t1, t2]}]
            }
        }
        
        for t in range(num_frames):
            new_beam = defaultdict(lambda: {"b": -float('inf'), "nb": -float('inf'), "segs": []})
            frame_lp = refined_log_probs[t]
            
            # Performance optimization: only consider top tokens for the beam
            top_vals, top_idx = torch.topk(frame_lp, k=min(20, beam_width * 2))
            
            for prefix, state in beam.items():
                # 1. Update with blank
                lp_blank = frame_lp[self.blank_id]
                existing = new_beam[prefix]
                existing["b"] = np.logaddexp(existing["b"], np.logaddexp(state["b"], state["nb"]) + lp_blank.item())
                existing["segs"] = state["segs"] # Segments don't change on blank
                
                # 2. Update with non-blanks
                for i in range(len(top_idx)):
                    char_id = top_idx[i].item()
                    if char_id == self.blank_id:
                        continue
                        
                    lp_char = top_vals[i].item()
                    new_prefix = prefix + (char_id,)
                    last_char = prefix[-1] if prefix else None
                    
                    if char_id == last_char:
                        # Case: repeated character
                        # NB probability for existing prefix (extension of same sound)
                        existing["nb"] = np.logaddexp(existing["nb"], state["nb"] + lp_char)
                        
                        # NB probability for new prefix (interrupted by blank)
                        new_state = new_beam[new_prefix]
                        new_state["nb"] = np.logaddexp(new_state["nb"], state["b"] + lp_char)
                        if not new_state["segs"]:
                            # Start new segment for the new prefix path
                            new_segs = state["segs"].copy()
                            new_segs.append({"p_id": char_id, "frames": [t]})
                            new_state["segs"] = new_segs
                        else:
                            # This is tricky in a simple beam search; we approximate by keeping the segments 
                            # from the most likely path to this prefix.
                            pass
                    else:
                        # Case: new character
                        new_state = new_beam[new_prefix]
                        new_state["nb"] = np.logaddexp(new_state["nb"], np.logaddexp(state["b"], state["nb"]) + lp_char)
                        if not new_state["segs"]:
                            new_segs = state["segs"].copy()
                            new_segs.append({"p_id": char_id, "frames": [t]})
                            new_state["segs"] = new_segs

                # Handle segment frame tracking for the 'existing' nb path (continuing current sound)
                if state["segs"] and state["nb"] > -float('inf'):
                    # We create a new list for the frames to avoid mutating other beam paths
                    new_nb_segs = []
                    for s_idx, s in enumerate(state["segs"]):
                        if s_idx == len(state["segs"]) - 1:
                            # Add frame to the last segment
                            new_nb_segs.append({"p_id": s["p_id"], "frames": s["frames"] + [t]})
                        else:
                            new_nb_segs.append(s)
                    existing["segs"] = new_nb_segs

            # Sort and Prune
            sorted_beam = sorted(new_beam.items(), key=lambda x: np.logaddexp(x[1]["b"], x[1]["nb"]), reverse=True)
            beam = dict(sorted_beam[:beam_width])

        # 8. Post-process best path
        best_prefix, best_state = list(beam.items())[0]
        
        # 9. Robust Aggregation and Temporal Metadata
        final_segments = []
        for seg in best_state["segs"]:
            p_id = seg["p_id"]
            frames = seg["frames"]
            
            # Duration check
            duration_ms = len(frames) * ms_per_frame
            if duration_ms < min_duration_ms:
                continue
            
            # Confidence aggregation from original log_probs (source of truth)
            # Use median(exp(log_prob)) for robustness
            frame_probs = [torch.exp(log_probs[f, p_id]).item() for f in frames]
            median_conf = np.median(frame_probs)
            
            # Log-confidence for statistical analysis
            log_conf = np.log(median_conf + 1e-12)
            
            # Map back to IPA string
            token = self.processor.decode([p_id])
            norm_phones = normalize_ipa_sequence([token])
            
            if norm_phones:
                final_segments.append({
                    "phoneme": norm_phones[0],
                    "start_ms": int(offset_ms + frames[0] * ms_per_frame),
                    "end_ms": int(offset_ms + (frames[-1] + 1) * ms_per_frame),
                    "confidence": float(median_conf),
                    "log_confidence": float(log_conf),
                    "num_frames": len(frames)
                })

        print(f"[Recognizer] Decoded {len(final_segments)} segments using Beam Search.")
        return final_segments
