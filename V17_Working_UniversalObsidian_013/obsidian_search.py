# -*- coding: utf-8 -*-
"""
obsidian_search.py — 현자의 거울 멀티볼트 RAG 검색 엔진 v2.0
[v2.0 업그레이드: 2026-05-27]
- CrossVaultBridge 통합: 세 밭(Production/Backup/Archive)을 하나의 검색 공간으로 통합
- 볼트 우선순위: 00_Obsidian > CrossVaultBridge > 00_Obsidian_Archive
- 결과에 볼트 출처 표시
- TF-IDF 스타일 가중치 적용 (제목 매칭 2배 가중)
"""
import os
import re
from typing import List, Dict
from pathlib import Path


# ── 밭별 볼트 경로 (CrossVault 통합 경로) ──
VAULT_PATHS = [
    r"C:\SageMirror_Production\00_Obsidian",
    r"C:\SageMirror_Production\00_Obsidian\_shared\CrossVaultBridge",
    r"C:\SageMirror_Production\00_Obsidian_Archive",
]

VAULT_LABELS = {
    r"C:\SageMirror_Production\00_Obsidian": "🌿 메인볼트",
    r"C:\SageMirror_Production\00_Obsidian\_shared\CrossVaultBridge": "🌉 브릿지",
    r"C:\SageMirror_Production\00_Obsidian_Archive": "📚 아카이브",
}


def load_obsidian_notes(vault_path: str) -> List[Dict]:
    """단일 볼트에서 모든 .md 파일을 로드합니다."""
    notes = []
    if not os.path.exists(vault_path):
        return notes

    vault_label = VAULT_LABELS.get(vault_path, "볼트")

    for root, _, files in os.walk(vault_path):
        for file in files:
            if not file.endswith(".md"):
                continue
            path = os.path.join(root, file)
            try:
                for enc in ["utf-8", "cp949", "euc-kr"]:
                    try:
                        content = Path(path).read_text(encoding=enc, errors="ignore")
                        break
                    except Exception:
                        content = ""
                notes.append({
                    "title": os.path.splitext(file)[0],
                    "path": path,
                    "content": content,
                    "vault": vault_label,
                    "vault_path": vault_path,
                })
            except Exception:
                continue
    return notes


def load_all_vaults(extra_vault_path: str = None) -> List[Dict]:
    """
    세 밭 전체에서 노트를 로드합니다.
    extra_vault_path: 세션 스테이트에서 넘어오는 추가 경로 (선택)
    """
    all_notes = []
    paths = list(VAULT_PATHS)
    if extra_vault_path and extra_vault_path not in paths and os.path.exists(extra_vault_path):
        paths.insert(0, extra_vault_path)

    seen_paths = set()
    for vault_path in paths:
        notes = load_obsidian_notes(vault_path)
        for note in notes:
            if note["path"] not in seen_paths:
                seen_paths.add(note["path"])
                all_notes.append(note)
    return all_notes


def simple_keyword_search(
    vault_path: str,
    query: str,
    top_k: int = 10,
    search_all_vaults: bool = True,
) -> List[Dict]:
    """
    키워드 기반 멀티볼트 RAG 검색.
    - search_all_vaults=True: 세 밭 전체 검색 (기본값)
    - search_all_vaults=False: vault_path 단일 볼트만 검색 (하위 호환)
    - 제목 매칭: 가중치 2배
    - 결과에 볼트 출처 표시
    """
    if search_all_vaults:
        notes = load_all_vaults(extra_vault_path=vault_path)
    else:
        notes = load_obsidian_notes(vault_path)

    query_terms = re.findall(r"\w+", query.lower())
    if not query_terms:
        return []

    results = []
    for note in notes:
        title_lower = note["title"].lower()
        content_lower = note["content"].lower()

        score = 0
        # 제목 매칭: 2배 가중치
        for term in query_terms:
            score += title_lower.count(term) * 2
            score += content_lower.count(term)

        if score > 0:
            results.append({
                "title": note["title"],
                "path": note["path"],
                "score": score,
                "preview": note["content"][:500],
                "vault": note.get("vault", "볼트"),
                "vault_path": note.get("vault_path", vault_path),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def search_archive_only(query: str, top_k: int = 5) -> List[Dict]:
    """아카이브 볼트(고전 문헌)만 검색합니다."""
    return simple_keyword_search(
        vault_path=r"C:\SageMirror_Production\00_Obsidian_Archive",
        query=query,
        top_k=top_k,
        search_all_vaults=False,
    )


def search_bridge_only(query: str, top_k: int = 5) -> List[Dict]:
    """CrossVaultBridge만 검색합니다."""
    return simple_keyword_search(
        vault_path=r"C:\SageMirror_Production\00_Obsidian\_shared\CrossVaultBridge",
        query=query,
        top_k=top_k,
        search_all_vaults=False,
    )