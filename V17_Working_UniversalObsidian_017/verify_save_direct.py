import os
import json
import hashlib
from datetime import datetime
from sage_popups_v17_2_4 import _save_raw_wiki

def test_save():
    user_query = "Obsidian 저장 검증 테스트입니다. Raw Wiki Schema Logs 저장 여부를 확인합니다."
    content = "이것은 옵시디언 4계층 구조 저장이 정상적으로 동작하는지 검증하기 위한 테스트 응답 내용입니다."
    title = "옵시디언 저장 검증"
    source_type = "RightResearch"
    part_key = "part0"
    model_name = "gemma4:e2b"
    
    print("1. 저장 시도...")
    res1 = _save_raw_wiki(user_query, content, title, source_type, part_key, model_name)
    print("결과1:", res1)
    
    print("2. 중복 저장 시도...")
    res2 = _save_raw_wiki(user_query, content, title, source_type, part_key, model_name)
    print("결과2:", res2)

    return res1

if __name__ == "__main__":
    test_save()
