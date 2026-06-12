# -*- coding: utf-8 -*-
"""
migrate_universal.py
00_Obsidian_Archive → 00_Obsidian/01_Raw_Data/99_과거_아카이브_통합
범용 YAML 프론트매터 자동 주입 후 이동
"""

import os
import re
import sys
import shutil
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SRC  = Path(r"C:\SageMirror_Production\00_Obsidian_Archive")
DST  = Path(r"C:\SageMirror_Production\00_Obsidian\01_Raw_Data\99_과거_아카이브_통합")
TODAY = datetime.now().strftime("%Y-%m-%d")

CATEGORY_RULES = [
    ("사유/성찰",   ["쇼펜하우어", "융", "철학", "니체", "프랭클", "실존", "스토아",
                     "고독", "허무", "의지", "로고테라피", "개성화", "키에르케고르"]),
    ("신앙/종교",   ["시편", "성경", "하나님", "잠언", "전도서", "욥기", "예수",
                     "기도", "은혜", "복음", "말씀", "신앙"]),
    ("유튜브전략",  ["유튜브", "알고리즘", "벤치마킹", "쇼츠", "썸네일", "조회수",
                     "구독자", "채널", "크리에이터", "업로드", "스크립트"]),
    ("정보/리뷰",   ["매출", "상품", "쇼핑", "쿠팡", "리뷰", "제품", "구매", "가격"]),
]

def detect_category(text: str) -> str:
    for category, keywords in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            return category
    return "일반/미분류"

FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

def inject_frontmatter(text: str, category: str) -> str:
    fm = (
        "---\n"
        f"channel_id: UNCLASSIFIED\n"
        f"category: {category}\n"
        f"status: \"#Raw_Data\"\n"
        f"migrated_date: {TODAY}\n"
        "---\n"
    )
    if FRONTMATTER_RE.match(text):
        # 이미 존재 → 병합: channel_id / category / status / migrated_date 추가
        existing = FRONTMATTER_RE.match(text).group(0)
        body_after = text[len(existing):]
        inner = existing[4:-4].strip()  # --- 제거한 내부
        # 없는 키만 추가
        additions = []
        if "channel_id:" not in inner:
            additions.append(f"channel_id: UNCLASSIFIED")
        if "category:" not in inner:
            additions.append(f"category: {category}")
        if "status:" not in inner:
            additions.append(f"status: \"#Raw_Data\"")
        if "migrated_date:" not in inner:
            additions.append(f"migrated_date: {TODAY}")
        merged_inner = inner + ("\n" + "\n".join(additions) if additions else "")
        return f"---\n{merged_inner}\n---\n{body_after}"
    else:
        return fm + text

def safe_dst_path(src_file: Path) -> Path:
    rel = src_file.relative_to(SRC)
    candidate = DST / rel
    # 중복 파일명 처리
    if candidate.exists():
        stem = candidate.stem
        suffix = candidate.suffix
        parent = candidate.parent
        i = 1
        while candidate.exists():
            candidate = parent / f"{stem}_{i}{suffix}"
            i += 1
    return candidate

def main():
    DST.mkdir(parents=True, exist_ok=True)

    success = 0
    skipped = 0
    errors  = []

    md_files = list(SRC.rglob("*.md"))
    total = len(md_files)
    print(f"[시작] 총 {total}개 .md 파일 이주 시작 → {DST}")
    print("-" * 60)

    for src_file in md_files:
        try:
            text = src_file.read_text(encoding="utf-8", errors="replace")
            category = detect_category(text)
            new_text  = inject_frontmatter(text, category)

            dst_file = safe_dst_path(src_file)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            dst_file.write_text(new_text, encoding="utf-8")
            # 읽기전용 속성 해제 후 삭제
            os.chmod(src_file, 0o666)
            src_file.unlink()
            success += 1
            print(f"  ✅ [{category:10s}] {src_file.name}")
        except Exception as e:
            errors.append((str(src_file), str(e)))
            skipped += 1
            print(f"  ❌ 오류: {src_file.name} → {e}")

    # 빈 디렉터리 정리 (SRC 하위 빈 폴더 + SRC 자체)
    for dirpath, dirnames, filenames in os.walk(str(SRC), topdown=False):
        if not os.listdir(dirpath):
            os.rmdir(dirpath)
            print(f"  🗑  빈 폴더 삭제: {dirpath}")

    print("\n" + "=" * 60)
    print(f"[완료 리포트]")
    print(f"  총 대상 파일  : {total}개")
    print(f"  ✅ 성공 이주  : {success}개")
    print(f"  ❌ 오류 스킵  : {skipped}개")
    print(f"  대상 경로     : {DST}")
    if errors:
        print(f"\n[오류 목록]")
        for path, msg in errors:
            print(f"  - {path}: {msg}")
    src_remains = SRC.exists()
    print(f"\n  소스 폴더 잔존: {'예 (비어있지 않음)' if src_remains else '삭제 완료'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
