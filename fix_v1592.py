import sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_2.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"[로드] 줄 수: {len(content.splitlines())}")

# 깨진 f-string 찾기
idx = content.find('candidates_text += f"[{i+1}]')
if idx >= 0:
    chunk = content[idx:idx+200]
    print(f"[문제 위치]: {repr(chunk)}")
    
    # 한글 깨진 부분을 영어로 교체
    old_fstr = 'candidates_text += f"[{i+1}] \\uc81c\\ubaa9: {r.get(\'title\',\'\')}\\n URL: {r.get(\'url\',\'\')}\\n \\ub0b4\\uc6a9: {r.get(\'content\',\'\')[:200]}\\n\\n"'
    new_fstr = 'candidates_text += f"[{i+1}] Title: {r.get(\'title\',\'\')}\\n URL: {r.get(\'url\',\'\')}\\n Content: {r.get(\'content\',\'\')[:200]}\\n\\n"'
    print(f"교체 전: {content.count(old_fstr)}개")

# 위치 기반으로 직접 찾아 교체
lines = content.split('\n')
for i_line, line in enumerate(lines):
    if 'candidates_text +=' in line and 'f"[{i+1}]' in line:
        print(f"발견! 줄 {i_line+1}: {repr(line[:80])}")
        lines[i_line] = '                        candidates_text += f"[{i+1}] Title: {r.get(\'title\',\'\')}\\n URL: {r.get(\'url\',\'\')}\\n Content: {r.get(\'content\',\'\')[:200]}\\n\\n"'
        print(f"교체 완료!")
        break

content = '\n'.join(lines)

# 세션스테이트 초기화 보완
old_init = '"youtube_api_key": "",'
new_init = ('"youtube_api_key": "",\n'
            '        "gemini_api_key": "AIzaSyAhLlLIgnFXNwZY5ARLXYvOMsPHvK82X7Q",\n'
            '        "p1_gemini_model": "gemini-2.0-flash-exp",\n'
            '        "p1_channel_top10": [],\n'
            '        "p1_benchmark_channel": {},\n'
            '        "p1_search_keywords": [],')
init_count = content.count(old_init)
if init_count > 0:
    content = content.replace(old_init, new_init, 1)
    print(f"[세션스테이트] 초기화 키 추가 완료")
else:
    print(f"[세션스테이트] youtube_api_key 패턴 미발견")
    # 다른 방법
    alt = '"youtube_api_key": ""'
    alt_count = content.count(alt)
    print(f"  alt 패턴: {alt_count}개")

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n[저장] 줄 수: {len(content.splitlines())}")

result = subprocess.run(
    ['C:\\Python314\\python.exe', '-m', 'py_compile', target_file],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
if result.returncode == 0:
    print("COMPILE: OK!")
else:
    # 에러 위치 표시
    err = result.stderr
    print(f"COMPILE ERROR: {err[:400]}")
    
    # 에러 줄 찾기
    import re
    match = re.search(r'line (\d+)', err)
    if match:
        err_line = int(match.group(1))
        lines2 = content.split('\n')
        for j in range(max(0, err_line-3), min(len(lines2), err_line+3)):
            print(f"  {j+1}: {repr(lines2[j][:80])}")
