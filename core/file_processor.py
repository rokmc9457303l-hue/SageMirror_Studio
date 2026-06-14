# -*- coding: utf-8 -*-
"""
core/file_processor.py — 파일 분석 + 3중 저장 파이프라인
지원 형식: .md .txt .pdf .docx .csv
흐름: 텍스트 추출 → Gemma 분석 → save_dual() + save_schema()
"""

import io
from pathlib import Path
from core.brain import call_gemma
from core.obsidian import save_dual, save_schema


CATEGORIES = [
    "감정", "철학", "다크심리학", "성경·신앙", "심리학",
    "문학·에세이", "고전소설", "한국문학", "인생단계", "역사·인물",
    "경제·비즈니스", "건강·생활", "유튜브전략", "채널운영", "제작자료", "출처자료",
]


def extract_text(file_bytes: bytes, filename: str) -> str:
    """파일 형식별 텍스트 추출"""
    ext = Path(filename).suffix.lower()

    if ext in (".md", ".txt"):
        return file_bytes.decode("utf-8", errors="ignore")

    if ext == ".csv":
        import csv
        text = file_bytes.decode("utf-8", errors="ignore")
        rows = list(csv.reader(io.StringIO(text)))
        return "\n".join(", ".join(r) for r in rows[:200])

    if ext == ".pdf":
        try:
            import pdfminer.high_level as _pdf
            result = _pdf.extract_text(io.BytesIO(file_bytes))
            return result or ""
        except ImportError:
            pass
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            return f"[PDF 추출 실패: pdfminer 또는 PyPDF2 설치 필요]\n파일명: {filename}"

    if ext == ".docx":
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            return f"[DOCX 추출 실패: python-docx 설치 필요]\n파일명: {filename}"

    return file_bytes.decode("utf-8", errors="ignore")


def analyze_content(content: str, filename: str) -> dict:
    """Gemma로 내용 분석 → 요약/카테고리/키워드/관련성"""
    preview = content[:3000]
    cats_str = "/".join(CATEGORIES)

    prompt = (
        f"자료를 분석하고 아래 형식 그대로만 답변하세요.\n\n"
        f"[자료]: {filename}\n[내용]:\n{preview}\n\n---\n"
        f"요약: (2~3문장)\n"
        f"카테고리: ({cats_str} 중 1~2개)\n"
        f"키워드: (핵심 키워드 5개, 쉼표 구분)\n"
        f"태그: (관련 인물/개념 3개, 쉼표 구분)\n"
        f"관련파트: (1~8 숫자, 쉼표 구분)\n"
        f"채널관련성: (0.0~1.0)\n"
        f"인용구: (가장 중요한 문장 1개)\n"
        f"감정키워드: (고독/후회/상실/공허/분노 등 3개, 쉼표 구분)"
    )

    raw = call_gemma(prompt, max_tokens=512, temperature=0.2)
    return _parse_analysis(raw)


def _parse_analysis(raw: str) -> dict:
    result = {
        "summary": "", "category": "출처자료", "keywords": [], "tags": [],
        "related_parts": [1], "channel_relevance": 0.5,
        "quote": "", "emotion_keywords": [],
    }
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("요약:"):
            result["summary"] = line[3:].strip()
        elif line.startswith("카테고리:"):
            result["category"] = line[5:].strip().split("/")[0].strip()
        elif line.startswith("키워드:"):
            result["keywords"] = [k.strip() for k in line[4:].split(",") if k.strip()][:5]
        elif line.startswith("태그:"):
            result["tags"] = [t.strip() for t in line[3:].split(",") if t.strip()][:3]
        elif line.startswith("관련파트:"):
            nums = [p.strip() for p in line[5:].split(",")]
            result["related_parts"] = [
                int(p) for p in nums if p.isdigit() and 1 <= int(p) <= 8
            ] or [1]
        elif line.startswith("채널관련성:"):
            try:
                result["channel_relevance"] = float(line[7:].strip())
            except ValueError:
                pass
        elif line.startswith("인용구:"):
            result["quote"] = line[4:].strip()
        elif line.startswith("감정키워드:"):
            result["emotion_keywords"] = [k.strip() for k in line[7:].split(",") if k.strip()][:3]
    return result


def process_and_save(content: str, filename: str, part_num: int = None,
                     source_type: str = "file") -> dict:
    """분석 → save_dual() + save_schema() 동시 실행"""
    analysis = analyze_content(content, filename)

    saved = save_dual(content=content, title=filename,
                      part_num=part_num, source_type=source_type)

    meta = {
        "source_type":       source_type,
        "category":          analysis["category"],
        "keywords":          analysis["keywords"],
        "tags":              analysis["tags"],
        "related_parts":     analysis.get("related_parts", [part_num] if part_num else [1]),
        "channel_relevance": analysis["channel_relevance"],
        "summary":           analysis["summary"],
        "quote":             analysis.get("quote", ""),
        "emotion_keywords":  analysis.get("emotion_keywords", []),
    }
    schema_path = save_schema(content=content, meta=meta, title=filename)
    saved["schema"] = schema_path

    return {"analysis": analysis, "saved": saved}
