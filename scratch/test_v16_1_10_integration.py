import sys
import os
import json
from unittest.mock import MagicMock

# 라이브러리 경로 추가
sys.path.append(r"C:\SageMirror_Production")

def test_prompt_no_overwriting_during_render():
    print("--- Test 1: Prompt initial state preservation on render ---")
    
    class MockSessionState(dict):
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)
        def __setattr__(self, key, value):
            self[key] = value
            
    import streamlit as st
    st.session_state = MockSessionState()
    
    # 1. 사용자가 임의로 수정한 프롬프트들을 세션에 적재했다고 가정
    st.session_state["p2_gemma_protocol"] = "MODIFIED_GEMMA_PROTOCOL_BY_USER_20260526"
    st.session_state["p2_bench_prompt"] = "MODIFIED_BENCH_PROMPT_BY_USER_20260526"
    st.session_state["p2_research_prompt"] = "MODIFIED_RESEARCH_PROMPT_BY_USER_20260526"
    st.session_state["p2_plan_prompt"] = "MODIFIED_PLAN_PROMPT_BY_USER_20260526"
    
    # 2. app_v16_1_10.py 내의 render_part2가 호출되기 직전 세션 상태
    # render_part2를 실행했을 때 st.session_state.p2_gemma_protocol 등이 덮어씌워지지 않는지 검증하기 위해,
    # render_part2 내에서 쓰이는 widgets, columns, selectbox 등 streamlit 컴포넌트들을 mocking해준다.
    def mock_columns(spec, **kwargs):
        if isinstance(spec, list):
            return [MagicMock() for _ in range(len(spec))]
        elif isinstance(spec, int):
            return [MagicMock() for _ in range(spec)]
        return [MagicMock(), MagicMock()]
        
    st.columns = mock_columns
    st.selectbox = MagicMock(return_value="gemma4:e2b")
    st.text_input = MagicMock(return_value="7777")
    st.button = MagicMock(return_value=False)
    
    def mock_text_area(label, value=None, **kwargs):
        return value if value is not None else ""
    st.text_area = mock_text_area
    st.caption = MagicMock()
    st.divider = MagicMock()
    st.subheader = MagicMock()
    st.tabs = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
    st.info = MagicMock()
    st.warning = MagicMock()
    st.success = MagicMock()
    st.markdown = MagicMock()
    
    # render_top_panel 등 임포트하는 함수들 mocking
    import app_v16_1_10
    app_v16_1_10.render_top_panel = MagicMock()
    app_v16_1_10.render_obsidian_rag_search = MagicMock()
    app_v16_1_10.save_workspace_state = MagicMock()
    
    # render_part2 실행
    app_v16_1_10.render_part2()
    
    # 3. 값들이 덮어써지지 않고 여전히 사용자가 수정한 값으로 남아있는지 검사
    print(f"p2_gemma_protocol: {st.session_state.p2_gemma_protocol}")
    print(f"p2_bench_prompt: {st.session_state.p2_bench_prompt}")
    
    assert st.session_state.p2_gemma_protocol == "MODIFIED_GEMMA_PROTOCOL_BY_USER_20260526", "렌더링 중 gemma_protocol이 덮어씌워짐"
    assert st.session_state.p2_bench_prompt == "MODIFIED_BENCH_PROMPT_BY_USER_20260526", "렌더링 중 bench_prompt가 덮어씌워짐"
    assert st.session_state.p2_research_prompt == "MODIFIED_RESEARCH_PROMPT_BY_USER_20260526", "렌더링 중 research_prompt가 덮어씌워짐"
    assert st.session_state.p2_plan_prompt == "MODIFIED_PLAN_PROMPT_BY_USER_20260526", "렌더링 중 plan_prompt가 덮어씌워짐"
    print("Test 1 Passed.")


def test_widget_direct_editing_and_saving():
    print("\n--- Test 2: Widget direct editing and save triggering ---")
    
    class MockSessionState(dict):
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)
        def __setattr__(self, key, value):
            self[key] = value
            
    import streamlit as st
    st.session_state = MockSessionState()
    
    # 1. 초기값 설정
    st.session_state.p2_gemma_protocol = "OLD_PROTOCOL"
    st.session_state.p2_thumbnail_plan = "OLD_THUMBNAIL"
    
    # 2. st.text_area 가 사용자가 새로 수정한 값을 리턴한다고 가정할 때
    # 첫 번째 호출(st.text_area 젬마 프로토콜) -> "NEW_PROTOCOL" 리턴
    # 두 번째 호출(st.text_area 썸네일 기획) -> "NEW_THUMBNAIL" 리턴
    # (그 외 다른 st.text_area 호출이 있으면 "dummy" 리턴)
    call_count = 0
    def mock_text_area(label, value=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if "젬마 프로토콜" in label:
            return "NEW_PROTOCOL"
        if "썸네일 기획" in label:
            return "NEW_THUMBNAIL"
        return "dummy"
        
    st.text_area = mock_text_area
    def mock_columns(spec, **kwargs):
        if isinstance(spec, list):
            return [MagicMock() for _ in range(len(spec))]
        elif isinstance(spec, int):
            return [MagicMock() for _ in range(spec)]
        return [MagicMock(), MagicMock()]
        
    st.columns = mock_columns
    st.selectbox = MagicMock(return_value="gemma4:e2b")
    st.text_input = MagicMock(return_value="7777")
    st.button = MagicMock(return_value=False)
    st.caption = MagicMock()
    st.divider = MagicMock()
    st.subheader = MagicMock()
    st.tabs = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
    st.info = MagicMock()
    st.warning = MagicMock()
    st.success = MagicMock()
    st.markdown = MagicMock()
    
    import app_v16_1_10
    app_v16_1_10.render_top_panel = MagicMock()
    app_v16_1_10.render_obsidian_rag_search = MagicMock()
    
    save_called = 0
    def mock_save():
        nonlocal save_called
        save_called += 1
        return True
    app_v16_1_10.save_workspace_state = mock_save
    
    # render_part2 호출
    app_v16_1_10.render_part2()
    
    # 3. 바뀐 값들이 세션에 잘 반영되고 save_workspace_state 가 잘 돌았는지 검사
    print(f"Updated protocol in state: {st.session_state.p2_gemma_protocol}")
    print(f"Updated thumbnail in state: {st.session_state.p2_thumbnail_plan}")
    print(f"save_workspace_state called count: {save_called}")
    
    assert st.session_state.p2_gemma_protocol == "NEW_PROTOCOL", "프로토콜 직접 편집 저장 실패"
    assert st.session_state.p2_thumbnail_plan == "NEW_THUMBNAIL", "썸네일 직접 편집 저장 실패"
    assert save_called >= 2, "자동 세이브 트리거 실패"
    print("Test 2 Passed.")


def main():
    try:
        test_prompt_no_overwriting_during_render()
        test_widget_direct_editing_and_saving()
        print("\n🎉 ALL RENDERING PERSISTENCE TESTS PASSED SUCCESSFULLY! v16.1.10 is fully stable.")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
