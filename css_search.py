# -*- coding: utf-8 -*-
# encoding: utf-8
"""
현자의 거울 스튜디오 UI 개선 스크립트 2단계
- CSS: 글래스모피즘 컨트롤 박스
- CSS: 파이프 라벨 폰트 확대
- 버전 헤더 업데이트
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"파일 로드 완료. 줄 수: {len(content.splitlines())}")

# ===========================================================================
# CSS 검색: 현재 .sage-pipe-label 스타일 찾기
# ===========================================================================
if 'sage-pipe-label' in content:
    idx = content.index('sage-pipe-label')
    print(f"sage-pipe-label 발견 위치: {idx}")
    print(f"주변 텍스트: {repr(content[idx-5:idx+200])}")
else:
    print("sage-pipe-label 미발견")

# ===========================================================================
# CSS 검색: header-pop-wrapper 찾기
# ===========================================================================
if 'header-pop-wrapper' in content:
    idx = content.index('header-pop-wrapper')
    print(f"header-pop-wrapper 발견. 주변: {repr(content[idx-5:idx+100])}")
else:
    print("header-pop-wrapper 미발견")

# ===========================================================================
# header-control-box-anchor 찾기
# ===========================================================================
if 'header-control-box-anchor' in content:
    idx = content.index('header-control-box-anchor')
    print(f"header-control-box-anchor 발견. 주변: {repr(content[idx-50:idx+150])}")

print("검색 완료!")
