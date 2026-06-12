import re

with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. Disable popup_assistant calls by replacing popup_assistant() with # popup_assistant()
content = re.sub(r'([ \t]*)popup_assistant\(\)', r'\1pass # popup_assistant()', content)

# 2. Change the Right Gemma Panel Title to h4
content = content.replace('st.markdown("### 🔍 리서치")', 'st.markdown("<h4>🔍 리서치</h4>", unsafe_allow_html=True)')
content = content.replace('st.markdown("### 🔎 리서치")', 'st.markdown("<h4>🔍 리서치</h4>", unsafe_allow_html=True)')

# 3. Change model short names
content = content.replace('["G2B", "G4B", "Gemini", "Gemini3", "Tavily"]', '["G2", "G4", "GM", "G3", "TV"]')
content = content.replace('["Gemma 2B", "Gemma 4B", "Gemini", "Gemini 3", "Tavily"]', '["G2", "G4", "GM", "G3", "TV"]')

# 4. Hide the 젬마 어시스턴트 button if it exists explicitly
content = content.replace('if st.button("🤖 젬마 어시스턴트", type="secondary", use_container_width=True, key="p0_popup_btn"):', 'if False: # st.button("🤖 젬마 어시스턴트", type="secondary", use_container_width=True, key="p0_popup_btn"):')

with open('app_v17_2_3.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("Fix applied.")
