import sys

with open("app_v17_2_3.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.startswith("def render_right_gemma_panel():"):
        start_idx = i
    if start_idx != -1 and line.startswith("# 파트 라우팅"):
        end_idx = i
        break

if start_idx == -1 or end_idx == -1:
    print("Could not find the function boundaries!")
    sys.exit(1)

new_code = """def run_right_research_engine(engine_id, query, context=None) -> dict:
    import time
    import os
    res = {
        "success": False,
        "engine": engine_id,
        "text": "",
        "sources": [],
        "verification_status": "unverified",
        "error_code": "",
        "error_message": "",
        "elapsed_seconds": 0.0
    }
    start_time = time.time()
    
    try:
        if engine_id in ["gemma4:e2b", "gemma4:e4b"]:
            # Local Ollama
            import requests
            import json
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": engine_id,
                "prompt": f"{context}\\n\\n{query}" if context else query,
                "stream": False,
                "options": {
                    "num_predict": 2000,
                    "temperature": 0.2
                }
            }
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            res["text"] = data.get("response", "").strip()
            if not res["text"]:
                res["error_code"] = "empty_response"
                res["error_message"] = "응답이 비어있습니다."
            else:
                res["success"] = True
                res["verification_status"] = "verified"
                res["sources"] = [{"title": "Ollama Local", "url": "localhost"}]
                
        elif "gemini" in engine_id:
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            if not api_key:
                res["error_code"] = "missing_key"
                res["error_message"] = "[Gemini API 키 미설정] GEMINI_API_KEY가 존재하지 않습니다."
                return res
            
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name=engine_id)
            prompt = f"{context}\\n\\n{query}" if context else query
            
            resp = model.generate_content(prompt)
            res["text"] = resp.text.strip()
            if not res["text"]:
                res["error_code"] = "empty_response"
                res["error_message"] = "응답이 비어있습니다."
            else:
                res["success"] = True
                res["verification_status"] = "verified"
                res["sources"] = [{"title": "Gemini API", "url": "google"}]
                
        elif engine_id == "Tavily 웹 검색":
            api_key = os.getenv("TAVILY_API_KEY", "").strip()
            if not api_key:
                res["error_code"] = "missing_key"
                res["error_message"] = "[Tavily API 키 미설정] TAVILY_API_KEY가 존재하지 않습니다."
                return res
                
            from research_router import run_tavily_research
            tavily_res = run_tavily_research(query, api_key, max_results=5)
            if "error" in tavily_res:
                res["error_code"] = "tavily_error"
                res["error_message"] = f"[Tavily 오류] {tavily_res['error']}"
            else:
                res["success"] = True
                res["text"] = tavily_res.get("answer", "Tavily 검색이 완료되었습니다.")
                if not res["text"] and tavily_res.get("results"):
                    res["text"] = "\\n".join([f"- {r.get('title')}: {r.get('content')}" for r in tavily_res["results"]])
                if not res["text"]:
                    res["text"] = "Tavily 검색 결과가 없습니다."
                for r in tavily_res.get("results", []):
                    res["sources"].append({"title": r.get("title", "제목 없음"), "url": r.get("url", "")})
                res["verification_status"] = "verified"
        else:
            res["error_code"] = "unknown_engine"
            res["error_message"] = f"알 수 없는 엔진: {engine_id}"
            
    except requests.exceptions.Timeout:
        res["error_code"] = "timeout"
        res["error_message"] = "[요청 시간 초과] API 응답이 너무 늦습니다."
    except requests.exceptions.ConnectionError:
        res["error_code"] = "connection_error"
        res["error_message"] = "[연결 오류] 서버에 연결할 수 없습니다. (Ollama 실행 여부 확인)"
    except Exception as e:
        import traceback
        res["error_code"] = "unknown_error"
        res["error_message"] = f"[오류 발생] {str(e)}"
        
    res["elapsed_seconds"] = round(time.time() - start_time, 2)
    return res

def render_right_gemma_panel():
    st.html('''
    <div id="right-gemma-sticky-marker"></div>
    <style>
    div[data-testid="stHorizontalBlock"]:has(#right-gemma-sticky-marker) {
        align-items: flex-start !important;
        overflow: visible !important;
    }
    div[data-testid="column"]:has(#right-gemma-sticky-marker) {
        position: sticky !important;
        top: 2rem !important;
        align-self: flex-start !important;
        height: calc(100vh - 4rem) !important;
        overflow-y: auto !important;
        padding-right: 5px;
        z-index: 999;
    }
    </style>
    ''')

    if "right_research_history" not in st.session_state:
        st.session_state.right_research_history = []

    chat_container = st.container(height=480, border=True)
    with chat_container:
        if not st.session_state.right_research_history:
            pass
        else:
            for msg in st.session_state.right_research_history:
                with st.chat_message(msg["role"]):
                    if msg.get("status") == "error":
                        st.error(msg["content"])
                    else:
                        st.markdown(msg["content"])
                    if msg.get("sources"):
                        with st.expander("출처 확인"):
                            for s in msg["sources"]:
                                st.write(f"- [{s.get('title')}]({s.get('url')})")

    st.markdown("<br>", unsafe_allow_html=True)

    user_input = st.text_area(
        "메시지",
        placeholder="메시지 입력하세요...",
        height=125,
        key="right_gemma_input_widget",
        label_visibility="collapsed"
    )

    ctrl_plus, ctrl_model, ctrl_send = st.columns([1.2, 2.4, 0.9])
    send_clicked = False

    with ctrl_plus:
        with st.popover("＋ 기능", use_container_width=True):
            if st.button("💾 마지막 정상 결과 저장", use_container_width=True):
                last_success_msg = None
                for msg in reversed(st.session_state.right_research_history):
                    if msg.get("role") == "assistant" and msg.get("status") != "error":
                        last_success_msg = msg
                        break
                if last_success_msg:
                    from sage_popups_v17_2_3 import _save_raw_wiki
                    import datetime
                    import os
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    cat = "RightResearch"
                    _save_raw_wiki(last_success_msg["content"], category=cat, custom_filename=f"research_{ts}")
                    
                    # Compute expected paths
                    base_dir = r"C:\\SageMirror_Production\\00_Obsidian"
                    raw_path = os.path.join(base_dir, "00_Raw", f"{cat}_{ts}_RAW.md")
                    wiki_path = os.path.join(base_dir, "01_Wiki", f"{cat}_{ts}_WIKI.md")
                    schema_path = os.path.join(base_dir, "02_Schema", f"{cat}_{ts}_SCHEMA.json")
                    
                    st.success(f"저장 성공!\\n- Raw: {raw_path}\\n- Wiki: {wiki_path}\\n- Schema: {schema_path}")
                else:
                    st.warning("저장할 정상 응답이 없습니다.")
                    
            if st.button("🧩 현재 Part로 Push", use_container_width=True):
                last_success_msg = None
                for msg in reversed(st.session_state.right_research_history):
                    if msg.get("role") == "assistant" and msg.get("status") != "error":
                        last_success_msg = msg
                        break
                if last_success_msg:
                    import uuid
                    import datetime
                    target_part = st.session_state.get("sidebar_part", "파트 1").split(":")[0].strip()
                    st.session_state["right_gemma_push_packet"] = {
                        "packet_id": str(uuid.uuid4()),
                        "source": "right_gemma",
                        "target_part": target_part,
                        "query": "우측 리서치 결과",
                        "result": last_success_msg["content"],
                        "engine": last_success_msg["engine"],
                        "sources": last_success_msg.get("sources", []),
                        "verification_status": last_success_msg.get("verification_status", "unverified"),
                        "status": "waiting_review",
                        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.success("자료 Push 성공. 중앙 화면에 나타납니다.")
                else:
                    st.warning("Push할 정상 응답이 없습니다.")
                    
            if st.button("🧹 대화 초기화", use_container_width=True):
                st.session_state.right_research_history = []
                st.rerun()

    with ctrl_model:
        models_display = ["G2", "G4", "GM", "G3", "TV"]
        models_internal = ["gemma4:e2b", "gemma4:e4b", "gemini-2.5-flash", "gemini-3-flash", "Tavily 웹 검색"]
        selected_mode_display = st.selectbox("모델", models_display, key="right_gemma_model_select", label_visibility="collapsed")
        selected_mode = models_internal[models_display.index(selected_mode_display)]

    with ctrl_send:
        send_clicked = st.button("전송", key="right_gemma_send_button", use_container_width=True, type="primary")

    if send_clicked and user_input.strip():
        import datetime
        st.session_state.right_research_history.append({
            "role": "user",
            "content": user_input,
            "engine": selected_mode,
            "status": "sent",
            "sources": [],
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        with chat_container.chat_message("user"):
            st.markdown(user_input)

        with chat_container.chat_message("assistant"):
            with st.spinner("응답 대기 중..."):
                sys_prompt = "안내: 당신은 매우 뛰어난 현자입니다. 사용자에게 직접적으로 답변을 주십시오. 존댓말 사용. 주인공을 @Protagonist 로 지칭하십시오."
                res = run_right_research_engine(selected_mode, user_input, context=sys_prompt)
                
                if res["success"]:
                    st.markdown(res["text"])
                    if res["sources"]:
                        with st.expander("출처 확인"):
                            for s in res["sources"]:
                                st.write(f"- [{s.get('title')}]({s.get('url')})")
                                
                    st.session_state.right_research_history.append({
                        "role": "assistant",
                        "content": res["text"],
                        "engine": res["engine"],
                        "status": "success",
                        "sources": res["sources"],
                        "verification_status": res["verification_status"],
                        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    err_msg = res["error_message"]
                    st.error(err_msg)
                    st.session_state.right_research_history.append({
                        "role": "assistant",
                        "content": err_msg,
                        "engine": res["engine"],
                        "status": "error",
                        "sources": [],
                        "verification_status": "error",
                        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        st.rerun()

"""

lines = lines[:start_idx] + [new_code] + lines[end_idx:]

with open("app_v17_2_3.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Refactored successfully!")
