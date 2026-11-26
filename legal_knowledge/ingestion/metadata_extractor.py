"""
Metadata Extraction for Egyptian Legislation.

Extracts law name, number, promulgation year, publication date,
and verified legal status without inventing missing fields.
"""

import re
import hashlib
from typing import Optional, Dict, Any
from legal_knowledge.ingestion.arabic_normalizer import ArabicNormalizer


class LegalMetadataExtractor:
    """Extracts verifiable metadata from legal document headers and texts."""

    # Regex patterns for law identifiers
    # "قانون رقم 12 لسنة 2003", "القانون رقم ١٣١ لسنة ١٩٤٨"
    LAW_ID_PATTERN = re.compile(
        r"(?:قانون|القانون)\s+(?:رقم\s+)?([0-9٠-٩]+)\s+(?:لسنة|سنة|عام)\s+([0-9٠-٩]{4})",
        re.UNICODE
    )

    # General law names: "القانون المدني", "قانون العمل", "قانون العقوبات", "قانون الإجراءات الجنائية"
    NAMED_LAW_PATTERN = re.compile(
        r"(القانون\s+المدني|قانون\s+العمل|قانون\s+التجارة|قانون\s+العقوبات|قانون\s+الإجراءات\s+الجنائية|قانون\s+المرافعات(?:\s+المدنية\s+والتجارية)?|قانون\s+الإثبات)",
        re.UNICODE
    )

    # Publication date in Egyptian Official Gazette:
    # "الجريدة الرسمية - العدد ... بتاريخ DD/MM/YYYY" or "بتاريخ DD شهر YYYY"
    PUBLICATION_DATE_PATTERN = re.compile(
        r"(?:بتاريخ|نشر\s+في|الجريدة\s+الرسمية\s+بتاريخ)\s*[:\-–]?\s*([0-9٠-٩]{1,2}[\/\-–.][0-9٠-٩]{1,2}[\/\-–.][0-9٠-٩]{4}|[0-9٠-٩]{1,2}\s+[^\s\d]+\s+[0-9٠-٩]{4})",
        re.UNICODE
    )

    # Verified status detection: ONLY when explicit in official gazette note
    LEGAL_STATUS_PATTERN = re.compile(
        r"(سارٍ|ساري\s+المفعول|معدل\s+بالقانون\s+رقم\s+[0-9٠-٩]+|ملغي\s+بموجب|أُلغي\s+بالقانون)",
        re.UNICODE
    )

    @classmethod
    def extract_document_metadata(
        cls,
        text: str,
        filename: Optional[str] = None,
        source_url: Optional[str] = None,
        provided_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract document-level metadata without hallucinating missing fields.
        Marks unknown fields as null.
        """
        meta: Dict[str, Any] = {
            "law_name": None,
            "law_number": None,
            "law_year": None,
            "publication_date": None,
            "amendment_date": None,
            "legal_status": None,
            "source_url": source_url,
        }

        # Override with user-provided verified metadata if available
        if provided_metadata:
            for k, v in provided_metadata.items():
                if v is not None and k in meta:
                    meta[k] = v

        sample_header = text[:3000] if text else ""
        norm_header = ArabicNormalizer.convert_eastern_to_western_digits(sample_header)

        # 1. Extract Law Number and Year
        if not meta["law_number"] or not meta["law_year"]:
            match = cls.LAW_ID_PATTERN.search(norm_header)
            if match:
                if not meta["law_number"]:
                    meta["law_number"] = match.group(1).strip()
                if not meta["law_year"]:
                    meta["law_year"] = match.group(2).strip()

        # 2. Extract Named Law
        if not meta["law_name"]:
            named_match = cls.NAMED_LAW_PATTERN.search(sample_header)
            if named_match:
                base_name = named_match.group(1).strip()
                if meta["law_number"] and meta["law_year"]:
                    meta["law_name"] = f"{base_name} رقم {meta['law_number']} لسنة {meta['law_year']}"
                else:
                    meta["law_name"] = base_name
            elif meta["law_number"] and meta["law_year"]:
                meta["law_name"] = f"قانون رقم {meta['law_number']} لسنة {meta['law_year']}"
            elif filename:
                clean_filename = filename.rsplit(".", 1)[0].replace("_", " ")
                meta["law_name"] = clean_filename
            else:
                meta["law_name"] = "تشريع مصري غير معرّف"

        # 3. Extract Publication Date
        if not meta["publication_date"]:
            pub_match = cls.PUBLICATION_DATE_PATTERN.search(sample_header)
            if pub_match:
                raw_date = pub_match.group(1).strip()
                meta["publication_date"] = ArabicNormalizer.convert_eastern_to_western_digits(raw_date)

        # 4. Extract Legal Status (ONLY if verifiable from text)
        if not meta["legal_status"]:
            status_match = cls.LEGAL_STATUS_PATTERN.search(sample_header)
            if status_match:
                status_text = status_match.group(1).strip()
                if "سار" in status_text:
                    meta["legal_status"] = "in_force"
                elif "معدل" in status_text:
                    meta["legal_status"] = "amended"
                elif "ملغي" in status_text or "أُلغي" in status_text:
                    meta["legal_status"] = "repealed"
            # Otherwise remains None (null) as required

        return meta

    @staticmethod
    def generate_document_id(law_name: str, law_number: Optional[str], law_year: Optional[str]) -> str:
        """Generate deterministic, deduplication-safe document ID."""
        key = f"{law_name}_{law_number or ''}_{law_year or ''}"
        hashed = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        prefix = f"law_{law_number}_{law_year}" if law_number and law_year else "doc"
        return f"{prefix}_{hashed}"

    @staticmethod
    def generate_chunk_id(document_id: str, article_number: str, sub_index: int = 0) -> str:
        """Generate deterministic chunk ID to ensure safe updates and no duplicates."""
        clean_article = article_number.replace(" ", "_").replace("(", "").replace(")", "")
        return f"{document_id}_art_{clean_article}_{sub_index}"
