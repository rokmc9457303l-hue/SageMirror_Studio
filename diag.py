import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
print(f"Total lines: {len(lines)}")

# sage-pipe-label CSS 찾기
for i, line in enumerate(lines):
    if 'sage-pipe-label' in line and '{' in line:
        print(f"Line {i+1}: {repr(line)}")
        # 주변 10줄 출력
        for j in range(i, min(i+12, len(lines))):
            print(f"  {j+1}: {repr(lines[j])}")
        break
