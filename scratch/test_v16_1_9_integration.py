import sys
import os
import json
import shutil
from unittest.mock import MagicMock

# 라이브러리 경로 추가
sys.path.append(r"C:\SageMirror_Production")

def test_save_and_load_persistence():
    print("--- Test 1: save_workspace_state_core & load_workspace_state_core ---")
    from memory_state_manager import save_workspace_state_core, load_workspace_state_core
    
    test_workspace_file = r"C:\SageMirror_Production\scratch\test_workspace_state.json"
    test_secrets_file = r"C:\SageMirror_Production\scratch\test_local_secrets.json"
    
    # 1. 초기 세션 값 임의 세팅 (Part 2 Step 1 관련 키들)
    state = {
        "p2_gemma_protocol": "TEST_P2_GEMMA_PROTOCOL_SAVE_20260526\nHow -> 자유 | What -> 통제",
        "p2_thumbnail_sets": [
            {"set_num": 1, "title": "늦은 후회의 과학", "topic": "후회", "image": "렘브란트 비주얼"}
        ],
        "p2_selected_thumbnail": {"set_num": 1, "title": "늦은 후회의 과학"},
        "p2_thumbnail_plan": "TEST_P2_THUMBNAIL_SAVE_20260526",
        "path_obsidian": "C:\\SageMirror_Production\\00_Obsidian_Archive",
        "selected_model": "gemma4:e2b"
    }
    
    # 2. 저장 테스트
    cleaned_updates, secrets, success = save_workspace_state_core(state, test_workspace_file, test_secrets_file)
    assert success, "저장 작업이 실패했습니다."
    print("Save Success. Saved data structure checked.")
    
    # 3. 실제 파일 확인
    with open(test_workspace_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    print(f"Saved JSON content keys: {list(saved_data.keys())}")
    assert "p2_gemma_protocol" in saved_data, "p2_gemma_protocol 저장 누락"
    assert "p2_thumbnail_sets" in saved_data, "p2_thumbnail_sets 저장 누락"
    assert "p2_selected_thumbnail" in saved_data, "p2_selected_thumbnail 저장 누락"
    assert "p2_thumbnail_plan" in saved_data, "p2_thumbnail_plan 저장 누락"
    
    assert saved_data["p2_gemma_protocol"] == state["p2_gemma_protocol"], "p2_gemma_protocol 값 훼손"
    assert len(saved_data["p2_thumbnail_sets"]) == 1, "p2_thumbnail_sets 값 훼손"
    assert saved_data["p2_selected_thumbnail"]["set_num"] == 1, "p2_selected_thumbnail 값 훼손"
    
    # 4. 로드 테스트
    loaded = load_workspace_state_core(test_workspace_file, test_secrets_file)
    print("Load Success. Loaded data structure checked.")
    assert loaded["p2_gemma_protocol"] == state["p2_gemma_protocol"], "로드된 p2_gemma_protocol 값 불일치"
    assert loaded["p2_thumbnail_plan"] == state["p2_thumbnail_plan"], "로드된 p2_thumbnail_plan 값 불일치"
    
    # Cleanup 임시 파일
    if os.path.exists(test_workspace_file):
        os.remove(test_workspace_file)
    if os.path.exists(test_secrets_file):
        os.remove(test_secrets_file)
    print("Test 1 Passed.")


def test_sanitize_integrity():
    print("\n--- Test 2: sanitize & clean_prompt_contamination integrity ---")
    from memory_state_manager import clean_prompt_contamination
    
    # 1. 정상 프로토콜 보존 검증 (삭제되면 안 됨)
    normal_protocol = "TEST_P2_GEMMA_PROTOCOL_SAVE_20260526\n- 규정 1: @Protagonist 명시\n- 출처: [SOURCE: 성경 - 시편 23:1]"
    cleaned_normal = clean_prompt_contamination(normal_protocol)
    print(f"Cleaned Normal Protocol:\n{cleaned_normal}")
    assert "TEST_P2_GEMMA_PROTOCOL_SAVE_20260526" in cleaned_normal, "정상 텍스트가 정화 필터에 의해 유실됨"
    assert "[SOURCE: 성경 - 시편 23:1]" in cleaned_normal, "정상 출처 텍스트가 유실됨"
    
    # 2. 오염 텍스트 제거 검증
    polluted = (
        "TEST_P2_GEMMA_PROTOCOL_SAVE_20260526\n"
        "<span title='리서치 자동저장 대기 중' style='display: inline-block; width: 14px;'></span>"
        "즉석 실시간 구글 리서치 & 저장"
    )
    cleaned_polluted = clean_prompt_contamination(polluted)
    print(f"Cleaned Polluted Text:\n{cleaned_polluted}")
    assert "즉석 실시간 구글 리서치" not in cleaned_polluted, "오염 텍스트가 정화되지 않음"
    assert "리서치 자동저장 대기 중" not in cleaned_polluted, "오염 span 태그가 정화되지 않음"
    print("Test 2 Passed.")


def test_init_session_state_non_overwriting():
    print("\n--- Test 3: init_session_state non-overwriting behavior ---")
    
    class MockSessionState(dict):
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)
        def __setattr__(self, key, value):
            self[key] = value
            
    # Streamlit Mocking
    import streamlit as st
    st.session_state = MockSessionState()
    
    # 1. 이미 세션 스테이트에 로드된 값이 존재할 경우
    st.session_state["p2_gemma_protocol"] = "PRE_LOADED_PROTOCOL_VALUE"
    st.session_state["p2_thumbnail_sets"] = [{"set_num": 2, "title": "외로움의 분석"}]
    
    # 임시 mock load_workspace_state
    import app_v16_1_9
    app_v16_1_9.load_workspace_state = MagicMock(return_value={
        "p2_gemma_protocol": "LOADED_FROM_FILE_PROTOCOL_VALUE",
        "p2_thumbnail_sets": [{"set_num": 3, "title": "옵시디언에서 로드됨"}]
    })
    
    # 2. init_session_state 실행
    app_v16_1_9.init_session_state()
    
    # 결과 확인: 이미 st.session_state에 들어있던 PRE_LOADED_PROTOCOL_VALUE 가 보존되어야 함.
    print(f"p2_gemma_protocol: {st.session_state.get('p2_gemma_protocol')}")
    print(f"p2_thumbnail_sets: {st.session_state.get('p2_thumbnail_sets')}")
    
    assert st.session_state.get("p2_gemma_protocol") == "PRE_LOADED_PROTOCOL_VALUE", "기존 세션 값을 기본값으로 덮어씀"
    assert len(st.session_state.get("p2_thumbnail_sets")) == 1, "기존 세션 리스트를 기본값으로 덮어씀"
    assert st.session_state.get("p2_thumbnail_sets")[0]["set_num"] == 2, "기존 세션 데이터가 변질됨"
    print("Test 3 Passed.")


def main():
    try:
        test_save_and_load_persistence()
        test_sanitize_integrity()
        test_init_session_state_non_overwriting()
        print("\n🎉 ALL PERSISTENCE TESTS PASSED SUCCESSFULLY! v16.1.9 is fully stable.")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
