import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '마스터' in line or 'GEMMA' in line.upper() or 'PIN' in line.upper():
        print(f'{i+1}: {line.strip()}')
