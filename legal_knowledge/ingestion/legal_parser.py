"""
Legal Structure Parser for Egyptian Legislation.

Detects legislative hierarchies:
- الديباجة (Preamble)
- الكتاب (Book)
- الباب (Part / Title)
- الفصل (Chapter)
- الفرع / المبحث (Section / Topic)
- المادة (Article: e.g. 'مادة 1', 'المادة (١) مكرر', 'المادة الأولى')
"""

import re
from typing import NamedTuple, Optional
import logging
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer

logger = logging.getLogger(__name__)


class ParsedArticle(NamedTuple):
    article_number: str
    original_text: str
    chapter: Optional[str]
    section: Optional[str]
    book: Optional[str]
    title: Optional[str]


class LegalStructureParser:
    """Parses Egyptian legal documents into hierarchical structural elements."""

    # Regex patterns for structural headers
    # Matches: "الكتاب الأول", "كتاب أول", etc.
    BOOK_PATTERN = re.compile(
        r"^(الكتاب\s+[\u0621-\u064A0-9\(\)]+(?:\s*[:\-–]\s*.*)?)$",
        re.MULTILINE
    )

    # Matches: "الباب الأول", "باب أول", "الباب الثاني: في الالتزامات", etc.
    CHAPTER_DOOR_PATTERN = re.compile(
        r"^(الباب\s+[\u0621-\u064A0-9\(\)]+(?:\s*[:\-–]\s*.*)?)$",
        re.MULTILINE
    )

    # Matches: "الفصل الأول", "فصل أول", "الفصل الثاني: ...", etc.
    SECTION_CHAPTER_PATTERN = re.compile(
        r"^(الفصل\s+[\u0621-\u064A0-9\(\)]+(?:\s*[:\-–]\s*.*)?)$",
        re.MULTILINE
    )

    # Matches: "الفرع الأول", "المبحث الأول", etc.
    SUBSECTION_PATTERN = re.compile(
        r"^((?:الفرع|المبحث)\s+[\u0621-\u064A0-9\(\)]+(?:\s*[:\-–]\s*.*)?)$",
        re.MULTILINE
    )

    # Matches Article declarations:
    # "مادة 1 -", "المادة (١) مكرر :", "مادة 147:", "المادة الأولى :", "مادة رقم (١٢)"
    ARTICLE_START_PATTERN = re.compile(
        r"(?:^|\n)\s*(مادة|المادة)\s+(?:رقم\s+)?(\([0-9٠-٩\s]+\)|[0-9٠-٩]+|[أ-ي\s]+?)(?:\s+(مكرر(?:\s+[أ-ي\d])?))?\s*[:\-–.\n]\s*",
        re.MULTILINE
    )

    @classmethod
    def parse_articles(cls, text: str) -> list[ParsedArticle]:
        """
        Parses full legal text into distinct structured articles, tracking
        hierarchical context (Book, Chapter, Section).
        """
        if not text or not text.strip():
            return []

        # Track active hierarchy
        current_book: Optional[str] = None
        current_chapter: Optional[str] = None
        current_section: Optional[str] = None

        # Clean text preserving line breaks
        cleaned_text = ArabicNormalizer.clean_original_text(text)

        # Split or scan through lines to capture hierarchy markers and articles
        articles: list[ParsedArticle] = []

        # Find all article start positions
        matches = list(cls.ARTICLE_START_PATTERN.finditer(cleaned_text))

        if not matches:
            # Fallback if text doesn't strictly match formal article headers
            logger.warning("No standard article markers found; attempting line-by-line fallback.")
            return cls._fallback_line_parser(cleaned_text)

        # If there is preamble text before the first article
        first_article_start = matches[0].start()
        if first_article_start > 0:
            preamble_text = cleaned_text[:first_article_start].strip()
            if preamble_text:
                articles.append(
                    ParsedArticle(
                        article_number="ديباجة",
                        original_text=preamble_text,
                        chapter="ديباجة",
                        section=None,
                        book=None,
                        title="ديباجة القانون ومذكرته الإيضاحية"
                    )
                )

        # Iterate over article matches
        for idx, match in enumerate(matches):
            raw_prefix = match.group(0)
            raw_num_part = match.group(2)
            raw_suffix = match.group(3) or ""

            article_num_str = f"{raw_num_part} {raw_suffix}".strip()
            normalized_article_num = ArabicNormalizer.normalize_article_number(article_num_str)

            # Determine article text slice
            start_pos = match.start()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned_text)

            article_block = cleaned_text[start_pos:end_pos].strip()

            # Inspect preceding text between previous article and this one to update hierarchy
            if idx > 0:
                prev_end = matches[idx - 1].end()
                between_text = cleaned_text[prev_end:start_pos]
                new_book, new_chap, new_sec = cls._extract_hierarchy_from_segment(between_text)
                if new_book:
                    current_book = new_book
                if new_chap:
                    current_chapter = new_chap
                if new_sec:
                    current_section = new_sec
            else:
                # Preceding first match
                pre_text = cleaned_text[:start_pos]
                new_book, new_chap, new_sec = cls._extract_hierarchy_from_segment(pre_text)
                if new_book:
                    current_book = new_book
                if new_chap:
                    current_chapter = new_chap
                if new_sec:
                    current_section = new_sec

            # Strip the article header from the beginning of block to keep cleanly,
            # or keep full block so original text contains the exact "مادة X" statement.
            # Keeping full block ensures verbatim legal authenticity!
            articles.append(
                ParsedArticle(
                    article_number=normalized_article_num,
                    original_text=article_block,
                    chapter=current_chapter,
                    section=current_section,
                    book=current_book,
                    title=f"مادة {normalized_article_num}"
                )
            )

        return articles

    @classmethod
    def _extract_hierarchy_from_segment(cls, segment: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract Book, Chapter, Section from interstitial text."""
        book, chapter, section = None, None, None
        for line in segment.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            if cls.BOOK_PATTERN.match(line_str):
                book = line_str
            elif cls.CHAPTER_DOOR_PATTERN.match(line_str):
                chapter = line_str
            elif cls.SECTION_CHAPTER_PATTERN.match(line_str) or cls.SUBSECTION_PATTERN.match(line_str):
                section = line_str
        return book, chapter, section

    @classmethod
    def _fallback_line_parser(cls, text: str) -> list[ParsedArticle]:
        """Fallback when no formal article markers match."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        fallback_articles = []
        for i, p in enumerate(paragraphs, start=1):
            fallback_articles.append(
                ParsedArticle(
                    article_number=str(i),
                    original_text=p,
                    chapter=None,
                    section=None,
                    book=None,
                    title=f"فقرة {i}"
                )
            )
        return fallback_articles
