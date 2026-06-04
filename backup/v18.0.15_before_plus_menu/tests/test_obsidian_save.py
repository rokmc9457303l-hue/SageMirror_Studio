# -*- coding: utf-8 -*-
"""
tests/test_obsidian_save.py — 옵시디언 듀얼 저장 실작동 테스트
"""

import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, r"C:\SageMirror_Studio_v18")

from core.config import OBSIDIAN_CHANNEL, OBSIDIAN_UNIVERSAL, APP_VERSION
from core.obsidian import save_dual, classify_tags
from core.auto_save import schedule_part_save, get_queue_status
import time


def test_basic_save():
    """기본 듀얼 저장 테스트"""
    print(f"\n=== {APP_VERSION} 옵시디언 저장 테스트 ===\n")
    
    # 테스트 콘텐츠 (4070 감성, 철학·심리·성경 포함)
    test_content = """
[테스트 주제] 60대의 고독

60대에 접어든 한 남성이 느끼는 깊은 외로움에 대한 자료조사입니다.

쇼펜하우어는 그의 저작에서 인간의 의지와 고통에 대해 이야기했습니다.
[SOURCE: 쇼펜하우어, 의지와 표상으로서의 세계]

빅터 프랭클의 로고테라피는 의미를 찾는 인간의 본질을 다룹니다.
[SOURCE: 프랭클, 죽음의 수용소에서]

시편 23편은 가장 어두운 골짜기에서도 함께하시는 분에 대해 노래합니다.
[SOURCE: 시편 23:4]

핵심 감정 키워드: 고독, 후회, 상실, 공허, 회복
연결 개념: 다크심리학, 그림자자아, 회복탄력성
"""
    
    print("[1] 직접 동기 저장 테스트")
    result = save_dual(
        content=test_content,
        title="60대고독_테스트_EP001",
        part_num=1,
        source_type="테스트 자료",
    )
    
    print(f"\n[규칙서 저장 경로]")
    print(f"  {result['규칙서']}")
    print(f"\n[범용 카테고리 저장 ({len(result['범용'])}건)]")
    for path in result['범용']:
        print(f"  - {path}")
    
    # 카테고리 자동 분류 확인
    print("\n[2] 자동 분류된 태그 확인")
    tags = classify_tags(test_content, "60대고독_테스트")
    for category, keywords in tags.items():
        print(f"  📁 {category}: {keywords}")
    
    print("\n[3] 백그라운드 자동 저장 테스트")
    schedule_part_save(
        part_num=2,
        content=test_content + "\n\n[Part 2 추가 분석]\n기승전결 프레임 적용 완료.",
        title="60대고독_Part2_백그라운드_테스트",
    )
    
    print(f"  큐 상태: {get_queue_status()}")
    print("  3초 대기 후 처리 확인...")
    time.sleep(3)
    print(f"  처리 후 큐 상태: {get_queue_status()}")
    
    print("\n[4] 옵시디언 폴더 확인")
    print(f"  채널_현자의거울: {OBSIDIAN_CHANNEL}")
    print(f"  범용카테고리: {OBSIDIAN_UNIVERSAL}")
    
    if OBSIDIAN_CHANNEL.exists():
        part1_folder = OBSIDIAN_CHANNEL / "Part1_자료수집"
        if part1_folder.exists():
            files = list(part1_folder.glob("*.md"))
            print(f"\n  Part1 폴더 파일 수: {len(files)}")
            for f in files[-3:]:
                print(f"    📄 {f.name}")
    
    if OBSIDIAN_UNIVERSAL.exists():
        print(f"\n  범용 카테고리 폴더:")
        for cat_dir in sorted(OBSIDIAN_UNIVERSAL.iterdir())[:5]:
            if cat_dir.is_dir():
                file_count = len(list(cat_dir.glob("*.md")))
                print(f"    📁 {cat_dir.name}: {file_count}건")
    
    print("\n✅ 테스트 완료\n")
    return result


if __name__ == "__main__":
    test_basic_save()
