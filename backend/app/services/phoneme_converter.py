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
    "ZH": "ʒ",
}


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
    """Convert a list of ARPAbet phonemes to IPA."""
    return [arpa_to_ipa(p) for p in phonemes]
