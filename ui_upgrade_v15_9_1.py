# -*- coding: utf-8 -*-
"""
현자의 거울 스튜디오 — UI 개선 스크립트 v15.9 → v15.9.1
작업: 4가지 UI 개선 + 버튼 명칭 변경
"""
import re

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

# BOM 포함 UTF-8로 읽기
with open(target_file, 'rb') as f:
    raw = f.read()

# BOM 제거 후 utf-8 디코딩
if raw[:3] == b'\xef\xbb\xbf':
    content = raw[3:].decode('utf-8')
else:
    content = raw.decode('utf-8')

print(f"파일 로드 완료. 전체 줄 수: {len(content.splitlines())}")

# =============================================================================
# 작업 1: 버튼 명칭 변경 "🤖 Sage Pop-up" → "🤖 젬마 어시스턴트"
# =============================================================================
old_btn = '"🤖 Sage Pop-up"'
new_btn = '"🤖 젬마 어시스턴트"'
count = content.count(old_btn)
content = content.replace(old_btn, new_btn)
print(f"[작업1] 버튼 명칭 변경: {count}개 교체 완료")

# =============================================================================
# 작업 2: 파트별 헤더 c_control 박스를 글래스모피즘 사각형 박스로 감싸기
# c_model_col, c_pin_col, c_pop_col 앞뒤로 div 추가
# =============================================================================

# 패턴: header-control-box-anchor div 바로 다음의 columns 호출 찾기
# 기존: st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
# 개선: 같은 내용이지만 glass-control-box div 추가

old_anchor = """        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)"""
new_anchor = """        st.markdown('<div id="header-control-box-anchor"></div><div class="glass-control-box">', unsafe_allow_html=True)"""

anchor_count = content.count(old_anchor)
content = content.replace(old_anchor, new_anchor)
print(f"[작업2a] 컨트롤 박스 시작 div 추가: {anchor_count}개")

# c_pop_col 의 닫는 div 다음에 glass-control-box 닫기
# header-pop-wrapper 닫는 div 다음 with c_pop_col 블록 끝에 추가
old_pop_close = """            st.markdown('</div>', unsafe_allow_html=True)

    is_locked"""
new_pop_close = """            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # glass-control-box 닫기

    is_locked"""

pop_count = content.count(old_pop_close)
content = content.replace(old_pop_close, new_pop_close)
print(f"[작업2b] 컨트롤 박스 닫기 div 추가: {pop_count}개")

# =============================================================================
# 작업 3: 파이프라인 노드 라벨 폰트 크기 확대 (CSS 패치)
# =============================================================================
old_pipe_css = """.sage-pipe-label {
    font-size: 0.70em;"""
new_pipe_css = """.sage-pipe-label {
    font-size: 0.82em;"""

pipe_count = content.count(old_pipe_css)
content = content.replace(old_pipe_css, new_pipe_css)
print(f"[작업3] 파이프 라벨 폰트 크기 확대: {pipe_count}개")

# =============================================================================
# 작업 4: CSS - 글래스모피즘 컨트롤 박스 스타일 추가
# sage_config.py의 GLOBAL_CSS는 건드리지 않음!
# app.py 내의 별도 st.markdown CSS에 추가
# =============================================================================
# 현재 파일 내에 header-model-wrapper, header-pin-wrapper, header-pop-wrapper
# CSS가 있는지 확인하고 glass-control-box 추가

old_model_css = """.header-model-wrapper {"""
new_model_css = """.glass-control-box {
    background: linear-gradient(135deg, rgba(40, 20, 10, 0.85) 0%, rgba(60, 30, 15, 0.75) 100%);
    border: 1px solid rgba(212,175,106,0.35);
    border-radius: 12px;
    padding: 6px 10px 6px 10px;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.4), inset 0 1px 0 rgba(212,175,106,0.2);
    display: flex;
    align-items: center;
    gap: 6px;
}
.header-model-wrapper {"""

model_count = content.count(old_model_css)
content = content.replace(old_model_css, new_model_css, 1)  # 첫 번째만
print(f"[작업4] 글래스모피즘 박스 CSS 추가: {model_count}개 (1개만 적용)")

# =============================================================================
# 작업 5: 연동 상태 카드 — 미연동 시 빨간 점 표시 로직 확인 (이미 구현되어 있으면 skip)
# =============================================================================
if 'status-dot-red' in content or 'clickable-card' in content:
    print("[작업5] 연동 상태 빨간 점 — 기존 로직 확인됨, 추가 작업 없음")
else:
    print("[작업5] 빨간 점 로직 미발견 — 별도 확인 필요")

# =============================================================================
# 파일 헤더 버전 정보 업데이트
# =============================================================================
old_ver = 'Master App v15.9'
new_ver = 'Master App v15.9.1'
content = content.replace(old_ver, new_ver, 1)

old_date_comment = '[v15.9 업데이트 사항:'
new_date_comment = '[v15.9.1 업데이트 사항: 2026-05-22]\n- UI 개선: 젬마 어시스턴트 버튼 명칭 변경 (Sage Pop-up → 젬마 어시스턴트)\n- UI 개선: 파트 헤더 우측 컨트롤 박스 글래스모피즘 디자인 적용\n- UI 개선: 실시간 데이터 연동 상황판 파이프 라벨 폰트 확대\n[v15.9 업데이트 사항:'
content = content.replace(old_date_comment, new_date_comment, 1)

print("[버전] v15.9 → v15.9.1 업데이트 완료")

# =============================================================================
# BOM 없이 UTF-8로 저장
# =============================================================================
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ 모든 작업 완료! 저장 경로: {target_file}")
print(f"최종 줄 수: {len(content.splitlines())}")
