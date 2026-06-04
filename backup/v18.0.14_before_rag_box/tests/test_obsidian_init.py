# -*- coding: utf-8 -*-
"""옵시디언 폴더 초기화 실행"""

import sys
sys.path.insert(0, r"C:\SageMirror_Studio_v18")

from core.obsidian_init import (
    initialize_obsidian_structure,
    get_structure_status,
)


def main():
    print("=" * 60)
    print("옵시디언 3층 도서관 구조 초기화 시작")
    print("=" * 60)
    
    # 초기화 실행
    result = initialize_obsidian_structure()
    
    print(f"\n[1] 00_Raw 폴더 생성: {len(result['raw'])}개")
    for sub in result["raw"]:
        print(f"   ✓ {sub}")
    
    print(f"\n[2] 10_Wiki 폴더 생성: {len(result['wiki'])}개")
    for sub in result["wiki"]:
        print(f"   ✓ {sub}")
    
    print(f"\n[3] 20_Schema 파일 생성: {len(result['schema'])}개")
    for f in result["schema"]:
        print(f"   ✓ {f}")
    
    if result["skipped"]:
        print(f"\n[!] 이미 존재 (건너뜀): {len(result['skipped'])}개")
        for s in result["skipped"][:5]:
            print(f"   - {s}")
    
    print("\n" + "=" * 60)
    print("최종 상태 확인")
    print("=" * 60)
    
    status = get_structure_status()
    print(f"\n00_Raw    : 하위폴더 {status['raw']['subfolders']}개, 파일 {status['raw']['files']}개")
    print(f"10_Wiki   : 하위폴더 {status['wiki']['subfolders']}개, 파일 {status['wiki']['files']}개")
    print(f"20_Schema : 파일 {status['schema']['files']}개")
    
    print("\n✅ 옵시디언 3층 도서관 구조 완성")


if __name__ == "__main__":
    main()
