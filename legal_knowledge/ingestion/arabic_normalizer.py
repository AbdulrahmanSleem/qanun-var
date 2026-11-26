"""
Arabic Legal Text Normalization Module.

Handles diacritics, tatweel, letter variants, digit conversion, punctuation,
and legal phrasing variants while strictly preserving the authentic original text.
"""

import re
from typing import Tuple


# Arabic Unicode Ranges
TASHKEEL_REGEX = re.compile(r"[\u064B-\u0652\u0670\u0653\u0654\u0655\u0656\u0657\u0658\u065C\u065D\u065E\u065F]")
TATWEEL_REGEX = re.compile(r"\u0640")
EXTRA_WHITESPACE_REGEX = re.compile(r"[\s\u200B-\u200D\uFEFF]+")
PUNCTUATION_REGEX = re.compile(r"[«»“”\"\'\(\)\[\]\{\}\.,،؛:؟!؟\-_/\\#@\*\+=~]")

# Digit mappings
EASTERN_TO_WESTERN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
WESTERN_TO_EASTERN_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

# Arabic written ordinal number mapping for legal articles (e.g. المادة الأولى -> 1)
ARABIC_ORDINALS_MAP = {
    "الاولى": "1",
    "الأولى": "1",
    "الاول": "1",
    "الأول": "1",
    "الثانية": "2",
    "الثاني": "2",
    "الثالثة": "3",
    "الثالث": "3",
    "الرابعة": "4",
    "الرابع": "4",
    "الخامسة": "5",
    "الخامس": "5",
    "السادسة": "6",
    "السادس": "6",
    "السابعة": "7",
    "السابع": "7",
    "الثامنة": "8",
    "الثامن": "8",
    "التاسعة": "9",
    "التاسع": "9",
    "العاشرة": "10",
    "العاشر": "10",
    "الحادية عشرة": "11",
    "الحادي عشر": "11",
    "الثانية عشرة": "12",
    "الثاني عشر": "12",
}


