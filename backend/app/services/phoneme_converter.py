"""
ARPAbet → IPA phoneme converter.
Maps CMU/ARPAbet symbols (used by g2p_en) to International Phonetic Alphabet.
"""

import re

ARPA_TO_IPA = {
    # Vowels
    "AA": "ɑ",
    "AE": "æ",
    "AH": "ʌ",
    "AO": "ɔ",
    "AW": "aʊ",
    "AY": "aɪ",
    "EH": "ɛ",
    "ER": "ɝ",
    "EY": "eɪ",
    "IH": "ɪ",
    "IY": "i",
    "OW": "oʊ",
    "OY": "ɔɪ",
    "UH": "ʊ",
    "UW": "u",
    # Consonants
    "B": "b",
    "CH": "tʃ",
    "D": "d",
    "DH": "ð",
    "F": "f",
    "G": "ɡ",
    "HH": "h",
    "JH": "dʒ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "ŋ",
    "P": "p",
    "R": "ɹ",
    "S": "s",
    "SH": "ʃ",
    "T": "t",
    "TH": "θ",
    "V": "v",
    "W": "w",
    "Y": "j",
    "Z": "z",
# Consonants (continued)
    "ZH": "ʒ",
}

def normalize_ipa_sequence(ipa_list: list[str]) -> list[str]:
    """
    Normalizes a list of IPA strings into a flat sequence of atomic IPA symbols.
    Handles diphthongs and affricates by splitting them into individual characters
    to ensure consistent alignment across different models.
    """
    import re
    # 1. Join everything into one string
    full_str = "".join(ipa_list)
    
    # 2. Cleanup: Remove stress marks and other non-phonemic symbols
    # ˈ (primary stress), ˌ (secondary stress), ː (length), 
    # ' (apostrophe/separator), spaces, etc.
    full_str = re.sub(r"[ˈˌː' \-.]", "", full_str)
    
    # 3. Standardize common variants
    # Sometimes models use 'g' instead of 'ɡ', etc.
    full_str = full_str.replace("g", "ɡ")
    
    # 4. Handle DIPHTHONG inconsistency: 
    # Ensure they are always treated as individual components for alignment.
    # Note: list() on a string already does this for most cases, 
    # but we want to be explicit.
    symbols = list(full_str)
    
    # Filter out empty or whitespace results
    return [s for s in symbols if s.strip()]


def arpa_to_ipa(phoneme: str) -> str:
    """
    Convert a single ARPAbet phoneme to IPA.
    Strips stress markers (0, 1, 2) before lookup.
    Returns the original phoneme if no mapping is found.
    """
    # Strip trailing stress digits (e.g. "AH0" -> "AH", "AY1" -> "AY")
    base = re.sub(r"[012]$", "", phoneme.strip())
    return ARPA_TO_IPA.get(base, phoneme)


def convert_phonemes(phonemes: list[str]) -> list[str]:
    """
    Convert a list of ARPAbet phonemes to IPA.
    Returns the list as provided by the mapping.
    """
    return [arpa_to_ipa(p) for p in phonemes]
