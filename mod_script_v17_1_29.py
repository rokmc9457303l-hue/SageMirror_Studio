import re

with open('app_v17_1_29.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. 사이드바 라우팅 정리
text = re.sub(r'\s*"파트 0: 🤖 젬마 스튜디오 \(대화 & 자료수집\)",?\n', '\n', text)

# 2. 메인 라우팅 찾기 및 제거
# 'if part.startswith("파트 0"):' 부터 'elif part.startswith("파트 1"):' 전까지 제거
part0_start_idx = text.find('if part.startswith("파트 0"):')
part1_start_idx = text.find('elif part.startswith("파트 1"):')

if part0_start_idx != -1 and part1_start_idx != -1:
    # 파트 1부터 파일 끝부분에서 라우팅이 끝나는 지점까지 찾기
    routing_end_idx = text.find('render_right_panel()')
    end_line_idx = text.find('\n', routing_end_idx)
    if end_line_idx == -1:
        end_line_idx = len(text)
        
    block = text[part1_start_idx:end_line_idx]
    
    # "elif part.startswith("파트 1"):" 를 "if part.startswith("파트 1"):" 로 변경 (문법 오류 방지)
    block = block.replace('elif part.startswith("파트 1"):', 'if part.startswith("파트 1"):', 1)
    
    # 들여쓰기 4칸
    indented_block = '\n'.join('    ' + line if line.strip() else line for line in block.split('\n'))
    
    css_and_wrapper = '''st.markdown("""
<style>
/* Streamlit의 두 번째 컬럼(우측 창)을 뷰포트에 영구 고정 */
div[data-testid="column"]:nth-of-type(2) {
    position: sticky !important;
    top: 4rem !important;
    height: calc(100vh - 4rem) !important;
    overflow-y: auto !important;
}
</style>
""", unsafe_allow_html=True)

col_main, col_gemma = st.columns([7, 3], gap="large")
with col_gemma:
    st.subheader("🤖 젬마 어시스턴트")
with col_main:
'''
    
    new_block = css_and_wrapper + indented_block
    
    text = text[:part0_start_idx] + new_block + text[end_line_idx:]

with open('app_v17_1_29_mod.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Modification done!")
