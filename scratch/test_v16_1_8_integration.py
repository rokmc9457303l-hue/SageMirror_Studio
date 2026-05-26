import sys
import os
from unittest.mock import MagicMock

# 라이브러리 경로 추가
sys.path.append(r"C:\SageMirror_Production")

def test_recent_activity_memory():
    print("--- Test 1: update_recent_activity_memory Deduplication & FIFO ---")
    from rag_memory_utils import update_recent_activity_memory
    
    state = {"recent_activity_memory": []}
    
    # 1. 일반 활동 추가
    state["recent_activity_memory"] = update_recent_activity_memory(state, "tavily", "검색 테스트 1")
    print(f"Added 1: {state['recent_activity_memory']}")
    
    # 2. 동일한 활동 추가 (중복 제거 검증)
    state["recent_activity_memory"] = update_recent_activity_memory(state, "tavily", "검색 테스트 1")
    print(f"Added duplicate (should stay 1, but update timestamp): {state['recent_activity_memory']}")
    assert len(state["recent_activity_memory"]) == 1, "중복 제거 실패"
    
    # 3. 다른 활동 추가
    state["recent_activity_memory"] = update_recent_activity_memory(state, "tavily", "검색 테스트 2")
    state["recent_activity_memory"] = update_recent_activity_memory(state, "obsidian", "노트 저장")
    print(f"Added distinct: {state['recent_activity_memory']}")
    assert len(state["recent_activity_memory"]) == 3, "개별 추가 실패"
    
    # 4. FIFO 검증 (15개 이상 추가)
    for i in range(20):
        state["recent_activity_memory"] = update_recent_activity_memory(state, "flow", f"작업 {i}")
    
    print(f"After adding 20 items (should limit to 15): {len(state['recent_activity_memory'])}")
    assert len(state["recent_activity_memory"]) <= 15, "FIFO 15개 제한 초과"
    print("Test 1 Passed.")


def test_build_recent_activity_memory():
    print("\n--- Test 2: build_recent_activity_memory formatting ---")
    from rag_memory_utils import build_recent_activity_memory
    
    state = {
        "recent_activity_memory": [
            {"timestamp": "2026-05-26 12:00:00", "type": "tavily", "content": "검색 쿼리 1"},
            {"timestamp": "2026-05-26 12:05:00", "type": "obsidian", "content": "메모리 세이브 1"},
            {"timestamp": "2026-05-26 12:10:00", "type": "part_save", "content": "Part1 벤치마킹 완료"},
        ]
    }
    
    res = build_recent_activity_memory(state, max_chars=1000)
    print("Formatted memory output:")
    print(res)
    assert "[RECENT_ACTIVITY_MEMORY]" in res, "Header missing"
    assert "검색 쿼리 1" in res or "메모리 세이브 1" in res or "Part1 벤치마킹 완료" in res, "Contents missing"
    print("Test 2 Passed.")


def test_agent_registry_metadata():
    print("\n--- Test 3: agent_registry metadata schema validation ---")
    from agent_registry import get_agent_tool_registry
    
    registry = get_agent_tool_registry()
    assert isinstance(registry, dict), "Registry should be a dictionary"
    
    for tool_name, info in registry.items():
        print(f"Tool: {tool_name} | experimental: {info.get('experimental')} | safe_mode: {info.get('safe_mode')}")
        assert "experimental" in info, f"{tool_name} is missing 'experimental' metadata"
        assert "safe_mode" in info, f"{tool_name} is missing 'safe_mode' metadata"
        assert isinstance(info["experimental"], bool), f"{tool_name} 'experimental' is not a boolean"
        assert isinstance(info["safe_mode"], bool), f"{tool_name} 'safe_mode' is not a boolean"
        
    print("Test 3 Passed.")