class ArabicNormalizer:
    """Production-grade Arabic text normalizer specialized for legal text."""

    @staticmethod
    def remove_tashkeel(text: str) -> str:
        """Strip all Arabic diacritics (harakat / tashkeel)."""
        if not text:
            return ""
        return TASHKEEL_REGEX.sub("", text)

    @staticmethod
    def remove_tatweel(text: str) -> str:
        """Strip Arabic elongation character (kashida)."""
        if not text:
            return ""
        return TATWEEL_REGEX.sub("", text)

    @staticmethod
    def normalize_alef(text: str) -> str:
        """Normalize different forms of Alef (أ, إ, آ, ٱ) into a bare Alef (ا)."""
        if not text:
            return ""
        text = re.sub(r"[إأآٱ]", "ا", text)
        return text

    @staticmethod
    def normalize_yaa_and_taa(text: str, search_mode: bool = True) -> str:
        """
        Normalize Yaa/Alef Maqsura (ى -> ي) and optionally Taa Marbuta (ة -> ه).
        In search mode, standardizes both to improve recall across spelling variants.
        """
        if not text:
            return ""
        text = re.sub(r"ى\b", "ي", text)
        text = text.replace("ى", "ي")
        if search_mode:
            text = text.replace("ة", "ه")
        return text

    @staticmethod
    def convert_eastern_to_western_digits(text: str) -> str:
        """Convert Eastern Arabic numerals (٠-٩) to standard Western digits (0-9)."""
        if not text:
            return ""
        return text.translate(EASTERN_TO_WESTERN_DIGITS)

    @staticmethod
    def convert_western_to_eastern_digits(text: str) -> str:
        """Convert standard Western digits (0-9) to Eastern Arabic numerals (٠-٩)."""
        if not text:
            return ""
        return text.translate(WESTERN_TO_EASTERN_DIGITS)

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Collapse redundant whitespaces, newlines, and strip zero-width spaces."""
        if not text:
            return ""
        return EXTRA_WHITESPACE_REGEX.sub(" ", text).strip()

    @staticmethod
    def normalize_legal_terms(text: str) -> str:
        """
        Standardize common Egyptian legal phrasing variations.
        e.g., 'القانون رقم' vs 'قانون رقم', 'المادة' vs 'مادة'.
        """
        if not text:
            return ""
        # Normalize article prefixes
        text = re.sub(r"\bالمادة\b", "مادة", text)
        # Normalize law prefixes
        text = re.sub(r"\bالقانون\b", "قانون", text)
        # Normalize year indicators
        text = re.sub(r"\bلسنه\b", "سنة", text)
        text = re.sub(r"\bلسنة\b", "سنة", text)
        text = re.sub(r"\bعام\b", "سنة", text)
        return text

    @staticmethod
    def normalize_hamza(text: str) -> str:
        """
        Normalize hamza variants (ؤ, ئ, ء) so that alternative orthographies
        like 'مسؤولية' and 'مسئولية' match identically during search.
        """
        if not text:
            return ""
        text = text.replace("ئ", "ء").replace("ؤ", "ء")
        return text

    @classmethod
    def normalize_for_search(cls, text: str) -> str:
        """
        Full search normalization pipeline:
        1. Remove diacritics (tashkeel).
        2. Remove elongation (tatweel).
        3. Convert eastern numbers to western.
        4. Normalize Alef variants.
        5. Normalize Yaa and Taa Marbuta.
        6. Normalize Hamza variants.
        7. Clean punctuation and whitespace.
        8. Normalize legal terms.
        
        NOTE: Used ONLY for indexing and search matching.
        """
        if not text:
            return ""
        text = cls.remove_tashkeel(text)
        text = cls.remove_tatweel(text)
        text = cls.convert_eastern_to_western_digits(text)
        text = cls.normalize_alef(text)
        text = cls.normalize_hamza(text)
        text = cls.normalize_yaa_and_taa(text, search_mode=True)
        text = cls.normalize_legal_terms(text)
        text = PUNCTUATION_REGEX.sub(" ", text)
        text = cls.clean_whitespace(text)
        return text.lower()

    @classmethod
    def clean_original_text(cls, text: str) -> str:
        """
        Light cleanup for the authentic original text:
        preserves exact letters, words, and structure, but cleans corrupted OCR artifacts,
        redundant line breaks, and trailing spaces.
        """
        if not text:
            return ""
        # Remove zero-width formatting artifacts
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
        # Normalize consecutive spaces but preserve structural paragraph breaks
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join(line for line in lines if line)
        return cleaned.strip()

    @classmethod
    def process_text_pair(cls, text: str) -> Tuple[str, str]:
        """
        Returns a pair: (text_original, text_normalized)
        ensuring strict compliance with requirement:
        'Never use aggressively normalized text as the official legal quotation.'
        """
        original = cls.clean_original_text(text)
        normalized = cls.normalize_for_search(original)
        return original, normalized

    @classmethod
    def normalize_article_number(cls, raw_article: str) -> str:
        """
        Extract and normalize an article number identifier.
        e.g., 'المادة (١) مكرر' -> '1 مكرر', 'المادة الأولى' -> '1'.
        """
        if not raw_article:
            return ""
        cleaned = cls.remove_tashkeel(raw_article)
        cleaned = cls.remove_tatweel(cleaned)
        cleaned = cls.convert_eastern_to_western_digits(cleaned)
        cleaned = re.sub(r"[\(\)\[\]\{\}\.:\-]", " ", cleaned)
        cleaned = cls.clean_whitespace(cleaned)

        # Check for written ordinals
        for ordinal, digit in ARABIC_ORDINALS_MAP.items():
            if ordinal in cleaned:
                suffix = " مكرر" if "مكرر" in cleaned else ""
                return f"{digit}{suffix}"

        # Extract digits and suffixes like 'مكرر' or 'أ'
        match = re.search(r"(\d+)\s*(مكرر(?:\s+[أ-ي\d])?|[أ-ي])?", cleaned)
        if match:
            num = match.group(1)
            suffix = f" {match.group(2)}" if match.group(2) else ""
            return f"{num}{suffix}".strip()

        return cleaned
