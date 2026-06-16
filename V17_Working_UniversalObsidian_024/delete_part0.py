import re

with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.startswith('def render_part0_assistant()'):
        skip = True
    if skip and line.startswith('def render_part1()'):
        skip = False
    
    if skip:
        continue
        
    if 'if cur_p.startswith("파트 0")' in line:
        continue
    if 'if sidebar_part.startswith("파트 0"):   sidebar_part_key = "part0"' in line:
        continue
    if '"part0": ("base_prompt_rules",' in line:
        continue
    if 'if part.startswith("파트 0"):' in line:
        skip_routing = True
        continue
        
    # The routing block is:
    # if part.startswith("파트 0"):
    #     part = "파트 1: 벤치마킹 & 자료조사"
    # So we skip the next line too if it's the assignment.
    # Actually wait, let's just do an exact match replacement.
    new_lines.append(line)

content = "".join(new_lines)

# Fix routing block
content = content.replace('if part.startswith("파트 0"):\n    part = "파트 1: 벤치마킹 & 자료조사"\n\n', '')

# Fix CSS to make sticky work properly
css_original = """    div[data-testid="column"]:has(#right-gemma-sticky-marker) {
        position: sticky !important;
        top: 2rem !important;
        align-self: flex-start !important;
        height: 95vh !important;
        overflow-y: auto !important;
        padding-right: 5px;
    }"""
css_fixed = """    /* 우측 패널 고정을 위한 부모 컨테이너 설정 */
    div[data-testid="stHorizontalBlock"]:has(#right-gemma-sticky-marker) {
        align-items: flex-start !important;
    }
    div[data-testid="column"]:has(#right-gemma-sticky-marker) {
        position: sticky !important;
        top: 2rem !important;
        align-self: flex-start !important;
        height: calc(100vh - 4rem) !important;
        overflow-y: auto !important;
        padding-right: 5px;
        z-index: 999;
    }"""
content = content.replace(css_original, css_fixed)

with open('app_v17_2_3.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("Part 0 deleted and sticky CSS fixed.")
