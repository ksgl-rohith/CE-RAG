import re
from typing import List, Dict, Any

# Section header regex mappings for standard FDA SPL labels
SECTION_PATTERNS = {
    "indications": re.compile(r"^\s*(?:\d+\s+)?(?:INDICATIONS\s+(?:AND|&)\s+USAGE|INDICATIONS)\s*$", re.IGNORECASE),
    "dosage": re.compile(r"^\s*(?:\d+\s+)?(?:DOSAGE\s+(?:AND|&)\s+ADMINISTRATION|DOSAGE)\s*$", re.IGNORECASE),
    "contraindications": re.compile(r"^\s*(?:\d+\s+)?(?:CONTRAINDICATIONS)\s*$", re.IGNORECASE),
    "warnings": re.compile(r"^\s*(?:\d+\s+)?(?:WARNINGS\s+(?:AND|&)\s+PRECAUTIONS|WARNINGS)\s*$", re.IGNORECASE),
    "side_effects": re.compile(r"^\s*(?:\d+\s+)?(?:ADVERSE\s+REACTIONS|ADVERSE\s+EFFECTS|SIDE\s+EFFECTS)\s*$", re.IGNORECASE),
    "interactions": re.compile(r"^\s*(?:\d+\s+)?(?:DRUG\s+INTERACTIONS)\s*$", re.IGNORECASE),
    "specific_populations": re.compile(r"^\s*(?:\d+\s+)?(?:USE\s+IN\s+SPECIFIC\s+POPULATIONS)\s*$", re.IGNORECASE)
}

class SectionChunker:
    @staticmethod
    def split_text_by_length(text: str, max_chars: int = 1200, overlap: int = 200) -> List[str]:
        """Splits a single block of text into overlapping sub-chunks."""
        if len(text) <= max_chars:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            chunks.append(text[start:end])
            start += max_chars - overlap
        return chunks

    @classmethod
    def chunk_drug_label(cls, pages: List[Dict[str, Any]], max_chars: int = 1200, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Chunks drug labels page-by-page, identifying clinical sections.
        """
        chunks = []
        current_section = "general"

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]
            lines = page_text.split("\n")
            
            # Identify if any section header exists on this page
            section_indices = []
            for i, line in enumerate(lines):
                cleaned_line = line.strip()
                for sec_name, pattern in SECTION_PATTERNS.items():
                    if pattern.match(cleaned_line):
                        section_indices.append((i, sec_name))
                        break
            
            # Sort transitions by line number
            section_indices.sort(key=lambda x: x[0])
            
            if not section_indices:
                # No new sections on this page. Entire page text belongs to current_section
                sub_texts = cls.split_text_by_length(page_text, max_chars, overlap)
                for sub_text in sub_texts:
                    chunks.append({
                        "chunk_text": sub_text,
                        "clinical_section": current_section,
                        "page_number": page_num
                    })
            else:
                # Section transitions occur on this page
                last_idx = 0
                for line_idx, next_section in section_indices:
                    # Capture text before the transition line
                    pre_text = "\n".join(lines[last_idx:line_idx]).strip()
                    if pre_text:
                        sub_texts = cls.split_text_by_length(pre_text, max_chars, overlap)
                        for sub_text in sub_texts:
                            chunks.append({
                                "chunk_text": sub_text,
                                "clinical_section": current_section,
                                "page_number": page_num
                            })
                    current_section = next_section
                    last_idx = line_idx + 1 # skip header line
                
                # Capture text after last transition
                post_text = "\n".join(lines[last_idx:]).strip()
                if post_text:
                    sub_texts = cls.split_text_by_length(post_text, max_chars, overlap)
                    for sub_text in sub_texts:
                        chunks.append({
                            "chunk_text": sub_text,
                            "clinical_section": current_section,
                            "page_number": page_num
                        })
        return chunks

    @classmethod
    def chunk_guideline(cls, pages: List[Dict[str, Any]], max_chars: int = 1500, overlap: int = 250) -> List[Dict[str, Any]]:
        """
        Chunks clinical guidelines page-by-page.
        """
        chunks = []
        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]
            
            sub_texts = cls.split_text_by_length(page_text, max_chars, overlap)
            for sub_text in sub_texts:
                chunks.append({
                    "chunk_text": sub_text,
                    "clinical_section": "guideline",
                    "page_number": page_num
                })
        return chunks
