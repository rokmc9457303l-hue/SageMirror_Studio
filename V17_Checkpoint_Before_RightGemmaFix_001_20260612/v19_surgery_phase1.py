"""
V19 UI Surgery Script
수술 1: popup_assistant() → render_assistant_chat() 변환 (팝업 폐기)
수술 2: app 라우팅 블록 7:3 분할
수술 3: Sticky CSS 주입 + 팝업 호출 버튼 제거
"""
import re

# ─────────────────────────────────────────────────────────────
# [수술 1] sage_popups_v19_0_1_WORK.py 수정
# ─────────────────────────────────────────────────────────────
print("=== 수술 1: sage_popups 수정 ===")

with open('sage_popups_v19_0_1_WORK.py', 'r', encoding='utf-8-sig') as f:
    popup_content = f.read()

# 1-a. @st.dialog 데코레이터 제거 + 함수명 변경
before_func = '@st.dialog("🤖 어시스턴트", width="large")\ndef popup_assistant():'
after_func = 'def render_assistant_chat():'
popup_content = popup_content.replace(before_func, after_func)
print(f"  함수명/데코레이터 교체: {'성공' if 'render_assistant_chat' in popup_content else '실패'}")

# 1-b. 대화 기록 컨테이너 높이를 750으로 변경
# 기존: _chat_box = st.container(height=500)
popup_content = popup_content.replace(
    '_chat_box = st.container(height=500)',
    '_chat_box = st.container(height=750)'
)
print("  대화창 height=750 설정: 완료")

with open('sage_popups_v19_0_1_WORK.py', 'w', encoding='utf-8-sig') as f:
    f.write(popup_content)

print("  sage_popups_v19_0_1_WORK.py 저장 완료\n")

# ─────────────────────────────────────────────────────────────
# [수술 2 + 3] app_v19_0_1_WORK.py 수정
# ─────────────────────────────────────────────────────────────
print("=== 수술 2+3: app_v19_0_1_WORK.py 수정 ===")

with open('app_v19_0_1_WORK.py', 'r', encoding='utf-8-sig') as f:
    app_content = f.read()

# ── 3-a. Sticky CSS 주입: GLOBAL_CSS 영역 뒤에 삽입 ──────────
# render_right_gemma_panel 함수 이전, 파트 라우팅 블록 이전에 st.html로 sticky CSS 삽입
# 라우팅 블록의 마커를 찾아 그 위에 CSS를 넣음
STICKY_CSS_INJECTION = """
# ── V19: 우측 대화창 Sticky 고정 CSS ──────────────────────────
st.html('''<style>
div[data-testid="column"]:nth-of-type(2) {
    position: sticky;
    top: 2rem;
    z-index: 999;
    align-self: flex-start;
    max-height: calc(100vh - 4rem);
    overflow-y: auto;
}
div[data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:nth-of-type(2)) {
    align-items: flex-start !important;
}
</style>''')
"""

# ── 3-b. 팝업 호출 버튼 제거 ───────────────────────────────────
# popup_assistant() 호출부를 주석 처리
app_content = re.sub(
    r'([ \t]*)(popup_assistant\(\))',
    r'\1# [V19 제거됨] \2',
    app_content
)

# popup_assistant 버튼 코드들 주석 처리 (if st.button 패턴으로 열리는 어시스턴트 버튼)
app_content = re.sub(
    r'([ \t]*if st\.button\([^\)]*어시스턴트[^\)]*\)[^:]*:)',
    r'\1  # [V19 비활성화]',
    app_content
)
print("  popup_assistant() 호출부 주석 처리 완료")

# ── 2. 파트 라우팅 블록 찾기 ─────────────────────────────────────
ROUTING_MARKER = '# 파트 라우팅 블록'
routing_idx = app_content.find(ROUTING_MARKER)
if routing_idx == -1:
    print("  !! 파트 라우팅 블록 마커를 찾지 못했습니다.")
    print("  대안 마커로 재시도...")
    # 대안 마커: render_part1() 등이 나오는 곳을 찾음
    routing_idx = app_content.find('if part.startswith("파트 1")')
    if routing_idx == -1:
        routing_idx = app_content.find("if part.startswith(")
    # 라인 시작으로 이동
    line_start = app_content.rfind('\n', 0, routing_idx) + 1
    routing_idx = line_start

print(f"  라우팅 블록 위치: {routing_idx}")

# 해당 위치의 코드 5줄 확인
snippet = app_content[routing_idx:routing_idx+300]
print(f"  마커 이후 코드 미리보기: {snippet[:200]!r}")

with open('app_v19_0_1_WORK.py', 'w', encoding='utf-8-sig') as f:
    f.write(app_content)

print("\n  app_v19_0_1_WORK.py 1차 저장 완료 (popup 호출 제거)")
print("\n=== 수술 스크립트 1단계 완료 ===")
print("  라우팅 구조 확인 후 2단계 진행 예정")
