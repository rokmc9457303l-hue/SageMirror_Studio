import shutil
import re

shutil.copy2(r'C:\SageMirror_Production\app_v17_1_30.py', r'C:\SageMirror_Production\app_v17_1_31.py')

with open(r'C:\SageMirror_Production\app_v17_1_31.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. delete render_part0_assistant completely.
text = re.sub(r'def render_part0_assistant\(\):[\s\S]*?(?=def render_part1\(\):)', '', text)
text = re.sub(r'\s*"파트 0: 🤖 젬마 스튜디오 \(대화 & 자료수집\)",?\n', '\n', text)

old_css_wrapper = '''st.markdown("""
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
'''

new_css_wrapper = '''st.markdown("""
<style>
div[data-testid="column"]:has(#gemma-right-anchor) {
    position: sticky !important;
    top: 3rem !important;
    height: calc(100vh - 3rem) !important;
    overflow-y: auto !important;
}
div[data-testid="column"]:has(#gemma-right-anchor)::-webkit-scrollbar { width: 4px; }
</style>
""", unsafe_allow_html=True)

col_main, col_gemma = st.columns([7, 3], gap="large")
with col_gemma:
    st.markdown('<div id="gemma-right-anchor"></div>', unsafe_allow_html=True)
    st.markdown("<h4 style='color:#d4af6a;'>🤖 젬마 어시스턴트</h4>", unsafe_allow_html=True)
    st.info("이곳이 1~8 파트 스크롤과 무관하게 영구 고정될 우측 젬마 대화창입니다.")
'''
text = text.replace(old_css_wrapper, new_css_wrapper)

if 'if part.startswith("파트 0"):' in text:
    part0_idx = text.find('if part.startswith("파트 0"):')
    part1_idx = text.find('elif part.startswith("파트 1"):')
    if part1_idx != -1:
        text = text[:part0_idx] + text[part1_idx:]

with open(r'C:\SageMirror_Production\app_v17_1_31.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('success')
