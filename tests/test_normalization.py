"""
Tests for Arabic Text Normalization module.
"""

from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer


def test_tashkeel_removal():
    text = "الْمَادَّةُ الْأُولَى: كُلُّ خَطَأٍ سَبَّبَ ضَرَرًا"
    cleaned = ArabicNormalizer.remove_tashkeel(text)
    assert "َ" not in cleaned
    assert "ً" not in cleaned
    assert "ّ" not in cleaned
    assert cleaned == "المادة الأولى: كل خطأ سبب ضررا"


def test_tatweel_removal():
    text = "المــــــــادة الأولـــــى"
    cleaned = ArabicNormalizer.remove_tatweel(text)
    assert "ـ" not in cleaned
    assert cleaned == "المادة الأولى"


def test_alef_normalization():
    text = "إصدار أحكام آراء ٱستئناف"
    norm = ArabicNormalizer.normalize_alef(text)
    assert norm == "اصدار احكام اراء استئناف"


def test_eastern_to_western_digits():
    text = "المادة (١٤٧) لسنة ١٩٤٨ رقم ١٢"
    norm = ArabicNormalizer.convert_eastern_to_western_digits(text)
    assert norm == "المادة (147) لسنة 1948 رقم 12"


def test_article_number_normalization():
    assert ArabicNormalizer.normalize_article_number("المادة (١)") == "1"
    assert ArabicNormalizer.normalize_article_number("مادة 147") == "147"
    assert ArabicNormalizer.normalize_article_number("المادة الأولى") == "1"
    assert ArabicNormalizer.normalize_article_number("المادة الثانية مكرر") == "2 مكرر"
    assert ArabicNormalizer.normalize_article_number("مادة (١٢) مكرر (أ)") == "12 مكرر أ"


def test_process_text_pair_preserves_original():
    raw = "المادَّةُ (١٤٧): الْعَقْدُ شَرِيعَةُ الْمُتَعَاقِدِينَ."
    original, normalized = ArabicNormalizer.process_text_pair(raw)

    # Original text must strictly preserve diacritics and letters
    assert "الْعَقْدُ" in original
    assert "شَرِيعَةُ" in original

    # Normalized text must be cleaned for search
    assert "شريعه" in normalized or "شريعة" in normalized
    assert "َ" not in normalized
