# -*- coding: utf-8 -*-
"""
safety/citation_validator.py — 인용 검증 (위조 방지)
"""

import re
from core.obsidian import search_rag


# ── 인용 패턴 ──
CITATION_PATTERNS = [
    r'\[SOURCE:\s*([^\]]+)\]',
    r'"([^"]+)"[\s—-]+(쇼펜하우어|니체|융|프랭클|몽테뉴|소크라테스)',
    r'(시편|잠언|전도서|욥기|로마서)\s*(\d+)[:장]\s*(\d+)?',
]


def extract_citations(text: str) -> list:
    """인용문 자동 추출"""
    citations = []
    for pattern in CITATION_PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            citations.append(m if isinstance(m, str) else " | ".join(m))
    return citations


def validate_citations(text: str) -> dict:
    """인용 검증 — Obsidian RAG 교차 확인"""
    citations = extract_citations(text)
    verified = []
    suspicious = []
    
    for citation in citations:
        if "Gemma 추론" in citation or "확인 필요" in citation or "NEED_RESEARCH" in citation:
            continue
        
        rag_result = search_rag(citation, max_files=2, max_chars=200)
        if rag_result:
            verified.append(citation)
        else:
            suspicious.append(citation)
    
    return {
        "total": len(citations),
        "verified": verified,
        "suspicious": suspicious,
        "trust_score": len(verified) / max(len(citations), 1),
        "action": "검증 필요" if suspicious else "통과",
    }