def test_tool_detection_and_execution():
    print("\n--- Test 4: Tool detection, permission checks and fallback execution ---")
    
    # streamlit Mocking
    import streamlit as st
    st.session_state = MagicMock()
    st.session_state.get.side_effect = lambda key, default=None: {
        "tavily_api_key": "dummy_key",
        "path_obsidian": "C:\\SageMirror_Production\\00_Obsidian"
    }.get(key, default)
    
    # registry와 toolkit의 함수들 로드
    from agent_registry import get_agent_tool_registry
    from sage_popups import _detect_tools, _execute_tool
    
    # 1. 정상 도구 감증
    test_text = "이 부분은 확실하지 않으므로 [[NEED_RESEARCH: 철학자 데카르트 방법서설]] 로 조사를 수행해라."
    detected = _detect_tools(test_text)
    print(f"Detected tools: {detected}")
    assert any(d["tool"] == "SEARCH_WEB" for d in detected), "SEARCH_WEB (NEED_RESEARCH) 감지 실패"
    
    # 2. 비활성화 도구 감지 배제 검증
    # 임시로 레지스트리의 특정 도구를 비활성화
    registry = get_agent_tool_registry()
    original_enabled = registry["SEARCH_WEB"]["enabled"]
    
    try:
        registry["SEARCH_WEB"]["enabled"] = False
        detected_after_disable = _detect_tools(test_text)
        print(f"Detected after disabling SEARCH_WEB: {detected_after_disable}")
        assert not any(d["tool"] == "SEARCH_WEB" for d in detected_after_disable), "비활성화 도구 감지 차단 실패"
        
        # 3. 비활성화된 도구를 직접 실행했을 때의 거부 메시지 검증
        exec_res = _execute_tool("SEARCH_WEB", "철학자 데카르트", "질문", "gemma4:e2b", "part1")
        print(f"Execution result of disabled tool: {exec_res}")
        assert "비활성화 상태" in exec_res, "비활성화 도구 실행 차단 실패"
    finally:
        registry["SEARCH_WEB"]["enabled"] = original_enabled
        
    # 4. 미등록 도구 실행 시 거부 메시지 검증
    exec_res_unknown = _execute_tool("UNKNOWN_CRITICAL_TOOL", "파라미터", "질문", "gemma4:e2b", "part1")
    print(f"Execution result of unregistered tool: {exec_res_unknown}")
    assert "등록되지 않은" in exec_res_unknown, "미등록 도구 실행 차단 실패"
    
    print("Test 4 Passed.")


def test_agent_loop_recovery():
    print("\n--- Test 5: run_agent_loop Recovery & try-except fallback ---")
    
    # streamlit Mocking
    import streamlit as st
    st.session_state = MagicMock()
    
    # 의도적으로 에러를 내도록 _execute_tool을 패치하여 run_agent_loop의 복구력 검증
    import sage_popups
    original_execute = sage_popups._execute_tool
    
    def mock_execute_tool(tool, param, question, model, part_key):
        raise ValueError("임의로 발생시킨 치명적 실행 에러")
        
    sage_popups._execute_tool = mock_execute_tool
    
    # call_gemma 모킹
    sage_popups.call_gemma = MagicMock(return_value="최종 결과 응답")
    sage_popups.call_gemma_stream = MagicMock(return_value=["[[NEED_RESEARCH: 테스트 쿼리]]"])
    
    # stream_placeholder와 status_widget 모킹
    stream_placeholder = MagicMock()
    status_widget = MagicMock()
    
    try:
        # 루프 실행
        res = sage_popups.run_agent_loop(
            question="질문",
            sys_ctx="시스템 콘텍스트",
            model="gemma4:e2b",
            part_key="part1",
            max_iterations=2,
            stream_placeholder=stream_placeholder,
            status_widget=status_widget
        )
        print("Loop completed without crashing!")
        print(f"Call gemma arguments: {sage_popups.call_gemma.call_args_list}")
        
        # 첫 번째 iteration 후 execute_tool이 실패하여 에러 메시지가 RAG 컨텍스트(accumulated_context)에 쌓였고,
        # 두 번째 iteration에서 call_gemma의 prompt 인자에 그 에러 메시지가 전달되었는지 확인
        args, kwargs = sage_popups.call_gemma.call_args
        prompt_passed = args[0]
        print(f"Passed prompt to next iteration:\n{prompt_passed}")
        
        assert "치명적 오류 발생" in prompt_passed or "ValueError" in prompt_passed or "임의로 발생시킨" in prompt_passed, "치명적 오류의 RAG 복구 전달 실패"
        print("Test 5 Passed.")
    finally:
        sage_popups._execute_tool = original_execute


def main():
    try:
        test_recent_activity_memory()
        test_build_recent_activity_memory()
        test_agent_registry_metadata()
        test_tool_detection_and_execution()
        test_agent_loop_recovery()
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! v16.1.8 is fully stable.")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
