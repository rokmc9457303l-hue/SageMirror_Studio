# -*- coding: utf-8 -*-
"""
panel/md_validator.py — MD 저장 전 검증 시스템 (Task K)

검증 항목:
  1. 빈 파일 금지
  2. 최소 길이 (50자)
  3. {{VAR}} 형식 오류 감지 ({VAR} 단일 중괄호 등)
  4. 깨진 JSON 블록 감지
  5. MAIN_PROMPT/AGENT_PROTOCOL 필수 섹션 존재 확인
"""

import re
import json
from pathlib import Path


def validate_md(content: str, path: str = "") -> list:
    """
    MD 내용 검증.

    Returns:
        list[str]: 오류 메시지 목록. 빈 리스트 = 통과.
    """
    issues = []
    filename = Path(path).name if path else ""

    # 1. 빈 내용
    if not content.strip():
        issues.append("파일이 비어 있습니다.")
        return issues  # 이후 검사 불필요

    # 2. 최소 길이
    if len(content.strip()) < 50:
        issues.append(f"내용이 너무 짧습니다 ({len(content.strip())}자 / 최소 50자).")

    # 3. 단일 중괄호 변수 패턴 ({VAR} — 이중이어야 함)
    single_brace = re.findall(r"(?<!\{)\{([A-Z_]+)\}(?!\})", content)
    if single_brace:
        issues.append(
            f"변수 형식 오류: {{{', '.join(single_brace)}}} — {{{{VAR}}}} 형식을 사용하세요."
        )

    # 4. 깨진 JSON 코드 블록
    json_blocks = re.findall(r"```json\s*([\s\S]*?)```", content)
    for i, block in enumerate(json_blocks, 1):
        try:
            json.loads(block.strip())
        except json.JSONDecodeError as e:
            issues.append(f"JSON 블록 {i}번 파싱 오류: {e}")

    # 5. 필수 섹션 확인 (파일명 기반)
    if "MAIN_PROMPT" in filename:
        required = ["## ", "출력", "입력"]
        for req in required:
            if req not in content:
                issues.append(f"MAIN_PROMPT 필수 항목 누락: '{req}'")

    if "AGENT_PROTOCOL" in filename:
        required = ["역할", "출력", "금지"]
        for req in required:
            if req not in content:
                issues.append(f"AGENT_PROTOCOL 필수 항목 누락: '{req}'")

    # 6. 하드코딩 채널명 감지 (범용성 원칙)
    hardcoded = ["현자의거울", "sage_mirror", "현자의 거울", "SageMirror"]
    for term in hardcoded:
        if term in content:
            issues.append(
                f"하드코딩 금지: '{term}' — {{{{CHANNEL_NAME}}}} 변수를 사용하세요."
            )

    return issues
