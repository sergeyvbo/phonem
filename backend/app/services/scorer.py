import Levenshtein

class ScorerService:
    def compare_phonemes(self, ref_phonemes: list[str], user_segments: list[dict]) -> dict:
        """
        Compares reference phonemes with user phoneme segments.
        
        :param ref_phonemes: Flat list of IPA phonemes (from reference).
        :param user_segments: List of segments from RecognizerService.
        """
        import difflib
        
        # Extract phoneme characters from segments for alignment
        user_phonemes = [s["phoneme"] for s in user_segments]
        
        matcher = difflib.SequenceMatcher(None, ref_phonemes, user_phonemes)
        ratio = matcher.ratio()
        
        score = int(ratio * 100)
        
        # Generate diff details
        details = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    seg = user_segments[j1+k]
                    details.append({
                        "phoneme": ref_phonemes[i1+k], 
                        "status": "match", 
                        "user": seg["phoneme"],
                        "confidence": seg["confidence"],
                        "start_ms": seg["start_ms"],
                        "end_ms": seg["end_ms"]
                    })
            elif tag == 'replace':
                for k in range(max(i2 - i1, j2 - j1)):
                    ref_p = ref_phonemes[i1+k] if k < (i2-i1) else ""
                    
                    if k < (j2-j1):
                        seg = user_segments[j1+k]
                        details.append({
                            "phoneme": ref_p, 
                            "status": "substitution", 
                            "user": seg["phoneme"],
                            "confidence": seg["confidence"],
                            "start_ms": seg["start_ms"],
                            "end_ms": seg["end_ms"]
                        })
                    else:
                        details.append({"phoneme": ref_p, "status": "substitution", "user": ""})
                        
            elif tag == 'delete':
                for k in range(i2 - i1):
                    details.append({"phoneme": ref_phonemes[i1+k], "status": "missing", "user": ""})
            elif tag == 'insert':
                for k in range(j2 - j1):
                    seg = user_segments[j1+k]
                    details.append({
                        "phoneme": "", 
                        "status": "insertion", 
                        "user": seg["phoneme"],
                        "confidence": seg["confidence"],
                        "start_ms": seg["start_ms"],
                        "end_ms": seg["end_ms"]
                    })
                    
        return {
            "score": score,
            "details": details
        }
