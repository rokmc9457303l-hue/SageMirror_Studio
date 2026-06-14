import re

with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. Disable all remaining "🤖 젬마 어시스턴트" buttons
content = content.replace(
    'if st.button("🤖 젬마 어시스턴트", type="secondary", use_container_width=True, key="p',
    'if False: # st.button("🤖 젬마 어시스턴트", type="secondary", use_container_width=True, key="p'
)

# 2. Check if any 🤖 젬마 어시스턴트 buttons are still active
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'st.button("🤖 젬마 어시스턴트"' in line and 'if False' not in line:
        print(f"Warning: active button still found on line {i+1}: {line.strip()}")

with open('app_v17_2_3.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("Dead UI removed.")
