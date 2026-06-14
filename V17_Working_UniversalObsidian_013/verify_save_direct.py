import os
import json
import hashlib
from datetime import datetime
from sage_popups_v17_2_4 import _save_raw_wiki

def test_save():
    user_query = "기술 발전이 인간의 집중력에 미치는 영향을 범용 지식 자료로 정리해줘."
    content = "기술 발전은 인간의 집중력에 큰 영향을 미칩니다. 스마트폰과 소셜 미디어는 주의력을 분산시키는 주된 요인입니다."
    title = "기술과 집중력"
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
