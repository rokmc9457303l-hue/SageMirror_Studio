import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'render_part0_assistant' in line or '파트 0' in line or 'Part 0' in line:
        print(f'{i+1}: {line.strip()}')
