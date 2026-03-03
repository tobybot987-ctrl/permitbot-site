from __future__ import annotations

import re
from pathlib import Path
from pypdf import PdfReader

from models import Claim, Evidence


PATTERNS = {
    "design_storm_event": re.compile(r"(\d{1,3}\s*[- ]?year\s*/\s*24[- ]?hour)", re.I),
    "retention_required_value": re.compile(r"required\s+retention\s*[:=]?\s*([\d,.]+)\s*(cf|ac-ft)?", re.I),
    "retention_provided_value": re.compile(r"provided\s+retention\s*[:=]?\s*([\d,.]+)\s*(cf|ac-ft)?", re.I),
    "freeboard_value": re.compile(r"freeboard\s*[:=]?\s*([\d.]+)\s*(ft|in)?", re.I),
}


def parse_pdfs(pdf_paths: list[str]) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    page_no = 1
    for p in pdf_paths:
        r = PdfReader(p)
        for pg in r.pages:
            pages.append((page_no, pg.extract_text() or ""))
            page_no += 1
    return pages


def extract_claims(pages: list[tuple[int, str]]) -> dict[str, Claim]:
    claims: dict[str, Claim] = {}
    for key, pat in PATTERNS.items():
        for page, text in pages:
            m = pat.search(text)
            if m:
                claims[key] = Claim(key=key, value=m.group(1), page=page, excerpt=text[max(0, m.start()-120):m.end()+120])
                break
    if "emergency_overflow_present" not in claims:
        for page, text in pages:
            if re.search(r"emergency\s+overflow|overflow\s+weir", text, re.I):
                claims["emergency_overflow_present"] = Claim(
                    key="emergency_overflow_present", value=True, page=page, excerpt=text[:300]
                )
                break
    return claims
