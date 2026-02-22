import Levenshtein

class ScorerService:
    def compare_phonemes(self, ref_phonemes: list[str], user_phonemes: list[str]) -> dict:
        """
        Compares reference phonemes with user phonemes using Levenshtein distance.
        Returns a dictionary with the score and detailed alignment ops.
        """
        # Convert lists to strings for Levenshtein (using a separator to avoid ambiguity if needed, 
        # but Levenshtein works on sequences. simple Levenshtein.ratio works on strings)
        # However, for phonemes we want sequence alignment.
        # python-Levenshtein 'ratio' works on strings. 'editops' works on sequences.
        
        # Map phonemes to single characters for easier Levenshtein if convenient, 
        # or use editops directly on the lists? 
        # 'Levenshtein.editops' supports lists in newer versions, checking...
        # If not, we map to char. identifying unique phonemes...
        
        # Fallback: simple string comparison if lists fail, but let's try sequence alignment first.
        # Actually, Levenshtein.ratio(str1, str2).
        
        # Let's try to map phonemes to private use unicode characters for accurate diffing
        # Or just use sequence matcher from difflib which is standard python
        
        import difflib
        matcher = difflib.SequenceMatcher(None, ref_phonemes, user_phonemes)
        ratio = matcher.ratio()
        
        score = int(ratio * 100)
        
        # Generate diff details
        details = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    details.append({"phoneme": ref_phonemes[i1+k], "status": "match", "user": user_phonemes[j1+k]})
            elif tag == 'replace':
                for k in range(max(i2 - i1, j2 - j1)):
                     # Simple alignment of the replacement block
                     ref_p = ref_phonemes[i1+k] if k < (i2-i1) else ""
                     user_p = user_phonemes[j1+k] if k < (j2-j1) else ""
                     details.append({"phoneme": ref_p, "status": "substitution", "user": user_p})
            elif tag == 'delete':
                for k in range(i2 - i1):
                    details.append({"phoneme": ref_phonemes[i1+k], "status": "missing", "user": ""})
            elif tag == 'insert':
                for k in range(j2 - j1):
                    # For insertions, we might not want to show them as main entries in the ref list visualization
                    # unless we want to show "extra" sounds. 
                    # For MVP, maybe just attach to previous or ignore?
                    # Let's add them with status "insertion"
                    details.append({"phoneme": "", "status": "insertion", "user": user_phonemes[j1+k]})
                    
        return {
            "score": score,
            "details": details
        }
